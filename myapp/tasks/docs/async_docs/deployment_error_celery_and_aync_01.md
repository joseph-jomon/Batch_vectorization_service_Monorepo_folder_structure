If you decide to make `send_to_aggregation_service` synchronous, using `async with` and `await` directly inside it won’t work, as these are asynchronous constructs. Since `httpx.AsyncClient` is designed for async usage, there are two main approaches to handle this when converting to synchronous code:

### 1. **Switch to `httpx.Client` for Synchronous Requests**
   - If you don’t require async features, the simplest change is to use the synchronous version of `httpx`, which is `httpx.Client` instead of `httpx.AsyncClient`. This removes the need for `async` and `await` keywords:

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

### 2. **Wrap Async Code with `async_to_sync` (Less Ideal in Pure Sync Contexts)**
   - If you need to keep `send_to_aggregation_service` async (e.g., if other parts of your code require async features) but still want `process_text_batch_task` to be synchronous, you could use `async_to_sync` to wrap `send_to_aggregation_service`. However, this is less efficient and only recommended if async requests are essential:

   ```python
   from asgiref.sync import async_to_sync

   @app.task
   def process_text_batch_task(texts_with_ids, company_name, batch_size=36):
       processor = TextBatchProcessor(batch_size)
       return async_to_sync(processor.process_and_send_text_batch)(texts_with_ids, company_name)
   ```

   Then, keep `send_to_aggregation_service` as an async function. This approach works but may add some latency due to sync-async conversions.

### Recommended Approach
Switching to `httpx.Client` for a synchronous request is the most straightforward solution here, as it maintains synchronous behavior throughout and ensures that Celery’s serialization process can handle the result without issues.