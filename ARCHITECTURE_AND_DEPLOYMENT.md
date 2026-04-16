# System Architecture & Deployment Guide

## 🏗️ System Architecture After Phase 1

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (Production)                │
│              (Nginx/ALB for TLS + Session Affinity)          │
└──────────────┬─────────────────────────────────┬─────────────┘
               ↓                                   ↓
        ┌─────────────┐                   ┌────────────────┐
        │ Flask App 1 │                   │ Flask App 2-N  │
        │ (Stateless) │                   │ (Stateless)    │
        └─────┬───────┘                   └────────┬───────┘
              │                                     │
              └─────────────────┬───────────────────┘
                                ↓
                    ┌───────────────────────┐
                    │  PostgreSQL (Master)  │
                    │  Connection Pool: 10  │
                    │  Auto-failover (RDS)  │
                    └──────────┬────────────┘
                               ↓
                    ┌───────────────────────┐
                    │   PostgreSQL Replica  │
                    │  (Read-only, Backup)  │
                    └───────────────────────┘

        ┌────────────────────────────────────────┐
        │         Redis Cluster                  │
        ├────────────────────────────────────────┤
        │ DB 0: Sessions (Persistence)           │
        │ DB 1: Celery Broker (Message Queue)    │
        │ DB 2: Celery Results (Task Results)    │
        │ DB 3: Cache (Questions, Suggestions)   │
        └──────────────┬─────────────────────────┘
                       ↓
        ┌──────────────────────────────────────────┐
        │        Celery Workers (Auto-scale)      │
        ├──────────────────────────────────────────┤
        │ AI Worker Pool      (Queue: ai)          │
        │ Email Worker Pool   (Queue: email)       │
        │ Resume Worker Pool  (Queue: resume)      │
        │ Cleanup Worker Pool (Single instance)    │
        └──────────────────────────────────────────┘

        ┌──────────────────────────────────────────┐
        │     Celery Beat (Scheduler)              │
        │ - Cleanup sessions (2 AM daily)          │
        │ - Cleanup cache (3 AM daily)             │
        │ - Generate reports (6 AM daily)          │
        └──────────────────────────────────────────┘

        ┌──────────────────────────────────────────┐
        │  Monitoring & Logging                    │
        ├──────────────────────────────────────────┤
        │ Flower (Celery monitoring)  :5555        │
        │ Sentry (Error tracking)                  │
        │ CloudWatch (Logs & Metrics)              │
        │ Prometheus (Metrics scraping) (optional) │
        └──────────────────────────────────────────┘

        ┌──────────────────────────────────────────┐
        │  External Services                       │
        ├──────────────────────────────────────────┤
        │ OpenAI / Anthropic / Ollama (AI)         │
        │ Gmail / SendGrid (Email)                 │
        │ AWS S3 (File Storage)                    │
        └──────────────────────────────────────────┘
```

### Data Flow: Synchronous Request (Before Phase 1)

```
1. User clicks "Generate Question"
   ↓
2. Flask receives request
   ↓
3. Flask blocks: Makes OpenAI API call (10-60 seconds)
   ↓
4. Browser shows spinner... user waits ⏳
   ↓
5. Finally: Flask returns response
   ↓
6. Browser displays question
```

**Problem:** UI frozen for 60 seconds!

### Data Flow: Asynchronous Request (After Phase 1)

```
1. User clicks "Generate Question"
   ↓
2. Flask receives request
   ↓
3. flask returns task_id immediately: {"task_id": "abc-123"} ✅
   ↓
4. Browser shows question input (NO blocking!)
   ↓
5. JavaScript polls: GET /api/task/abc-123 every 500ms
   ↓
6. Meanwhile: Celery worker processes in background
   - Calls OpenAI API
   - Stores result in Redis
   - Updates task status
   ↓
7. Status poll finds result ready
   ↓
8. Browser displays question
```

**Benefit:** UI responsive immediately!

---

## 🚀 Deployment Paths

### Development (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start services
./start-services.sh

# 3. Access
flask app: http://localhost:5000
flower:   http://localhost:5555
redis:    localhost:6379
postgres: localhost:5432
```

### Staging (Docker Compose)

```bash
# 1. Build images
docker-compose build

# 2. Create network
docker network create interview-prodb

# 3. Start all services
docker-compose up -d

# 4. Run migrations
docker exec interview-prodb-app-1 alembic upgrade head

# 5. Access
flask: http://localhost:5000
flower: http://localhost:5555
```

### Production (Kubernetes)

