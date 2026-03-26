# ✈️ AI Travel Expense Tracker — Bobathon Lab

> **Build an AI-powered expense tracker in 150 minutes using IBM Bob and watsonx.ai.**
> Upload travel receipts → AI extracts and categorizes every line item → Export to CSV.

---

## What You'll Build

A working Streamlit web application that:

- 📄 Accepts PDF receipts — hotels, flights, meals, and car rentals
- 🤖 Uses IBM watsonx.ai (Granite 3) to extract structured expense data automatically
- 📊 Generates interactive charts: by vendor, by category, by document type
- 💾 Exports all extracted data as a CSV file

You will use **IBM Bob** to generate all the code from scratch. No copy-pasting from tutorials — you describe what you want, Bob builds it.

---

## Before You Start

### What you need

| Requirement | Notes |
|---|---|
| IBM Bob installed | Download from your Techzone environment |
| Python 3.10–3.13 | Check with `python3 --version` |
| IBM Cloud account | Free tier is fine — sign up at [cloud.ibm.com](https://cloud.ibm.com) |
| 5 GB free disk space | Docling downloads ~2 GB of ML models on first run |
| Stable internet | Required for model downloads and API calls |

> ⚠️ **Python 3.14 users**: Special setup required — see the [Cheat Sheet](cheat-sheet.md#python-314-setup).

### Credentials you'll need

You need two things from IBM Cloud before writing any code:

1. **IBM Cloud API Key** — [How to get it →](cheat-sheet.md#getting-your-ibm-cloud-api-key)
2. **watsonx.ai Project ID** — [How to get it →](cheat-sheet.md#getting-your-watsonxai-project-id)

Get these ready before the lab starts. It takes about 5 minutes.

---

## Lab Overview (150 minutes)

```
Phase 1 — Setup         (~25 min)   Get credentials, create project folder
Phase 2 — Build with Bob (~85 min)   Prompt Bob to generate all 4 files
Phase 3 — Run & Test    (~40 min)   Install, launch, upload sample receipts
```

---

## Phase 1 — Setup (15 min)

### 1. Get your credentials

Follow the steps in the [Cheat Sheet](cheat-sheet.md) to get your:
- IBM Cloud API Key
- watsonx.ai Project ID

### 2. Create your project folder

```bash
mkdir ai-travel-expense-tracker
cd ai-travel-expense-tracker
```

### 3. Create your `.env` file

Copy the template below, paste it into a file called `.env`, and fill in your credentials:

```env
# IBM watsonx.ai — fill in your values
API_KEY=paste_your_api_key_here
PROJECT_ID=paste_your_project_id_here
CLOUD_URL=https://us-south.ml.cloud.ibm.com
LLM_NAME=ibm/granite-3-8b-instruct
```

> 📌 **Region note**: If your IBM Cloud is not in US South, update `CLOUD_URL`.
> See [Region URLs →](cheat-sheet.md#cloud-url-by-region)

Or use the pre-filled template: [`.env.template`](.env.template)

---

## Phase 2 — Build with Bob (55 min)

You will prompt Bob to generate **4 files**. Work through them in order.

### File 1 — `requirements.txt` (~2 min)

Open Bob and use this prompt:

```
Create a requirements.txt file for a Streamlit app that uses:
- streamlit
- pandas
- plotly
- docling
- python-dotenv
- requests
```

### File 2 — `model_gateway.py` (~10 min)

```
Create a Python module called model_gateway.py that connects to IBM watsonx.ai.

Requirements:
- Use the REST API directly (NOT the ibm-watsonx-ai SDK)
- Load API_KEY, PROJECT_ID, CLOUD_URL, and LLM_NAME from a .env file
- Implement IAM token exchange: POST to https://iam.cloud.ibm.com/identity/token
- Cache the token for 50 minutes (IBM tokens expire after 60 minutes)
- Expose a single function: invoke_llm(prompt: str) -> str
- Use these generation parameters: max_new_tokens=2048, temperature=0.0,
  repetition_penalty=1.05, stop_sequences=["```"]
```

> 💡 **Why REST API, not SDK?** The SDK has compatibility issues with Python 3.14. The REST API works on all versions. See [Cheat Sheet →](cheat-sheet.md#why-rest-api-not-sdk)

### File 3 — `doc_processing.py` (~20 min)

```
Create a Python module called doc_processing.py that processes PDF receipts.

Requirements:
- Use Docling to convert PDFs to Markdown (disable OCR, enable table structure)
- Detect document type from filename keywords:
    hotel/inn/marriott/hilton/hyatt/accommodation → "hotel" (highest priority, default)
    flight/airline/boarding → "flight"
    meal/restaurant/food/dining → "meal"
    car/rental/vehicle → "car"
- Each document type gets its own LLM extraction prompt
- Extract these fields: date, vendor, doc_type, category, description,
  currency, amount, confidence
- Parse amounts robustly (handle $, €, £, commas, European format 1.234,56)
- Always use abs() on amounts (expenses are always positive)
- Parse JSON from LLM output safely using regex to find the [...] array
- Return a pandas DataFrame with columns:
  Date, Vendor, Doc Type, Category, Description, Currency, Amount, Confidence
- Add an analyze_invoices(df) function that returns 3 Plotly charts:
    1. Horizontal bar chart — expenses by vendor
    2. Donut chart — expenses by category
    3. Bar chart — expenses by document type, using these colors:
       Hotel=#3B82F6, Flight=#A855F7, Meal=#10B981, Car Rental=#F59E0B
```

### File 4 — `app.py` (~20 min)

```
Create a Streamlit application called app.py for an AI Travel Expense Tracker.

Requirements:
- Import from doc_processing and model_gateway
- Page config: title "AI Travel Expense Tracker", icon ✈️, wide layout
- Hero banner with gradient background showing the app name and subtitle
- File uploader: accepts PDF files, up to 10 at once
- Three buttons: Submit (primary), Analyze (secondary), Export CSV (download)
- Use session_state to persist the DataFrame between button clicks
- On Submit: call process_invoices(), show success message
- Show metrics: Files Processed, Line Items, Total Amount, Avg Confidence
- Show a styled dataframe with emoji column headers
- On Analyze: call analyze_invoices(), display 3 charts using st.plotly_chart
- AI chat assistant at the bottom: answers questions about the expense data
  using invoke_llm(), maintains chat history in session_state
- Custom CSS: Inter font, white cards, light gray background (#F1F5F9)
- Do NOT include Astra DB or any database integration
```

---

## Phase 3 — Run & Test (20 min)

### 1. Validate your setup

Run these three checks before installing anything:

```bash
# Check Python version (should be 3.10–3.13)
python3 --version

# Test your API Key (should return 200)
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://iam.cloud.ibm.com/identity/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_API_KEY"
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **First-time install**: Docling has many dependencies. This may take a few minutes.

### 3. Launch the app

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

> ⚠️ **First run**: Docling downloads ~2 GB of ML models. Wait 5–10 minutes. Do not close the terminal.

### 4. Test with sample receipts

Sample PDFs are in the [`sample-receipts/`](sample-receipts/) folder. Upload them to try the app.

---

## Troubleshooting

See the full troubleshooting table in the **[Cheat Sheet](cheat-sheet.md#troubleshooting)**.

Quick fixes for the most common issues:

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `401 Unauthorized` | Check your API Key in `.env` — no extra spaces or quotes |
| Total amount shows `$0.00` | Ask Bob to add `abs()` to the amount parsing in `doc_processing.py` |
| Wrong document type detected | Rename the file to include the keyword (e.g. `marriott_hotel.pdf`) |
| First run takes forever | Normal — Docling is downloading models. Wait it out. |
| `streamlit: command not found` | Use `python3 -m streamlit run app.py` instead |

---

## Project Structure

```
ai-travel-expense-tracker/
├── requirements.txt       # Python dependencies
├── .env                   # Your credentials (never commit this)
├── model_gateway.py       # IBM watsonx.ai REST API layer
├── doc_processing.py      # PDF parsing + LLM extraction + charts
└── app.py                 # Streamlit UI
```



## 🎉 You Built It — What's Next?

Now that your tracker is running, try using Bob's **Plan Mode** 
to extend it further.

Some ideas to explore:

- 💬 Add an AI chat assistant that answers questions about your expenses
- 🗄️ Connect a database to store receipts across sessions (Astra DB)
- 📧 Auto-generate an expense report email
- 🚨 Add a policy checker that flags expenses over a certain amount
- 🌍 Add currency conversion for international receipts

**How to use Plan Mode:**
Open Bob → switch to **Plan** → describe what you want to add →
Bob will map out the approach before writing any code.
It's great for features you're not sure how to structure yet.
---

## Reference

- 📋 [Cheat Sheet](cheat-sheet.md) — Bob prompts, credentials, troubleshooting
- 🔧 [env.Template](env.template) — Pre-formatted credentials file
- 📄 [Invoice](invoice) — Test PDFs to try the app
- 💡 [Solution](solution/) — Reference implementation if you get stuck

---

## Need Help?

1. Check the [Cheat Sheet](cheat-sheet.md) first
2. Ask your session facilitator
3. Look at the [solution](solution/) folder as a last resort

---

*Built for IBM Bobathon · Powered by IBM watsonx.ai Granite 3 · Made with Bob*
