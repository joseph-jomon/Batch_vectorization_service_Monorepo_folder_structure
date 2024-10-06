In your TextBatchProcessor implementation, the send_to_aggregation_service method from the BatchProcessor class is used, which I've updated to use httpx in an asynchronous fashion. Since process_text_batch is a Celery task, there are a few changes required to handle async properly.

Changes to Implement Async httpx in TextBatchProcessor
Make process_text_batch Asynchronous:
Since send_to_aggregation_service is now asynchronous, the process_text_batch method should also be converted to an asynchronous method.
The Celery task needs to handle the async nature of the new method, which means we need to modify how we interact with Celery to ensure async compatibility.
Here's the updated version of text_batch_processor.py:

text_batch_processor.py:

python
Copy code
import datasets
import torch
from torch.utils.data import DataLoader
from myapp.models.text_vectorizer import TextVectorizer
from myapp.tasks.base_batch_processor import BatchProcessor
from myapp.celery_app import app
import asyncio  # Import asyncio for async processing

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
        Processes a batch of text data to generate vector embeddings.
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

        # Send the embeddings to the aggregation service asynchronously
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

# Define a Celery task to asynchronously process a batch of text data
@app.task
def process_text_batch(texts_with_ids, batch_size=36):
    """
    Celery task to process a batch of text data and generate embeddings.
    Args:
        texts_with_ids (list): A list of dictionaries, each containing 'id' and 'immo_text'.
        batch_size (int): The size of each batch for processing.

    Returns:
        dict: Status of sending the embeddings to the aggregation service.
    """
    # Create an instance of TextBatchProcessor and use it to process the batch
    processor = TextBatchProcessor(batch_size)
    
    # As Celery does not directly support async, run the async function using asyncio
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(processor.process_text_batch(texts_with_ids))
Key Changes Explained:
Make process_text_batch Method Asynchronous:

async def process_text_batch(): The method is now asynchronous, allowing you to use await with the new send_to_aggregation_service() method.
Updated the call to await self.send_to_aggregation_service() to handle the HTTP request asynchronously.
Handling Async in Celery Task:

Celery does not natively support async functions. Therefore, to run an async function in a Celery task, we use asyncio.get_event_loop() and loop.run_until_complete().
In the Celery task process_text_batch(), after creating an instance of TextBatchProcessor, we run the async process_text_batch() method using the event loop.
Summary of Updates:
Asynchronous Support: Updated send_to_aggregation_service and process_text_batch to be asynchronous, allowing the service to send requests without blocking.
Celery Task: Used asyncio to run the async task, since Celery itself doesn't support async natively.
Improved Scalability: These changes will help your service to be more scalable by not blocking during HTTP requests, which is especially important when working with microservices that rely heavily on network I/O.
Additional Recommendations:
Celery with AsyncIO: If you need more native support for async tasks in Celery, you might consider using third-party solutions like aiocelery, which offer experimental support for async operations in Celery.
Error Handling: Consider adding error handling in both send_to_aggregation_service() and the Celery task to catch network errors or any unexpected issues during execution.