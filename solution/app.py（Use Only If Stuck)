import streamlit as st
import pandas as pd
from doc_processing import process_invoices, analyze_invoices, clear_cache
from model_gateway import invoke_llm


# Page configuration
st.set_page_config(
    page_title="IBM Travel Expense Tracker",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced custom CSS styling with IBM Carbon Design System
custom_css = """
<style>
/* Hide Streamlit branding */
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

/* Global font and background improvements - IBM Plex Sans */
.stApp {
    background: #f4f4f4;
    font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif;
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
    background: linear-gradient(135deg, #0F62FE 0%, #0043CE 50%, #002D9C 100%);
    padding: 3rem;
    border-radius: 0;
    margin-bottom: 2rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    animation: fadeInDown 0.8s ease-out;
    border-left: 4px solid #0F62FE;
}

.hero-banner h1 {
    color: white;
    margin: 0;
    font-size: 2.5rem;
    font-weight: 600;
    letter-spacing: 0;
}

.hero-banner p {
    color: #ffffff;
    margin: 0.75rem 0 0 0;
    font-size: 1.125rem;
    font-weight: 400;
    opacity: 0.9;
}

/* File uploader styling */
.stFileUploader {
    background: white;
    padding: 2rem;
    border-radius: 0;
    border: 1px solid #0F62FE;
    box-shadow: none;
    transition: all 0.11s cubic-bezier(0.2, 0, 0.38, 0.9);
}

.stFileUploader:hover {
    border-color: #0043CE;
    box-shadow: 0 0 0 1px #0F62FE, 0 0 0 3px rgba(15, 98, 254, 0.1);
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
    border-radius: 0;
    box-shadow: none;
    border-left: 3px solid #0F62FE;
    border-top: 1px solid #e0e0e0;
    border-right: 1px solid #e0e0e0;
    border-bottom: 1px solid #e0e0e0;
    transition: all 0.11s cubic-bezier(0.2, 0, 0.38, 0.9);
}

div[data-testid="metric-container"]:hover {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

/* Dataframe styling */
.stDataFrame {
    border-radius: 0;
    overflow: hidden;
    box-shadow: none;
    border: 1px solid #e0e0e0;
}

/* Section headers */
.section-header {
    color: #161616;
    font-size: 1.75rem;
    font-weight: 600;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #0F62FE;
    letter-spacing: 0;
}

/* Info box styling */
.stAlert {
    border-radius: 0;
    border-left: 3px solid #0F62FE;
    box-shadow: none;
    border: 1px solid #e0e0e0;
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
    border-color: #0F62FE !important;
}

/* Chart containers */
.js-plotly-plot {
    border-radius: 0;
    background: white;
    padding: 1rem;
    box-shadow: none;
    border: 1px solid #e0e0e0;
}

/* Summary box */
.summary-box {
    background: #f4f4f4;
    padding: 2rem;
    border-radius: 0;
    border-left: 3px solid #0F62FE;
    border: 1px solid #e0e0e0;
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
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = {}
if 'processed_hashes' not in st.session_state:
    st.session_state.processed_hashes = set()

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
    total_budget = st.session_state.total_budget
    budget_remaining = total_budget - total_amount
    
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
    
    # Find biggest spending category
    top_category = ""
    top_category_amount = -1.0
    for category_name, category_amount in category_breakdown.items():
        if category_amount > top_category_amount:
            top_category = category_name
            top_category_amount = category_amount

    # Build prompt using fill-in template
    budget_status = (
        f"You are ${abs(budget_remaining):.2f} over budget."
        if budget_remaining < 0
        else f"You have ${budget_remaining:.2f} left in your budget."
    )

    prompt = f"""Complete this travel expense summary by filling in the blanks. Output only the 3 completed sentences, nothing else.

Sentence 1: "You spent $[TOTAL] on this trip, mostly on [TOP_CATEGORY]."
Sentence 2: "[BUDGET_STATUS]"
Sentence 3: "Consider [ONE_SIMPLE_TIP] to manage future travel costs."

Fill in using these values:
- [TOTAL] = {total_amount:.2f}
- [TOP_CATEGORY] = {top_category}
- [BUDGET_STATUS] = {budget_status}
- [ONE_SIMPLE_TIP] = one short practical tip based on the top spending category

Output only the 3 sentences. No explanation. No revision. No "However". No analysis."""

    # Call LLM and strip any meta-commentary
    raw = invoke_llm(prompt).strip()

    # Remove lines that contain meta-commentary patterns
    lines = raw.splitlines()
    clean_lines = [
        line for line in lines
        if line.strip()
        and not line.strip().startswith("However")
        and not line.strip().startswith("Note")
        and not line.strip().startswith("Here")
        and not line.strip().startswith("The above")
        and not line.strip().startswith("To make")
        and "can be combined" not in line
        and "sentences long" not in line
    ]
    summary = " ".join(clean_lines[:3]).strip()
    return summary

def get_expense_context(df: pd.DataFrame) -> str:
    """Generate context string about expenses for chat."""
    total_amount = df['Amount'].sum()
    num_items = len(df)
    
    # Breakdown by category
    category_breakdown = df.groupby('Category')['Amount'].sum().to_dict()
    category_str = "\n".join([f"  - {cat}: ${amt:.2f}" for cat, amt in category_breakdown.items()])
    
    # Breakdown by doc type
    doc_type_breakdown = df.groupby('Doc Type')['Amount'].sum().to_dict()
    doc_type_str = "\n".join([f"  - {doc}: ${amt:.2f}" for doc, amt in doc_type_breakdown.items()])
    
    # Breakdown by vendor
    vendor_breakdown_map = df.groupby('Vendor')['Amount'].sum().to_dict()
    top_vendors = sorted(vendor_breakdown_map.items(), key=lambda item: item[1], reverse=True)[:5]
    vendor_str = "\n".join([f"  - {vendor}: ${amt:.2f}" for vendor, amt in top_vendors])
    
    # Date range
    try:
        df['Date_parsed'] = pd.to_datetime(df['Date'])
        date_range = f"{df['Date_parsed'].min().strftime('%Y-%m-%d')} to {df['Date_parsed'].max().strftime('%Y-%m-%d')}"
        num_days = (df['Date_parsed'].max() - df['Date_parsed'].min()).days + 1
        avg_daily_spend = total_amount / num_days if num_days > 0 else 0
        date_info = f"Date range: {date_range}\nAverage daily spend: ${avg_daily_spend:.2f}"
    except:
        date_info = "Date information not available"
    
    context = f"""Current Expense Data:
Total expenses: ${total_amount:.2f}
Number of line items: {num_items}

Spending by Category:
{category_str}

Spending by Document Type:
{doc_type_str}

Top 5 Vendors:
{vendor_str}

{date_info}"""
    
    return context


def chat_with_expenses(user_question: str, df: pd.DataFrame) -> str:
    """Answer questions about expenses using LLM."""
    context = get_expense_context(df)
    
    prompt = f"""You are a helpful AI assistant analyzing travel expenses. Answer the user's question based only on the expense data provided.

{context}

User Question: {user_question}

Response rules:
- Give the direct answer first in the first sentence.
- If a numeric answer is available, state the exact number immediately.
- Keep the full response to 1-3 short sentences.
- Do not repeat the same number in multiple ways.
- Do not hedge unnecessarily.
- Do not add long caveats unless the data is actually missing or ambiguous.
- If the question asks for a total in an existing category, provide that total directly.
- If the exact answer is not available, say that clearly in one sentence and give the closest available figure.
- Do not use phrases like "based on the provided data", "however", "nonetheless", "to summarize", or "the final answer is".

Return only the answer text."""
    
    response = invoke_llm(prompt).strip()
    return response


# Hero banner with IBM branding
st.markdown("""
<div class="hero-banner">
    <h1>💼 IBM Travel Expense Tracker</h1>
    <p>Enterprise-grade expense management powered by IBM Watson AI</p>
</div>
""", unsafe_allow_html=True)

# Instructions section
with st.container():
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 0; margin-bottom: 1.5rem; border: 1px solid #e0e0e0; border-left: 3px solid #0F62FE;">
        <h3 style="color: #161616; margin-top: 0; font-weight: 600;">📝 How it works</h3>
        <ol style="color: #525252; line-height: 1.8; font-size: 0.95rem;">
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
col1, col2, col3, col4, col5 = st.columns(5)

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

with col5:
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.df = None
        st.session_state.summary = None
        st.session_state.debug_info = {}
        st.session_state.processed_hashes = set()
        st.session_state.chat_history = []
        st.rerun()

# Submit button logic
if submit_button:
    if uploaded_files:
        import hashlib as _hashlib

        # Filter out already-processed files
        new_files = []
        skipped = []
        for f in uploaded_files:
            file_hash = _hashlib.md5(f.getvalue()).hexdigest()
            if file_hash in st.session_state.processed_hashes:
                skipped.append(f.name)
            else:
                new_files.append((f, file_hash))

        if skipped:
            st.info(f"⏭️ Skipped (already processed): {', '.join(skipped)}")

        if not new_files:
            st.warning("⚠️ All uploaded files have already been processed.")
        else:
            files_to_process = [f for f, _ in new_files]
            progress_bar = st.progress(0)
            status_text = st.empty()
            file_status = st.empty()
            total_files = len(files_to_process)

            def update_progress(completed, total, filename):
                progress = int((completed / total) * 100)
                progress_bar.progress(progress)
                status_text.text(f"Processing: {completed}/{total} files completed")
                file_status.text(f"✅ Completed: {filename}")

            status_text.text(f"Processing {total_files} new file(s)...")

            try:
                new_df, new_debug = process_invoices(
                    files_to_process,
                    max_workers=2,
                    progress_callback=update_progress
                )

                # Append new results to existing data
                if st.session_state.df is not None and not st.session_state.df.empty:
                    import pandas as pd
                    st.session_state.df = pd.concat(
                        [st.session_state.df, new_df], ignore_index=True
                    )
                else:
                    st.session_state.df = new_df

                # Only mark a file as processed if it produced at least 1 row
                # (so failed files due to 429 or 0-row extraction can be retried on next submit)
                successfully_processed = set()
                for f, file_hash in new_files:
                    if not new_debug.get(f.name, "").startswith("ERROR"):
                        successfully_processed.add(file_hash)

                st.session_state.processed_hashes.update(successfully_processed)
                failed_files = [f.name for f, fh in new_files if fh not in successfully_processed]

                st.session_state.debug_info.update(new_debug)
                st.session_state.summary = None

                progress_bar.progress(100)
                status_text.text("✨ Processing complete!")
                file_status.empty()

                import time
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()

                total_so_far = len(st.session_state.processed_hashes)
                st.success(f"🎉 Added {total_files} file(s). Total files processed: {total_so_far}")
                if failed_files:
                    st.warning(f"⚠️ These files failed (will retry on next Submit): {', '.join(failed_files)}")
                if st.session_state.debug_info:
                    with st.expander("🔍 Debug Info (click to expand)"):
                        for fname, info in st.session_state.debug_info.items():
                            st.text(f"{fname}: {info}")
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                file_status.empty()
                st.error(f"❌ Error processing files: {str(e)}")
    else:
        st.warning("⚠️ Please upload PDF files first.")

# Display results if DataFrame exists
if st.session_state.df is not None and not st.session_state.df.empty:
    df = st.session_state.df
    
    # Divider
    st.markdown("---")
    
    # Metric cards with enhanced styling
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown('<p class="section-header">📊 Overview</p>', unsafe_allow_html=True)
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        st.metric(
            label="📁 Files Processed",
            value=len(st.session_state.processed_hashes),
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
    expected_cols = ['Date', 'Vendor', 'Doc Type', 'Category', 'Description', 'Currency', 'Amount']
    display_df = display_df[expected_cols]
    
    # Rename with emojis
    display_df.columns = [
        "📅 Date",
        "🏢 Vendor",
        "📄 Doc Type",
        "🏷️ Category",
        "📝 Description",
        "💱 Currency",
        "💰 Amount"
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
            result = analyze_invoices(df, budgets={
                "Hotel": st.session_state.hotel_budget,
                "Flight": st.session_state.flight_budget,
                "Meal": st.session_state.meal_budget,
                "Car Rental": st.session_state.car_budget,
            })
        
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
        st.markdown('<p class="section-header">🤖 Watson AI Insights</p>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="summary-box">
            <p style="color: #161616; font-size: 1rem; line-height: 1.75; margin: 0; font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif;">
                {st.session_state.summary}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # AI Chat Assistant Section
    st.markdown("---")
    st.markdown('<p class="section-header">💬 Chat with AI Assistant</p>', unsafe_allow_html=True)
    st.markdown("Ask questions about your expenses and get instant insights!")
    
    # Display chat history
    for i, (question, answer) in enumerate(st.session_state.chat_history):
        with st.container():
            st.markdown(f"""
            <div style="background: #e8f4ff; padding: 1rem; border-radius: 0; margin-bottom: 0.5rem; font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif; border-left: 3px solid #0F62FE;">
                <strong style="color: #0F62FE;">You:</strong> {question}
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 0; margin-bottom: 1rem; border-left: 3px solid #0F62FE; font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif; line-height: 1.75; border: 1px solid #e0e0e0;">
                <strong style="color: #0F62FE;">IBM Watson:</strong> {answer}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_button = st.columns([4, 1])
        with col_input:
            user_question = st.text_input(
                "Ask a question",
                placeholder="e.g., What was my biggest expense? How much did I spend on hotels?",
                label_visibility="collapsed"
            )
        with col_button:
            ask_button = st.form_submit_button("Ask", use_container_width=True)
    
    if ask_button and user_question:
        with st.spinner("🤔 Thinking..."):
            answer = chat_with_expenses(user_question, df)
            st.session_state.chat_history.append((user_question, answer))
            st.rerun()
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <p style="color: #0F62FE; font-weight: 600; font-family: 'IBM Plex Sans', sans-serif;">💼 IBM Travel Expense Tracker</p>
    <p style="font-size: 0.875rem; color: #525252;">Powered by IBM Watson AI | © 2026 International Business Machines Corporation</p>
    <p style="font-size: 0.75rem; color: #8d8d8d;">IBM, the IBM logo, and Watson are trademarks of IBM Corp.</p>
</div>
""", unsafe_allow_html=True)
