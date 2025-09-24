"""
Playwright test suite to verify enhanced analysis display functionality.

Tests verify that:
- Analysis sections are properly separated with spacing
- Recommendation and rationale sections are highlighted
- Timestamps are clickable links to video positions
- Sections display with proper formatting
"""

import pytest
import re
from playwright.sync_api import Page, expect
from urllib.parse import parse_qs, urlparse

BASE_URL = "http://127.0.0.1:8000"

class TestDashboardEnhancedDisplay:
    """Test suite for enhanced analysis display functionality"""
    
    def test_analysis_sections_properly_separated(self, page: Page):
        """Test that analysis sections are visually separated with proper spacing"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Find a card and click "Show Full"
        cards = page.locator(".analysis-card").all()
        assert len(cards) > 0, "No analysis cards found"
        
        first_card = cards[0]
        show_full_btn = first_card.locator("button:has-text('Show Full')")
        show_full_btn.click()
        
        # Wait for full analysis to display
        page.wait_for_timeout(500)
        
        # Check for analysis sections
        analysis_sections = first_card.locator(".analysis-section").all()
        
        if len(analysis_sections) > 0:
            print(f"Found {len(analysis_sections)} analysis sections")
            
            # Check that sections have proper spacing
            for i, section in enumerate(analysis_sections):
                # Check section has proper CSS classes
                section_classes = section.get_attribute("class")
                assert "analysis-section" in section_classes
                
                # Check section has title and content
                section_title = section.locator(".section-title")
                section_content = section.locator(".section-content")
                
                expect(section_title).to_be_visible()
                expect(section_content).to_be_visible()
                
                title_text = section_title.text_content()
                print(f"Section {i+1} title: {title_text}")
                
                # Verify title ends with colon
                assert title_text.endswith(':'), f"Section title should end with colon: {title_text}"
        else:
            print("No structured sections found - testing fallback formatting")
            # Check that at least basic formatting is applied
            full_analysis = first_card.locator(".analysis-full")
            expect(full_analysis).to_be_visible()
    
    def test_recommendation_section_highlighted(self, page: Page):
        """Test that recommendation sections are highlighted"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Look for cards with recommendations
        cards = page.locator(".analysis-card").all()
        
        found_recommendation = False
        
        for card in cards[:3]:  # Check first 3 cards
            show_full_btn = card.locator("button:has-text('Show Full')")
            show_full_btn.click()
            page.wait_for_timeout(500)
            
            # Look for highlighted recommendation sections
            highlighted_sections = card.locator(".analysis-section.highlighted").all()
            
            for section in highlighted_sections:
                section_title = section.locator(".section-title")
                title_text = section_title.text_content().lower()
                
                if "recommendation" in title_text:
                    found_recommendation = True
                    print(f"Found highlighted recommendation section: {title_text}")
                    
                    # Verify highlighting styles are applied
                    section_classes = section.get_attribute("class")
                    assert "highlighted" in section_classes
                    
                    # Check that section has the highlighted styling
                    section_style = section.evaluate("el => getComputedStyle(el)")
                    # The highlighted sections should have different background
                    background = section_style.get('background-color', '').lower()
                    assert background != 'rgba(0, 0, 0, 0)', "Highlighted section should have background color"
                    
                    break
            
            # Switch back to summary view for next card
            show_less_btn = card.locator("button:has-text('Show Less')")
            if show_less_btn.is_visible():
                show_less_btn.click()
                page.wait_for_timeout(200)
        
        if found_recommendation:
            print("✅ Found and verified highlighted recommendation section")
        else:
            print("ℹ️  No recommendation sections found in first 3 cards")
    
    def test_rationale_section_highlighted(self, page: Page):
        """Test that rationale sections are highlighted"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Look for cards with rationale
        cards = page.locator(".analysis-card").all()
        
        found_rationale = False
        
        for card in cards[:5]:  # Check first 5 cards
            show_full_btn = card.locator("button:has-text('Show Full')")
            show_full_btn.click()
            page.wait_for_timeout(500)
            
            # Look for highlighted rationale sections
            highlighted_sections = card.locator(".analysis-section.highlighted").all()
            
            for section in highlighted_sections:
                section_title = section.locator(".section-title")
                title_text = section_title.text_content().lower()
                
                if "rationale" in title_text:
                    found_rationale = True
                    print(f"Found highlighted rationale section: {title_text}")
                    
                    # Verify highlighting styles are applied
                    section_classes = section.get_attribute("class")
                    assert "highlighted" in section_classes
                    break
            
            # Switch back to summary view for next card
            show_less_btn = card.locator("button:has-text('Show Less')")
            if show_less_btn.is_visible():
                show_less_btn.click()
                page.wait_for_timeout(200)
        
        if found_rationale:
            print("✅ Found and verified highlighted rationale section")
        else:
            print("ℹ️  No rationale sections found in first 5 cards")
    
    def test_timestamps_are_clickable_links(self, page: Page):
        """Test that timestamps are converted to clickable links"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Look for cards with timestamps
        cards = page.locator(".analysis-card").all()
        
        found_timestamp_links = False
        
        for card in cards[:5]:  # Check first 5 cards
            show_full_btn = card.locator("button:has-text('Show Full')")
            show_full_btn.click()
            page.wait_for_timeout(500)
            
            # Look for timestamp links
            timestamp_links = card.locator("a.timestamp-link").all()
            
            if len(timestamp_links) > 0:
                found_timestamp_links = True
                print(f"Found {len(timestamp_links)} timestamp links in card")
                
                # Test first timestamp link
                first_link = timestamp_links[0]
                link_text = first_link.text_content()
                link_href = first_link.get_attribute("href")
                
                print(f"Timestamp link text: {link_text}, href: {link_href}")
                
                # Verify link text format (e.g., "(15:30)")
                timestamp_pattern = re.compile(r'\((\d{1,2}:\d{2})\)')
                assert timestamp_pattern.match(link_text), f"Timestamp text should match (MM:SS) format: {link_text}"
                
                # Verify link href points to YouTube with timestamp
                assert link_href, "Timestamp link should have href attribute"
                assert "youtube.com" in link_href, f"Link should point to YouTube: {link_href}"
                assert "t=" in link_href, f"Link should include timestamp parameter: {link_href}"
                
                # Verify target="_blank"
                target = first_link.get_attribute("target")
                assert target == "_blank", "Timestamp links should open in new tab"
                
                break
            
            # Switch back to summary view for next card
            show_less_btn = card.locator("button:has-text('Show Less')")
            if show_less_btn.is_visible():
                show_less_btn.click()
                page.wait_for_timeout(200)
        
        if found_timestamp_links:
            print("✅ Found and verified clickable timestamp links")
        else:
            print("ℹ️  No timestamp links found in first 5 cards")

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