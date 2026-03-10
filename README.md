# AI Log Intelligence and Automated Incident Ticketing System

A final-year engineering project that automatically monitors application and infrastructure logs, detects repeated errors, identifies patterns, determines probable root causes, assesses severity, and automatically generates incident tickets in Jira.

## 🎯 Project Overview

This system provides an **enterprise-grade observability solution** for detecting and responding to application failures automatically. It combines:
- Centralized log aggregation via Filebeat
- Full-text log indexing with Elasticsearch
- Intelligent error clustering and anomaly detection
- Automatic Jira ticket creation for incident management
- Health monitoring for critical endpoints

**Perfect for:**
- Multi-service applications on college servers
- Student projects requiring production-like monitoring
- Learning DevOps, SRE, and observability patterns

---

## 🏗️ System Architecture

```
Application Logs + Health Checks
    ↓
┌─────────────────────────────────┐
│   Filebeat (Log Shipper)        │  Monitors /logs/*.log files
└─────────────────┬───────────────┘
                  ↓
┌─────────────────────────────────┐
│   Elasticsearch (Log Storage)   │  Indexes and stores logs
└─────────────────┬───────────────┘
                  ↓
        ┌─────────┴────────────┐
        ↓                      ↓
   ┌────────────┐      ┌────────────┐
   │  Kibana    │      │  Analyzer  │
   │ Dashboard  │      │  Service   │
   └────────────┘      └─────┬──────┘
                              ↓
                    ┌─────────────────┐
                    │  Jira API       │
                    │  Tickets        │
                    └─────────────────┘
```

---

## 📁 Project Structure

```
ai-log-intelligence-system/
├── .env                          # Environment variables (SENSITIVE - never commit)
├── .env.example                  # Template for .env
├── docker-compose.yml            # Docker Compose orchestration
├── setup.sh                       # Setup script
├── README.md                      # This file
│
├── analyzer/                      # Python Log Analyzer Service
│   ├── analyzer.py              # Main analyzer logic
│   ├── Dockerfile               # Container image definition
│   └── requirements.txt          # Python dependencies
│
├── filebeat/                      # Filebeat Configuration
│   └── filebeat.yml             # Log shipper config
│
├── health-check/                  # Website Health Monitor
│   ├── health-checker.py        # Health check script
│   ├── config.py                # Config loader
│   ├── Dockerfile               # Container image
│   └── requirements.txt          # Python dependencies
│
├── log-generator/                 # Test Log Generator
│   └── generate_logs.py         # Generates fake logs for testing
│
└── logs/                          # Log storage (volume)
    ├── app.log                  # Application logs
    └── health.log               # Health check logs
```

---

## 🔧 File-by-File Explanation

### 1. **docker-compose.yml** — Orchestration
Defines and manages 6 interconnected Docker services:

| Service | Port | Purpose |
|---------|------|---------|
| `elasticsearch` | 9200 | Log indexing & storage (8.12.0) |
| `kibana` | 5601 | Log visualization dashboard |
| `filebeat` | — | Log shipper that reads `logs/` directory |
| `log-generator` | — | Generates fake application logs |
| `health-check` | — | Monitors target URLs and logs results |
| `analyzer` | — | Error detection & Jira ticket creation |

**Key Features:**
- Uses shared volume `logs/` for log files
- Environment variables loaded from `.env`
- Elasticsearch data persists in `es_data` volume
- Services depend on Elasticsearch startup

### 2. **analyzer/analyzer.py** — The Brain
The core intelligence service that:

**Reads logs every 30 seconds:**
```python
res = es.search(
    index="filebeat-*",
    query={"range": {"@timestamp": {"gte": "now-5m"}}},
    size=500
)
```

**Processes logs through 4 stages:**

#### Stage 1: Normalization (Error Clustering)
Converts different error messages into categories:
```python
"Database connection failed" → "database connection failure"
"Timeout contacting service" → "network timeout"
"Internal server error" → "backend internal error"
```

#### Stage 2: Service Detection
Extracts service name from log:
```
2026-03-10T12:00:00Z service=backend level=ERROR message="..."
                          ↑
                     Parsed here
```

#### Stage 3: Severity Classification
```python
≥100 errors in 5 min  → CRITICAL
≥50 errors in 5 min   → HIGH
≥10 errors in 5 min   → WARNING
<10 errors            → INFO (no ticket)
```

#### Stage 4: Duplicate Prevention
Caches incident summaries with 10-minute dedup window:
```python
incident_cache = {
    "WARNING: backend - database failure": datetime(2026-03-10 12:00)
}
# Won't create duplicate ticket for 10 minutes (DEDUP_TIME=600)
```

