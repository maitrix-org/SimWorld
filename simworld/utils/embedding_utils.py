import torch
from transformers import CLIPModel, CLIPProcessor, CLIPTokenizer

device = "cuda" if torch.cuda.is_available() else "cpu"
model_ID = "openai/clip-vit-large-patch14-336"
model = CLIPModel.from_pretrained(model_ID).to(device)
processor = CLIPProcessor.from_pretrained(model_ID)
tokenizer = CLIPTokenizer.from_pretrained(model_ID)

def get_single_text_embedding(text: str) -> torch.Tensor:
    inputs = tokenizer(text, return_tensors = "pt").to(device)
    text_embeddings = model.get_text_features(**inputs)
    embedding_as_np = text_embeddings.cpu().detach().numpy()
    return embedding_as_np

def get_single_image_embedding(my_image) -> torch.Tensor:
    image = processor(
        text = None,
        images = my_image, 
        return_tensors="pt"
    )["pixel_values"].to(device)
    
    embedding = model.get_image_features(image)
    embedding_as_np = embedding.cpu().detach().numpy()
    return embedding_as_np
