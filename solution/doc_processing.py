import os
import re
import json
import tempfile
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

import pandas as pd
import plotly.graph_objects as go
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from model_gateway import invoke_llm


_file_cache: dict[str, list[dict[str, Any]]] = {}
_DOC_CONVERTER: Optional[DocumentConverter] = None


def _get_document_converter() -> DocumentConverter:
    """Create and cache a high-fidelity Docling converter."""
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


def _detect_doc_type(filename: str, text: str) -> str:
    """Detect document type from filename and text using weighted scoring."""
    filename_lower = filename.lower()
    text_lower = text.lower()

    keyword_groups = {
        "hotel": [
            "hotel", "inn", "folio", "marriott", "hilton", "hyatt", "sheraton",
            "westin", "fairmont", "resort", "lodge", "accommodation", "room rate",
            "check-in", "check-out", "guest number", "room charge", "city tax"
        ],
        "flight": [
            "flight", "airline", "boarding", "airways", "airfare", "itinerary",
            "departure", "arrival", "seat", "gate", "delta", "base fare",
            "transportation tax", "security fee", "passenger facility charge"
        ],
        "meal": [
            "meal", "restaurant", "food", "dining", "cafe", "bistro", "menu",
            "cuisine", "eatery", "tavern", "gratuity", "subtotal", "guest check"
        ],
        "car": [
            "car", "rental", "vehicle", "hertz", "avis", "enterprise", "budget rent",
            "national car", "mileage", "odometer", "daily rate", "rental agreement"
        ],
    }

    scores = {
        "hotel": 0,
        "flight": 0,
        "meal": 0,
        "car": 0,
    }

    for doc_type, keywords in keyword_groups.items():
        score = 0
        for keyword in keywords:
            if keyword in filename_lower:
                score += 3
            if keyword in text_lower:
                score += 1
        scores[doc_type] = score

    best_type = "generic"
    best_score = 0
    for doc_type, score in scores.items():
        if score > best_score:
            best_type = doc_type
            best_score = score

    if best_score == 0:
        return "generic"

    return best_type


def _get_extraction_prompt(doc_type: str, markdown_text: str) -> str:
    """Generate an extraction prompt for the given document type."""
    shared_rules = """
Return ONLY a valid JSON array.
No markdown.
No code fences.
No explanation.
No preamble.

Each row must contain these exact fields:
- date (YYYY-MM-DD or empty string if unknown)
- vendor
- doc_type
- category
- description
- currency
- amount (numeric)
- confidence (0.0-1.0)
""".strip()

    if doc_type == "hotel":
        return f"""Extract every individual charge line item from this hotel folio. Each charge must be a separate JSON object.
Do not merge multiple charges into one row.
IMPORTANT: Extract ALL charges including:
- Room charges
- Food & Beverage charges
- Taxes (as separate line items with category "Taxes & Fees")
- Service charges and fees
- All other individual charges
Do NOT extract: credits, payments, refunds, balance lines, grand total lines that duplicate other amounts.
Categories: Room, Food & Beverage, Parking, Spa & Wellness, Taxes & Fees, Telephone, Laundry, Minibar, Service Charge, Miscellaneous

{shared_rules}

Receipt text:
{markdown_text}

["""

    if doc_type == "flight":
        return f"""Extract every individual flight-related charge from this receipt.
IMPORTANT: Extract ALL charges including:
- Base airfare
- Baggage fees
- Seat upgrades
- Taxes and fees (as separate line items with category "Taxes & Fees")
- Security fees, facility charges, etc.
- All other individual charges
Do NOT extract: grand total lines, payment method lines, balance lines that duplicate other amounts.

Categories: Airfare, Baggage Fee, Seat Upgrade, Travel Insurance, Change Fee, Taxes & Fees, Security Fee, Facility Charge, Miscellaneous

{shared_rules}

Receipt text:
{markdown_text}

["""

    if doc_type == "meal":
        return f"""Extract each individual menu item or charge as a separate line item. Do not merge multiple items into one row.
IMPORTANT: Extract ALL charges including:
- Individual food and drink items
- Tax (as a separate line item with category "Taxes & Fees")
- Gratuity/Tip (as a separate line item with category "Gratuity")
- Service charges (as separate line items)
Do NOT extract: subtotal lines, balance lines, payment method lines, or grand total lines that duplicate other amounts.
If the invoice shows only a final total with no itemization, extract it as one row.
Categories: Breakfast, Lunch, Dinner, Coffee & Snacks, Alcohol, Taxes & Fees, Gratuity, Service Charge, Miscellaneous

{shared_rules}

Receipt text:
{markdown_text}

["""

    if doc_type == "car":
        return f"""Extract every individual car-rental-related charge from this receipt.
IMPORTANT: Extract ALL charges including:
- Base rental charges
- Fuel charges
- Insurance fees
- Taxes and fees (as separate line items with category "Taxes & Fees")
- Toll charges, GPS, equipment rentals
- All other individual charges
Do NOT extract: grand total lines, payment method lines, balance lines that duplicate other amounts.

Categories: Base Rental, Fuel, Insurance, Toll Charges, GPS & Equipment, Taxes & Fees, Service Charge, Miscellaneous

{shared_rules}

Receipt text:
{markdown_text}

["""

    return f"""Extract ALL line items. For each row, detect doc_type from the content - must be one of: Hotel, Flight, Meal, Car Rental.
Use all categories from all 4 types combined.

{shared_rules}

Receipt text:
{markdown_text}

["""


