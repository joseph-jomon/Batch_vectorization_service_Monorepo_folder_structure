The error message you're seeing, `Connection refused`, typically indicates that the Celery worker is trying to send a request to the dummy endpoint (`http://localhost:8000/dummy-store-vectors/`), but it's unable to connect because the FastAPI service (where the dummy endpoint is hosted) is not running or is not accessible from within the Celery worker's environment.

### **Potential Causes and Solutions:**

1. **FastAPI Service Not Running**:
   - Ensure that the FastAPI service, where the dummy endpoint is defined, is running. If you're using `docker-compose`, both the FastAPI service and the Celery worker should be started together.

2. **Networking in Docker**:
   - If you're running both services in Docker containers, using `localhost` inside a container may not point to the host machine or another container but to the container itself. This is likely the cause of your issue.
   - In Docker Compose, services communicate with each other using their service names as hostnames.

### **Solution: Use the Service Name Instead of `localhost`**

In a Docker Compose setup, you should refer to the FastAPI service by its service name, not `localhost`. 

For example, if your FastAPI service is named `fastapi_service` in the `docker-compose.yml`, the URL in your `tasks.py` should be:

```python
response = requests.post("http://fastapi_service:8000/dummy-store-vectors/", json=payload)
```

### **Updated `tasks.py` with Correct Service Name**

```python
import requests
from app.celery import app
from app.models.text_vectorizer import TextVectorizer
from app.models.image_vectorizer import ImageVectorizer
import datasets
import torch
import numpy as np
from tqdm import tqdm

@app.task
def process_text_batch(texts_with_ids: list, batch_size: int = 36):
    ids = [item["id"] for item in texts_with_ids]
    texts = [item["text"] for item in texts_with_ids]

    ds = datasets.Dataset.from_dict({"Combined_Text": texts})

    vectorizer = TextVectorizer()

    def text_collate(examples):
        return vectorizer.tokenizer.batch_encode_plus(
            [example['Combined_Text'] for example in examples],  # Fixed access pattern
            truncation=True, 
            padding=True,
            return_tensors="pt"
        )

    text_dl = torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0, collate_fn=text_collate)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vectorizer.text_model.to(device)
    vectorizer.text_model.eval()

    outputs = []
    for batch in tqdm(text_dl):
        with torch.no_grad():
            text_embeddings = vectorizer.text_model(**{k: v.to(device) for k, v in batch.items()}).text_embeds.squeeze()
            outputs.append(text_embeddings.to("cpu"))

    text_embeddings = np.vstack(outputs)
    text_embeddings_normed = text_embeddings / np.linalg.norm(text_embeddings, axis=1)[:, np.newaxis]

    payload = {
        "embeddings": text_embeddings_normed.tolist(),
        "ids": ids,
        "metadata": {"texts": texts}
    }

    # Use the service name instead of localhost
    response = requests.post("http://fastapi_service:8000/dummy-store-vectors/", json=payload)

    return response.json()

@app.task
def process_image_batch(images_with_ids: list, batch_size: int = 36):
    ids = [item["id"] for item in images_with_ids]
    images = [item["image"] for item in images_with_ids]

    pil_images = [Image.open(io.BytesIO(base64.b64decode(img))) for img in images]

    ds = datasets.Dataset.from_dict({"Image": pil_images})

    vectorizer = ImageVectorizer()

    def image_collate(examples):
        images = [vectorizer.preprocess(image) for image in examples['Image']]
        return torch.stack(images)

    image_dl = torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0, collate_fn=image_collate)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vectorizer.model.to(device)
    vectorizer.model.eval()

    outputs = []
    for batch in tqdm(image_dl):
        with torch.no_grad():
            image_embeddings = vectorizer.model(batch.to(device)).squeeze()
            outputs.append(image_embeddings.to("cpu"))

    image_embeddings = torch.cat(outputs)
    image_embeddings_normed = image_embeddings / image_embeddings.norm(dim=1, keepdim=True)

    payload = {
        "embeddings": image_embeddings_normed.tolist(),
        "ids": ids,
        "metadata": {"images": images}
    }

    # Use the service name instead of localhost
    response = requests.post("http://fastapi_service:8000/dummy-store-vectors/", json=payload)

    return response.json()
```

### **Additional Notes:**

- **Docker Compose Service Name**: Make sure that `fastapi_service` matches the service name in your `docker-compose.yml` file.
- **Expose Port 8000**: Ensure that the FastAPI service is exposing port 8000 and that it is available for other services to connect to.

### **Conclusion:**

By using the service name in Docker Compose instead of `localhost`, you ensure that the Celery worker can correctly connect to the FastAPI service, avoiding the `Connection refused` error. This is a common approach when dealing with Docker Compose environments where services need to communicate with each other.