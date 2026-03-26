# 📋 Cheat Sheet — AI Travel Expense Tracker Bobathon

> Keep this open the whole time. Everything you need is on this page.

---

## 📌 Table of Contents

1. [What You're Building](#1-what-youre-building)
2. [Before You Start — Checklist](#2-before-you-start--checklist)
3. [Get Your IBM Credentials, API Keys](#3-get-your-ibm-credentials)
4. [Set Up Your Project Folder](#4-set-up-your-project-folder)
5. [Bob Prompts — Generate Each File](#5-bob-prompts--generate-each-file)
6. [Install & Run](#6-install--run)
7. [Test the App](#7-test-the-app)
8. [Troubleshooting](#8-troubleshooting)
9. [Python 3.14 Special Setup](#9-python-314-special-setup)
10. [File Naming Tips](#10-file-naming-tips)

---

## 1. What You're Building

A Streamlit web app that:

| Feature | Details |
|---------|---------|
| 📄 Upload receipts | Up to 10 PDF files at once |
| 🤖 AI extraction | IBM watsonx.ai reads each receipt and pulls out expense data |
| 📊 Charts | 3 interactive charts: by vendor, by category, by document type |
| 💾 Export | Download all extracted data as a CSV file |

**You are NOT building**: a database, a login system, or a chat interface. Just the core tracker.

**Files you'll create** (Bob generates all of these):

```
ai-travel-expense-tracker/
├── requirements.txt     ← Python packages to install
├── .env                 ← Your IBM credentials (never share this)
├── model_gateway.py     ← Connects to IBM watsonx.ai
├── doc_processing.py    ← Reads PDFs and extracts expense data
└── app.py               ← The web interface
```

---

## 2. Before You Start — Checklist

Go through this before the lab begins:

- [ ] **Bob is installed** and you can open it
- [ ] **Python 3.10–3.13** is installed → run `python3 --version` in your terminal to check
- [ ] **You have an IBM Cloud account** → [sign up free at cloud.ibm.com](https://cloud.ibm.com)
- [ ] **You have a watsonx.ai project** created in IBM Cloud
- [ ] **5 GB+ free disk space** → Docling downloads ~2 GB of AI models on first run
- [ ] **Stable internet** → needed for model downloads and API calls

> ⚠️ **Using Python 3.14?** Stop here and read [Section 9](#9-python-314-special-setup) first.

---

## 3. Get Your IBM Credentials

You need **two things** from IBM Cloud before writing any code. Get these first.

---

### 3a. Get Your API Key

Your API Key is like a password that lets your app talk to IBM watsonx.ai.

**Step by step:**

1. Go to [cloud.ibm.com](https://cloud.ibm.com) and sign in
2. Click your **profile avatar** in the top-right corner
3. Click **Manage** → **Access (IAM)**
4. In the left sidebar, click **API keys**
5. Click the blue **Create** button
6. Give it a name — anything works, e.g. `bobathon-key`
7. Click **Create**
8. ⚠️ **Copy the key immediately** — IBM only shows it once. If you miss it, you'll need to create a new one.
9. Paste it somewhere safe (you'll need it in a moment)

> 💡 The key looks like this: `abc123XYZdef456...` — a long string of random characters

---

### 3b. Get Your Project ID

Your Project ID tells watsonx.ai which project to bill usage to.

**Step by step:**

1. From the IBM Cloud dashboard, click **Resource List** in the left sidebar
2. Look under **AI / Machine Learning** — find your **watsonx.ai** instance and click it
3. Click **Launch IBM watsonx** (blue button)
4. On the watsonx home screen, scroll down to find **Developer Access**
5. Click the project dropdown and select your project
6. Copy the **Project ID** — it looks like this: `12345678-1234-1234-1234-123456789abc` (36 characters with dashes)

> 💡 Can't find Developer Access? Try: top-right menu → **Manage** → your project → **Manage** tab → copy the ID from there.

---

### 3c. Find Your Region URL

Your `CLOUD_URL` depends on where your IBM Cloud account is based.
Check the region name in the **top-right corner** of the IBM Cloud dashboard.

| Your Region | Use this URL |
|-------------|-------------|
| US South (Dallas) | `https://us-south.ml.cloud.ibm.com` |
| Canada (Toronto) | `https://ca-tor.ml.cloud.ibm.com` |
| Europe (Frankfurt) | `https://eu-de.ml.cloud.ibm.com` |
| UK (London) | `https://eu-gb.ml.cloud.ibm.com` |
| Asia Pacific (Tokyo) | `https://jp-tok.ml.cloud.ibm.com` |

---

## 4. Set Up Your Project Folder

### Create the folder

```bash
mkdir ai-travel-expense-tracker
cd ai-travel-expense-tracker
```

### Create your `.env` file

This file stores your credentials. Create a file called `.env` (just `.env`, no other extension) and paste this in:

```env
API_KEY=paste_your_api_key_here
PROJECT_ID=paste_your_project_id_here
CLOUD_URL=https://us-south.ml.cloud.ibm.com
LLM_NAME=ibm/granite-3-8b-instruct
```

Replace the two placeholder values with your real credentials from Section 3.
Update `CLOUD_URL` if you're not in US South.

**How to create `.env` on Mac/Linux:**
```bash
touch .env
open -e .env    # opens in TextEdit
```

**How to create `.env` on Windows:**
```powershell
New-Item .env
notepad .env
```

> 🔒 **Never share or upload your `.env` file.** It contains your API key.
> Add `.env` to your `.gitignore` if using Git.

---

### Create `requirements.txt`

Create a file called `requirements.txt` with exactly this content:

```
streamlit
pandas
plotly
docling
python-dotenv
requests
```

You can ask Bob to create this, or just create it manually — it's only 6 lines.

---

## 5. Bob Prompts — Generate Each File

Use these prompts in Bob **in order**. Copy the whole prompt, paste it into Bob, wait for Bob to finish, then save the file before moving on.

> 💡 **Tip**: After Bob generates each file, quickly skim it to make sure it looks complete (not cut off). If it seems truncated, use the follow-up prompt at the bottom of this section.

---

### Prompt 1 — Generate `model_gateway.py`

This file handles the connection to IBM watsonx.ai.

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

**Why REST API and not the SDK?**
The IBM watsonx-ai Python SDK has compatibility issues with Python 3.14. Using the REST API directly works on all Python versions and is more reliable in workshop environments.

---

### Prompt 2 — Generate `doc_processing.py`

This file reads PDFs and uses the LLM to extract expense data.

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
- Default fallback (no keyword match): "hotel"
- Hotel keywords take highest priority

LLM extraction:
- Write a separate extraction prompt for each of the 4 document types
- Each prompt asks the LLM to return ONLY a JSON array (no markdown, no explanation)
- Each extracted row must have these fields:
    date (YYYY-MM-DD), vendor, doc_type, category, description, currency, amount, confidence (0.0–1.0)
- Categories for hotel: Room, Food & Beverage, Parking, Spa & Wellness, Taxes & Fees, Telephone, Laundry, Minibar, Miscellaneous
- Categories for flight: Airfare, Baggage Fee, Seat Upgrade, Travel Insurance, Change Fee, Miscellaneous
- Categories for meal: Breakfast, Lunch, Dinner, Coffee & Snacks, Alcohol, Miscellaneous
- Categories for car: Base Rental, Fuel, Insurance, Toll Charges, GPS & Equipment, Taxes & Fees, Miscellaneous

Amount parsing:
- Handle currency symbols: $, €, £, ¥, ₹
- Handle thousands separators: 1,234.56
- Handle European decimal format: 1.234,56
- Always apply abs() to the final amount (expenses are always positive)

JSON parsing:
- Use regex to find the [...] array in LLM output (LLM may include extra text)
- Return an empty list if no valid JSON is found

Output:
- Function process_invoices(uploaded_files) → pandas DataFrame
- Columns: Date, Vendor, Doc Type, Category, Description, Currency, Amount, Confidence
- Function analyze_invoices(df) → tuple of 3 Plotly figures:
    1. Horizontal bar chart: expenses by vendor (color #3B82F6)
    2. Donut chart: expenses by category (hole=0.4)
    3. Bar chart: expenses by document type (Hotel=#3B82F6, Flight=#A855F7, Meal=#10B981, Car Rental=#F59E0B)
- All charts: transparent background, Inter font, color #1E293B

Return only the complete Python file with no explanations.
```

---

### Prompt 3 — Generate `app.py`

This file is the Streamlit web interface.

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
- File uploader: accepts PDF only, up to 10 files, label "Upload your receipts (PDF format)"
- Three buttons in a row: Submit (primary), Analyze (secondary), Export CSV (download button)

Session state:
- st.session_state.df → stores the extracted DataFrame
- st.session_state.chat_history → stores chat messages

On Submit button click:
- Call process_invoices(uploaded_files) and store result in st.session_state.df
- Show a success message

Results section (shown when st.session_state.df is not empty):
- 4 metric cards: Files Processed, Line Items, Total Amount (formatted as $X,XXX.XX), Avg Confidence (as %)
- Styled dataframe with emoji column headers:
  📅 Date, 🏢 Vendor, 📄 Doc Type, 🏷️ Category, 📝 Description, 💱 Currency, 💵 Amount, 🎯 Confidence

On Analyze button click:
- Call analyze_invoices(st.session_state.df)
- Show all 3 charts using st.plotly_chart

Export CSV button:
- Only show when st.session_state.df is not empty
- Download filename: "expenses.csv"

Do NOT include: Astra DB, database connections, or any external storage.

Return only the complete Python file with no explanations.
```

---

### If Bob's output looks incomplete

If Bob stops generating mid-file or the code looks cut off:

```
The file you generated appears to be incomplete or truncated. Please regenerate 
the complete [file name] from the beginning. Include every function in full. 
Do not summarize or skip any section. Return only the complete Python file.
```

### If you want Bob to explain something

```
Explain what this code does in simple terms, as if I'm new to Python:

[paste the code here]
```

### If Bob generates an error in the code

```
This code produces the following error when I run it:

[paste the error message here]

Please fix the issue and return the corrected complete file.
```

---

## 6. Install & Run

### Step 1 — Validate before installing

Run these checks first. They catch the most common problems before you waste time installing.

**Check Python version:**
```bash
python3 --version
# ✅ Good: Python 3.10.x, 3.11.x, 3.12.x, or 3.13.x
# ⚠️  If 3.14.x: go to Section 9 before continuing
```

**Test your API Key (Mac/Linux):**
```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://iam.cloud.ibm.com/identity/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_API_KEY"
# ✅ Good: 200
# ❌ Bad: 400 or 401 → your API key is wrong, go back to Section 3a
```

**Test your API Key (Windows PowerShell):**
```powershell
$body = "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_API_KEY"
Invoke-RestMethod -Method Post `
  -Uri "https://iam.cloud.ibm.com/identity/token" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body $body | Select-Object token_type
# ✅ Good: shows token_type = Bearer
```

Replace `YOUR_API_KEY` with your actual key from `.env`.

---

### Step 2 — Install dependencies

**Python 3.10–3.13:**
```bash
pip install -r requirements.txt
```

**Python 3.14:** → See [Section 9](#9-python-314-special-setup)

> ⏳ This may take a few minutes. Docling has many dependencies.

**Verify everything installed correctly:**
```bash
python3 -c "import streamlit, pandas, plotly, docling, requests; print('✅ All imports OK')"
# ✅ Good: All imports OK
# ❌ Bad: ModuleNotFoundError → run pip install again
```

---

### Step 3 — Launch the app

```bash
streamlit run app.py
```

If that doesn't work:
```bash
python3 -m streamlit run app.py
```

The app opens automatically at **http://localhost:8501**

> ⚠️ **First run warning**: Docling will download ~2 GB of AI models. This takes **5–10 minutes** depending on your internet speed. You'll see download progress in the terminal. **Do not close the terminal or interrupt the process** — if you do, you'll have to start the download again.
>
> Second run onwards is instant — the models are cached locally.

---

## 7. Test the App

Once the app is running:

1. **Upload a receipt** → click the file uploader, select a PDF from `sample-receipts/`
2. **Click Submit** → wait 10–30 seconds per file while the AI reads it
3. **Check the table** → you should see extracted rows with dates, vendors, amounts
4. **Click Analyze** → three charts appear
5. **Click Export CSV** → downloads a `.csv` file with all extracted data

**If the results look wrong:**
- Check that the PDF filename contains the right keyword (see Section 10)
- Try a different sample receipt
- Make sure you clicked Submit before Analyze

---

## 8. Troubleshooting

### Common errors and how to fix them

| Error / Symptom | What it means | How to fix |
|-----------------|---------------|------------|
| `ModuleNotFoundError: No module named 'docling'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `streamlit: command not found` | Streamlit not on PATH | Use `python3 -m streamlit run app.py` |
| `401 Unauthorized` | API key not converting to token | Check that `model_gateway.py` uses IAM token exchange — look for a POST to `iam.cloud.ibm.com/identity/token`. It should NOT use the raw API key directly. |
| `400 Bad Request` on token call | API key is wrong or expired | Double-check `API_KEY` in `.env` — no spaces, no quotes around the value |
| `JSONDecodeError` | LLM returned markdown instead of JSON | Check that `stop_sequences: ["` ``` `"]` is in `model_gateway.py` |
| Total Amount shows `$0.00` | Amounts are negative | Find `_normalize_row` in `doc_processing.py` — make sure `abs()` is applied to the amount |
| Wrong document type detected | Filename doesn't match keywords | Rename the PDF to include the right keyword — see Section 10 |
| Charts don't appear | Analyzed before submitting | Always click **Submit** first, then **Analyze** |
| Pie/donut chart error | Wrong Plotly layout applied | Bar and pie charts need separate layout configs — don't apply `xaxis`/`yaxis` to a pie chart |
| `TypeError: object.__init__()` | Python 3.14 + wrong install order | See Section 9 |
| Port 8501 already in use | Another app is on that port | Run `streamlit run app.py --server.port 8502` |
| First run takes forever | Docling downloading models | This is normal — wait 5–10 min, don't interrupt |
| `.env` file not found | File hidden or wrong name | Make sure the file is called `.env` (not `env.txt` or `.env.txt`) |
| `PROJECT_ID` not working | Wrong value copied | Should be 36 characters with dashes: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |

---

### How to check your `.env` file is correct

```bash
# Mac/Linux — print the file contents
cat .env

# Windows PowerShell
Get-Content .env
```

You should see your actual API key and Project ID, not the placeholder text. Make sure there are no quotes around the values:

```env
# ✅ Correct
API_KEY=abc123yourrealkeyhere

# ❌ Wrong — don't put quotes
API_KEY="abc123yourrealkeyhere"
```

---

### How to find a hidden `.env` file

`.env` files are hidden by default on most systems.

**Mac — show hidden files in Finder:**
Press `Cmd + Shift + .`

**Mac — open in text editor from terminal:**
```bash
open -e .env
```

**Windows — show hidden files in File Explorer:**
Go to **View** → check **Hidden items**

**Windows — open in Notepad:**
```powershell
notepad .env
```

---

## 9. Python 3.14 Special Setup

If `python3 --version` shows `3.14.x`, **do not run `pip install -r requirements.txt` directly** — it will fail.

Use this exact sequence instead:

```bash
# Step 1: Install uv (a faster, more compatible package manager)
pip install uv

# Step 2: Install pillow FIRST with binary-only flag
uv pip install pillow==11.3.0 --only-binary :all:

# Step 3: Install everything else
uv pip install -r requirements.txt
```

**Why does this happen?** Python 3.14 introduced binary compatibility changes that break how `pip` compiles certain packages (especially `pillow` and its dependencies). Installing `pillow` first with `--only-binary :all:` forces it to use a pre-compiled version, which unblocks the rest of the installation.

---

## 10. File Naming Tips

The app detects what kind of receipt a PDF is based on **keywords in the filename**.
If the filename has no recognizable keyword, it defaults to **Hotel**.

Name your PDF files to include one of these keywords:

| Receipt Type | Keywords to include in filename | Example filename |
|---|---|---|
| 🏨 Hotel | `hotel`, `inn`, `marriott`, `hilton`, `hyatt`, `sheraton`, `westin`, `fairmont`, `resort`, `lodge`, `accommodation` | `marriott_hotel_toronto.pdf` |
| ✈️ Flight | `flight`, `airline`, `boarding`, `airways` | `delta_flight_nyc.pdf` |
| 🍽️ Meal | `meal`, `restaurant`, `food`, `dining`, `cafe`, `bistro` | `lunch_restaurant_chicago.pdf` |
| 🚗 Car Rental | `car`, `rental`, `vehicle`, `hertz`, `avis`, `enterprise` | `hertz_car_rental.pdf` |

> 💡 **Tip**: Rename the sample PDFs in `sample-receipts/` before uploading if you want to test different document types.

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Check Python version | `python3 --version` |
| Install dependencies | `pip install -r requirements.txt` |
| Check imports | `python3 -c "import streamlit, pandas, plotly, docling, requests; print('OK')"` |
| Run the app | `streamlit run app.py` |
| Run if streamlit not found | `python3 -m streamlit run app.py` |
| Run on different port | `streamlit run app.py --server.port 8502` |
| App URL | http://localhost:8501 |

---

*Stuck? Ask your facilitator — or check the `solution/` folder as a last resort.* 🚀
