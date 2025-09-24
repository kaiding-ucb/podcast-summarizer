#!/usr/bin/env python3
"""
Migration script to backfill missing metadata for existing video analyses.

This script:
1. Queries video_analyses table for records with missing channel_name, channel_id, or published_at
2. Uses YouTube API to fetch missing metadata
3. Updates the database records with the fetched metadata

Usage:
    python scripts/backfill_metadata.py
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add parent directory to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.youtube_service import YouTubeService
from services.database import DatabaseService

def main():
    print("🔄 Starting metadata backfill process...")
    
    # Initialize services
    youtube_service = YouTubeService()
    db_service = DatabaseService()
    
    # Query records with missing metadata
    try:
        with sqlite3.connect(db_service.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT video_id, video_url, title, channel_name, channel_id, published_at, video_duration
                FROM video_analyses 
                WHERE channel_name IS NULL OR channel_id IS NULL OR published_at IS NULL OR video_duration IS NULL OR video_duration = 0
                ORDER BY created_at DESC
            """)
            records_to_update = cursor.fetchall()
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return
    
    if not records_to_update:
        print("✅ No records need metadata backfilling.")
        return
    
    print(f"📊 Found {len(records_to_update)} records that need metadata updates")
    
    updated_count = 0
    failed_count = 0
    
    for record in records_to_update:
        video_id = record['video_id']
        video_url = record['video_url']
        
        print(f"🔍 Processing video: {record['title'][:50]}...")
        
        try:
            # Fetch video info from YouTube API
            video_info = youtube_service.get_video_info(video_url)
            
            if video_info:
                # Update the database record
                with sqlite3.connect(db_service.db_path) as conn:
                    conn.execute("""
                        UPDATE video_analyses 
                        SET channel_name = ?, channel_id = ?, published_at = ?, video_duration = ?
                        WHERE video_id = ?
                    """, (
                        video_info.get('channel_name'),
                        video_info.get('channel_id'),
                        video_info.get('published_at'),
                        video_info.get('duration', 0),
                        video_id
                    ))
                    conn.commit()
                
                updated_count += 1
                print(f"✅ Updated metadata for video: {video_id}")
                
            else:
                failed_count += 1
                print(f"❌ Could not fetch metadata for video: {video_id}")
                
        except Exception as e:
            failed_count += 1
            print(f"❌ Error processing video {video_id}: {e}")
            continue
    
    print(f"\n📈 Backfill complete!")
    print(f"✅ Successfully updated: {updated_count} records")
    print(f"❌ Failed to update: {failed_count} records")

if __name__ == "__main__":
    main()