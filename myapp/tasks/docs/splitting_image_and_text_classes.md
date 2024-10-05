Splitting up the text and image processing into separate files can have advantages, particularly when it comes to maintainability, readability, and the application of the **Single Responsibility Principle (SRP)**. However, the decision to split these into separate files or keep them in one depends on several factors, including project size, team familiarity, and code organization preferences.

Let’s consider the pros and cons of splitting them:

### Advantages of Splitting into Separate Files

1. **Single Responsibility and Clarity**:
   - Each file has a well-defined role, making it easier to understand what each file does. This adheres closely to **Single Responsibility Principle**—a core aspect of **SOLID** principles.
   - For example, `text_batch_processor.py` will only handle text-specific logic, while `image_batch_processor.py` deals with image-related tasks. This makes it easier to locate code relevant to text vs. image processing.

2. **Simpler Navigation and Readability**:
   - In larger projects, having separate files for different functionalities improves **navigability**. Developers can easily open a file knowing it only deals with one particular aspect of batch processing.
   - If the code for each processor becomes more complex (e.g., additional preprocessing steps, different model architectures), splitting it into separate files helps keep the file sizes manageable and readable.

3. **Scalability and Maintainability**:
   - If there’s a need for future expansion—e.g., adding new types of data processing (e.g., audio or video)—having separate files already encourages consistency in how new modules are added.
   - Changes related to text processing or image processing are isolated, reducing the risk of accidental modifications or bugs affecting the other.

4. **Ease of Testing**:
   - With separate files, unit tests can be more targeted, as you’ll be working with smaller, self-contained pieces of code.
   - It becomes easier to **mock** dependencies specific to text or image processing when they are isolated in their own modules.

### Disadvantages of Splitting into Separate Files

1. **Overhead for Small Projects**:
   - If the project is relatively small, splitting into multiple files can feel like **over-engineering** and add unnecessary complexity in terms of more files to manage. This may be more of an issue if your team is relatively small or the entire workflow is still evolving rapidly.

2. **Cross-File Dependencies**:
   - Splitting files can sometimes lead to scenarios where cross-file imports create **tight coupling**. Care must be taken to ensure each module remains relatively independent.
   - If there are many common utilities shared between text and image processing, those should be factored into their own helper module to avoid redundancy and tight coupling.

### My Recommendation

Given that you're aiming to follow **SOLID principles** and keep maintainability in mind, **splitting text and image processing into separate files** is likely the better choice for the longer-term scalability and clarity of your project, especially if:

- The codebases for text and image processing are likely to grow in size and complexity.
- You anticipate expanding into other modalities (e.g., audio, video) or adding additional preprocessing steps.
- You have a development team where different developers can take ownership of different processing types.

However, for projects that are still evolving and are fairly small, it may make sense to initially keep them together and refactor once the boundaries and feature set stabilize. 

#### How Would I Do It?

Here’s how I’d proceed with splitting the current setup:

### Updated Folder Structure:

```
tasks/
├── __init__.py
├── base_batch_processor.py   # The abstract base class and shared logic
├── text_batch_processor.py   # Logic specific to text processing
└── image_batch_processor.py  # Logic specific to image processing
```

### Splitting the Code into Separate Files

#### 1. `base_batch_processor.py` - Shared Logic
This file remains unchanged from the previous version I provided.

#### 2. `text_batch_processor.py` - Text-Specific Processing

```python
import datasets
import torch
from torch.utils.data import DataLoader
from myapp.models.text_vectorizer import TextVectorizer
from tasks.base_batch_processor import BatchProcessor
from myapp.celery_app import app

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

@app.task
def process_text_batch(texts_with_ids, batch_size=36):
    processor = TextBatchProcessor(batch_size)
    return processor.process_text_batch(texts_with_ids)
```

#### 3. `image_batch_processor.py` - Image-Specific Processing

```python
import datasets
import torch
from torch.utils.data import DataLoader
from myapp.models.image_vectorizer import ImageVectorizer
from tasks.base_batch_processor import BatchProcessor
from myapp.celery_app import app
from PIL import Image
import base64
import io

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

@app.task
def process_image_batch(images_with_ids, batch_size=36):
    processor = ImageBatchProcessor(batch_size)
    return processor.process_image_batch(images_with_ids)
```

### Summary

- **Separation of Concerns**: Splitting the text and image processing into two separate files (`text_batch_processor.py` and `image_batch_processor.py`) keeps the logic for each type of processing distinct and easier to manage.
- **Improved Maintainability**: This approach makes the codebase easier to navigate and modify. Any future changes specific to text or image processing can be made in their respective files without affecting the other.
- **Following SOLID Principles**: This organization improves adherence to **Single Responsibility Principle** and allows for better scalability, especially when extending the system to support additional types of data.
- **Modular Celery Task Definitions**: The `@app.task` decorators are compatible with these classes, keeping the task definitions clean and modular. Each task is responsible for instantiating and calling the appropriate class method, making the Celery integration seamless.

In conclusion, splitting the files for text and image processing is **not too much** and is actually a recommended approach, especially if your codebase is expected to grow or needs to be maintained by multiple developers. It helps enforce good software design practices, particularly around separation of concerns and single responsibility, making your codebase easier to maintain and extend in the long run.