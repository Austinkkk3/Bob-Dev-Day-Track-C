# AI Travel Expense Tracker — Build Guide

Complete guide for building an AI-powered expense tracker using IBM Bob and watsonx.ai.

This guide assumes no prior context. Follow every step to build a working application from scratch.

---

## What This Application Does

✅ Upload up to 10 PDF receipts (hotels, flights, meals, car rentals)  
✅ Auto-detect document type from filename  
✅ Extract structured expense data using IBM watsonx.ai Granite 3 LLM  
✅ Display results in a table with 8 columns  
✅ Show 4 metric cards (Files Processed, Line Items, Total Amount, Avg Confidence)  
✅ Generate 4 interactive Plotly charts (by vendor, by category, by document type)  
✅ Export data to CSV  
✅ Generate an AI-written plain-English summary of your trip expenses  


---

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows
- **Python Version**: 3.10, 3.11, 3.12, or 3.13 (recommended)
  - Python 3.14 requires special setup (see below)
- **Internet Connection**: Required for first run (downloads ~2GB of ML models)
- **Disk Space**: At least 5GB free

### Installing Python

If you don't have Python installed, follow these steps:

**Mac:**
1. Go to [python.org/downloads](https://python.org/downloads)
2. Click **Download Python 3.13.x** (the big yellow button)
3. Open the downloaded `.pkg` file and follow the installer
4. When done, open Terminal and run `python3 --version` to confirm

**Windows:**
1. Go to [python.org/downloads](https://python.org/downloads)
2. Click **Download Python 3.13.x**
3. Open the `.exe` file
4. ⚠️ **Check "Add Python to PATH"** before clicking Install — this is critical
5. Click **Install Now**
6. When done, open Command Prompt and run `python --version` to confirm

> 💡 If you see a version number like `Python 3.13.x`, you're good to go.
> If you see an error, restart your computer and try again.

### Python 3.14 Users — CRITICAL SETUP （Ignore if your are not using 3.14)

If you're using Python 3.14, you **MUST** follow this exact sequence:


```bash
# 1. Install uv package manager
pip install uv

# 2. Install pillow with binary-only flag BEFORE anything else
uv pip install pillow==11.3.0 --only-binary :all:

# 3. Then install other dependencies
uv pip install -r requirements.txt
```
---
```
> 💡 pip comes bundled with Python 3.13. If `pip3 --version` gives an error,
> run `python3 -m ensurepip` to install it.
```
### Installing IBM Bob

1. Search for IBM Bob online
2. Download the IBM Bob installer for your operating system
3. Open the installer and follow the prompts
4. Launch Bob — you should see the Bob IDE with the chat panel on the right


### Required Accounts

- **IBM Cloud Account** (free tier available) — sign up at [cloud.ibm.com](https://cloud.ibm.com)

---

## Get Your Credentials

Before writing any code, you need three pieces of information from IBM Cloud.

### Step 1: Get IBM Cloud API Key

1. Go to [cloud.ibm.com](https://cloud.ibm.com) and sign in
2. Click on the highlighted icon with the arrow. If you expand the display with the hamburger menu
icon on the top-left, you will see this is the Resource list  
 <img width="1498" alt="Screenshot 2026-04-06 at 4 13 32 PM" src="https://github.ibm.com/user-attachments/assets/bbd382c4-e7ea-471b-a918-43b73d394a5a" />
3. Click on the down arrow beside AI/Machine Learning. The window will expand to show multiple
resources. Click the resource name with the product watsonx.ai Runtime.
<img width="1151" alt="runtime" src="https://github.ibm.com/user-attachments/assets/d377fc86-6668-45ef-91f8-24d618af412b" />

4. Launch in IBM WatsonX
 <img width="1498" alt="ss3" src="https://github.ibm.com/user-attachments/assets/3617cf3d-b558-4947-91ce-3398a0fdb815" />
8. Find the **Developer Access** section
 <img width="1498" alt="ss4" src="https://github.ibm.com/user-attachments/assets/a9bacadc-f506-4ef3-b4e7-3fdb485e1c41" />

9. Give it a name (e.g., `watsonx-expense-tracker`)
10. ⚠️ **Copy the API key immediately** — it's shown only once
11. Save it securely (you'll paste it into `.env` later)

 



### Step 2: Get watsonx.ai Project ID

1. At the same page of where you find the API Key
2. Select your project from the dropdown
3. Copy the **Project ID** (36-character UUID like `12345678-1234-1234-1234-123456789abc`)
4. Save it securely
5. If you want to go back IBM CLoud Dashboard, simply click the logo in the top left corner

### Step 3: Note Your Region

Your `CLOUD_URL` depends on your IBM Cloud region:

| Region | URL |
|--------|-----|
| US South (Dallas) | `https://us-south.ml.cloud.ibm.com` |
| Canada (Toronto) | `https://ca-tor.ml.cloud.ibm.com` |
| Europe (Frankfurt) | `https://eu-de.ml.cloud.ibm.com` |
| UK (London) | `https://eu-gb.ml.cloud.ibm.com` |

Check your region in the IBM Cloud dashboard (top right, next to your account name).

---

## Project Structure

You will create these files:

```
ai-travel-expense-tracker/
├── app.py                 # Streamlit UI
├── doc_processing.py      # PDF parsing + LLM extraction + charts
├── model_gateway.py       # watsonx.ai REST API layer
├── requirements.txt       # Python dependencies
└── .env                   # Your credentials
```

---

## Step 1: Create Your Project Folder

```bash
# Navigate to your Desktop (easy to find later)
cd ~/Desktop

# Create the project folder
mkdir ai-travel-expense-tracker

# Enter the folder
cd ai-travel-expense-tracker
```
> 💡 **Important**: Every time you open a new Terminal window, you must run this command first before doing anything else:
> ```bash
> cd "/path/to/your/project-folder"
> ```
> If you skip this step, all subsequent commands will fail with "module not found" or "file not found" errors.
---

## Step 2: Create `requirements.txt`

Create a file named `requirements.txt` with this exact content:

```
cat > requirements.txt << 'EOF'
streamlit
pandas
plotly
docling
python-dotenv
requests
EOF
```
## Step 2.5: Install Dependencies

After creating requirements.txt, install the packages:

```bash
pip install -r requirements.txt
```
If you get ModuleNotFoundError when running the app later, try:

```bash
pip3 install -r requirements.txt
```
---

## Step 3: Create `.env` File

First, make sure you are in your project folder:
```bash
cd ~/Desktop/ai-travel-expense-tracker

Then run this command to create the file:
cat > .env << 'EOF'
API_KEY=paste_your_api_key_here
PROJECT_ID=paste_your_project_id_here
CLOUD_URL=https://us-south.ml.cloud.ibm.com
LLM_NAME=ibm/granite-3-8b-instruct
EOF
```
No output means it worked. Verify the file was created:
```bash
cat .env
```
You should see the four lines above.

3d. Fill In Your Real Credentials
Open the file in a text editor:
```bash
# Mac
open -e .env

# Windows
notepad .env
```
Replace the placeholder values with your real credentials:
```bash
API_KEY=your_actual_api_key_here
PROJECT_ID=your_actual_project_id_here
CLOUD_URL=https://us-south.ml.cloud.ibm.com
LLM_NAME=ibm/granite-3-8b-instruct
```
> ⚠️ If your file downloaded as `env (1).template` (with a number in brackets), run this instead:
```bash
> cp "env (1).template" .env
```
> 🔒 **Security Note**: Never commit `.env` to version control. Add it to `.gitignore`.

---

## Step 4: Generate `model_gateway.py` with Bob

This file handles the connection to watsonx.ai using the REST API.

💡 Why REST API and not the SDK? The IBM watsonx-ai SDK has compatibility issues with Python 3.14. The REST API works across all supported Python versions.

4a Open Bob and paste this prompt:

```
Generate a Python file called model_gateway.py that connects to IBM watsonx.ai using the REST API (not the SDK).

Requirements:
- Load API_KEY, PROJECT_ID, CLOUD_URL, and LLM_NAME from a .env file using python-dotenv
- Implement IAM token exchange: POST to https://iam.cloud.ibm.com/identity/token to get a Bearer token
- Cache the token for 50 minutes (IBM tokens expire after 60 minutes)
- Expose a single public function: invoke_llm(prompt: str) -> str
- Call the watsonx.ai text generation endpoint: {CLOUD_URL}/ml/v1/text/generation?version=2023-05-29
- Use these generation parameters:
    max_new_tokens: 2048
    temperature: 0.0
    repetition_penalty: 1.05
    stop_sequences: ["```"]

Return only the complete Python file with no explanations.
```


4b. Save the file
Click Apply in Bob, or copy the generated code and save it as model_gateway.py in your project folder.

4c: Verify your API Key
```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://iam.cloud.ibm.com/identity/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_API_KEY"
```
Replace `YOUR_API_KEY` with the value from your `.env` file.
 
| Output | Meaning |
|--------|---------|
| `200` | ✅ API Key is valid |
| `400` | ❌ Wrong `PROJECT_ID` — check it's the 36-character UUID |
| `401` | ❌ API Key is invalid — contact your lab organizer |

### 4d. Test the watsonx.ai connection
 
```bash
python3 -c "
from model_gateway import invoke_llm
print(invoke_llm('Say hello in one sentence.'))
"
```
 
**Expected:** Granite 3 replies with a sentence ✅
 
---

## Step 5: Generate `doc_processing.py` with Bob

This file handles PDF parsing and AI-powered data extraction.

###Open Bob and paste this prompt:

```
Generate a Python file called doc_processing.py for processing travel expense PDF receipts.

Requirements:

PDF parsing:
- Use Docling to convert PDF bytes to Markdown text
- Configure Docling with: do_ocr=True, do_table_structure=True (high-fidelity mode — do NOT disable these)
- Use PdfPipelineOptions and PdfFormatOption to pass options (do NOT pass do_ocr or do_table_structure as direct arguments to converter.convert())
- Correct usage:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )
    result = converter.convert(tmp_path)
- Save PDF bytes to a temp file, convert, then delete the temp file

Document type detection:
- Implement _detect_doc_type(filename: str, text: str) -> str
- Detection uses BOTH filename and document text content, with weighted scoring
- Score each candidate type by counting keyword matches in filename (weight 3) and in text (weight 1)
- Keywords per type:
    hotel: hotel, inn, folio, marriott, hilton, hyatt, sheraton, westin, fairmont, resort, lodge, accommodation, room rate, check-in, check-out
    flight: flight, airline, boarding, airways, airfare, itinerary, departure, arrival, seat, gate
    meal: meal, restaurant, food, dining, cafe, bistro, menu, cuisine, eatery, tavern
    car: car, rental, vehicle, hertz, avis, enterprise, budget rent, national car, mileage, odometer
- Return the type with the highest score
- If all scores are 0, return "generic"
- No single type has blanket priority — scoring determines winner

LLM extraction:
- Write a separate extraction prompt for each of the 5 document types (hotel, flight, meal, car, generic)
- Each prompt instructs the LLM to return ONLY a valid JSON array — no markdown, no code fences, no explanation, no preamble
- Each extracted row must have these exact fields:
    date (YYYY-MM-DD or empty string if unknown), vendor, doc_type, category, description, currency, amount (numeric), confidence (0.0–1.0)

- Hotel prompt must say:
    "Extract every individual line item from this hotel folio. Each charge must be a separate JSON object.
    Do not merge multiple charges into one row.
    Categories: Room, Food & Beverage, Parking, Spa & Wellness, Taxes & Fees, Telephone, Laundry, Minibar, Miscellaneous"

- Flight prompt categories: Airfare, Baggage Fee, Seat Upgrade, Travel Insurance, Change Fee, Miscellaneous

- Meal prompt must say:
    "Extract each menu item or charge as a separate line item. Do not merge multiple items into one row.
    If the invoice shows a total only, extract it as one row.
    Categories: Breakfast, Lunch, Dinner, Coffee & Snacks, Alcohol, Miscellaneous"

- Car prompt categories: Base Rental, Fuel, Insurance, Toll Charges, GPS & Equipment, Taxes & Fees, Miscellaneous

- Generic prompt must say:
    "Extract ALL line items. For each row, detect doc_type from the content — must be one of: Hotel, Flight, Meal, Car Rental.
    Use all categories from all 4 types combined."

- Summary / chat prompts (if any) must say:
    "Answer directly in the first sentence. Do not restate the question, do not add preamble or commentary."

Vendor extraction:
- Implement _extract_vendor_from_text(text: str) -> str
    - Look for vendor name in the first 10 lines of the document text
    - Return the most prominent proper noun or company name found
    - Return "Unknown" only if nothing is found
- Implement _normalize_expenses(rows: list) -> list
    - If vendor field is empty or "Unknown", call _extract_vendor_from_text on the raw text and fill it in
    - If doc_type is missing, set it to the detected type from _detect_doc_type
    - Strip whitespace from all string fields

Amount parsing:
- Handle currency symbols: $, €, £, ¥, ₹
- Handle thousands separators: 1,234.56
- Handle European decimal format: 1.234,56
- Always apply abs() to the final parsed amount (all expenses are positive)

JSON parsing:
- Use regex to find the [...] array in LLM output
- Strip any markdown code fences (``` or ```json) before parsing
- Return an empty list [] if no valid JSON is found — do not raise exceptions

Output:
- Function process_invoices(uploaded_files) → pandas DataFrame
- Columns: Date, Vendor, Doc Type, Category, Description, Currency, Amount, Confidence
- Function analyze_invoices(df) → tuple of 3 Plotly figures:
    1. Horizontal bar chart: expenses by vendor (color #3B82F6)
    2. Donut chart: expenses by category (hole=0.4)
    3. Bar chart: expenses by document type (Hotel=#3B82F6, Flight=#A855F7, Meal=#10B981, Car Rental=#F59E0B)
- CRITICAL: Bar charts and pie/donut charts must use SEPARATE layout config objects
    - Do NOT apply xaxis or yaxis to any pie or donut chart — this causes a crash
    - Bar chart layout: include xaxis, yaxis, font, plot_bgcolor, paper_bgcolor
    - Pie/donut chart layout: include only font, plot_bgcolor, paper_bgcolor (no axis keys)
- All charts: transparent background, Inter font

Use only straight ASCII quotes (" and ') throughout. Do not use curly or smart quotes.
Include all return statements explicitly — do not omit any return.
Return only the complete Python file with no explanations.
```
----

## Step 6 — Generate `app.py` with Bob

Open Bob and paste this prompt:
```
Generate a Python file called app.py for a Streamlit web application called "AI Travel Expense Tracker".

Requirements:

Imports:
- from doc_processing import process_invoices, analyze_invoices
- from model_gateway import invoke_llm

Page setup:
- st.set_page_config: title="AI Travel Expense Tracker", page_icon="✈️", layout="wide"
- Custom CSS: Inter font, background #F1F5F9, white cards with border-radius, hide Streamlit footer

Layout:
- Hero banner: dark gradient background (#0F172A to #1D4ED8), show app title and subtitle
- Badge in hero: "Powered by IBM watsonx.ai"
- File uploader: accepts PDF only, up to 10 files
- Four buttons in a row: Submit (primary), Analyze (secondary), Generate Summary (secondary), Export CSV (download)

Session state:
- st.session_state.df → stores the extracted DataFrame
- st.session_state.summary → stores the generated summary string

On Submit button click:
- Show a progress bar using st.progress(0) and a status text placeholder
- Process each file one by one, updating the progress bar and status text
  as each file is completed (e.g. "Processing file 2 of 3: marriott_hotel.pdf...")
- After all files are processed, clear the progress bar and status text
- Store the combined results in st.session_state.df
- Reset st.session_state.summary to None
- Show a success message

Results section (shown when st.session_state.df is not empty):
- 4 metric cards: Files Processed, Line Items, Total Amount (formatted as $X,XXX.XX), Avg Confidence (as %)
- Styled dataframe with emoji column headers:
  📅 Date, 🏢 Vendor, 📄 Doc Type, 🏷️ Category, 📝 Description, 💱 Currency, 💵 Amount, 

On Analyze button click:
- Call analyze_invoices(st.session_state.df)
- Show all 3 charts using st.plotly_chart

On Generate Summary button click:
- If no data, show a warning: "Please upload and submit receipts first"
- Otherwise, call generate_summary(df) with st.spinner("✨ Generating AI summary...")
- Store result in st.session_state.summary
- Display with st.info()

generate_summary(df) function:
- Compute these stats from the DataFrame:
    total amount, number of line items, breakdown by category (category name + subtotal),
    top vendor and their total, breakdown by doc type, date range, average daily spend
- Handle date parsing errors gracefully with try/except — do not crash if dates are missing or malformed
- Build a prompt using the stats above and send it to invoke_llm()
- The prompt must instruct the LLM:
    "You are a corporate travel expense analyst. Given the following expense data, write a concise
    3-sentence summary. Cover only: (1) total spend and date range, (2) largest spending category
    and top vendor, (3) one specific actionable recommendation to reduce costs.
    Do not restate all the numbers. Do not use markdown, bullet points, headers, or bold text.
    Do not add preamble or commentary. Return plain text only."
- After receiving the LLM response, strip any remaining markdown symbols: **, ##, *, and leading -
- Store the result in a variable called summary
- Return summary explicitly with a return statement — do not omit the return

Do NOT include: Astra DB, database connections, or chat interface.
Use only straight ASCII quotes (" and ') throughout. Do not use curly or smart quotes.
Return only the complete Python file with no explanations.
```


## Pre-Run Validation

Before starting the app, run these three commands to catch issues early:

### 1. Check Python Version

```bash
python3 --version
# Expected: Python 3.10.x, 3.11.x, 3.12.x, or 3.13.x
```

### 2. Test API Key

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://iam.cloud.ibm.com/identity/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_API_KEY"
```

Replace `YOUR_API_KEY` with your actual key. Expected output: `200`

- Got `400`? Wrong `PROJECT_ID` in `.env` — check it's the 36-character UUID
- Got `401`? API Key is invalid — regenerate it in IBM Cloud

### 3. Test All Imports

```bash
python3 -c "import streamlit, pandas, plotly, docling, requests, dotenv; print('✅ All OK')"
# Expected: ✅ All OK
```

---

## Install Dependencies

### Python 3.10–3.13

```bash
pip install -r requirements.txt
```

### Python 3.14

```bash
pip install uv
uv pip install pillow==11.3.0 --only-binary :all:
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

If `streamlit` is not on your PATH:

```bash
python3 -m streamlit run app.py
```
For example:
```bash
cd /Users/austinzhang/Desktop/Test\ Bob && streamlit run app.py
```

The app opens automatically at **http://localhost:8501**.


## Usage

1. **Upload PDFs**: Click the file uploader and select up to 10 receipt PDFs
2. **Submit**: Click "⚡ Submit" to extract data (takes 10–30 seconds per file)
3. **View Results**: See table with 8 columns and 4 metric cards
4. **Analyze**: Click "📊 Analyze" to generate 3 interactive charts
5. **Summarize**: Click "📝 Generate Summary" to get an AI-written summary of your expenses
6. **Export**: Click "⬇️ Export CSV" to download the extracted data

---

---

## Tips for Success

- **Use Ask Mode first** — if you don't understand what Bob generated, switch to Ask Mode and paste the code to get an explanation
- **One file at a time** — generate and test each file before moving to the next
- **Rename your PDFs** — include keywords like `marriott_hotel.pdf` or `delta_flight.pdf` so the app detects the type correctly
- **If Bob's output looks cut off** — ask it to regenerate: *"Please regenerate the complete file, do not truncate"*
- **Use the solution folder** — if you're stuck, `solution/` has a working reference implementation

---

## If you still have time, check LAB2 and LAB3.

## Congratulations! 🎉

You've extended your AI Travel Expense Tracker with a full budget tracking system — all built using IBM Bob.

Your app now has:
- PDF parsing using IBM Docling
- AI extraction using watsonx.ai Granite 3
- A clear UI design
- Interactive charts with Plotly
- Detailed Summary of all your spend
- Easy to download CSV version
- Budget tracking and overspend alerts



---

## Support

If you encounter issues not covered in this guide:

1. Check the [Cheat Sheet](cheat-sheet.md) for quick fixes
2. Verify all three Pre-Run Validation commands pass
3. Ensure your `.env` file has correct credentials
4. Try with a single, simple PDF first
5. Check the `solution/` folder as a last resort

---

**End of Build Guide**

You now have a complete, working AI Travel Expense Tracker. Happy building! 🚀