```yaml
# deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: interview-flask
spec:
  replicas: 3  # 3 Flask instances
  selector:
    matchLabels:
      app: interview-flask
  template:
    metadata:
      labels:
        app: interview-flask
    spec:
      containers:
      - name: flask
        image: interview-prodb:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          value: postgresql://user:pass@postgres-rds:5432/db
        - name: REDIS_URL
          value: redis://redis-cluster:6379/0
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 10

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: interview-celery-ai
spec:
  replicas: 2  # Auto-scale based on queue depth
  selector:
    matchLabels:
      app: interview-celery-ai
  template:
    metadata:
      labels:
        app: interview-celery-ai
    spec:
      containers:
      - name: celery-worker
        image: interview-prodb:latest
        command: ["celery", "-A", "celery_app", "worker", "-Q", "ai", "--concurrency=4"]
        env:
        - name: REDIS_URL
          value: redis://redis-cluster:6379/0

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: interview-celery-email
spec:
  replicas: 1  # Email workers don't need scaling
  selector:
    matchLabels:
      app: interview-celery-email
  template:
    metadata:
      labels:
        app: interview-celery-email
    spec:
      containers:
      - name: celery-worker
        image: interview-prodb:latest
        command: ["celery", "-A", "celery_app", "worker", "-Q", "email"]

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: interview-celery-beat
spec:
  replicas: 1  # Only 1 scheduler instance
  selector:
    matchLabels:
      app: interview-celery-beat
  template:
    metadata:
      labels:
        app: interview-celery-beat
    spec:
      containers:
      - name: celery-beat
        image: interview-prodb:latest
        command: ["celery", "-A", "celery_app", "beat", "--scheduler=redis"]
```

---

## 📊 Scaling Strategies

### Horizontal Scaling (Adding More Servers)

```
Before Phase 1:
┌─────────────┐
│Flask + SQLite + Memory Sessions│ ← Can only handle 10 users
└─────────────┘

After Phase 1:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Flask App 1  │  │ Flask App 2  │  │ Flask App 3+ │
├──────────────┼──┼──────────────┼──┼──────────────┤
              ↓  ↓              ↓  ↓              ↓
        ┌─────────────────────────┐
        │   PostgreSQL + Redis    │ ← Unlimited users!
        └─────────────────────────┘
```

### Worker Scaling (Celery)

```
Automatic scaling based on queue depth:

Queue Depth < 100 tasks
  → 2 AI workers (minimum)
  → 1 Email worker
  → 1 Resume worker

Queue Depth 100-500 tasks
  → 5 AI workers
  → 2 Email workers
  → 2 Resume workers

Queue Depth > 500 tasks
  → 10 AI workers
  → 5 Email workers
  → 3 Resume workers

Algorithm: monitor queue depth every 30 seconds
If depth > threshold, launch new worker pod
If depth < minimum, scale down (keep 1 always)
```

### Load Balancing

```
Incoming requests
  ↓
┌─────────────────┐
│ Load Balancer   │
│ (Round Robin)   │
└────────────────┬┘
    ┌────────────┼────────────┐
    ↓            ↓            ↓
┌─────────┐  ┌─────────┐  ┌─────────┐
│App-1    │  │App-2    │  │App-3    │
│Sessions:│  │Sessions:│  │Sessions:│
│→Redis   │  │→Redis   │  │→Redis   │
└─────────┘  └─────────┘  └─────────┘

Result: Session persistence across servers!
```

---

## 🔄 Database Scaling

### PostgreSQL Replication

```
Write Operations:
┌──────────────────┐
│ PostgreSQL Master│ (Accepts writes)
└────────┬─────────┘
         ↓ Replication stream
    ┌────────────┐
    ├─ Replica 1 │ (Read-only, Backup)
    ├─ Replica 2 │ (Read-only, Analytics)
    └─ Replica 3 │ (Read-only, Standby)
```

### Connection Pooling

```
Request 1 ──┐
Request 2 ──┤
Request 3 ──├──→ Pooler (10 connections) ──→ PostgreSQL (shared)
Request 4 ──┤
Request 5 ──┘

Result: 5 requests share 1-2 database connections
vs. 5 requests opening 5 separate connections
```

---

## 🔐 Production Checklist

### Before Going Live

- [ ] **Database**
  - [x] PostgreSQL configured with pooling
  - [ ] Automated backup (daily to S3)
  - [ ] Replica configured for failover
  - [ ] SSL certificates for DB connections
  - [ ] VPC security groups locked down

- [ ] **Redis**
  - [ ] ElastiCache cluster configured
  - [ ] Sentinel for automatic failover
  - [ ] Persistence enabled (AOF)
  - [ ] Backups configured
  - [ ] VPC security groups locked down

