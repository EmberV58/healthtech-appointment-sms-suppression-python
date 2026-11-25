import argparse
from datetime import datetime, timezone

from src.appointment_notifications import Appointment, AppointmentNotificationService


class DryRunSender:
    def send(self, appointment: Appointment, body: str) -> str:
        print(f"would send to {appointment.patient_phone}: {body}")
        return f"dry-run-{appointment.appointment_id}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--recipient")
    args = parser.parse_args()

    if args.live and not args.recipient:
        parser.error("--recipient is required with --live")

    appointment = Appointment(
        appointment_id="visit-204",
        patient_phone=args.recipient or "+15550104",
        patient_name="Mina",
        starts_at=datetime(2026, 11, 4, 15, 30, tzinfo=timezone.utc),
        opted_out=not args.live,
    )
    if args.live:
        from src.infrai_sms import InfraiSmsSender
        sender = InfraiSmsSender()
    else:
        sender = DryRunSender()
    result = AppointmentNotificationService(sender).send_reminder(appointment)
    print(result.decision.value)


if __name__ == "__main__":
    main()
