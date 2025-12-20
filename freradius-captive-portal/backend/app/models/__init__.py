# Models package initialization file
# Import tous les modèles pour s'assurer qu'ils sont chargés par SQLAlchemy

from app.models.radius import RadCheck, RadReply, RadUserGroup, RadGroupReply
from app.models.accounting import RadAcct, NASInfo
