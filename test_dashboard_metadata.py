"""
Playwright test suite to verify that the dashboard correctly displays video metadata.

Tests verify that video cards show:
- Channel names (instead of "Unknown")
- Publish dates (instead of "Unknown") 
- Video durations in MM:SS format (instead of "Unknown")
"""

import pytest
import re
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8000"

class TestDashboardMetadata:
    """Test suite for dashboard metadata display functionality"""
    
    def test_dashboard_loads_successfully(self, page: Page):
        """Test that the dashboard page loads without errors"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for the page to load
        expect(page).to_have_title(re.compile("Dashboard"))
        
        # Check that the main dashboard elements are present
        expect(page.locator("h2")).to_contain_text("Analysis Dashboard")
        expect(page.locator(".dashboard-controls")).to_be_visible()
        expect(page.locator("#analyses-grid")).to_be_visible()
        
    def test_api_returns_test_data(self, page: Page):
        """Verify that the API endpoint returns our test data"""
        response = page.request.get(f"{BASE_URL}/api/analyses")
        assert response.status == 200
        
        data = response.json()
        assert "analyses" in data
        assert "total_count" in data
        assert data["total_count"] > 0
        
        # Verify we have analyses with proper metadata
        analyses = data["analyses"]
        for analysis in analyses:
            assert analysis["channel_name"] != "Unknown"
            assert analysis["channel_name"] is not None
            assert analysis["published_at"] != "Unknown" 
            assert analysis["published_at"] is not None
            assert analysis["video_duration"] > 0
    
    def test_dashboard_displays_channel_names(self, page: Page):
        """Test that video cards show channel names instead of 'Unknown'"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Get all channel badges
        channel_badges = page.locator(".channel-badge").all()
        assert len(channel_badges) > 0, "No channel badges found on dashboard"
        
        for badge in channel_badges:
            channel_text = badge.text_content()
            print(f"Found channel badge: {channel_text}")
            
            # Should not contain "Unknown"
            assert "Unknown" not in channel_text, f"Channel badge contains 'Unknown': {channel_text}"
            
            # Should contain expected channel names
            assert any(channel in channel_text for channel in [
                "Forward Guidance", 
                "Prof G Markets"
            ]), f"Channel badge doesn't contain expected channel name: {channel_text}"
    
    def test_dashboard_displays_publish_dates(self, page: Page):
        """Test that video cards show publish dates instead of 'Unknown'"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Get all date badges
        date_badges = page.locator(".date-badge").all()
        assert len(date_badges) > 0, "No date badges found on dashboard"
        
        for badge in date_badges:
            date_text = badge.text_content()
            print(f"Found date badge: {date_text}")
            
            # Should not contain "Unknown"
            assert "Unknown" not in date_text, f"Date badge contains 'Unknown': {date_text}"
            
            # Should contain a formatted date (MM/DD/YYYY or similar)
            # Remove the calendar emoji and any extra spaces
            clean_date = date_text.replace("📅", "").strip()
            date_pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
            assert date_pattern.search(clean_date), f"Date badge doesn't contain valid date format: {date_text}"
    
    def test_dashboard_displays_video_durations(self, page: Page):
        """Test that video cards show video durations in MM:SS format instead of 'Unknown'"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Get all duration badges
        duration_badges = page.locator(".duration-badge").all()
        assert len(duration_badges) > 0, "No duration badges found on dashboard"
        
        for badge in duration_badges:
            duration_text = badge.text_content()
            print(f"Found duration badge: {duration_text}")
            
            # Should not contain "Unknown"
            assert "Unknown" not in duration_text, f"Duration badge contains 'Unknown': {duration_text}"
            
            # Should contain MM:SS format
            # Remove the clock emoji and any extra spaces
            clean_duration = duration_text.replace("⏱️", "").strip()
            duration_pattern = re.compile(r'\d{1,2}:\d{2}')
            assert duration_pattern.search(clean_duration), f"Duration badge doesn't contain MM:SS format: {duration_text}"
    
    def test_all_video_cards_have_complete_metadata(self, page: Page):
        """Test that every video card has all required metadata fields populated"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Get all analysis cards
        cards = page.locator(".analysis-card").all()
        assert len(cards) > 0, "No analysis cards found on dashboard"
        
        print(f"Found {len(cards)} analysis cards on dashboard")
        
        for i, card in enumerate(cards):
            print(f"Checking card {i+1}...")
            
            # Check that the card has a title
            title_element = card.locator(".analysis-title")
            expect(title_element).to_be_visible()
            title_text = title_element.text_content()
            assert title_text and len(title_text.strip()) > 0, f"Card {i+1} has empty title"
            
            # Check metadata section exists
            meta_section = card.locator(".analysis-meta")
            expect(meta_section).to_be_visible()
            
            # Check channel badge
            channel_badge = card.locator(".channel-badge")
            expect(channel_badge).to_be_visible()
            channel_text = channel_badge.text_content()
            assert "Unknown" not in channel_text, f"Card {i+1} channel is Unknown"
            
            # Check date badge
            date_badge = card.locator(".date-badge") 
            expect(date_badge).to_be_visible()
            date_text = date_badge.text_content()
            assert "Unknown" not in date_text, f"Card {i+1} date is Unknown"
            
            # Check duration badge
            duration_badge = card.locator(".duration-badge")
            expect(duration_badge).to_be_visible()
            duration_text = duration_badge.text_content()
            assert "Unknown" not in duration_text, f"Card {i+1} duration is Unknown"
            
            print(f"✅ Card {i+1} has complete metadata: {title_text[:50]}...")
    
    def test_specific_test_data_visibility(self, page: Page):
        """Test that our specific test data is visible with correct formatting"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Expected test data
        expected_videos = [
            {
                "title": "Market Analysis: Tech Stocks Deep Dive",
                "channel": "Forward Guidance", 
                "duration": "20:45"  # 1245 seconds
            },
            {
                "title": "Portfolio Strategy: Diversification in 2024",
                "channel": "Prof G Markets",
                "duration": "28:00"  # 1680 seconds  
            },
            {
                "title": "Breaking: Federal Reserve Rate Decision Impact",
                "channel": "Forward Guidance",
                "duration": "15:45"  # 945 seconds
            }
        ]
        
        for expected in expected_videos:
            # Find card by title
            title_selector = f"text='{expected['title']}'"
            card = page.locator(".analysis-card").filter(has_text=expected['title'])
            expect(card).to_be_visible(timeout=5000)
            
            # Check channel
            channel_badge = card.locator(".channel-badge")
            expect(channel_badge).to_contain_text(expected['channel'])
            
            # Check duration format
            duration_badge = card.locator(".duration-badge")
            expect(duration_badge).to_contain_text(expected['duration'])
            
            print(f"✅ Found expected video: {expected['title']}")

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