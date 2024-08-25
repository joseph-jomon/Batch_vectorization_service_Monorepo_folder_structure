import requests
from myapp.celery_app import app
from myapp.models.text_vectorizer import TextVectorizer
from myapp.models.image_vectorizer import ImageVectorizer
import datasets
import torch
import numpy as np
from tqdm import tqdm

@app.task
def process_text_batch(texts_with_ids: list, batch_size: int = 36):
    """
    Task to process a batch of text data, generate vector embeddings, 
    and send them to the database service.

    Args:
        texts_with_ids (list): The list of dictionaries, each containing 'id' and 'text'.
        batch_size (int): The batch size for processing.

    Returns:
        dict: A dictionary with the status of the database write operation.
    """
    # Extract the texts and their corresponding IDs
    ids = [item["id"] for item in texts_with_ids]
    texts = [item["text"] for item in texts_with_ids]

    # Convert the list of texts to a Hugging Face Dataset
    ds = datasets.Dataset.from_dict({"Combined_Text": texts})

    # Initialize the TextVectorizer
    vectorizer = TextVectorizer()

    # Define the text collate function
    def text_collate(examples):
        return vectorizer.tokenizer.batch_encode_plus(
            examples['Combined_Text'], 
            truncation=True, 
            padding=True,
            return_tensors="pt"
        )

    # Prepare DataLoader to handle batch processing within the task
    text_dl = torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0, collate_fn=text_collate)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vectorizer.text_model.to(device)
    vectorizer.text_model.eval()

    outputs = []
    for batch in tqdm(text_dl):
        with torch.no_grad():
            text_embeddings = vectorizer.text_model(**{k: v.to(device) for k, v in batch.items()}).text_embeds.squeeze()
            outputs.append(text_embeddings.to("cpu"))

    text_embeddings = np.vstack(outputs)
    text_embeddings_normed = text_embeddings / np.linalg.norm(text_embeddings, axis=1)[:, np.newaxis]

    # Prepare the payload to send to the database service
    payload = {
        "embeddings": text_embeddings_normed.tolist(),
        "ids": ids,  # Include the corresponding IDs
        "metadata": {"texts": texts}  # Include any necessary metadata
    }

    # Send the embeddings to the database service
    response = requests.post("http://localhost:8000/dummy-store-vectors/", json=payload)

    return response.json()

@app.task
def process_image_batch(images_with_ids: list, batch_size: int = 36):
    """
    Task to process a batch of image data, generate vector embeddings, 
    and send them to the database service.

    Args:
        images_with_ids (list): The list of dictionaries, each containing 'id' and base64-encoded 'image'.
        batch_size (int): The batch size for processing.

    Returns:
        dict: A dictionary with the status of the database write operation.
    """
    # Extract the images and their corresponding IDs
    ids = [item["id"] for item in images_with_ids]
    images = [item["image"] for item in images_with_ids]

    # Convert the list of images to PIL Images
    pil_images = [Image.open(io.BytesIO(base64.b64decode(img))) for img in images]

    # Convert the PIL Images to a Hugging Face Dataset
    ds = datasets.Dataset.from_dict({"Image": pil_images})

    # Initialize the ImageVectorizer
    vectorizer = ImageVectorizer()

    # Define the image collate function
    def image_collate(examples):
        images = [vectorizer.preprocess(image) for image in examples['Image']]
        return torch.stack(images)

    # Prepare DataLoader to handle batch processing within the task
    image_dl = torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0, collate_fn=image_collate)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vectorizer.model.to(device)
    vectorizer.model.eval()

    outputs = []
    for batch in tqdm(image_dl):
        with torch.no_grad():
            image_embeddings = vectorizer.model(batch.to(device)).squeeze()
            outputs.append(image_embeddings.to("cpu"))

    image_embeddings = torch.cat(outputs)
    image_embeddings_normed = image_embeddings / image_embeddings.norm(dim=1, keepdim=True)

    # Prepare the payload to send to the database service
    payload = {
        "embeddings": image_embeddings_normed.tolist(),
        "ids": ids,  # Include the corresponding IDs
        "metadata": {"images": images}  # Include any necessary metadata
    }

    # Send the embeddings to the database service
    response = requests.post("http://localhost:8000/dummy-store-vectors/", json=payload)

    return response.json()