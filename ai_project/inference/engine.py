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
    def generate_stream(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7, top_k: int = 50, top_p: float = 0.9):
        """
        Generates tokens in a streaming fashion (generator) using KV caching.
        """
        import time
        # Auto-wrap raw prompts into the SFT conversational structure if not present
        if "<|user|>" not in prompt:
            prompt = f"<|system|>\nYou are a helpful Python coding assistant.\n<|user|>\n{prompt}\n<|assistant|>\n"
            
        # Fallback for untrained / empty model to allow end-to-end integration testing with readable text
        if not getattr(self.model, "is_trained", True):
            mock_response = (
                "Greetings! I am Phoenix AI, your local coding assistant.\n\n"
                "The model is currently running in **untrained/mock mode** because no SFT or pretraining checkpoints were found.\n\n"
                "However, all systems (FastAPI backend, secure code execution Sandbox, and Vector database memory) are fully functional!\n\n"
                "Try out the 'Code Sandbox' tab or the 'Semantic Memory' tab to test them."
            )
            # Yield word by word to simulate streaming
            words = mock_response.split(" ")
            num_tokens = len(words)
            prefill_time = 0.05
            
            t_decode_start = time.time()
            for word in words:
                yield word + " "
                time.sleep(0.03)
            decode_time = time.time() - t_decode_start
            
            monitor = getattr(self, "monitor", None)
            if monitor is not None:
                monitor.record_generation(num_tokens, prefill_time, decode_time)
            return
            
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
        t_prefill_start = time.time()
        logits, _ = self.model(tokens_tensor, use_cache=True, start_pos=0)
        next_token_logits = logits[:, -1, :]
        prefill_time = time.time() - t_prefill_start
        
        curr_pos = seqlen
        num_tokens = 0
        t_decode_start = time.time()
        
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
            num_tokens += 1
            
            # Step phase: feed ONLY the single next token utilizing the existing KV cache
            next_token_logits, _ = self.model(next_token, use_cache=True, start_pos=curr_pos)
            next_token_logits = next_token_logits[:, -1, :]
            curr_pos += 1

        decode_time = time.time() - t_decode_start
        
        monitor = getattr(self, "monitor", None)
        if monitor is not None:
            monitor.record_generation(num_tokens, prefill_time, decode_time)

    @torch.no_grad()
    def generate_speculative(self, prompt: str, draft_model=None, max_new_tokens: int = 512, K: int = 4):
        """
        Generates tokens in a speculative fashion using a draft model for proposal
        and base model for parallel validation.
        """
        if draft_model is None:
            if not hasattr(self, "_cached_draft_model") or self._cached_draft_model is None:
                from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
                draft_args = PhoenixModelArgs(
                    vocab_size=self.model.args.vocab_size,
                    n_layers=1,
                    dim=64,
                    n_heads=2,
                    hidden_dim=128,
                    max_seq_len=self.model.args.max_seq_len
                )
                self._cached_draft_model = PhoenixTransformer(draft_args).to(self.device)
                self._cached_draft_model.eval()
            draft_model = self._cached_draft_model

        if "<|user|>" not in prompt:
            prompt = f"<|system|>\nYou are a helpful Python coding assistant.\n<|user|>\n{prompt}\n<|assistant|>\n"

        if not getattr(self.model, "is_trained", True):
            for chunk in self.generate_stream(prompt, max_new_tokens=max_new_tokens):
                yield chunk
            return

        tokens = self.tokenizer.encode(prompt)
        tokens_tensor = torch.tensor([tokens], dtype=torch.long, device=self.device)
        seqlen = tokens_tensor.shape[1]

        if seqlen >= self.model.args.max_seq_len:
            raise ValueError(f"Prompt length ({seqlen}) exceeds model max_seq_len ({self.model.args.max_seq_len})")

        max_new_tokens = min(max_new_tokens, self.model.args.max_seq_len - seqlen)

        # Reset caches
        for layer in self.model.layers:
            layer.attention.cache_k = None
            layer.attention.cache_v = None
        for layer in draft_model.layers:
            layer.attention.cache_k = None
            layer.attention.cache_v = None

        # Prefill base and draft
        base_logits, _ = self.model(tokens_tensor, use_cache=True, start_pos=0)
        draft_logits, _ = draft_model(tokens_tensor, use_cache=True, start_pos=0)

        curr_pos = seqlen
        generated_tokens = []

        base_next_logits = base_logits[:, -1, :]
        draft_next_logits = draft_logits[:, -1, :]

        while len(generated_tokens) < max_new_tokens:
            draft_tokens = []
            temp_pos = curr_pos
            curr_draft_logits = draft_next_logits

            # 1. Draft K steps
            for _ in range(K):
                next_draft_token = torch.argmax(curr_draft_logits, dim=-1, keepdim=True)
                draft_tokens.append(next_draft_token)
                curr_draft_logits, _ = draft_model(next_draft_token, use_cache=True, start_pos=temp_pos)
                curr_draft_logits = curr_draft_logits[:, -1, :]
                temp_pos += 1

            candidates = torch.cat(draft_tokens, dim=1) # (1, K)

            # 2. Base parallel eval
            base_candidate_logits, _ = self.model(candidates, use_cache=True, start_pos=curr_pos)
            base_preds = torch.cat([base_next_logits.unsqueeze(1), base_candidate_logits[:, :-1, :]], dim=1) # (1, K, vocab_size)

            # 3. Verify
            accepted_count = 0
            for i in range(K):
                candidate_id = candidates[0, i].item()
                base_greedy_id = torch.argmax(base_preds[0, i], dim=-1).item()
                if candidate_id == base_greedy_id:
                    accepted_count += 1
                else:
                    break

            # Slices caches
            for layer in self.model.layers:
                if layer.attention.cache_k is not None:
                    layer.attention.cache_k = layer.attention.cache_k[:, :curr_pos + accepted_count]
                    layer.attention.cache_v = layer.attention.cache_v[:, :curr_pos + accepted_count]

            if accepted_count == K:
                next_token_id = torch.argmax(base_candidate_logits[0, -1], dim=-1).item()
            else:
                next_token_id = torch.argmax(base_preds[0, accepted_count], dim=-1).item()

            # Yield accepted tokens
            for i in range(accepted_count):
                token_val = candidates[0, i].item()
                generated_tokens.append(token_val)
                yield self.tokenizer.decode([token_val])

            if len(generated_tokens) < max_new_tokens:
                generated_tokens.append(next_token_id)
                yield self.tokenizer.decode([next_token_id])

            if next_token_id == self.tokenizer.eos_id:
                break

            next_token_tensor = torch.tensor([[next_token_id]], dtype=torch.long, device=self.device)
            curr_pos = curr_pos + accepted_count

            base_next_logits, _ = self.model(next_token_tensor, use_cache=True, start_pos=curr_pos)
            base_next_logits = base_next_logits[:, -1, :]

            # Sync draft cache
            for layer in draft_model.layers:
                if layer.attention.cache_k is not None:
                    layer.attention.cache_k = layer.attention.cache_k[:, :curr_pos]
                    layer.attention.cache_v = layer.attention.cache_v[:, :curr_pos]

            draft_next_logits, _ = draft_model(next_token_tensor, use_cache=True, start_pos=curr_pos)
            draft_next_logits = draft_next_logits[:, -1, :]
            curr_pos += 1

    def generate(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7, top_k: int = 50, top_p: float = 0.9) -> str:
        """
        Generates full completed text.
        """
        return "".join(list(self.generate_stream(prompt, max_new_tokens, temperature, top_k, top_p)))

    def generate_speculative_full(self, prompt: str, draft_model=None, max_new_tokens: int = 512, K: int = 4) -> str:
        """
        Generates full completed text speculatively.
        """
        return "".join(list(self.generate_speculative(prompt, draft_model, max_new_tokens, K)))
