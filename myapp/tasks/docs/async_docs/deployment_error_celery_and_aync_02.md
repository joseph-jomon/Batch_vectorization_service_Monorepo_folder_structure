Yes, that’s correct. Even if the **task function itself is synchronous** and calls another synchronous function (`send_to_aggregation_service`), if `send_to_aggregation_service` contains asynchronous code (like `async with` or `await`), it will still trigger issues. The reason is that the async constructs (`await` and `async with`) are only allowed in asynchronous functions. Therefore:

1. **Any function containing `async with` or `await` must be async**, and thus incompatible in a synchronous context unless explicitly wrapped with something like `async_to_sync`.

2. **To use `send_to_aggregation_service` synchronously**, you must convert any async-specific code within it to synchronous code.

### What This Means for Your Code
In your case, converting `send_to_aggregation_service` to use `httpx.Client` (the synchronous version) instead of `httpx.AsyncClient` removes the need for async constructs altogether. This way, `send_to_aggregation_service` can be called synchronously, ensuring it’s fully compatible with a synchronous task setup in Celery. Here’s what it looks like:

```python
import httpx

def send_to_aggregation_service(self, ids, embeddings, embedding_type, company_name):
    payload = {
        "ids": ids,
        "embeddings": embeddings,
        "type": embedding_type,
        "company_name": company_name
    }

    # Use synchronous httpx client
    with httpx.Client() as client:
        response = client.post(self.aggregation_service_url, json=payload)

    # Return the response as a JSON object
    return response.json()
```

### In Summary
Yes, even if the task function (`process_text_batch_task`) is synchronous, **all functions called within it (like `send_to_aggregation_service`) must also be synchronous** if they contain asynchronous calls. By switching to `httpx.Client`, you ensure all parts of the task are synchronous and compatible with Celery’s synchronous task execution model.