- [ ] **Application**
  - [ ] All environment variables set
  - [ ] HTTPS/TLS enabled
  - [ ] CORS configured
  - [ ] CSRF protection enabled
  - [ ] Rate limiting active

- [ ] **Monitoring**
  - [ ] CloudWatch alarms for errors
  - [ ] Sentry error tracking active
  - [ ] Prometheus metrics scraping
  - [ ] Grafana dashboards created
  - [ ] Alert channels configured (Slack, email)

- [ ] **Security**
  - [ ] Security audit completed
  - [ ] SQL injection tests passed
  - [ ] XSS vulnerability scanned
  - [ ] CSRF tokens verified
  - [ ] Secrets management (no hardcoded passwords)

- [ ] **Performance**
  - [ ] Load test (100+ concurrent users)
  - [ ] Database query optimized
  - [ ] Cache hit rates > 80%
  - [ ] Response times < 200ms
  - [ ] Worker pool sized for peak load

---

## 📈 Monitoring & Alerts

### Key Metrics to Monitor

```
Metric                          Threshold    Action
─────────────────────────────────────────────────────
Task completion rate           < 95%        Alert + page on-call
Task execution time (AI)       > 30s        Log + investigate
Task failure rate              > 5%         Alert + check logs
Database connection pool usage > 80%        Add connections
Redis memory usage             > 80%        Evict old data
Worker availability            < N-1        Restart workers
API response time              > 500ms      Scale up
Error rate                     > 1%         Page on-call
```

### Current Monitoring

```bash
# View in Flower
open http://localhost:5555

# Monitor via CLI
celery -A celery_app inspect active
celery -A celery_app inspect queues
celery -A celery_app inspect stats

# Database monitoring
psql -U user -d interview_prodb
  → select count(*) from pg_stat_activity;
  → select * from pg_stat_database;

# Redis monitoring
redis-cli info stats
redis-cli info memory
redis-cli monitor  # see all requests
```

---

## 🔧 Common Operations

### Scale Up AI Workers

```bash
# Current state
celery -A celery_app inspect active

# Increase to 5 workers
for i in {1..4}; do
  celery -A celery_app worker -Q ai --concurrency=2 --loglevel=info &
done

# Verify
celery -A celery_app inspect active_queues
```

### Drain Queue Gracefully

```bash
# Stop accepting new tasks
celery -A celery_app control shutdown

# Let existing tasks complete
# Then restart
celery -A celery_app worker -Q ai
```

### Clear Failed Tasks

```bash
celery -A celery_app purge_failed
```

### Inspect Specific Task

```bash
celery -A celery_app inspect result <task_id>
```

---

## 📝 Logging Strategy

### What Gets Logged

```json
{
  "timestamp": "2026-04-16T14:23:45.123Z",
  "level": "INFO",
  "logger": "tasks.ai_tasks",
  "message": "Question generated",
  "task_id": "abc-123-def-456",
  "user_id": 42,
  "execution_time": 8.5,
  "status": "SUCCESS",
  "question": "What is...",
  "difficulty": "medium"
}
```

### Log Shipping

```
Application logs (JSON)
    ↓
CloudWatch/ELK
    ↓
Analysis & Alerts
    ↓
Grafana dashboards
```

### Expected Log Volume

- Development: ~100 lines/minute
- Staging: ~500 lines/minute
- Production (100 users): ~2000 lines/minute
- Production (1000 users): ~20,000 lines/minute

---

## 🎯 Success Metrics

After Phase 1 deployment, these metrics should improve:

| Metric | Target | Verification |
|--------|--------|--------------|
| API Response Time | <100ms | curl -w "%{time_total}" |
| Task Processing Time | <30s | Flower dashboard |
| Success Rate | >99% | Sentry error tracking |
| Concurrent Users | 1000+ | Load test with locust |
| Database Connections | <10 | SELECT count(*) from... |
| Memory Usage | <2GB | Redis info memory |

---

## 📚 Additional Resources

### Official Docs
- Celery: https://docs.celeryproject.org/
- PostgreSQL: https://www.postgresql.org/docs/
- Redis: https://redis.io/documentation
- Kubernetes: https://kubernetes.io/docs/
- Flower: https://flower.readthedocs.io/

### Tools & Services
- AWS RDS (PostgreSQL): https://aws.amazon.com/rds/
- AWS ElastiCache (Redis): https://aws.amazon.com/elasticache/
- Sentry (Error Tracking): https://sentry.io/
- Prometheus (Metrics): https://prometheus.io/
- Grafana (Dashboards): https://grafana.com/

---

**You have everything needed to scale from 10 users to 10,000 users! 🚀**

