Certainly! Below are the folder structures and the corresponding code for each service: **Data Collection Service**, **Batch Vectorization Service**, and **Elasticsearch Storage Service**. Each service is designed to be deployed as a separate microservice using Traefik and Docker, with FastAPI as the web framework.

### **1. Data Collection Service**

**Folder Structure:**

```plaintext
data_collection_service/
├── app/
│   ├── __init__.py
│   ├── tasks.py
│   ├── utils/
│   │   ├── flowfact_api.py
│   ├── config.py
├── celery.py
├── Dockerfile
├── requirements.txt
└── tests/
    ├── test_data_collection.py
```

**File Contents:**

- **`app/__init__.py`**:
  ```python
  # This file can be empty or contain package-level initializations if needed.
  ```

- **`app/tasks.py`**:
  ```python
  from celery import Celery
  from app.utils.flowfact_api import fetch_data_from_flowfact, preprocess_data

  app = Celery('data_collection', broker='redis://redis:6379/0')

  @app.task
  def collect_and_send_data():
      # Fetch data from Flowfact API
      raw_data = fetch_data_from_flowfact()

      # Preprocess the data
      preprocessed_data = preprocess_data(raw_data)

      # Send preprocessed data to the vectorization service
      send_to_vectorization_service.delay(preprocessed_data)

  @app.task
  def send_to_vectorization_service(preprocessed_data):
      # Code to send data to the vectorization service
      # This can be via an HTTP API or a message broker
      pass
  ```

- **`app/utils/flowfact_api.py`**:
  ```python
  import requests

  def fetch_data_from_flowfact():
      # Implement the GET request to the Flowfact API
      response = requests.get("https://api.flowfact.de/your-endpoint")
      return response.json()

  def preprocess_data(raw_data):
      # Implement your preprocessing logic
      preprocessed_data = []
      for item in raw_data:
          # Example: Normalize and clean text data
          processed_item = {
              "text": item.get("text"),
              "metadata": item.get("metadata")
          }
          preprocessed_data.append(processed_item)
      return preprocessed_data
  ```

- **`app/config.py`**:
  ```python
  # Configuration settings for the service
  FLOWFACT_API_URL = "https://api.flowfact.de/your-endpoint"
  ```

- **`celery.py`**:
  ```python
  from celery import Celery

  app = Celery('data_collection', broker='redis://redis:6379/0')
  app.config_from_object('app.config')
  ```

- **`Dockerfile`**:
  ```dockerfile
  FROM python:3.9-slim

  WORKDIR /app

  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY . .

  CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=info"]
  ```

- **`requirements.txt`**:
  ```plaintext
  fastapi
  celery
  redis
  requests
  ```

- **`tests/test_data_collection.py`**:
  ```python
  # Implement unit tests for your data collection and preprocessing logic
  ```

### **2. Batch Vectorization Service**

**Folder Structure:**

```plaintext
batch_vectorization_service/
├── app/
│   ├── __init__.py
│   ├── tasks.py
│   ├── models/
│   │   ├── text_vectorizer.py
│   │   ├── image_vectorizer.py
│   ├── utils/
│   │   ├── preprocessor.py
│   └── config.py
├── celery.py
├── Dockerfile
├── requirements.txt
└── tests/
    ├── test_batch_vectorization.py
```

**File Contents:**

- **`app/__init__.py`**:
  ```python
  # This file can be empty or contain package-level initializations if needed.
  ```

- **`app/tasks.py`**:
  ```python
  from celery import Celery
  from app.models.text_vectorizer import TextVectorizer
  from app.models.image_vectorizer import ImageVectorizer

  app = Celery('batch_vectorization', broker='redis://redis:6379/0')

  text_vectorizer = TextVectorizer()
  image_vectorizer = ImageVectorizer()

  @app.task
  def process_data(preprocessed_data):
      if 'text' in preprocessed_data:
          vector = text_vectorizer.vectorize(preprocessed_data['text'])
      elif 'image' in preprocessed_data:
          vector = image_vectorizer.vectorize(preprocessed_data['image'])

      send_to_storage_service.delay(vector, preprocessed_data['metadata'])

  @app.task
  def send_to_storage_service(vector, metadata):
      # Code to send the vector to the storage service
      pass
  ```

