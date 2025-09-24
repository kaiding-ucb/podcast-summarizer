import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
import os

class DatabaseService:
    def __init__(self, db_path: str = "podcast_analyzer.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS video_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    video_url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    analysis TEXT NOT NULL,
                    channel_id TEXT,
                    channel_name TEXT,
                    published_at TEXT,
                    video_duration INTEGER DEFAULT 0,
                    timestamps_valid BOOLEAN DEFAULT FALSE,
                    vaneck_excluded BOOLEAN DEFAULT FALSE,
                    success BOOLEAN DEFAULT FALSE,
                    error TEXT,
                    batch_analysis_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS discovered_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    channel_id TEXT,
                    duration INTEGER DEFAULT 0,
                    published_at TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    analyzed BOOLEAN DEFAULT FALSE,
                    excluded_from_analysis BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_published_at ON video_analyses(published_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_batch_id ON video_analyses(batch_analysis_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_video_published ON discovered_videos(published_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analyzed ON discovered_videos(analyzed)")
            
            conn.commit()

    def save_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """Save video analysis to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO video_analyses 
                    (video_id, video_url, title, analysis, channel_id, channel_name, published_at,
                     video_duration, timestamps_valid, vaneck_excluded, success, error, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_data['video_id'],
                    analysis_data['video_url'],
                    analysis_data['title'],
                    analysis_data['analysis'],
                    analysis_data.get('channel_id'),
                    analysis_data.get('channel_name'),
                    analysis_data.get('published_at'),
                    analysis_data.get('video_duration', 0),
                    analysis_data.get('timestamps_valid', False),
                    analysis_data.get('vaneck_excluded', False),
                    analysis_data.get('success', False),
                    analysis_data.get('error'),
                    analysis_data.get('created_at', datetime.now())
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False

    def get_analysis(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis for a video"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM video_analyses WHERE video_id = ?
                """, (video_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            print(f"Error retrieving analysis: {e}")
            return None

    def save_discovered_video(self, video_data: Dict[str, Any]) -> bool:
        """Save discovered video to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO discovered_videos 
                    (video_id, title, url, channel_name, channel_id, duration, published_at, excluded_from_analysis)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_data['video_id'],
                    video_data['title'],
                    video_data['url'],
                    video_data['channel_name'],
                    video_data.get('channel_id'),
                    video_data.get('duration', 0),
                    video_data.get('published_at'),
                    video_data.get('excluded_from_analysis', False)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving discovered video: {e}")
            return False

    def get_recent_videos(self, limit: int = 20) -> list[Dict[str, Any]]:
        """Get recently discovered videos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM discovered_videos 
                    ORDER BY discovered_at DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving recent videos: {e}")
            return []
    
    def get_unanalyzed_videos(self) -> list[Dict[str, Any]]:
        """Get videos that haven't been analyzed yet"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT dv.* FROM discovered_videos dv
                    LEFT JOIN video_analyses va ON dv.video_id = va.video_id
                    WHERE (va.video_id IS NULL OR dv.analyzed = 0) 
                    AND dv.excluded_from_analysis = 0
                    ORDER BY dv.published_at DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving unanalyzed videos: {e}")
            return []
    
    def mark_video_analyzed(self, video_id: str) -> bool:
        """Mark a video as analyzed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE discovered_videos 
                    SET analyzed = 1 
                    WHERE video_id = ?
                """, (video_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error marking video as analyzed: {e}")
            return False
    
    def get_recent_analyses(self, days: int = 7) -> list[Dict[str, Any]]:
        """Get analyses from the last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM video_analyses 
                    WHERE datetime(created_at) >= datetime('now', '-' || ? || ' days')
                    ORDER BY created_at DESC
                """, (days,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving recent analyses: {e}")
            return []
    
    def get_all_analyses(self, channel_id: str = None) -> list[Dict[str, Any]]:
        """Get all analyses, optionally filtered by channel"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if channel_id:
                    cursor = conn.execute("""
                        SELECT * FROM video_analyses 
                        WHERE channel_id = ?
                        ORDER BY published_at DESC
                    """, (channel_id,))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM video_analyses 
                        ORDER BY published_at DESC
                    """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving analyses: {e}")
            return []
    
    def get_paginated_analyses(self, page: int = 1, page_size: int = 10, channel_id: str = None) -> dict:
        """Get paginated analyses with metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Calculate offset
                offset = (page - 1) * page_size
                
                # Get total count
                if channel_id:
                    count_cursor = conn.execute("""
                        SELECT COUNT(*) as total FROM video_analyses 
                        WHERE channel_id = ?
                    """, (channel_id,))
                    total_count = count_cursor.fetchone()['total']
                    
                    # Get paginated results
                    cursor = conn.execute("""
                        SELECT * FROM video_analyses 
                        WHERE channel_id = ?
                        ORDER BY 
                            CASE WHEN published_at IS NULL OR published_at = '' THEN 1 ELSE 0 END,
                            published_at DESC
                        LIMIT ? OFFSET ?
                    """, (channel_id, page_size, offset))
                else:
                    count_cursor = conn.execute("SELECT COUNT(*) as total FROM video_analyses")
                    total_count = count_cursor.fetchone()['total']
                    
                    # Get paginated results
                    cursor = conn.execute("""
                        SELECT * FROM video_analyses 
                        ORDER BY 
                            CASE WHEN published_at IS NULL OR published_at = '' THEN 1 ELSE 0 END,
                            published_at DESC
                        LIMIT ? OFFSET ?
                    """, (page_size, offset))
                
                analyses = [dict(row) for row in cursor.fetchall()]
                
                # Calculate pagination metadata
                total_pages = (total_count + page_size - 1) // page_size
                has_next = page < total_pages
                has_prev = page > 1
                
                return {
                    'analyses': analyses,
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev
                }
                
        except Exception as e:
            print(f"Error retrieving paginated analyses: {e}")
            return {
                'analyses': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'has_next': False,
                'has_prev': False
            }