from backend.rag.vectorstore import get_vectorstore

def retrieve_questions(company: str, interview_type: str, difficulty: str = "", role: str = "", skills: list = None, project_keywords: list = None, k: int = 4):
    """
    Query FAISS with rich resume context to avoid hallucination.
    STRICT RULE: ONLY use retrieved context, NO hallucination.
    """
    # 🔥 PRODUCTION FIX: Fallback to SDE for PDF retrieval if role is mismatch
    # UI shows all roles, but PDFs are currently SDE-only
    effective_role = "SDE" if role != "SDE" else role
    
    vectorstore = get_vectorstore(company, interview_type)
    
    if not vectorstore:
        raise Exception(f"RAG Error: Knowledge database for {company} {interview_type} not found. (Role: {effective_role})")
    
    # Build a rich, resume-aware query using the EFFECTIVE role
    query_parts = [company, effective_role, interview_type, difficulty]
    
    # Inject resume skills into the query
    if skills:
        top_skills = skills[:5]  # Use top 5 skills to focus the retrieval
        query_parts.extend(top_skills)
        
    # Add project keywords for case study context
    if project_keywords:
        query_parts.extend(project_keywords[:3])
        
    query_parts.append("interview question")
    query = " ".join([p for p in query_parts if p])
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(query)
    
    if not docs:
        raise Exception("No questions found in PDFs")
        
    # Combine top chunks into a single rich context
    context = "\n\n---\n\n".join([doc.page_content for doc in docs])
    return context
