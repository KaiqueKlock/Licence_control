from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import html
import re

import pandas as pd


PROJECT_TITLE = "Access and License Control - Demo"
STATUS_ORDER = ["Active", "Warning", "Inactive", "No record"]
STATUS_CLASS = {
    "Active": "badge-active",
    "Warning": "badge-warning",
    "Inactive": "badge-inactive",
    "No record": "badge-neutral",
}


def make_safe_id(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().upper())
    clean = re.sub(r"_+", "_", clean).strip("_")
    return clean or "UNASSIGNED"


def parse_days_without_login(value: str) -> int | None:
    if not value or str(value).strip() == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    delta = datetime.now(timezone.utc).date() - parsed.date()
    return max(delta.days, 0)


def classify_status(days_without_login: int | None) -> str:
    if days_without_login is None:
        return "No record"
    if days_without_login <= 45:
        return "Active"
    if days_without_login <= 90:
        return "Warning"
    return "Inactive"


def status_counters(df: pd.DataFrame) -> dict[str, int]:
    counts = {status: 0 for status in STATUS_ORDER}
    for status, value in df["status"].value_counts().items():
        counts[status] = int(value)
    return counts


def enrich_user_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["display_name"] = out["display_name"].fillna("").replace("", "Unknown User")
    out["email"] = out["email"].fillna("").replace("", "unknown@example.com")
    out["location"] = out["location"].fillna("").replace("", "UNASSIGNED")
    out["department"] = out["department"].fillna("").replace("", "Not informed")
    out["last_logon"] = out["last_logon"].fillna("")
    out["days_without_login"] = out["last_logon"].map(parse_days_without_login)
    out["status"] = out["days_without_login"].map(classify_status)
    return out


def summarize_by_dimension(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[dimension, "Records", "Active", "Warning", "Inactive", "No record"]
        )

    rows: list[dict[str, int | str]] = []
    for key, part in df.groupby(dimension, dropna=False):
        row = {dimension: key, "Records": int(len(part))}
        counts = status_counters(part)
        row.update(counts)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(by=["Records", dimension], ascending=[False, True])


def dataframe_to_html(df: pd.DataFrame, column_order: list[str], rename_map: dict[str, str]) -> str:
    if df.empty:
        return '<p class="empty-state">No records in this section.</p>'

    view = df.loc[:, column_order].copy()
    view = view.rename(columns=rename_map)
    if "Status" in view.columns:
        view["Status"] = view["Status"].map(
            lambda value: (
                f'<span class="badge {STATUS_CLASS.get(value, "badge-neutral")}">'
                f"{html.escape(str(value))}</span>"
            )
        )
    if "Days without login" in view.columns:
        view["Days without login"] = view["Days without login"].map(
            lambda value: "-" if pd.isna(value) else int(value)
        )
    return view.to_html(index=False, classes="table", border=0, escape=False)


