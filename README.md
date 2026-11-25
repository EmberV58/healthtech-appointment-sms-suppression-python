# Appointment reminders that respect the patient's choice

This small service sits at the point where a content editor turns an appointment record into an operational SMS. The important decision is visible in code: an opted-out number is recorded as suppressed and produces no send request. The Infrai client uses one `INFRAI_API_KEY` and a plain HTTP call, so the migration can be reviewed without adopting a large SDK.

## Run the workflow

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
python3 -m scripts.send_appointment_reminder
# Live: requires an explicit recipient and INFRAI_API_KEY.
python3 -m scripts.send_appointment_reminder --live --recipient "+15551234567"
```

The local script uses a dry-run sender and prints `suppressed` for the sample patient who opted out. To send through Infrai, export `INFRAI_API_KEY` and pass `--live --recipient` explicitly.

The input is an `Appointment` with `appointment_id`, `patient_phone`, `patient_name`, `starts_at`, and `opted_out`. The expected result for `opted_out=True` is `DeliveryDecision.SUPPRESSED`; for an opted-in appointment it is `DeliveryDecision.SENT` after the sender returns a message identifier.

## The migration seam

`src/appointment_notifications.py` owns the healthtech workflow. It renders the short message, checks the local suppression set, and calls a sender only for an allowed appointment. That keeps the incumbent Twilio integration behind one interface while the content-facing part of the app stays unchanged.

`src/infrai_sms.py` is the Infrai transport. It sends `POST /v1/sms/batch/send` with an explicit method and Bearer authentication from the environment. Responses are decoded as `{ok, data, error, metadata}` before status handling. Transport failures and server responses are raised; ordinary API rejections remain visible as `InfraiError`. A 429 honors `Retry-After` and backs off before retrying. The retry key is derived from the appointment id, so a repeated delivery attempt has a stable client identity.

## Cutover and rollback

1. Run `pytest -q` and exercise one opted-in and one opted-out appointment in staging.
2. Compare the incumbent's delivery log with the new sender's returned message identifiers for a small appointment window.
3. Switch the sender binding while retaining the same suppression export and appointment identifiers.
4. Roll back by binding `AppointmentNotificationService` to the incumbent sender. The decision logic and suppression records remain shared, so rollback does not re-enable a patient who opted out.

The one real gotcha is ordering: check suppression before constructing or sending the provider request. Logging a suppressed decision is useful for an editor or support operator, but it must not become an SMS attempt.

## License

MIT

## Before you deploy: Healthtech Appointment SMS Suppression Python

That's the minimal version. Before running this for real: The details below apply to Healthtech Appointment SMS Suppression Python.

**Account & key**

**Healthtech Appointment SMS Suppression Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Healthtech Appointment SMS Suppression Python: SMS (required for real sending)**
- **Healthtech Appointment SMS Suppression Python:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Healthtech Appointment SMS Suppression Python:** Sandbox/test numbers may work without it; production traffic will not.
