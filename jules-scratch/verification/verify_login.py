from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:5173/login")
    page.get_by_placeholder("Username").fill("jules")
    page.get_by_placeholder("Password").fill("verne")
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("http://localhost:5173/dashboard")
    page.screenshot(path="jules-scratch/verification/dashboard.png")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
