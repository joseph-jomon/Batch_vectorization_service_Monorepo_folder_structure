### **Normal Usage of Celery**

Celery is a distributed task queue system that allows you to run tasks asynchronously across multiple workers. It is commonly used in Python applications to offload long-running tasks, such as sending emails, processing files, or making API calls, to background workers. This frees up your main application to handle incoming requests more quickly.

### **Celery with FastAPI**

**Yes, Celery is commonly used with FastAPI**, and it's considered a best practice for handling background tasks that are time-consuming or resource-intensive.

#### **Typical Usage Pattern**

The common approach when using Celery with FastAPI is to run Celery and FastAPI as separate services:

1. **Celery Workers**: These are processes that consume tasks from a message broker (e.g., Redis, RabbitMQ) and execute them. The workers are typically run in separate containers or processes.

2. **FastAPI Application**: The FastAPI app is responsible for handling HTTP requests and triggering Celery tasks when needed. The FastAPI server is usually run in its own container or process.

### **Why Separate Processes?**

- **Scalability**: By running Celery workers and FastAPI separately, you can scale them independently. For instance, if your background tasks are heavy, you can scale the number of Celery workers without affecting the FastAPI app.
- **Reliability**: Isolating the two services reduces the chance that an issue in one will affect the other. If a worker crashes or becomes unresponsive, it won’t take down the FastAPI app.
- **Resource Optimization**: Celery workers can be optimized for CPU or I/O operations, while FastAPI instances can be optimized for handling web traffic.

### **Recommended Setup for FastAPI with Celery**

Instead of running both FastAPI and Celery in the same container, the recommended approach is:

#### **1. FastAPI Service**

This service handles HTTP requests and triggers Celery tasks.

**Example Dockerfile for FastAPI:**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Example FastAPI Endpoint:**

```python
from fastapi import FastAPI, BackgroundTasks
from app.tasks import process_text_data

app = FastAPI()

@app.post("/process-text/")
async def process_text_endpoint(text: str, background_tasks: BackgroundTasks):
    task = process_text_data.delay(text)
    return {"task_id": task.id, "status": "Processing started"}
```

#### **2. Celery Worker Service**

This service runs the Celery workers that consume tasks from the message broker and execute them.

**Example Dockerfile for Celery Worker:**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "app.celery", "worker", "--loglevel=info"]
```

#### **3. Docker Compose Setup**

Use Docker Compose to manage and run the services together, along with a Redis or RabbitMQ broker.

```yaml
version: '3.8'

services:
  redis:
    image: "redis:alpine"
    container_name: redis
    ports:
      - "6379:6379"

  fastapi_service:
    build: ./fastapi_service
    ports:
      - "8000:8000"
    depends_on:
      - redis

  celery_worker:
    build: ./celery_worker
    depends_on:
      - redis
```

### **Summary**

- **Separate Services**: It's standard practice to run Celery workers and the FastAPI app as separate services or processes. This allows for better scalability, reliability, and resource optimization.
- **Celery with FastAPI**: Celery is commonly used with FastAPI for background task processing. FastAPI handles the HTTP requests and enqueues tasks for Celery to process asynchronously.
- **Supervisord**: Running both in the same container using `supervisord` is possible, but it's not the most scalable or recommended approach in production.

### **When to Use Supervisord?**
- **Development**: If you’re in a development environment or have a very simple use case, running both FastAPI and Celery in the same container using `supervisord` might be convenient.
- **Production**: For production environments, it’s better to follow the separation of concerns and run them as independent services.

This setup aligns with modern microservices architecture practices and ensures that each component of your application can scale and function independently.