"""
AI Travel Expense Tracker - Streamlit Application
Main UI for uploading receipts, extracting expenses, and analyzing data
"""

import streamlit as st
import pandas as pd
from io import BytesIO

from doc_processing import process_invoices, analyze_invoices
from astra_helper import upload_files_to_astra
from model_gateway import invoke_llm


# Page configuration
st.set_page_config(
    page_title="AI Travel Expense Tracker",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Global background */
    .stApp {
        background-color: #F1F5F9;
    }
    
    /* Hero banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #1D4ED8 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        position: relative;
    }
    
    .hero-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        margin-bottom: 1rem;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        margin: 1rem 0;
        background: linear-gradient(90deg, #FFFFFF 0%, #60A5FA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .hero-subtitle {
        font-size: 1.125rem;
        opacity: 0.9;
        margin-bottom: 1rem;
    }
    
    .powered-by-card {
        position: absolute;
        top: 2rem;
        right: 2rem;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-size: 0.875rem;
    }
    
    /* Upload panel */
    .upload-panel {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    
    /* Type pills */
    .type-pills {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    
    .type-pill {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .pill-hotel { background: #DBEAFE; color: #1E40AF; }
    .pill-flight { background: #F3E8FF; color: #7C3AED; }
    .pill-meal { background: #D1FAE5; color: #065F46; }
    .pill-car { background: #FEF3C7; color: #92400E; }
    
    /* File uploader styling */
    .stFileUploader {
        border: 2px dashed #3B82F6 !important;
        border-radius: 12px !important;
        background: #EFF6FF !important;
        padding: 2rem !important;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* Success/Error banners */
    .success-banner {
        background: #D1FAE5;
        color: #065F46;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #10B981;
        margin: 1rem 0;
    }
    
    .warning-banner {
        background: #FEF3C7;
        color: #92400E;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #F59E0B;
        margin: 1rem 0;
    }
    
    /* Chat messages */
    .stChatMessage {
        background: white !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    
    .stChatMessage p {
        color: #1E293B !important;
    }
    
    /* Footer */
    .custom-footer {
        text-align: center;
        padding: 2rem;
        color: #64748B;
        font-size: 0.875rem;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "astra_uploaded" not in st.session_state:
    st.session_state.astra_uploaded = False


def _ask_ai(question: str, session_id: str = "default") -> str:
    """
    Answer user questions using DataFrame context or Astra DB fallback.
    """
    context = ""
    
    # Use DataFrame if available
    if st.session_state.df is not None and not st.session_state.df.empty:
        df = st.session_state.df
        
        # Pre-compute aggregations
        total_amount = df["Amount"].sum()
        by_category = df.groupby("Category")["Amount"].sum().to_dict()
        by_vendor = df.groupby("Vendor")["Amount"].sum().to_dict()
        by_type = df.groupby("Doc Type")["Amount"].sum().to_dict()
        
        context = f"""You are an AI assistant helping analyze travel expenses.

Current expense data summary:
- Total amount: ${total_amount:.2f}
- Number of line items: {len(df)}
- Expenses by category: {by_category}
- Expenses by vendor: {by_vendor}
- Expenses by document type: {by_type}

User question: {question}

Provide a helpful, concise answer based on the data above."""
    else:
        # Fallback to generic response
        context = f"""You are an AI assistant for a travel expense tracker.

User question: {question}

Provide a helpful response. Note that no expense data has been uploaded yet."""
    
    # Call LLM
    response = invoke_llm(context)
    return response


# Hero Banner
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">✈️ AI-Powered · IBM watsonx.ai</div>
    <div class="powered-by-card">
        <strong>Powered by</strong><br>
        Docling & Granite 3
    </div>
    <h1 class="hero-title">AI Travel Expense Tracker</h1>
    <p class="hero-subtitle">
        Automatically extract and analyze expenses from your travel receipts<br>
        Supports: Hotels · Flights · Meals · Car Rentals
    </p>
</div>
""", unsafe_allow_html=True)


# Upload Panel
st.markdown('<div class="upload-panel">', unsafe_allow_html=True)

st.markdown("""
<div class="type-pills">
    <span class="type-pill pill-hotel">🏨 Hotel</span>
    <span class="type-pill pill-flight">✈️ Flight</span>
    <span class="type-pill pill-meal">🍽️ Meal</span>
    <span class="type-pill pill-car">🚗 Car Rental</span>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload your receipts (PDF format)",
    type=["pdf"],
    accept_multiple_files=True,
    help="You can upload up to 10 PDF files at once"
)

if uploaded_files:
    st.markdown(f"""
    <div class="success-banner">
        ✅ <strong>{len(uploaded_files)} file(s) uploaded successfully</strong>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# Action Buttons
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    submit_btn = st.button("⚡ Submit", type="primary", use_container_width=True)

with col2:
    analyze_btn = st.button("📊 Analyze", type="secondary", use_container_width=True)

with col3:
    if st.session_state.df is not None:
        csv = st.session_state.df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Export CSV",
            data=csv,
            file_name="expenses.csv",
            mime="text/csv",
            use_container_width=True
        )


# Process uploaded files
if submit_btn and uploaded_files:
    with st.spinner("🔄 Processing receipts with AI..."):
        try:
            # Process invoices
            df = process_invoices(uploaded_files)
            st.session_state.df = df
            
            # Upload to Astra DB
            try:
                # Reset file pointers
                for f in uploaded_files:
                    f.seek(0)
                
                chunks_uploaded = upload_files_to_astra(uploaded_files)
                st.session_state.astra_uploaded = True
                
                st.markdown(f"""
                <div class="success-banner">
                    ✅ <strong>Successfully uploaded {chunks_uploaded} text chunks to Astra DB</strong>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class="warning-banner">
                    ⚠️ <strong>Astra DB upload failed:</strong> {str(e)}
                </div>
                """, unsafe_allow_html=True)
            
            st.success("✅ Processing complete!")
            
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")


# Results Panel
if st.session_state.df is not None and not st.session_state.df.empty:
    df = st.session_state.df
    
    st.markdown("---")
    st.subheader("📊 Extraction Results")
    
    # Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 Files Processed", len(uploaded_files) if uploaded_files else 0)
    
    with col2:
        st.metric("📝 Line Items", len(df))
    
    with col3:
        # Calculate total with explicit conversion
        total_amount = float(df["Amount"].astype(float).sum())
        st.metric("💰 Total Amount", f"${total_amount:,.2f}")
    
    with col4:
        avg_confidence = df["Confidence"].mean()
        st.metric("🎯 Avg Confidence", f"{avg_confidence:.1%}")
    
    # Data Table
    st.markdown("### 📋 Detailed Breakdown")
    
    # Add emoji icons to column names
    display_df = df.copy()
    display_df.columns = [
        "📅 Date", "🏢 Vendor", "📄 Doc Type", "🏷️ Category",
        "📝 Description", "💱 Currency", "💵 Amount", "🎯 Confidence"
    ]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400
    )


# Analysis Panel
if analyze_btn and st.session_state.df is not None and not st.session_state.df.empty:
    st.markdown("---")
    st.subheader("📈 Expense Analysis")
    
    with st.spinner("Generating charts..."):
        fig_vendor, fig_category, fig_doctype = analyze_invoices(st.session_state.df)
        
        # Top row: Vendor and Category charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(fig_vendor, use_container_width=True)
        
        with col2:
            st.plotly_chart(fig_category, use_container_width=True)
        
        # Bottom row: Document Type chart (full width)
        st.plotly_chart(fig_doctype, use_container_width=True)


# AI Assistant Chat Panel
st.markdown("---")
st.subheader("💬 AI Assistant")
st.markdown("Ask questions about your expenses")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about your expenses..."):
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = _ask_ai(prompt)
            st.markdown(response)
    
    # Add assistant response to history
    st.session_state.chat_history.append({"role": "assistant", "content": response})


# Footer
st.markdown("""
<div class="custom-footer">
    <p>
        Built with ❤️ using <strong>IBM watsonx.ai</strong> · <strong>Docling</strong> · <strong>Streamlit</strong><br>
        © 2024 AI Travel Expense Tracker. All rights reserved.
    </p>
</div>
""", unsafe_allow_html=True)

# Made with Bob
