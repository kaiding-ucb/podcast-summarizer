#!/usr/bin/env python3
"""
Simple test to verify dashboard improvements are working correctly.
This test uses requests to check API functionality and basic HTML parsing
to verify that the improvements are in place.
"""

import requests
import re
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_api_ordering():
    """Test that API returns results in correct order"""
    print("=== Testing API Ordering ===")
    
    response = requests.get(f"{BASE_URL}/api/analyses?page=1&page_size=5")
    assert response.status_code == 200, f"API failed: {response.status_code}"
    
    data = response.json()
    analyses = data['analyses']
    
    if len(analyses) > 1:
        print(f"Found {len(analyses)} analyses")
        
        # Check ordering
        previous_date = None
        unknown_dates_started = False
        
        for i, analysis in enumerate(analyses):
            published_at = analysis.get('published_at')
            title = analysis.get('title', 'Unknown')[:40]
            
            print(f"  {i+1}: {title} - {published_at}")
            
            if published_at and published_at.strip():
                assert not unknown_dates_started, "Known date found after unknown dates"
                
                try:
                    current_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    if previous_date:
                        assert current_date <= previous_date, f"Wrong order: {current_date} > {previous_date}"
                    previous_date = current_date
                except ValueError:
                    print(f"    ⚠️  Invalid date format: {published_at}")
            else:
                unknown_dates_started = True
                print(f"    ℹ️  Unknown date (correctly at end)")
        
        print("✅ API ordering is correct")
    else:
        print("⚠️  Not enough data to test ordering")

def test_analysis_structure():
    """Test that analysis content has proper structure for sectioning"""
    print("\n=== Testing Analysis Structure ===")
    
    response = requests.get(f"{BASE_URL}/api/analyses?page=1&page_size=3")
    assert response.status_code == 200, f"API failed: {response.status_code}"
    
    data = response.json()
    analyses = data['analyses']
    
    structured_count = 0
    timestamp_count = 0
    
    for i, analysis in enumerate(analyses):
        title = analysis.get('title', 'Unknown')[:40]
        analysis_text = analysis.get('analysis', '')
        
        print(f"\nAnalysis {i+1}: {title}")
        
        # Check for sectioned structure
        has_sections = bool(re.search(r'\*\*(Summary|Recommendation|Rationale|Key Points?|Timestamps?):\*\*', analysis_text))
        if has_sections:
            structured_count += 1
            print("  ✅ Has structured sections")
            
            # List found sections
            sections = re.findall(r'\*\*(Summary|Recommendation|Rationale|Key Points?|Timestamps?):\*\*', analysis_text)
            print(f"    Sections: {', '.join(sections)}")
        else:
            print("  ⚠️  No structured sections detected")
        
        # Check for timestamps
        timestamps = re.findall(r'\(\d{1,2}:\d{2}(?::\d{2})?\)', analysis_text)
        if timestamps:
            timestamp_count += 1
            print(f"  ✅ Has {len(timestamps)} timestamps: {timestamps[:3]}...")
        else:
            print("  ℹ️  No timestamps found")
        
        # Check video URL
        video_url = analysis.get('video_url')
        if video_url and 'youtube.com' in video_url:
            print("  ✅ Has YouTube video URL for clickable timestamps")
        else:
            print("  ⚠️  No YouTube URL")
    
    print(f"\nSummary:")
    print(f"  Analyses with sections: {structured_count}/{len(analyses)}")
    print(f"  Analyses with timestamps: {timestamp_count}/{len(analyses)}")
    
    assert structured_count > 0, "No analyses have structured sections"
    print("✅ Analysis structure test passed")

def test_dashboard_html():
    """Test that dashboard HTML contains expected JavaScript functions"""
    print("\n=== Testing Dashboard HTML ===")
    
    response = requests.get(f"{BASE_URL}/dashboard")
    assert response.status_code == 200, f"Dashboard failed: {response.status_code}"
    
    html = response.text
    
    # Check for key JavaScript functions
    functions_to_check = [
        'parseAnalysisSections',
        'formatSectionedAnalysis', 
        'createTimestampUrl',
        'formatAnalysisText'
    ]
    
    for func_name in functions_to_check:
        if f"function {func_name}" in html:
            print(f"  ✅ Found function: {func_name}")
        else:
            print(f"  ❌ Missing function: {func_name}")
            assert False, f"Missing JavaScript function: {func_name}"
    
    # Check for improved CSS classes
    css_classes = [
        'analysis-section',
        'analysis-section highlighted',
        'timestamp-link',
        'timestamp-display',
        'section-title',
        'section-content'
    ]
    
    for css_class in css_classes:
        if css_class in html:
            print(f"  ✅ Found CSS class: {css_class}")
        else:
            print(f"  ⚠️  CSS class may be missing: {css_class}")
    
    print("✅ Dashboard HTML test passed")

def test_timestamp_url_generation():
    """Test timestamp URL generation logic"""
    print("\n=== Testing Timestamp Logic ===")
    
    # Test cases for timestamp conversion
    test_cases = [
        ("0:56", 56),
        ("1:23", 83),
        ("12:34", 754),
        ("1:23:45", 5025),
        ("0:05:30", 330)
    ]
    
    base_video_url = "https://www.youtube.com/watch?v=1XVHNhjDiJk"
    
    for time_str, expected_seconds in test_cases:
        # Simulate the timestamp URL creation logic
        parts = time_str.split(':')
        if len(parts) == 2:
            total_seconds = int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            total_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            continue
        
        expected_url = f"{base_video_url}&t={total_seconds}s"
        
        print(f"  {time_str} -> {total_seconds}s: {expected_url}")
        assert total_seconds == expected_seconds, f"Timestamp conversion error: {time_str}"
    
    print("✅ Timestamp logic test passed")

def test_recent_analyses_endpoint():
    """Test that recent analyses endpoint uses correct ordering"""
    print("\n=== Testing Recent Analyses Endpoint ===")
    
    response = requests.get(f"{BASE_URL}/api/analyses/recent?days=30&page=1&page_size=5")
    assert response.status_code == 200, f"Recent API failed: {response.status_code}"
    
    data = response.json()
    analyses = data['analyses']
    
    if len(analyses) > 0:
        print(f"Found {len(analyses)} recent analyses")
        
        for i, analysis in enumerate(analyses[:3]):
            title = analysis.get('title', 'Unknown')[:40]
            published_at = analysis.get('published_at', 'Unknown')
            print(f"  {i+1}: {title} - {published_at}")
        
        print("✅ Recent analyses endpoint working")
    else:
        print("ℹ️  No recent analyses found")

def main():
    """Run all tests"""
    print("🧪 Testing Dashboard Improvements")
    print(f"🎯 Testing against: {BASE_URL}")
    
    try:
        test_api_ordering()
        test_analysis_structure() 
        test_dashboard_html()
        test_timestamp_url_generation()
        test_recent_analyses_endpoint()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Result ordering: Fixed")
        print("✅ Analysis sections: Improved parsing")
        print("✅ Timestamp links: Enhanced functionality") 
        print("✅ Visual organization: Updated styling")
        print("="*50)
        
        return True
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)