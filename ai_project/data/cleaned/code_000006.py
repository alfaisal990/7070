import torch
import torch.nn.functional as F
from ai_project.models.model import PhoenixTransformer
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer

class PhoenixInferenceEngine:
    """
    Inference Engine for Phoenix AI.
    Handles text generation using KV-caching, top-k/top-p sampling, and greedy search.
    Provides streaming and full-text generation interfaces.
    """
    def __init__(self, model: PhoenixTransformer, tokenizer: PhoenixTokenizer, device: str = "cuda"):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.model.to(self.device)
        self.model.eval()

    @torch.no_grad()
    def generate_stream(self, prompt: str, max_new_tokens: int = 512, temperature: str = 0.7, top_k: int = 50, top_p: float = 0.9):
        """
        Generates tokens in a streaming fashion (generator) using KV caching.
        """
        # Auto-wrap raw prompts into the SFT conversational structure if not present
        if "<|user|>" not in prompt:
            prompt = f"<|system|>\nYou are a helpful Python coding assistant.\n<|user|>\n{prompt}\n<|assistant|>\n"
            
        tokens = self.tokenizer.encode(prompt)
        tokens_tensor = torch.tensor([tokens], dtype=torch.long, device=self.device)
        seqlen = tokens_tensor.shape[1]
        
        # Ensure we do not generate beyond the model's maximum sequence length
        if seqlen >= self.model.args.max_seq_len:
            raise ValueError(f"Prompt length ({seqlen}) exceeds model max_seq_len ({self.model.args.max_seq_len})")
        max_new_tokens = min(max_new_tokens, self.model.args.max_seq_len - seqlen)
        
        # Reset model attention KV-caches
        for layer in self.model.layers:
            layer.attention.cache_k = None
            layer.attention.cache_v = None
            
        # Prefill phase: evaluate prompt and build KV cache
        logits, _ = self.model(tokens_tensor, use_cache=True, start_pos=0)
        next_token_logits = logits[:, -1, :]
        
        curr_pos = seqlen
        
        for _ in range(max_new_tokens):
            if temperature > 0.0:
                logits_scaled = next_token_logits / temperature
                
                # Top-K filtering
                if top_k > 0:
                    v, _ = torch.topk(logits_scaled, min(top_k, logits_scaled.size(-1)))
                    logits_scaled[logits_scaled < v[:, [-1]]] = float("-inf")
                    
                # Top-P (Nucleus) filtering
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(logits_scaled, descending=True, dim=-1)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    # Mask tokens with cumulative probability exceeding top_p
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = False
                    
                    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                    logits_scaled[indices_to_remove] = float("-inf")
                    
                probs = F.softmax(logits_scaled, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            else:
                # Greedy decoding
                next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
                
            token_id = next_token.item()
            if token_id == self.tokenizer.eos_id:
                break
                
            # Yield decoded token string
            yield self.tokenizer.decode([token_id])
            
            # Step phase: feed ONLY the single next token utilizing the existing KV cache
            next_token_logits, _ = self.model(next_token, use_cache=True, start_pos=curr_pos)
            next_token_logits = next_token_logits[:, -1, :]
            curr_pos += 1

    def generate(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7, top_k: int = 50, top_p: float = 0.9) -> str:
        """
        Generates full completed text.
        """
        return "".join(list(self.generate_stream(prompt, max_new_tokens, temperature, top_k, top_p)))
