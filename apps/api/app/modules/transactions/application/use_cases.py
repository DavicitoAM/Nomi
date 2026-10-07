from app.modules.commitments.application.use_cases import present
from app.shared.errors import DomainError
from app.shared.ports import UnitOfWork


def reverse_payment(uow: UnitOfWork, context, key, transaction_id, expected_version, note=None):
    command = dict(transaction_id=transaction_id, expected_version=expected_version, note=note)
    with uow:
        original = uow.transactions.original(transaction_id)
        try:
            current = uow.commitments.get(context.workspace_id, original["commitment_id"])
        except DomainError as error:
            if error.status == 404:
                raise DomainError(
                    "TRANSACTION_NOT_FOUND", "No encontramos ese movimiento.", 404
                ) from None
            raise
        record_id, previous = uow.effects.reserve(context, "ReversePayment", key, command)
        if previous is not None:
            return previous
        if original["type"] != "payment":
            raise DomainError("NOT_A_PAYMENT", "Sólo puedes revertir un abono.", 409)
        if (
            original["currency_code"] != current.currency_code
            or current.currency_code != context.currency
        ):
            raise DomainError("CURRENCY_MISMATCH", "La moneda del movimiento no coincide.", 409)
        if uow.transactions.is_reversed(transaction_id):
            raise DomainError("PAYMENT_ALREADY_REVERSED", "Este abono ya fue revertido.", 409)
        updated = current.reverse_payment(original["amount_minor"], expected_version)
        uow.commitments.save_payment(updated, expected_version)
        transaction = uow.transactions.reversal(updated, original, note, context.user_id)
        uow.audit.record(
            context.workspace_id,
            context.user_id,
            "transaction.payment_reversed",
            "transaction",
            transaction["id"],
        )
        uow.effects.emit(context.workspace_id, "PaymentReversed", transaction["id"])
        response = {"transaction": transaction, "commitment": present(updated, context.timezone)}
        uow.effects.complete(record_id, response, "transaction", transaction["id"])
        uow.commit()
        return response


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
