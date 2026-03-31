import streamlit as st
import pandas as pd
from doc_processing import process_invoices, analyze_invoices
from model_gateway import invoke_llm


# Page configuration
st.set_page_config(
    page_title="AI Travel Expense Tracker",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced custom CSS styling
custom_css = """
<style>
/* Hide Streamlit branding */
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

/* Global font and background improvements */
.stApp {
    background: linear-gradient(to bottom, #f8fafc 0%, #e2e8f0 100%);
}

/* Hero banner animation */
@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.hero-banner {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%);
    padding: 2.5rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(30, 58, 138, 0.3);
    animation: fadeInDown 0.8s ease-out;
}

.hero-banner h1 {
    color: white;
    margin: 0;
    font-size: 2.5rem;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.hero-banner p {
    color: #e0e7ff;
    margin: 0.5rem 0 0 0;
    font-size: 1.2rem;
    font-weight: 300;
}

/* File uploader styling */
.stFileUploader {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    border: 2px dashed #3b82f6;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
}

.stFileUploader:hover {
    border-color: #1e3a8a;
    box-shadow: 0 6px 12px rgba(59, 130, 246, 0.15);
}

/* Button styling */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* Metric card styling */
div[data-testid="metric-container"] {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    border-left: 4px solid #3b82f6;
    transition: all 0.3s ease;
}

div[data-testid="metric-container"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.2);
}

/* Dataframe styling */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

/* Section headers */
.section-header {
    color: #1e3a8a;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #3b82f6;
}

/* Info box styling */
.stAlert {
    border-radius: 12px;
    border-left: 4px solid #3b82f6;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

/* Success message */
.stSuccess {
    background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
    color: white;
    border-radius: 12px;
    padding: 1rem;
    font-weight: 600;
}

/* Warning message */
.stWarning {
    background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
    color: white;
    border-radius: 12px;
    padding: 1rem;
    font-weight: 600;
}

/* Error message */
.stError {
    background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
    color: white;
    border-radius: 12px;
    padding: 1rem;
    font-weight: 600;
}

/* Spinner */
.stSpinner > div {
    border-color: #3b82f6 !important;
}

/* Chart containers */
.js-plotly-plot {
    border-radius: 12px;
    background: white;
    padding: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

/* Summary box */
.summary-box {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    padding: 2rem;
    border-radius: 12px;
    border-left: 4px solid #3b82f6;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin-top: 1rem;
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem;
    color: #64748b;
    font-size: 0.9rem;
    margin-top: 3rem;
}

/* Fade in animation for content */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.fade-in {
    animation: fadeIn 0.6s ease-in;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'total_budget' not in st.session_state:
    st.session_state.total_budget = 5000
if 'hotel_budget' not in st.session_state:
    st.session_state.hotel_budget = 2000
if 'flight_budget' not in st.session_state:
    st.session_state.flight_budget = 1500
if 'meal_budget' not in st.session_state:
    st.session_state.meal_budget = 800
if 'car_budget' not in st.session_state:
    st.session_state.car_budget = 700

# Sidebar - Budget Settings
with st.sidebar:
    st.markdown("### 💰 Budget Settings")
    
    st.session_state.total_budget = st.number_input(
        "Total Trip Budget",
        min_value=0,
        value=st.session_state.total_budget,
        step=100,
        format="%d",
        help="Set your overall trip budget"
    )
    
    st.markdown("#### Per-Category Budgets")
    
    st.session_state.hotel_budget = st.number_input(
        "Hotel Budget",
        min_value=0,
        value=st.session_state.hotel_budget,
        step=100,
        format="%d"
    )
    
    st.session_state.flight_budget = st.number_input(
        "Flight Budget",
        min_value=0,
        value=st.session_state.flight_budget,
        step=100,
        format="%d"
    )
    
    st.session_state.meal_budget = st.number_input(
        "Meal Budget",
        min_value=0,
        value=st.session_state.meal_budget,
        step=100,
        format="%d"
    )
    
    st.session_state.car_budget = st.number_input(
        "Car Rental Budget",
        min_value=0,
        value=st.session_state.car_budget,
        step=100,
        format="%d"
    )


def generate_summary(df: pd.DataFrame) -> str:
    """Generate AI summary of expense data."""
    # Compute statistics
    total_amount = df['Amount'].sum()
    num_items = len(df)
    
    # Breakdown by category
    category_breakdown = df.groupby('Category')['Amount'].sum().to_dict()
    category_str = ", ".join([f"{cat}: ${amt:.2f}" for cat, amt in category_breakdown.items()])
    
    # Top vendor
    top_vendor = df.groupby('Vendor')['Amount'].sum().idxmax()
    top_vendor_amount = df.groupby('Vendor')['Amount'].sum().max()
    
    # Breakdown by doc type
    doc_type_breakdown = df.groupby('Doc Type')['Amount'].sum().to_dict()
    doc_type_str = ", ".join([f"{doc}: ${amt:.2f}" for doc, amt in doc_type_breakdown.items()])
    
    # Try to compute date range and average daily spend
    try:
        df['Date_parsed'] = pd.to_datetime(df['Date'])
        date_range = f"{df['Date_parsed'].min().strftime('%Y-%m-%d')} to {df['Date_parsed'].max().strftime('%Y-%m-%d')}"
        num_days = (df['Date_parsed'].max() - df['Date_parsed'].min()).days + 1
        avg_daily_spend = total_amount / num_days if num_days > 0 else 0
        date_info = f"Date range: {date_range}. Average daily spend: ${avg_daily_spend:.2f}."
    except:
        date_info = ""
    
    # Build prompt
    prompt = f"""Analyze these travel expense statistics and provide a 3-4 sentence plain English summary:

Total expenses: ${total_amount:.2f}
Number of line items: {num_items}
Category breakdown: {category_str}
Top vendor: {top_vendor} (${top_vendor_amount:.2f})
Document type breakdown: {doc_type_str}
{date_info}

Provide a concise, professional summary highlighting key insights and spending patterns."""
    
    # Call LLM
    summary = invoke_llm(prompt)
    return summary


# Hero banner with enhanced styling
st.markdown("""
<div class="hero-banner">
    <h1>✈️ AI Travel Expense Tracker</h1>
    <p>Upload your travel receipts and let AI extract and analyze your expenses instantly</p>
</div>
""", unsafe_allow_html=True)

# Instructions section
with st.container():
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
        <h3 style="color: #1e3a8a; margin-top: 0;">📝 How it works</h3>
        <ol style="color: #475569; line-height: 1.8;">
            <li><strong>Upload</strong> your PDF receipts (up to 10 files)</li>
            <li><strong>Submit</strong> to extract expense data using AI</li>
            <li><strong>Analyze</strong> to view interactive charts and insights</li>
            <li><strong>Generate Summary</strong> for an AI-powered expense report</li>
            <li><strong>Export CSV</strong> to download your data</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# File uploader with enhanced styling
st.markdown('<div class="fade-in">', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "📎 Upload PDF Receipts",
    type=['pdf'],
    accept_multiple_files=True,
    help="Drag and drop or click to upload up to 10 PDF receipts"
)
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_files and len(uploaded_files) > 10:
    st.error("⚠️ Please upload a maximum of 10 files.")
    uploaded_files = uploaded_files[:10]

# Action buttons with icons
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    submit_button = st.button("🚀 Submit", type="primary", use_container_width=True)

with col2:
    analyze_button = st.button("📊 Analyze", use_container_width=True)

with col3:
    summary_button = st.button("🤖 Generate Summary", use_container_width=True)

with col4:
    if st.session_state.df is not None:
        csv = st.session_state.df.to_csv(index=False)
        st.download_button(
            label="💾 Export CSV",
            data=csv,
            file_name="expenses.csv",
            mime="text/csv",
            use_container_width=True
        )

# Submit button logic
if submit_button:
    if uploaded_files:
        with st.spinner("Processing receipts..."):
            st.session_state.df = process_invoices(uploaded_files)
            st.session_state.summary = None
        st.success(f"Successfully processed {len(uploaded_files)} file(s)!")
    else:
        st.warning("Please upload PDF files first.")

# Display results if DataFrame exists
if st.session_state.df is not None and not st.session_state.df.empty:
    df = st.session_state.df
    
    # Divider
    st.markdown("---")
    
    # Metric cards with enhanced styling
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown('<p class="section-header">📊 Overview</p>', unsafe_allow_html=True)
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric(
            label="📁 Files Processed",
            value=len(uploaded_files) if uploaded_files else 0,
            delta=None
        )
    
    with metric_col2:
        st.metric(
            label="📝 Line Items",
            value=len(df),
            delta=None
        )
    
    with metric_col3:
        st.metric(
            label="💰 Total Amount",
            value=f"${df['Amount'].sum():.2f}",
            delta=None
        )
    
    with metric_col4:
        avg_conf = df['Confidence'].mean()
        st.metric(
            label="✅ Avg Confidence",
            value=f"{avg_conf:.1%}",
            delta=None
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Budget Summary Section
    st.markdown("---")
    st.markdown('<p class="section-header">💰 Budget Tracking</p>', unsafe_allow_html=True)
    
    total_spent = df['Amount'].sum()
    total_budget = st.session_state.total_budget
    budget_percentage = (total_spent / total_budget * 100) if total_budget > 0 else 0
    
    # Progress bar and status
    st.markdown(f"**Total Trip Budget:** Spent ${total_spent:,.2f} of ${total_budget:,.2f} budget ({budget_percentage:.1f}%)")
    st.progress(min(total_spent / total_budget, 1.0) if total_budget > 0 else 0)
    
    # Budget status alerts
    if total_spent > total_budget:
        overspend = total_spent - total_budget
        st.error(f"⚠️ Over budget by ${overspend:,.2f}")
    elif budget_percentage >= 80:
        st.warning("⚠️ Approaching budget limit")
    else:
        st.success("✅ Within budget")
    
    # Per-category budget alerts
    st.markdown("#### Category Budget Status")
    
    category_budgets = {
        'Hotel': st.session_state.hotel_budget,
        'Flight': st.session_state.flight_budget,
        'Meal': st.session_state.meal_budget,
        'Car Rental': st.session_state.car_budget
    }
    
    for category, budget in category_budgets.items():
        category_spent = df[df['Doc Type'] == category]['Amount'].sum() if category in df['Doc Type'].values else 0
        
        if category_spent > budget and budget > 0:
            st.error(f"⚠️ {category} over budget: spent ${category_spent:,.2f} of ${budget:,.2f}")
        else:
            col_cat1, col_cat2 = st.columns([3, 1])
            with col_cat1:
                st.markdown(f"**{category}:** ${category_spent:,.2f} / ${budget:,.2f}")
                if budget > 0:
                    st.progress(min(category_spent / budget, 1.0))
            with col_cat2:
                percentage = (category_spent / budget * 100) if budget > 0 else 0
                st.markdown(f"<div style='text-align: right; padding-top: 8px;'>{percentage:.1f}%</div>", unsafe_allow_html=True)
    
    # Styled dataframe with emoji headers
    st.markdown("---")
    st.markdown('<p class="section-header">📋 Expense Details</p>', unsafe_allow_html=True)
    
    # Create display dataframe with renamed columns
    display_df = df.copy()
    
    # Ensure we have the expected columns
    expected_cols = ['Date', 'Vendor', 'Doc Type', 'Category', 'Description', 'Currency', 'Amount', 'Confidence']
    display_df = display_df[expected_cols]
    
    # Format confidence as percentage using list comprehension
    display_df['Confidence'] = [f"{x:.1%}" for x in display_df['Confidence']]
    
    # Rename with emojis
    display_df.columns = [
        "📅 Date",
        "🏢 Vendor",
        "📄 Doc Type",
        "🏷️ Category",
        "📝 Description",
        "💱 Currency",
        "💰 Amount",
        "✅ Confidence"
    ]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Analyze button logic
    if analyze_button:
        st.markdown("---")
        st.markdown('<p class="section-header">📈 Analytics Dashboard</p>', unsafe_allow_html=True)
        with st.spinner("📊 Generating interactive charts..."):
            # Pass category budgets to analyze_invoices
            category_budgets = {
                'Hotel': st.session_state.hotel_budget,
                'Flight': st.session_state.flight_budget,
                'Meal': st.session_state.meal_budget,
                'Car Rental': st.session_state.car_budget
            }
            result = analyze_invoices(df, category_budgets)
        
        # Handle both 3-figure and 4-figure return values
        if len(result) == 4:
            vendor_chart, category_chart, doc_type_chart, budget_chart = result
            
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("**💼 Spending by Vendor**")
                st.plotly_chart(vendor_chart, use_container_width=True)
            
            with chart_col2:
                st.markdown("**🏷️ Spending by Category**")
                st.plotly_chart(category_chart, use_container_width=True)
            
            chart_col3, chart_col4 = st.columns(2)
            
            with chart_col3:
                st.markdown("**📄 Spending by Document Type**")
                st.plotly_chart(doc_type_chart, use_container_width=True)
            
            with chart_col4:
                st.markdown("**💰 Budget vs. Actual**")
                st.plotly_chart(budget_chart, use_container_width=True)
        else:
            vendor_chart, category_chart, doc_type_chart = result
            
            chart_col1, chart_col2, chart_col3 = st.columns(3)
            
            with chart_col1:
                st.markdown("**💼 Spending by Vendor**")
                st.plotly_chart(vendor_chart, use_container_width=True)
            
            with chart_col2:
                st.markdown("**🏷️ Spending by Category**")
                st.plotly_chart(category_chart, use_container_width=True)
            
            with chart_col3:
                st.markdown("**📄 Spending by Document Type**")
                st.plotly_chart(doc_type_chart, use_container_width=True)
    
    # Generate Summary button logic
    if summary_button:
        with st.spinner("🤖 Generating AI-powered summary..."):
            st.session_state.summary = generate_summary(df)
    
    # Display summary if exists
    if st.session_state.summary:
        st.markdown("---")
        st.markdown('<p class="section-header">🤖 AI-Powered Insights</p>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="summary-box">
            <p style="color: #1e3a8a; font-size: 1.05rem; line-height: 1.8; margin: 0;">
                {st.session_state.summary}
            </p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>🚀 Powered by AI | Built with ❤️ using Streamlit</p>
    <p style="font-size: 0.8rem; color: #94a3b8;">© 2026 AI Travel Expense Tracker</p>
</div>
""", unsafe_allow_html=True)
