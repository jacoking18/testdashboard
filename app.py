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
st.title("🚀 CSV-to-Dashboard App")

# ————— Sidebar: File upload —————
st.sidebar.header("1. Upload CSV")
uploaded_file = st.sidebar.file_uploader(
    "Choose a CSV file",
    type=["csv"],
    help="Only .csv files supported"
)
if not uploaded_file:
    st.sidebar.info("Please upload a CSV to begin.")
    st.stop()

# ————— Read CSV —————
try:
    df_raw = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Error loading file: {e}")
    st.stop()

# Copy for filtering
df = df_raw.copy()

# ————— Sidebar: Filters —————
st.sidebar.header("2. Filters")
# Date range filter for datetime columns
datetime_cols = df.select_dtypes(include="datetime").columns.tolist()
# Attempt parsing
for col in df.columns:
    if df[col].dtype == 'object':
        try:
            df[col] = pd.to_datetime(df[col])
            datetime_cols.append(col)
        except:
            pass

if datetime_cols:
    date_col = st.sidebar.selectbox("Date column for range filter", [None] + datetime_cols)
    if date_col:
        min_date, max_date = st.sidebar.date_input(
            "Select date range",
            value=[df[date_col].min(), df[date_col].max()]
        )
        df = df[(df[date_col] >= pd.to_datetime(min_date)) & (df[date_col] <= pd.to_datetime(max_date))]

# Categorical and numeric filters
disable = []
for col in df.columns:
    if col in datetime_cols:
        continue
    vals = df[col].dropna().unique().tolist()
    if len(vals) <= 50:
        selected = st.sidebar.multiselect(f"Filter {col}", vals, default=vals)
        df = df[df[col].isin(selected)]
    else:
        disable.append(col)
if disable:
    st.sidebar.caption(f"Skipped filters for high-cardinality columns: {', '.join(disable)}")

# ————— Data preview —————
st.subheader("📋 Filtered Data Preview")
st.dataframe(df, height=300)

# ————— Sidebar: Visualization options —————
st.sidebar.header("3. Visualization")
# Grid mode toggle
grid_mode = st.sidebar.checkbox("Grid mode for auto charts", value=False)
# Histogram bins
bins = st.sidebar.slider("Histogram bins", min_value=5, max_value=100, value=20)

numeric_cols = df.select_dtypes(include="number").columns.tolist()
categorical_cols = df.select_dtypes(exclude=["number", "datetime"]).columns.tolist()

# ————— Auto-Generated Charts —————
st.subheader("📊 Auto-Generated Charts")
if grid_mode:
    # Numeric in grid
    if numeric_cols:
        cols = st.columns(2)
        for i, num in enumerate(numeric_cols):
            fig = px.histogram(df, x=num, nbins=bins, title=f"Distribution of {num}")
            cols[i % 2].plotly_chart(fig, use_container_width=True)
    if categorical_cols:
        cols2 = st.columns(2)
        for i, cat in enumerate(categorical_cols):
            counts = df[cat].value_counts().reset_index()
            counts.columns = [cat, "count"]
            fig = px.bar(counts, x=cat, y="count", title=f"Counts of {cat}")
            cols2[i % 2].plotly_chart(fig, use_container_width=True)
else:
    col1, col2 = st.columns(2)
    with col1:
        if numeric_cols:
            num = numeric_cols[0]
            fig1 = px.histogram(df, x=num, nbins=bins, title=f"Distribution of {num}")
            st.plotly_chart(fig1, use_container_width=True)
    with col2:
        if categorical_cols:
            cat = categorical_cols[0]
            counts = df[cat].value_counts().reset_index()
            counts.columns = [cat, "count"]
            fig2 = px.bar(counts, x=cat, y="count", title=f"Counts of {cat}")
            st.plotly_chart(fig2, use_container_width=True)

# ————— Custom Chart Builder —————
st.sidebar.subheader("Custom Chart Builder")
chart_type = st.sidebar.selectbox("Chart type", ["Line", "Bar", "Scatter", "Pie"])
x_axis = st.sidebar.selectbox("X-axis", df.columns)
agg = st.sidebar.selectbox("Aggregate", ["None", "Count"])
if chart_type == "Pie":
    y_axis = st.sidebar.selectbox("Values", numeric_cols)
elif agg == "None":
    y_axis = st.sidebar.selectbox("Y-axis", numeric_cols if numeric_cols else df.columns)
else:
    y_axis = None

if st.sidebar.button("Generate Chart"):
    if agg == "Count":
        grouped = df.groupby(x_axis).size().reset_index(name='count')
        if chart_type == "Bar":
            fig = px.bar(grouped, x=x_axis, y='count', title=f"Count by {x_axis}")
        else:
            fig = px.scatter(grouped, x=x_axis, y='count', title=f"Count by {x_axis}")
    else:
        if chart_type == "Line":
            fig = px.line(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
        elif chart_type == "Bar":
            fig = px.bar(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
        else:
            fig = px.pie(df, names=x_axis, values=y_axis, title=f"{y_axis} distribution")
    st.plotly_chart(fig, use_container_width=True)

# ————— Footer —————
st.markdown("---")
st.markdown(
    "<center>Made with ❤️ using Streamlit & Plotly | Upload a new file to refresh</center>",
    unsafe_allow_html=True
)
