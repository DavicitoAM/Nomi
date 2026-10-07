from app.shared.ports import UnitOfWork


def create_contact(uow: UnitOfWork, context, name, email=None, phone=None, notes=None):
    with uow:
        result = uow.contacts.create(context.workspace_id, name, email, phone, notes)
        uow.audit.record(
            context.workspace_id, context.user_id, "contact.created", "contact", result["id"]
        )
        uow.commit()
        return result


def get_contact(uow: UnitOfWork, context, contact_id):
    with uow:
        result = uow.contacts.get(context.workspace_id, contact_id)
        result["summary"] = uow.commitments.contact_summary(context.workspace_id, contact_id)
        return result


def edit_contact(uow: UnitOfWork, context, contact_id, expected_updated_at, changes):
    with uow:
        result = uow.contacts.edit(context.workspace_id, contact_id, expected_updated_at, changes)
        uow.audit.record(
            context.workspace_id, context.user_id, "contact.updated", "contact", contact_id
        )
        uow.commit()
        return result


def archive_contact(uow: UnitOfWork, context, contact_id, expected_updated_at, archived):
    with uow:
        result, changed = uow.contacts.archive(
            context.workspace_id, contact_id, expected_updated_at, archived
        )
        if changed:
            action = "contact.archived" if archived else "contact.restored"
            uow.audit.record(context.workspace_id, context.user_id, action, "contact", contact_id)
            uow.effects.emit(
                context.workspace_id,
                "ContactArchived" if archived else "ContactRestored",
                contact_id,
            )
        uow.commit()
        return result
