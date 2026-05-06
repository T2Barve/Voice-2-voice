from backend.rag.vectorstore import get_vectorstore

def retrieve_questions(
    company: str,
    interview_type: str,
    difficulty: str = "",
    role: str = "",
    skills: list = None,
    project_keywords: list = None,
    k: int = 4
):
    """
    Query FAISS with rich resume context to retrieve highly relevant questions.
    STRICT RULE: ONLY use retrieved context, NO hallucination.
    """
    effective_role = "SDE" if role not in ["SDE"] else role

    vectorstore = get_vectorstore(company, interview_type)

    if not vectorstore:
        raise Exception(
            f"RAG Error: Knowledge database for '{company}' ({interview_type}) not found. "
            f"Ensure PDFs exist in backend/rag_data/{interview_type}/ with '{company.lower()}' in filename."
        )

    # Build a rich, resume-aware query vector
    query_parts = [company, effective_role, interview_type]

    if difficulty:
        query_parts.append(difficulty)

    # Inject top skills for semantic relevance
    if skills:
        query_parts.extend(skills[:6])

    # Inject project keywords for case study / technical depth
    if project_keywords:
        query_parts.extend(project_keywords[:4])

    query_parts.append("interview question")

    query = " ".join([p.strip() for p in query_parts if p and p.strip()])

    print(f"[RAG] Query: {query[:120]}...")

    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(query)

    if not docs:
        raise Exception(f"No documents retrieved from FAISS for query: '{query[:80]}'")

    context = "\n\n---\n\n".join([doc.page_content for doc in docs])
    return context
