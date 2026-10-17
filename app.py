"""
Chat with your PDF: a beginner-friendly RAG (Retrieval-Augmented Generation) app.

How it works:
  1. Read the PDF and split the text into small overlapping chunks.
  2. Store the chunks in a vector database (ChromaDB), which turns each chunk
     into an "embedding" so we can search by meaning, not just keywords.
  3. When you ask a question, find the chunks most similar to it.
  4. Send those chunks plus your question to Gemini and ask it to answer
     using ONLY that context, citing page numbers.
"""

import time
import uuid

import chromadb
import streamlit as st
from google import genai
from google.genai import errors, types
from pypdf import PdfReader

# ---------- Settings you can experiment with ----------
CHUNK_SIZE = 1200     # characters per chunk
CHUNK_OVERLAP = 150   # characters shared between neighbouring chunks
TOP_K = 10            # how many chunks to retrieve per question
# Free Gemini model. If you get a "model not found" error, try
# "gemini-2.5-flash-lite" or check the current names at aistudio.google.com
MODEL = "gemini-3.8-flash"
# Tried in order if the main model is overloaded or unavailable.
FALLBACK_MODELS = ["gemini-3.7-flash", "gemini-3.5-flash-lite", "gemini-flash-lite-latest"]


# ---------- Step 1: read and chunk the PDF ----------
def extract_pages(pdf_file):
    """Return a list of (page_number, text) for every page in the PDF."""
    reader = PdfReader(pdf_file)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((i, text))
    return pages


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping pieces so ideas aren't cut off mid-way."""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


# ---------- Step 2: store chunks in a vector database ----------
def build_index(pdf_file):
    """Chunk the PDF and put every chunk into a fresh ChromaDB collection."""
    client = chromadb.Client()  # in-memory, nothing saved to disk
    collection = client.create_collection(name=f"doc_{uuid.uuid4().hex[:8]}")

    ids, docs, metas = [], [], []
    for page_num, text in extract_pages(pdf_file):
        for j, chunk in enumerate(chunk_text(text)):
            ids.append(f"p{page_num}_c{j}")
            docs.append(chunk)
            metas.append({"page": page_num})

    if not docs:
        return None, 0

    # Chroma creates the embeddings for us using a built-in model.
    collection.add(ids=ids, documents=docs, metadatas=metas)
    return collection, len(docs)


# ---------- Step 3 + 4: retrieve and answer ----------
def answer_question(question, collection):
    results = collection.query(query_texts=[question], n_results=TOP_K)
    chunks = results["documents"][0]
    pages = [m["page"] for m in results["metadatas"][0]]

    context = "\n\n".join(
        f"[Page {p}]\n{c}" for p, c in zip(pages, chunks)
    )

    system_prompt = (
        "You answer questions using ONLY the document excerpts provided. "
        "If the answer is not in the excerpts, say you couldn't find it in the "
        "document. Mention the page number(s) your answer comes from."
    )
    user_prompt = f"Excerpts:\n{context}\n\nQuestion: {question}"

    client = genai.Client()  # reads GEMINI_API_KEY from your environment
    text = call_gemini(client, system_prompt, user_prompt)
    return text, sorted(set(pages)), chunks


def call_gemini(client, system_prompt, user_prompt):
    """Call Gemini, retrying on temporary errors and falling back to other models."""
    last_error = None
    for model in [MODEL] + FALLBACK_MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=800,
                    ),
                )
                return response.text
            except errors.ServerError as e:      # 500/503: Google is busy, wait and retry
                last_error = e
                time.sleep(2 ** (attempt + 1))   # waits 2s, 4s, 8s
            except errors.ClientError as e:
                if e.code in (404, 429):         # model missing or quota hit: try next model
                    last_error = e
                    break
                raise                            # anything else (bad key, etc.) is a real bug
    raise last_error


# ---------- The web interface ----------
st.set_page_config(page_title="Chat with your PDF", page_icon="📄")
st.title("📄 Chat with your PDF")

uploaded = st.file_uploader("Upload a PDF", type="pdf")

if uploaded:
    # Only rebuild the index when a new file is uploaded.
    if st.session_state.get("file_name") != uploaded.name:
        with st.spinner("Reading and indexing your document..."):
            collection, n_chunks = build_index(uploaded)
        if collection is None:
            st.error("No readable text found. Scanned PDFs need OCR first.")
            st.stop()
        st.session_state.collection = collection
        st.session_state.file_name = uploaded.name
        st.session_state.n_chunks = n_chunks

    st.success(f"Indexed {st.session_state.n_chunks} chunks from {uploaded.name}")

    question = st.text_input("Ask a question about the document")
    if question:
        try:
            with st.spinner("Thinking..."):
                reply, pages, chunks = answer_question(question, st.session_state.collection)
        except (errors.ServerError, errors.ClientError) as e:
            st.error(
                "Gemini couldn't answer right now (it may be busy or over the free "
                f"limit). Wait a minute and ask again.\n\nDetails: {e}"
            )
            st.stop()
        st.markdown(reply)
        st.caption(f"Sources: pages {', '.join(map(str, pages))}")
        with st.expander("See the text the AI was given"):
            for c in chunks:
                st.text(c)
                st.divider()
else:
    st.info("Upload a PDF to get started.")
