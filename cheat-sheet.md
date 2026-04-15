# 🛠️ Cheat Sheet — AI Travel Expense Tracker

Quick reference for credentials, commands, Bob prompts, and fixes.
If something breaks, start here before anything else.

---

## 📋 Table of Contents

1. [Credentials Setup](#1-credentials-setup)
2. [Terminal Commands](#2-terminal-commands)
3. [Validation Checks](#3-validation-checks)
4. [Bob Prompt Fixes](#4-bob-prompt-fixes)
5. [Troubleshooting — Error by Error](#5-troubleshooting--error-by-error)
6. [File Naming Rules](#6-file-naming-rules)
7. [Python 3.14 Special Setup](#7-python-314-special-setup)

---

## 1. Credentials Setup

### What goes in your `.env` file

```env
API_KEY=your_ibm_cloud_api_key_here
PROJECT_ID=your_watsonx_project_id_here
CLOUD_URL=https://us-south.ml.cloud.ibm.com
LLM_NAME=ibm/granite-3-8b-instruct
```

### CLOUD_URL by Region

| Region | URL |
|--------|-----|
| US South (Dallas) | `https://us-south.ml.cloud.ibm.com` |
| Canada (Toronto) | `https://ca-tor.ml.cloud.ibm.com` |
| Europe (Frankfurt) | `https://eu-de.ml.cloud.ibm.com` |
| UK (London) | `https://eu-gb.ml.cloud.ibm.com` |

> ⚠️ **Wrong region = 403 Forbidden error.** Check your region in IBM Cloud — top right corner next to your account name. If you're on a TechZone reservation, check the reservation details page.

### How to get your API Key

1. Go to [cloud.ibm.com](https://cloud.ibm.com) and sign in
2. Click your avatar (top right) → **Manage** → **Access (IAM)**
3. Left sidebar → **API keys** → **Create**
4. Give it any name (e.g. `bobathon-key`) → **Create**
5. ⚠️ Copy it **immediately** — it is shown only once. If you miss it, delete it and create a new one.

### How to get your Project ID

1. IBM Cloud → **Resource List** → under **AI / Machine Learning** → click your **watsonx.ai Runtime** instance
2. Click **Launch IBM watsonx**
3. On the home screen, find **Developer Access**
4. Select your project from the dropdown
5. Copy the **Project ID** — it is a 36-character UUID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

> ⚠️ **Truncated Project ID = 400 Bad Request.** Always verify the full 36 characters including hyphens.

### How to open your `.env` file to edit it

`.env` is a hidden file. You cannot double-click it — use one of these:

```bash
# Mac — opens in TextEdit
open -e .env

# Mac — opens in nano (terminal editor)
nano .env

# Windows
notepad .env
```

### How to update credentials when your IBM environment expires

Only the `.env` file needs to change — no code changes required.

```bash
# Open the file
open -e .env   # Mac
notepad .env   # Windows

# Replace API_KEY and PROJECT_ID with your new values
# Save and restart the app
streamlit run app.py
```

---

## 2. Terminal Commands

### Navigate to your project folder

```bash
# Mac / Linux
cd ~/Desktop/ai-travel-expense-tracker

# If your folder has a space in the name
cd ~/Desktop/Test\ Bob
# or
cd "/Users/yourname/Desktop/Test Bob"
```

> ⚠️ **Always run this first** every time you open a new Terminal window. If you skip it, you'll get "module not found" errors.

### Install dependencies

```bash
# Standard (Python 3.10–3.13)
pip install -r requirements.txt

# If pip3 is needed
pip3 install -r requirements.txt

# If you get permission errors
pip install -r requirements.txt --user
```

### Run the app

```bash
streamlit run app.py

# If 'streamlit' command not found
python3 -m streamlit run app.py

# If port 8501 is already in use
streamlit run app.py --server.port 8502
```

### Fix smart quote errors (one-time fix)

```bash
# If you get SyntaxError: invalid character '"' (U+201C)
python3 -c "
f = open('doc_processing.py', 'r', encoding='utf-8')
content = f.read()
f.close()
content = content.replace('\u201c', '\"').replace('\u201d', '\"').replace('\u2018', \"'\").replace('\u2019', \"'\")
f = open('doc_processing.py', 'w', encoding='utf-8')
f.write(content)
f.close()
print('Done!')
"
```

Run the same command for `app.py` or `model_gateway.py` if needed — just replace the filename.

### Show hidden files in Finder (Mac)

```
Cmd + Shift + .
```

---

## 3. Validation Checks

Run these **before** starting the app to catch problems early.

### Check Python version

```bash
python3 --version
# Expected: Python 3.10.x, 3.11.x, 3.12.x, or 3.13.x
# Python 3.14 works but needs special setup — see Section 7
```

### Check all packages are installed

```bash
python3 -c "import streamlit, pandas, plotly, docling, requests, dotenv; print('✅ All OK')"
# Expected: ✅ All OK
# If ModuleNotFoundError: run pip install -r requirements.txt again
```

### Test your API Key (Mac / Linux)

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://iam.cloud.ibm.com/identity/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_API_KEY"
```

Replace `YOUR_API_KEY` with your actual key.

| Output | Meaning |
|--------|---------|
| `200` | ✅ Key is valid |
| `400` | ❌ Malformed request — check for typos in the key |
| `401` | ❌ Key is invalid or deleted — generate a new one |

### Test your API Key (Windows PowerShell)

```powershell
$body = "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_API_KEY"
Invoke-RestMethod -Method Post `
  -Uri "https://iam.cloud.ibm.com/identity/token" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body $body | Select-Object token_type
# Expected: token_type = Bearer
```

### Test the full watsonx.ai connection

```bash
# Run from inside your project folder
python3 -c "
from model_gateway import invoke_llm
print(invoke_llm('Say hello in one sentence.'))
"
# Expected: Granite 3 replies with a sentence
```

### Check your `.env` file is correct

```bash
cat .env        # Mac / Linux
Get-Content .env  # Windows PowerShell
```

You should see your actual credentials, not placeholder text.

---

## 4. Bob Prompt Fixes

Paste these into Bob when something goes wrong with generated code.

### Fix: Missing return statement (Generate Summary button does nothing)

```
The generate_summary() function in app.py is not returning a value.
Find the invoke_llm() call inside generate_summary(), store the result
in a variable called summary, and add an explicit return statement:
    return summary
Return the complete fixed app.py.
```

### Fix: Smart / curly quotes causing SyntaxError

```
This file contains curly/smart quotes (" " ' ') instead of straight
ASCII quotes (" "). Python does not accept curly quotes as string
delimiters and throws a SyntaxError.

Replace all curly quotes with straight ASCII quotes throughout the
entire file. Use only straight " and ' characters everywhere.
Return the complete fixed file.
```

### Fix: Docling API error (do_ocr / do_table_structure arguments rejected)

```
The _pdf_to_markdown function is calling converter.convert() with
do_ocr and do_table_structure as direct arguments. These are no longer
accepted. Fix it to use PdfPipelineOptions instead:

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
result = converter.convert(tmp_path)

Return the complete fixed doc_processing.py.
```

### Fix: AI Summary returns Markdown symbols (**, ##, *, -)

```
The generate_summary() function in app.py sometimes receives a response
from the LLM that contains Markdown formatting like **, ##, *, -.
These appear as raw symbols in the Streamlit UI.

Make two changes:
1. In the prompt sent to invoke_llm(), add this instruction:
   "Do not use any markdown formatting, bullet points, headers, or
   bold text. Return plain text only."
2. After receiving the response, strip any remaining markdown symbols
   before returning: remove **, ##, *, and leading - characters.

Return the complete fixed app.py.
```

### Fix: Amount shows $0.00

```
The expense amounts in the extracted DataFrame are showing as $0.00.
This is caused by negative amounts in the LLM output.

In the _normalize_row() function in doc_processing.py, make sure
abs() is applied to the final amount value before it is added to the
row. Return the complete fixed doc_processing.py.
```

### Fix: Pie chart / donut chart error

```
The analyze_invoices() function is applying xaxis and yaxis layout
settings to a pie/donut chart, which causes an error. Pie charts
do not support xaxis/yaxis.

Separate the layout configuration: use one layout dict for bar charts
and a different layout dict for the pie/donut chart. Do not apply
xaxis or yaxis to any pie or donut chart.
Return the complete fixed doc_processing.py.
```

### Fix: Bob's output looks cut off / incomplete

```
The file you generated appears to be incomplete. Please regenerate the
full [model_gateway.py / doc_processing.py / app.py] with all functions
fully implemented. Do not truncate, summarize, or skip any section.
Return only the complete file.
```

### Add to every Bob prompt (preventive)

Add this line at the end of any prompt to prevent common issues:

```
Use only straight ASCII quotes (" and ') in all code. Do not use curly
or smart quotes. Include all return statements explicitly.
```

---

## 5. Troubleshooting — Error by Error

### App errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'docling'` | Dependencies not installed | `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'dotenv'` | python-dotenv not installed | `pip install python-dotenv` |
| `streamlit: command not found` | Streamlit not on PATH | Use `python3 -m streamlit run app.py` |
| `SyntaxError: invalid character '"' (U+201C)` | Bob generated curly quotes | Run the smart quote fix command in Section 2 |
| `SyntaxError: invalid syntax` | Bob generated broken code | Paste the file back into Bob: *"Fix all syntax errors. Return the complete file."* |
| `NameError: name 'X' is not defined` | Missing import or undefined function | Paste the error + full file into Bob: *"Fix this error. Return the complete file."* |
| Port 8501 already in use | Another app is running | `streamlit run app.py --server.port 8502` |

### API / credential errors

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | API Key invalid or not exchanged for token | Check `model_gateway.py` uses IAM token exchange (POST to `iam.cloud.ibm.com/identity/token`). Regenerate API Key if needed. |
| `403 Forbidden` | Wrong region URL | Check `CLOUD_URL` in `.env` matches your IBM Cloud region. See region table in Section 1. |
| `403 Forbidden` (even after fixing region) | API Key does not have access to this project | Go to IBM Cloud → IAM → check the API Key has access to your watsonx.ai project |
| `400 Bad Request` on token call | API Key malformed or truncated | Check `.env` — no spaces, no quotes around the value, full key copied |
| `400 Bad Request` on watsonx call | Project ID is wrong or truncated | Verify `PROJECT_ID` in `.env` is exactly 36 characters: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `JSONDecodeError` | LLM returned markdown fences instead of JSON | Check `stop_sequences: ["` ``` `"]` is in `model_gateway.py` |

### Data / output issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Total Amount shows `$0.00` | LLM returned negative amounts, `abs()` missing | See Bob fix prompt in Section 4 |
| Wrong document type detected | PDF filename doesn't match keywords | Rename file — see Section 6 |
| Generate Summary button does nothing | `return` statement missing in `generate_summary()` | See Bob fix prompt in Section 4 |
| Summary shows `**bold**` or `### headers` | LLM returned Markdown | See Bob fix prompt in Section 4 |
| Charts don't appear | Clicked Analyze before Submit | Always click **Submit** first, then **Analyze** |
| Pie chart crashes the app | Wrong Plotly layout applied | See Bob fix prompt in Section 4 |
| App shows blank page / no content | Streamlit state issue | Refresh the browser tab |
| First run takes 5–10 minutes | Docling downloading ~2GB of ML models | Normal — wait, do not interrupt. Subsequent runs are instant. |
| `.env` file not found | File has wrong name or wrong extension | Make sure it is exactly `.env` — not `env.txt`, `.env.txt`, or `env` |

### Installation issues

| Error | Cause | Fix |
|-------|-------|-----|
| `TypeError: object.__init__() takes exactly one argument` | Python 3.14 + IBM SDK | Use REST API in `model_gateway.py`, not the SDK. See Section 7. |
| `ERROR: Failed to build pillow` | Python 3.14 binary incompatibility | See Section 7 — install pillow with `--only-binary :all:` first |
| `pip takes forever / resolution too deep` | Dependency conflict | Use `uv` instead: `pip install uv && uv pip install -r requirements.txt` |
| `pip install` fails with permissions error | System Python | Add `--user` flag: `pip install -r requirements.txt --user` |

---

## 6. File Naming Rules

The app detects document type from the **PDF filename**. If the filename doesn't contain the right keyword, the wrong extraction prompt is used and results will be inaccurate.

| Document Type | Keywords that trigger it |
|---------------|--------------------------|
| Hotel | `hotel`, `inn`, `marriott`, `hilton`, `hyatt`, `sheraton`, `westin`, `fairmont`, `resort`, `lodge`, `accommodation` |
| Flight | `flight`, `airline`, `boarding`, `airways` |
| Meal | `meal`, `restaurant`, `food`, `dining`, `cafe`, `bistro` |
| Car Rental | `car`, `rental`, `vehicle`, `hertz`, `avis`, `enterprise` |
| Generic | anything that doesn't match the above |

**Good examples:**
```
marriott_hotel_nov2024.pdf     ✅ detected as Hotel
delta_flight_receipt.pdf       ✅ detected as Flight
uber_eats_meal.pdf             ✅ detected as Meal
hertz_car_rental.pdf           ✅ detected as Car Rental
```

**Bad examples:**
```
receipt_001.pdf                ⚠️ detected as Generic
invoice.pdf                    ⚠️ detected as Generic
scan_20241103.pdf              ⚠️ detected as Generic
```

---

## 7. Python 3.14 Special Setup

Python 3.14 has binary compatibility issues with some packages. Use this install sequence instead of the standard one.

```bash
# Step 1 — Install uv package manager
pip install uv

# Step 2 — Install pillow with binary-only flag FIRST, before anything else
uv pip install pillow==11.3.0 --only-binary :all:

# Step 3 — Install everything else
uv pip install -r requirements.txt
```

> ⚠️ Do NOT run `pip install -r requirements.txt` normally on Python 3.14 — it will fail with a pillow build error. Always follow the three steps above in order.

Also make sure your `model_gateway.py` uses the **REST API**, not the IBM SDK. The SDK (`ibm-watsonx-ai`) is incompatible with Python 3.14. If Bob generated an SDK-based version, paste this into Bob:

```
Rewrite model_gateway.py to connect to IBM watsonx.ai using the REST API only.
Do not import or use ibm-watsonx-ai or any IBM SDK packages.
Use only: requests, python-dotenv, and standard library modules.
Return the complete rewritten file.
```

---

*Built for IBM Bobathon · Powered by IBM Bob and watsonx.ai Granite 3*