**Anomaly Detection:**
If error count suddenly spikes 5x higher:
```python
if len(errors) > previous_error_count * 5 and len(errors) > 20:
    # Create "ANOMALY: sudden error spike" ticket
```

**Jira Ticket Creation:**
Sends formatted incident to Jira REST API v3:
```python
POST /rest/api/3/issue
{
    "fields": {
        "project": {"key": "OPS"},
        "summary": "WARNING: backend service - database connection failure (10 times)",
        "issuetype": {"name": "Bug"}
    }
}
```

**Configuration (from `.env`):**
```env
ELASTIC_HOST=http://elasticsearch:9200
JIRA_URL=https://hpvictusvansh.atlassian.net
JIRA_EMAIL=hpvictusvansh@gmail.com
JIRA_TOKEN=your_api_token
JIRA_PROJECT=OPS
CHECK_INTERVAL=30          # seconds between analysis runs
DEDUP_TIME=600             # seconds before same incident can be created again
```

### 3. **health-check/health-checker.py** — Endpoint Monitor
Periodically pings target URLs and logs health status:

```python
def check_website(url):
    r = requests.get(url, timeout=5)
    if r.status_code == 200:
        log("INFO", f"{url} healthy status={r.status_code}")
    elif r.status_code >= 500:
        log("ERROR", f"{url} server_error status={r.status_code}")
```

**Features:**
- Checks every 30 seconds (configurable)
- Logs results in same format as app logs
- Filebeat picks up health logs and ships to ES
- Analyzer can detect when monitored endpoints fail

**Configuration (from `.env`):**
```env
TARGET_URLS=https://scholar.iiitnr.ac.in/login
CHECK_INTERVAL=30
REQUEST_TIMEOUT=5
```

### 4. **health-check/config.py** — Configuration Loader
Reads health-check settings from environment variables:
```python
TARGET_URLS = os.getenv("TARGET_URLS", "https://scholar.iiitnr.ac.in/login").split(",")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 5))
```

Supports multiple URLs (comma-separated):
```env
TARGET_URLS=https://site1.com,https://site2.com,https://site3.com
```

### 5. **log-generator/generate_logs.py** — Test Data
Generates synthetic application logs for testing:

**Simulates 3 services:** `backend`, `nginx`, `database`

**Log distribution:**
- 70% INFO (normal operations)
- 20% WARN (non-critical issues)
- 10% ERROR (failures that trigger incidents)

**Example output:**
```
2026-03-10T12:05:30Z service=backend level=INFO request_id=a1b2c3d4 message="User login success"
2026-03-10T12:05:31Z service=database level=ERROR request_id=e5f6g7h8 message="Database connection failed"
2026-03-10T12:05:32Z service=nginx level=WARN request_id=i9j0k1l2 message="Memory usage high"
```

**Configuration:**
```python
LOG_FILE = os.getenv("LOG_FILE", "/logs/app.log")   # Where logs are written
# Generates every 0.5-2 seconds (random interval)
```

### 6. **filebeat/filebeat.yml** — Log Shipper Configuration
Instructs Filebeat what logs to ship and where:

```yaml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /logs/*.log              # Watch all .log files in /logs

output.elasticsearch:
  hosts: ["http://elasticsearch:9200"]

setup.kibana:
  host: "http://kibana:5601"

setup.ilm.enabled: false        # Disable index lifecycle management
```

**How it works:**
1. Watches `/logs/*.log` for new lines
2. Parses each line and adds metadata (`@timestamp`, `host`, etc.)
3. Sends to Elasticsearch for indexing
4. Updates Kibana with log schema

### 7. **.env** — Environment Variables (SENSITIVE)
Never commit this file! Contains credentials:

```env
# Elasticsearch connection
ELASTIC_HOST=http://elasticsearch:9200

# Jira API credentials
JIRA_URL=https://hpvictusvansh.atlassian.net
JIRA_EMAIL=hpvictusvansh@gmail.com
JIRA_TOKEN=your_api_token_here              # Generate from https://id.atlassian.com/manage-profile/security/api-tokens
JIRA_PROJECT=OPS                            # Your Jira project key

# Enable/disable Jira ticket creation
JIRA_ENABLED=true

# Analyzer tuning
CHECK_INTERVAL=30                           # How often to analyze logs (seconds)
DEDUP_TIME=600                              # Prevent duplicate tickets for 10 minutes
ERROR_THRESHOLD_LOW=10                      # WARNING severity threshold
ERROR_THRESHOLD_MEDIUM=50                   # HIGH severity threshold
ERROR_THRESHOLD_CRITICAL=100                # CRITICAL severity threshold

# Health checker
TARGET_URLS=https://scholar.iiitnr.ac.in/login
REQUEST_TIMEOUT=5                           # Timeout for health checks
```