def _parse_amount(amount_str: Any) -> float:
    """Parse amount string handling currency symbols and localized number formats."""
    amount_text = str(amount_str).strip()
    amount_text = re.sub(r"[$€£¥₹]", "", amount_text)
    amount_text = amount_text.replace(" ", "")

    if "," in amount_text and "." in amount_text:
        if amount_text.rfind(",") > amount_text.rfind("."):
            amount_text = amount_text.replace(".", "").replace(",", ".")
        else:
            amount_text = amount_text.replace(",", "")
    elif "," in amount_text:
        parts = amount_text.split(",")
        if len(parts) == 2 and len(parts[1]) == 2:
            amount_text = amount_text.replace(",", ".")
        else:
            amount_text = amount_text.replace(",", "")

    try:
        return abs(float(amount_text))
    except ValueError:
        return 0.0


def _extract_top_level_objects(text: str) -> list[str]:
    """Extract top-level {...} JSON objects from text using brace counting."""
    objects = []
    depth = 0
    start = -1
    for i, char in enumerate(text):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start != -1:
                objects.append(text[start:i + 1])
                start = -1
    return objects


def _parse_json_from_llm(llm_output: str) -> list[dict[str, Any]]:
    """Extract a JSON array from LLM output, with multiple fallback strategies."""
    # The prompt ends with "[" to prime JSON output — prepend it back
    cleaned_output = "[" + llm_output.replace("```json", "").replace("```", "").strip()

    def _rows_from_data(data: Any) -> list[dict[str, Any]]:
        items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        rows: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if "amount" in item:
                item["amount"] = _parse_amount(item["amount"])
            rows.append(item)
        return rows

    # Strategy 1: find a [...] array (handles nested objects via re.DOTALL)
    for array_match in re.finditer(r"\[", cleaned_output):
        start = array_match.start()
        depth = 0
        for i in range(start, len(cleaned_output)):
            if cleaned_output[i] == '[':
                depth += 1
            elif cleaned_output[i] == ']':
                depth -= 1
                if depth == 0:
                    candidate = cleaned_output[start:i + 1]
                    try:
                        data = json.loads(candidate)
                        rows = _rows_from_data(data)
                        if rows:
                            return rows
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
                    break

    # Strategy 2: extract all top-level {...} objects using brace counting
    obj_strings = _extract_top_level_objects(cleaned_output)
    if obj_strings:
        rows: list[dict[str, Any]] = []
        for obj_str in obj_strings:
            try:
                item = json.loads(obj_str)
                if isinstance(item, dict) and "amount" in item:
                    item["amount"] = _parse_amount(item["amount"])
                    rows.append(item)
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        if rows:
            return rows

    # Strategy 3: try parsing the whole output as JSON
    try:
        return _rows_from_data(json.loads(cleaned_output))
    except (json.JSONDecodeError, ValueError, TypeError):
        return []


