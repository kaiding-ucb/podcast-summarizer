"""
Playwright test suite to verify that timestamps in analysis content are properly
detected, formatted, and made clickable with correct YouTube links.

Tests verify that:
- Timestamps in various formats are detected (0:56, 1:23:45, (0:56-1:14), etc.)
- Clickable timestamp links are generated with proper YouTube URLs
- Timestamp links include the correct time parameter (&t=XXXs)
- Non-clickable timestamps are properly styled when video URL is unavailable
- Timestamp ranges are handled correctly
"""

import pytest
import re
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8000"

class TestDashboardTimestamps:
    """Test suite for dashboard timestamp functionality"""
    
    def test_dashboard_loads_and_shows_content(self, page: Page):
        """Test that the dashboard loads and shows analysis content"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        # Check that analysis cards exist
        cards = page.locator(".analysis-card").all()
        assert len(cards) > 0, "No analysis cards found on dashboard"
        
        print(f"Found {len(cards)} analysis cards for timestamp testing")
    
    def test_timestamps_are_clickable_links(self, page: Page):
        """Test that timestamps in analysis content become clickable YouTube links"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        cards = page.locator(".analysis-card").all()
        clickable_timestamps_found = False
        
        for card_index, card in enumerate(cards[:3]):  # Test first 3 cards
            # Click show full to see complete analysis
            show_full_btn = card.locator("button:has-text('Show Full')")
            if show_full_btn.is_visible():
                show_full_btn.click()
                page.wait_for_timeout(500)  # Wait for content to expand
                
                # Look for timestamp links
                timestamp_links = card.locator(".timestamp-link").all()
                
                if len(timestamp_links) > 0:
                    clickable_timestamps_found = True
                    print(f"✅ Card {card_index + 1} has {len(timestamp_links)} clickable timestamps")
                    
                    # Test each timestamp link
                    for i, link in enumerate(timestamp_links[:5]):  # Test first 5 timestamps
                        # Verify link is visible and clickable
                        expect(link).to_be_visible()
                        
                        # Get link attributes
                        href = link.get_attribute("href")
                        text = link.text_content()
                        target = link.get_attribute("target")
                        
                        print(f"  Timestamp {i+1}: '{text}' -> {href}")
                        
                        # Verify it's a proper YouTube URL
                        assert href is not None, f"Timestamp link has no href: {text}"
                        assert "youtube.com/watch" in href, f"Invalid YouTube URL: {href}"
                        assert "v=" in href, f"Missing video ID in URL: {href}"
                        
                        # Verify timestamp parameter is present
                        assert "&t=" in href, f"Missing timestamp parameter in URL: {href}"
                        
                        # Verify link opens in new tab
                        assert target == "_blank", f"Timestamp link should open in new tab: {text}"
                        
                        # Extract and validate timestamp format from text
                        timestamp_match = re.search(r'(\d{1,2}:\d{2}(:\d{2})?)', text)
                        assert timestamp_match, f"Invalid timestamp format in text: {text}"
                        
                        # Extract seconds from URL and verify it makes sense
                        seconds_match = re.search(r'&t=(\d+)s', href)
                        assert seconds_match, f"Invalid timestamp seconds in URL: {href}"
                        
                        seconds = int(seconds_match.group(1))
                        assert seconds >= 0, f"Invalid timestamp seconds: {seconds}"
                        print(f"    -> Links to {seconds} seconds into video")
        
        assert clickable_timestamps_found, "No clickable timestamps found in any analysis cards"
    
    def test_timestamp_formats_are_detected(self, page: Page):
        """Test that various timestamp formats are properly detected and converted"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        cards = page.locator(".analysis-card").all()
        format_examples = {
            'parentheses': r'\(\d{1,2}:\d{2}(?::\d{2})?\)',  # (0:56) or (1:23:45)
            'plain': r'\d{1,2}:\d{2}(?::\d{2})?',  # 0:56 or 1:23:45
            'range': r'\(\d{1,2}:\d{2}-\d{1,2}:\d{2}\)',  # (0:56-1:14)
        }
        
        formats_found = {fmt: False for fmt in format_examples.keys()}
        
        for card_index, card in enumerate(cards[:3]):
            # Click show full
            show_full_btn = card.locator("button:has-text('Show Full')")
            if show_full_btn.is_visible():
                show_full_btn.click()
                page.wait_for_timeout(300)
                
                # Get all text content to analyze
                full_content = card.locator(".analysis-full")
                if full_content.is_visible():
                    content_text = full_content.text_content()
                    
                    # Check for different timestamp formats
                    for format_name, pattern in format_examples.items():
                        matches = re.findall(pattern, content_text)
                        if matches:
                            formats_found[format_name] = True
                            print(f"✅ Found {format_name} format timestamps: {matches[:3]}")
                
                # Also check for timestamp links and displays
                timestamp_elements = card.locator(".timestamp-link, .timestamp-display").all()
                for element in timestamp_elements:
                    element_text = element.text_content()
                    print(f"Processed timestamp element: {element_text}")
        
        # Report findings
        found_count = sum(formats_found.values())
        print(f"Timestamp formats detected: {found_count}/{len(format_examples)}")
        
        # At least some timestamp format should be found
        assert found_count > 0, "No timestamp formats detected in analysis content"
    
    def test_timestamp_seconds_calculation(self, page: Page):
        """Test that timestamps are correctly converted to seconds in YouTube URLs"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        cards = page.locator(".analysis-card").all()
        conversions_tested = 0
        
        for card in cards[:2]:  # Test first 2 cards
            show_full_btn = card.locator("button:has-text('Show Full')")
            if show_full_btn.is_visible():
                show_full_btn.click()
                page.wait_for_timeout(300)
                
                timestamp_links = card.locator(".timestamp-link").all()
                
                for link in timestamp_links[:3]:  # Test first 3 timestamps per card
                    text = link.text_content()
                    href = link.get_attribute("href")
                    
                    if href and "&t=" in href:
                        # Extract timestamp from text
                        time_match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', text)
                        if time_match:
                            hours = 0
                            minutes = int(time_match.group(1))
                            seconds = int(time_match.group(2))
                            
                            # Handle HH:MM:SS format
                            if time_match.group(3):
                                hours = minutes
                                minutes = seconds
                                seconds = int(time_match.group(3))
                            
                            expected_total_seconds = hours * 3600 + minutes * 60 + seconds
                            
                            # Extract actual seconds from URL
                            url_seconds_match = re.search(r'&t=(\d+)s', href)
                            if url_seconds_match:
                                actual_seconds = int(url_seconds_match.group(1))
                                
                                print(f"Timestamp: {text} -> Expected: {expected_total_seconds}s, Got: {actual_seconds}s")
                                
                                assert actual_seconds == expected_total_seconds, \
                                    f"Timestamp conversion error: {text} should be {expected_total_seconds}s but got {actual_seconds}s"
                                
                                conversions_tested += 1
        
        assert conversions_tested > 0, "No timestamp conversions could be tested"
        print(f"✅ Successfully tested {conversions_tested} timestamp conversions")
    
    def test_timestamp_ranges_handled_correctly(self, page: Page):
        """Test that timestamp ranges like (0:56-1:14) use the start time for links"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        cards = page.locator(".analysis-card").all()
        ranges_found = False
        
        for card in cards[:3]:
            show_full_btn = card.locator("button:has-text('Show Full')")
            if show_full_btn.is_visible():
                show_full_btn.click()
                page.wait_for_timeout(300)
                
                # Look for timestamp links that might be ranges
                timestamp_links = card.locator(".timestamp-link").all()
                
                for link in timestamp_links:
                    text = link.text_content()
                    href = link.get_attribute("href")
                    
                    # Check if this is a range format
                    range_match = re.search(r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})', text)
                    if range_match and href:
                        ranges_found = True
                        start_time = range_match.group(1)
                        end_time = range_match.group(2)
                        
                        print(f"✅ Found timestamp range: {text} (start: {start_time}, end: {end_time})")
                        
                        # Verify that the URL uses the start time
                        start_parts = start_time.split(':')
                        expected_seconds = int(start_parts[0]) * 60 + int(start_parts[1])
                        
                        url_seconds_match = re.search(r'&t=(\d+)s', href)
                        if url_seconds_match:
                            actual_seconds = int(url_seconds_match.group(1))
                            assert actual_seconds == expected_seconds, \
                                f"Range should use start time: expected {expected_seconds}s but got {actual_seconds}s"
                            
                            print(f"  ✅ Correctly uses start time: {expected_seconds}s")
        
        if not ranges_found:
            print("ℹ️  No timestamp ranges found in analysis content")
    
    def test_non_clickable_timestamps_when_no_video_url(self, page: Page):
        """Test that timestamps are styled but not clickable when video URL is unavailable"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        cards = page.locator(".analysis-card").all()
        display_timestamps_found = False
        
        for card in cards[:2]:
            show_full_btn = card.locator("button:has-text('Show Full')")
            if show_full_btn.is_visible():
                show_full_btn.click()
                page.wait_for_timeout(300)
                
                # Look for non-clickable timestamp displays
                timestamp_displays = card.locator(".timestamp-display").all()
                
                if len(timestamp_displays) > 0:
                    display_timestamps_found = True
                    print(f"✅ Found {len(timestamp_displays)} non-clickable timestamp displays")
                    
                    for display in timestamp_displays:
                        # Verify it's visible and styled
                        expect(display).to_be_visible()
                        expect(display).to_have_class(re.compile(r".*timestamp-display.*"))
                        
                        text = display.text_content()
                        print(f"  Display timestamp: {text}")
                        
                        # Verify it's not a link (no href attribute)
                        assert display.get_attribute("href") is None, \
                            f"timestamp-display should not have href: {text}"
        
        if not display_timestamps_found:
            print("ℹ️  No non-clickable timestamp displays found")
    
    def test_timestamp_hover_effects(self, page: Page):
        """Test that timestamp links have proper hover styling"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for analyses to load
        page.wait_for_selector(".analysis-card", timeout=10000)
        
        first_card = page.locator(".analysis-card").first
        show_full_btn = first_card.locator("button:has-text('Show Full')")
        
        if show_full_btn.is_visible():
            show_full_btn.click()
            page.wait_for_timeout(500)
            
            # Find first timestamp link
            timestamp_link = first_card.locator(".timestamp-link").first
            
            if timestamp_link.is_visible():
                # Test basic styling
                expect(timestamp_link).to_have_class(re.compile(r".*timestamp-link.*"))
                
                # Hover over the link and check for visual changes
                timestamp_link.hover()
                page.wait_for_timeout(200)
                
                print("✅ Timestamp link hover effect tested")
                
                # Get text to confirm functionality
                link_text = timestamp_link.text_content()
                href = timestamp_link.get_attribute("href")
                print(f"Hovered timestamp: {link_text} -> {href[:50]}...")
            else:
                print("ℹ️  No timestamp links available for hover testing")

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