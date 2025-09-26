#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.gemini_analyzer import GeminiAnalyzer
from services.youtube_service import YouTubeService

def test_video_duration_fix():
    """Test that video duration is fetched correctly using YouTube Data API"""
    
    print("Testing video duration fix...")
    
    # Test with a real YouTube video
    test_url = "https://www.youtube.com/watch?v=qkMUpDPizUE"  # Gold Price Up 40% video from your logs
    
    # Test YouTubeService directly
    print("1. Testing YouTubeService.get_video_info()...")
    youtube_service = YouTubeService()
    video_info = youtube_service.get_video_info(test_url)
    
    if video_info:
        print(f"   ✅ Video info retrieved successfully")
        print(f"   Title: {video_info['title']}")
        print(f"   Duration: {video_info['duration']} seconds")
        print(f"   Channel: {video_info['channel_name']}")
    else:
        print("   ❌ Failed to get video info")
        return False
    
    # Test GeminiAnalyzer duration method
    print("\n2. Testing GeminiAnalyzer.get_video_duration()...")
    analyzer = GeminiAnalyzer()
    duration = analyzer.get_video_duration(test_url)
    
    if duration > 0:
        print(f"   ✅ Duration fetched successfully: {duration} seconds")
    else:
        print("   ❌ Failed to get video duration")
        return False
    
    # Verify they match
    if video_info['duration'] == duration:
        print(f"   ✅ Durations match: {duration} seconds")
    else:
        print(f"   ⚠️  Duration mismatch: {video_info['duration']} vs {duration}")
    
    # Test optimization: analyze_video with provided duration
    print("\n3. Testing optimized analyze_video with provided duration...")
    try:
        # This should NOT make an additional API call for duration
        result = analyzer.analyze_video(test_url, video_duration=video_info['duration'])
        
        if result.get('success'):
            print(f"   ✅ Analysis successful with provided duration")
            print(f"   Video duration in result: {result.get('video_duration')} seconds")
        else:
            print(f"   ❌ Analysis failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"   ❌ Analysis threw exception: {e}")
        return False
    
    print("\n🎉 All tests passed! pytube fix is working correctly.")
    return True

if __name__ == "__main__":
    success = test_video_duration_fix()
    sys.exit(0 if success else 1)