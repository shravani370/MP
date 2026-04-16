# 🚀 Quick Start: Running Interview-ProAI with Celery

## Prerequisites (60 seconds)

```bash
# 1. Install packages
pip install -r requirements.txt

# 2. Start Redis (choose one)
# Option A: Homebrew
brew services start redis

# Option B: Docker
docker-compose up -d redis

# 3. Verify Redis
redis-cli ping   # Should print: PONG
```

---

## ⚡ Start Everything (120 seconds)

### Method 1: Automated Script (Recommended)
```bash
# Make script executable
chmod +x start-services.sh

# Run everything at once
./start-services.sh

# Output will show:
# ✅ Redis connected
# ✅ Flask server starting on :5000
# ✅ Celery Worker-AI starting
# ✅ Celery Worker-Email starting
# ✅ Celery Beat Scheduler starting
# ✅ Flower dashboard on :5555
```

### Method 2: Manual (Alternative)
```bash
# Terminal 1: Flask app
python app.py

# Terminal 2: Celery AI worker
celery -A celery_app worker -Q ai --loglevel=info --concurrency=2

# Terminal 3: Celery Email worker
celery -A celery_app worker -Q email --loglevel=info --concurrency=2

# Terminal 4: Celery Beat scheduler
celery -A celery_app beat --loglevel=info

# Terminal 5: Flower monitoring dashboard
celery -A celery_app flower

# Terminal 6: Redis (if not using docker)
redis-server
```

---

## 🌐 Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Flask App** | http://localhost:5000 | Main web app |
| **Flower Dashboard** | http://localhost:5555 | Monitor tasks |
| **Health Check** | http://localhost:5000/health | Verify setup |

---

## ✅ Verify Everything Works

### 1. Check Health
```bash
curl http://localhost:5000/health

# Expected output:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected"
# }
```

### 2. Check Workers
```bash
curl http://localhost:5000/admin/workers

# Expected output:
# {
#   "workers": {
#     "celery@AI-queue": {"ok": "pong"},
#     "celery@Email-queue": {"ok": "pong"}
#   }
# }
```

### 3. Submit Test Task
```bash
# Generate a question asynchronously
curl -X POST http://localhost:5000/api/generate-question \
  -H "Content-Type: application/json" \
  -d '{"topic":"Python", "previous_answer":"", "history":[], "asked_questions":[]}'

# Expected output:
# {
#   "task_id": "abc-def-123",
#   "status": "queued",
#   "message": "Task submitted to AI queue"
# }

# Save the task_id
TASK_ID="abc-def-123"
```

### 4. Poll Task Status
```bash
# Check immediately (task still processing)
curl http://localhost:5000/api/task/$TASK_ID

# Expected output while processing:
# {
#   "state": "PENDING",
#   "current": 0,
#   "total": 100
# }

# After 5-10 seconds, try again
sleep 5
curl http://localhost:5000/api/task/$TASK_ID

# Expected output when done:
# {
#   "state": "SUCCESS",
#   "result": {
#     "question": "What is...",
#     "difficulty": "medium"
#   }
# }
```

---

## 📊 Monitor in Flower

Open http://localhost:5555 in browser:

1. **Tasks Tab** → See all submitted tasks
2. **Workers Tab** → Check worker health
3. **Queues Tab** → Monitor queue depth
4. **Graphs Tab** → Real-time task rate

---

## 🧪 Test Different Task Types

### Generate Question
```bash
curl -X POST http://localhost:5000/api/generate-question \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python",
    "previous_answer": "I like Python because of its simplicity",
    "history": [],
    "asked_questions": []
  }'
```

### Evaluate Answer
```bash
curl -X POST http://localhost:5000/api/evaluate-answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain recursion",
    "answer": "Recursion is when a function calls itself"
  }'
```

### Parse Resume
```bash
curl -X POST http://localhost:5000/api/parse-resume \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/uploads/resume.pdf",
    "user_email": "user@example.com"
  }'
```

### Send Email
```bash
curl -X POST http://localhost:5000/api/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "user@example.com",
    "role": "Python Developer",
    "mcq_score": 85,
    "code_score": 92,
    "passed": true
  }'
```

---

## 🔍 View Logs

```bash
# Flask app logs
tail -f logs/app.log

# Celery AI worker logs
tail -f logs/celery_worker.log

# Celery email worker logs
tail -f logs/celery_email.log

# Celery beat scheduler logs
tail -f logs/celery_beat.log

# Flower dashboard logs
tail -f logs/flower.log
```

---

## 🛑 Stop Everything

