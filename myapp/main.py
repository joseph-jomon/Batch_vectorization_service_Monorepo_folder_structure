from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from myapp.tasks import process_text_batch, process_image_batch

app = FastAPI()

# Define a Pydantic model for the text batch request
class TextBatchRequest(BaseModel):
    texts: List[Dict[str, str]]  # Each item is a dict with 'id' and 'text'

# Define a Pydantic model for the image batch request
class ImageBatchRequest(BaseModel):
    images: List[Dict[str, str]]  # Each item is a dict with 'id' and 'image' (base64-encoded)

@app.post("/process-text-batch/")
async def process_text_batch_endpoint(batch: TextBatchRequest):
    # Send the list of text data with their IDs as a batch to the Celery task
    task = process_text_batch.delay(batch.texts)
    return {"task_id": task.id, "status": "Processing started"}

@app.post("/process-image-batch/")
async def process_image_batch_endpoint(batch: ImageBatchRequest):
    # Send the list of image data with their IDs as a batch to the Celery task
    task = process_image_batch.delay(batch.images)
    return {"task_id": task.id, "status": "Processing started"}

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    task = process_text_batch.AsyncResult(task_id)
    if task.state == 'PENDING':
        return {"state": task.state, "status": "Pending..."}
    elif task.state == 'SUCCESS':
        return {"state": task.state, "result": task.result}
    else:
        return {"state": task.state, "status": str(task.info)}
    
# Dummy endpoint to simulate the database service
@app.post("/dummy-store-vectors/")
async def dummy_store_vectors(request: Request):
    data = await request.json()
    print("Received data:", data)  # Print the received data to the console
    return {"status": "Success", "message": "Data received successfully", "data_received": data}