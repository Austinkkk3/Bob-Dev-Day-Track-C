# AI Travel Expense Tracker - Production Build Guide (Simplified)

**Complete guide for building a production-ready expense tracker with no database or chat interface.**

This guide assumes no prior context. Follow every step to build a working application from scratch.

---

## What This Application Does

✅ Upload up to 10 PDF receipts (hotels, flights, meals, car rentals)  
✅ Auto-detect document type from filename  
✅ Extract structured expense data using IBM watsonx.ai Granite 3 LLM  
✅ Display results in a table with 8 columns  
✅ Show 4 metric cards (Files Processed, Line Items, Total Amount, Avg Confidence)  
✅ Generate 3 interactive Plotly charts (by vendor, by category, by document type)  
✅ Export data to CSV  

❌ No database (no Astra DB)  
❌ No AI chat assistant  

---

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows
- **Python Version**: 3.10, 3.11, 3.12, or 3.13 (recommended)
  - Python 3.14 requires special setup (see below)
- **Internet Connection**: Required for first run (downloads ~2GB of ML models)
- **Disk Space**: At least 5GB free

### Python 3.14 Users - CRITICAL SETUP

If you're using Python 3.14, you **MUST** follow this exact sequence:

```bash
# 1. Install uv package manager
pip install uv

# 2. Install pillow with binary-only flag BEFORE anything else
uv pip install pillow==11.3.0 --only-binary :all:

# 3. Then install other dependencies
uv pip install -r requirements.txt
```

**Why?** Python 3.14 has binary compatibility issues that prevent standard package installation. Installing pillow first with `--only-binary :all:` resolves this blocking issue.

### Required Accounts

1. **IBM Cloud Account** (free tier available)
   - For watsonx.ai API access
   - Sign up at: https://cloud.ibm.com/

---

## Get Your Credentials

Before writing any code, you need two pieces of information from IBM Cloud.

### Step 1: Get IBM Cloud API Key

