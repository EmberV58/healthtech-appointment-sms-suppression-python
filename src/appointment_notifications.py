from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol


@dataclass(frozen=True)
class Appointment:
    appointment_id: str
    patient_phone: str
    patient_name: str
    starts_at: datetime
    opted_out: bool = False


class DeliveryDecision(str, Enum):
    SENT = "sent"
    SUPPRESSED = "suppressed"


@dataclass(frozen=True)
class NotificationResult:
    appointment_id: str
    decision: DeliveryDecision
    message_id: str | None = None


class SmsSender(Protocol):
    def send(self, appointment: Appointment, body: str) -> str:
        """Return the provider message identifier."""


class AppointmentNotificationService:
    def __init__(self, sender: SmsSender) -> None:
        self._sender = sender
        self._suppressed_phones: set[str] = set()

    def record_opt_out(self, phone: str) -> None:
        self._suppressed_phones.add(phone)

    def send_reminder(self, appointment: Appointment) -> NotificationResult:
        if appointment.opted_out:
            self.record_opt_out(appointment.patient_phone)
        if appointment.patient_phone in self._suppressed_phones:
            return NotificationResult(appointment.appointment_id, DeliveryDecision.SUPPRESSED)

        body = (
            f"Hi {appointment.patient_name}, your appointment is "
            f"scheduled for {appointment.starts_at.isoformat()}."
        )
        message_id = self._sender.send(appointment, body)
        return NotificationResult(appointment.appointment_id, DeliveryDecision.SENT, message_id)
