import os
import sqlite3
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer

# Load API key from .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

GROQ_MODEL = "openai/gpt-oss-120b"

DB_PATH = os.path.join("database", "analytics.db")

# Schema description — this tells the LLM what columns exist
SCHEMA = """
Table: loans
Columns:
- ID, year, loan_limit, Gender, approv_in_adv, loan_type, loan_purpose,
  Credit_Worthiness, open_credit, business_or_commercial, loan_amount,
  rate_of_interest, Interest_rate_spread, Upfront_charges, term,
  Neg_ammortization, interest_only, lump_sum_payment, property_value,
  construction_type, occupancy_type, Secured_by, total_units, income,
  credit_type, Credit_Score, co-applicant_credit_type, age,
  submission_of_application, LTV, Region, Security_Type, Status, dtir1
"""

def call_groq(prompt: str) -> str:
    """Helper to call the Groq API and return the text response."""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()

# --- Text-to-SQL functions ---

def generate_sql(user_question: str) -> str:
    """Turn a plain-English question into a SQL query."""
    prompt = f"""You are a SQL expert. Given this database schema:

{SCHEMA}

Write a SQLite query to answer this question: "{user_question}"

Rules:
- Return ONLY the SQL query, no explanation, no markdown formatting, no ```sql``` tags.
- Use the exact column names given above.
- For any text/string comparisons (like Region, Gender, loan_type, credit_type, etc.), always use LOWER(column_name) = LOWER('value') instead of a direct = comparison, since the data has inconsistent capitalization.
- If the question can't be answered from this schema, return: SELECT 'Cannot answer this from available data' AS message;
"""
    sql = call_groq(prompt)
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def run_sql(sql: str) -> pd.DataFrame:
    """Run SQL against the SQLite database and return results as a DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df

def generate_answer(user_question: str, result_df: pd.DataFrame) -> str:
    """Turn the raw SQL result into a natural-language answer."""
    result_text = result_df.to_string(index=False)
    prompt = f"""The user asked: "{user_question}"

Here is the query result:
{result_text}

Write a short, clear, natural-language answer based on this data. 
Do not mention SQL or databases. Just answer like a helpful analyst.
"""
    return call_groq(prompt)

# --- RAG setup ---

CHROMA_PATH = os.path.join("vectorstore", "chroma_db")
_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _chroma_client.get_collection(name="complaints")
_embedder = SentenceTransformer("all-MiniLM-L6-v2")

def is_rag_question(user_question: str) -> bool:
    """Decide whether a question should use RAG (complaints/experiences) or SQL (structured loan data), using free keyword matching (no API call)."""
    rag_keywords = [
        "complaint", "complaints", "problem", "problems", "issue", "issues",
        "experience", "experiences", "report", "reported", "reports",
        "customer", "customers", "said", "say", "opinion", "opinions",
        "feedback", "concern", "concerns", "trouble", "unhappy", "frustrat"
    ]
    question_lower = user_question.lower()
    return any(keyword in question_lower for keyword in rag_keywords)

def retrieve_complaints(user_question: str, n_results: int = 5) -> list:
    """Find the most relevant complaint narratives for a question."""
    query_embedding = _embedder.encode([user_question]).tolist()
    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    return results["documents"][0] if results["documents"] else []

def generate_rag_answer(user_question: str, retrieved_docs: list) -> str:
    """Generate an answer based on retrieved complaint narratives."""
    context = "\n\n---\n\n".join(retrieved_docs)
    prompt = f"""The user asked: "{user_question}"

Here are relevant consumer complaint excerpts:

{context}

Based on these complaints, write a short, clear answer to the user's question. 
Summarize patterns or common themes you see. Do not quote complaints word-for-word, paraphrase instead.
"""
    return call_groq(prompt)