import os

TARGET_URLS = os.getenv(
    "TARGET_URLS",
    "https://scholar.iiitnr.ac.in/login"
).split(",")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 5))