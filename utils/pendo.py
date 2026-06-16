import json
import logging
import time
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

PENDO_TRACK_URL = "https://data.pendo.io/data/track"
PENDO_INTEGRATION_KEY = "ad01b090-1492-468a-834d-0476b6761356"


def track(event, properties=None):
    """Send a server-side track event to Pendo.

    Failures are logged but never raised so tracking cannot break app flow.
    """
    payload = {
        "type": "track",
        "event": event,
        "visitorId": "anonymous",
        "accountId": "anonymous",
        "timestamp": int(time.time() * 1000),
    }
    if properties:
        payload["properties"] = properties

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            PENDO_TRACK_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-pendo-integration-key": PENDO_INTEGRATION_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
    except Exception:
        logger.debug("Failed to send Pendo track event %s", event, exc_info=True)