def _extract_vendor_from_text(text: str) -> str:
    """Extract vendor name from the first 10 lines of document text."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    top_lines = lines[:10]

    for line in top_lines:
        if re.search(r"(?i)(invoice|folio|date|page|guest number|charges|credits|description)", line):
            continue
        if re.search(r"[A-Za-z]", line) and len(line) >= 3:
            return line

    for line in top_lines:
        words = re.findall(r"[A-Z][A-Za-z&.'-]*", line)
        if words:
            return " ".join(words)

    return "Unknown"


def _normalize_expenses(rows: list[dict[str, Any]], filename: str, text: str) -> list[dict[str, Any]]:
    """Normalize extracted rows and backfill missing fields."""
    normalized_rows: list[dict[str, Any]] = []
    detected_type = _detect_doc_type(filename, text)
    vendor_from_text = _extract_vendor_from_text(text)

    detected_type_map = {
        "hotel": "Hotel",
        "flight": "Flight",
        "meal": "Meal",
        "car": "Car Rental",
        "generic": "",
    }

    for row in rows:
        if not isinstance(row, dict):
            continue

        normalized_row: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, str):
                normalized_row[key] = value.strip()
            else:
                normalized_row[key] = value

        for required_key in ["date", "vendor", "doc_type", "category", "description", "currency", "amount", "confidence"]:
            if required_key not in normalized_row:
                if required_key in ["date", "vendor", "doc_type", "category", "description", "currency"]:
                    normalized_row[required_key] = ""
                elif required_key == "amount":
                    normalized_row[required_key] = 0.0
                elif required_key == "confidence":
                    normalized_row[required_key] = 0.0

        vendor = str(normalized_row.get("vendor", "")).strip()
        if not vendor or vendor.lower() == "unknown":
            normalized_row["vendor"] = vendor_from_text

        # Use filename/text-based detected_type as the authoritative source.
        # Do NOT rely on the LLM's returned doc_type field — it is unreliable across models.
        normalized_row["doc_type"] = detected_type_map.get(detected_type, "")

        normalized_row["amount"] = _parse_amount(normalized_row.get("amount", 0.0))

        try:
            normalized_row["confidence"] = float(normalized_row.get("confidence", 0.0))
        except (ValueError, TypeError):
            normalized_row["confidence"] = 0.0

        normalized_rows.append(normalized_row)

    return normalized_rows


def clear_cache() -> None:
    """Clear the file processing cache to force re-extraction."""
    global _file_cache
    _file_cache = {}


def _process_single_file(file) -> tuple[list[dict[str, Any]], str]:
    """Process a single uploaded PDF and return (extracted expense rows, debug info)."""
    filename = file.name
    pdf_bytes = file.getvalue()

    file_hash = hashlib.md5(pdf_bytes).hexdigest()
    cache_key = f"{filename}_{file_hash}"

    if cache_key in _file_cache:
        return _file_cache[cache_key], "cached"

    markdown_text = _pdf_to_markdown(pdf_bytes)
    md_len = len(markdown_text.strip())

    detected_type = _detect_doc_type(filename, markdown_text)
    prompt = _get_extraction_prompt(detected_type, markdown_text)
    llm_output = invoke_llm(prompt)
    rows = _parse_json_from_llm(llm_output)
    normalized_rows = _normalize_expenses(rows, filename, markdown_text)

    llm_preview = repr(llm_output.strip()[:300])
    debug = (
        f"detected_type={detected_type}, "
        f"markdown_len={md_len}, "
        f"llm_output_len={len(llm_output.strip())}, "
        f"rows_extracted={len(rows)}, "
        f"rows_normalized={len(normalized_rows)}, "
        f"llm_preview={llm_preview}"
    )
    print(f"[DEBUG] {filename}: {debug}")

    _file_cache[cache_key] = normalized_rows
    return normalized_rows, debug


def process_invoices(uploaded_files, max_workers: int = 2, progress_callback=None) -> tuple[pd.DataFrame, dict[str, str]]:
    """Process uploaded PDF receipts and return (DataFrame, debug_info dict)."""
    all_rows: list[dict[str, Any]] = []
    debug_info: dict[str, str] = {}
    total_files = len(uploaded_files)
    completed_files = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(_process_single_file, file): file for file in uploaded_files
        }

        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                rows, debug = future.result()
                all_rows.extend(rows)
                debug_info[file.name] = debug
            except Exception as exc:
                error_msg = f"ERROR: {exc}"
                print(f"Error processing {file.name}: {exc}")
                debug_info[file.name] = error_msg
            finally:
                completed_files += 1
                if progress_callback is not None:
                    progress_callback(completed_files, total_files, file.name)

    columns = pd.Index([
        "Date",
        "Vendor",
        "Doc Type",
        "Category",
        "Description",
        "Currency",
        "Amount",
        "Confidence",
    ])

    if not all_rows:
        return pd.DataFrame(columns=columns), debug_info

    df = pd.DataFrame(all_rows)
    df = df.rename(
        columns={
            "date": "Date",
            "vendor": "Vendor",
            "doc_type": "Doc Type",
            "category": "Category",
            "description": "Description",
            "currency": "Currency",
            "amount": "Amount",
            "confidence": "Confidence",
        }
    )

    for column in columns:
        if column not in df.columns:
            if column in ["Amount", "Confidence"]:
                df[column] = 0.0
            else:
                df[column] = ""

    ordered_columns = list(columns)
    final_df = df.loc[:, ordered_columns].copy()
    return final_df, debug_info


def analyze_invoices(df: pd.DataFrame, budgets: dict | None = None) -> tuple:
    """Generate Plotly charts from expense data."""
    vendor_totals = df.groupby("Vendor")["Amount"].sum().to_dict()
    vendor_items = sorted(vendor_totals.items(), key=lambda item: item[1])
    vendor_labels = [item[0] for item in vendor_items]
    vendor_values = [item[1] for item in vendor_items]

    bar_layout = {
        "font": {"family": "Inter"},
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "xaxis": {"title": "Amount"},
        "yaxis": {"title": "Vendor"},
    }

    pie_layout = {
        "font": {"family": "Inter"},
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
    }

    vendor_chart = go.Figure(
        data=[
            go.Bar(
                x=vendor_values,
                y=vendor_labels,
                orientation="h",
                marker_color="#3B82F6",
            )
        ]
    )
    vendor_chart.update_layout(title="Total Expenses by Vendor", height=400, **bar_layout)

    category_totals = df.groupby("Category")["Amount"].sum()
    category_chart = go.Figure(
        data=[
            go.Pie(
                labels=category_totals.index,
                values=category_totals.values,
                hole=0.4,
            )
        ]
    )
    category_chart.update_layout(title="Expenses by Category", height=400, **pie_layout)

    doc_type_totals = df.groupby("Doc Type")["Amount"].sum()
    color_map = {
        "Hotel": "#3B82F6",
        "Flight": "#A855F7",
        "Meal": "#10B981",
        "Car Rental": "#F59E0B",
    }
    doc_type_colors = [color_map.get(str(doc_type), "#3B82F6") for doc_type in doc_type_totals.index]

    doc_type_chart = go.Figure(
        data=[
            go.Bar(
                x=doc_type_totals.index,
                y=doc_type_totals.values,
                marker_color=doc_type_colors,
            )
        ]
    )
    doc_type_chart.update_layout(
        title="Expenses by Document Type",
        height=400,
        **{
            "font": {"family": "Inter"},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"title": "Document Type"},
            "yaxis": {"title": "Amount"},
        },
    )

    # Budget vs Actual chart
    categories = ["Hotel", "Flight", "Meal", "Car Rental"]
    default_budgets = {"Hotel": 0, "Flight": 0, "Meal": 0, "Car Rental": 0}
    budget_values = budgets if budgets else default_budgets

    actual_values = []
    budget_bar_values = []
    for cat in categories:
        actual = df[df["Doc Type"] == cat]["Amount"].sum() if cat in df["Doc Type"].values else 0.0
        actual_values.append(actual)
        budget_bar_values.append(budget_values.get(cat, 0))

    budget_chart = go.Figure(data=[
        go.Bar(
            name="Actual",
            x=categories,
            y=actual_values,
            marker_color=["#3B82F6", "#A855F7", "#10B981", "#F59E0B"],
        ),
        go.Bar(
            name="Budget",
            x=categories,
            y=budget_bar_values,
            marker_color="rgba(0,0,0,0.15)",
            marker_line_color=["#3B82F6", "#A855F7", "#10B981", "#F59E0B"],
            marker_line_width=2,
        )
    ])
    budget_chart.update_layout(
        title="Budget vs Actual by Category",
        barmode="overlay",
        height=400,
        font={"family": "Inter"},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis={"title": "Category"},
        yaxis={"title": "Amount"},
        legend={"orientation": "h", "y": 1.1},
    )

    return vendor_chart, category_chart, doc_type_chart, budget_chart

# Made with Bob
