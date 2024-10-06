To make the TextBatchProcessor fully compatible with httpx for asynchronous requests, and also to align it with modern asynchronous programming (which is ideal for batch processing and FastAPI/Celery-based systems), we need to modify the existing code to integrate asynchronous methods.

Here's what we will do:

Convert the process_text_batch method to support async.
Update send_to_aggregation_service to be async, as you've already done in BatchProcessor.
Ensure that the Celery task is asynchronous by adjusting how it interacts with the new async methods.
Updated Code for TextBatchProcessor
python
Copy code
import datasets
import torch
from torch.utils.data import DataLoader
from myapp.models.text_vectorizer import TextVectorizer
from myapp.tasks.base_batch_processor import BatchProcessor
from myapp.celery_app import app
import asyncio  # Import asyncio to run asynchronous tasks

# Class that inherits from BatchProcessor to handle text batch processing
class TextBatchProcessor(BatchProcessor):
    def __init__(self, batch_size=36):
        """
        Initializes the TextBatchProcessor with a given batch size.
        Args:
            batch_size (int): The size of each batch for processing.
        """
        super().__init__(batch_size)
        # Initialize the TextVectorizer to handle text vectorization
        self.vectorizer = TextVectorizer()

    async def process_text_batch(self, texts_with_ids):
        """
        Asynchronously processes a batch of text data to generate vector embeddings.
        Args:
            texts_with_ids (list): A list of dictionaries, each containing an 'id' and 'immo_text'.

        Returns:
            dict: Status of sending the embeddings to the aggregation service.
        """
        # Extract the IDs and corresponding text values from the input data
        ids = [item["id"] for item in texts_with_ids]
        texts = [item["immo_text"] for item in texts_with_ids]

        # Convert the list of texts into a Hugging Face Dataset for efficient handling
        ds = datasets.Dataset.from_dict({"Combined_Text": texts})

        # Define a collate function to tokenize and prepare batches of text for processing
        def text_collate(examples):
            return self.vectorizer.tokenizer.batch_encode_plus(
                [example['Combined_Text'] for example in examples],  # Extract 'Combined_Text' from each dictionary
                truncation=True,  # Truncate the text if it's too long
                padding=True,     # Pad the text sequences to make them uniform length
                return_tensors="pt"  # Return the tensors in PyTorch format
            )

        # Create a DataLoader to handle batch processing of the dataset
        text_dl = DataLoader(ds, batch_size=self.batch_size, shuffle=False, num_workers=0, collate_fn=text_collate)

        # Process the text batches through the vectorizer model
        embeddings = self.process_batches(text_dl, self.vectorizer.text_model)
        
        # Normalize the embeddings to ensure they are on a consistent scale
        normalized_embeddings = self.normalize_embeddings(embeddings)

        # Send the embeddings to the aggregation service (async)
        return await self.send_to_aggregation_service(ids, normalized_embeddings, "EMBEDDINGS_TEXT")

    def _generate_embeddings(self, batch, model):
        """
        Generates embeddings for a given batch of data using the specified model.
        Args:
            batch (dict): The batch of tokenized text data.
            model (torch.nn.Module): The model used to generate the embeddings.

        Returns:
            torch.Tensor: The resulting embeddings.
        """
        # Move the batch to the correct device and pass it through the model to get embeddings
        return model(**{k: v.to(self.device) for k, v in batch.items()}).text_embeds.squeeze()

# Define an asynchronous Celery task to process a batch of text data
@app.task
async def process_text_batch(texts_with_ids, batch_size=36):
    """
    Asynchronously processes a batch of text data and generates embeddings.
    Args:
        texts_with_ids (list): A list of dictionaries, each containing 'id' and 'immo_text'.
        batch_size (int): The size of each batch for processing.

    Returns:
        dict: Status of sending the embeddings to the aggregation service.
    """
    # Create an instance of TextBatchProcessor and use it to process the batch
    processor = TextBatchProcessor(batch_size)
    return await processor.process_text_batch(texts_with_ids)
Key Changes and Explanations
Asynchronous process_text_batch:

The process_text_batch method inside TextBatchProcessor has been converted to async to make use of non-blocking I/O when sending the embeddings to the aggregation service via the async send_to_aggregation_service method.
This ensures that HTTP requests made to the aggregation service do not block the main thread, making the entire operation more scalable.
Asynchronous Celery Task:

The Celery task is now defined as an async function (async def), allowing it to call the TextBatchProcessor asynchronously and handle batch processing and HTTP requests in a non-blocking manner.
Awaiting send_to_aggregation_service:

Since send_to_aggregation_service is now asynchronous (from the changes in BatchProcessor), the call to this method in process_text_batch is prefixed with await to ensure it runs asynchronously.
Async-Safe Data Handling:

Although the DataLoader and embedding generation are synchronous processes (because they rely on PyTorch operations), the HTTP requests to external services (aggregation service) can be async, allowing your overall service to be more responsive and efficient when sending data to the aggregation service.
Benefits of This Update
Non-blocking HTTP Requests:

The batch processor will not block the event loop when making HTTP requests to the aggregation service, meaning it can handle many requests in parallel, increasing throughput.
Improved Scalability:

By making the Celery tasks asynchronous, you ensure that the system can scale better as it can handle multiple batches of data more efficiently, especially when there are slow network calls to the aggregation service.
Consistency in Asynchronous Operations:

If the entire stack (including the aggregation service and other microservices) uses asynchronous operations, this update keeps the architecture consistent and modern.
Next Steps
Ensure that the aggregation service is able to handle asynchronous requests if necessary. Since httpx is used for making the requests, everything is non-blocking on both ends.
Test the new asynchronous flow with Celery, as it might require configuring Celery to work properly with async tasks if not already done.
This should now fully integrate asynchronous capabilities into your TextBatchProcessor, leveraging httpx and async programming for more efficient processing. Let me know if you have any further questions!