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
    
    # Hotel keywords take highest priority
    if any(keyword in filename_lower for keyword in hotel_keywords):
        return "hotel"
    elif any(keyword in filename_lower for keyword in flight_keywords):
        return "flight"
    elif any(keyword in filename_lower for keyword in meal_keywords):
        return "meal"
    elif any(keyword in filename_lower for keyword in car_keywords):
        return "car"
    else:
        return "generic"


def _pdf_to_markdown(pdf_bytes: bytes) -> str:
    """Convert PDF bytes to Markdown using Docling."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_path = tmp_file.name
    
    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        result = converter.convert(tmp_path)
        markdown_text = result.document.export_to_markdown()
        return markdown_text
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _get_extraction_prompt(doc_type: str, markdown_text: str) -> str:
    """Generate extraction prompt based on document type."""
    
    if doc_type == "hotel":
        return f"""Extract expense information from this hotel receipt.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

Each object must have these fields:
- date: transaction date (YYYY-MM-DD format)
- vendor: hotel name
- doc_type: "Hotel"
- category: one of "Room", "Food & Beverage", "Parking", "Spa & Wellness", "Taxes & Fees", "Telephone", "Laundry", "Minibar", "Miscellaneous"
- description: item description
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
- doc_type: "Flight"
- category: one of "Airfare", "Baggage Fee", "Seat Upgrade", "Travel Insurance", "Change Fee", "Miscellaneous"
- description: flight details
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
- doc_type: "Meal"
- category: one of "Breakfast", "Lunch", "Dinner", "Coffee & Snacks", "Alcohol", "Miscellaneous"
- description: meal details
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number
- confidence: confidence score 0.0-1.0

Receipt text:
{markdown_text}

Return only the JSON array:"""

    elif doc_type == "car":
        return f"""Extract expense information from this car rental receipt.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

Each object must have these fields:
- date: rental date (YYYY-MM-DD format)
- vendor: rental company name
- doc_type: "Car Rental"
- category: one of "Base Rental", "Fuel", "Insurance", "Toll Charges", "GPS & Equipment", "Taxes & Fees", "Miscellaneous"
- description: rental details
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number
- confidence: confidence score 0.0-1.0

Receipt text:
{markdown_text}

Return only the JSON array:"""

    else:  # generic
        return f"""Extract ALL line items from this mixed travel invoice.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

For each line item, detect the doc_type from the content itself. It must be one of: "Hotel", "Flight", "Meal", "Car Rental".

Each object must have these fields:
- date: transaction date (YYYY-MM-DD format)
- vendor: vendor name
- doc_type: one of "Hotel", "Flight", "Meal", "Car Rental" (detect from content)
- category: appropriate category based on doc_type:
  * Hotel: "Room", "Food & Beverage", "Parking", "Spa & Wellness", "Taxes & Fees", "Telephone", "Laundry", "Minibar", "Miscellaneous"
  * Flight: "Airfare", "Baggage Fee", "Seat Upgrade", "Travel Insurance", "Change Fee", "Miscellaneous"
  * Meal: "Breakfast", "Lunch", "Dinner", "Coffee & Snacks", "Alcohol", "Miscellaneous"
  * Car Rental: "Base Rental", "Fuel", "Insurance", "Toll Charges", "GPS & Equipment", "Taxes & Fees", "Miscellaneous"
- description: item description
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number
- confidence: confidence score 0.0-1.0

Receipt text:
{markdown_text}

Return only the JSON array:"""


def _parse_amount(amount_str: str) -> float:
    """Parse amount string handling various formats."""
    # Remove currency symbols
    amount_str = re.sub(r'[$€£¥₹]', '', str(amount_str))
    
    # Handle European format (1.234,56)
    if ',' in amount_str and '.' in amount_str:
        if amount_str.rindex(',') > amount_str.rindex('.'):
            # European format
            amount_str = amount_str.replace('.', '').replace(',', '.')
        else:
            # US format
            amount_str = amount_str.replace(',', '')
    elif ',' in amount_str:
        # Could be European decimal or US thousands separator
        if amount_str.count(',') == 1 and len(amount_str.split(',')[1]) == 2:
            # European decimal
            amount_str = amount_str.replace(',', '.')
        else:
            # US thousands separator
            amount_str = amount_str.replace(',', '')
    
    try:
        return abs(float(amount_str))
    except ValueError:
        return 0.0


def _parse_json_from_llm(llm_output: str) -> list:
    """Extract JSON array from LLM output using regex."""
    match = re.search(r'\[.*\]', llm_output, re.DOTALL)
    if not match:
        return []
    
    try:
        json_str = match.group(0)
        data = json.loads(json_str)
        
        # Apply abs() to amounts and parse them
        for item in data:
            if 'amount' in item:
                item['amount'] = _parse_amount(item['amount'])
        
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
        
        doc_type = _detect_doc_type(filename)
        markdown_text = _pdf_to_markdown(pdf_bytes)
        prompt = _get_extraction_prompt(doc_type, markdown_text)
        llm_output = invoke_llm(prompt)
        expenses = _parse_json_from_llm(llm_output)
        all_expenses.extend(expenses)
    
    if not all_expenses:
        return pd.DataFrame(columns=['Date', 'Vendor', 'Doc Type', 'Category', 
                                    'Description', 'Currency', 'Amount', 'Confidence'])
    
    df = pd.DataFrame(all_expenses)
    
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


def analyze_invoices(df: pd.DataFrame, category_budgets: dict = None) -> tuple:
    """
    Generate Plotly visualizations from expense data.
    
    Args:
        df: DataFrame with expense data
        category_budgets: Optional dict with budget amounts for each category
        
    Returns:
        Tuple of (vendor_chart, category_chart, doc_type_chart) or
        (vendor_chart, category_chart, doc_type_chart, budget_chart) if category_budgets provided
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
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter')
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
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter')
    )
    
    # 3. Bar chart by doc type with specific colors
    doc_type_totals = df.groupby('Doc Type')['Amount'].sum()
    
    color_map = {
        'hotel': '#3B82F6',
        'flight': '#A855F7',
        'meal': '#10B981',
        'car rental': '#F59E0B'
    }
    
    colors = [color_map.get(str(doc_type).lower(), '#3B82F6') for doc_type in doc_type_totals.index]
    
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
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter')
    )
    
    # If category_budgets provided, create budget vs actual chart
    if category_budgets is not None:
        categories = ['Hotel', 'Flight', 'Meal', 'Car Rental']
        budgeted = []
        actual = []
        colors_actual = []
        
        for category in categories:
            budget = category_budgets.get(category, 0)
            spent = df[df['Doc Type'] == category]['Amount'].sum() if category in df['Doc Type'].values else 0
            
            budgeted.append(budget)
            actual.append(spent)
            
            # Color actual bars: red if over budget, blue if under
            if spent > budget and budget > 0:
                colors_actual.append('#EF4444')
            else:
                colors_actual.append('#3B82F6')
        
        budget_chart = go.Figure(data=[
            go.Bar(
                name='Budgeted',
                x=categories,
                y=budgeted,
                marker_color='#94A3B8'
            ),
            go.Bar(
                name='Actual',
                x=categories,
                y=actual,
                marker_color=colors_actual
            )
        ])
        
        budget_chart.update_layout(
            title='Budget vs. Actual by Category',
            xaxis_title='Category',
            yaxis_title='Amount',
            height=400,
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter')
        )
        
        return vendor_chart, category_chart, doc_type_chart, budget_chart
    
    return vendor_chart, category_chart, doc_type_chart

# Made with Bob
