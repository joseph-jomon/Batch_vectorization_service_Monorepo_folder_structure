Good observation. Indeed, the code provided for `tasks.py` has some redundancy, especially between the `process_text_batch` and `process_image_batch` functions. This redundancy not only violates the **DRY (Don't Repeat Yourself)** principle, which is an important part of clean code practices, but it also makes the maintenance harder if changes need to be made across both functions. By applying **SOLID** principles, we can refactor the code to be more modular, reusable, and maintainable.

The **SOLID** principles that are particularly relevant here include:

- **Single Responsibility Principle (SRP)**: Each function or class should have a clear responsibility.
- **Open/Closed Principle (OCP)**: The code should be open for extension but closed for modification.
- **Dependency Inversion Principle (DIP)**: High-level modules should not depend on low-level modules. Instead, both should depend on abstractions.

### Refactoring Using Classes

To make the `tasks.py` more consistent with SOLID principles and reduce redundancy, we can create a class that handles the common parts of both the text and image processing tasks. This class will be responsible for processing batches, generating embeddings, and sending the results to the aggregation service.

Below, I'll outline a refactored version that uses an **abstract base class** and two derived classes for text and image batch processing. This will make the code more modular, and the logic for text and image processing can be easily extended or modified without duplicating code.

### Proposed Refactoring

#### Step 1: Define an Abstract Base Class (`BatchProcessor`)
This abstract base class will handle common functionalities such as:
- Device setup (e.g., using GPU if available)
- Preparing the data loader
- Normalizing embeddings
- Sending data to the aggregation service

We will then create specific subclasses (`TextBatchProcessor` and `ImageBatchProcessor`) for handling text and image-specific parts.

#### Updated Folder Structure
Let's introduce the following:
```
tasks/
├── __init__.py
├── base_batch_processor.py   # The abstract base class and shared logic
└── text_image_batch_processors.py # Specific processors for text and image
```

#### 1. `base_batch_processor.py` - Abstract Base Class

```python
from abc import ABC, abstractmethod
import torch
import requests
import numpy as np
from tqdm import tqdm

class BatchProcessor(ABC):
    def __init__(self, batch_size=36):
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def process_batches(self, data_loader, model):
        model.to(self.device)
        model.eval()
        outputs = []

        for batch in tqdm(data_loader):
            with torch.no_grad():
                embeddings = self._generate_embeddings(batch, model)
                outputs.append(embeddings.to("cpu"))

        return torch.cat(outputs)

    def normalize_embeddings(self, embeddings):
        return embeddings / embeddings.norm(dim=1, keepdim=True)

    @abstractmethod
    def _generate_embeddings(self, batch, model):
        pass

    def send_to_aggregation_service(self, ids, embeddings, embedding_type):
        payload = {
            "embeddings": [
                {
                    "id": ids[i],
                    "embedding_type": embedding_type,
                    "embedding": embeddings[i].tolist()
                }
                for i in range(len(ids))
            ]
        }
        response = requests.post("http://fastapi_service_batch_processing:8000/aggregate/", json=payload)
        return response.json()
```

#### 2. `text_image_batch_processors.py` - Specific Batch Processors for Text and Image

```python
import datasets
import torch
from torch.utils.data import DataLoader
from myapp.celery_app import app
from myapp.models.text_vectorizer import TextVectorizer
from myapp.models.image_vectorizer import ImageVectorizer
from tasks.base_batch_processor import BatchProcessor
from PIL import Image
import base64
import io

class TextBatchProcessor(BatchProcessor):
    def __init__(self, batch_size=36):
        super().__init__(batch_size)
        self.vectorizer = TextVectorizer()

    def process_text_batch(self, texts_with_ids):
        ids = [item["id"] for item in texts_with_ids]
        texts = [item["immo_text"] for item in texts_with_ids]

        ds = datasets.Dataset.from_dict({"Combined_Text": texts})

        def text_collate(examples):
            return self.vectorizer.tokenizer.batch_encode_plus(
                [example['Combined_Text'] for example in examples], 
                truncation=True, 
                padding=True,
                return_tensors="pt"
            )

        text_dl = DataLoader(ds, batch_size=self.batch_size, shuffle=False, num_workers=0, collate_fn=text_collate)

        embeddings = self.process_batches(text_dl, self.vectorizer.text_model)
        normalized_embeddings = self.normalize_embeddings(embeddings)

        return self.send_to_aggregation_service(ids, normalized_embeddings, "EMBEDDINGS_TEXT")

    def _generate_embeddings(self, batch, model):
        return model(**{k: v.to(self.device) for k, v in batch.items()}).text_embeds.squeeze()

class ImageBatchProcessor(BatchProcessor):
    def __init__(self, batch_size=36):
        super().__init__(batch_size)
        self.vectorizer = ImageVectorizer()

    def process_image_batch(self, images_with_ids):
        ids = [item["id"] for item in images_with_ids]
        images = [item["image"] for item in images_with_ids]
        pil_images = [Image.open(io.BytesIO(base64.b64decode(img))) for img in images]

        ds = datasets.Dataset.from_dict({"Image": pil_images})

        def image_collate(examples):
            images = [self.vectorizer.preprocess(image) for image in examples['Image']]
            return torch.stack(images)

        image_dl = DataLoader(ds, batch_size=self.batch_size, shuffle=False, num_workers=0, collate_fn=image_collate)

        embeddings = self.process_batches(image_dl, self.vectorizer.model)
        normalized_embeddings = self.normalize_embeddings(embeddings)

        return self.send_to_aggregation_service(ids, normalized_embeddings, "EMBEDDINGS_IMAGE")

    def _generate_embeddings(self, batch, model):
        return model(batch.to(self.device)).squeeze()

# Celery Tasks
@app.task
def process_text_batch(texts_with_ids, batch_size=36):
    processor = TextBatchProcessor(batch_size)
    return processor.process_text_batch(texts_with_ids)

@app.task
def process_image_batch(images_with_ids, batch_size=36):
    processor = ImageBatchProcessor(batch_size)
    return processor.process_image_batch(images_with_ids)
```

### Benefits of This Refactor

1. **Reduced Redundancy**:
   - Both text and image processing tasks share a lot of common functionality (e.g., device setup, batch processing, normalization, and sending data to the aggregation service).
   - By moving this common functionality into an abstract base class (`BatchProcessor`), we avoid repeating the same code in both text and image tasks.

2. **Single Responsibility Principle**:
   - Each class now has a clear responsibility:
     - `BatchProcessor` handles generic batch processing, normalization, and sending data.
     - `TextBatchProcessor` and `ImageBatchProcessor` inherit from `BatchProcessor` and provide the specific logic for text and image data processing.

3. **Open/Closed Principle**:
   - If a new type of data processing (e.g., audio or video) is introduced, you can create another subclass without modifying the existing ones. The abstract methods (`_generate_embeddings`) are overridden in each subclass, making it extendable.

4. **Code Reuse with Inheritance**:
   - The use of an abstract base class (`BatchProcessor`) provides a blueprint for the common behavior while allowing specific implementations to override methods, keeping the code DRY and extendable.

5. **Compatibility with Celery**:
   - The Celery tasks (`@app.task`) can easily call the new classes. Since each processor class method is responsible for the whole workflow (loading data, generating embeddings, normalizing, and sending), they fit well as self-contained Celery tasks.
   - Using the class doesn’t complicate the Celery task system. Celery can execute any callable, so calling a class method (e.g., `processor.process_text_batch()`) works seamlessly.

### Summary
This refactored version eliminates redundancy, adheres more closely to SOLID principles, and is more maintainable. The abstract base class (`BatchProcessor`) encapsulates shared behavior, and the specific subclasses (`TextBatchProcessor` and `ImageBatchProcessor`) handle the unique processing steps.

Using classes in this manner doesn’t add complexity but instead reduces the clutter, makes the code more extendable, and still works effectively with the Celery `@app.task` decorator. This is a cleaner, more modular approach that’s ideal for scaling and maintaining the system in the long term.