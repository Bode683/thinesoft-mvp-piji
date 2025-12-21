from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Todo, Tenant, User, AuditLog
from .serializers import (
    TodoSerializer,
    TenantSerializer,
    UserSerializer,
    UserWriteSerializer,
    RoleAssignmentSerializer,
    PasswordSetSerializer,
    ActivateSerializer,
)
from rest_framework import permissions, viewsets, decorators
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from .permissions import (
    IsSuperAdmin,
    IsPlatformAdmin,
    IsTenantOwner,
    CanManageTenantUsers,
    in_group,
    IsSuperAdminOrPlatformAdmin,
)

class TodoListApiView(APIView):
    # add permission to check if user is authenticated
    permission_classes = [permissions.IsAuthenticated]

    # 1. List all
    def get(self, request, *args, **kwargs):
        '''
        List all the todo items for given requested user
        '''
        todos = Todo.objects.filter(user = request.user.id)
        serializer = TodoSerializer(todos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 2. Create
    def post(self, request, *args, **kwargs):
        '''
        Create the Todo with given todo data
        '''
        data = {
            'task': request.data.get('task'), 
            'completed': request.data.get('completed'), 
            'user': request.user.id
        }
        serializer = TodoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TodoDetailApiView(APIView):
    # add permission to check if user is authenticated
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, todo_id, user_id):
        '''
        Helper method to get the object with given todo_id, and user_id
        '''
        try:
            return Todo.objects.get(id=todo_id, user = user_id)
        except Todo.DoesNotExist:
            return None

    # 3. Retrieve
    def get(self, request, todo_id, *args, **kwargs):
        '''
        Retrieves the Todo with given todo_id
        '''
        todo_instance = self.get_object(todo_id, request.user.id)
        if not todo_instance:
            return Response(
                {"res": "Object with todo id does not exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TodoSerializer(todo_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 4. Update
    def put(self, request, todo_id, *args, **kwargs):
        '''
        Updates the todo item with given todo_id if exists
        '''
        todo_instance = self.get_object(todo_id, request.user.id)
        if not todo_instance:
            return Response(
                {"res": "Object with todo id does not exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        data = {
            'task': request.data.get('task'), 
            'completed': request.data.get('completed'), 
            'user': request.user.id
        }
        serializer = TodoSerializer(instance = todo_instance, data=data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 5. Delete
    def delete(self, request, todo_id, *args, **kwargs):
        '''
        Deletes the todo item with given todo_id if exists
        '''
        todo_instance = self.get_object(todo_id, request.user.id)
        if not todo_instance:
            return Response(
                {"res": "Object with todo id does not exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        todo_instance.delete()
        return Response(
            {"res": "Object deleted!"},
            status=status.HTTP_200_OK
        )


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Tenant.objects.none()
        # SuperAdmin or Platform Admin can see all tenants
        if user.is_superuser or (user.is_staff and in_group(user, "Admin")):
            return Tenant.objects.all()
        # Tenant Owner can only see their own tenant
        if getattr(user, "role", None) == user.Roles.TENANT_OWNER and user.tenant_id:
            return Tenant.objects.filter(id=user.tenant_id)
        # Others: no access
        return Tenant.objects.none()

    def get_permissions(self):
        if self.action in ["list", "create", "destroy"]:
            return [IsSuperAdminOrPlatformAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or (user.is_staff and in_group(user, "Admin"))):
            raise PermissionDenied("Only SuperAdmin or Platform Admin can create tenants.")
        serializer.save()

    @decorators.action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        """Get or update the current user's tenant (TenantOwner convenience)."""
        user = request.user
        if not (getattr(user, "role", None) == user.Roles.TENANT_OWNER and user.tenant_id):
            raise PermissionDenied("Only TenantOwner with a tenant can access this endpoint.")
        tenant = Tenant.objects.get(id=user.tenant_id)
        if request.method.lower() == "get":
            return Response(TenantSerializer(tenant).data)
        serializer = TenantSerializer(instance=tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related("tenant")
    permission_classes = [permissions.IsAuthenticated, CanManageTenantUsers]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        # SuperAdmin and Platform Admin can manage all users
        if user.is_superuser or (user.is_staff and in_group(user, "Admin")):
            return User.objects.all().select_related("tenant")
        # TenantOwner: only users in their tenant
        if getattr(user, "role", None) == user.Roles.TENANT_OWNER and user.tenant_id:
            return User.objects.filter(tenant_id=user.tenant_id).select_related("tenant")
        # Subscribers: no access by default
        return User.objects.none()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return UserWriteSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, "role", None) == user.Roles.TENANT_OWNER:
            # Force tenant to current user's tenant
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        # Tenant owners cannot move users to a different tenant
        if getattr(user, "role", None) == user.Roles.TENANT_OWNER:
            if instance.tenant_id != user.tenant_id:
                raise PermissionDenied("TenantOwner cannot manage users outside their tenant.")
        serializer.save()

    @decorators.action(detail=True, methods=["post"], url_path="assign-role")
    def assign_role(self, request, pk=None):
        target = self.get_object()
        serializer = RoleAssignmentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        new_role = serializer.validated_data["role"]
        actor = request.user

        if getattr(actor, "role", None) == actor.Roles.TENANT_OWNER:
            if target.tenant_id != actor.tenant_id:
                raise PermissionDenied("TenantOwner cannot manage users outside their tenant.")
        # Apply role; model save() will sync flags; signals will sync groups
        old_role = target.role
        target.role = new_role
        # avoid duplicate auto audit from signals
        setattr(target, "_skip_auto_audit", True)
        target.save()
        AuditLog.objects.create(
            actor=actor,
            target=target,
            action=AuditLog.Actions.ROLE_CHANGED,
            details=f"role changed from {old_role} to {new_role}",
        )
        return Response({"status": "role updated", "role": target.role}, status=200)

    @decorators.action(detail=True, methods=["post"], url_path="set-password")
    def set_password(self, request, pk=None):
        target = self.get_object()
        serializer = PasswordSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target.set_password(serializer.validated_data["new_password1"])
        target.password_updated = timezone.now()
        # avoid duplicate auto audit from signals
        setattr(target, "_skip_auto_audit", True)
        target.save()
        AuditLog.objects.create(
            actor=request.user,
            target=target,
            action=AuditLog.Actions.PASSWORD_RESET,
            details="password updated via API",
        )
        return Response({"status": "password updated"}, status=200)

    @decorators.action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        target = self.get_object()
        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_active = serializer.validated_data["is_active"]
        old_active = target.is_active
        target.is_active = new_active
        # avoid duplicate auto audit from signals
        setattr(target, "_skip_auto_audit", True)
        target.save()
        AuditLog.objects.create(
            actor=request.user,
            target=target,
            action=AuditLog.Actions.ACTIVATION_CHANGED,
            details=f"is_active changed from {old_active} to {new_active}",
        )
        return Response({"status": "activation updated", "is_active": target.is_active}, status=200)