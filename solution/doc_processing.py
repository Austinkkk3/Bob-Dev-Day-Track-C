import os
import re
import json
import tempfile
import hashlib
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Mapping, Optional
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from model_gateway import invoke_llm

# Cache for processed files (in-memory cache)
_file_cache: dict[str, list[dict[str, Any]]] = {}


def _detect_doc_type(filename: str, text: str = "") -> str:
    """Detect document type from filename and extracted text using weighted signals."""
    combined_text = f"{filename}\n{text}".lower()

    keyword_groups = {
        "hotel": [
            "hotel", "inn", "marriott", "hilton", "hyatt", "sheraton", "westin",
            "fairmont", "resort", "lodge", "accommodation", "folio", "room chg",
            "guest number", "invoice nbr", "check out", "check-out", "city tax",
            "state tax", "room charge", "occupancy tax"
        ],
        "flight": [
            "flight", "airline", "boarding", "airways", "delta", "united", "american airlines",
            "southwest", "jetblue", "air canada", "base fare", "seat selection", "baggage fee",
            "passenger facility charge", "transportation tax", "security fee", "trip fare"
        ],
        "meal": [
            "meal", "restaurant", "food", "dining", "cafe", "bistro", "gratuity",
            "tip", "subtotal", "server", "breakfast", "lunch", "dinner", "brunch",
            "table", "guest check", "check #", "order #", "menu", "burger", "pizza",
            "salad", "sandwich", "coffee", "tea", "soda", "beer", "wine", "service charge"
        ],
        "car": [
            "car rental", "rental car", "vehicle rental", "hertz", "avis", "enterprise",
            "national", "alamo", "budget", "pickup", "dropoff", "drop-off",
            "daily rate", "rental agreement", "vehicle class"
        ],
    }

    scores = {doc_type: 0 for doc_type in keyword_groups}
    for doc_type, keywords in keyword_groups.items():
        scores[doc_type] = sum(1 for keyword in keywords if keyword in combined_text)

    strongest_doc_type = "generic"
    strongest_score = 0
    for doc_type, score in scores.items():
        if score > strongest_score:
            strongest_doc_type = doc_type
            strongest_score = score

    if strongest_score > 0:
        return strongest_doc_type

    return "generic"


_DOC_CONVERTER: Optional[DocumentConverter] = None


def _get_document_converter() -> DocumentConverter:
    """Create and cache the Docling converter for reuse across files."""
    global _DOC_CONVERTER

    if _DOC_CONVERTER is None:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True

        _DOC_CONVERTER = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    return _DOC_CONVERTER


