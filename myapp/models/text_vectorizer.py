from transformers import AutoTokenizer
from transformers import CLIPTextModelWithProjection
import torch
import numpy as np
from tqdm import tqdm

class TextVectorizer:
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initializes the TextVectorizer with the specified model.
        
        Args:
            model_name (str): The name of the pre-trained model to use.
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.text_model = CLIPTextModelWithProjection.from_pretrained(model_name)
        self.text_model.eval()  # Set the model to evaluation mode
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.text_model.to(self.device)

    def text_collate(self, examples):
        """
        Collate function to process a batch of examples.

        Args:
            examples (list): List of examples from the dataset.

        Returns:
            dict: Batch encoded input for the model.
        """
        return self.tokenizer.batch_encode_plus(
            [e['Combined_Text'] for e in examples], 
            truncation=True, 
            padding=True,
            return_tensors="pt"
        )

    def vectorize(self, ds, batch_size: int = 36):
        """
        Generates vector embeddings for the text data in the dataset.

        Args:
            ds (datasets.Dataset): The Hugging Face dataset containing the text data.
            batch_size (int): The batch size for processing.

        Returns:
            np.ndarray: The normalized text embeddings.
        """
        text_dl = torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0, collate_fn=self.text_collate)
        outputs = []

        for batch in tqdm(text_dl):
            with torch.no_grad():
                text_embeddings = self.text_model(**{k: v.to(self.device) for k,v in batch.items()}).text_embeds.squeeze()
                outputs.append(text_embeddings.to("cpu"))

        text_embeddings = np.vstack(outputs)
        text_embeddings_normed = text_embeddings / np.linalg.norm(text_embeddings, axis=1)[:, np.newaxis]
        return text_embeddings_normed
