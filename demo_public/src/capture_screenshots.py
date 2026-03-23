from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright


VIEWPORT = {"width": 1600, "height": 1000}


def to_file_url(path: Path) -> str:
    return f"file:///{quote(str(path.resolve()).replace('\\', '/'))}"


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    output_dir = base_dir / "output"
    screenshots_dir = base_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    pages = [
        ("home.html", "01-home.png"),
        ("index_SITE_NORTH.html", "02-site-north.png"),
        ("index_SITE_EAST.html", "03-site-east.png"),
        ("index_SITE_SOUTH.html", "04-site-south.png"),
    ]

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(viewport=VIEWPORT)
        page = context.new_page()

        for html_name, png_name in pages:
            html_path = output_dir / html_name
            if not html_path.exists():
                print(f"Skipped (not found): {html_path}")
                continue

            page.goto(to_file_url(html_path), wait_until="networkidle")
            page.wait_for_timeout(350)
            destination = screenshots_dir / png_name
            page.screenshot(path=str(destination), full_page=True)
            print(f"Saved: {destination}")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