def build_location_page(
    location: str,
    infra_loc: pd.DataFrame,
    sap_loc: pd.DataFrame,
    generated_at: str,
) -> str:
    merged = pd.concat([infra_loc[["status"]], sap_loc[["status"]]], ignore_index=True)
    counters = status_counters(merged) if not merged.empty else {status: 0 for status in STATUS_ORDER}

    infra_summary = summarize_by_dimension(infra_loc, "service_name")
    sap_summary = summarize_by_dimension(sap_loc, "sap_module")

    infra_table = dataframe_to_html(
        infra_loc,
        ["display_name", "user_id", "service_name", "department", "last_logon", "days_without_login", "status"],
        {
            "display_name": "Display name",
            "user_id": "User",
            "service_name": "Service",
            "department": "Department",
            "last_logon": "Last logon",
            "days_without_login": "Days without login",
            "status": "Status",
        },
    )
    sap_table = dataframe_to_html(
        sap_loc,
        ["display_name", "user_id", "sap_module", "profile_type", "last_logon", "days_without_login", "status"],
        {
            "display_name": "Display name",
            "user_id": "User",
            "sap_module": "SAP module",
            "profile_type": "Profile",
            "last_logon": "Last logon",
            "days_without_login": "Days without login",
            "status": "Status",
        },
    )
    infra_summary_html = dataframe_to_html(
        infra_summary,
        ["service_name", "Records", "Active", "Warning", "Inactive", "No record"],
        {"service_name": "Service"},
    )
    sap_summary_html = dataframe_to_html(
        sap_summary,
        ["sap_module", "Records", "Active", "Warning", "Inactive", "No record"],
        {"sap_module": "SAP module"},
    )

    location_safe = html.escape(location)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{PROJECT_TITLE} - {location_safe}</title>
  <style>
    :root {{
      --bg: #f3f5f8;
      --card: #ffffff;
      --text: #102a43;
      --muted: #627d98;
      --primary: #125d98;
      --primary-soft: #d9ebf9;
      --success: #1f8f4e;
      --warning: #c07a00;
      --danger: #b42318;
      --neutral: #5d6b82;
      --border: #d9e2ec;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    .page {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }}
    .header {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 20px;
      box-shadow: 0 4px 14px rgba(16, 42, 67, 0.08);
      margin-bottom: 16px;
    }}
    .header h1 {{ margin: 0 0 8px 0; font-size: 26px; }}
    .header p {{ margin: 0; color: var(--muted); }}
    .header-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .link-btn {{
      background: var(--primary);
      color: #fff;
      text-decoration: none;
      padding: 10px 14px;
      border-radius: 8px;
      font-weight: 600;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
      margin: 14px 0 18px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      text-align: center;
    }}
    .card .label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; }}
    .card .value {{ margin-top: 6px; font-size: 26px; font-weight: 700; }}
    .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0 12px; }}
    .tab {{
      border: 1px solid var(--border);
      background: var(--card);
      color: var(--text);
      border-radius: 8px;
      padding: 8px 12px;
      cursor: pointer;
      font-weight: 600;
    }}
    .tab.active {{ background: var(--primary); color: #fff; border-color: var(--primary); }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 4px 14px rgba(16, 42, 67, 0.08);
      padding: 12px;
      display: none;
    }}
    .panel.active {{ display: block; }}
    .section-title {{ margin: 4px 0 10px; }}
    .table {{
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      font-size: 14px;
    }}
    .table th, .table td {{
      border: 1px solid var(--border);
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }}
    .table th {{
      background: var(--primary-soft);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }}
    .badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 3px 8px;
      color: #fff;
      font-size: 12px;
      font-weight: 700;
    }}
    .badge-active {{ background: var(--success); }}
    .badge-warning {{ background: var(--warning); }}
    .badge-inactive {{ background: var(--danger); }}
    .badge-neutral {{ background: var(--neutral); }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
      margin-bottom: 14px;
    }}
    .empty-state {{ color: var(--muted); font-style: italic; }}
    @media (min-width: 980px) {{
      .grid-2 {{ grid-template-columns: 1fr 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="header">
      <div class="header-row">
        <div>
          <h1>{location_safe}</h1>
          <p>{PROJECT_TITLE}</p>
        </div>
        <a href="home.html" class="link-btn">Back to home</a>
      </div>
      <div class="cards">
        <article class="card"><div class="label">Active</div><div class="value">{counters["Active"]}</div></article>
        <article class="card"><div class="label">Warning</div><div class="value">{counters["Warning"]}</div></article>
        <article class="card"><div class="label">Inactive</div><div class="value">{counters["Inactive"]}</div></article>
        <article class="card"><div class="label">No record</div><div class="value">{counters["No record"]}</div></article>
      </div>
      <p>Generated at {generated_at} UTC</p>
    </section>

    <div class="tabs">
      <button class="tab active" onclick="showPanel('overview', this)">Overview</button>
      <button class="tab" onclick="showPanel('infra', this)">Infra licenses</button>
      <button class="tab" onclick="showPanel('sap', this)">SAP licenses</button>
    </div>

    <section id="overview" class="panel active">
      <h3 class="section-title">Overview by service</h3>
      <div class="grid-2">
        <div>
          <h4>Infrastructure</h4>
          {infra_summary_html}
        </div>
        <div>
          <h4>SAP</h4>
          {sap_summary_html}
        </div>
      </div>
    </section>

    <section id="infra" class="panel">
      <h3 class="section-title">Infrastructure license details</h3>
      {infra_table}
    </section>

    <section id="sap" class="panel">
      <h3 class="section-title">SAP license details</h3>
      {sap_table}
    </section>
  </div>

  <script>
    function showPanel(panelId, button) {{
      const panels = document.querySelectorAll(".panel");
      const tabs = document.querySelectorAll(".tab");
      panels.forEach((panel) => panel.classList.remove("active"));
      tabs.forEach((tab) => tab.classList.remove("active"));
      document.getElementById(panelId).classList.add("active");
      button.classList.add("active");
    }}
  </script>
</body>
</html>
"""


def build_home_page(cards_html: str, generated_at: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{PROJECT_TITLE} - Home</title>
  <style>
    :root {{
      --bg: #f2f4f7;
      --card: #ffffff;
      --text: #1d2939;
      --muted: #667085;
      --primary: #175cd3;
      --border: #d0d5dd;
    }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, sans-serif;
      background: radial-gradient(circle at top right, #dce9ff 0%, var(--bg) 40%);
      color: var(--text);
    }}
    .wrapper {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px;
    }}
    .hero {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 18px;
      box-shadow: 0 5px 16px rgba(16, 24, 40, 0.1);
    }}
    .hero h1 {{ margin: 0 0 8px; font-size: 30px; }}
    .hero p {{ margin: 0; color: var(--muted); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 12px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 4px 12px rgba(16, 24, 40, 0.08);
    }}
    .card h2 {{ margin: 2px 0 10px; font-size: 18px; }}
    .meta {{ color: var(--muted); font-size: 13px; margin: 4px 0; }}
    .btn {{
      display: inline-block;
      margin-top: 10px;
      text-decoration: none;
      background: var(--primary);
      color: white;
      padding: 8px 12px;
      border-radius: 8px;
      font-weight: 600;
    }}
  </style>
</head>
<body>
  <main class="wrapper">
    <section class="hero">
      <h1>{PROJECT_TITLE}</h1>
      <p>Parallel demo project with synthetic data only.</p>
      <p>Generated at {generated_at} UTC.</p>
    </section>
    <section class="grid">
      {cards_html}
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    users = pd.read_csv(data_dir / "users_directory.csv", dtype=str).fillna("")
    licenses = pd.read_csv(data_dir / "license_inventory.csv", dtype=str).fillna("")
    sap = pd.read_csv(data_dir / "sap_assignments.csv", dtype=str).fillna("")

    infra = enrich_user_data(licenses.merge(users, on="user_id", how="left"))
    sap_access = enrich_user_data(sap.merge(users, on="user_id", how="left"))

    locations = sorted(
        set(infra["location"].dropna().tolist()) | set(sap_access["location"].dropna().tolist())
    )
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    cards: list[str] = []

    for location in locations:
        location_id = make_safe_id(location)
        infra_loc = infra[infra["location"] == location].copy()
        sap_loc = sap_access[sap_access["location"] == location].copy()

        unique_users = (
            pd.concat([infra_loc["user_id"], sap_loc["user_id"]], ignore_index=True)
            .dropna()
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )
        total_records = len(infra_loc) + len(sap_loc)
        warning_or_inactive = int(
            (pd.concat([infra_loc["status"], sap_loc["status"]], ignore_index=True).isin(["Warning", "Inactive"])).sum()
        )
        cards.append(
            f"""
<article class="card">
  <h2>{html.escape(location)}</h2>
  <p class="meta">Unique users: {unique_users}</p>
  <p class="meta">Total records: {total_records}</p>
  <p class="meta">Warning + Inactive: {warning_or_inactive}</p>
  <a class="btn" href="index_{location_id}.html">Open dashboard</a>
</article>
""".strip()
        )

        location_html = build_location_page(location, infra_loc, sap_loc, generated_at)
        (output_dir / f"index_{location_id}.html").write_text(location_html, encoding="utf-8")

    home_html = build_home_page("\n".join(cards), generated_at)
    (output_dir / "home.html").write_text(home_html, encoding="utf-8")
    print(f"Demo pages generated in: {output_dir}")


if __name__ == "__main__":
    main()
