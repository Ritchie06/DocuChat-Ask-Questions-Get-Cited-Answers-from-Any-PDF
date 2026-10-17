# Chat with your PDF (RAG starter)

Upload a PDF, ask questions, get answers grounded in the document with page citations.

## Setup

1. Install Python 3.10+.
2. (Recommended) create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Get an API key from https://console.anthropic.com and set it:
   ```
   export ANTHROPIC_API_KEY="your-key-here"      # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key-here"
   ```
5. Run the app:
   ```
   streamlit run app.py
   ```

The first run downloads a small embedding model, so it may take a minute.

## How it works

| Step | What happens | Where in `app.py` |
|------|--------------|-------------------|
| 1 | Extract text from the PDF and split into overlapping chunks | `extract_pages`, `chunk_text` |
| 2 | Embed chunks and store them in ChromaDB | `build_index` |
| 3 | Find the chunks most similar to the question | `collection.query` in `answer_question` |
| 4 | Ask Claude to answer using only those chunks | `answer_question` |

## Experiments to learn from

- Change `CHUNK_SIZE`, `CHUNK_OVERLAP` and `TOP_K`. How do answers change?
- Ask something that is NOT in the PDF. Does it say "I couldn't find it"?
- Edit the system prompt to change the tone (e.g. explain like I'm 12).
- Open "See the text the AI was given" and check whether retrieval found the right passages.

## Ideas to extend it

- Keep chat history so follow-up questions work
- Support multiple PDFs or .docx/.txt files
- Save the index to disk with `chromadb.PersistentClient`
- Add a small test set of questions with known answers and measure accuracy
- Deploy it free on Streamlit Community Cloud
