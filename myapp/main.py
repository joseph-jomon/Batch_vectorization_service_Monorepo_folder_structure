from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
from tasks.text_batch_processor import process_text_batch
from tasks.image_batch_processor import process_image_batch

app = FastAPI()

# Define a Pydantic model for each text item
class TextItem(BaseModel):
    id: str  # The ID associated with the text
    immo_text: str  # The actual text content

# Define a Pydantic model for each image item
class ImageItem(BaseModel):
    id: str  # The ID associated with the image
    image: str  # The base64-encoded image string

# Define a Pydantic model for the text batch request
class TextBatchRequest(BaseModel):
    texts: List[TextItem]  # Each item is now a TextItem with 'id' and 'immo_text'

# Define a Pydantic model for the image batch request
class ImageBatchRequest(BaseModel):
    images: List[ImageItem]  # Each item is now an ImageItem with 'id' and 'image'

@app.post("/process-text-batch/")
async def process_text_batch_endpoint(batch: TextBatchRequest):
    # Convert Pydantic models to list of dictionaries as expected by the Celery task
    # Send the list of text data with their IDs as a batch to the Celery task
    task = process_text_batch.delay([item.dict() for item in batch.texts])
    return {"task_id": task.id, "status": "Processing started"}

@app.post("/process-image-batch/")
async def process_image_batch_endpoint(batch: ImageBatchRequest):
    # Convert Pydantic models to list of dictionaries as expected by the Celery task
    # Send the list of image data with their IDs as a batch to the Celery task
    task = process_image_batch.delay([item.dict() for item in batch.images])
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