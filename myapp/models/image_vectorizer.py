from transformers import CLIPVisionModelWithProjection, AutoFeatureExtractor
import time
import torch
import numpy as np
from datasets import Dataset, Image as DatasetsImage
from PIL import Image


class ImageVectorizer:
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.model_name = model_name
        self.vision_model = CLIPVisionModelWithProjection.from_pretrained(model_name)
        self.extractor = AutoFeatureExtractor.from_pretrained(model_name)
        self.vision_model.eval()

    def vectorize(self, image: Image.Image) -> dict:
        # Convert the PIL image to the datasets Image format
        ds = Dataset.from_dict({"Image": [image]}).cast_column("Image", DatasetsImage())
        
        # Extract the image tensors
        image_input = self.extractor(images=ds[0]['Image'], return_tensors="pt")
        
        # Generate the visual embedding
        with torch.no_grad():
            visual_embedding = self.vision_model(**image_input).image_embeds.squeeze().numpy()
        
        # Prepare the response
        response = {
            "embedding": visual_embedding.tolist(),
            "model": self.model_name,
            "timestamp": int(time.time())
        }
        
        return response
