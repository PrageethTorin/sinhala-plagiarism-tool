import torch
from transformers import XLMRobertaTokenizer, XLMRobertaModel

class SinhalaEmbeddingExtractor:
    def __init__(self):
        # xlm-roberta-base provides a strong balance of speed and depth for Sinhala
        self.model_name = 'xlm-roberta-base'
        self.tokenizer = XLMRobertaTokenizer.from_pretrained(self.model_name)
        self.model = XLMRobertaModel.from_pretrained(self.model_name)
        self.model.eval() 

    def get_embeddings(self, text):
        """Converts Sinhala text into a 768-dimension contextual vector."""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # We use the [CLS] token representation for the overall style vector
        return outputs.last_hidden_state[:, 0, :].numpy().flatten()