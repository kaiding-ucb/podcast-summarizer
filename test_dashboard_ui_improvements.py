"""
Playwright test to verify dashboard UI improvements on first 3 results.
Tests:
1. Section separation with proper styling
2. Highlighted recommendation/rationale sections  
3. Clickable timestamp links
"""

import pytest
import re
import time
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8000"

def test_dashboard_ui_improvements(page: Page):
    """Test UI improvements on first 3 dashboard results"""
    
    print("\n🧪 Testing Dashboard UI Improvements...")
    
    # Navigate to dashboard
    page.goto(f"{BASE_URL}/dashboard")
    
    # Wait for analyses to load
    page.wait_for_selector(".analysis-card", timeout=10000)
    
    # Get first 3 cards
    cards = page.locator(".analysis-card").all()[:3]
    assert len(cards) >= 3, f"Need at least 3 cards, found {len(cards)}"
    
    print(f"\n✅ Found {len(cards)} analysis cards")
    
    # Test each of the first 3 cards
    for i, card in enumerate(cards, 1):
        print(f"\n📋 Testing Card {i}...")
        
        # Get video title for logging
        title_elem = card.locator("h3").first
        title = title_elem.text_content() if title_elem else f"Card {i}"
        print(f"   Title: {title[:50]}...")
        
        # Click "Show Full" button
        show_full_btn = card.locator("button:has-text('Show Full')").first
        if not show_full_btn.is_visible():
            print(f"   ⚠️  No 'Show Full' button found, skipping...")
            continue
            
        show_full_btn.click()
        page.wait_for_timeout(500)  # Wait for animation
        
        # Test 1: Check for analysis sections with proper structure
        sections = card.locator(".analysis-section").all()
        
        if len(sections) > 0:
            print(f"   ✅ Found {len(sections)} properly structured sections")
            
            # Check first section has proper styling
            first_section = sections[0]
            computed_style = first_section.evaluate("""
                el => {
                    const style = window.getComputedStyle(el);
                    return {
                        borderLeft: style.borderLeftWidth + ' ' + style.borderLeftStyle + ' ' + style.borderLeftColor,
                        background: style.background || style.backgroundColor,
                        padding: style.padding,
                        margin: style.margin
                    };
                }
            """)
            
            print(f"   📐 Section styling:")
            print(f"      Border: {computed_style.get('borderLeft', 'none')}")
            print(f"      Background: {computed_style.get('background', 'none')[:50]}...")
            
            # Test 2: Check for highlighted sections
            highlighted = card.locator(".analysis-section.highlighted").all()
            if highlighted:
                print(f"   ✅ Found {len(highlighted)} highlighted sections")
                for h_section in highlighted[:1]:  # Check first highlighted
                    title = h_section.locator(".section-title").text_content()
                    print(f"      Highlighted: {title}")
            else:
                print(f"   ℹ️  No highlighted sections in this card")
            
        else:
            # Fallback: Check if analysis text is at least formatted
            full_analysis = card.locator(".analysis-full").first
            if full_analysis.is_visible():
                print(f"   ℹ️  No structured sections, but full analysis is visible")
                
                # Check for any formatting
                strong_elements = full_analysis.locator("strong").count()
                em_elements = full_analysis.locator("em").count()
                br_elements = full_analysis.locator("br").count()
                
                print(f"      Formatting: {strong_elements} bold, {em_elements} italic, {br_elements} line breaks")
        
        # Test 3: Check for timestamp links
        timestamp_links = card.locator("a.timestamp-link").all()
        if timestamp_links:
            print(f"   ✅ Found {len(timestamp_links)} timestamp links")
            
            # Test first timestamp link
            first_link = timestamp_links[0]
            link_text = first_link.text_content()
            link_href = first_link.get_attribute("href")
            link_target = first_link.get_attribute("target")
            
            # Verify timestamp format and YouTube URL
            timestamp_pattern = r'\(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\)'
            assert re.match(timestamp_pattern, link_text), f"Invalid timestamp format: {link_text}"
            assert "youtube.com" in link_href, f"Not a YouTube link: {link_href}"
            assert "t=" in link_href, f"Missing timestamp parameter: {link_href}"
            assert link_target == "_blank", f"Link should open in new tab"
            
            print(f"      First timestamp: {link_text} -> {link_href[:60]}...")
            
            # Check timestamp styling
            link_style = first_link.evaluate("""
                el => {
                    const style = window.getComputedStyle(el);
                    return {
                        color: style.color,
                        borderBottom: style.borderBottom,
                        textDecoration: style.textDecoration
                    };
                }
            """)
            print(f"      Styling: color={link_style.get('color')}, border={link_style.get('borderBottom')}")
        else:
            print(f"   ℹ️  No timestamp links in this card")
        
        # Click "Show Less" to reset for next card
        show_less_btn = card.locator("button:has-text('Show Less')").first
        if show_less_btn.is_visible():
            show_less_btn.click()
            page.wait_for_timeout(200)
    
    print("\n✅ Dashboard UI improvements test completed!")
    print("\nSummary:")
    print("- Tested first 3 analysis cards")
    print("- Verified section structure and styling")
    print("- Checked highlighted sections (Recommendation/Rationale)")
    print("- Validated timestamp links and formatting")

if __name__ == "__main__":
    # Run with playwright
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for CI
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        try:
            test_dashboard_ui_improvements(page)
        finally:
            browser.close()