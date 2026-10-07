from alembic import context

from app.core.database import Base, engine
from app.modules.audit.infrastructure import models as audit
from app.modules.commitments.infrastructure import models as commitments
from app.modules.contacts.infrastructure import models as contacts
from app.modules.identity.infrastructure import models as identity
from app.modules.transactions.infrastructure import models as transactions
from app.modules.workspaces.infrastructure import models as workspaces
from app.shared import models as shared

assert all((audit, commitments, contacts, identity, transactions, workspaces, shared))

if context.is_offline_mode():
    context.configure(url=str(engine.url), target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
