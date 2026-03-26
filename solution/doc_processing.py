"""
Document Processing Module
Handles PDF parsing, LLM extraction, and data visualization
"""

import json
import re
from io import BytesIO
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from docling.document_converter import DocumentConverter

from model_gateway import invoke_llm


def _detect_doc_type(filename: str) -> str:
    """
    Detect document type from filename keywords.
    Hotel has highest priority to avoid misclassification.
    """
    filename_lower = filename.lower()
    
    # Hotel has highest priority
    if any(kw in filename_lower for kw in ["hotel", "accommodation", "lodging"]):
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
    import tempfile
    import os
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    
    # Configure pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    # Save bytes to temporary file
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
    """
    base_instruction = """Extract expense information from the following receipt and return ONLY a JSON array. Do not include any explanations, markdown formatting, or additional text.

Receipt content:
{content}

Return format: Pure JSON array with no markdown code blocks or explanations."""

    if doc_type == "hotel":
        prompt = base_instruction.format(content=markdown_content) + """

Required fields for each line item:
- date: Transaction date (YYYY-MM-DD format)
- vendor: Hotel/property name
- doc_type: "Hotel"
- category: One of [Room, Food & Beverage, Parking, Spa & Wellness, Taxes & Fees, Telephone, Laundry, Minibar, Miscellaneous]
- description: Brief description of the charge
- currency: Currency code (e.g., USD, EUR)
- amount: Numeric amount (no currency symbols)
- confidence: Your confidence level (0.0-1.0)

Return only the JSON array."""

    elif doc_type == "flight":
        prompt = base_instruction.format(content=markdown_content) + """

Required fields for each line item:
- date: Transaction date (YYYY-MM-DD format)
- vendor: Airline name
- doc_type: "Flight"
- category: One of [Airfare, Baggage Fee, Seat Upgrade, Travel Insurance, Change Fee, Miscellaneous]
- description: Brief description of the charge
- currency: Currency code (e.g., USD, EUR)
- amount: Numeric amount (no currency symbols)
- confidence: Your confidence level (0.0-1.0)

Return only the JSON array."""

    elif doc_type == "meal":
        prompt = base_instruction.format(content=markdown_content) + """

Required fields for each line item:
- date: Transaction date (YYYY-MM-DD format)
- vendor: Restaurant/establishment name
- doc_type: "Meal"
- category: One of [Breakfast, Lunch, Dinner, Coffee & Snacks, Alcohol, Miscellaneous]
- description: Brief description of the item
- currency: Currency code (e.g., USD, EUR)
- amount: Numeric amount (no currency symbols)
- confidence: Your confidence level (0.0-1.0)

Return only the JSON array."""

    else:  # car
        prompt = base_instruction.format(content=markdown_content) + """

Required fields for each line item:
- date: Transaction date (YYYY-MM-DD format)
- vendor: Car rental company name
- doc_type: "Car Rental"
- category: One of [Base Rental, Fuel, Insurance, Toll Charges, GPS & Equipment, Taxes & Fees, Miscellaneous]
- description: Brief description of the charge
- currency: Currency code (e.g., USD, EUR)
- amount: Numeric amount (no currency symbols)
- confidence: Your confidence level (0.0-1.0)

Return only the JSON array."""

    return prompt


def _parse_llm_json(raw_output: str) -> list:
    """
    Extract JSON array from LLM output.
    Handles cases where LLM includes markdown code blocks or extra text.
    """
    # Try to find JSON array in the output
    json_match = re.search(r'\[[\s\S]*\]', raw_output)
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # If no valid JSON found, return empty list
    return []


def _parse_amount(amount_str) -> float:
    """
    Parse amount string to float.
    Handles currency symbols, commas, and European format (1.234,56).
    """
    if isinstance(amount_str, (int, float)):
        return float(amount_str)
    
    if not isinstance(amount_str, str):
        return 0.0
    
    # Remove currency symbols and whitespace
    amount_str = re.sub(r'[€$£¥₹\s]', '', amount_str)
    
    # Check if European format (comma as decimal separator)
    if ',' in amount_str and '.' in amount_str:
        # Format like 1.234,56 (European)
        if amount_str.rindex(',') > amount_str.rindex('.'):
            amount_str = amount_str.replace('.', '').replace(',', '.')
        else:
            # Format like 1,234.56 (US)
            amount_str = amount_str.replace(',', '')
    elif ',' in amount_str:
        # Only comma - could be decimal or thousands separator
        # If only one comma and 2 digits after, it's decimal
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
    """
    return {
        "Date": row.get("date", ""),
        "Vendor": row.get("vendor", ""),
        "Doc Type": row.get("doc_type", ""),
        "Category": row.get("category", ""),
        "Description": row.get("description", ""),
        "Currency": row.get("currency", "USD"),
        "Amount": abs(_parse_amount(row.get("amount", 0))),  # Use absolute value for expenses
        "Confidence": float(row.get("confidence", 0.0))
    }


def process_invoices(uploaded_files) -> pd.DataFrame:
    """
    Process multiple uploaded PDF files and extract expense data.
    
    Args:
        uploaded_files: List of uploaded file objects from Streamlit
        
    Returns:
        DataFrame with columns: Date, Vendor, Doc Type, Category, Description, Currency, Amount, Confidence
    """
    all_rows = []
    
    for uploaded_file in uploaded_files:
        # Detect document type from filename
        doc_type = _detect_doc_type(uploaded_file.name)
        
        # Read PDF bytes
        pdf_bytes = uploaded_file.read()
        
        # Convert PDF to Markdown
        markdown_content = _pdf_to_markdown(pdf_bytes)
        
        # Get extraction prompt
        prompt = _get_extraction_prompt(doc_type, markdown_content)
        
        # Call LLM to extract data
        raw_output = invoke_llm(prompt)
        
        # Parse JSON from LLM output
        extracted_data = _parse_llm_json(raw_output)
        
        # Normalize each row
        for row in extracted_data:
            normalized_row = _normalize_row(row)
            all_rows.append(normalized_row)
    
    # Create DataFrame
    if all_rows:
        df = pd.DataFrame(all_rows)
        return df
    else:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=["Date", "Vendor", "Doc Type", "Category", "Description", "Currency", "Amount", "Confidence"])


def analyze_invoices(df: pd.DataFrame) -> tuple:
    """
    Generate three Plotly charts from the expense data.
    
    Args:
        df: DataFrame with expense data
        
    Returns:
        Tuple of (fig_vendor, fig_category, fig_doctype)
    """
    # Chart styling
    font_config = dict(family="Inter", color="#1E293B")
    layout_config = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=font_config,
        xaxis=dict(gridcolor="#E2E8F0", showline=True, linecolor="#E2E8F0"),
        yaxis=dict(gridcolor="#E2E8F0", showline=True, linecolor="#E2E8F0")
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
    fig_vendor.update_layout(**layout_config)
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
        paper_bgcolor="rgba(0,0,0,0)",
        font=font_config
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
    fig_doctype.update_layout(**layout_config)
    fig_doctype.update_traces(marker_color=colors)
    
    return fig_vendor, fig_category, fig_doctype

# Made with Bob
