"""
Playwright test suite to verify channel filtering functionality in dashboard.

Tests verify that:
- Channel dropdown shows all available channels from database
- Channel filtering works correctly
- Filter state is preserved during pagination
- Channel filter affects both "All time" and "Recent" filters
"""

import pytest
import re
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8005"

class TestChannelFiltering:
    """Test suite for channel filtering functionality"""
    
    def test_channel_dropdown_loads_all_channels(self, page: Page):
        """Test that channel dropdown shows all available channels"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for page to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Wait for channels to load
        page.wait_for_timeout(1000)
        
        # Get channel dropdown
        channel_filter = page.locator("#channelFilter")
        expect(channel_filter).to_be_visible()
        
        # Get all options
        options = channel_filter.locator("option").all()
        option_texts = [option.text_content() for option in options]
        option_values = [option.get_attribute("value") for option in options]
        
        print(f"Found {len(options)} channel options:")
        for i, (text, value) in enumerate(zip(option_texts, option_values)):
            print(f"  {i+1}. {text} ({value})")
        
        # Should have at least "All Channels" plus actual channels
        assert len(options) >= 2, f"Expected at least 2 options, found {len(options)}"
        
        # First option should be "All Channels"
        assert option_texts[0] == "All Channels"
        assert option_values[0] == ""
        
        # Should include expected channels
        expected_channels = ["Forward Guidance", "Prof G Markets", "All-In Podcast"]
        for expected in expected_channels:
            assert any(expected in text for text in option_texts), f"Expected channel '{expected}' not found in options"
    
    def test_channel_filtering_works(self, page: Page):
        """Test that selecting a channel filters the results"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for initial load
        page.wait_for_selector(".analysis-card", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Get initial count
        initial_cards = page.locator(".analysis-card").all()
        initial_count = len(initial_cards)
        print(f"Initial analysis count: {initial_count}")
        
        # Select Forward Guidance channel
        channel_filter = page.locator("#channelFilter")
        channel_filter.select_option("UCkrwgzhIBKccuDsi_SvZtnQ")
        
        # Click refresh to apply filter
        refresh_btn = page.locator("#refreshBtn")
        refresh_btn.click()
        
        # Wait for results to update
        page.wait_for_timeout(2000)
        
        # Check filtered results
        filtered_cards = page.locator(".analysis-card").all()
        filtered_count = len(filtered_cards)
        print(f"Filtered analysis count: {filtered_count}")
        
        # Should have fewer results (unless all were from that channel)
        if initial_count > 1:
            assert filtered_count <= initial_count, "Filtered results should be <= initial results"
        
        # All visible cards should be from Forward Guidance
        for card in filtered_cards:
            channel_badge = card.locator(".channel-badge")
            channel_text = channel_badge.text_content()
            assert "Forward Guidance" in channel_text, f"Expected Forward Guidance, found: {channel_text}"
        
        print(f"✅ All {filtered_count} cards are from Forward Guidance")
    
    def test_channel_filter_with_recent_filter(self, page: Page):
        """Test that channel filtering works with recent days filter"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for initial load
        page.wait_for_selector(".analysis-card", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Set days filter to "Last 7 days"
        days_filter = page.locator("#daysFilter")
        days_filter.select_option("7")
        
        # Select Prof G Markets channel
        channel_filter = page.locator("#channelFilter")
        channel_filter.select_option("UC1E1SVcVyU3ntWMSQEp38Yw")
        
        # Click refresh to apply filters
        refresh_btn = page.locator("#refreshBtn")
        refresh_btn.click()
        
        # Wait for results to update
        page.wait_for_timeout(2000)
        
        # Check filtered results
        filtered_cards = page.locator(".analysis-card").all()
        
        if len(filtered_cards) > 0:
            # All visible cards should be from Prof G Markets
            for card in filtered_cards:
                channel_badge = card.locator(".channel-badge")
                channel_text = channel_badge.text_content()
                assert "Prof G Markets" in channel_text, f"Expected Prof G Markets, found: {channel_text}"
            
            print(f"✅ All {len(filtered_cards)} recent cards are from Prof G Markets")
        else:
            print("ℹ️  No recent analyses found for Prof G Markets")
    
    def test_channel_filter_reset(self, page: Page):
        """Test that resetting channel filter shows all results"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for initial load
        page.wait_for_selector(".analysis-card", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Get initial count
        initial_cards = page.locator(".analysis-card").all()
        initial_count = len(initial_cards)
        
        # Apply channel filter
        channel_filter = page.locator("#channelFilter")
        channel_filter.select_option("UCkrwgzhIBKccuDsi_SvZtnQ")
        
        refresh_btn = page.locator("#refreshBtn")
        refresh_btn.click()
        page.wait_for_timeout(2000)
        
        # Get filtered count
        filtered_cards = page.locator(".analysis-card").all()
        filtered_count = len(filtered_cards)
        
        # Reset filter to "All Channels"
        channel_filter.select_option("")
        refresh_btn.click()
        page.wait_for_timeout(2000)
        
        # Get reset count
        reset_cards = page.locator(".analysis-card").all()
        reset_count = len(reset_cards)
        
        print(f"Initial: {initial_count}, Filtered: {filtered_count}, Reset: {reset_count}")
        
        # Reset count should match initial count
        assert reset_count == initial_count, f"Reset count {reset_count} should match initial count {initial_count}"
        
        print("✅ Channel filter reset works correctly")
    
    def test_channel_filter_preserves_pagination(self, page: Page):
        """Test that channel filtering works with pagination"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for initial load
        page.wait_for_selector(".analysis-card", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Apply channel filter
        channel_filter = page.locator("#channelFilter")
        channel_filter.select_option("UCkrwgzhIBKccuDsi_SvZtnQ")
        
        refresh_btn = page.locator("#refreshBtn")
        refresh_btn.click()
        page.wait_for_timeout(2000)
        
        # Check if pagination is visible
        pagination_controls = page.locator("#pagination-controls")
        
        if pagination_controls.is_visible():
            # Check pagination info includes channel filter
            pagination_info = page.locator("#pagination-info-text")
            info_text = pagination_info.text_content()
            print(f"Pagination info with filter: {info_text}")
            
            # Navigate to next page if available
            next_btn = page.locator("#next-page-btn")
            if not next_btn.is_disabled():
                next_btn.click()
                page.wait_for_timeout(1000)
                
                # Check that filter is still applied on page 2
                cards = page.locator(".analysis-card").all()
                if len(cards) > 0:
                    first_card = cards[0]
                    channel_badge = first_card.locator(".channel-badge")
                    channel_text = channel_badge.text_content()
                    assert "Forward Guidance" in channel_text, "Filter should be preserved on page 2"
                    print("✅ Channel filter preserved on page 2")
        else:
            print("ℹ️  No pagination available for filtered results")
    
    def test_api_channels_endpoint(self, page: Page):
        """Test that the API channels endpoint returns expected data"""
        # Test the API directly
        response = page.request.get(f"{BASE_URL}/api/channels")
        assert response.status == 200, f"Expected status 200, got {response.status}"
        
        data = response.json()
        channels = data.get('channels', [])
        
        print(f"API returned {len(channels)} channels:")
        for channel in channels:
            print(f"  - {channel['name']} ({channel['channel_id']})")
        
        # Should have at least the expected channels
        assert len(channels) >= 3, f"Expected at least 3 channels, got {len(channels)}"
        
        # Check for expected channels
        channel_names = [ch['name'] for ch in channels]
        expected_names = ["Forward Guidance", "Prof G Markets", "All-In Podcast"]
        
        for expected in expected_names:
            assert expected in channel_names, f"Expected channel '{expected}' not found in API response"
        
        print("✅ API channels endpoint returns correct data")

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