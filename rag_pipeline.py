import os
import tempfile
from typing import List

import streamlit as st
import google.generativeai as genai

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings


# -----------------------------------
# Configure Gemini (OFFICIAL SDK)
# -----------------------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


def ingest_pdfs(uploaded_files: List):
    documents = []

    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        try:
            loader = PyPDFLoader(tmp_path)
            documents.extend(loader.load())
        finally:
            os.remove(tmp_path)

    if not documents:
        raise ValueError("No text extracted from PDFs")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    # ✅ LOCAL EMBEDDINGS (NO QUOTA / NO API)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return FAISS.from_documents(chunks, embeddings)


def rag_answer(query: str, vectorstore):
    if vectorstore is None:
        return "Please upload and process documents first."

    docs = vectorstore.similarity_search(query, k=3)
    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = f"""
You are a professional hotel booking assistant providing exceptional guest service.
Answer ONLY using the context below.
If the answer is not available in the context, respond with:
"I apologize, but I don't have information about that in our hotel documentation. Please contact our reservations team at our main office or visit our website for additional assistance."

Always maintain a courteous and professional tone befitting a luxury hotel.

Context:
{context}

Question:
{query}
"""

    # ✅ THE ONLY MODEL THAT WORKS FOR YOU
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return response.text