def _pdf_to_markdown(pdf_bytes: bytes) -> str:
    """Convert PDF bytes to Markdown using Docling."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_path = tmp_file.name
    
    try:
        converter = _get_document_converter()
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
- vendor: hotel name taken from the receipt header, brand, or merchant name; never use "Unknown" if a business name appears anywhere in the text
- doc_type: "Hotel"
- category: one of "Room", "Food & Beverage", "Parking", "Spa & Wellness", "Taxes & Fees", "Telephone", "Laundry", "Minibar", "Miscellaneous"
- description: item description
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number

Receipt text:
{markdown_text}

Return only the JSON array:"""

    elif doc_type == "flight":
        return f"""Extract expense information from this flight receipt.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

Extract every charge line that belongs to the trip, including airfare, taxes, seat fees, baggage, insurance, and other airline-related items.
If the receipt is from a travel agency or booking platform, still classify flight-related charges as doc_type "Flight".
Do not return an empty array unless there are truly no flight-related charges in the receipt.

Each object must have these fields:
- date: flight date (YYYY-MM-DD format)
- vendor: airline name, carrier, or booking agency name shown on the receipt; never use "Unknown" if a carrier or business name appears anywhere in the text
- doc_type: "Flight"
- category: one of "Airfare", "Baggage Fee", "Seat Upgrade", "Travel Insurance", "Change Fee", "Taxes & Fees", "Miscellaneous"
- description: flight details
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number

Receipt text:
{markdown_text}

Return only the JSON array:"""

    elif doc_type == "meal":
        return f"""Extract expense information from this meal receipt.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.
Do not return an empty array unless there are truly no meal-related charges in the receipt.

Extract individual menu items as separate expense objects whenever the receipt shows each food or drink item with its own price.
Do not combine all dishes into one description if line-item prices are available.
Use the actual dish or drink name in the description field for each separate item.
If the receipt is itemized, prefer returning multiple rows over summarizing the whole meal in one row.
You may return additional separate rows for tax, tip, service charge, or other meal-related charges when they appear as distinct lines.

Each object must have these fields:
- date: meal date (YYYY-MM-DD format)
- vendor: restaurant name taken from the receipt header, merchant name, or store branding; never use "Unknown" if a business name appears anywhere in the text
- doc_type: "Meal"
- category: one of "Breakfast", "Lunch", "Dinner", "Coffee & Snacks", "Alcohol", "Miscellaneous"
- description: exact item-level description such as the dish name, drink name, tax line, or tip line; do not merge multiple dishes into one description
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number

Receipt text:
{markdown_text}

Return only the JSON array:"""

    elif doc_type == "car":
        return f"""Extract expense information from this car rental receipt.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

Extract every charge line that belongs to the rental, including base rental, taxes, fuel, tolls, insurance, equipment, and other car-rental-related fees.
Do not return an empty array unless there are truly no car-rental-related charges in the receipt.

Each object must have these fields:
- date: rental date (YYYY-MM-DD format)
- vendor: rental company name taken from the receipt header, merchant name, or brand; never use "Unknown" if a business name appears anywhere in the text
- doc_type: "Car Rental"
- category: one of "Base Rental", "Fuel", "Insurance", "Toll Charges", "GPS & Equipment", "Taxes & Fees", "Miscellaneous"
- description: rental details
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number

Receipt text:
{markdown_text}

Return only the JSON array:"""

    else:  # generic
        return f"""Extract ALL line items from this mixed travel invoice.

Return ONLY a JSON array with no markdown formatting, no code blocks, and no explanation.

For each line item, detect the doc_type from the content itself. It must be one of: "Hotel", "Flight", "Meal", "Car Rental".

Each object must have these fields:
- date: transaction date (YYYY-MM-DD format)
- vendor: vendor name from the receipt header, merchant, carrier, or hotel/restaurant/rental brand; never use "Unknown" if any business name appears anywhere in the text
- doc_type: one of "Hotel", "Flight", "Meal", "Car Rental" (detect from content)
- category: appropriate category based on doc_type:
  * Hotel: "Room", "Food & Beverage", "Parking", "Spa & Wellness", "Taxes & Fees", "Telephone", "Laundry", "Minibar", "Miscellaneous"
  * Flight: "Airfare", "Baggage Fee", "Seat Upgrade", "Travel Insurance", "Change Fee", "Miscellaneous"
  * Meal: "Breakfast", "Lunch", "Dinner", "Coffee & Snacks", "Alcohol", "Miscellaneous"
  * Car Rental: "Base Rental", "Fuel", "Insurance", "Toll Charges", "GPS & Equipment", "Taxes & Fees", "Miscellaneous"
- description: item description
- currency: currency code (e.g., USD, CAD)
- amount: total amount as positive number

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


def _parse_json_from_llm(llm_output: str) -> list[dict[str, Any]]:
    """Extract JSON array from LLM output using regex."""
    match = re.search(r'\[.*\]', llm_output, re.DOTALL)
    if not match:
        return []
    
    try:
        json_str = match.group(0)
        data = json.loads(json_str)
        if not isinstance(data, list):
            return []
        
        normalized_data: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue

            if 'amount' in item:
                item['amount'] = _parse_amount(item['amount'])

            normalized_data.append(item)
        
        return normalized_data
    except (json.JSONDecodeError, ValueError):
        return []


def _extract_vendor_from_text(markdown_text: str) -> str:
    """Extract vendor name directly from structured receipt text."""
    vendor_patterns = [
        r'(?im)^(westin[^\n]*)$',
        r'(?im)^(marriott[^\n]*)$',
        r'(?im)^(hilton[^\n]*)$',
        r'(?im)^(hyatt[^\n]*)$',
        r'(?im)^([A-Z][A-Za-z&.\' -]{2,}(?:hotel|resort|inn|suites|airlines|air lines|rental|cafe|bistro)[^\n]*)$',
    ]

    for pattern in vendor_patterns:
        match = re.search(pattern, markdown_text)
        if match:
            return match.group(1).strip()

    for line in markdown_text.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
        if re.search(r'(?i)(invoice|folio|guest number|page number|date|description|charges|credits)', clean_line):
            continue
        if re.search(r'(?i)(westin|marriott|hilton|hyatt|sheraton|fairmont|delta|united|american airlines|southwest|enterprise|hertz|avis)', clean_line):
            return clean_line

    return ""


def _normalize_expenses(expenses: list[dict[str, Any]], filename: str, markdown_text: str) -> list[dict[str, Any]]:
    """Clean extracted expenses and replace weak vendor values with receipt-derived fallbacks."""
    normalized_expenses = []
    text_vendor = _extract_vendor_from_text(markdown_text)
    fallback_vendor = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").strip()

    for item in expenses:
        if not isinstance(item, dict):
            continue

        vendor = str(item.get("vendor", "")).strip()
        if not vendor or vendor.lower() == "unknown":
            item["vendor"] = text_vendor or fallback_vendor or "Unspecified Vendor"

        normalized_expenses.append(item)

    return normalized_expenses


def _process_single_file(file) -> list[dict[str, Any]]:
    """
    Process a single PDF file and return extracted expenses.
    Uses caching to avoid reprocessing identical files.
    
    Args:
        file: Uploaded file object with 'name' and 'getvalue()' method
        
    Returns:
        List of expense dictionaries
    """
    filename = file.name
    pdf_bytes = file.getvalue()
    
    # Generate cache key from file content hash
    file_hash = hashlib.md5(pdf_bytes).hexdigest()
    cache_key = f"{filename}_{file_hash}"
    
    # Check cache first
    if cache_key in _file_cache:
        return _file_cache[cache_key]
    
    # Process file if not in cache
    markdown_text = _pdf_to_markdown(pdf_bytes)
    doc_type = _detect_doc_type(filename, markdown_text)
    prompt = _get_extraction_prompt(doc_type, markdown_text)
    llm_output = invoke_llm(prompt)
    expenses = _normalize_expenses(_parse_json_from_llm(llm_output), filename, markdown_text)
    
    # Store in cache
    _file_cache[cache_key] = expenses
    
    return expenses


def process_invoices(uploaded_files, max_workers: int = 3, progress_callback=None) -> pd.DataFrame:
    """
    Process uploaded PDF receipts and extract expense data in parallel.
    
    Args:
        uploaded_files: List of uploaded file objects with 'name' and 'getvalue()' method
        max_workers: Maximum number of parallel workers (default: 3)
        progress_callback: Optional callback function(completed, total, filename) for progress updates
        
    Returns:
        DataFrame with columns: Date, Vendor, Doc Type, Category, Description, Currency, Amount
    """
    all_expenses: list[dict[str, Any]] = []
    total_files = len(uploaded_files)
    completed_files = 0
    
    # Accuracy-first processing: use fewer workers to reduce OCR/model contention
    max_workers = min(max_workers, 2)
    
    # Process files in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all files for processing
        future_to_file = {executor.submit(_process_single_file, file): file for file in uploaded_files}
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                expenses = future.result()
                all_expenses.extend(expenses)
                completed_files += 1
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(completed_files, total_files, file.name)
                    
            except Exception as e:
                completed_files += 1
                print(f"Error processing {file.name}: {str(e)}")
                
                # Still update progress even on error
                if progress_callback:
                    progress_callback(completed_files, total_files, f"{file.name} (error)")
    
    if not all_expenses:
        empty_columns = pd.Index(['Date', 'Vendor', 'Doc Type', 'Category',
                                  'Description', 'Currency', 'Amount'])
        return pd.DataFrame(columns=empty_columns)
    
    df = pd.DataFrame(all_expenses)
    
    column_mapping = {
        'date': 'Date',
        'vendor': 'Vendor',
        'doc_type': 'Doc Type',
        'category': 'Category',
        'description': 'Description',
        'currency': 'Currency',
        'amount': 'Amount'
    }
    df = df.rename(columns=column_mapping)
    
    return df


def analyze_invoices(df: pd.DataFrame, category_budgets: Optional[Mapping[str, int | float]] = None) -> tuple:
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
    vendor_totals_map = df.groupby('Vendor')['Amount'].sum().to_dict()
    vendor_totals_items = sorted(vendor_totals_map.items(), key=lambda item: item[1])
    vendor_labels = [item[0] for item in vendor_totals_items]
    vendor_values = [item[1] for item in vendor_totals_items]
    
    vendor_chart = go.Figure(data=[
        go.Bar(
            x=vendor_values,
            y=vendor_labels,
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
