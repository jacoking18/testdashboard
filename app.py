import streamlit as st
import pandas as pd
import plotly.express as px

# ————— Page config —————
st.set_page_config(
    page_title="CSV Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ————— Title —————
st.title("🚀 Lead Analytics Dashboard")

# ————— 1. Upload CSV —————
st.sidebar.header("1. Upload CSV")
uploaded_file = st.sidebar.file_uploader(
    "Choose a CSV file",
    type=["csv"],
    help="Upload lead data with columns like ID, Provider, Cost"
)
if not uploaded_file:
    st.sidebar.info("Upload a CSV to begin analysis")
    st.stop()

# ————— Read data —————
try:
    df_raw = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Error loading file: {e}")
    st.stop()
# Work copy
df = df_raw.copy()

# ————— 2. Filters —————
st.sidebar.header("2. Filters")
# Convert object columns to datetime if possible
for col in df.columns:
    if df[col].dtype == 'object':
        try:
            df[col] = pd.to_datetime(df[col])
        except:
            pass

# Date range filter
date_cols = df.select_dtypes(include='datetime').columns.tolist()
if date_cols:
    date_col = st.sidebar.selectbox("Date column", [None] + date_cols)
    if date_col:
        start, end = st.sidebar.date_input(
            "Date range", [df[date_col].min(), df[date_col].max()]
        )
        df = df[(df[date_col] >= pd.to_datetime(start)) & (df[date_col] <= pd.to_datetime(end))]

# Categorical filters
for col in df.select_dtypes(include=['object', 'category']).columns:
    vals = df[col].dropna().unique().tolist()
    if len(vals) < 50:
        sel = st.sidebar.multiselect(f"Filter {col}", options=vals, default=vals)
        df = df[df[col].isin(sel)]

# ————— 3. Data Overview —————
st.subheader("📋 Data Overview")
st.write(f"Total records: {len(df):,}")
st.dataframe(df.head(10))

# ————— 4. Duplicate Leads Analysis —————
st.subheader("🔎 Duplicate Leads")
# Select ID column for duplicates
dup_col = st.selectbox("Lead ID column for duplicate detection", options=[None] + list(df.columns))
if dup_col:
    dup_counts = df[dup_col].value_counts()
    dup_values = dup_counts[dup_counts > 1]
    st.write(f"Found {len(dup_values)} duplicated IDs (total duplicates: {dup_counts.sum() - len(dup_counts)})")
    if not dup_values.empty:
        st.dataframe(dup_values.rename('count').to_frame())
        # Show detail of duplicated rows
        if st.checkbox("Show duplicated row details"):
            duplicated_rows = df[df[dup_col].isin(dup_values.index)]
            st.dataframe(duplicated_rows)

# ————— 5. Cost by Provider —————
st.subheader("💰 Cost and Spend Analysis")
# Select provider and cost columns
providers = df.columns.tolist()
prov_col = st.selectbox("Lead Provider column", options=[None] + providers)
cost_col = st.selectbox("Cost column", options=[None] + providers)
if prov_col and cost_col:
    df[cost_col] = pd.to_numeric(df[cost_col], errors='coerce')
    summary = (
        df.groupby(prov_col)[cost_col]
        .agg(total_spend='sum', lead_count='count', avg_cost='mean')
        .sort_values('total_spend', ascending=False)
    )
    st.write("Spend summary by provider:")
    st.dataframe(summary)
    # Plot spend
    fig_spend = px.bar(
        summary.reset_index(),
        x=prov_col,
        y='total_spend',
        title='Total Spend by Provider',
        labels={'total_spend':'Total Spend', prov_col:'Provider'}
    )
    st.plotly_chart(fig_spend, use_container_width=True)

# ————— 6. Auto Charts —————
st.subheader("📊 Quick Distribution Charts")
num_cols = df.select_dtypes(include='number').columns.tolist()
cat_cols = df.select_dtypes(include=['object','category']).columns.tolist()
if num_cols:
    col = st.selectbox("Numeric column for histogram", num_cols)
    bins = st.slider("Bins", min_value=5, max_value=100, value=20)
    fig = px.histogram(df, x=col, nbins=bins, title=f"Distribution of {col}")
    st.plotly_chart(fig, use_container_width=True)
if cat_cols:
    c = st.selectbox("Categorical column for bar chart", cat_cols)
    counts = df[c].value_counts().reset_index()
    counts.columns = [c, 'count']
    fig2 = px.bar(counts, x=c, y='count', title=f"Counts of {c}")
    st.plotly_chart(fig2, use_container_width=True)

# ————— Footer —————
st.markdown("---")
st.caption("Made with ❤️ using Streamlit & Plotly")
