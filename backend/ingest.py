"""
ingest.py

One-shot script to embed a PDF into a FAISS index on disk.
Run this once per document before starting the agent; the agent
loads the saved index at startup (Phase 3).

Two modes controlled by flags:
  --pdf + --index   →  build a new index from a PDF
  --index + --query →  load an existing index and print top-4 chunks

Why RecursiveCharacterTextSplitter?
  It tries to split on paragraphs, then sentences, then words, so chunks
  stay semantically coherent. Splitting naively on character count often
  cuts mid-sentence, hurting retrieval quality.

Why chunk_size=1000 / overlap=200?
  1 000 chars ≈ ~200 tokens, well within most embedding model limits.
  The 200-char overlap ensures a sentence spanning a boundary is fully
  present in at least one of the two neighbouring chunks.
"""

import argparse
import os
import sys
import warnings

# langchain-community is deprecated in LangChain 1.x. The standalone replacements
# (langchain-pypdf, langchain-faiss) are not yet on PyPI, so community imports are
# still correct. Suppress the warning by matching the message text — matching on
# module= doesn't work because the warn() call fires inside langchain_community's
# own __init__ before Python's import machinery can apply our filter.
warnings.filterwarnings("ignore", message=".*langchain-community.*")

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()  # reads OPENAI_API_KEY from .env


def build_index(pdf_path: str, index_path: str) -> None:
    """Load a PDF, split it into chunks, embed them, and save a FAISS index."""

    if not os.path.isfile(pdf_path):
        print(f"[ERROR] PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading PDF: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    # PyPDFLoader already sets doc.metadata["source"] and doc.metadata["page"].
    pages = loader.load()
    print(f"  Pages loaded: {len(pages)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(pages)

    # Re-stamp metadata explicitly so callers don't have to know PyPDFLoader's
    # internal key names.  "page" from PyPDFLoader is 0-indexed; keep it as-is.
    filename = os.path.basename(pdf_path)
    for chunk in chunks:
        chunk.metadata["source"] = filename
        # PyPDFLoader already sets "page"; this line is explicit documentation.
        chunk.metadata["page"] = chunk.metadata.get("page", 0)

    print(f"  Chunks created: {len(chunks)}")

    print("Embedding chunks (this calls the OpenAI API) …")
    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(chunks, embeddings)

    db.save_local(index_path)
    print(f"  Index saved to: {index_path}")
    print(f"\nDone. {len(chunks)} chunks indexed.")


def query_index(index_path: str, query: str) -> None:
    """Load a saved FAISS index and print the top-4 most relevant chunks."""

    if not os.path.isdir(index_path):
        print(f"[ERROR] Index directory not found: {index_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading index from: {index_path}")
    embeddings = OpenAIEmbeddings()

    # allow_dangerous_deserialization=True is required by LangChain when
    # loading a local FAISS index; the flag is a reminder that you should
    # only load indexes you created yourself.
    db = FAISS.load_local(
        index_path, embeddings, allow_dangerous_deserialization=True
    )

    results = db.similarity_search(query, k=4)
    print(f"\nTop {len(results)} chunks for query: '{query}'\n{'─' * 60}")

    for i, doc in enumerate(results, 1):
        src = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        print(f"\n[{i}] source={src}  page={page}")
        print(doc.page_content[:500])   # truncate long chunks for readability
        print("─" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build or query a FAISS index from a PDF."
    )
    parser.add_argument("--pdf", help="Path to the PDF file to ingest.")
    parser.add_argument(
        "--index", required=True, help="Directory path for the FAISS index."
    )
    parser.add_argument(
        "--query", help="If provided, query an existing index instead of building one."
    )
    args = parser.parse_args()

    if args.query:
        # Query mode: index must already exist.
        query_index(args.index, args.query)
    elif args.pdf:
        # Build mode: create a new index from the PDF.
        build_index(args.pdf, args.index)
    else:
        print(
            "[ERROR] Provide --pdf to build an index, or --query to search one.",
            file=sys.stderr,
        )
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
