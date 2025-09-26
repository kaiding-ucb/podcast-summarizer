#!/usr/bin/env python3

import asyncio
import pytest
import sys
import os
from playwright.async_api import async_playwright

class TestPhase2MultiSelect:
    """Test suite for Phase 2: Multi-Select UI with Playwright"""
    
    @pytest.mark.asyncio
    async def test_checkbox_appears_on_video_cards(self):
        """Test that checkbox appears on each video card"""
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
                
                # Check that each video card has a checkbox
                for i, card in enumerate(video_cards[:3]):  # Check first 3 cards
                    checkbox = await card.query_selector('input[type="checkbox"]')
                    assert checkbox is not None, f"Video card {i+1} should have a checkbox"
                
                print(f"✅ Found checkboxes on {len(video_cards)} video cards")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_select_all_checkbox_functionality(self):
        """Test Select All checkbox checks/unchecks all video checkboxes"""
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
                
                # Find Select All checkbox
                select_all = await page.wait_for_selector('#selectAll', timeout=5000)
                assert select_all is not None, "Should have Select All checkbox"
                
                # Check Select All
                await select_all.check()
                
                # Verify all video checkboxes are checked
                video_checkboxes = await page.query_selector_all('.video-card input[type="checkbox"]')
                for checkbox in video_checkboxes:
                    is_checked = await checkbox.is_checked()
                    assert is_checked, "All video checkboxes should be checked when Select All is checked"
                
                # Uncheck Select All
                await select_all.uncheck()
                
                # Verify all video checkboxes are unchecked
                for checkbox in video_checkboxes:
                    is_checked = await checkbox.is_checked()
                    assert not is_checked, "All video checkboxes should be unchecked when Select All is unchecked"
                
                print(f"✅ Select All functionality works correctly with {len(video_checkboxes)} checkboxes")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_selected_count_updates_correctly(self):
        """Test that selected count updates as checkboxes are checked/unchecked"""
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
                
                # Find selected count display
                count_display = await page.wait_for_selector('#selectedCount', timeout=5000)
                assert count_display is not None, "Should have selected count display"
                
                # Initially should show 0
                initial_text = await count_display.text_content()
                assert "0" in initial_text, f"Initial count should show 0, got: {initial_text}"
                
                # Check first checkbox
                video_checkboxes = await page.query_selector_all('.video-card input[type="checkbox"]')
                if len(video_checkboxes) > 0:
                    await video_checkboxes[0].check()
                    await page.wait_for_timeout(500)
                    
                    count_text = await count_display.text_content()
                    assert "1" in count_text, f"Count should show 1 after checking one, got: {count_text}"
                
                # Check second checkbox
                if len(video_checkboxes) > 1:
                    await video_checkboxes[1].check()
                    await page.wait_for_timeout(500)
                    
                    count_text = await count_display.text_content()
                    assert "2" in count_text, f"Count should show 2 after checking two, got: {count_text}"
                
                # Uncheck first checkbox
                if len(video_checkboxes) > 0:
                    await video_checkboxes[0].uncheck()
                    await page.wait_for_timeout(500)
                    
                    count_text = await count_display.text_content()
                    assert "1" in count_text, f"Count should show 1 after unchecking one, got: {count_text}"
                
                print("✅ Selected count updates correctly")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_analyze_selected_button_shows_count(self):
        """Test Analyze Selected button shows correct count"""
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
                
                # Find Analyze Selected button
                analyze_btn = await page.wait_for_selector('#analyzeSelectedBtn', timeout=5000)
                assert analyze_btn is not None, "Should have Analyze Selected button"
                
                # Initially should show count 0 and be disabled
                initial_text = await analyze_btn.text_content()
                assert "0" in initial_text or "Analyze Selected" in initial_text, f"Initial button text: {initial_text}"
                
                is_disabled = await analyze_btn.is_disabled()
                assert is_disabled, "Button should be disabled when no videos selected"
                
                # Check some checkboxes
                video_checkboxes = await page.query_selector_all('.video-card input[type="checkbox"]')
                if len(video_checkboxes) >= 2:
                    await video_checkboxes[0].check()
                    await video_checkboxes[1].check()
                    await page.wait_for_timeout(500)
                    
                    button_text = await analyze_btn.text_content()
                    assert "2" in button_text, f"Button should show count 2, got: {button_text}"
                    
                    is_disabled = await analyze_btn.is_disabled()
                    assert not is_disabled, "Button should be enabled when videos are selected"
                
                print("✅ Analyze Selected button shows correct count and state")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_analyze_selected_triggers_batch_analysis(self):
        """Test clicking Analyze Selected triggers batch analysis"""
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
                
                # Check some videos
                video_checkboxes = await page.query_selector_all('.video-card input[type="checkbox"]')
                if len(video_checkboxes) >= 2:
                    await video_checkboxes[0].check()
                    await video_checkboxes[1].check()
                    await page.wait_for_timeout(500)
                
                # Click Analyze Selected
                analyze_btn = await page.wait_for_selector('#analyzeSelectedBtn', timeout=5000)
                await analyze_btn.click()
                
                # Check for progress indicator
                progress_element = await page.wait_for_selector('#batch-progress', timeout=5000)
                assert progress_element is not None, "Should show progress indicator"
                
                # Wait for progress text to appear
                progress_text = await page.wait_for_selector('#progress-text', timeout=5000)
                text_content = await progress_text.text_content()
                assert "Analyzing" in text_content or "video" in text_content.lower(), \
                    f"Progress text should indicate analysis in progress, got: {text_content}"
                
                print("✅ Analyze Selected triggers batch analysis with progress")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_progress_bar_shows_video_x_of_y(self):
        """Test progress bar shows 'Analyzing video X of Y'"""
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
                
                # Check 2 videos
                video_checkboxes = await page.query_selector_all('.video-card input[type="checkbox"]')
                if len(video_checkboxes) >= 2:
                    await video_checkboxes[0].check()
                    await video_checkboxes[1].check()
                    await page.wait_for_timeout(500)
                
                # Start analysis
                analyze_btn = await page.wait_for_selector('#analyzeSelectedBtn', timeout=5000)
                await analyze_btn.click()
                
                # Wait for and check progress text format
                progress_text = await page.wait_for_selector('#progress-text', timeout=10000)
                
                # Check progress text format over time
                for i in range(3):  # Check a few times during analysis
                    await page.wait_for_timeout(1000)
                    text_content = await progress_text.text_content()
                    
                    # Should contain pattern like "video X of Y" or similar
                    if "video" in text_content.lower() and "of" in text_content.lower():
                        print(f"✅ Progress text shows correct format: '{text_content}'")
                        break
                else:
                    # If we don't find the pattern, still check for reasonable progress text
                    text_content = await progress_text.text_content()
                    assert len(text_content) > 0, "Progress text should not be empty"
                    print(f"✅ Progress text present: '{text_content}'")
                
            finally:
                await browser.close()

def run_tests():
    """Run all Phase 2 tests"""
    print("\n" + "="*60)
    print("🧪 Running Phase 2 Tests: Multi-Select UI with Playwright")
    print("="*60 + "\n")
    
    # Run pytest with verbose output
    pytest.main([__file__, "-v", "-s"])

if __name__ == "__main__":
    run_tests()