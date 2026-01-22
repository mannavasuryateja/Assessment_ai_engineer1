import sys
import os

# ----------------------------
# Fix import paths
# ----------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st

from app.chat_logic import initialize_chat_state, handle_user_message
from app.rag_pipeline import ingest_pdfs, rag_answer
from app.admin_dashboard import render_admin_dashboard


# ----------------------------
# Streamlit config
# ----------------------------
st.set_page_config(
    page_title="Hotel Booking AI Assistant",
    layout="wide"
)

# ----------------------------
# Sidebar navigation
# ----------------------------
page = st.sidebar.radio("Navigation", ["Chat", "Admin Dashboard"])

if page == "Admin Dashboard":
    render_admin_dashboard()
    st.stop()

# ----------------------------
# Sidebar: PDF upload
# ----------------------------
st.sidebar.header("📄 Upload Hotel Documents")

uploaded_files = st.sidebar.file_uploader(
    "Upload hotel PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if uploaded_files and st.sidebar.button("Process Documents"):
    with st.spinner("Processing PDFs..."):
        st.session_state.vectorstore = ingest_pdfs(uploaded_files)
    st.sidebar.success("Documents processed successfully!")

# ----------------------------
# Chat state init
# ----------------------------
if "chat_state" not in st.session_state:
    st.session_state.chat_state = initialize_chat_state()

# ----------------------------
# Chat UI
# ----------------------------
st.title("🏨 Hotel Booking AI Assistant")

for msg in st.session_state.chat_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Ask about the hotel or book a room...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    # 1️⃣ Booking logic first
    response = handle_user_message(
        st.session_state.chat_state,
        user_input
    )

    # 2️⃣ If booking logic didn't handle → RAG
    if response is None and st.session_state.vectorstore is not None:
        response = rag_answer(
            user_input,
            st.session_state.vectorstore
        )

    # 3️⃣ Final fallback
    if response is None:
        response = "Please upload hotel documents or say *I want to book a room*."

    with st.chat_message("assistant"):
        st.write(response)
