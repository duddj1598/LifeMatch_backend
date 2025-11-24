import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "./CHROMA_DB"))
CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nlpai-lab/KURE-v1")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929")

# 지연 초기화용 전역 핸들
_embedding_model = None
_chroma_db = None
_llm_client = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from langchain_huggingface.embeddings import HuggingFaceEmbeddings
        _embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embedding_model

def get_chroma_db():
    global _chroma_db
    if _chroma_db is None:
        from langchain_chroma import Chroma
        _chroma_db = Chroma(persist_directory=str(CHROMA_DB_PATH), embedding_function=get_embedding_model())
    return _chroma_db

def get_llm_client():
    global _llm_client
    if _llm_client is None:
        from langchain_anthropic import ChatAnthropic
        _llm_client = ChatAnthropic(model_name=LLM_MODEL)
    return _llm_client
