import datasets
import torch
from torch.utils.data import DataLoader
from myapp.models.image_vectorizer import ImageVectorizer
from myapp.tasks.base_batch_processor import BatchProcessor
from myapp.celery_app import app
from PIL import Image
import base64
import io

# Class that inherits from BatchProcessor to handle image batch processing
class ImageBatchProcessor(BatchProcessor):
    def __init__(self, batch_size=36):
        """
        Initializes the ImageBatchProcessor with a given batch size.
        Args:
            batch_size (int): The size of each batch for processing.
        """
        super().__init__(batch_size)
        # Initialize the ImageVectorizer to handle image vectorization
        self.vectorizer = ImageVectorizer()

    def process_and_send_image_batch(self, images_with_ids, company_name):
        """
        Processes a batch of image data to generate vector embeddings.
        Args:
            images_with_ids (list): A list of dictionaries, each containing 'id' and base64-encoded 'image'.
        
        Returns:
            dict: Status of sending the embeddings to the aggregation service.
        """
        # Extract the IDs and corresponding base64-encoded images from the input data
        ids = [item["id"] for item in images_with_ids]
        images = [item["image"] for item in images_with_ids]

        # Decode the base64-encoded images and convert them to PIL Images
        pil_images = [Image.open(io.BytesIO(base64.b64decode(img))) for img in images]

        # Convert the list of PIL images into a Hugging Face Dataset for easier handling
        ds = datasets.Dataset.from_dict({"Image": pil_images})

        # Define a collate function to preprocess and stack the images for batch processing
        def image_collate(examples):
            images = [self.vectorizer.preprocess(image) for image in examples['Image']]  # Preprocess each image
            return torch.stack(images)  # Stack images into a single tensor

        # Create a DataLoader to handle batch processing of the dataset
        image_dl = DataLoader(ds, batch_size=self.batch_size, shuffle=False, num_workers=0, collate_fn=image_collate)

        # Process the image batches through the vectorizer model
        embeddings = self.process_batches(image_dl, self.vectorizer.model)

        # Normalize the embeddings to ensure they are on a consistent scale
        normalized_embeddings = self.normalize_embeddings(embeddings)

        # Send the embeddings to the aggregation service
        return self.send_to_aggregation_service(ids, normalized_embeddings, "EMBEDDINGS_IMAGE", company_name)

    def _generate_embeddings(self, batch, model):
        """
        Generates embeddings for a given batch of images using the specified model.
        Args:
            batch (torch.Tensor): The batch of images to be processed.
            model (torch.nn.Module): The model used to generate the embeddings.
        
        Returns:
            torch.Tensor: The resulting embeddings.
        """
        # Pass the batch of images through the model and return the embeddings
        return model(batch.to(self.device)).squeeze()

# Define a Celery task to  process a batch of image data
@app.task
def process_image_batch_task(images_with_ids, company_name, batch_size=36):
    """
    Celery task to process a batch of image data and generate embeddings.
    Args:
        images_with_ids (list): A list of dictionaries, each containing 'id' and base64-encoded 'image'.
        batch_size (int): The size of each batch for processing.

    Returns:
        dict: Status of sending the embeddings to the aggregation service.
    """
    # Create an instance of ImageBatchProcessor and use it to process the batch
    processor = ImageBatchProcessor(batch_size)
    # Call the synchronous method directly
    return processor.process_and_send_image_batch(images_with_ids, company_name)
