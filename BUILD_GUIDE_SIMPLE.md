# AI Travel Expense Tracker — Build Guide

Complete guide for building an AI-powered expense tracker using IBM Bob and watsonx.ai.

This guide assumes no prior context. Follow every step to build a working application from scratch.

---

## What This Application Does

✅ Upload up to 10 PDF receipts (hotels, flights, meals, car rentals)/
✅ Auto-detect document type from filename/
✅ Extract structured expense data using IBM watsonx.ai Granite 3 LLM/
✅ Display results in a table with 8 columns/
✅ Show 4 metric cards (Files Processed, Line Items, Total Amount, Avg Confidence)/
✅ Generate 3 interactive Plotly charts (by vendor, by category, by document type)/
✅ Export data to CSV/
✅ Generate an AI-written plain-English summary of your trip expenses/


---

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows
- **Python Version**: 3.10, 3.11, 3.12, or 3.13 (recommended)
  - Python 3.14 requires special setup (see below)
- **Internet Connection**: Required for first run (downloads ~2GB of ML models)
- **Disk Space**: At least 5GB free

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

**Why?** Python 3.14 has binary compatibility issues that prevent standard package installation. Installing pillow first with `--only-binary :all:` resolves this blocking issue.

### Required Accounts

- **IBM Cloud Account** (free tier available) — sign up at [cloud.ibm.com](https://cloud.ibm.com)

---

## Get Your Credentials

Before writing any code, you need two pieces of information from IBM Cloud.

### Step 1: Get IBM Cloud API Key

1. Go to [cloud.ibm.com](https://cloud.ibm.com) and sign in
2. Click your account avatar (top right corner)
3. Select **Manage** → **Access (IAM)**
4. In the left sidebar, click **API keys**
5. Click **Create** button
6. Give it a name (e.g., `watsonx-expense-tracker`)
7. Click **Create**
8. ⚠️ **Copy the API key immediately** — it's shown only once
9. Save it securely (you'll paste it into `.env` later)

### Step 2: Get watsonx.ai Project ID

1. From IBM Cloud dashboard, go to **Resource List**
2. Under **AI / Machine Learning**, find your watsonx.ai instance
3. Click on it, then click **Launch IBM watsonx**
4. On the watsonx home screen, find the **Developer Access** section
5. Select your project from the dropdown
6. Copy the **Project ID** (36-character UUID like `12345678-1234-1234-1234-123456789abc`)
7. Save it securely

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
- Configure Docling with: do_ocr=False, do_table_structure=True
- Save PDF bytes to a temp file, convert, then delete the temp file

Document type detection (from filename, case-insensitive):
- hotel: keywords hotel, inn, marriott, hilton, hyatt, sheraton, westin, fairmont, resort, lodge, accommodation → doc_type = "hotel"
- flight: keywords flight, airline, boarding, airways → doc_type = "flight"
- meal: keywords meal, restaurant, food, dining, cafe, bistro → doc_type = "meal"
- car: keywords car, rental, vehicle, hertz, avis, enterprise → doc_type = "car"
- Default fallback (no keyword match): "generic"
- Hotel keywords take highest priority

LLM extraction:
- Write a separate extraction prompt for each of the 5 document types (hotel, flight, meal, car, generic)
- Each prompt asks the LLM to return ONLY a JSON array (no markdown, no explanation)
- Each extracted row must have these fields:
    date (YYYY-MM-DD), vendor, doc_type, category, description, currency, amount, confidence (0.0-1.0)
- Categories for hotel: Room, Food & Beverage, Parking, Spa & Wellness, Taxes & Fees, Telephone, Laundry, Minibar, Miscellaneous
- Categories for flight: Airfare, Baggage Fee, Seat Upgrade, Travel Insurance, Change Fee, Miscellaneous
- Categories for meal: Breakfast, Lunch, Dinner, Coffee & Snacks, Alcohol, Miscellaneous
- Categories for car: Base Rental, Fuel, Insurance, Toll Charges, GPS & Equipment, Taxes & Fees, Miscellaneous
- For generic: extract ALL line items from mixed travel invoices (e.g. travel agency invoices). For each row, detect doc_type from the content itself — must be one of "Hotel", "Flight", "Meal", "Car Rental". Use all categories from all 4 types combined.

Amount parsing:
- Handle currency symbols: $, €, £, ¥, ₹
- Handle thousands separators: 1,234.56
- Handle European decimal format: 1.234,56
- Always apply abs() to the final amount (expenses are always positive)

JSON parsing:
- Use regex to find the [...] array in LLM output
- Return an empty list if no valid JSON is found

Output:
- Function process_invoices(uploaded_files) → pandas DataFrame
- Columns: Date, Vendor, Doc Type, Category, Description, Currency, Amount, Confidence
- Function analyze_invoices(df) → tuple of 3 Plotly figures:
    1. Horizontal bar chart: expenses by vendor (color #3B82F6)
    2. Donut chart: expenses by category (hole=0.4)
    3. Bar chart: expenses by document type (Hotel=#3B82F6, Flight=#A855F7, Meal=#10B981, Car Rental=#F59E0B)
- Bar charts and pie/donut charts must use SEPARATE layout configs (pie charts do not support xaxis/yaxis)
- All charts: transparent background, Inter font

Return only the complete Python file with no explanations.
---

## Step 6: Generate `app.py` with Bob

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
- Call process_invoices(uploaded_files) and store result in st.session_state.df
- Reset st.session_state.summary to None
- Show a success message

Results section (shown when st.session_state.df is not empty):
- 4 metric cards: Files Processed, Line Items, Total Amount (formatted as $X,XXX.XX), Avg Confidence (as %)
- Styled dataframe with emoji column headers:
  📅 Date, 🏢 Vendor, 📄 Doc Type, 🏷️ Category, 📝 Description, 💱 Currency, 💵 Amount, 🎯 Confidence

On Analyze button click:
- Call analyze_invoices(st.session_state.df)
- Show all 3 charts using st.plotly_chart

On Generate Summary button click:
- If no data, show a warning: "Please upload and submit receipts first"
- Otherwise, call a generate_summary(df) function with st.spinner("✨ Generating AI summary...")
- Store result in st.session_state.summary
- Display with st.info()

generate_summary(df) function:
- Compute: total amount, number of items, breakdown by category, top vendor and their total, breakdown by doc type
- Try to compute date range and average daily spend from the Date column (handle errors gracefully)
- Build a prompt with these stats and ask the LLM to write a 3-4 sentence professional plain-English summary
- Call invoke_llm(prompt) and return the result

Do NOT include: Astra DB, database connections, or chat interface.

Return only the complete Python file with no explanations.
```

Save Bob's output as `app.py`.

---

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

The app opens automatically at **http://localhost:8501**.

---

## Usage

1. **Upload PDFs**: Click the file uploader and select up to 10 receipt PDFs
2. **Submit**: Click "⚡ Submit" to extract data (takes 10–30 seconds per file)
3. **View Results**: See table with 8 columns and 4 metric cards
4. **Analyze**: Click "📊 Analyze" to generate 3 interactive charts
5. **Summarize**: Click "📝 Generate Summary" to get an AI-written summary of your expenses
6. **Export**: Click "⬇️ Export CSV" to download the extracted data

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Total Amount shows $0.00` | LLM returned negative amounts | Make sure `abs()` is applied in `_normalize_row` in `doc_processing.py` |
| `TypeError: object.__init__()` | Python 3.14 + wrong install order | Install pillow first with `--only-binary :all:`, then use `uv` |
| `JSONDecodeError` | LLM returned markdown fences | Make sure `stop_sequences: ["` ``` `"]` is in `model_gateway.py` |
| Document type wrong | Filename doesn't match keywords | Rename file to include keyword (e.g., `hilton_hotel.pdf`) |
| `401 Unauthorized` | API Key not exchanged for token | Make sure `model_gateway.py` uses IAM token exchange, not raw API key |
| Pie chart errors | Wrong layout applied to pie chart | Use separate layout dicts for bar vs pie charts |
| `streamlit: command not found` | Streamlit not on PATH | Use `python3 -m streamlit run app.py` instead |
| First run takes forever | Downloading Docling models (~2GB) | Wait 5–10 minutes. Do not interrupt. |
| `ModuleNotFoundError: docling` | Dependencies not installed | Run `pip install -r requirements.txt` |
| Charts don't appear | Clicked Analyze before Submit | Click "⚡ Submit" first, then "📊 Analyze" |
| `400 Bad Request` on token call | Wrong Project ID | Check `PROJECT_ID` in `.env` — must be 36-character UUID |

---

## Advanced Configuration

### Change LLM Model

Edit `.env` and change `LLM_NAME`:

```env
LLM_NAME=ibm/granite-3-8b-instruct      # Default
# LLM_NAME=ibm/granite-13b-instruct-v2
# LLM_NAME=meta-llama/llama-3-70b-instruct
```

### Change Region

Edit `.env` and update `CLOUD_URL`:

```env
CLOUD_URL=https://us-south.ml.cloud.ibm.com   # US South (default)
CLOUD_URL=https://ca-tor.ml.cloud.ibm.com      # Canada (Toronto)
CLOUD_URL=https://eu-de.ml.cloud.ibm.com       # Europe (Frankfurt)
```

### Change Port

```bash
streamlit run app.py --server.port 8502
```

---

## Tips for Success

- **Use Ask Mode first** — if you don't understand what Bob generated, switch to Ask Mode and paste the code to get an explanation
- **One file at a time** — generate and test each file before moving to the next
- **Rename your PDFs** — include keywords like `marriott_hotel.pdf` or `delta_flight.pdf` so the app detects the type correctly
- **If Bob's output looks cut off** — ask it to regenerate: *"Please regenerate the complete file, do not truncate"*
- **Use the solution folder** — if you're stuck, `solution/` has a working reference implementation

---

## 🎉 What's Next — Bonus Lab

If you still have time, check out **Lab 2** to extend your tracker with more features using Bob's Plan Mode!

# 🎯 AI Travel Expense Tracker — Lab 2: Budget Tracker

> **Prerequisites:** You must have completed Lab 1 and have a working app before starting this lab.
>
> Just like Lab 1, you will use **IBM Bob** to generate all the code. No manual coding required.

---

## What You'll Add

By the end of this lab, your app will have a new budget tracking feature:

- ✅ **Total Trip Budget** — Set an overall spending limit for your trip
- ✅ **Per-Category Budgets** — Set individual limits for Hotel, Flight, Meal, and Car Rental
- ✅ **Overspend Alerts** — Red warning banners when you exceed any budget
- ✅ **Budget vs. Actual Chart** — A new chart comparing what you planned to spend vs. what you actually spent

---

## How This Lab Works

You will modify two existing files using Bob:

| File | What Changes |
|------|-------------|
| `app.py` | Add budget input UI, progress bars, and alert banners |
| `doc_processing.py` | Add a 4th chart comparing budget vs. actual spending |

> 💡 **Tip:** Use Bob's **Ask Mode** if you want to understand what a piece of code does before applying it.

---

## Step 1 — Add Budget Settings to `app.py`

### 1a. Open `app.py` in Bob

In Bob's Explorer panel, click on `app.py` to open it.

### 1b. Paste this prompt into Bob
```
I have an existing Streamlit app called app.py for an AI Travel Expense Tracker.
I want to add budget tracking features. Modify app.py to include the following:

Budget settings UI (add this in the sidebar using st.sidebar):
- A number input for "Total Trip Budget" (default: 5000, min: 0, step: 100, prefix: $)
- Four number inputs for per-category budgets:
    Hotel budget (default: 2000)
    Flight budget (default: 1500)
    Meal budget (default: 800)
    Car Rental budget (default: 700)
- Store all budget values in st.session_state

Budget summary section (add this below the 4 metric cards, only shown when st.session_state.df is not empty):
- A progress bar showing Total Spent vs Total Budget
- Format: "Spent $X,XXX.XX of $X,XXX.XX budget (XX%)"
- If spent exceeds budget: show st.error with message "⚠️ Over budget by $X,XXX.XX"
- If spent is between 80-100% of budget: show st.warning with message "⚠️ Approaching budget limit"
- If spent is under 80%: show st.success with message "✅ Within budget"

Per-category alert section (add this below the budget summary):
- For each of the 4 categories (Hotel, Flight, Meal, Car Rental):
    - Calculate total spent in that category from st.session_state.df
    - If spent exceeds the category budget: show st.error "⚠️ [Category] over budget: spent $X,XXX.XX of $X,XXX.XX"
    - Otherwise: show a compact one-line status with a progress bar

Return the complete modified app.py with no explanations.
```

### 1c. Save the file

Click **Apply** in Bob, or copy the output and replace the contents of `app.py`.

> ⚠️ **If Bob's output looks cut off**, ask it: *"Please regenerate the complete file, do not truncate."*

---

## Step 2 — Add a Budget vs. Actual Chart to `doc_processing.py`

### 2a. Open `doc_processing.py` in Bob

### 2b. Paste this prompt into Bob
```
I have an existing file called doc_processing.py for an AI Travel Expense Tracker.

Modify the analyze_invoices() function to accept an optional second parameter:
    category_budgets: dict = None

If category_budgets is provided, add a 4th Plotly figure to the returned tuple:
- A grouped bar chart comparing "Budgeted" vs "Actual" spending for each of the 4 doc types:
  Hotel, Flight, Meal, Car Rental
- Budgeted bars: color #94A3B8
- Actual bars: color #3B82F6 if under budget, #EF4444 if over budget
- Chart title: "Budget vs. Actual by Category"
- Transparent background, Inter font
- If category_budgets is None, return the original 3-figure tuple as before

Return the complete modified doc_processing.py with no explanations.
```

### 2c. Save the file

Click **Apply** in Bob, or copy the output and replace the contents of `doc_processing.py`.

---

## Step 3 — Update the Analyze Button in `app.py`

Now that `analyze_invoices()` can return a 4th chart, update `app.py` to pass the budget data through and display it.

### Paste this prompt into Bob
```
In my app.py, update the Analyze button section to:
- Pass category_budgets from st.session_state into analyze_invoices()
- Handle both 3-figure and 4-figure return values (use len() to check)
- If 4 figures are returned, display all 4 charts using st.plotly_chart
- Keep all other existing behavior unchanged

Return the complete modified app.py with no explanations.
```

Click **Apply** in Bob.

---

## Step 4 — Test the New Features

Make sure you are in your project folder, then restart the app:
```bash
cd ~/Desktop/ai-travel-expense-tracker
streamlit run app.py
```

### What to test:

1. **Sidebar** — You should see budget input fields on the left side
2. **Submit receipts** — Upload some PDFs and click ⚡ Submit as usual
3. **Budget summary** — Below the metric cards, check the progress bar and alert banner
4. **Set a low budget** — Change Total Trip Budget to `$100` and confirm the red ⚠️ banner appears
5. **Category alerts** — Set Hotel budget to `$1` and check for a category-level warning
6. **Budget chart** — Click **📊 Analyze** and confirm a 4th chart appears comparing budget vs. actual

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Sidebar not showing | Budget UI not added correctly | Check that Bob added `st.sidebar` inputs, not regular inputs |
| `analyze_invoices() takes 1 argument` | Old function signature | Re-run the Step 2 prompt to update `doc_processing.py` |
| 4th chart not appearing | Analyze button not updated | Re-run the Step 3 prompt |
| Budget always shows $0 | Session state not initialized | Make sure `st.session_state` budget values are set with defaults |
| App crashes on restart | Syntax error in generated code | Paste the broken file into Bob and ask: *"Fix any syntax errors in this file."* |

---

## Tips for Success

- **Test after each step** — restart the app after Step 1, Step 2, and Step 3 to catch issues early
- **Use Ask Mode** — paste any confusing code into Bob in Ask Mode to get an explanation
- **Check the `solution/` folder** — `solution/app_lab2.py` and `solution/doc_processing_lab2.py` are available if you get stuck

---

## Congratulations! 🎉

You've extended your AI Travel Expense Tracker with a full budget tracking system — all built using IBM Bob.

Your app now has:
- PDF parsing using IBM Docling
- AI extraction using watsonx.ai Granite 3
- Interactive charts with Plotly
- Budget tracking and overspend alerts

**Want to go further?** Ask Bob to help you add:
- Email export of the summary
- Support for image receipts (JPG/PNG)
- Currency conversion using a live exchange rate API


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
