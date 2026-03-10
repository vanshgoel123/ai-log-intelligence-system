import time
import random
import uuid
from datetime import datetime
import os

LOG_FILE = os.getenv("LOG_FILE", "/logs/app.log")   # use env var, absolute path

services = ["backend", "nginx", "database"]

info_messages = [
    "User login success",
    "Request completed",
    "Cache hit"
]

warn_messages = [
    "Memory usage high",
    "Slow response detected"
]

error_messages = [
    "Database connection failed",
    "Timeout contacting service",
    "Internal server error"
]


def generate_log():

    level = random.choices(
        ["INFO", "WARN", "ERROR"],
        weights=[70, 20, 10]
    )[0]

    if level == "INFO":
        msg = random.choice(info_messages)

    elif level == "WARN":
        msg = random.choice(warn_messages)

    else:
        msg = random.choice(error_messages)

    service = random.choice(services)

    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    request_id = str(uuid.uuid4())[:8]

    return f"{timestamp} service={service} level={level} request_id={request_id} message=\"{msg}\""


while True:

    log_line = generate_log()

    print(log_line)

    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

    time.sleep(random.uniform(0.5, 2))