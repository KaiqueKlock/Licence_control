# Demo Public Project

This folder contains a safe public demo of the internal license-control concept.

## What is included

- Synthetic CSV datasets (`data/`)
- Python generator (`src/generate_demo_dashboard.py`)
- Generated static HTML dashboards (`output/`)

## Run locally

```bash
python -m pip install -r requirements.txt
python src/generate_demo_dashboard.py
```

After execution, open `output/home.html`.

## Notes

- No real names, real emails, internal links, or company branding are used here.
- The objective is to demonstrate architecture, flow, and visualization only.
