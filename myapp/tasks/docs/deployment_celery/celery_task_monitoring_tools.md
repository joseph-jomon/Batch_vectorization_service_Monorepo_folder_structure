In Celery, task events are turned off by default, as shown in your logs. Task events allow you to monitor and track the execution of tasks, which is helpful for debugging and for building monitoring dashboards. To enable task events, use the `-E` flag when starting the worker.

Here’s how you can enable task events:

### 1. **Enable Task Events with the `-E` Flag**

Update the `docker-compose.yml` file to include the `-E` flag in the Celery worker command:
```yaml
celery_worker:
  build:
    context: .
    dockerfile: celery_worker/Dockerfile
  volumes:
    - ./myapp:/myapp  # Mount the myapp directory to /myapp in the container
  depends_on:
    - redis
  environment:
    - PYTHONUNBUFFERED=1
  command: ["celery", "-A", "myapp.celery_app", "worker", "--loglevel=info", "--concurrency=4", "-E"]
```

### 2. **Start the Worker with Task Events Manually**
If you’re running Celery from the command line, you can simply add the `-E` flag:
```bash
celery -A myapp.celery_app worker --loglevel=info --concurrency=4 -E
```

### 3. **Using Celery Events Monitor Tool (Optional)**
Once task events are enabled, you can monitor the task events using `celery events` (a real-time monitoring tool provided by Celery):
```bash
celery -A myapp.celery_app events
```

This will display task events in real time, which can be useful for debugging or understanding task flow.

### 4. **Monitoring Tools**
If you’re using Celery monitoring tools like `Flower`, enabling task events will allow Flower to display task progress and history. You would launch Flower with:
```bash
celery -A myapp.celery_app flower
```

Enabling task events with the `-E` flag should give you visibility into task states and help with debugging. Let me know if you need more insights into using task events or monitoring tools.