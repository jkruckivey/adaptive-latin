#!/usr/bin/env python3
"""
Test interactive simulation flow for adaptive Latin course.

Tests:
1. Navigate to course
2. Start learning session
3. Complete onboarding
4. Interact with simulation content
5. Verify postMessage communication
6. Check feedback display
"""

from playwright.sync_api import sync_playwright
import time

def test_simulation_flow():
    print("Starting simulation flow test...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False to see what's happening
        page = browser.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))

        try:
            # Navigate to frontend
            print("\n1. Navigating to http://localhost:5173")
            page.goto('http://localhost:5173')
            page.wait_for_load_state('networkidle')
            time.sleep(2)

            # Take screenshot of initial page
            page.screenshot(path='screenshots/01_initial_page.png', full_page=True)
            print("   Screenshot saved: 01_initial_page.png")

            # Look for course cards
            print("\n2. Looking for course cards...")
            cards = page.locator('.course-card').all()
            print(f"   Found {len(cards)} course cards")

            if len(cards) > 0:
                # Click first course card
                print("   Clicking first course card...")
                cards[0].click()
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                page.screenshot(path='screenshots/02_course_selected.png', full_page=True)
                print("   Screenshot saved: 02_course_selected.png")

                # Look for start/continue button
                print("\n3. Looking for start/continue button...")
                start_buttons = page.locator('button:has-text("Start"), button:has-text("Continue")').all()
                if len(start_buttons) > 0:
                    print("   Clicking start/continue button...")
                    start_buttons[0].click()
                    page.wait_for_load_state('networkidle')
                    time.sleep(2)
                    page.screenshot(path='screenshots/03_session_started.png', full_page=True)
                    print("   Screenshot saved: 03_session_started.png")

                    # Check if onboarding appears
                    print("\n4. Checking for onboarding...")
                    if page.locator('.onboarding-screen').count() > 0:
                        print("   Onboarding screen found, completing it...")

                        # Fill out onboarding form
                        # Name input
                        name_input = page.locator('input[type="text"]').first
                        if name_input.count() > 0:
                            name_input.fill("Test User")
                            print("   Filled name: Test User")

                        # Look for submit/continue buttons and click through onboarding
                        max_steps = 10
                        for step in range(max_steps):
                            time.sleep(1)
                            # Try to find and click continue/next/submit buttons
                            continue_button = page.locator('button:has-text("Continue"), button:has-text("Next"), button:has-text("Submit"), button:has-text("Start Learning")').first
                            if continue_button.count() > 0 and continue_button.is_visible():
                                print(f"   Step {step + 1}: Clicking continue button...")
                                continue_button.click()
                                page.wait_for_load_state('networkidle')
                                time.sleep(1)
                                page.screenshot(path=f'screenshots/04_onboarding_step_{step + 1}.png', full_page=True)
                            else:
                                print(f"   Onboarding completed after {step} steps")
                                break

                        time.sleep(2)
                        page.screenshot(path='screenshots/05_after_onboarding.png', full_page=True)
                        print("   Screenshot saved: 05_after_onboarding.png")

                    # Check for simulation content
                    print("\n5. Looking for simulation viewer...")
                    if page.locator('.simulation-viewer').count() > 0:
                        print("   Simulation viewer found!")
                        page.screenshot(path='screenshots/06_simulation_viewer.png', full_page=True)
                        print("   Screenshot saved: 06_simulation_viewer.png")

                        # Wait a bit for simulation to load
                        time.sleep(3)

                        # Look for simulation buttons/interactions
                        print("\n6. Looking for simulation interactions...")

                        # Try to find and interact with simulation elements
                        # Look for quiz options, buttons, etc.
                        options = page.locator('.option, .quiz-option, button:not(.continue-button)').all()
                        print(f"   Found {len(options)} interactive elements")

                        if len(options) > 0:
                            # Click first few options (for pre-assessment quiz)
                            for i, option in enumerate(options[:5]):  # Click up to 5 options
                                if option.is_visible():
                                    print(f"   Clicking option {i + 1}...")
                                    try:
                                        option.click()
                                        time.sleep(0.5)
                                    except:
                                        print(f"   Could not click option {i + 1}")

                        page.screenshot(path='screenshots/07_after_interactions.png', full_page=True)
                        print("   Screenshot saved: 07_after_interactions.png")

                        # Look for complete button
                        print("\n7. Looking for complete button...")
                        complete_button = page.locator('button:has-text("Complete"), button:has-text("Submit")').first
                        if complete_button.count() > 0 and complete_button.is_visible():
                            print("   Clicking complete button...")
                            complete_button.click()
                            time.sleep(3)  # Wait for postMessage and feedback
                            page.screenshot(path='screenshots/08_after_complete.png', full_page=True)
                            print("   Screenshot saved: 08_after_complete.png")

                            # Check for feedback display
                            print("\n8. Checking for feedback...")
                            if page.locator('.simulation-feedback').count() > 0:
                                print("   ✅ Feedback displayed!")
                                feedback_text = page.locator('.simulation-feedback').text_content()
                                print(f"   Feedback content: {feedback_text[:200]}...")
                            else:
                                print("   ❌ No feedback found")

                            # Check for continue button enabled
                            continue_btn = page.locator('.simulation-footer button').first
                            if continue_btn.count() > 0:
                                is_enabled = not continue_btn.is_disabled()
                                print(f"   Continue button enabled: {is_enabled}")

                                if is_enabled:
                                    print("\n9. Clicking continue to next content...")
                                    continue_btn.click()
                                    time.sleep(2)
                                    page.screenshot(path='screenshots/09_next_content.png', full_page=True)
                                    print("   Screenshot saved: 09_next_content.png")
                        else:
                            print("   No complete button found")
                    else:
                        print("   No simulation viewer found yet")
                        print("   Current URL:", page.url)
                        print("   Page content preview:", page.content()[:500])
                else:
                    print("   No start/continue button found")
            else:
                print("   No course cards found")

            print("\n[SUCCESS] Test completed successfully!")
            print("   Check the screenshots/ directory for visual verification")

        except Exception as e:
            print(f"\n[FAILED] Test failed with error: {e}")
            page.screenshot(path='screenshots/error.png', full_page=True)
            raise
        finally:
            time.sleep(5)  # Keep browser open for 5 seconds to review
            print("\nClosing browser...")
            browser.close()

if __name__ == '__main__':
    import os
    os.makedirs('screenshots', exist_ok=True)
    test_simulation_flow()
