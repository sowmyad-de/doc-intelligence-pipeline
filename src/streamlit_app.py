"""
Healthcare Claims Document Intelligence Dashboard
Reads from Snowflake Gold layer and renders KPIs + charts.
"""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Healthcare Claims Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="GOLD",
    )


@st.cache_data(ttl=300)
def run_query(sql):
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)
    df = cur.fetch_pandas_all()
    cur.close()
    return df


st.title("Healthcare Claims Document Intelligence")
st.caption("End-to-end pipeline: PDF to Claude API to Snowflake Medallion to Dashboard")

st.sidebar.header("Filters")
carriers_df = run_query("SELECT INSURANCE_CARRIER FROM GOLD_CLAIMS_BY_CARRIER ORDER BY INSURANCE_CARRIER")
carrier_options = ["All Carriers"] + carriers_df["INSURANCE_CARRIER"].tolist()
selected_carrier = st.sidebar.selectbox("Insurance Carrier", carrier_options)

st.sidebar.markdown("---")
st.sidebar.markdown("**Pipeline Stats**")
st.sidebar.markdown("- 500 PDFs processed")
st.sidebar.markdown("- 100% extraction success")
st.sidebar.markdown("- Bronze to Silver to Gold")

if selected_carrier == "All Carriers":
    kpi_sql = "SELECT SUM(TOTAL_CLAIMS) AS TOTAL_CLAIMS, SUM(TOTAL_CLAIM_AMOUNT) AS TOTAL_AMOUNT, ROUND(AVG(AVG_CLAIM_AMOUNT), 2) AS AVG_CLAIM, COUNT(*) AS CARRIER_COUNT FROM GOLD_CLAIMS_BY_CARRIER"
else:
    kpi_sql = f"SELECT TOTAL_CLAIMS, TOTAL_CLAIM_AMOUNT AS TOTAL_AMOUNT, AVG_CLAIM_AMOUNT AS AVG_CLAIM, 1 AS CARRIER_COUNT FROM GOLD_CLAIMS_BY_CARRIER WHERE INSURANCE_CARRIER = '{selected_carrier}'"

kpi_df = run_query(kpi_sql)
total_claims = int(kpi_df["TOTAL_CLAIMS"].iloc[0])
total_amount = float(kpi_df["TOTAL_AMOUNT"].iloc[0])
avg_claim = float(kpi_df["AVG_CLAIM"].iloc[0])
carrier_count = int(kpi_df["CARRIER_COUNT"].iloc[0])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Claims", f"{total_claims:,}")
col2.metric("Total Billed", f"${total_amount:,.2f}")
col3.metric("Avg Claim", f"${avg_claim:,.2f}")
col4.metric("Carriers", carrier_count)

st.markdown("---")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Claims by Insurance Carrier")
    carrier_chart_df = run_query("SELECT INSURANCE_CARRIER, TOTAL_CLAIMS, TOTAL_CLAIM_AMOUNT FROM GOLD_CLAIMS_BY_CARRIER ORDER BY TOTAL_CLAIM_AMOUNT DESC")
    fig = px.bar(carrier_chart_df, x="INSURANCE_CARRIER", y="TOTAL_CLAIM_AMOUNT", labels={"INSURANCE_CARRIER": "Carrier", "TOTAL_CLAIM_AMOUNT": "Total Billed ($)"}, text="TOTAL_CLAIMS")
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Top 10 Diagnosis Codes")
    diag_df = run_query("SELECT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, CLAIM_COUNT, TOTAL_AMOUNT FROM GOLD_CLAIMS_BY_DIAGNOSIS ORDER BY CLAIM_COUNT DESC LIMIT 10")
    fig2 = px.bar(diag_df, x="CLAIM_COUNT", y="DIAGNOSIS_CODE", orientation="h", hover_data=["DIAGNOSIS_DESCRIPTION", "TOTAL_AMOUNT"], labels={"CLAIM_COUNT": "Claims", "DIAGNOSIS_CODE": "ICD-10 Code"})
    fig2.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Daily Claims Trend")
trend_df = run_query("SELECT SERVICE_DATE, DAILY_CLAIM_COUNT, DAILY_TOTAL_AMOUNT FROM GOLD_DAILY_CLAIMS_TREND ORDER BY SERVICE_DATE")
fig3 = px.line(trend_df, x="SERVICE_DATE", y="DAILY_TOTAL_AMOUNT", labels={"SERVICE_DATE": "Service Date", "DAILY_TOTAL_AMOUNT": "Daily Total ($)"}, markers=True)
fig3.update_layout(height=350)
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Top 15 Providers by Total Billed")
prov_df = run_query("SELECT PROVIDER_NAME, CLAIM_COUNT, TOTAL_BILLED, UNIQUE_PATIENTS FROM GOLD_CLAIMS_BY_PROVIDER ORDER BY TOTAL_BILLED DESC LIMIT 15")
st.dataframe(prov_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Architecture: Synthetic PDFs to pdfplumber to Claude API (extraction) to pydantic validation to Snowflake VARIANT (Bronze) to typed Silver with quality checks to Gold aggregations to Streamlit dashboard.")
