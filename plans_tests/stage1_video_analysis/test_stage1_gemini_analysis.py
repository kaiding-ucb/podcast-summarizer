#!/usr/bin/env python3
"""
Test Stage 1: Gemini Video Analysis
Tests the core video analysis functionality with specific sample videos.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.gemini_analyzer import GeminiAnalyzer

def test_video_analysis():
    """Test video analysis with the two required sample videos"""
    
    analyzer = GeminiAnalyzer()
    
    # Test videos from the requirements
    test_videos = [
        "https://www.youtube.com/watch?v=699dsom_fuM",
        "https://www.youtube.com/watch?v=Er6M5gQiLRo"
    ]
    
    results = []
    
    for i, video_url in enumerate(test_videos, 1):
        print(f"\n{'='*60}")
        print(f"TESTING VIDEO {i}: {video_url}")
        print(f"{'='*60}")
        
        try:
            result = analyzer.analyze_video(video_url)
            
            if result['success']:
                print(f"✅ Analysis successful!")
                print(f"📹 Video duration: {result['video_duration']} seconds")
                print(f"⏰ Timestamps valid: {result['timestamps_valid']}")
                print(f"🚫 VanEck excluded: {result['vaneck_excluded']}")
                
                print(f"\n📝 ANALYSIS RESULT:")
                print("-" * 40)
                print(result['analysis'])
                print("-" * 40)
                
                # Success criteria validation
                analysis_text = result['analysis']
                
                # Check format compliance
                has_recommendation = "**Recommendation:**" in analysis_text
                has_summary = "**Summary:**" in analysis_text or "*Summary:*" in analysis_text
                has_timestamps = "**Timestamps:**" in analysis_text or "*Timestamps:*" in analysis_text
                
                format_compliant = has_recommendation and has_summary and has_timestamps
                
                print(f"\n🔍 SUCCESS CRITERIA CHECK:")
                print(f"   ✓ Has Recommendation section: {has_recommendation}")
                print(f"   ✓ Has Summary section: {has_summary}")
                print(f"   ✓ Has Timestamps section: {has_timestamps}")
                print(f"   ✓ Format compliant: {format_compliant}")
                print(f"   ✓ Timestamps valid: {result['timestamps_valid']}")
                print(f"   ✓ VanEck excluded: {result['vaneck_excluded']}")
                
                overall_success = (format_compliant and 
                                 result['timestamps_valid'] and 
                                 result['vaneck_excluded'])
                
                print(f"   🎯 OVERALL SUCCESS: {overall_success}")
                
                results.append({
                    'video': video_url,
                    'success': overall_success,
                    'analysis': result['analysis']
                })
                
            else:
                print(f"❌ Analysis failed: {result['error']}")
                results.append({
                    'video': video_url,
                    'success': False,
                    'error': result['error']
                })
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append({
                'video': video_url,
                'success': False,
                'error': str(e)
            })
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    
    print(f"📊 Tests completed: {successful_tests}/{total_tests}")
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"   Video {i}: {status}")
        if not result['success'] and 'error' in result:
            print(f"      Error: {result['error']}")
    
    if successful_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! Stage 1 requirements met.")
        return True
    else:
        print(f"\n⚠️  {total_tests - successful_tests} test(s) failed.")
        return False

if __name__ == "__main__":
    test_video_analysis()