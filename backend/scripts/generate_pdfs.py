import os
import time
import re
from pathlib import Path
from dotenv import load_dotenv

# Use Gemini SDK
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import ResourceExhausted

# For PDFs
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

BASE_DIR = Path(__file__).resolve().parent.parent

# Load the API key explicitly from the server/.env file
server_env_path = BASE_DIR.parent / "server" / ".env"
load_dotenv(server_env_path, override=True)

# Verify API key
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError(f"GEMINI_API_KEY or GOOGLE_API_KEY not found in {server_env_path}")

os.environ["GOOGLE_API_KEY"] = api_key 

RAG_DATA_DIR = BASE_DIR / "rag_data"

COMPANIES = ["Microsoft"]
CATEGORIES = ["technical", "case_study"]

TARGET_QUESTIONS_PER_PDF = 10
BATCH_SIZE = 2   # STRICT as per requirement
DELAY = 6        # seconds between calls
MAX_RETRIES = 2

# Global set to ensure absolute uniqueness across all PDFs
global_questions_set = set()

# Initialize model (gemini-flash-latest verified as working)
model = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.7)

def ensure_folders():
    for cat in CATEGORIES:
        (RAG_DATA_DIR / cat).mkdir(parents=True, exist_ok=True)

def normalize(q):
    """Normalize question text to identify semantic duplicates easily."""
    if not q:
        return ""
    # Remove alphanumeric and lowercase
    return re.sub(r'\W+', '', q.lower())

def parse_questions(text):
    """Parse raw text blocks into question dictionaries."""
    questions = []
    # Split by "Question:" markers
    blocks = re.split(r'\n(?=Question:)', "\n" + text.strip())
    
    for block in blocks:
        block = block.strip()
        if not block.startswith("Question:"):
            continue
            
        q_dict = {}
        lines = block.split('\n')
        current_key = "Question"
        current_val = []
        
        for line in lines:
            line_stripped = line.strip()
            # If line is a known key
            match = re.match(r'^(Question|Difficulty|Tags|Problem Statement|Expected Approach|Optimized Approach|Time Complexity|Space Complexity|Optimizations|Hints):\s*(.*)', line_stripped, re.IGNORECASE)
            
            if match:
                if current_val:
                    q_dict[current_key] = "\n".join(current_val).strip()
                current_key = match.group(1).title()
                # If "Hints", keep the value part if present
                val_part = match.group(2).strip()
                current_val = [val_part] if val_part else []
            else:
                current_val.append(line_stripped)
                
        if current_val:
            q_dict[current_key] = "\n".join(current_val).strip()
            
        # Validate all required fields
        required_keys = ["Question", "Difficulty", "Tags", "Problem Statement", "Expected Approach", "Optimized Approach", "Time Complexity", "Space Complexity", "Optimizations", "Hints"]
        
        is_valid = True
        for k in required_keys:
            if k not in q_dict or not q_dict[k]:
                is_valid = False
                break
                
        if is_valid:
            questions.append(q_dict)
            
    return questions

def generate_question_batch(company, category, count):
    """Generate a batch of questions using Gemini with optimized prompt."""
    prompt = f"""You are a FAANG interviewer at {company}.

Generate EXACTLY {count} UNIQUE {category} interview questions.

STRICT RULES:
- Questions must be realistic and company-level
- Avoid common problems (no Two Sum, no basic stuff)
- Keep answers concise (avoid long paragraphs)
- Ensure all questions are different from each other

FORMAT STRICTLY:

Question:
Difficulty:
Tags:
Problem Statement:
Expected Approach:
Optimized Approach:
Time Complexity:
Space Complexity:
Optimizations:
Hints:

Return ONLY structured questions. No extra text."""

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            response = model.invoke(prompt)
            content = response.content
            
            # Handle cases where content is a list of dictionaries (common in newer LangChain/Gemini versions)
            if isinstance(content, list):
                raw_text = ""
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        raw_text += part["text"]
                    elif isinstance(part, str):
                        raw_text += part
                raw_text = raw_text.strip()
            else:
                raw_text = content.strip() if content else ""
                
            if not raw_text:
                raise ValueError("Empty response received from Gemini.")
            
            parsed = parse_questions(raw_text)
            if not parsed:
                raise ValueError("Could not parse any structured questions from Gemini response.")
            return parsed
            
        except ResourceExhausted:
            print("ResourceExhausted hit! Sleeping for 60 seconds...")
            time.sleep(60)
            continue
            
        except Exception as e:
            print(f"Gemini Error (Attempt {attempt}/{MAX_RETRIES + 1}): {e}")
            if attempt > MAX_RETRIES:
                print("Max retries reached for this batch. Skipping.")
                return []
            time.sleep(DELAY) # Wait before retry
            
    return []

