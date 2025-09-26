#!/usr/bin/env python3

import asyncio
import pytest
import sys
import os
from playwright.async_api import async_playwright

class TestAnalyzedVideoSelection:
    """Test suite to verify analyzed videos cannot be re-selected for analysis"""
    
    @pytest.mark.asyncio
    async def test_analyzed_videos_have_no_checkboxes(self):
        """Test that analyzed videos do not have checkboxes"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to discover page
                await page.goto("http://localhost:57212/discover")
                await page.wait_for_load_state('networkidle')
                
                # Click discover to load videos
                discover_btn = await page.wait_for_selector('#discoverBtn', timeout=5000)
                await discover_btn.click()
                
                # Wait for videos to load
                await page.wait_for_timeout(3000)
                
                # Check for video cards
                video_cards = await page.query_selector_all('.video-card')
                assert len(video_cards) > 0, "Should have video cards loaded"
                
                analyzed_videos_without_checkboxes = 0
                unanalyzed_videos_with_checkboxes = 0
                
                for card in video_cards:
                    # Check if this card is analyzed
                    is_analyzed = await card.query_selector('.analyzed-badge')
                    checkbox = await card.query_selector('.video-checkbox')
                    
                    if is_analyzed:
                        # Analyzed videos should NOT have checkboxes
                        assert checkbox is None, "Analyzed videos should not have checkboxes"
                        analyzed_videos_without_checkboxes += 1
                    else:
                        # Unanalyzed videos SHOULD have checkboxes
                        assert checkbox is not None, "Unanalyzed videos should have checkboxes"
                        unanalyzed_videos_with_checkboxes += 1
                
                print(f"✅ Found {analyzed_videos_without_checkboxes} analyzed videos without checkboxes")
                print(f"✅ Found {unanalyzed_videos_with_checkboxes} unanalyzed videos with checkboxes")
                
                # At least one of each type should exist for a meaningful test
                assert analyzed_videos_without_checkboxes > 0, "Should have some analyzed videos for testing"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_select_all_only_selects_unanalyzed_videos(self):
        """Test that Select All only affects unanalyzed videos"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate and load videos
                await page.goto("http://localhost:57212/discover")
                await page.wait_for_load_state('networkidle')
                
                discover_btn = await page.wait_for_selector('#discoverBtn', timeout=5000)
                await discover_btn.click()
                await page.wait_for_timeout(3000)
                
                # Count total videos vs available checkboxes
                total_videos = len(await page.query_selector_all('.video-card'))
                available_checkboxes = len(await page.query_selector_all('.video-checkbox'))
                
                print(f"Total videos: {total_videos}")
                print(f"Available checkboxes: {available_checkboxes}")
                
                # Select All should only affect videos with checkboxes
                select_all = await page.wait_for_selector('#selectAll', timeout=5000)
                await select_all.check()
                
                # Count checked checkboxes
                checked_boxes = await page.query_selector_all('.video-checkbox:checked')
                checked_count = len(checked_boxes)
                
                # All available checkboxes should be checked
                assert checked_count == available_checkboxes, \
                    f"Expected {available_checkboxes} checked boxes, got {checked_count}"
                
                # Verify analyze button shows correct count
                analyze_btn = await page.wait_for_selector('#analyzeSelectedBtn', timeout=5000)
                button_text = await analyze_btn.text_content()
                
                assert str(checked_count) in button_text, \
                    f"Button should show {checked_count} selected videos, got: {button_text}"
                
                print(f"✅ Select All correctly selected {checked_count} unanalyzed videos")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_analyzed_videos_have_visual_indicators(self):
        """Test that analyzed videos have proper visual indicators"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate and load videos
                await page.goto("http://localhost:57212/discover")
                await page.wait_for_load_state('networkidle')
                
                discover_btn = await page.wait_for_selector('#discoverBtn', timeout=5000)
                await discover_btn.click()
                await page.wait_for_timeout(3000)
                
                # Find analyzed video cards
                analyzed_cards = await page.query_selector_all('.video-card.analyzed')
                
                if len(analyzed_cards) > 0:
                    for card in analyzed_cards[:3]:  # Check first 3
                        # Should have analyzed class
                        class_name = await card.get_attribute('class')
                        assert 'analyzed' in class_name, "Should have 'analyzed' class"
                        
                        # Should have analyzed badge
                        badge = await card.query_selector('.analyzed-badge')
                        assert badge is not None, "Should have analyzed badge"
                        
                        # Should NOT have checkbox
                        checkbox = await card.query_selector('.video-checkbox')
                        assert checkbox is None, "Should not have checkbox"
                    
                    print(f"✅ {len(analyzed_cards)} analyzed videos have proper visual indicators")
                else:
                    print("⚠️  No analyzed videos found for visual indicator testing")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_analyze_button_disabled_when_only_analyzed_selected(self):
        """Test that analyze button is disabled when no selectable videos exist"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate and load videos
                await page.goto("http://localhost:57212/discover")
                await page.wait_for_load_state('networkidle')
                
                discover_btn = await page.wait_for_selector('#discoverBtn', timeout=5000)
                await discover_btn.click()
                await page.wait_for_timeout(3000)
                
                # Check if there are any selectable videos
                available_checkboxes = await page.query_selector_all('.video-checkbox')
                analyze_btn = await page.wait_for_selector('#analyzeSelectedBtn', timeout=5000)
                
                if len(available_checkboxes) == 0:
                    # No selectable videos - button should be disabled
                    is_disabled = await analyze_btn.is_disabled()
                    assert is_disabled, "Analyze button should be disabled when no videos are selectable"
                    
                    button_text = await analyze_btn.text_content()
                    assert "(0)" in button_text, f"Button should show (0), got: {button_text}"
                    
                    print("✅ Analyze button correctly disabled when no selectable videos")
                else:
                    # Some selectable videos exist - test selection behavior
                    print(f"Found {len(available_checkboxes)} selectable videos for further testing")
                
            finally:
                await browser.close()

def run_tests():
    """Run all analyzed video selection tests"""
    print("\n" + "="*70)
    print("🧪 Running Analyzed Video Selection Tests")
    print("="*70 + "\n")
    
    # Run pytest with verbose output
    pytest.main([__file__, "-v", "-s"])

if __name__ == "__main__":
    run_tests()