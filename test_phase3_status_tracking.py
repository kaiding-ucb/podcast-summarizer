#!/usr/bin/env python3

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database import DatabaseService

class TestPhase3StatusTracking:
    """Test suite for Phase 3: Status Tracking"""
    
    def test_database_has_in_progress_column(self):
        """Test that discovered_videos table has in_progress column"""
        db_service = DatabaseService("test_phase3.db")
        
        # Clean up test database
        if os.path.exists("test_phase3.db"):
            os.remove("test_phase3.db")
        
        db_service = DatabaseService("test_phase3.db")
        
        # Check table schema
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(discovered_videos)")
            columns = cursor.fetchall()
            
            column_names = [col[1] for col in columns]
            assert 'in_progress' in column_names, f"in_progress column missing. Found columns: {column_names}"
        
        print("✅ Database has in_progress column")
        
        # Clean up
        if os.path.exists("test_phase3.db"):
            os.remove("test_phase3.db")
    
    def test_mark_video_in_progress_functionality(self):
        """Test marking video as in_progress works correctly"""
        db_service = DatabaseService("test_phase3.db")
        
        # Clean up test database
        if os.path.exists("test_phase3.db"):
            os.remove("test_phase3.db")
        
        db_service = DatabaseService("test_phase3.db")
        
        # Create a test video
        test_video = {
            'video_id': 'test_video_123',
            'title': 'Test Video',
            'url': 'https://youtube.com/watch?v=test_video_123',
            'channel_name': 'Test Channel',
            'channel_id': 'test_channel',
            'duration': 600,
            'published_at': '2024-01-01'
        }
        
        # Save video
        db_service.save_discovered_video(test_video)
        
        # Mark as in_progress
        success = db_service.mark_video_in_progress(test_video['video_id'])
        assert success, "Should successfully mark video as in_progress"
        
        # Verify it's marked as in_progress
        video = db_service.get_discovered_video(test_video['video_id'])
        assert video is not None, "Video should exist"
        assert video['in_progress'] == True, "Video should be marked as in_progress"
        
        # Clear in_progress status
        success = db_service.clear_video_in_progress(test_video['video_id'])
        assert success, "Should successfully clear in_progress status"
        
        # Verify it's no longer in_progress
        video = db_service.get_discovered_video(test_video['video_id'])
        assert video['in_progress'] == False, "Video should no longer be in_progress"
        
        print("✅ Mark video in_progress functionality works correctly")
        
        # Clean up
        if os.path.exists("test_phase3.db"):
            os.remove("test_phase3.db")
    
    def test_multiple_videos_can_be_in_progress_simultaneously(self):
        """Test that multiple videos can be in_progress at the same time"""
        db_service = DatabaseService("test_phase3.db")
        
        # Clean up test database
        if os.path.exists("test_phase3.db"):
            os.remove("test_phase3.db")
        
        db_service = DatabaseService("test_phase3.db")
        
        # Create test videos
        test_videos = [
            {
                'video_id': f'test_video_{i}',
                'title': f'Test Video {i}',
                'url': f'https://youtube.com/watch?v=test_video_{i}',
                'channel_name': 'Test Channel',
                'channel_id': 'test_channel',
                'duration': 600,
                'published_at': '2024-01-01'
            }
            for i in range(3)
        ]
        
        # Save videos
        for video in test_videos:
            db_service.save_discovered_video(video)
        
        # Mark all as in_progress
        for video in test_videos:
            success = db_service.mark_video_in_progress(video['video_id'])
            assert success, f"Should mark video {video['video_id']} as in_progress"
        
        # Verify all are in_progress
        in_progress_count = 0
        for video in test_videos:
            db_video = db_service.get_discovered_video(video['video_id'])
            if db_video and db_video['in_progress']:
                in_progress_count += 1
        
        assert in_progress_count == 3, f"Expected 3 videos in_progress, got {in_progress_count}"
        
        print("✅ Multiple videos can be in_progress simultaneously")
        
        # Clean up
        if os.path.exists("test_phase3.db"):
            os.remove("test_phase3.db")

def run_tests():
    """Run all Phase 3 tests"""
    print("\n" + "="*60)
    print("🧪 Running Phase 3 Tests: Status Tracking")
    print("="*60 + "\n")
    
    # Run pytest with verbose output
    pytest.main([__file__, "-v", "-s"])

if __name__ == "__main__":
    run_tests()