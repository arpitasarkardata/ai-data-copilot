import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os

# Make sure Python can find llm_helper.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_helper import (
    generate_sql, run_sql, generate_answer,
    is_rag_question, retrieve_complaints, generate_rag_answer
)

st.set_page_config(page_title="AI Analytics Co-pilot", layout="wide")
st.title("📊 AI Analytics Co-pilot")
st.caption("Ask questions about loan data or customer complaints in plain English")

# Keep chat history in session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg:
            with st.expander("View generated SQL"):
                st.code(msg["sql"], language="sql")
        if "source" in msg:
            st.caption(f"Source: {msg['source']}")

# Chat input
user_question = st.chat_input("Ask a question about loan data or complaints...")

if user_question:
    # Show user message
    with st.chat_message("user"):
        st.markdown(user_question)
    st.session_state.messages.append({"role": "user", "content": user_question})

    # Route and answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                use_rag = is_rag_question(user_question)

                if use_rag:
                    # RAG path
                    retrieved_docs = retrieve_complaints(user_question)
                    if not retrieved_docs:
                        answer = "I couldn't find any relevant complaints for this question."
                    else:
                        answer = generate_rag_answer(user_question, retrieved_docs)

                    st.markdown(answer)
                    st.caption("Source: Customer complaints (RAG)")

                    with st.expander("View retrieved complaint excerpts"):
                        for i, doc in enumerate(retrieved_docs, 1):
                            st.markdown(f"**Excerpt {i}:** {doc[:300]}...")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "source": "Customer complaints (RAG)"
                    })

                else:
                    # SQL path
                    sql = generate_sql(user_question)
                    result_df = run_sql(sql)
                    answer = generate_answer(user_question, result_df)

                    st.markdown(answer)
                    st.caption("Source: Loan database (SQL)")

                    with st.expander("View generated SQL"):
                        st.code(sql, language="sql")

                    if not result_df.empty and len(result_df) > 1:
                        st.dataframe(result_df)

                        # Auto-chart if we have exactly one text column and one numeric column
                        if len(result_df.columns) == 2:
                            col1, col2 = result_df.columns
                            if pd.api.types.is_string_dtype(result_df[col1]) and pd.api.types.is_numeric_dtype(result_df[col2]):

                                proportion_keywords = ["percentage", "proportion", "share", "distribution", "breakdown"]
                                use_pie = any(kw in user_question.lower() for kw in proportion_keywords)

                                if use_pie and len(result_df) <= 8:
                                    fig = px.pie(result_df, names=col1, values=col2, title=user_question)
                                else:
                                    fig = px.bar(result_df, x=col1, y=col2, title=user_question)

                                st.plotly_chart(fig, use_container_width=True)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sql": sql,
                        "source": "Loan database (SQL)"
                    })

            except Exception as e:
                error_msg = f"Something went wrong: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})