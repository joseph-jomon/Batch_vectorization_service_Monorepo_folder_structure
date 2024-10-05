from abc import ABC, abstractmethod
import torch
import requests
import numpy as np
from tqdm import tqdm
from myapp.config.config_loader import config_loader  # Import the config

class BatchProcessor(ABC):
    def __init__(self, batch_size=36):
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.aggregation_service_url = config_loader.get_aggregation_service_url()

    def process_batches(self, data_loader, model):
        model.to(self.device)
        model.eval()
        outputs = []

        for batch in tqdm(data_loader):
            with torch.no_grad():
                embeddings = self._generate_embeddings(batch, model)
                outputs.append(embeddings.to("cpu"))

        return np.vstack(outputs) 

    def normalize_embeddings(self, embeddings):
        return embeddings / np.linalg.norm(embeddings, axis=1)[:,np.newaxis]

    @abstractmethod
    def _generate_embeddings(self, batch, model):
        pass
    def send_to_aggregation_service(self, ids, embeddings, embedding_type):
        # Prepare the payload to send to the database service
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
        # Send the embeddings to the database service
        response = requests.post(self.aggregation_service_url, json=payload)
        return response.json()
