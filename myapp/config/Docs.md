Sure! Here's the extended version of `config_loader.py` that will load all your settings from `config.yaml` and make them accessible throughout your project:

### Extended `config_loader.py`

**`config/config_loader.py`**:
```python
import yaml
import os

class ConfigLoader:
    def __init__(self, config_file_path="config/config.yaml"):
        self.config = self._load_config(config_file_path)

    def _load_config(self, config_file_path):
        # Load the YAML configuration file
        with open(config_file_path, "r") as file:
            return yaml.safe_load(file)

    def get_celery_broker_url(self):
        return self.config['celery']['broker_url']

    def get_celery_result_backend(self):
        return self.config['celery']['result_backend']

    def get_aggregation_service_url(self):
        return self.config['aggregation_service']['url']


# Instantiate the ConfigLoader to use throughout the project
config_loader = ConfigLoader()

# Usage examples:
#   config_loader.get_celery_broker_url()
#   config_loader.get_aggregation_service_url()
```

### Explanation

1. **`ConfigLoader` Class**:
   - A `ConfigLoader` class is created to encapsulate the logic of loading and retrieving configurations.
   - This makes accessing configuration values throughout the project easy and consistent.

2. **Private Method `_load_config()`**:
   - This method reads the configuration file (`config.yaml`) and loads its content into a dictionary (`self.config`).
   - The config file path is set to `config/config.yaml` by default, but it can be overridden if needed.

3. **Public Methods to Retrieve Configurations**:
   - `get_celery_broker_url()`, `get_celery_result_backend()`, and `get_aggregation_service_url()` provide easy access to each specific configuration value.
   - This method-based approach helps maintain control over how configurations are accessed and modified, thus adhering to the **Single Responsibility Principle**.

4. **Global `config_loader` Instance**:
   - A global instance, `config_loader`, is created at the end of the script. You can import and use `config_loader` throughout your project.
   - For example, in `tasks/base_batch_processor.py`, you would use:
     ```python
     from config.config_loader import config_loader

     self.aggregation_service_url = config_loader.get_aggregation_service_url()
     ```

### Example Usage in Project Files

#### Update `base_batch_processor.py` to Use `ConfigLoader`

**`tasks/base_batch_processor.py`**:
```python
from abc import ABC, abstractmethod
import torch
import requests
import numpy as np
from tqdm import tqdm
from config.config_loader import config_loader  # Import the config loader

class BatchProcessor(ABC):
    def __init__(self, batch_size=36):
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.aggregation_service_url = config_loader.get_aggregation_service_url()  # Use the config loader to get the URL

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
        response = requests.post(self.aggregation_service_url, json=payload)  # Use the configured URL
        return response.json()
```

### Summary

- The **`ConfigLoader` class** centralizes the configuration loading logic, providing easy access to various settings like Celery URLs and aggregation service URLs.
- **Getter methods** (`get_celery_broker_url()`, `get_aggregation_service_url()`, etc.) allow a clean and consistent way to access configuration values.
- The **global instance (`config_loader`)** can be imported and used across different modules in the project, making configuration management clean, modular, and adhering to **SOLID** principles.
  
This solution avoids hard-coding configurations, follows best practices for configuration management, and suits your preference for config files over environment variables.