### Method 1: Script
```bash
# If using start-services.sh
pkill -f "python app.py"
pkill -f "celery worker"
pkill -f "celery beat"
pkill -f "flower"
```

### Method 2: Docker
```bash
docker-compose down
```

---

## 🐛 Troubleshooting

### Problem: Redis Connection Refused
```bash
# Check if Redis is running
redis-cli ping

# If not running, start it
redis-server

# Or with Docker
docker-compose up -d redis
```

### Problem: No Workers Available
```bash
# Check if workers are running
ps aux | grep celery

# Restart if needed
./start-services.sh
```

### Problem: Task Stuck in PENDING
```bash
# Check worker status
celery -A celery_app inspect active

# View worker logs
tail -f logs/celery_worker.log

# Restart workers
pkill -f "celery worker"
./start-services.sh
```

### Problem: Email Not Sending
```bash
# Check SMTP configuration
env | grep MAIL_

# Verify in .env file
cat .env | grep -E "MAIL_|CELERY_"

# Test SMTP connection
python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).starttls(); print('OK')"
```

### Problem: Flower Shows No Workers
```bash
# Make sure flower.log shows connections
tail -f logs/flower.log

# Manually verify workers
celery -A celery_app inspect active_queues
```

---

## 📊 Performance Test

### Send 100 Tasks at Once
```bash
# This will test the task queue under load
for i in {1..100}; do
  curl -X POST http://localhost:5000/api/generate-question \
    -H "Content-Type: application/json" \
    -d "{\"topic\":\"Python\", \"previous_answer\":\"Test $i\", \"history\":[], \"asked_questions\":[]}" \
    &
done

# Wait for all to complete
wait

# Check Flower to see processing
open http://localhost:5555
```

### Monitor Queue Depth
```bash
# Show current queue sizes
while true; do
  echo "=== $(date) ==="
  celery -A celery_app inspect active_queues
  sleep 2
done
```

---

## 🎯 Common Tasks

### Clear All Tasks
```bash
celery -A celery_app purge  # WARNING: Deletes all pending tasks
```

### Inspect Specific Task
```bash
celery -A celery_app inspect result $TASK_ID
```

### List All Registered Tasks
```bash
celery -A celery_app inspect registered
```

### Check Worker Stats
```bash
celery -A celery_app inspect stats
```

### View Task History
```bash
# In Flower: http://localhost:5555/tasks
# Shows all completed, failed, and pending tasks
```

---

## 🌍 Environment Configuration

### .env File Required
```env
# Flask
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/interview_prodb

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here

# OpenAI (if using OpenAI as AI backend)
OPENAI_API_KEY=sk-...

# Sentry (optional)
SENTRY_DSN=
```

---

## 📱 Frontend Integration Example

```javascript
// How to use async tasks in your frontend

async function submitAnswer() {
  const answer = document.getElementById('answer-input').value;
  const question = document.getElementById('question').innerText;
  
  // 1. Submit task
  const response = await fetch('/api/evaluate-answer', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question, answer})
  });
  
  const {task_id} = await response.json();
  
  // 2. Show loading
  document.getElementById('result').innerText = 'Evaluating...';
  
  // 3. Poll for result
  const result = await pollTaskResult(task_id);
  
  // 4. Display result
  document.getElementById('result').innerHTML = `
    <p>Score: ${result.score}%</p>
    <p>Feedback: ${result.feedback}</p>
  `;
}

// Helper function to poll task status
async function pollTaskResult(taskId, maxAttempts = 120, interval = 500) {
  for (let i = 0; i < maxAttempts; i++) {
    const response = await fetch(`/api/task/${taskId}`);
    const status = await response.json();
    
    if (status.state === 'SUCCESS') {
      return status.result;
    } else if (status.state === 'FAILURE') {
      throw new Error(status.error_message);
    }
    
    // Wait before next attempt
    await new Promise(r => setTimeout(r, interval));
  }
  
  throw new Error('Task timeout');
}
```

---

## 🎓 Learning Resources

- **Celery:** https://docs.celeryproject.org/
- **Flower:** https://flower.readthedocs.io/
- **Redis:** https://redis.io/commands/
- **Flask-Mail:** https://flask-mail.readthedocs.io/
- **Flask Sessions:** https://flask.palletsprojects.com/en/latest/quickstart/#sessions

---

## ✨ Next Steps

1. ✅ Run `./start-services.sh`
2. ✅ Open http://localhost:5555 (Flower)
3. ✅ Submit test tasks
4. ✅ Watch them process in real-time
5. ✅ Configure email in .env
6. ✅ Test with your actual AI backend
7. ✅ Deploy to production!

---

**Ready to scale?** You've got async, caching, and monitoring all set up! 🚀
