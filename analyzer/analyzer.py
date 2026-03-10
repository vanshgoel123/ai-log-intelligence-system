import os
import time
import requests
from datetime import datetime, timedelta
from collections import Counter
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
load_dotenv()   # loads .env when running locally

# ENVIRONMENT VARIABLES
ELASTIC_HOST = os.getenv("ELASTIC_HOST", "http://elasticsearch:9200")
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT", "OPS")

CHECK_INTERVAL = 30
DEDUP_TIME = 600   # 10 minutes


# GLOBAL MEMORY
incident_cache = {}

previous_error_count = None   

# SERVICE HEALTH TRACKING
service_error_tracker = {}

SERVICE_DOWN_THRESHOLD = 30

# CONNECT ELASTICSEARCH
def connect_elasticsearch():
    while True:
        try:
            print("Connecting to Elasticsearch...")
            es = Elasticsearch(ELASTIC_HOST)
            es.info()
            print("Connected!")
            return es
        except Exception as e:
            print("Elasticsearch not ready:", e)
        time.sleep(5)

# PARSE SERVICE NAME
def parse_service(message):
    service = "unknown"
    if "service=" in message:
        try:
            service = message.split("service=")[1].split(" ")[0]
        except:
            pass
    return service


# SERVICE DOWN DETECTION
def detect_service_downtime(service, count):
    if service not in service_error_tracker:
        service_error_tracker[service] = 0
    service_error_tracker[service] += count

    if service_error_tracker[service] >= SERVICE_DOWN_THRESHOLD:
        summary = f"CRITICAL: {service} service appears DOWN ({service_error_tracker[service]} errors)"

        if should_create_ticket(summary):
            print("SERVICE DOWN DETECTED:", summary)
            create_jira_ticket(summary)
            incident_cache[summary] = datetime.now()

        service_error_tracker[service] = 0

# NORMALIZE ERROR (CLUSTERING)
def normalize_error(msg):
    msg = msg.lower()

    if "database connection failed" in msg:
        return "database connection failure"

    if "timeout" in msg:
        return "network timeout"

    if "internal server error" in msg:
        return "backend internal error"

    return msg


# SEVERITY DETECTION
def get_severity(count):
    if count >= 100:
        return "CRITICAL"
    if count >= 50:
        return "HIGH"
    if count >= 10:
        return "WARNING"
    return None


# JIRA TICKET CREATION
def create_jira_ticket(summary):
    print("Creating Jira ticket...")
    url = f"{JIRA_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT},
            "summary": summary,
            "issuetype": {"name": "Bug"},
            "description": summary
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            auth=(JIRA_EMAIL, JIRA_TOKEN)
        )
        print("Jira response:", response.status_code)
    except Exception as e:
        print("Jira error:", e)

# DUPLICATE INCIDENT CHECK
def should_create_ticket(error):
    if error not in incident_cache:
        return True

    last_time = incident_cache[error]
    if datetime.now() - last_time > timedelta(seconds=DEDUP_TIME):
        return True

    return False


# MAIN ANALYZER LOOP
print("Analyzer starting...")
es = connect_elasticsearch()
while True:
    try:
        print("Fetching logs...")
        res = es.search(
            index="filebeat-*",
            query={
                "range": {
                    "@timestamp": {
                        "gte": "now-5m"
                    }
                }
            },
            size=500
        )
        errors = []
        for hit in res["hits"]["hits"]:
            msg=hit["_source"]["message"]

            if "ERROR" in msg:
                normalized = normalize_error(msg)
                service = parse_service(msg)
                errors.append((service, normalized))

        print("Total errors:", len(errors))

        # ANOMALY DETECTION
        if previous_error_count is not None and len(errors) > previous_error_count * 5 and len(errors) > 20:
            summary = f"ANOMALY: sudden error spike detected ({len(errors)} errors)"
            if should_create_ticket(summary):
                print(summary)
                create_jira_ticket(summary)
                incident_cache[summary] = datetime.now()
        previous_error_count = max(len(errors), 1)


        # INCIDENT GROUPING
        error_counts = Counter(errors)
        for (service, error), count in error_counts.items():
            detect_service_downtime(service, count)
            severity = get_severity(count)

            if severity:
                incident_key = f"{service}:{error}"

                if should_create_ticket(incident_key):
                    summary = f"{severity}: {service} service - {error} ({count} times)"
                    print("INCIDENT DETECTED:", summary)
                    create_jira_ticket(summary)
                    incident_cache[incident_key] = datetime.now()

                else:
                    print("Duplicate incident skipped:", incident_key)

    except Exception as e:
        print("Analyzer error:", e)

    time.sleep(CHECK_INTERVAL)