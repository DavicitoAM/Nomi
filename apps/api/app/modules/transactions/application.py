from app.modules.commitments.application import present
from app.shared.ports import UnitOfWork


def register_payment(
    uow: UnitOfWork,
    context,
    key,
    commitment_id,
    amount_minor,
    expected_version,
    occurred_at,
    note=None,
    type="payment",
):
    command = dict(
        commitment_id=commitment_id,
        amount_minor=amount_minor,
        expected_version=expected_version,
        occurred_at=occurred_at,
        note=note,
        type=type,
    )
    with uow:
        # Authorization still happens on every replay; version validation follows deduplication.
        current = uow.commitments.get(context.workspace_id, commitment_id)
        record_id, previous = uow.effects.reserve(context, "RegisterPayment", key, command)
        if previous is not None:
            return previous
        updated = current.pay(amount_minor, expected_version)
        uow.commitments.save_payment(updated, expected_version)
        transaction = uow.transactions.payment(
            updated, amount_minor, occurred_at, note, context.user_id
        )
        uow.audit.record(
            context.workspace_id,
            context.user_id,
            "transaction.payment_registered",
            "transaction",
            transaction["id"],
        )
        uow.effects.emit(context.workspace_id, "PaymentRegistered", transaction["id"])
        if updated.balance_minor == 0:
            uow.effects.emit(context.workspace_id, "CommitmentFullyPaid", updated.id)
        response = {"transaction": transaction, "commitment": present(updated, context.timezone)}
        uow.effects.complete(record_id, response, "transaction", transaction["id"])
        uow.commit()
        return response
