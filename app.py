"""Streamlit application for exploring Swedish job postings."""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from main import collect_jobs_sync, jobs_to_dataframe

st.set_page_config(page_title="Swedish Job Explorer", layout="wide")
st.title("Swedish Job Explorer")
st.caption("Collects open positions from Arbetsformedlingen, Monster and TNG.")


@st.cache_data(show_spinner=False)
def load_jobs(job_title: str | None, location: str | None, limit: int, use_groq: bool) -> pd.DataFrame:
    """Fetch and cache job data based on the provided filters."""
    jobs = collect_jobs_sync(job_title=job_title, location=location, limit=limit, use_groq=use_groq)
    return jobs_to_dataframe(jobs)


with st.form("job_filters"):
    job_title = st.text_input("Job title", value="data engineer")
    location = st.text_input("Location", value="Stockholm")
    limit = st.slider("Maximum jobs per source", min_value=5, max_value=50, value=20, step=5)
    use_groq = st.toggle("Use Groq summaries", value=False, help="Requires GROQ_API_KEY to be set.")
    submitted = st.form_submit_button("Fetch jobs")

if submitted:
    with st.spinner("Collecting job postings..."):
        st.session_state["jobs_df"] = load_jobs(job_title or None, location or None, limit, use_groq)

jobs_df: pd.DataFrame | None = st.session_state.get("jobs_df")

if jobs_df is not None and not jobs_df.empty:
    sources = sorted(jobs_df["source"].dropna().unique())
    selected_sources = st.multiselect("Source", options=sources, default=sources)
    filtered_df = jobs_df[jobs_df["source"].isin(selected_sources)] if selected_sources else jobs_df

    st.subheader("Results")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    csv_buffer = io.BytesIO()
    filtered_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "Download CSV",
        data=csv_buffer.getvalue(),
        file_name="jobs.csv",
        mime="text/csv",
    )

    json_str = filtered_df.to_json(orient="records", force_ascii=False, indent=2)
    st.download_button(
        "Download JSON",
        data=json_str,
        file_name="jobs.json",
        mime="application/json",
    )
else:
    st.info("Adjust the filters above and click 'Fetch jobs' to begin.")
