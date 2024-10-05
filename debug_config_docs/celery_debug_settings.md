The **port mapping** in the Docker Compose file is correctly configured, but let me clarify how it works in relation to your **`--listen`** command:

- **Docker Compose `ports` Section**:
  ```yaml
  ports:
    - "5679:5678"  # Debugger port for Celery worker (host:container)
  ```
  This means:
  - **`5679`** is the **host port** that you can use to attach your debugger.
  - **`5678`** is the **container port** where `debugpy` is listening inside the container.

- **`--listen` Command in `debugpy`**:
  ```yaml
  command: ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "celery", "-A", "myapp.celery_app", "worker", "--loglevel=info"]
  ```
  - The **`--listen` argument with `0.0.0.0:5678`** tells `debugpy` to listen for connections on **port 5678** of **all network interfaces** inside the container.

### Summary of the Mapping:
- **Port `5678`** inside the **container** is where `debugpy` listens for debug connections.
- **Port `5679`** on the **host** is mapped to port `5678` on the container.
  - This means that to connect to the Celery worker with your debugger from your development machine, you need to attach to **port 5679** on your host.
  
This configuration ensures that:
- **`debugpy`** listens on port **5678** inside the container, which is mapped to **port 5679** on your local machine.
- When debugging from your local IDE, you should use **port 5679** to connect to the Celery worker.

The mapping is correct, but make sure you're connecting to the appropriate **host port** (`5679` in this case) when trying to debug the Celery worker.