export interface Tenant {
  id: string
  slug: string
  name: string
}

export interface AuthMe {
  id: string
  email: string
  name: string
  roles: string[]
  tenants: Tenant[]
  defaultTenant: string
}
