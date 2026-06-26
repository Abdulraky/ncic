# NCIC Intelligence Lab

Lightweight Streamlit app for NCIC forensic evidence aggregation from X (Twitter) via Apify.

Quick start

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run locally:

```bash
streamlit run "ncic_app.py"
```

3. For live scraping, paste your Apify API token in the sidebar. If not provided, the app runs in simulation mode.

Notes

- Exports are saved to the `data/` folder as timestamped JSON files for audit.
- The app ships with a tiny TF-IDF + LogisticRegression classifier trained at startup; replace or improve with a production model as needed.
- Review legal text and admissibility claims with NCIC counsel before using in production.

Docker

Build:

```bash
docker build -t ncic-intel .
```

Run:

```bash
docker run -p 8501:8501 ncic-intel
```