### 8. **.env.example** — Template for Developers
Safe version without real credentials:
```env
JIRA_TOKEN=your_token_here      # Placeholder
JIRA_ENABLED=false              # Default to disabled for dev
```

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose installed
- Jira account with API token (optional, but needed for auto-ticketing)
- 2GB free disk space for Elasticsearch

### Step 1: Clone and Setup
```bash
cd /home/vansh/Desktop/MINOR\ 6TH\ SEM/ai-log-intelligence-system
cp .env.example .env              # Create .env from template
```

### Step 2: Configure .env
Edit `.env` with your Jira credentials:

```bash
# Get your Jira API token from:
# https://id.atlassian.com/manage-profile/security/api-tokens

JIRA_URL=https://your-instance.atlassian.net
JIRA_EMAIL=your-email@gmail.com
JIRA_TOKEN=your_new_api_token
JIRA_PROJECT=YOUR_PROJECT_KEY
JIRA_ENABLED=true
```

**For development (Jira disabled):**
```env
JIRA_ENABLED=false         # Won't create real tickets
```

### Step 3: Start the System
```bash
docker compose up --build
```

**Expected startup output:**
```
[+] Building 15.2s (8/8) FINISHED
[+] Running 6/6
 ✓ Container elasticsearch      Started
 ✓ Container filebeat           Started
 ✓ Container log-generator      Started
 ✓ Container kibana             Started
 ✓ Container health-check       Started
 ✓ Container analyzer           Started
```

### Step 4: Verify Everything Works
In another terminal:
```bash
# Check Elasticsearch is running
curl http://localhost:9200

# Count indexed logs
curl http://localhost:9200/filebeat-*/_count | jq .count

# View Kibana
# Open browser: http://localhost:5601
```

### Step 5: Watch Analyzer in Action
```bash
docker logs -f analyzer
```

**Expected output every 30 seconds:**
```
Analyzer starting...
Connecting to Elasticsearch...
Connected!
Fetching logs...
Total errors: 5
Fetching logs...
Total errors: 12
INCIDENT DETECTED: WARNING: backend service - database connection failure (10 times)
Creating Jira ticket...
Jira response: 201
```

---

## 📊 Data Flow Example

### Scenario: Database errors spike

**Time: T+0s**
- `log-generator` writes: `service=backend level=ERROR message="Database connection failed"` to `/logs/app.log`
- `filebeat` reads and ships to Elasticsearch
- Elasticsearch indexes with timestamp

**Time: T+30s**
- `analyzer` queries: "errors in last 5 minutes"
- Finds 15 occurrences of "Database connection failed" from backend
- Normalizes to: `("backend", "database connection failure")`
- Checks severity: 15 errors → WARNING threshold
- Not in cache: creates ticket
- **Jira Ticket Created:** "WARNING: backend service - database connection failure (15 times)"
- Caches incident for 10 minutes

**Time: T+60s**
- Analyzer runs again
- Still sees 20 errors from backend
- Same incident key in cache AND within dedup window
- **Skips duplicate ticket** ← prevents spam

**Time: T+120s (cache expires)**
- Error count is now 25
- Not in cache anymore (outside dedup window)
- **New ticket created** with updated count
- Cycle repeats

---

## 🔍 Monitoring & Debugging

### Check Logs in Kibana
1. Go to `http://localhost:5601`
2. Click **"Explore on my own"**
3. Select data view (should show `filebeat-*`)
4. View logs with fields:
   - `@timestamp` — when log occurred
   - `service` — which service
   - `level` — INFO/WARN/ERROR
   - `message` — log message

### Filter by Service
```
service: "backend"
```

### Filter by Error Level
```
level: "ERROR"
```

### Search for Specific Message
```
message: "Database connection"
```

### Check Analyzer Decisions
```bash
docker logs analyzer | grep "INCIDENT\|ANOMALY\|Duplicate"
```

### Check Elasticsearch Index
```bash
# List all indices
curl http://localhost:9200/_cat/indices

# Get index stats
curl http://localhost:9200/filebeat-*/stat

# Delete logs and start fresh
curl -X DELETE http://localhost:9200/filebeat-*
```

---

## ⚙️ Configuration Tuning

### Make Incidents More Sensitive
Decrease thresholds in `.env`:
```env
ERROR_THRESHOLD_LOW=5           # Instead of 10
ERROR_THRESHOLD_MEDIUM=25       # Instead of 50
ERROR_THRESHOLD_CRITICAL=50     # Instead of 100
```

