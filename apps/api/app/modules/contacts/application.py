from app.shared.ports import UnitOfWork


def create_contact(uow: UnitOfWork, context, name, email=None, phone=None):
    with uow:
        result = uow.contacts.create(context.workspace_id, name, email, phone)
        uow.audit.record(
            context.workspace_id, context.user_id, "contact.created", "contact", result["id"]
        )
        uow.commit()
        return result