def generate_pdf_for_company(company, category):
    """Generate the full PDF document using Gemini API strictly batched."""
    filepath = RAG_DATA_DIR / category / f"{company}_{category}.pdf".lower()
    
    pdf_docs = []
    failed_batches = 0
    
    print(f"\nStarting Generation: {company} | {category}")
    
    while len(pdf_docs) < TARGET_QUESTIONS_PER_PDF:
        needed = min(BATCH_SIZE, TARGET_QUESTIONS_PER_PDF - len(pdf_docs))
        print(f"   => Requesting batch of {needed} questions from Gemini...")
        
        batch = generate_question_batch(company, category, needed)
        
        if not batch:
            failed_batches += 1
            if failed_batches > 2:
                print(f"Consecutive failures. Halting PDF generation for {company} {category}.")
                break
            continue
        else:
            failed_batches = 0
            
        accepted = 0
        for q in batch:
            norm_q = normalize(q.get("Question", ""))
            if not norm_q:
                continue
                
            if norm_q in global_questions_set:
                print(f"      [DUPLICATE REJECTED] {q['Question'][:50]}...")
            else:
                global_questions_set.add(norm_q)
                pdf_docs.append(q)
                accepted += 1
                if len(pdf_docs) >= TARGET_QUESTIONS_PER_PDF:
                    break
                    
        print(f"   => {accepted}/{len(batch)} accepted. Total: {len(pdf_docs)}/{TARGET_QUESTIONS_PER_PDF}")
        
        # Enforce delay between successful calls to prevent quota crashes
        if len(pdf_docs) < TARGET_QUESTIONS_PER_PDF:
            print(f"   Batch DELAY: Sleeping {DELAY} seconds...")
            time.sleep(DELAY)
            
    if len(pdf_docs) < TARGET_QUESTIONS_PER_PDF:
        print(f"FAILED to get {TARGET_QUESTIONS_PER_PDF} valid questions for {company} {category}. Only got {len(pdf_docs)}. Skipping write.")
        return
        
    print(f"Writing PDF to {filepath}...")
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    q_title_style = styles['Heading2']
    normal_style = styles['Normal']
    normal_style.wordWrap = 'CJK'
    
    flowables = []
    
    flowables.append(Paragraph(f"Company: {company}", title_style))
    flowables.append(Paragraph(f"Interview Type: {category.upper()}", title_style))
    flowables.append(Paragraph("-" * 50, normal_style))
    flowables.append(Spacer(1, 20))
    
    for i, q in enumerate(pdf_docs):
        flowables.append(Paragraph(f"Q{i+1}: {q['Question']}", q_title_style))
        flowables.append(Spacer(1, 10))
        
        keys_to_print = ["Difficulty", "Tags", "Problem Statement", "Expected Approach", 
                         "Optimized Approach", "Time Complexity", "Space Complexity", 
                         "Optimizations", "Hints"]
                         
        for key in keys_to_print:
            val = str(q.get(key, ''))
            # Escape for ReportLab XML-like Paragraph handling
            val = val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
            p = Paragraph(f"<b>{key}:</b> {val}", normal_style)
            flowables.append(p)
            flowables.append(Spacer(1, 5))
            
        flowables.append(Paragraph("-" * 50, normal_style))
        flowables.append(Spacer(1, 15))
        
    try:
        doc.build(flowables)
        print(f"Successfully written: {filepath}")
    except Exception as e:
        print(f"Failed to build PDF for {company} {category}: {e}")

if __name__ == "__main__":
    print("Starting GEMINI STABLE PDF Generation Engine (gemini-flash-latest)...")
    ensure_folders()
    
    for company in COMPANIES:
        for category in CATEGORIES:
            generate_pdf_for_company(company, category)
            
    print("\nALL PDF GENERATION COMPLETE!")
    print(f"Total Unique Questions Tracked Globally: {len(global_questions_set)}")
