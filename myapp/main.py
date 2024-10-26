from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
from myapp.tasks.text_batch_processor import process_text_batch_task
from myapp.tasks.image_batch_processor import process_image_batch_task
from celery.result import AsyncResult

app = FastAPI(    
    title="Batch Vectorization Service",
    description="Accepts text and image data and converts it to vectors and sends it to the Aggregation Service",
    version="1.0.0",)

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
    texts: List[TextItem]  # List of TextItem models
    company_name:str       # Add company name for indexing


# Define a Pydantic model for the image batch request
class ImageBatchRequest(BaseModel):
    images: List[ImageItem]  # List of ImageItem models
    company_name: str       # Add company name for indexig

@app.post("/process-text-batch/")
async def process_text_batch_endpoint(batch: TextBatchRequest):
    # Convert Pydantic models to list of dictionaries as expected by the Celery task
    # Send the list of text data with their IDs as a batch to the Celery task
    task = process_text_batch_task.delay([item.dict() for item in batch.texts], batch.company_name)
    return {"task_id": task.id, "status": "Processing started"}

@app.post("/process-image-batch/")
async def process_image_batch_endpoint(batch: ImageBatchRequest):
    # Convert Pydantic models to list of dictionaries as expected by the Celery task
    # Send the list of image data with their IDs as a batch to the Celery task
    task = process_image_batch_task.delay([item.dict() for item in batch.images], batch.company_name)
    return {"task_id": task.id, "status": "Processing started"}

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id)  # Use a generic AsyncResult to access any task

    if task_result.state == 'PENDING':
        return {"state": task_result.state, "status": "Pending..."}
    elif task_result.state == 'STARTED':
        return {"state": task_result.state, "status": "Processing..."}
    elif task_result.state == 'SUCCESS':
        return {"state": task_result.state, "result": task_result.result}
    elif task_result.state == 'FAILURE':
        # Return an error message if the task failed
        return {"state": task_result.state, "status": str(task_result.info)}
    else:
        return {"state": task_result.state, "status": "Unknown state"}
    
# Dummy endpoint to simulate the da
# tabase service
@app.post("/dummy-store-vectors/")
async def dummy_store_vectors(request: Request):
    data = await request.json()
    print("Received data:", data)  # Print the received data to the console
    return {"status": "Success", "message": "Data received successfully", "data_received": data}