1. Go to https://cloud.ibm.com/ and sign in
2. Click your account avatar (top right corner)
3. Select **Manage** → **Access (IAM)**
4. In the left sidebar, click **API keys**
5. Click **Create** button
6. Give it a name (e.g., "watsonx-expense-tracker")
7. Click **Create**
8. **IMPORTANT**: Copy the API key immediately — it's shown only once
9. Save it securely (you'll paste it into `.env` later)

### Step 2: Get watsonx.ai Project ID

1. From IBM Cloud dashboard, go to **Resource List**
2. Under **AI / Machine Learning**, find your watsonx.ai instance
3. Click on it, then click **Launch IBM watsonx**
4. On the watsonx home screen, find the **Developer Access** section
5. Select your project from the dropdown
6. Copy the **Project ID** (it's a 36-character UUID like `12345678-1234-1234-1234-123456789abc`)
7. Save it securely

### Step 3: Note Your Region

Your `CLOUD_URL` depends on your IBM Cloud region:
- **US South**: `https://us-south.ml.cloud.ibm.com`
- **Canada (Toronto)**: `https://ca-tor.ml.cloud.ibm.com`
- **Europe (Frankfurt)**: `https://eu-de.ml.cloud.ibm.com`

Check your region in the IBM Cloud dashboard (top right, next to your account name).

---

## Project Structure

You will create these files:

```
ai-travel-expense-tracker/
├── app.py                 # Streamlit UI (280 lines)
├── doc_processing.py      # PDF parsing + LLM extraction + charts (360 lines)
├── model_gateway.py       # watsonx.ai REST API layer (95 lines)
├── requirements.txt       # Python dependencies (6 packages)
└── .env                   # Your credentials (4 variables)
```

---

## Step 1: Create requirements.txt

Create a file named `requirements.txt` with this exact content:

```
streamlit
pandas
plotly
docling
python-dotenv
requests
```

---

## Step 2: Create .env File

Create a file named `.env` and paste your credentials:

```env
# IBM watsonx.ai Configuration
API_KEY=paste_your_api_key_here
PROJECT_ID=paste_your_project_id_here
CLOUD_URL=https://us-south.ml.cloud.ibm.com
LLM_NAME=ibm/granite-3-8b-instruct
```

**Replace**:
- `paste_your_api_key_here` with your IBM Cloud API Key from Step 1
- `paste_your_project_id_here` with your Project ID from Step 2
- Update `CLOUD_URL` if you're not in US South region

**Security Note**: Never commit `.env` to version control. Add it to `.gitignore`.

---

## Step 3: Create model_gateway.py

Create a file named `model_gateway.py` and paste this complete code:

```python
"""
IBM watsonx.ai REST API Gateway
Handles IAM token generation and LLM invocation using REST API
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Environment variables
API_KEY = os.getenv("API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
CLOUD_URL = os.getenv("CLOUD_URL", "https://us-south.ml.cloud.ibm.com")
LLM_NAME = os.getenv("LLM_NAME", "ibm/granite-3-8b-instruct")

# Token cache
_token_cache = {
    "token": None,
    "expires_at": 0
}


def _get_iam_token() -> str:
    """
    Get IBM Cloud IAM Bearer Token using API Key.
    Caches token for 50 minutes (IBM tokens valid for 60 minutes).
    """
    current_time = time.time()
    
    # Return cached token if still valid
    if _token_cache["token"] and current_time < _token_cache["expires_at"]:
        return _token_cache["token"]
    
    # Request new token
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": API_KEY
    }
    
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    # Cache token for 50 minutes (3000 seconds)
    _token_cache["token"] = access_token
    _token_cache["expires_at"] = current_time + 3000
    
    return access_token


def invoke_llm(prompt: str) -> str:
    """
    Invoke IBM watsonx.ai LLM using REST API.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        Generated text from the LLM
    """
    token = _get_iam_token()
    
    url = f"{CLOUD_URL}/ml/v1/text/generation?version=2023-05-29"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "input": prompt,
        "parameters": {
            "max_new_tokens": 2048,
            "temperature": 0.0,
            "repetition_penalty": 1.05,
            "stop_sequences": ["```"]
        },
        "model_id": LLM_NAME,
        "project_id": PROJECT_ID
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    generated_text = data["results"][0]["generated_text"]
    
    return generated_text
```

**Key Points**:
- Uses IAM token exchange (not raw API key)
- Caches token for 50 minutes
- `stop_sequences: ["```"]` prevents markdown code blocks in LLM output
- `temperature: 0.0` for consistent extraction

---

## Step 4: Create doc_processing.py

Create a file named `doc_processing.py` and paste this complete code:

```python
"""
Document Processing Module
Handles PDF parsing, LLM extraction, and data visualization
"""

import json
import re
import tempfile
import os
from io import BytesIO
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from model_gateway import invoke_llm


def _detect_doc_type(filename: str) -> str:
    """
    Detect document type from filename keywords.
    Hotel has highest priority and is the default fallback.
    """
    filename_lower = filename.lower()
    
    # Hotel has highest priority (expanded keyword list)
    hotel_keywords = [
        "hotel", "inn", "marriott", "hilton", "hyatt", "sheraton", 
        "westin", "fairmont", "intercontinental", "resort", "lodge", 
        "motel", "accommodation"
    ]
    if any(kw in filename_lower for kw in hotel_keywords):
        return "hotel"
    elif any(kw in filename_lower for kw in ["flight", "airline", "boarding"]):
        return "flight"
    elif any(kw in filename_lower for kw in ["meal", "restaurant", "food", "dining"]):
        return "meal"
    elif any(kw in filename_lower for kw in ["car", "rental", "vehicle"]):
        return "car"
    
    # Default to hotel
    return "hotel"


def _pdf_to_markdown(pdf_bytes: bytes) -> str:
    """
    Convert PDF to Markdown using Docling.
    Disables OCR, enables table structure recognition.
    """
    # Configure pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    # Save bytes to temporary file (Docling requires file path)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_path = tmp_file.name
    
    try:
        # Convert PDF to markdown
        result = converter.convert(tmp_path)
        markdown_text = result.document.export_to_markdown()
        return markdown_text
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _get_extraction_prompt(doc_type: str, markdown_content: str) -> str:
    """
    Get the appropriate extraction prompt based on document type.
    Each prompt is self-contained with clear instructions.
    """
    if doc_type == "hotel":
        return f"""You are an expert at extracting structured data from hotel receipts.

--- BEGIN DOCUMENT ---
{markdown_content}
--- END DOCUMENT ---

Extract all expense line items from this hotel receipt. For each line item, provide:
- date: Transaction date in YYYY-MM-DD format (e.g., 2024-03-15)
- vendor: Hotel or property name (e.g., "Marriott Downtown")
- doc_type: Must be exactly "Hotel"
- category: Must be one of: Room, Food & Beverage, Parking, Spa & Wellness, Taxes & Fees, Telephone, Laundry, Minibar, Miscellaneous
- description: Brief description of the charge (e.g., "Deluxe King Room - 2 nights")
- currency: Three-letter currency code (e.g., USD, EUR, GBP)
- amount: Numeric amount as a plain float with no currency symbols (e.g., 299.99, not $299.99)
- confidence: Your confidence level as a float between 0.0 and 1.0 (e.g., 0.95)

Return ONLY a valid JSON array. No explanation. No markdown fences."""

    elif doc_type == "flight":
        return f"""You are an expert at extracting structured data from flight receipts.

--- BEGIN DOCUMENT ---
{markdown_content}
--- END DOCUMENT ---

Extract all expense line items from this flight receipt. For each line item, provide:
- date: Transaction date in YYYY-MM-DD format (e.g., 2024-03-15)
- vendor: Airline name (e.g., "United Airlines")
- doc_type: Must be exactly "Flight"
- category: Must be one of: Airfare, Baggage Fee, Seat Upgrade, Travel Insurance, Change Fee, Miscellaneous
- description: Brief description of the charge (e.g., "Economy ticket SFO-JFK")
- currency: Three-letter currency code (e.g., USD, EUR, GBP)
- amount: Numeric amount as a plain float with no currency symbols (e.g., 450.00, not $450.00)
- confidence: Your confidence level as a float between 0.0 and 1.0 (e.g., 0.95)

Return ONLY a valid JSON array. No explanation. No markdown fences."""

    elif doc_type == "meal":
        return f"""You are an expert at extracting structured data from meal receipts.

--- BEGIN DOCUMENT ---
{markdown_content}
--- END DOCUMENT ---

Extract all expense line items from this meal receipt. For each line item, provide:
- date: Transaction date in YYYY-MM-DD format (e.g., 2024-03-15)
- vendor: Restaurant or establishment name (e.g., "The Cheesecake Factory")
- doc_type: Must be exactly "Meal"
- category: Must be one of: Breakfast, Lunch, Dinner, Coffee & Snacks, Alcohol, Miscellaneous
- description: Brief description of the item (e.g., "Pasta Carbonara")
- currency: Three-letter currency code (e.g., USD, EUR, GBP)
- amount: Numeric amount as a plain float with no currency symbols (e.g., 28.50, not $28.50)
- confidence: Your confidence level as a float between 0.0 and 1.0 (e.g., 0.95)

Return ONLY a valid JSON array. No explanation. No markdown fences."""

    else:  # car
        return f"""You are an expert at extracting structured data from car rental receipts.

--- BEGIN DOCUMENT ---
{markdown_content}
--- END DOCUMENT ---

Extract all expense line items from this car rental receipt. For each line item, provide:
- date: Transaction date in YYYY-MM-DD format (e.g., 2024-03-15)
- vendor: Car rental company name (e.g., "Enterprise Rent-A-Car")
- doc_type: Must be exactly "Car Rental"
- category: Must be one of: Base Rental, Fuel, Insurance, Toll Charges, GPS & Equipment, Taxes & Fees, Miscellaneous
- description: Brief description of the charge (e.g., "Compact car - 3 days")
- currency: Three-letter currency code (e.g., USD, EUR, GBP)
- amount: Numeric amount as a plain float with no currency symbols (e.g., 180.00, not $180.00)
- confidence: Your confidence level as a float between 0.0 and 1.0 (e.g., 0.95)

Return ONLY a valid JSON array. No explanation. No markdown fences."""


def _parse_llm_json(raw_output: str) -> list:
    """
    Extract JSON array from LLM output.
    Handles cases where LLM includes extra text.
    """
    json_match = re.search(r'\[[\s\S]*\]', raw_output)
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    return []


def _parse_amount(amount_str) -> float:
    """
    Parse amount string to float.
    Handles currency symbols, commas, and European format.
    """
    if isinstance(amount_str, (int, float)):
        return float(amount_str)
    
    if not isinstance(amount_str, str):
        return 0.0
    
    # Remove currency symbols and whitespace
    amount_str = re.sub(r'[€$£¥₹\s]', '', amount_str)
    
    # Handle European format (1.234,56)
    if ',' in amount_str and '.' in amount_str:
        if amount_str.rindex(',') > amount_str.rindex('.'):
            amount_str = amount_str.replace('.', '').replace(',', '.')
        else:
            amount_str = amount_str.replace(',', '')
    elif ',' in amount_str:
        if amount_str.count(',') == 1 and len(amount_str.split(',')[1]) == 2:
            amount_str = amount_str.replace(',', '.')
        else:
            amount_str = amount_str.replace(',', '')
    
    try:
        return float(amount_str)
    except ValueError:
        return 0.0


def _normalize_row(row: dict) -> dict:
    """
    Normalize a single row of extracted data.
    Uses abs() to handle negative amounts from LLM.
    """
    return {
        "Date": row.get("date", ""),
        "Vendor": row.get("vendor", ""),
        "Doc Type": row.get("doc_type", ""),
        "Category": row.get("category", ""),
        "Description": row.get("description", ""),
        "Currency": row.get("currency", "USD"),
        "Amount": abs(_parse_amount(row.get("amount", 0))),
        "Confidence": float(row.get("confidence", 0.0))
    }


def process_invoices(uploaded_files) -> pd.DataFrame:
    """
    Process multiple uploaded PDF files and extract expense data.
    """
    all_rows = []
    
    for uploaded_file in uploaded_files:
        # Reset file pointer in case it was already read
        uploaded_file.seek(0)
        
        doc_type = _detect_doc_type(uploaded_file.name)
        pdf_bytes = uploaded_file.read()
        markdown_content = _pdf_to_markdown(pdf_bytes)
        prompt = _get_extraction_prompt(doc_type, markdown_content)
        raw_output = invoke_llm(prompt)
        extracted_data = _parse_llm_json(raw_output)
        
        for row in extracted_data:
            normalized_row = _normalize_row(row)
            all_rows.append(normalized_row)
    
    if all_rows:
        return pd.DataFrame(all_rows)
    else:
        return pd.DataFrame(columns=["Date", "Vendor", "Doc Type", "Category", "Description", "Currency", "Amount", "Confidence"])


def analyze_invoices(df: pd.DataFrame) -> tuple:
    """
    Generate three Plotly charts from the expense data.
    Uses separate layout configs for bar charts vs pie charts.
    """
    # Font configuration (shared)
    font_config = dict(family="Inter", color="#1E293B")
    
    # Layout for bar charts (includes axis configs)
    bar_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=font_config,
        xaxis=dict(gridcolor="#E2E8F0", showline=True, linecolor="#E2E8F0"),
        yaxis=dict(gridcolor="#E2E8F0", showline=True, linecolor="#E2E8F0")
    )
    
    # Layout for pie chart (NO axis configs - causes errors)
    pie_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        font=font_config
    )
    
    # 1. By Vendor - Horizontal bar chart
    vendor_data = df.groupby("Vendor")["Amount"].sum().sort_values(ascending=True)
    fig_vendor = px.bar(
        x=vendor_data.values,
        y=vendor_data.index,
        orientation='h',
        title="Expenses by Vendor",
        labels={"x": "Total Amount", "y": "Vendor"}
    )
    fig_vendor.update_layout(**bar_layout)
    fig_vendor.update_traces(marker_color="#3B82F6")
    
    # 2. By Category - Donut chart
    category_data = df.groupby("Category")["Amount"].sum()
    fig_category = go.Figure(data=[go.Pie(
        labels=category_data.index,
        values=category_data.values,
        hole=0.4
    )])
    fig_category.update_layout(
        title="Expenses by Category",
        **pie_layout
    )
    
    # 3. By Document Type - Bar chart with custom colors
    doctype_data = df.groupby("Doc Type")["Amount"].sum()
    color_map = {
        "Hotel": "#3B82F6",
        "Flight": "#A855F7",
        "Meal": "#10B981",
        "Car Rental": "#F59E0B"
    }
    colors = [color_map.get(dt, "#6B7280") for dt in doctype_data.index]
    
    fig_doctype = px.bar(
        x=doctype_data.index,
        y=doctype_data.values,
        title="Expenses by Document Type",
        labels={"x": "Document Type", "y": "Total Amount"}
    )
    fig_doctype.update_layout(**bar_layout)
    fig_doctype.update_traces(marker_color=colors)
    
    return fig_vendor, fig_category, fig_doctype
