"""
Playwright test suite to verify dashboard pagination functionality.

Tests verify that:
- Pagination displays max 10 results per page
- Pagination controls work correctly
- Page navigation functions properly
- URL reflects current page
- Pagination preserves filters
"""

import pytest
import re
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8000"

class TestDashboardPagination:
    """Test suite for dashboard pagination functionality"""
    
    def test_pagination_displays_max_10_results(self, page: Page):
        """Test that dashboard displays maximum 10 results per page"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Count analysis cards on the page
        cards = page.locator(".analysis-card").all()
        card_count = len(cards)
        
        print(f"Found {card_count} analysis cards on page 1")
        
        # Should display max 10 results (or all if less than 10 total)
        assert card_count <= 10, f"Expected max 10 cards per page, found {card_count}"
        
        # If there are exactly 10 cards, pagination should be visible
        if card_count == 10:
            pagination_controls = page.locator("#pagination-controls")
            expect(pagination_controls).to_be_visible()
            
    def test_pagination_controls_visible_with_multiple_pages(self, page: Page):
        """Test that pagination controls are visible when there are multiple pages"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses and pagination to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Check if pagination controls are visible
        pagination_controls = page.locator("#pagination-controls")
        pagination_info = page.locator("#pagination-info-text")
        
        # Get total count from API to verify behavior
        response = page.request.get(f"{BASE_URL}/api/analyses")
        data = response.json()
        total_count = data.get('total_count', 0)
        
        print(f"Total analyses: {total_count}")
        
        if total_count > 10:
            expect(pagination_controls).to_be_visible()
            expect(pagination_info).to_be_visible()
            
            # Check pagination info text
            info_text = pagination_info.text_content()
            assert "Showing" in info_text
            assert "results" in info_text
            print(f"Pagination info: {info_text}")
        else:
            # If 10 or fewer results, pagination might not be visible
            print("10 or fewer total results, pagination behavior may vary")
    
    def test_next_prev_buttons_functionality(self, page: Page):
        """Test that next/previous buttons work correctly"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Check if we have multiple pages
        pagination_controls = page.locator("#pagination-controls")
        next_btn = page.locator("#next-page-btn")
        prev_btn = page.locator("#prev-page-btn")
        page_info = page.locator("#page-info")
        
        if pagination_controls.is_visible():
            # Check initial state
            initial_page_text = page_info.text_content()
            print(f"Initial page info: {initial_page_text}")
            
            # Previous button should be disabled on page 1
            expect(prev_btn).to_be_disabled()
            
            # If next button is enabled, test navigation
            if not next_btn.is_disabled():
                # Click next button
                next_btn.click()
                
                # Wait for page to update
                page.wait_for_timeout(1000)
                
                # Check that page info updated
                new_page_text = page_info.text_content()
                print(f"After next click: {new_page_text}")
                assert new_page_text != initial_page_text
                
                # Previous button should now be enabled
                expect(prev_btn).not_to_be_disabled()
                
                # Click previous to go back
                prev_btn.click()
                page.wait_for_timeout(1000)
                
                # Should be back to original page
                final_page_text = page_info.text_content()
                assert final_page_text == initial_page_text
    
    def test_page_numbers_update_correctly(self, page: Page):
        """Test that page numbers update correctly during navigation"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        pagination_controls = page.locator("#pagination-controls")
        page_info = page.locator("#page-info")
        
        if pagination_controls.is_visible():
            # Extract page numbers from page info
            page_text = page_info.text_content()
            print(f"Page info text: {page_text}")
            
            # Should match format "Page X of Y"
            page_pattern = re.compile(r'Page (\d+) of (\d+)')
            match = page_pattern.search(page_text)
            
            assert match, f"Page info doesn't match expected format: {page_text}"
            
            current_page = int(match.group(1))
            total_pages = int(match.group(2))
            
            print(f"Current page: {current_page}, Total pages: {total_pages}")
            
            assert current_page == 1, "Should start on page 1"
            assert total_pages >= 1, "Should have at least 1 page"
            
            # Test navigation to last page if multiple pages exist
            if total_pages > 1:
                last_btn = page.locator("#last-page-btn")
                last_btn.click()
                page.wait_for_timeout(1000)
                
                # Check we're on the last page
                final_page_text = page_info.text_content()
                final_match = page_pattern.search(final_page_text)
                assert final_match
                
                final_current_page = int(final_match.group(1))
                assert final_current_page == total_pages
    
    def test_url_reflects_current_page(self, page: Page):
        """Test that browser URL updates to reflect current page"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Initial URL should not have page parameter or should be page=1
        current_url = page.url
        print(f"Initial URL: {current_url}")
        assert "page=" not in current_url or "page=1" in current_url
        
        pagination_controls = page.locator("#pagination-controls")
        next_btn = page.locator("#next-page-btn")
        
        if pagination_controls.is_visible() and not next_btn.is_disabled():
            # Navigate to page 2
            next_btn.click()
            page.wait_for_timeout(1000)
            
            # URL should now contain page=2
            new_url = page.url
            print(f"URL after next click: {new_url}")
            assert "page=2" in new_url
            
            # Navigate back to page 1
            first_btn = page.locator("#first-page-btn")
            first_btn.click()
            page.wait_for_timeout(1000)
            
            # URL should remove page parameter or show page=1
            final_url = page.url
            print(f"Final URL: {final_url}")
            # Should either not have page param or have page=1, but not page=2
            assert "page=2" not in final_url
    
    def test_pagination_preserves_filters(self, page: Page):
        """Test that pagination preserves channel and date filters"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for initial load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Apply a channel filter
        channel_filter = page.locator("#channelFilter")
        channel_filter.select_option("UCkrwgzhIBKccuDsi_SvZtnQ")  # Forward Guidance
        
        # Click refresh to apply filter
        refresh_btn = page.locator("#refreshBtn")
        refresh_btn.click()
        
        # Wait for filtered results
        page.wait_for_timeout(2000)
        
        # Check that filter is applied by looking for channel name
        cards = page.locator(".analysis-card").all()
        if len(cards) > 0:
            # Check first card has the filtered channel
            first_card = cards[0]
            channel_badge = first_card.locator(".channel-badge")
            channel_text = channel_badge.text_content()
            print(f"Filtered channel: {channel_text}")
            assert "Forward Guidance" in channel_text
            
            # If pagination is visible, test navigation preserves filter
            pagination_controls = page.locator("#pagination-controls")
            next_btn = page.locator("#next-page-btn")
            
            if pagination_controls.is_visible() and not next_btn.is_disabled():
                # Navigate to next page
                next_btn.click()
                page.wait_for_timeout(1000)
                
                # Check that filter is still applied
                new_cards = page.locator(".analysis-card").all()
                if len(new_cards) > 0:
                    new_channel_badge = new_cards[0].locator(".channel-badge")
                    new_channel_text = new_channel_badge.text_content()
                    assert "Forward Guidance" in new_channel_text
                    print("Filter preserved after pagination")
    
    def test_pagination_info_accuracy(self, page: Page):
        """Test that pagination info shows accurate result counts"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        pagination_controls = page.locator("#pagination-controls")
        
        if pagination_controls.is_visible():
            pagination_info = page.locator("#pagination-info-text")
            info_text = pagination_info.text_content()
            
            print(f"Pagination info: {info_text}")
            
            # Parse the info text "Showing X-Y of Z results"
            info_pattern = re.compile(r'Showing (\d+)-(\d+) of (\d+) results')
            match = info_pattern.search(info_text)
            
            assert match, f"Pagination info doesn't match expected format: {info_text}"
            
            start = int(match.group(1))
            end = int(match.group(2))
            total = int(match.group(3))
            
            # Verify the counts make sense
            assert start >= 1, "Start should be at least 1"
            assert end >= start, "End should be >= start"
            assert total >= end, "Total should be >= end"
            
            # Count actual cards on page
            actual_cards = len(page.locator(".analysis-card").all())
            expected_cards = end - start + 1
            
            assert actual_cards == expected_cards, f"Expected {expected_cards} cards based on pagination info, found {actual_cards}"

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