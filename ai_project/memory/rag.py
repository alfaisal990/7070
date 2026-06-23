import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from ai_project.memory.vector_db import PhoenixMemoryStore

logger = logging.getLogger("PhoenixRAG")

class PhoenixRAGPipeline:
    """
    RAG Document Ingestion Pipeline.
    Parses files, chunks them using a sliding window, and indexes them into the vector database.
    """
    def __init__(self, memory_store: PhoenixMemoryStore):
        self.memory_store = memory_store

    def recursive_chunk_text(self, text: str, separators: List[str] = None, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
        """
        Splits text recursively using a list of separators (e.g. paragraphs, lines, spaces)
        to keep semantic units (like paragraphs or sentences) intact.
        """
        if not text:
            return []
            
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
            
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
            
        if separators is None:
            separators = ["\n\n", "\n", " ", ""]
            
        def split_recursive(text_to_split: str, separators_list: List[str]) -> List[str]:
            if len(text_to_split) <= chunk_size:
                return [text_to_split]
                
            if not separators_list:
                # Fallback to character sliding window
                chunks = []
                start = 0
                while start < len(text_to_split):
                    end = min(start + chunk_size, len(text_to_split))
                    chunks.append(text_to_split[start:end])
                    if end == len(text_to_split):
                        break
                    start += (chunk_size - chunk_overlap)
                return chunks
                
            separator = separators_list[0]
            remaining_separators = separators_list[1:]
            
            if separator == "":
                chunks = []
                start = 0
                while start < len(text_to_split):
                    end = min(start + chunk_size, len(text_to_split))
                    chunks.append(text_to_split[start:end])
                    if end == len(text_to_split):
                        break
                    start += (chunk_size - chunk_overlap)
                return chunks
                
            splits = text_to_split.split(separator)
                
            merged_chunks = []
            current_chunk = []
            current_len = 0
            
            for s in splits:
                item = s
                if len(item) > chunk_size:
                    if current_chunk:
                        merged_chunks.append(separator.join(current_chunk))
                        current_chunk = []
                        current_len = 0
                    merged_chunks.extend(split_recursive(item, remaining_separators))
                else:
                    added_len = len(item) + (len(separator) if current_chunk else 0)
                    if current_len + added_len <= chunk_size:
                        current_chunk.append(item)
                        current_len += added_len
                    else:
                        if current_chunk:
                            merged_chunks.append(separator.join(current_chunk))
                        current_chunk = [item]
                        current_len = len(item)
                        
            if current_chunk:
                merged_chunks.append(separator.join(current_chunk))
                
            return [c for c in merged_chunks if c]
            
        return split_recursive(text, separators)

    def chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
        """
        Splits text into chunks using the recursive character-based splitter.
        """
        return self.recursive_chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def ingest_file(self, file_path: str, chunk_size: int = 500, chunk_overlap: int = 100) -> Dict[str, Any]:
        """
        Ingests a single file, chunks it, and indexes it in the vector memory store.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = path.suffix.lower()
        if ext == ".csv":
            import csv
            rows_text = []
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if headers:
                    for idx, row in enumerate(reader):
                        row_desc = f"Row {idx+1}: " + ", ".join([f"{headers[col_idx]} is {val}" for col_idx, val in enumerate(row) if col_idx < len(headers)])
                        rows_text.append(row_desc)
            content = "\n".join(rows_text)
        elif ext == ".json":
            import json
            def flatten_json(data: Any, prefix: str = "") -> List[str]:
                statements = []
                if isinstance(data, dict):
                    for k, v in data.items():
                        new_key = f"{prefix}.{k}" if prefix else k
                        statements.extend(flatten_json(v, new_key))
                elif isinstance(data, list):
                    for idx, item in enumerate(data):
                        new_key = f"{prefix}[{idx}]"
                        statements.extend(flatten_json(item, new_key))
                else:
                    statements.append(f"{prefix} is {data}")
                return statements
                
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                try:
                    data = json.load(f)
                    content = "\n".join(flatten_json(data))
                except Exception:
                    f.seek(0)
                    content = f.read()
        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
        chunks = self.chunk_text(content, chunk_size, chunk_overlap)
        file_name = path.name
        
        for idx, chunk in enumerate(chunks):
            metadata = {
                "source": file_name,
                "chunk_idx": idx,
                "total_chunks": len(chunks),
                "type": "document"
            }
            # Add to memory store
            self.memory_store.add_memory(chunk, metadata)
            
        logger.info(f"Ingested {file_name}: split into {len(chunks)} chunks.")
        
        return {
            "file_name": file_name,
            "chunks_count": len(chunks),
            "status": "success"
        }
