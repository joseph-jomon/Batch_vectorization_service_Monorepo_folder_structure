import requests
from myapp.celery_app import app
from myapp.models.text_vectorizer import TextVectorizer
from myapp.models.image_vectorizer import ImageVectorizer
import datasets

@app.task
def process_text_batch(dataframe, batch_size: int = 36):
    """
    Task to process a batch of text data, generate vector embeddings, 
    and send them to the database service.

    Args:
        dataframe (pandas.DataFrame): The pandas DataFrame containing the text data.
        batch_size (int): The batch size for processing.

    Returns:
        dict: A dictionary with the status of the database write operation.
    """
    # Convert the pandas DataFrame to a Hugging Face Dataset
    ds = datasets.Dataset.from_pandas(dataframe)

    # Initialize the TextVectorizer
    vectorizer = TextVectorizer()

    # Generate text embeddings
    text_embeddings = vectorizer.vectorize(ds, batch_size=batch_size)

    # Prepare the payload to send to the database service
    payload = {
        "embeddings": text_embeddings.tolist(),
        "metadata": dataframe.to_dict()  # Include any necessary metadata
    }

    # Send the embeddings to the database service
    response = requests.post("http://database_service:8001/store-vectors", json=payload)

    return response.json()

@app.task
def process_image_batch(dataframe, batch_size: int = 36):
    """
    Task to process a batch of image data, generate vector embeddings, 
    and send them to the database service.

    Args:
        dataframe (pandas.DataFrame): The pandas DataFrame containing the image data.
        batch_size (int): The batch size for processing.

    Returns:
        dict: A dictionary with the status of the database write operation.
    """
    # Convert the pandas DataFrame to a Hugging Face Dataset with Image type
    ds = datasets.Dataset.from_pandas(dataframe).cast_column("Image", datasets.Image())

    # Initialize the ImageVectorizer
    vectorizer = ImageVectorizer()

    # Generate image embeddings
    image_embeddings = vectorizer.vectorize(ds, batch_size=batch_size)

    # Prepare the payload to send to the database service
    payload = {
        "embeddings": image_embeddings.tolist(),
        "metadata": dataframe.to_dict()  # Include any necessary metadata
    }

    # Send the embeddings to the database service
    response = requests.post("http://database_service:8001/store-vectors", json=payload)

    return response.json()
