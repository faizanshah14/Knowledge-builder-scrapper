from __future__ import annotations
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain.chains import RetrievalQA


def debug_index_contents(index_dir: str):
    """Debug function to check what's in the FAISS index"""
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    vs = FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
    
    # Get all documents from the index
    all_docs = vs.similarity_search("", k=100)  # Search with empty query to get all docs
    print(f"Index contains {len(all_docs)} documents:")
    for i, doc in enumerate(all_docs):
        print(f"  {i+1}. {doc.metadata.get('title', 'No title')} - {doc.metadata.get('source_url', 'No URL')}")
        print(f"     Content: {doc.page_content[:100]}...")
    
    return len(all_docs)


def load_retriever(index_dir: str):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    vs = FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
    return vs.as_retriever(search_kwargs={"k": 6})


def answer_question(index_dir: str, question: str, anthropic_api_key: str, model: str = "claude-3-5-sonnet-20241022") -> str:
    retriever = load_retriever(index_dir)
    
    llm = ChatAnthropic(
        model=model, 
        api_key=anthropic_api_key, 
        temperature=0,
        max_tokens=2000
    )
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
    )
    result = qa.invoke({"query": question})
    return result["result"]
