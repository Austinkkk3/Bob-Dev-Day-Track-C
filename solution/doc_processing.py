import os
import re
import json
import tempfile
import pandas as pd
import plotly.graph_objects as go
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from model_gateway import invoke_llm


def _detect_doc_type(filename: str) -> str:
    """Detect document type from filename."""
    filename_lower = filename.lower()
    
    hotel_keywords = ["hotel", "inn", "marriott", "hilton", "hyatt", "sheraton", 
                      "westin", "fairmont", "resort", "lodge", "accommodation"]
    flight_keywords = ["flight", "airline", "boarding", "airways"]
    meal_keywords = ["meal", "restaurant", "food", "dining", "cafe", "bistro"]
    car_keywords = ["car", "rental", "vehicle", "hertz", "avis", "enterprise"]
    
    if any(keyword in filename_lower for keyword in flight_keywords):
        return "flight"
    elif any(keyword in filename_lower for keyword in meal_keywords):
        return "meal"
    elif any(keyword in filename_lower for keyword in car_keywords):
        return "car"
    elif any(keyword in filename_lower for keyword in hotel_keywords):
        return "hotel"
    else:
        return "hotel"


def _pdf_to_markdown(pdf_bytes: bytes) -> str:
    """Convert PDF bytes to Markdown using Docling."""
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_path = tmp_file.name
    
    try:
        # Configure pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True
        
        # Create converter with options
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Convert PDF to Markdown
        result = converter.convert(tmp_path)
        markdown_text = result.document.export_to_markdown()
        return markdown_text
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _get_extraction_prompt(doc_type: str, markdown_text: str) -> str:
    """Generate extraction prompt based on document type."""
    
    if doc_type == "hotel":
        return f"""Extract expense information from this hotel receipt.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

Each object must have these fields:
- date: check-in or transaction date (YYYY-MM-DD format)
- vendor: hotel name
- doc_type: "hotel"
- category: "Accommodation"
- description: room type and nights stayed
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number
- confidence: confidence score 0.0-1.0

Receipt text:
{markdown_text}

Return only the JSON array:"""

    elif doc_type == "flight":
        return f"""Extract expense information from this flight receipt.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

Each object must have these fields:
- date: flight date (YYYY-MM-DD format)
- vendor: airline name
- doc_type: "flight"
- category: "Transportation"
- description: flight route and class
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number
- confidence: confidence score 0.0-1.0

Receipt text:
{markdown_text}

Return only the JSON array:"""

    elif doc_type == "meal":
        return f"""Extract expense information from this meal receipt.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

Each object must have these fields:
- date: meal date (YYYY-MM-DD format)
- vendor: restaurant name
- doc_type: "meal"
- category: "Meals"
- description: meal type or items
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number
- confidence: confidence score 0.0-1.0

Receipt text:
{markdown_text}

Return only the JSON array:"""

    else:  # car
        return f"""Extract expense information from this car rental receipt.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

Each object must have these fields:
- date: rental start date (YYYY-MM-DD format)
- vendor: rental company name
- doc_type: "car"
- category: "Transportation"
- description: vehicle type and rental period
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number
- confidence: confidence score 0.0-1.0

Receipt text:
{markdown_text}

Return only the JSON array:"""


def _parse_json_from_llm(llm_output: str) -> list:
    """Extract JSON array from LLM output using regex."""
    # Find JSON array pattern
    match = re.search(r'\[.*\]', llm_output, re.DOTALL)
    if not match:
        return []
    
    try:
        json_str = match.group(0)
        data = json.loads(json_str)
        
        # Apply abs() to amounts
        for item in data:
            if 'amount' in item:
                item['amount'] = abs(float(item['amount']))
        
        return data
    except (json.JSONDecodeError, ValueError):
        return []


def process_invoices(uploaded_files) -> pd.DataFrame:
    """
    Process uploaded PDF receipts and extract expense data.
    
    Args:
        uploaded_files: List of uploaded file objects with 'name' and 'getvalue()' method
        
    Returns:
        DataFrame with columns: Date, Vendor, Doc Type, Category, Description, Currency, Amount, Confidence
    """
    all_expenses = []
    
    for file in uploaded_files:
        filename = file.name
        pdf_bytes = file.getvalue()
        
        # Detect document type
        doc_type = _detect_doc_type(filename)
        
        # Convert PDF to Markdown
        markdown_text = _pdf_to_markdown(pdf_bytes)
        
        # Generate extraction prompt
        prompt = _get_extraction_prompt(doc_type, markdown_text)
        
        # Call LLM
        llm_output = invoke_llm(prompt)
        
        # Parse JSON
        expenses = _parse_json_from_llm(llm_output)
        all_expenses.extend(expenses)
    
    # Create DataFrame
    if not all_expenses:
        return pd.DataFrame(columns=['Date', 'Vendor', 'Doc Type', 'Category', 
                                    'Description', 'Currency', 'Amount', 'Confidence'])
    
    df = pd.DataFrame(all_expenses)
    
    # Rename columns to match output format
    column_mapping = {
        'date': 'Date',
        'vendor': 'Vendor',
        'doc_type': 'Doc Type',
        'category': 'Category',
        'description': 'Description',
        'currency': 'Currency',
        'amount': 'Amount',
        'confidence': 'Confidence'
    }
    df = df.rename(columns=column_mapping)
    
    return df


def analyze_invoices(df: pd.DataFrame) -> tuple:
    """
    Generate three Plotly visualizations from expense data.
    
    Args:
        df: DataFrame with expense data
        
    Returns:
        Tuple of (vendor_chart, category_chart, doc_type_chart)
    """
    # 1. Horizontal bar chart by vendor
    vendor_totals = df.groupby('Vendor')['Amount'].sum().sort_values()
    
    vendor_chart = go.Figure(data=[
        go.Bar(
            x=vendor_totals.values,
            y=vendor_totals.index,
            orientation='h',
            marker_color='#3B82F6'
        )
    ])
    
    vendor_chart.update_layout(
        title='Total Expenses by Vendor',
        xaxis_title='Amount',
        yaxis_title='Vendor',
        height=400,
        showlegend=False
    )
    
    # 2. Donut chart by category
    category_totals = df.groupby('Category')['Amount'].sum()
    
    category_chart = go.Figure(data=[
        go.Pie(
            labels=category_totals.index,
            values=category_totals.values,
            hole=0.4
        )
    ])
    
    category_chart.update_layout(
        title='Expenses by Category',
        height=400
    )
    
    # 3. Bar chart by doc type with specific colors
    doc_type_totals = df.groupby('Doc Type')['Amount'].sum()
    
    color_map = {
        'hotel': '#3B82F6',
        'flight': '#A855F7',
        'meal': '#10B981',
        'car': '#F59E0B'
    }
    
    colors = [color_map.get(doc_type.lower(), '#3B82F6') for doc_type in doc_type_totals.index]
    
    doc_type_chart = go.Figure(data=[
        go.Bar(
            x=doc_type_totals.index,
            y=doc_type_totals.values,
            marker_color=colors
        )
    ])
    
    doc_type_chart.update_layout(
        title='Expenses by Document Type',
        xaxis_title='Document Type',
        yaxis_title='Amount',
        height=400,
        showlegend=False
    )
    
    return vendor_chart, category_chart, doc_type_chart

# Made with Bob
