# 📊 AI Analytics Co-pilot

An AI-powered analytics assistant that lets you ask plain-English questions about loan data and customer complaints. It automatically routes each question to the right data source — running SQL queries on structured loan data, or performing semantic search over unstructured complaint narratives — and returns a natural-language answer with supporting tables and charts.

**🔗 Live demo:** [ai-data-copilot-qntrnghwuoux25mnpx4pj4.streamlit.app](https://ai-data-copilot-qntrnghwuoux25mnpx4pj4.streamlit.app/)

---

## What it does

Ask a question like *"What is the average loan amount by region?"* or *"What issues have customers reported about their loans?"* — the app figures out which data source is relevant, retrieves the right information, and answers in plain language.

- **Text-to-SQL**: Converts natural-language questions into SQL queries run against a structured loan dataset (148,670 rows, 34 columns) — covering loan amounts, interest rates, credit scores, regions, income, and more.
- **RAG (Retrieval-Augmented Generation)**: Semantically searches a vector database of real consumer complaint narratives to answer questions about customer experiences, issues, and feedback.
- **Automatic routing**: Each question is classified and sent to the correct pipeline — no manual toggling required.
- **Auto-charting**: Query results are automatically visualized as bar charts (comparisons) or pie charts (proportions/distributions), chosen based on the question and data shape.
- **Transparent reasoning**: Every answer shows its source (SQL database or complaint corpus), the generated SQL query, or the retrieved complaint excerpts — so you can verify how the answer was derived.

### Example questions to try
- "What is the average interest rate for loans in the South region?"
- "What is the distribution of loans by loan type?"
- "What are customers most commonly complaining about regarding their loans?"
- "How many loans have a credit score below 600?"

---

## Architecture

```
User question (plain English)
        ↓
Streamlit chat UI
        ↓
   Keyword-based router
        ↓
   ┌────┴────┐
   ↓         ↓
SQL path   RAG path
   ↓         ↓
Groq LLM   Question embedded (sentence-transformers)
generates    ↓
SQL query  Semantic search in ChromaDB
   ↓         ↓
SQLite     Top-k relevant complaint
query        excerpts retrieved
   ↓         ↓
   └────┬────┘
        ↓
Groq LLM generates natural-language answer
        ↓
Answer + source label + table/chart (SQL)
or retrieved excerpts (RAG) shown in UI
```

---

## Tech stack

| Layer           | Tool                                        | Purpose                                   |
| --------------- | -------------------------------------------- | ------------------------------------------ |
| Language        | Python                                       | Core implementation                       |
| UI              | Streamlit                                    | Chat interface                            |
| LLM             | Groq API (`openai/gpt-oss-120b`)             | SQL generation, answer generation         |
| Structured data | SQLite                                       | Loan dataset storage and querying         |
| Embeddings      | sentence-transformers (`all-MiniLM-L6-v2`)   | Converting complaint text to vectors      |
| Vector store    | ChromaDB                                     | Semantic search over complaint narratives |
| Charting        | Plotly                                       | Auto-generated bar/pie charts             |
| Deployment      | Streamlit Community Cloud                    | Public hosting                            |

---

## Datasets

- **Structured — [Loan Default Dataset (Kaggle)](https://www.kaggle.com/datasets/yasserh/loan-default-dataset)**
  148,670 rows of loan application data — loan amount, region, credit score, interest rate, income, loan type, loan purpose, LTV, status, and more — loaded into a SQLite database (`analytics.db`, table `loans`).

- **Unstructured — [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/)**
  ~9,458 real consumer complaint records, filtered to the **"Consumer Loan"** product with narratives only. The free-text `Consumer complaint narrative` field is embedded (as full narratives, one embedding per complaint) and indexed in ChromaDB for semantic retrieval. A random sample of 2,000 narratives is used to keep local indexing time reasonable.

> Both CSVs are included directly in the `data/` folder of this repo, so no separate download is needed to run the project locally — just clone and go. (`.env`, containing the API key, is excluded via `.gitignore` and must be created separately — see setup steps below.)

---

## Project structure

```
ai-data-copilot/
├── data/
│   ├── Loan_Default.csv
│   └── complaints-*.csv
├── database/
│   └── create_db.py          # Loads CSV into SQLite
├── vectorstore/
│   ├── build_index.py        # Embeds complaint narratives into ChromaDB
│   └── chroma_db/            # Persisted vector index
├── app.py                    # Streamlit app: UI, routing, chart logic
├── llm_helper.py             # LLM calls: SQL generation, RAG retrieval, answer generation
└── requirements.txt
```

---

## Running it locally

1. **Clone the repo**
   ```
   git clone https://github.com/arpitasarkardata/ai-data-copilot.git
   cd ai-data-copilot
   ```

2. **Create a virtual environment and install dependencies**
   ```
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

3. **Add your Groq API key** — create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
   (Free API key available at [console.groq.com](https://console.groq.com))

4. **Build the database and vector index** (only needed once — the datasets are already included in `data/`)
   ```
   cd database
   python create_db.py
   cd ../vectorstore
   python build_index.py
   cd ..
   ```

5. **Run the app**
   ```
   streamlit run app.py
   ```

---

## Notable engineering decisions

- **Case-insensitive SQL matching** — the source data has inconsistent capitalization in categorical columns (e.g., `south`, `North`, `central`). The SQL-generation prompt instructs the LLM to always use `LOWER()` comparisons to avoid silent query mismatches.
- **Keyword-based routing instead of an LLM call** — rather than spending an extra API call per question to classify SQL vs. RAG, routing is done with a lightweight keyword match, reducing API usage by roughly half with no meaningful accuracy trade-off for this use case.
- **Chart type selection** — charts are chosen based on question intent (proportion-related keywords → pie chart) and data shape (safety fallback to bar chart when there are too many categories for a readable pie chart).

---

## Known limitations

- Chart rendering can occasionally flicker/disappear on window resize — a known Plotly-in-Streamlit quirk, not a data issue.
- The complaint vector index is built from a sample of 2,000 complaints (out of ~9,458) to keep indexing time reasonable for local development.
- Groq's free-tier rate limits apply; heavy concurrent usage may be throttled.

## Future improvements

- Expand the vector index to the full complaint set
- Replace keyword-based routing with a lightweight classifier for edge cases
- Add hybrid questions that combine SQL and RAG results in a single answer
- Chunk longer complaint narratives before embedding, to improve retrieval precision on lengthy complaints

---

## License

This project is for portfolio/demonstration purposes.
