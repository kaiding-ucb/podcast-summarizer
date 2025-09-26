#!/usr/bin/env python3
"""
Data migration script to backfill missing channel metadata for existing video analyses.
This script updates existing database records that have NULL or missing channel_id, 
channel_name, and published_at fields by fetching this data from YouTube API.
"""

import sqlite3
from services.youtube_service import YouTubeService
from services.database import DatabaseService
from typing import List, Dict, Any
import time

def get_videos_missing_metadata(db_path: str = "podcast_analyzer.db") -> List[Dict[str, Any]]:
    """Get all analyzed videos that are missing channel metadata"""
    videos = []
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT video_id, video_url, title
                FROM video_analyses 
                WHERE channel_name IS NULL OR channel_name = '' 
                   OR channel_id IS NULL OR channel_id = ''
                   OR published_at IS NULL OR published_at = ''
                ORDER BY created_at DESC
            """)
            videos = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching videos missing metadata: {e}")
    
    return videos

def update_video_metadata(video_id: str, metadata: Dict[str, Any], db_path: str = "podcast_analyzer.db") -> bool:
    """Update a video record with the fetched metadata"""
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                UPDATE video_analyses 
                SET channel_id = ?, channel_name = ?, published_at = ?
                WHERE video_id = ?
            """, (
                metadata.get('channel_id'),
                metadata.get('channel_name'),
                metadata.get('published_at'),
                video_id
            ))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating video {video_id}: {e}")
        return False

def main():
    """Main migration function"""
    print("🔄 Starting video metadata migration...")
    
    # Check if we have a config file
    try:
        # Initialize services
        youtube_service = YouTubeService()
    except FileNotFoundError:
        print("❌ Config file (config.yaml) not found.")
        print("💡 This script requires YouTube API credentials in config.yaml")
        print("Please create config.yaml with:")
        print("youtube_api_key: 'your_api_key_here'")
        return
    
    # Get videos missing metadata
    videos_to_update = get_videos_missing_metadata()
    
    if not videos_to_update:
        print("✅ No videos found missing metadata. Migration complete!")
        return
    
    print(f"📊 Found {len(videos_to_update)} videos missing metadata")
    
    updated_count = 0
    failed_count = 0
    
    for i, video in enumerate(videos_to_update, 1):
        video_id = video['video_id']
        video_url = video['video_url']
        title = video['title']
        
        print(f"[{i}/{len(videos_to_update)}] Processing: {title[:50]}...")
        
        try:
            # Fetch video info from YouTube API
            video_info = youtube_service.get_video_info(video_url)
            
            if video_info:
                # Update database with fetched metadata
                if update_video_metadata(video_id, video_info):
                    updated_count += 1
                    print(f"  ✅ Updated: {video_info.get('channel_name', 'Unknown Channel')}")
                else:
                    failed_count += 1
                    print(f"  ❌ Failed to update database for {video_id}")
            else:
                failed_count += 1
                print(f"  ⚠️  Could not fetch video info for {video_id}")
                
        except Exception as e:
            failed_count += 1
            print(f"  ❌ Error processing {video_id}: {e}")
        
        # Rate limiting - be nice to YouTube API
        if i % 10 == 0:
            print("⏱️  Pausing for rate limiting...")
            time.sleep(1)
    
    print(f"\n🎉 Migration complete!")
    print(f"✅ Successfully updated: {updated_count} videos")
    print(f"❌ Failed to update: {failed_count} videos")
    print(f"📊 Total processed: {len(videos_to_update)} videos")

if __name__ == "__main__":
    main()