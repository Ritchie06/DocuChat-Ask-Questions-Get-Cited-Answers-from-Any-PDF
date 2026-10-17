<img width="1408" height="881" alt="4" src="https://github.com/user-attachments/assets/3f35a679-a7dc-4ea6-a540-5f3f1b6cfa48" />
<img width="1408" height="881" alt="3" src="https://github.com/user-attachments/assets/c271d5b5-275a-47b3-a5ad-7e60d9a4fc8a" />
<img width="1408" height="881" alt="2" src="https://github.com/user-attachments/assets/fe03351b-f663-4985-9277-24a613804542" />
<img width="1408" height="881" alt="1" src="https://github.com/user-attachments/assets/8e7651a1-f899-4d05-92b5-608b7126c102" />
# DocuChat: Ask Questions, Get Cited Answers from Any PDF

A Retrieval-Augmented Generation (RAG) app. Upload a PDF, ask questions in plain English, and get answers grounded in the document, with the page numbers they came from. If the answer isn't in the document, it says so instead of guessing.

Built with Python, Streamlit, ChromaDB and Google Gemini (free tier).

## Features

- **Cited answers:** every answer lists the pages it was drawn from.
- **Grounded, not guessed:** the model is told to use only the retrieved excerpts, and to say "I couldn't find it" otherwise.
- **Reads diagrams and images:** pictures in the PDF are described by Gemini and indexed as searchable text, so questions about figures and charts work.
- **Transparent:** an expander shows the exact passages sent to the model, which makes it easy to debug wrong answers.
- **Resilient:** retries on temporary Gemini errors and falls back to other models if one is overloaded or unavailable.

## How it works

1. **Extract:** text is read from each page. Embedded images are sent to Gemini, which transcribes and explains them.
2. **Chunk:** text is split into small overlapping pieces so ideas aren't cut off.
3. **Embed and store:** chunks go into an in-memory ChromaDB collection, which turns them into embeddings for search by meaning.
4. **Retrieve:** the question is matched against the chunks and the closest ones are selected.
5. **Answer:** the chunks and the question are sent to Gemini, which answers using only that context and cites the pages.

## Setup

Requires Python 3.10 or newer. Python 3.12 or 3.13 is safest, since some packages can lag behind brand-new Python versions.

```bash
git clone <your-repo-url>
cd <your-repo-folder>

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Get a free API key at https://aistudio.google.com/apikey, then set it:

```bash
export GEMINI_API_KEY="your-key-here"          # Windows PowerShell: $env:GEMINI_API_KEY="your-key-here"
```

Run the app:

```bash
streamlit run app.py
```

Never put your key in the code or commit it to GitHub. Set it as an environment variable as shown above.

## Settings

At the top of `app.py`:

| Setting | What it does |
|---|---|
| `CHUNK_SIZE` | Characters per chunk. Larger chunks keep more context together. |
| `CHUNK_OVERLAP` | Characters shared between neighbouring chunks. |
| `TOP_K` | How many chunks are retrieved per question. More means a better chance of finding the answer, but more text for the model. |
| `MODEL` | The Gemini model used for answers. Model names change, so check aistudio.google.com if you get a 404. |
| `FALLBACK_MODELS` | Models tried in order if the main one is busy or missing. |
| `READ_IMAGES` | Set to `False` to skip image reading and index text only (much faster). |
| `MAX_IMAGES` | Upper limit on images described per PDF, to protect the free tier. |

## What I learned

- **Retrieval is the hard part.** A broad question like "what does ikigai mean?" first failed because the search returned prologue pages that repeat the word without defining it. Retrieving more and longer chunks fixed it.
- **Text-only RAG can't see images.** A diagram in the book was invisible to the first version. Describing images with a vision-capable model and indexing the description fixed this.
- **Real PDFs have messy text.** Extracted text often contains broken words and odd spacing. The model usually copes, but it affects search quality.
- **Free tiers need defensive code.** Temporary 503 errors, missing model names and rate limits are common, so retries and fallback models matter.

## Limitations

- Scanned PDFs (photos of pages) have no text layer. They would need OCR first.
- Reading images makes the first upload slow, because each image is a separate API call.
- The index lives in memory, so you re-upload and re-index each time you restart.
- Free-tier requests may be used by Google to improve its products. Don't upload private or confidential documents.

## Ideas for next steps

- Chat history, so follow-up questions work
- Sentence-aware chunking and cleanup of extracted text
- Cache image descriptions on disk so re-indexing is instant
- Support for several documents and other file types
- A small test set of questions with known answers to measure accuracy
- Deploy on Streamlit Community Cloud
