from abc import ABC, abstractmethod
import torch
import requests
import numpy as np
from tqdm import tqdm
from myapp.config.config_loader import config_loader  # Import the config loader to access configuration settings

# Abstract base class to handle common batch processing tasks, meant to be inherited by specific processors (e.g., text, image)
class BatchProcessor(ABC):
    def __init__(self, batch_size=36):
        """
        Initializes the BatchProcessor with a given batch size.
        Args:
            batch_size (int): The size of each batch for processing.
        """
        self.batch_size = batch_size
        # Set the device to GPU if available, otherwise CPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Load the aggregation service URL from the configuration
        self.aggregation_service_url = config_loader.get_aggregation_service_url()

    def process_batches(self, data_loader, model):
        """
        Processes batches of data using the given model.
        Args:
            data_loader (DataLoader): DataLoader for providing batches of data.
            model (torch.nn.Module): The model used to generate embeddings.
        
        Returns:
            numpy.ndarray: A 2D array of embeddings generated for the data.
        """
        # Set the model to the appropriate device and set it to evaluation mode
        model.to(self.device)
        model.eval()
        outputs = []

        # Iterate through each batch in the data loader and generate embeddings
        for batch in tqdm(data_loader):
            with torch.no_grad():  # Disable gradient calculations to improve performance during inference
                embeddings = self._generate_embeddings(batch, model)
                # Move embeddings to CPU and append to the output list
                outputs.append(embeddings.to("cpu"))

        # Stack all generated embeddings into a single 2D NumPy array
        return np.vstack(outputs)

    def normalize_embeddings(self, embeddings):
        """
        Normalizes the embeddings to ensure consistent scaling.
        Args:
            embeddings (numpy.ndarray): A 2D array of generated embeddings.
        
        Returns:
            numpy.ndarray: The normalized embeddings.
        """
        # Normalize the embeddings across each vector (row-wise) for consistency
        return embeddings / np.linalg.norm(embeddings, axis=1)[:, np.newaxis]

    @abstractmethod
    def _generate_embeddings(self, batch, model):
        """
        Abstract method to be implemented by subclasses for generating embeddings.
        Args:
            batch (dict): The batch of data to process.
            model (torch.nn.Module): The model used to generate embeddings.
        
        Returns:
            torch.Tensor: The embeddings generated from the model.
        """
        pass  # This method must be implemented by any class that inherits from BatchProcessor

    def send_to_aggregation_service(self, ids, embeddings, embedding_type):
        """
        Sends the generated embeddings to the aggregation service for further processing or storage.
        Args:
            ids (list): A list of unique identifiers for each item in the batch.
            embeddings (numpy.ndarray): The generated embeddings.
            embedding_type (str): The type of embedding (e.g., "EMBEDDINGS_TEXT" or "EMBEDDINGS_IMAGE").
        
        Returns:
            dict: Response from the aggregation service.
        """
        # Prepare the payload with the list of embeddings, including their IDs and type
        payload = {
            "embeddings": [
                {
                    "id": ids[i],  # Unique identifier for each item
                    "embedding_type": embedding_type,  # Type of embedding (e.g., text, image)
                    "embedding": embeddings[i].tolist()  # Convert embedding to list format for JSON serialization
                }
                for i in range(len(ids))
            ]
        }

        # Send the payload to the aggregation service using a POST request
        response = requests.post(self.aggregation_service_url, json=payload)
        
        # Return the response as a JSON object
        return response.json()
