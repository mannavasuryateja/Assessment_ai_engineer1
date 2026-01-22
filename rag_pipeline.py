import os
import tempfile
from typing import List

import streamlit as st
import google.generativeai as genai

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings


# -----------------------------------
# Configure Gemini (OFFICIAL SDK)
# -----------------------------------
if "GEMINI_API_KEY" not in st.secrets:
    st.error("GEMINI_API_KEY not found in Streamlit secrets")
    st.stop()

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
        st.warning("No text extracted from uploaded PDFs.")
        return None

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    # ✅ CLOUD-SAFE EMBEDDINGS (Gemini)
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=st.secrets["GEMINI_API_KEY"]
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

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return response.text