### Make Incidents Less Frequent
Increase dedup time in `.env`:
```env
DEDUP_TIME=1800                 # 30 minutes instead of 10
```

### Check Logs More Frequently
Decrease check interval:
```env
CHECK_INTERVAL=15               # Every 15 seconds instead of 30
```
⚠️ **Warning:** Smaller intervals = more load on Elasticsearch

### Monitor More Endpoints
```env
TARGET_URLS=https://site1.com,https://site2.com,https://site3.com
```

### Disable Jira Tickets (for testing)
```env
JIRA_ENABLED=false
```
Analyzer will print "Would create ticket" instead of actually creating them.

---

## 🐛 Troubleshooting

### "Elasticsearch not ready"
**Problem:** Analyzer can't connect to ES after 60 seconds
**Solution:**
```bash
# Check if ES is running
curl http://localhost:9200

# If not responding, check container logs
docker logs elasticsearch

# Restart ES
docker restart elasticsearch
```

### "Jira response: 401"
**Problem:** Jira authentication failed
**Solution:**
1. Verify `JIRA_TOKEN` is correct (generate new token at `https://id.atlassian.com/manage-profile/security/api-tokens`)
2. Verify `JIRA_EMAIL` matches your Jira account email
3. Verify `JIRA_URL` is correct (no trailing slash)
4. Try with `JIRA_ENABLED=false` first to test other components

### "Jira response: 400"
**Problem:** Missing required fields in Jira payload
**Solution:** Ensure latest `analyzer.py` includes `description` field in ADF format

### No logs appearing in Kibana
**Problem:** Filebeat not shipping logs
**Solution:**
```bash
# Check if logs are being generated
tail -f logs/app.log

# Check if Filebeat is running
docker logs filebeat

# Restart Filebeat
docker restart filebeat
```

### "Cannot write to /logs directory"
**Problem:** Permission issue with shared volume
**Solution:**
```bash
# Create logs directory if missing
mkdir -p logs

# Give write permissions
chmod 777 logs

# Restart containers
docker compose restart
```

---

## 🎓 Learning Outcomes

This project teaches:

| Concept | Where It's Used |
|---------|---|
| **Containerization** | Docker, Dockerfile, docker-compose |
| **Microservices** | 6 independent services communicating |
| **Log Aggregation** | Filebeat → Elasticsearch pipeline |
| **Full-text Search** | Elasticsearch queries |
| **REST APIs** | Jira API integration |
| **Environment Config** | .env file management |
| **Error Detection** | Pattern recognition in logs |
| **Incident Management** | Automatic ticketing workflow |
| **Observability** | Kibana dashboards |
| **DevOps/SRE** | Production-like monitoring |

---

## 🚀 Future Enhancements

### AI/ML Integration
- Use `scikit-learn` for log classification
- Train BERT model on error messages
- Anomaly detection with Isolation Forest
- Root cause analysis with LLMs (ChatGPT/Ollama)

### Advanced Features
- Slack/Teams notifications
- Custom threshold per service
- Log aggregation by trace ID
- Performance metrics (response time, throughput)
- On-call escalation workflows

### Production Readiness
- Elasticsearch authentication & encryption
- Filebeat log rotation
- Prometheus metrics export
- Alerting with PagerDuty
- Multi-region deployment

---

## 📝 License

This is a student engineering project. Free to use and modify.

---

## 👨‍💻 Author

Built as a Final Year Engineering Project

**Project Stack:**
- Python 3.10
- Docker & Docker Compose
- Elasticsearch 8.12.0
- Filebeat 8.12.0
- Kibana 8.12.0
- Jira Cloud API v3

---

## ❓ Quick Reference

| Task | Command |
|------|---------|
| Start system | `docker compose up --build` |
| Stop system | `docker compose down` |
| View analyzer logs | `docker logs -f analyzer` |
| View all service logs | `docker compose logs -f` |
| Test Elasticsearch | `curl http://localhost:9200` |
| Access Kibana | `http://localhost:5601` |
| Count indexed logs | `curl http://localhost:9200/filebeat-*/_count \| jq .count` |
| Delete all logs | `curl -X DELETE http://localhost:9200/filebeat-*` |
| Restart a service | `docker restart analyzer` |
| Rebuild images | `docker compose down && docker compose up --build` |

---

## 📞 Support

If something isn't working:
1. Check `.env` file configuration
2. Review Docker Compose output: `docker compose logs`
3. Verify Elasticsearch is accessible: `curl http://localhost:9200`
4. Check Kibana dashboard for indexed logs
5. Enable `JIRA_ENABLED=false` to isolate Jira issues

