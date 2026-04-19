import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Import strict types explicitly designed to match instructor expectations
from schema import FundSource, FundRecord


FUNDS: List[FundSource] = [
    {"name": "HDFC Mid-Cap Opportunities Fund", "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"},
    {"name": "HDFC Flexi Cap Fund", "url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"},
    {"name": "HDFC Focused 30 Fund", "url": "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth"},
    {"name": "HDFC ELSS Tax Saver Fund", "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"},
    {"name": "HDFC Top 100 Fund (Large Cap)", "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"},
    {"name": "Nippon India Large Cap Fund", "url": "https://groww.in/mutual-funds/nippon-india-large-cap-fund-direct-growth"},
    {"name": "Nippon India Growth Fund (Mid Cap)", "url": "https://groww.in/mutual-funds/nippon-india-growth-mid-cap-fund-direct-growth"},
    {"name": "Nippon India Multi Cap Fund", "url": "https://groww.in/mutual-funds/nippon-india-multi-cap-fund-direct-growth"},
    {"name": "Nippon India Power & Infra Fund", "url": "https://groww.in/mutual-funds/nippon-india-power-infra-fund-direct-growth"}
]

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(DATA_DIR, exist_ok=True)

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted tags containing non-content or duplicate semantics
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "iframe"]):
        tag.decompose()
        
    text = soup.get_text(separator=' ', strip=True)
    return text

def extract_key_metrics(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    metrics = {
        "nav": "Data Unavailable",
        "min_sip": "Data Unavailable",
        "fund_size": "Data Unavailable",
        "expense_ratio": "Data Unavailable",
        "rating": "Data Unavailable"
    }
    
    # Heuristic scraping: search the DOM's linear text stream for the labels 
    # and extract the immediate next textual value (since Groww renders them as adjacent UI spans/divs)
    texts = list(soup.stripped_strings)
    
    for i, txt in enumerate(texts):
        lower_txt = txt.lower()
        # Ensure we don't go out of bounds
        if i + 1 >= len(texts): break
        
        # Look for exact or highly probable label matches
        if lower_txt == "nav" and metrics["nav"] == "Data Unavailable":
            metrics["nav"] = texts[i+1]
        elif lower_txt == "min. sip amount" and metrics["min_sip"] == "Data Unavailable":
            metrics["min_sip"] = texts[i+1]
        elif lower_txt == "fund size" and metrics["fund_size"] == "Data Unavailable":
            metrics["fund_size"] = texts[i+1]
        elif lower_txt == "expense ratio" and metrics["expense_ratio"] == "Data Unavailable":
            metrics["expense_ratio"] = texts[i+1]
        elif "rating" in lower_txt and metrics["rating"] == "Data Unavailable":
            metrics["rating"] = texts[i+1]
            
    return metrics

def run_scraper():
    results = []
    print("Starting Groww mutual fund scraper...")
    print(f"Data will be saved to: {DATA_DIR}")
    
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        # Using a custom User-Agent mapping a modern browser prevents generic BOT blocking
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for fund in FUNDS:
            print(f"Scraping: {fund['name']}...")
            try:
                # Networkidle ensures that JS frameworks complete fetching their data payloads
                page.goto(fund["url"], wait_until="networkidle", timeout=30000)
                
                content = page.content()
                clean_text = clean_html(content)
                metrics = extract_key_metrics(content)
                
                # Type enforce the strictly designed record dictionary
                record: FundRecord = {
                    "fund_name": fund["name"],
                    "source_url": fund["url"],
                    "document_type": "Webpage Content",
                    "last_updated_date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "nav": metrics["nav"],
                    "min_sip": metrics["min_sip"],
                    "fund_size": metrics["fund_size"],
                    "expense_ratio": metrics["expense_ratio"],
                    "rating": metrics["rating"],
                    "raw_text": clean_text
                }
                
                timestamp = datetime.utcnow().strftime("%Y%m%d")
                
                # Make filename filesystem safe
                safe_name = "".join([c if c.isalnum() else "_" for c in fund['name']])
                filename = f"{safe_name}_{timestamp}.json"
                filepath = os.path.join(DATA_DIR, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
                    
                results.append(filename)
                print(f"  -> Saved text ({len(clean_text)} characters) to {filename}")

            except Exception as e:
                print(f"  -> Error fetching {fund['name']}: {e}")
                
        browser.close()
    print("Scraping completed.")

if __name__ == "__main__":
    run_scraper()
