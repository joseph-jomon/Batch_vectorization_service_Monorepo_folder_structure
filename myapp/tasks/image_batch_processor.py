import datasets
import torch
from torch.utils.data import DataLoader
from myapp.models.image_vectorizer import ImageVectorizer
from tasks.base_batch_processor import BatchProcessor
from myapp.celery_app import app
from PIL import Image
import base64
import io

class ImageBatchProcessor(BatchProcessor):
    def __init__(self, batch_size=36):
        super().__init__(batch_size)
        self.vectorizer = ImageVectorizer()

    def process_image_batch(self, images_with_ids):
        ids = [item["id"] for item in images_with_ids]
        images = [item["image"] for item in images_with_ids]
        pil_images = [Image.open(io.BytesIO(base64.b64decode(img))) for img in images]

        ds = datasets.Dataset.from_dict({"Image": pil_images})

        def image_collate(examples):
            images = [self.vectorizer.preprocess(image) for image in examples['Image']]
            return torch.stack(images)

        image_dl = DataLoader(ds, batch_size=self.batch_size, shuffle=False, num_workers=0, collate_fn=image_collate)

        embeddings = self.process_batches(image_dl, self.vectorizer.model)
        normalized_embeddings = self.normalize_embeddings(embeddings)

        return self.send_to_aggregation_service(ids, normalized_embeddings, "EMBEDDINGS_IMAGE")

    def _generate_embeddings(self, batch, model):
        return model(batch.to(self.device)).squeeze()

@app.task
def process_image_batch(images_with_ids, batch_size=36):
    processor = ImageBatchProcessor(batch_size)
    return processor.process_image_batch(images_with_ids)
