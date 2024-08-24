from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from myapp.tasks import process_text_batch, process_image_batch

app = FastAPI()

# Define a Pydantic model for the batch request
class TextBatchRequest(BaseModel):
    texts: List[str]

class ImageBatchRequest(BaseModel):
    images: List[str]  # Assuming base64-encoded image strings

@app.post("/process-text-batch/")
async def process_text_batch_endpoint(batch: TextBatchRequest):
    task = process_text_batch.delay(batch.texts)
    return {"task_id": task.id, "status": "Processing started"}

@app.post("/process-image-batch/")
async def process_image_batch_endpoint(batch: ImageBatchRequest):
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