```

**Key Bug Fixes**:
- ✅ `abs()` in `_normalize_row` to handle negative amounts
- ✅ Separate `bar_layout` and `pie_layout` (pie charts don't support axis configs)
- ✅ `uploaded_file.seek(0)` before reading
- ✅ Expanded hotel keyword list (13 keywords)
- ✅ Improved extraction prompts with clear role and format instructions

---

## Step 5: Create app.py

Create a file named `app.py` and paste this complete code:

```python
"""
AI Travel Expense Tracker - Simplified Version
No Astra DB, No Chat Interface
"""

import streamlit as st
import pandas as pd

from doc_processing import process_invoices, analyze_invoices


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
    .pill-flight { background: #EDE9FE; color: #7C3AED; }
    .pill-meal { background: #D1FAE5; color: #065F46; }
    .pill-car { background: #FEF3C7; color: #92400E; }
    
    /* File uploader */
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
    
    /* Success banner */
    .success-banner {
        background: #D1FAE5;
        color: #065F46;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #10B981;
        margin: 1rem 0;
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
            df = process_invoices(uploaded_files)
            st.session_state.df = df
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
        total_amount = df["Amount"].sum()
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


# Footer
st.markdown("""
<div class="custom-footer">
    <p>
        Built with ❤️ using <strong>IBM watsonx.ai</strong> · <strong>Docling</strong> · <strong>Streamlit</strong><br>
        © 2024 AI Travel Expense Tracker. All rights reserved.
    </p>
</div>
""", unsafe_allow_html=True)
```

---

## Pre-Run Validation

Before starting the app, run these three commands to validate your setup:

### 1. Test API Key

This should return `200`:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://iam.cloud.ibm.com/identity/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_API_KEY"
```

Replace `YOUR_API_KEY` with your actual API key from `.env`.

**Expected output**: `200`  
**If you get `400` or `401`**: Your API key is invalid. Double-check it in IBM Cloud.

### 2. Test All Imports

```bash
python3 -c "import streamlit, pandas, plotly, docling, requests; print('✅ All OK')"
```

**Expected output**: `✅ All OK`  
**If you get `ModuleNotFoundError`**: Run `pip install -r requirements.txt` again.

### 3. Check Python Version

```bash
python3 --version
```

**Expected output**: `Python 3.10.x`, `3.11.x`, `3.12.x`, or `3.13.x`  
**If you see `3.14.x`**: Make sure you followed the Python 3.14 setup steps above.

---

## Install Dependencies

### For Python 3.10 - 3.13

```bash
pip install -r requirements.txt
```

### For Python 3.14

```bash
# 1. Install uv
pip install uv

# 2. Install pillow first
uv pip install pillow==11.3.0 --only-binary :all:

# 3. Install other dependencies
uv pip install -r requirements.txt
```

---

## Run the Application

### First-Run Warning

⚠️ **IMPORTANT**: The first run will download Docling ML models (~2GB). This takes 5–10 minutes depending on your internet speed. Subsequent runs are instant. **Do not interrupt the process.**

### Start the App

```bash
streamlit run app.py
```

Or if `streamlit` is not on your PATH:

```bash
python3 -m streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`.

If it doesn't open automatically, manually navigate to that URL.

---

## Usage

1. **Upload PDFs**: Click the file uploader and select up to 10 receipt PDFs
2. **Submit**: Click "⚡ Submit" to extract data (takes 10-30 seconds per file)
3. **View Results**: See table with 8 columns and 4 metric cards
4. **Analyze**: Click "📊 Analyze" to generate 3 interactive charts
5. **Export**: Click "⬇️ Export CSV" to download the extracted data

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| **Total Amount shows $0.00** | LLM returned negative amounts | Confirm `abs()` is in `_normalize_row` (line 237 of doc_processing.py) |
| **`TypeError: object.__init__()`** | Python 3.14 + wrong install order | Install pillow first with `--only-binary :all:`, then use `uv` for other packages |
| **`JSONDecodeError`** | LLM returned markdown fences | Confirm `stop_sequences: ["```"]` is in model_gateway.py (line 90) |
| **Document type wrong** | Filename doesn't match keywords | Rename file to include keyword (e.g., `hilton_invoice.pdf` for hotel) |
| **`401 Unauthorized`** | API Key not exchanged for token | Confirm model_gateway.py uses IAM token exchange (line 26-58), not raw API key |
| **Pie chart errors** | layout_config applied to pie chart | Use separate layout dicts for bar vs pie charts (lines 327-337 of doc_processing.py) |
| **`streamlit: command not found`** | Streamlit not on PATH | Use `python3 -m streamlit run app.py` instead |
| **First run takes forever** | Downloading Docling models (~2GB) | Wait 5-10 minutes. Do not interrupt. Subsequent runs are instant. |
| **`ModuleNotFoundError: docling`** | Dependencies not installed | Run `pip install -r requirements.txt` |
| **Charts don't appear** | Clicked Analyze before Submit | Click "⚡ Submit" first, then "📊 Analyze" |

---

## Advanced Configuration

### Change LLM Model

Edit `.env` and change `LLM_NAME`:

```env
LLM_NAME=ibm/granite-3-8b-instruct  # Default
# Or try:
# LLM_NAME=ibm/granite-13b-instruct-v2
# LLM_NAME=meta-llama/llama-3-70b-instruct
```

### Change Region

Edit `.env` and update `CLOUD_URL`:

```env
# US South (default)
CLOUD_URL=https://us-south.ml.cloud.ibm.com

# Canada (Toronto)
CLOUD_URL=https://ca-tor.ml.cloud.ibm.com

# Europe (Frankfurt)
CLOUD_URL=https://eu-de.ml.cloud.ibm.com
```

### Change Port

If port 8501 is busy:

```bash
streamlit run app.py --server.port 8502
```

---

## Security Best Practices

1. **Never commit `.env` to version control**
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Rotate API keys regularly**
   - Create new keys every 90 days
   - Delete old keys in IBM Cloud

3. **Use separate credentials for dev/prod**
   - Create different projects in watsonx.ai
   - Use different API keys

4. **Monitor API usage**
   - Check IBM Cloud billing dashboard
   - Set up usage alerts

---

## Performance Tips

1. **Process files in batches**
   - Upload 2-3 files at a time for faster processing
   - Large batches may timeout

2. **Use descriptive filenames**
   - Include document type in filename (e.g., `marriott_hotel_2024.pdf`)
   - Improves auto-detection accuracy

3. **Optimize PDF quality**
   - Use text-based PDFs (not scanned images)
   - Smaller files process faster

---

## What's Next?

This simplified version is perfect for:
- ✅ Quick demos
- ✅ Learning the basics
- ✅ Proof of concept
- ✅ Small-scale usage

For production use, consider adding:
- 🔄 Database storage (Astra DB, PostgreSQL)
- 🔄 User authentication
- 🔄 Batch processing
- 🔄 API endpoints
- 🔄 Automated testing
- 🔄 Logging and monitoring

---

## Support

If you encounter issues not covered in this guide:

1. Check the Troubleshooting section above
2. Verify all three Pre-Run Validation commands pass
3. Ensure your `.env` file has correct credentials
4. Try with a single, simple PDF first

---

**End of Production Build Guide**

You now have a complete, working AI Travel Expense Tracker. Happy coding! 🚀