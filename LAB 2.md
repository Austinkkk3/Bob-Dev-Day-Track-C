# 🎉 What's Next — Bonus Lab

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

