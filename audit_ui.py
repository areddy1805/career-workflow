from playwright.sync_api import sync_playwright
import time
import os

ARTIFACT_DIR = "/Users/ashwinireddy/.gemini/antigravity-ide/brain/1462eaab-39de-4ab2-b395-bc04018e2a6e/scratch"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(color_scheme="dark", viewport={"width": 1280, "height": 800})
        page = context.new_page()

        print("Navigating to Providers...")
        page.goto("http://localhost:5174/providers")
        time.sleep(3)
        page.screenshot(path=f"{ARTIFACT_DIR}/providers.png")
        print("Providers screenshot saved.")
        
        # Check if table exists
        if page.locator("table").count() > 0:
            print("Table found on providers page")
        else:
            print("Table NOT found on providers page. Text on page:")
            print(page.locator("body").inner_text())

        print("Navigating to Queues...")
        page.goto("http://localhost:5174/queues")
        time.sleep(3)
        page.screenshot(path=f"{ARTIFACT_DIR}/queues.png")
        print("Queues screenshot saved.")

        print("Navigating to Search Intelligence...")
        page.goto("http://localhost:5174/search")
        time.sleep(3)
        page.screenshot(path=f"{ARTIFACT_DIR}/search.png")
        print("Search Intelligence screenshot saved.")

        browser.close()

if __name__ == "__main__":
    run()
