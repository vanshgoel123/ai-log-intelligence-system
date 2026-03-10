import requests
import time
from datetime import datetime
from config import TARGET_URLS, CHECK_INTERVAL, REQUEST_TIMEOUT

LOG_FILE = "/logs/health.log"


def log(level, message):

    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    log_line = f"{timestamp} service=health-check level={level} message=\"{message}\""

    print(log_line)

    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def check_website(url):

    try:

        r = requests.get(url, timeout=REQUEST_TIMEOUT, verify=False)

        if r.status_code == 200:

            log("INFO", f"{url} healthy status={r.status_code}")

        elif r.status_code >= 500:

            log("ERROR", f"{url} server_error status={r.status_code}")

        else:

            log("WARN", f"{url} unexpected_status status={r.status_code}")

    except Exception as e:

        log("ERROR", f"{url} unreachable error={str(e)}")


def main():

    log("INFO", "Health monitoring started")

    while True:

        for url in TARGET_URLS:
            check_website(url)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()