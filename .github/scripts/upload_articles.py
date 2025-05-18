import os
import requests
from docx import Document
from pathlib import Path

# WordPress environment variables
WP_URL = os.environ["WP_URL"]
WP_USER = os.environ["WP_USER"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]

# Path to the articles directory
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent
ARTICLES_DIR = SCRIPT_DIR / "articles"

def extract_text(docx_path):
    """Extracts text content from a .docx file"""
    doc = Document(docx_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def get_or_create_category(category_name):
    """Fetches the category ID or creates it in WordPress"""
    categories_url = WP_URL.replace("/posts", "/categories")
    print(WP_USER)
    # Check if category exists
    res = requests.get(categories_url, auth=(WP_USER, WP_APP_PASSWORD), params={"search": category_name})
    if res.status_code == 200 and res.json():
        return res.json()[0]["id"]

    # Create category
    res = requests.post(categories_url, auth=(WP_USER, WP_APP_PASSWORD), json={"name": category_name})
    if res.status_code == 201:
        return res.json()["id"]
    else:
        raise Exception(f"Failed to create category '{category_name}': {res.text}")

def upload_article(file_path):
    """Uploads a single article as a WordPress post"""
    content = extract_text(file_path)
    title = file_path.stem.replace("-", " ").title()
    category_name = file_path.parent.name

    try:
        category_id = get_or_create_category(category_name)
    except Exception as e:
        print(f"❌ Category error for {file_path.name}: {e}")
        return

    post_data = {
        "title": title,
        "content": content,
        "categories": [category_id],
        "status": "publish"
    }

    res = requests.post(WP_URL, auth=(WP_USER, WP_APP_PASSWORD), json=post_data)

    if res.status_code == 201:
        print(f"✅ {file_path.name} published as post ID {res.json()['id']}")
    else:
        print(f"❌ Failed to publish {file_path.name}: {res.status_code} - {res.text}")

def main():
    print("🔍 Checking environment variables...")
    wp_user = os.environ.get("WP_USER")
    wp_pass = os.environ.get("WP_APP_PASSWORD")

    if wp_user and wp_pass:
        print(f"✅ WP_USER loaded: {wp_user}")
        print("✅ WP_APP_PASSWORD is set.")
    else:
        print("❌ Environment variables missing!")
        return
    if not ARTICLES_DIR.exists():
        print(f"❌ Articles folder not found: {ARTICLES_DIR}")
        return

    docx_files = list(ARTICLES_DIR.rglob("*.docx"))
    if not docx_files:
        print("⚠️ No .docx files found to upload.")
        return

    for docx_file in docx_files:
        upload_article(docx_file)

if __name__ == "__main__":
    main()
