# Demo Public Project

This folder contains a safe public demo of the internal license-control concept.

## What is included

- Synthetic CSV datasets (`data/`)
- Python generator (`src/generate_demo_dashboard.py`)
- Generated static HTML dashboards (`output/`)

## Run locally

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
python src/generate_demo_dashboard.py
python src/capture_screenshots.py
```

After execution, open `output/home.html`.

## Screenshots

![Demo Home](screenshots/01-home.png)
![Demo Site North](screenshots/02-site-north.png)
![Demo Site East](screenshots/03-site-east.png)
![Demo Site South](screenshots/04-site-south.png)

## Notes

- No real names, real emails, internal links, or company branding are used here.
- The objective is to demonstrate architecture, flow, and visualization only.
