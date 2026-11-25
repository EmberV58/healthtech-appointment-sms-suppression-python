from datetime import datetime, timezone

from src.appointment_notifications import (
    Appointment,
    AppointmentNotificationService,
    DeliveryDecision,
)


class RecordingSender:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def send(self, appointment: Appointment, body: str) -> str:
        self.calls.append(body)
        return "msg-204"


def test_opted_out_appointment_is_suppressed_before_sender() -> None:
    sender = RecordingSender()
    service = AppointmentNotificationService(sender)
    appointment = Appointment(
        "visit-204",
        "+15550104",
        "Mina",
        datetime(2026, 11, 4, 15, 30, tzinfo=timezone.utc),
        opted_out=True,
    )

    result = service.send_reminder(appointment)

    assert result.decision is DeliveryDecision.SUPPRESSED
    assert result.message_id is None
    assert sender.calls == []


def test_allowed_appointment_returns_provider_identifier() -> None:
    sender = RecordingSender()
    appointment = Appointment(
        "visit-205",
        "+15550105",
        "Noah",
        datetime(2026, 11, 4, 15, 30, tzinfo=timezone.utc),
    )

    result = AppointmentNotificationService(sender).send_reminder(appointment)

    assert result.decision is DeliveryDecision.SENT
    assert result.message_id == "msg-204"
    assert len(sender.calls) == 1
