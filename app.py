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
uploaded_file = st.sidebar.file_uploader(
    "🔽 Upload your CSV file",
    type=["csv"],
    help="Only .csv files are supported for now."
)
if not uploaded_file:
    st.sidebar.info("Please upload a CSV to begin.")
    st.stop()

# ————— Read CSV —————
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"❗️ Error loading file:\n{e}")
    st.stop()

# ————— Data preview —————
st.subheader("📋 Data Preview")
st.dataframe(df, height=300)

# ————— Column type inference —————
for col in df.columns:
    if df[col].dtype == object:
        try:
            df[col] = pd.to_datetime(df[col])
        except Exception:
            pass

numeric_cols = df.select_dtypes(include="number").columns.tolist()
datetime_cols = df.select_dtypes(include="datetime").columns.tolist()
categorical_cols = df.select_dtypes(exclude=["number", "datetime"]).columns.tolist()

# ————— Sidebar: Visualization options —————
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Visualization Options")

# Grid mode toggle for auto-generated charts
grid_mode = st.sidebar.checkbox("Grid mode for auto-charts", value=False)

# Custom chart builder options
st.sidebar.subheader("🛠️ Build Your Own Chart")
chart_type = st.sidebar.selectbox(
    "Chart type",
    ["Line", "Bar", "Scatter", "Pie"]
)
x_axis = st.sidebar.selectbox("X-axis", df.columns)

# Aggregate functions
agg = st.sidebar.selectbox("Aggregate function", ["None", "Count"])

# Y-axis selection (only for non-pie, non-count)
if chart_type == "Pie":
    y_axis = st.sidebar.selectbox(
        "Values (for Pie)",
        numeric_cols,
        help="Select a numeric column for slice sizes."
    )
elif agg == "None":
    y_axis = st.sidebar.selectbox(
        "Y-axis",
        numeric_cols if numeric_cols else df.columns
    )
else:
    y_axis = None  # will be overridden by count logic

# ————— Auto-Generated Charts —————
st.subheader("📊 Auto-Generated Charts")

if grid_mode:
    # generate all numeric histograms in a grid
    if numeric_cols:
        cols = st.columns(2)
        for i, num in enumerate(numeric_cols):
            fig = px.histogram(
                df,
                x=num,
                title=f"Distribution of {num}",
                marginal="box"
            )
            cols[i % 2].plotly_chart(fig, use_container_width=True)
    else:
        st.info("No numeric columns for histograms.")

    # generate all categorical bar charts in next grid
    if categorical_cols:
        cols2 = st.columns(2)
        for i, cat in enumerate(categorical_cols):
            counts = df[cat].value_counts().reset_index()
            counts.columns = [cat, "count"]
            fig = px.bar(
                counts,
                x=cat,
                y="count",
                title=f"Counts of {cat}"
            )
            cols2[i % 2].plotly_chart(fig, use_container_width=True)
    else:
        st.info("No categorical columns for bar charts.")

else:
    # default single numeric + single categorical
    col1, col2 = st.columns(2)
    with col1:
        if numeric_cols:
            num = numeric_cols[0]
            fig1 = px.histogram(
                df,
                x=num,
                title=f"Distribution of {num}",
                marginal="box"
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No numeric columns found for histogram.")
    with col2:
        if categorical_cols:
            cat = categorical_cols[0]
            counts = df[cat].value_counts().reset_index()
            counts.columns = [cat, "count"]
            fig2 = px.bar(
                counts,
                x=cat,
                y="count",
                title=f"Counts of {cat}"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No categorical columns found for bar chart.")

# ————— Custom Chart Builder —————
if st.sidebar.button("Generate Chart"):
    try:
        if agg == "Count":
            grouped = df.groupby(x_axis).size().reset_index(name='count')
            if chart_type in ["Bar", "Scatter"]:
                if chart_type == "Bar":
                    fig = px.bar(
                        grouped,
                        x=x_axis,
                        y='count',
                        title=f"Count of records by {x_axis}"
                    )
                else:
                    fig = px.scatter(
                        grouped,
                        x=x_axis,
                        y='count',
                        title=f"Count of records by {x_axis}"
                    )
            else:
                st.error("Count aggregation only supported for Bar and Scatter charts.")
                fig = None
        else:
            if chart_type == "Line":
                fig = px.line(df, x=x_axis, y=y_axis,
                              title=f"{chart_type} of {y_axis} vs {x_axis}")
            elif chart_type == "Bar":
                fig = px.bar(df, x=x_axis, y=y_axis,
                             title=f"{chart_type} of {y_axis} vs {x_axis}")
            elif chart_type == "Scatter":
                fig = px.scatter(df, x=x_axis, y=y_axis,
                                 title=f"{chart_type} of {y_axis} vs {x_axis}")
            else:  # Pie
                fig = px.pie(df, names=x_axis, values=y_axis,
                             title=f"{chart_type} of {y_axis}")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not generate chart: {e}")

# ————— Footer —————
st.markdown("---")
st.markdown(
    "<center>Made with ❤️ using Streamlit & Plotly | "
    "Upload a new file to refresh</center>",
    unsafe_allow_html=True
)