- **`app/models/text_vectorizer.py`**:
  ```python
  from transformers import AutoTokenizer, AutoModel
  import numpy as np

  class TextVectorizer:
      def __init__(self, model_name="bert-base-uncased"):
          self.tokenizer = AutoTokenizer.from_pretrained(model_name)
          self.model = AutoModel.from_pretrained(model_name)

      def vectorize(self, text: str) -> np.ndarray:
          inputs = self.tokenizer(text, return_tensors='pt')
          outputs = self.model(**inputs)
          return outputs.last_hidden_state.mean(dim=1).detach().numpy()
  ```

- **`app/models/image_vectorizer.py`**:
  ```python
  from torchvision import models, transforms
  from PIL import Image
  import torch
  import numpy as np

  class ImageVectorizer:
      def __init__(self):
          self.model = models.resnet50(pretrained=True)
          self.model.eval()
          self.preprocess = transforms.Compose([
              transforms.Resize(256),
              transforms.CenterCrop(224),
              transforms.ToTensor(),
              transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
          ])

      def vectorize(self, image: Image.Image) -> np.ndarray:
          img_t = self.preprocess(image)
          batch_t = torch.unsqueeze(img_t, 0)
          with torch.no_grad():
              output = self.model(batch_t)
          return output.numpy()
  ```

- **`app/utils/preprocessor.py`**:
  ```python
  def preprocess_text(text):
      # Implement text preprocessing logic
      return text

  def preprocess_image(image):
      # Implement image preprocessing logic
      return image
  ```

- **`app/config.py`**:
  ```python
  # Configuration settings for the service
  ```

- **`celery.py`**:
  ```python
  from celery import Celery

  app = Celery('batch_vectorization', broker='redis://redis:6379/0')
  app.config_from_object('app.config')
  ```

- **`Dockerfile`**:
  ```dockerfile
  FROM python:3.9-slim

  WORKDIR /app

  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY . .

  CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=info"]
  ```

- **`requirements.txt`**:
  ```plaintext
  fastapi
  celery
  redis
  transformers
  torch
  torchvision
  pillow
  ```

- **`tests/test_batch_vectorization.py`**:
  ```python
  # Implement unit tests for your vectorization logic
  ```

### **3. Elasticsearch Storage Service**

**Folder Structure:**

```plaintext
elasticsearch_storage_service/
├── app/
│   ├── __init__.py
│   ├── tasks.py
│   ├── utils/
│   │   ├── elasticsearch_client.py
│   └── config.py
├── celery.py
├── Dockerfile
├── requirements.txt
└── tests/
    ├── test_elasticsearch_storage.py
```

**File Contents:**

- **`app/__init__.py`**:
  ```python
  # This file can be empty or contain package-level initializations if needed.
  ```

- **`app/tasks.py`**:
  ```python
  from celery import Celery
  from app.utils.elasticsearch_client import store_vector_in_elasticsearch

  app = Celery('elasticsearch_storage', broker='redis://redis:6379/0')

  @app.task
  def store_vector(vector, metadata):
      store_vector_in_elasticsearch(vector, metadata)
  ```

- **`app/utils/elasticsearch_client.py`**:
  ```python
  from elasticsearch import Elasticsearch

  es = Elasticsearch([{"host": "localhost", "port": 9200}])

  def store_vector_in_elasticsearch(vector, metadata):
      es.index(index="vectors", body={
          "vector": vector,
          **metadata
      })
  ```

- **`app/config.py`**:
  ```python
  # Configuration settings for the Elasticsearch client
  ELASTICSEARCH_HOST = "localhost"
  ELASTICSEARCH_PORT = 9200
 

 ```

- **`celery.py`**:
  ```python
  from celery import Celery

  app = Celery('elasticsearch_storage', broker='redis://redis:6379/0')
  app.config_from_object('app.config')
  ```

- **`Dockerfile`**:
  ```dockerfile
  FROM python:3.9-slim

  WORKDIR /app

  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY . .

  CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=info"]
  ```

- **`requirements.txt`**:
  ```plaintext
  fastapi
  celery
  redis
  elasticsearch
  ```

- **`tests/test_elasticsearch_storage.py`**:
  ```python
  # Implement unit tests for your Elasticsearch storage logic
  ```

### **Conclusion**

Each service is structured to be a self-contained microservice with its own Dockerfile, dependencies, and task processing via Celery. The services interact through message queues (managed by Celery and Redis), and each service adheres to the single responsibility principle:

1. **Data Collection Service**: Handles data retrieval and preprocessing.
2. **Batch Vectorization Service**: Handles vector generation for text and images.
3. **Elasticsearch Storage Service**: Handles storing vectors in the Elasticsearch database.

This structure is designed to work well in a microservices architecture, where each service can be independently deployed, scaled, and maintained.