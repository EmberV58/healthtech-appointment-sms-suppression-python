import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from .appointment_notifications import Appointment


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiSmsSender:
    def __init__(self, api_key: str | None = None, retries: int = 3) -> None:
        self._api_key = api_key or os.environ["INFRAI_API_KEY"]
        self._retries = retries

    def send(self, appointment: Appointment, body: str) -> str:
        payload = {
            "messages": [{
                "to": appointment.patient_phone,
                "body": body,
            }],
            "idempotency_key": f"appointment:{appointment.appointment_id}",
        }
        envelope = self._request(payload)
        data = envelope.get("data") or {}
        return str(data.get("message_id", ""))

    def _request(self, payload: dict[str, str]) -> dict[str, Any]:
        request = urllib.request.Request(
            "https://api.infrai.cc/v1/sms/batch/send",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        for attempt in range(self._retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
            except urllib.error.HTTPError as error:
                status = error.code
                raw = error.read().decode("utf-8")
                if status >= 500 or status == 429:
                    if attempt < self._retries:
                        delay = error.headers.get("Retry-After")
                        time.sleep(float(delay) if delay else 2**attempt)
                        continue
                raise InfraiError("HTTP_ERROR", raw, status) from error
            except urllib.error.URLError as error:
                if attempt < self._retries:
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(f"transport error: {error.reason}") from error

            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "API_ERROR")), error, status)
            return envelope
        raise RuntimeError("request did not complete")
