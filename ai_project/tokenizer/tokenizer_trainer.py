import os
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.decoders import ByteLevel as ByteLevelDecoder

class PhoenixTokenizer:
    """
    Custom Byte-Level BPE Tokenizer for Phoenix AI, optimized for Python code.
    Includes special tokens for system prompts, user prompts, assistant answers, 
    and tool execution sequences.
    """
    SPECIAL_TOKENS = [
        "<|endoftext|>",
        "<|pad|>",
        "<|system|>",
        "<|user|>",
        "<|assistant|>",
        "<|tool_call|>",
        "<|tool_response|>",
    ]

    def __init__(self, tokenizer_path=None):
        if tokenizer_path and os.path.exists(tokenizer_path):
            self.tokenizer = Tokenizer.from_file(tokenizer_path)
        else:
            # Create a blank tokenizer with BPE model
            self.tokenizer = Tokenizer(BPE(unk_token="<|endoftext|>"))
            self.tokenizer.pre_tokenizer = ByteLevel(add_prefix_space=False)
            self.tokenizer.decoder = ByteLevelDecoder()

    @classmethod
    def train(cls, files, vocab_size=32000, min_frequency=2, save_dir="ai_project/tokenizer"):
        """
        Trains a custom Byte-Level BPE tokenizer on a list of files.
        """
        tokenizer = Tokenizer(BPE(unk_token="<|endoftext|>"))
        tokenizer.pre_tokenizer = ByteLevel(add_prefix_space=False)
        
        trainer = BpeTrainer(
            vocab_size=vocab_size,
            min_frequency=min_frequency,
            special_tokens=cls.SPECIAL_TOKENS,
            show_progress=True
        )
        
        tokenizer.train(files, trainer)
        tokenizer.decoder = ByteLevelDecoder()
        
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "tokenizer.json")
        tokenizer.save(save_path)
        print(f"Tokenizer trained successfully and saved to {save_path}")
        return cls(tokenizer_path=save_path)

    def encode(self, text, add_special_tokens=False):
        """Encodes text to token IDs."""
        encoding = self.tokenizer.encode(text)
        return encoding.ids

    def decode(self, ids, skip_special_tokens=False):
        """Decodes token IDs back to text."""
        return self.tokenizer.decode(ids, skip_special_tokens=skip_special_tokens)

    def token_to_id(self, token):
        """Gets the ID of a specific token."""
        return self.tokenizer.token_to_id(token)

    def id_to_token(self, idx):
        """Gets the token string of a specific ID."""
        return self.tokenizer.id_to_token(idx)

    def get_vocab_size(self):
        """Returns the size of the vocabulary."""
        return self.tokenizer.get_vocab_size()

    def save(self, filepath):
        """Saves the tokenizer to a file."""
        self.tokenizer.save(filepath)

    @property
    def pad_id(self):
        return self.tokenizer.token_to_id("<|pad|>")

    @property
    def eos_id(self):
        return self.tokenizer.token_to_id("<|endoftext|>")

    @property
    def bos_id(self):
        return self.tokenizer.token_to_id("<|endoftext|>")
