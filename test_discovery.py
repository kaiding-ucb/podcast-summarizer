#!/usr/bin/env python3

import asyncio
from playwright.async_api import async_playwright
import json
import sys

async def test_discovery():
    """Test that Forward Guidance videos appear after clicking 'discover new videos'"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)  # Set to True for headless mode
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🌐 Navigating to application...")
            # Navigate to the discover page
            await page.goto("http://localhost:8000/discover")
            await page.wait_for_load_state('networkidle')
            
            print("🔍 Looking for discover button...")
            # Look for the discover new videos button - check multiple possible selectors
            discover_button = None
            
            # Try different possible selectors for the discover button
            selectors = [
                '#discoverBtn',  # Most specific selector
                'button:has-text("Discover New Videos")',
                'button:has-text("Discover")',
                '[onclick*="discoverVideos"]',
                '[onclick*="discover"]',
                '.btn:has-text("Discover")'
            ]
            
            for selector in selectors:
                try:
                    discover_button = await page.wait_for_selector(selector, timeout=2000)
                    if discover_button:
                        print(f"✅ Found discover button with selector: {selector}")
                        break
                except:
                    continue
            
            if not discover_button:
                # Let's examine the page content to understand the structure
                print("🔍 Could not find discover button, examining page content...")
                content = await page.content()
                print("📄 Page HTML preview:")
                print(content[:1000] + "..." if len(content) > 1000 else content)
                
                # Try to find any clickable elements
                buttons = await page.query_selector_all('button')
                inputs = await page.query_selector_all('input[type="button"], input[type="submit"]')
                links = await page.query_selector_all('a')
                
                print(f"🔘 Found {len(buttons)} buttons, {len(inputs)} inputs, {len(links)} links")
                
                # Print text content of clickable elements
                for i, button in enumerate(buttons):
                    text = await button.text_content()
                    print(f"  Button {i}: '{text}'")
                
                for i, input_elem in enumerate(inputs):
                    value = await input_elem.get_attribute('value')
                    print(f"  Input {i}: '{value}'")
                
                # Look for any element containing "discover" text
                discover_elements = await page.query_selector_all('*:has-text("discover")')
                for i, elem in enumerate(discover_elements):
                    text = await elem.text_content()
                    tag = await elem.evaluate('el => el.tagName')
                    print(f"  Element with 'discover' {i}: {tag} - '{text}'")
                
                return False, "Could not find discover button"
            
            print("🖱️  Clicking discover button...")
            # Click the discover button
            await discover_button.click()
            
            # Wait for the API call to complete and page to update
            print("⏳ Waiting for discovery to complete...")
            await page.wait_for_timeout(5000)  # Wait 5 seconds for API call
            
            # Check the page content for Forward Guidance videos
            print("🔍 Checking for Forward Guidance videos...")
            content = await page.content()
            
            # Look for Forward Guidance in the page content
            forward_guidance_found = "Forward Guidance" in content
            
            if forward_guidance_found:
                print("✅ SUCCESS: Forward Guidance videos found on the page!")
                
                # Try to count how many Forward Guidance videos we found
                forward_guidance_count = content.count("Forward Guidance")
                print(f"📊 Found {forward_guidance_count} references to Forward Guidance")
                
                return True, f"Found {forward_guidance_count} Forward Guidance videos"
            else:
                print("❌ FAILED: No Forward Guidance videos found")
                
                # Check if Prof G Markets videos are present (to verify the discovery worked at all)
                prof_g_found = "Prof G Markets" in content
                if prof_g_found:
                    prof_g_count = content.count("Prof G Markets")
                    print(f"⚠️  Found {prof_g_count} Prof G Markets videos but no Forward Guidance")
                    return False, f"Discovery worked (found {prof_g_count} Prof G Markets videos) but no Forward Guidance videos"
                else:
                    print("❌ No videos found at all - discovery may have failed")
                    return False, "No videos found - discovery failed completely"
            
        except Exception as e:
            print(f"❌ ERROR during test: {e}")
            return False, f"Test error: {e}"
        
        finally:
            await browser.close()

async def main():
    print("🚀 Starting Forward Guidance discovery test...")
    success, message = await test_discovery()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 TEST PASSED!")
    else:
        print("💥 TEST FAILED!")
    print(f"📝 Result: {message}")
    print(f"{'='*50}")
    
    return success

if __name__ == "__main__":
    # Install playwright if needed
    import subprocess
    import os
    
    try:
        import playwright
    except ImportError:
        print("📦 Installing playwright...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.run([sys.executable, "-m", "playwright", "install"])
        import playwright
    
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)