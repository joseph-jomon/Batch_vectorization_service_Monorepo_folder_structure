import datasets
import torch
from torch.utils.data import DataLoader
from myapp.models.text_vectorizer import TextVectorizer
from tasks.base_batch_processor import BatchProcessor
from myapp.celery_app import app

class TextBatchProcessor(BatchProcessor):
    def __init__(self, batch_size=36):
        super().__init__(batch_size)
        self.vectorizer = TextVectorizer()

    def process_text_batch(self, texts_with_ids):
        ids = [item["id"] for item in texts_with_ids]
        texts = [item["immo_text"] for item in texts_with_ids]

        ds = datasets.Dataset.from_dict({"Combined_Text": texts})

        def text_collate(examples):
            return self.vectorizer.tokenizer.batch_encode_plus(
                [example['Combined_Text'] for example in examples], 
                truncation=True, 
                padding=True,
                return_tensors="pt"
            )

        text_dl = DataLoader(ds, batch_size=self.batch_size, shuffle=False, num_workers=0, collate_fn=text_collate)

        embeddings = self.process_batches(text_dl, self.vectorizer.text_model)
        normalized_embeddings = self.normalize_embeddings(embeddings)

        return self.send_to_aggregation_service(ids, normalized_embeddings, "EMBEDDINGS_TEXT")

    def _generate_embeddings(self, batch, model):
        return model(**{k: v.to(self.device) for k, v in batch.items()}).text_embeds.squeeze()

@app.task
def process_text_batch(texts_with_ids, batch_size=36):
    processor = TextBatchProcessor(batch_size)
    return processor.process_text_batch(texts_with_ids)
