#!/usr/bin/env python3
"""
Playwright test to verify dashboard improvements are working correctly.
This script will:
1. Navigate to the dashboard
2. Wait for analyses to load
3. Click "Show Full" on the first analysis
4. Take a screenshot
5. Verify the expected elements are present
"""

import asyncio
import sys
from playwright.async_api import async_playwright
import json

async def test_dashboard_improvements():
    async with async_playwright() as p:
        # Launch browser in headless mode to avoid manual interference
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("🚀 Starting dashboard improvements test...")
            
            # Step 1: Navigate to dashboard
            print("📍 Step 1: Navigating to http://127.0.0.1:8000/dashboard")
            await page.goto('http://127.0.0.1:8000/dashboard')
            await page.wait_for_load_state('networkidle')
            
            # Step 2: Wait for analyses to appear
            print("⏳ Step 2: Waiting for analysis cards to load...")
            try:
                await page.wait_for_selector('.analysis-card', timeout=10000)
                analysis_cards = await page.query_selector_all('.analysis-card')
                print(f"✅ Found {len(analysis_cards)} analysis cards")
                
                if len(analysis_cards) == 0:
                    print("❌ No analysis cards found! The dashboard might be empty.")
                    await page.screenshot(path='dashboard_no_analyses.png')
                    return False
                    
            except Exception as e:
                print(f"❌ Failed to find analysis cards: {e}")
                await page.screenshot(path='dashboard_loading_error.png')
                return False
            
            # Step 3: Find and click "Show Full" on first analysis
            print("🔍 Step 3: Looking for 'Show Full' button...")
            try:
                # Look for toggle button with "Show Full" text
                toggle_buttons = await page.query_selector_all('button[onclick*="toggleAnalysis"]')
                if not toggle_buttons:
                    print("❌ No toggle buttons found!")
                    await page.screenshot(path='no_toggle_buttons.png')
                    return False
                
                first_toggle = toggle_buttons[0]
                toggle_text = await first_toggle.inner_text()
                print(f"📖 Found toggle button with text: '{toggle_text}'")
                
                if "Show Full" not in toggle_text:
                    print(f"⚠️  Expected 'Show Full' but found: '{toggle_text}'")
                
                print("👆 Clicking 'Show Full' button...")
                await first_toggle.click()
                await page.wait_for_timeout(2000)  # Wait for content to expand
                
            except Exception as e:
                print(f"❌ Failed to click Show Full: {e}")
                await page.screenshot(path='show_full_error.png')
                return False
            
            # Step 4: Take screenshot of current state
            print("📸 Step 4: Taking screenshot of expanded analysis...")
            await page.screenshot(path='dashboard_expanded_analysis.png', full_page=True)
            
            # Step 5: Verify expected elements
            print("🔍 Step 5: Verifying dashboard improvements...")
            
            # Check for .analysis-section elements
            analysis_sections = await page.query_selector_all('.analysis-section')
            print(f"📊 Found {len(analysis_sections)} .analysis-section elements")
            
            # Check for .timestamp-link elements
            timestamp_links = await page.query_selector_all('.timestamp-link')
            print(f"🔗 Found {len(timestamp_links)} .timestamp-link elements")
            
            # Check for highlighted sections
            highlighted_sections = await page.query_selector_all('.analysis-section.highlighted')
            print(f"⭐ Found {len(highlighted_sections)} highlighted sections")
            
            # Detailed analysis of the first expanded analysis
            full_analysis_divs = await page.query_selector_all('[id^="full-"]')
            if full_analysis_divs:
                first_full_div = full_analysis_divs[0]
                is_visible = await first_full_div.is_visible()
                print(f"👁️  First full analysis div visibility: {is_visible}")
                
                if is_visible:
                    # Get the HTML content to analyze structure
                    full_content = await first_full_div.inner_html()
                    
                    # Count sections and their titles
                    sections_with_titles = await first_full_div.query_selector_all('.analysis-section h3')
                    section_titles = []
                    for section in sections_with_titles:
                        title = await section.inner_text()
                        section_titles.append(title)
                    
                    print(f"📝 Section titles found: {section_titles}")
                    
                    # Check if content looks organized vs big text block
                    raw_text_length = len(await first_full_div.inner_text())
                    html_complexity = full_content.count('<div') + full_content.count('<h3') + full_content.count('<br')
                    
                    print(f"📏 Text length: {raw_text_length} characters")
                    print(f"🏗️  HTML complexity score: {html_complexity}")
                    
                    # Test timestamp link functionality
                    if timestamp_links:
                        first_link = timestamp_links[0]
                        href = await first_link.get_attribute('href')
                        target = await first_link.get_attribute('target')
                        link_text = await first_link.inner_text()
                        print(f"🎯 First timestamp link: '{link_text}' -> {href} (target: {target})")
                else:
                    print("❌ Full analysis div is not visible after clicking Show Full")
            
            # Summary report
            print("\n" + "="*60)
            print("📋 DASHBOARD IMPROVEMENTS TEST SUMMARY")
            print("="*60)
            
            success_indicators = 0
            total_checks = 6
            
            if len(analysis_sections) > 0:
                print("✅ Analysis sections found (.analysis-section)")
                success_indicators += 1
            else:
                print("❌ No analysis sections found - JavaScript sectioning may not be working")
            
            if len(timestamp_links) > 0:
                print("✅ Timestamp links found (.timestamp-link)")
                success_indicators += 1
            else:
                print("❌ No timestamp links found - timestamp parsing may not be working")
            
            if len(highlighted_sections) > 0:
                print("✅ Highlighted sections found (important sections)")
                success_indicators += 1
            else:
                print("⚠️  No highlighted sections found - may be normal depending on content")
                success_indicators += 0.5  # Half point as this depends on content
            
            if len(section_titles) > 0:
                print(f"✅ Section titles found: {', '.join(section_titles)}")
                success_indicators += 1
            else:
                print("❌ No section titles found - content may not have proper headers")
            
            if full_analysis_divs and is_visible:
                print("✅ Show Full functionality working")
                success_indicators += 1
            else:
                print("❌ Show Full functionality not working properly")
            
            if html_complexity > 20:  # Arbitrary threshold for "organized" content
                print("✅ Content appears well-structured (high HTML complexity)")
                success_indicators += 1
            else:
                print("❌ Content may be a big text block (low HTML complexity)")
            
            success_rate = (success_indicators / total_checks) * 100
            print(f"\n🎯 Success Rate: {success_rate:.1f}% ({success_indicators}/{total_checks})")
            
            if success_rate >= 80:
                print("🎉 Dashboard improvements are working well!")
                result = True
            elif success_rate >= 50:
                print("⚠️  Dashboard improvements partially working - some issues detected")
                result = True
            else:
                print("❌ Dashboard improvements need debugging")
                result = False
                
            print("\n📸 Screenshots saved:")
            print("  - dashboard_expanded_analysis.png (main result)")
            if len(analysis_cards) == 0:
                print("  - dashboard_no_analyses.png (empty dashboard)")
            
            return result
            
        except Exception as e:
            print(f"💥 Unexpected error during test: {e}")
            await page.screenshot(path='dashboard_test_error.png')
            return False
            
        finally:
            await browser.close()

if __name__ == "__main__":
    print("🧪 Dashboard Improvements Playwright Test")
    print("==========================================")
    
    # Check if server is running
    print("🔍 Checking if server is running at http://127.0.0.1:8000...")
    import requests
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        print("✅ Server is responding")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not responding: {e}")
        print("💡 Please make sure the FastAPI server is running:")
        print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")
        sys.exit(1)
    
    # Run the test
    result = asyncio.run(test_dashboard_improvements())
    
    if result:
        print("\n🎊 Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test found issues that need attention")
        sys.exit(1)