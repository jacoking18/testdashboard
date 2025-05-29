import streamlit as st
import pandas as pd
import plotly.express as px

# ————— Page config —————
st.set_page_config(
    page_title="Lead Analytics Dashboard",
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
    help="Upload your lead data"
)
if not uploaded_file:
    st.sidebar.info("Please upload a CSV to begin.")
    st.stop()

# ————— Read data —————
try:
    df_raw = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Error loading file: {e}")
    st.stop()

# Work copy
df = df_raw.copy()

# ————— 2. Field Mapping —————
st.sidebar.header("2. Field Mapping")
columns = df.columns.tolist()
id_field = st.sidebar.selectbox("Unique ID field", options=[None] + columns)
provider_field = st.sidebar.selectbox("Provider field", options=[None] + columns)
cost_field = st.sidebar.selectbox("Cost field (numeric)", options=[None] + columns)
date_field = st.sidebar.selectbox("Date field", options=[None] + columns)

# Convert and filter by date if mapped
if date_field:
    df[date_field] = pd.to_datetime(df[date_field], errors='coerce')
    start, end = st.sidebar.date_input(
        "Filter by date range", [df[date_field].min(), df[date_field].max()]
    )
    df = df[(df[date_field] >= pd.to_datetime(start)) & (df[date_field] <= pd.to_datetime(end))]

# ————— 3. Filters —————
st.sidebar.header("3. Additional Filters")
for col in df.columns:
    if col in [id_field, provider_field, cost_field, date_field]:
        continue
    vals = df[col].dropna().unique()
    if len(vals) <= 50:
        sel = st.sidebar.multiselect(f"Filter {col}", options=sorted(vals), default=list(vals))
        df = df[df[col].isin(sel)]

# ————— 4. Data Overview —————
st.subheader("📋 Data Overview")
st.write(f"Total records: {len(df):,}")
st.dataframe(df.head(10))

# ————— 5. Duplicate Detection —————
st.subheader("🔎 Duplicate Leads")
if id_field:
    dup_counts = df[id_field].value_counts()
    dup = dup_counts[dup_counts > 1]
    st.write(f"Found {len(dup)} duplicate IDs")
    if not dup.empty:
        st.dataframe(dup.rename('count').to_frame())
        if st.checkbox("Show duplicated rows details"):
            st.dataframe(df[df[id_field].isin(dup.index)])
else:
    st.info("Select Unique ID field to detect duplicates.")

# ————— 6. Spend Analysis —————
st.subheader("💰 Spend Analysis")
if provider_field and cost_field:
    df[cost_field] = pd.to_numeric(df[cost_field], errors='coerce')
    spend = (
        df.groupby(provider_field)[cost_field]
        .agg(total_spend='sum', lead_count='count', avg_cost='mean')
        .sort_values('total_spend', ascending=False)
    )
    st.write(spend)
    fig = px.bar(
        spend.reset_index(),
        x=provider_field, y='total_spend',
        title='Total Spend by Provider'
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Map Provider and Cost fields for spend analysis.")

# ————— 7. Custom Chart Builder —————
st.subheader("📊 Custom Chart Builder")
st.write("Configure X, Y, and aggregation for tailored visualizations.")

chart_cols = df.select_dtypes(include=['number', 'object', 'category', 'datetime']).columns.tolist()
x = st.selectbox("X-axis", options=[None] + chart_cols)
if x:
    y_options = df.select_dtypes(include=['number']).columns.tolist()
    y = st.selectbox("Y-axis (numeric)", options=[None] + y_options)
    agg = st.selectbox("Aggregation", options=["None", "Count", "Sum", "Mean"])
    chart_type = st.selectbox("Chart type", options=["Bar", "Line", "Scatter", "Pie"])
    if st.button("Generate Chart"):
        temp = df.copy()
        if agg != "None" and y:
            if agg == "Count":
                data = temp.groupby(x).size().reset_index(name='value')
            else:
                data = temp.groupby(x)[y].agg('sum' if agg=='Sum' else 'mean').reset_index(name='value')
            fig = getattr(px, chart_type.lower())(data, x=x, y='value', title=f"{agg} of {y} by {x}")
        elif y and agg == "None":
            fig = getattr(px, chart_type.lower())(temp, x=x, y=y, title=f"{y} vs {x}")
        else:
            fig = px.histogram(temp, x=x, title=f"Distribution of {x}")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Select an X-axis to start.")

# ————— Footer —————
st.markdown("---")
st.caption("Made with ❤️ using Streamlit & Plotly")
