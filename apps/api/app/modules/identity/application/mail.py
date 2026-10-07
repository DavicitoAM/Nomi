from uuid import UUID

from app.shared.ports import UnitOfWork

PURPOSES = {
    "EmailVerificationRequested": "verify",
    "PasswordResetRequested": "reset",
    "PasswordChanged": "changed",
}


def process_next_mail(uow: UnitOfWork, transport):
    # Persist a lease and any legacy-token conversion before touching an external system.
    with uow:
        uow.identity.clear_expired_delivery_secrets()
        event = uow.effects.claim_mail()
        if event is None:
            uow.commit()
            return False
        purpose = PURPOSES[event["event_type"]]
        resource_id = UUID(event["resource_id"])
        if purpose != "changed":
            resource_id = uow.identity.resolve_mail_resource(resource_id, purpose)
            if resource_id is None:
                uow.effects.finish_mail(event["id"], event["attempts"])
                uow.commit()
                return True
            uow.effects.prepare_mail_resource(event["id"], event["attempts"], resource_id)
        event_id, attempt = event["id"], event["attempts"]
        uow.commit()
    try:
        with uow:
            if purpose == "changed":
                profile = uow.identity.profile(resource_id)
                # Change notifications intentionally have no token.
                message = {
                    "recipient": profile["email"],
                    "purpose": purpose,
                    "token": None,  # nosec B105
                    "expires_at": None,
                }
            else:
                message = uow.identity.mail_data(resource_id, purpose)
        if message:
            transport.send(str(event_id), message)
        with uow:
            if uow.effects.finish_mail(event_id, attempt) and purpose != "changed":
                uow.identity.clear_delivery_secret(resource_id, purpose)
            uow.commit()
    except Exception:
        # Never persist exception messages: SMTP providers can include addresses or credentials.
        with uow:
            uow.effects.finish_mail(event_id, attempt, "MAIL_DELIVERY_FAILED")
            uow.commit()
    return True
