#!/usr/bin/env python3

import httpx
import asyncio

async def verify_selection_fix():
    """Verify that our analyzed video selection fix is working"""
    print("🔍 Verifying analyzed video selection fix...")
    
    async with httpx.AsyncClient() as client:
        # Get discover page to see current videos
        try:
            response = await client.get("http://localhost:8005/api/discover?days_back=10")
            if response.status_code == 200:
                data = response.json()
                videos = data.get('videos', [])
                
                analyzed_count = sum(1 for v in videos if v.get('analyzed'))
                unanalyzed_count = sum(1 for v in videos if not v.get('analyzed'))
                
                print(f"📊 Found {len(videos)} total videos:")
                print(f"   ✅ {analyzed_count} analyzed videos")
                print(f"   ⏳ {unanalyzed_count} unanalyzed videos")
                
                if analyzed_count > 0:
                    print("\n✅ GOOD: We have analyzed videos to test with")
                else:
                    print("\n⚠️  No analyzed videos found - may need to analyze some first")
                
                if unanalyzed_count > 0:
                    print("✅ GOOD: We have unanalyzed videos that should be selectable")
                else:
                    print("ℹ️  All videos are analyzed - selection should be disabled")
                
                return True
                
            else:
                print(f"❌ Failed to get videos: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking videos: {e}")
            return False

def main():
    print("="*60)
    print("🧪 Analyzed Video Selection Fix Verification")
    print("="*60)
    
    success = asyncio.run(verify_selection_fix())
    
    if success:
        print("\n🎯 Manual Testing Instructions:")
        print("1. Open: http://localhost:8005/discover")
        print("2. Click 'Discover New Videos'")
        print("3. Verify:")
        print("   ✅ Analyzed videos have NO checkboxes")
        print("   ✅ Only unanalyzed videos have checkboxes")
        print("   ✅ Select All only affects unanalyzed videos") 
        print("   ✅ Analyze Selected button shows correct count")
        print("   ✅ Cannot re-analyze already analyzed videos")

if __name__ == "__main__":
    main()