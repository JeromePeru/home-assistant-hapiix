"""Constants for the Hapiix integration."""

from datetime import timedelta

DOMAIN = "hapiix"
PLATFORMS = ["button", "sensor"]

CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"

API_BASE_URL = "https://api.hapiix.io/occupant/"
UPDATE_INTERVAL = timedelta(minutes=5)

