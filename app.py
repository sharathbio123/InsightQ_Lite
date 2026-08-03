import os
import shutil
import tempfile
import streamlit as st
from pathlib import Path

# Import pipeline builder from the existing script
try:
    from Test_AI import setup_rag_pipeline
except Exception as e:
    setup_rag_pipeline = None
    st.warning(f"Could not import setup_rag_pipeline from Test_AI.py: {e}")

st.set_page_config(page_title="InsightQ — Local RAG UI", layout="wide")

st.title("InsightQ — Local Retrieval-Augmented Generation (RAG) UI")
st.markdown(
    "A lightweight Streamlit frontend for InsightQ. Upload PDFs, build a local vector index, and chat with your documents using a local LLM."
)

DATA_DIR = Path("documents")
DATA_DIR.mkdir(exist_ok=True)

if "pipeline" not in st.session_state:
    st.session_state.pipeline = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "status" not in st.session_state:
    st.session_state.status = "idle"

with st.sidebar:
    st.header("Upload PDFs")
    uploaded = st.file_uploader("Upload one or more PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded:
        save_btn = st.button("Save uploaded PDFs to documents")
        if save_btn:
            saved = 0
            for file in uploaded:
                dest = DATA_DIR / file.name
                with open(dest, "wb") as f:
                    f.write(file.getbuffer())
                saved += 1
            st.success(f"Saved {saved} files to '{DATA_DIR.resolve()}'")

    st.markdown("---")
    st.header("Index / Model")
    st.text_input("PDF folder path", value=str(DATA_DIR.resolve()), key="pdf_folder")
    build = st.button("Build RAG index (run pipeline)")

    st.markdown("---")
    st.header("Notes")
    st.markdown(
        "- This UI wraps the existing Test_AI.py pipeline.\n"
        "- Make sure local Ollama is installed and the models (llama3.2:3b and nomic-embed-text) are pulled.\n"
        "- Building the index may take time depending on PDFs and models."
    )

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Chat")
    if st.session_state.pipeline is None:
        st.info("Pipeline not built yet. Upload PDFs and click 'Build RAG index' in the sidebar.")

    query = st.text_input("Enter your question", key="query_input")
    if st.button("Send") and query.strip():
        if st.session_state.pipeline is None:
            st.error("Pipeline not available — build the index first.")
        else:
            try:
                st.session_state.status = "running"
                with st.spinner("Processing — this may take a few seconds..."):
                    response = st.session_state.pipeline.invoke({
                        "input": query,
                        "chat_history": st.session_state.chat_history,
                    })
                st.session_state.chat_history.append({"role": "human", "content": query})
                st.session_state.chat_history.append({"role": "ai", "content": response})
                st.success("Response received")
            except Exception as e:
                st.session_state.status = "error"
                st.error(f"Error while invoking pipeline: {e}")

    if st.session_state.chat_history:
        st.markdown("### Conversation")
        for turn in st.session_state.chat_history[::-1]:
            role = turn.get("role")
            content = turn.get("content")
            if role == "human":
                st.markdown(f"**You:** {content}")
            else:
                st.markdown(f"**AI:** {content}")

with col2:
    st.subheader("Status")
    st.write(st.session_state.status)

# Build pipeline action handled after layout to avoid Streamlit rerun issues
if st.sidebar.button("Build RAG index (run pipeline)") or (build and not st.session_state.pipeline):
    folder = Path(st.session_state.pdf_folder)
    if not folder.exists() or not any(folder.glob("*.pdf")):
        st.error(f"No PDFs found in {folder}. Upload files using the sidebar uploader first.")
    elif setup_rag_pipeline is None:
        st.error("setup_rag_pipeline is not available (import failed).")
    else:
        try:
            st.session_state.status = "building"
            with st.spinner("Setting up RAG pipeline — processing PDFs and creating embeddings..."):
                pipeline = setup_rag_pipeline(str(folder))
                st.session_state.pipeline = pipeline
                st.session_state.chat_history = []
            st.session_state.status = "ready"
            st.success("Pipeline built and ready. You can ask questions now.")
        except Exception as e:
            st.session_state.status = "error"
            st.error(f"Failed to build pipeline: {e}")

# Small cleanup button
if st.sidebar.button("Clear saved PDFs and reset"):
    try:
        for f in DATA_DIR.glob("*.pdf"):
            f.unlink()
        st.session_state.pipeline = None
        st.session_state.chat_history = []
        st.success("Cleared PDF folder and reset state.")
    except Exception as e:
        st.error(f"Could not clear files: {e}")
