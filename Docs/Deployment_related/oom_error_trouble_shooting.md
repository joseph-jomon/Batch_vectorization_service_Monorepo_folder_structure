From the output, it appears that the logs only show the HTTP status (200) for requests, with no detailed information about internal processes or errors that might explain batch processing behavior. To capture more information about the request flow, including potential issues with data processing, consider enabling detailed application logging in your FastAPI and Celery services.

Here’s how you can adjust logging settings to provide more insight:

### 1. **Add More Logging to FastAPI Application**:
   - Edit `main.py` to include detailed logging inside the `process-text-batch` and other key endpoints. For instance:
     ```python
     import logging

     logger = logging.getLogger("uvicorn.error")

     @app.post("/process-text-batch/")
     async def process_text_batch_endpoint(batch: TextBatchRequest):
         logger.info(f"Received text batch with {len(batch.texts)} items for processing.")
         # existing code
     ```

### 2. **Enhance Gunicorn Logs**:
   - Enable `--log-level` to `debug` or `info` in the Docker Compose file to ensure Gunicorn provides detailed logs. Also, ensure any log files you specify in Gunicorn’s configuration have write permissions.
   ```yaml
   command: ["gunicorn", "myapp.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--log-level", "info"]
   ```

### 3. **Enable Celery Logging**:
   - In `celery_worker`’s `command` in `docker-compose.yml`, set `--loglevel=DEBUG` to capture detailed Celery logs:
     ```yaml
     celery_worker:
       command: ["celery", "-A", "myapp.celery_app", "worker", "--loglevel=DEBUG"]
     ```

### 4. **Check Docker Memory and CPU Allocation**:
   - DigitalOcean machines with limited memory may lead to silent terminations if memory gets constrained. Confirm that Docker containers have enough memory allocated and check for OOM errors in the host system logs:
     ```bash
     dmesg | grep -i "killed process"
     ```

After these adjustments, if logs still do not display the needed details, try writing logs to a file and examining them after execution, as Docker’s stdout/stderr buffer may not retain extensive logs in memory-constrained environments.