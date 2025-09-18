from __future__ import annotations
import json
from typing import List, Dict
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def load_items(json_path: str) -> List[Dict]:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return data.get("items", [])


def build_documents(items: List[Dict]):
    from langchain_core.documents import Document
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]  # Better separators for technical content
    )

    docs: List[Document] = []
    for it in items:
        content = it.get("content", "")
        metadata = {k: it.get(k) for k in ["title", "content_type", "source_url"]}
        
        chunks = splitter.split_text(content)
        
        for i, chunk in enumerate(chunks):
            # Add chunk info to metadata
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            docs.append(Document(page_content=chunk, metadata=chunk_metadata))
    
    return docs


def build_faiss_index(json_path: str, index_dir: str) -> str:
    items = load_items(json_path)
    
    if not items:
        raise ValueError("No items found in the scraped data. Please check if the website has content or try different include/exclude patterns.")
    
    docs = build_documents(items)
    
    if not docs:
        raise ValueError("No text chunks could be created from the scraped content. The content might be too short or empty.")
    
    # Use free HuggingFace embeddings instead of OpenAI
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    try:
        vs = FAISS.from_documents(docs, embeddings)
        vs.save_local(index_dir)
        return index_dir
    except Exception as e:
        raise ValueError(f"Failed to create FAISS index: {str(e)}. This might be due to empty content or embedding issues.")
