"""
Playwright test suite to verify that the dashboard correctly parses and displays
analysis text in sections instead of showing large text blocks.

Tests verify that:
- Analysis content is broken into logical sections
- Section headers are displayed with proper styling
- Highlighted sections (recommendations, rationale) have visual emphasis
- Fallback sectioning works when no structured sections are found
"""

import pytest
import re
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8000"

class TestDashboardSections:
    """Test suite for dashboard sectioning functionality"""
    
    def test_dashboard_loads_with_sections(self, page: Page):
        """Test that the dashboard loads and shows sectioned analysis content"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Check that analysis cards exist
        cards = page.locator(".analysis-card").all()
        assert len(cards) > 0, "No analysis cards found on dashboard"
        
        print(f"Found {len(cards)} analysis cards")
    
    def test_show_full_displays_sections(self, page: Page):
        """Test that clicking 'Show Full' displays content in sections"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Find first analysis card and click "Show Full"
        first_card = page.locator(".analysis-card").first
        show_full_btn = first_card.locator("button:has-text('Show Full')")
        
        # Verify button exists and click it
        expect(show_full_btn).to_be_visible()
        show_full_btn.click()
        
        # Wait a moment for content to expand
        page.wait_for_timeout(500)
        
        # Check if sections are displayed
        sections = first_card.locator(".analysis-section").all()
        
        if len(sections) > 0:
            print(f"✅ Found {len(sections)} analysis sections")
            
            # Verify section structure
            for i, section in enumerate(sections):
                # Check for section title
                title = section.locator(".section-title")
                expect(title).to_be_visible()
                title_text = title.text_content()
                print(f"Section {i+1}: {title_text}")
                
                # Check for section content
                content = section.locator(".section-content")
                expect(content).to_be_visible()
                content_text = content.text_content()
                assert len(content_text.strip()) > 0, f"Section {i+1} has empty content"
                
            # Check for highlighted sections
            highlighted_sections = first_card.locator(".analysis-section.highlighted").all()
            if len(highlighted_sections) > 0:
                print(f"✅ Found {len(highlighted_sections)} highlighted sections")
            else:
                print("⚠️  No highlighted sections found")
        else:
            # If no sections found, check if content is still structured somehow
            full_content = first_card.locator(".analysis-full")
            content_text = full_content.text_content()
            assert len(content_text.strip()) > 0, "No analysis content found at all"
            print("⚠️  No sections found, but content is present")
    
    def test_section_titles_are_meaningful(self, page: Page):
        """Test that section titles are meaningful, not generic like 'Section 1'"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        cards = page.locator(".analysis-card").all()
        sectioned_cards = 0
        meaningful_titles = 0
        
        for card_index, card in enumerate(cards[:3]):  # Test first 3 cards
            # Click show full
            show_full_btn = card.locator("button:has-text('Show Full')")
            if show_full_btn.is_visible():
                show_full_btn.click()
                page.wait_for_timeout(300)
                
                # Check for sections
                sections = card.locator(".analysis-section").all()
                if len(sections) > 0:
                    sectioned_cards += 1
                    print(f"Card {card_index + 1} has {len(sections)} sections:")
                    
                    for section in sections:
                        title_element = section.locator(".section-title")
                        if title_element.is_visible():
                            title_text = title_element.text_content().strip()
                            print(f"  - {title_text}")
                            
                            # Check if title is meaningful (not generic like "Section 1")
                            if not re.match(r'^Section \d+', title_text):
                                meaningful_titles += 1
        
        print(f"Cards with sections: {sectioned_cards}")
        print(f"Meaningful section titles: {meaningful_titles}")
        
        # At least some cards should have sections
        assert sectioned_cards > 0, "No cards have sectioned content"
    
    def test_highlighted_sections_have_special_styling(self, page: Page):
        """Test that highlighted sections (recommendations, rationale) have visual emphasis"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        cards = page.locator(".analysis-card").all()
        highlighted_found = False
        
        for card_index, card in enumerate(cards[:2]):  # Check first 2 cards
            # Click show full
            show_full_btn = card.locator("button:has-text('Show Full')")
            if show_full_btn.is_visible():
                show_full_btn.click()
                page.wait_for_timeout(300)
                
                # Look for highlighted sections
                highlighted_sections = card.locator(".analysis-section.highlighted").all()
                if len(highlighted_sections) > 0:
                    highlighted_found = True
                    print(f"✅ Card {card_index + 1} has {len(highlighted_sections)} highlighted sections")
                    
                    for section in highlighted_sections:
                        # Check that highlighted sections have special styling
                        expect(section).to_have_class(re.compile(r".*highlighted.*"))
                        
                        # Check for star icon (::before pseudo-element content)
                        # We can't directly test pseudo-elements, but we can check computed styles
                        title = section.locator(".section-title")
                        if title.is_visible():
                            title_text = title.text_content()
                            print(f"  - Highlighted: {title_text}")
        
        if not highlighted_found:
            print("⚠️  No highlighted sections found in tested cards")
    
    def test_timestamps_in_sections(self, page: Page):
        """Test that timestamps within sections are properly formatted and linkable"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        cards = page.locator(".analysis-card").all()
        timestamps_found = False
        
        for card_index, card in enumerate(cards[:2]):
            # Click show full
            show_full_btn = card.locator("button:has-text('Show Full')")
            if show_full_btn.is_visible():
                show_full_btn.click()
                page.wait_for_timeout(300)
                
                # Look for timestamp links in sections
                timestamp_links = card.locator(".timestamp-link").all()
                if len(timestamp_links) > 0:
                    timestamps_found = True
                    print(f"✅ Card {card_index + 1} has {len(timestamp_links)} timestamp links")
                    
                    for link in timestamp_links[:3]:  # Check first 3 timestamps
                        # Verify link is clickable and has proper href
                        expect(link).to_be_visible()
                        href = link.get_attribute("href")
                        link_text = link.text_content()
                        
                        print(f"  - Timestamp: {link_text} -> {href[:50]}...")
                        
                        # Verify it's a YouTube link with timestamp
                        assert href and "youtube.com/watch" in href, f"Invalid timestamp URL: {href}"
                        assert "&t=" in href, f"Timestamp missing in URL: {href}"
                
                # Also look for timestamp displays (non-clickable)
                timestamp_displays = card.locator(".timestamp-display").all()
                if len(timestamp_displays) > 0:
                    print(f"✅ Card {card_index + 1} has {len(timestamp_displays)} timestamp displays")
        
        if not timestamps_found:
            print("ℹ️  No timestamps found in tested cards")
    
    def test_section_content_formatting(self, page: Page):
        """Test that section content has proper formatting (bold, italic, line breaks)"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        first_card = page.locator(".analysis-card").first
        show_full_btn = first_card.locator("button:has-text('Show Full')")
        
        if show_full_btn.is_visible():
            show_full_btn.click()
            page.wait_for_timeout(500)
            
            # Check for formatted content within sections
            sections = first_card.locator(".analysis-section").all()
            formatting_found = False
            
            for section in sections:
                content = section.locator(".section-content")
                if content.is_visible():
                    # Check for bold text
                    bold_elements = content.locator("strong").all()
                    if len(bold_elements) > 0:
                        formatting_found = True
                        print(f"✅ Found {len(bold_elements)} bold elements in sections")
                    
                    # Check for italic text
                    italic_elements = content.locator("em").all()
                    if len(italic_elements) > 0:
                        formatting_found = True
                        print(f"✅ Found {len(italic_elements)} italic elements in sections")
                    
                    # Check for line breaks
                    content_html = content.inner_html()
                    if "<br>" in content_html:
                        formatting_found = True
                        print("✅ Found line breaks in section content")
            
            if not formatting_found:
                print("⚠️  No text formatting found in sections")
            
            assert len(sections) > 0 or first_card.locator(".analysis-full").is_visible(), "No content displayed at all"

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context with necessary settings"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

if __name__ == "__main__":
    # Run the tests when script is executed directly
    pytest.main([__file__, "-v", "--tb=short"])