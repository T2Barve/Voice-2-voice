import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
RAG_DATA_DIR = BASE_DIR / "rag_data"
DB_DIR = BASE_DIR / "rag_db"

def get_embeddings():
    # Use GoogleGenerativeAIEmbeddings since Gemini is heavily used in the project
    # Fallback to HuggingFace Embeddings if requested, but Google's are often preferred unless specified.
    # The prompt listed "HuggingFaceEmbeddings or Gemini". I'll stick to Gemini to reduce heavy local dependencies if possible,
    # but the prompt specifically mentioned "HuggingFaceEmbeddings" in one place. Let's use Gemini since google-genai is already set up.
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def load_documents(company: str, interview_type: str):
    company = company.lower().replace(" ", "_")
    interview_type = interview_type.lower().replace(" ", "_")
    
    dir_path = RAG_DATA_DIR / interview_type
    
    docs = []
    if not dir_path.exists():
        return docs
        
    for file_name in os.listdir(dir_path):
        if file_name.endswith(".pdf") and company in file_name.lower():
            file_path = dir_path / file_name
            loader = PyPDFLoader(str(file_path))
            docs.extend(loader.load())
            
    return docs

def build_vectorstore(company: str, interview_type: str):
    docs = load_documents(company, interview_type)
    if not docs:
        print(f"No documents found for {company} - {interview_type}")
        return None
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    splits = text_splitter.split_documents(docs)
    
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(splits, embeddings)
    
    save_path = DB_DIR / f"{company}_{interview_type}"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(save_path))
    
    return vectorstore

def get_vectorstore(company: str, interview_type: str):
    company = company.lower().replace(" ", "_")
    interview_type = interview_type.lower().replace(" ", "_")
    
    save_path = DB_DIR / f"{company}_{interview_type}"
    embeddings = get_embeddings()
    
    if save_path.exists() and (save_path / "index.faiss").exists():
        return FAISS.load_local(str(save_path), embeddings, allow_dangerous_deserialization=True)
    
    # If it doesn't exist, try building it
    return build_vectorstore(company, interview_type)
