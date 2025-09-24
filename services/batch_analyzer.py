import asyncio
from typing import List, Dict, Any
from datetime import datetime
import uuid
import yaml
import time
from concurrent.futures import ThreadPoolExecutor

from services.gemini_analyzer import GeminiAnalyzer
from services.youtube_service import YouTubeService
from services.database import DatabaseService

class BatchAnalyzer:
    def __init__(self, config_path: str = "config.yaml", mock_mode: bool = False):
        self.analyzer = GeminiAnalyzer(config_path)
        self.youtube_service = YouTubeService(config_path)
        self.db_service = DatabaseService()
        self.mock_mode = mock_mode
        
        # Thread pool for non-blocking analysis
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        self.channels = config.get('channels', [])
        self.discovery_days_back = config.get('discovery_days_back', 7)
    
    def mock_analyze_video(self, video_url: str) -> dict:
        """Mock video analysis that simulates blocking I/O without hitting APIs"""
        # Simulate the time it takes to analyze a video (3-5 seconds)
        time.sleep(4)
        return {
            "analysis": "**Mock Analysis Result** - This is a simulated analysis for testing purposes only.",
            "video_duration": 1200,  # 20 minutes
            "timestamps_valid": True,
            "vaneck_excluded": True,
            "success": True
        }
    
    async def analyze_recent_videos(self, days_back: int = None) -> Dict[str, Any]:
        """Analyze all recent videos from trusted channels"""
        if days_back is None:
            days_back = self.discovery_days_back
        
        batch_id = str(uuid.uuid4())
        results = {
            'batch_id': batch_id,
            'started_at': datetime.now().isoformat(),
            'total_videos': 0,
            'analyzed': 0,
            'failed': 0,
            'videos': []
        }
        
        # Get recent videos from all channels
        print(f"Discovering videos from last {days_back} days...")
        recent_videos = self.youtube_service.get_recent_channel_videos(
            self.channels, 
            days_back=days_back
        )
        
        results['total_videos'] = len(recent_videos)
        print(f"Found {len(recent_videos)} videos to analyze")
        
        # Save discovered videos to database
        for video in recent_videos:
            self.db_service.save_discovered_video(video)
        
        # Analyze each video
        for i, video in enumerate(recent_videos, 1):
            video_id = video['video_id']
            video_url = video['url']
            
            # Check if already analyzed
            existing_analysis = self.db_service.get_analysis(video_id)
            if existing_analysis:
                print(f"[{i}/{len(recent_videos)}] Skipping {video['title']} - already analyzed")
                results['videos'].append({
                    'video_id': video_id,
                    'title': video['title'],
                    'status': 'already_analyzed'
                })
                continue
            
            print(f"[{i}/{len(recent_videos)}] Analyzing: {video['title']}")
            
            try:
                # Perform analysis using thread pool to avoid blocking
                if self.mock_mode:
                    # Use mock analysis that doesn't populate dashboard
                    analysis_result = await asyncio.get_event_loop().run_in_executor(
                        self.thread_pool, self.mock_analyze_video, video_url
                    )
                    # Skip database save for mock mode
                    print(f"Mock analysis completed for: {video['title']}")
                    results['analyzed'] += 1
                    results['videos'].append({
                        'video_id': video_id,
                        'title': video['title'],
                        'status': 'mock_completed'
                    })
                    continue
                else:
                    # Real analysis using thread pool
                    analysis_result = await asyncio.get_event_loop().run_in_executor(
                        self.thread_pool, self.analyzer.analyze_video, video_url
                    )
                
                # Prepare data for storage (only in non-mock mode)
                analysis_data = {
                    'video_id': video_id,
                    'video_url': video_url,
                    'title': video['title'],
                    'channel_id': video.get('channel_id'),
                    'channel_name': video.get('channel_name'),
                    'published_at': video.get('published_at'),
                    'analysis': analysis_result.get('analysis', ''),
                    'video_duration': analysis_result.get('video_duration', video.get('duration', 0)),
                    'timestamps_valid': analysis_result.get('timestamps_valid', False),
                    'vaneck_excluded': analysis_result.get('vaneck_excluded', False),
                    'success': analysis_result.get('success', False),
                    'error': analysis_result.get('error'),
                    'batch_analysis_id': batch_id,
                    'created_at': datetime.now()
                }
                
                # Save to database
                if self.db_service.save_analysis(analysis_data):
                    self.db_service.mark_video_analyzed(video_id)
                    results['analyzed'] += 1
                    status = 'success'
                else:
                    results['failed'] += 1
                    status = 'save_failed'
                
                results['videos'].append({
                    'video_id': video_id,
                    'title': video['title'],
                    'status': status,
                    'analysis_summary': analysis_result.get('analysis', '')[:200] + '...'
                })
                
                # Small delay to avoid rate limiting (only in non-mock mode)
                if not self.mock_mode:
                    await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Error analyzing video {video_id}: {e}")
                results['failed'] += 1
                results['videos'].append({
                    'video_id': video_id,
                    'title': video['title'],
                    'status': 'error',
                    'error': str(e)
                })
        
        results['completed_at'] = datetime.now().isoformat()
        return results
    
    def get_unanalyzed_videos(self) -> List[Dict[str, Any]]:
        """Get list of videos that haven't been analyzed yet"""
        return self.db_service.get_unanalyzed_videos()
    
    async def analyze_unanalyzed_videos(self) -> Dict[str, Any]:
        """Analyze all unanalyzed videos in the database"""
        unanalyzed = self.get_unanalyzed_videos()
        
        batch_id = str(uuid.uuid4())
        results = {
            'batch_id': batch_id,
            'started_at': datetime.now().isoformat(),
            'total_videos': len(unanalyzed),
            'analyzed': 0,
            'failed': 0,
            'videos': []
        }
        
        print(f"Found {len(unanalyzed)} unanalyzed videos")
        
        for i, video in enumerate(unanalyzed, 1):
            video_id = video['video_id']
            video_url = video['url']
            
            print(f"[{i}/{len(unanalyzed)}] Analyzing: {video['title']}")
            
            try:
                # Perform analysis
                analysis_result = self.analyzer.analyze_video(video_url)
                
                # Prepare data for storage
                analysis_data = {
                    'video_id': video_id,
                    'video_url': video_url,
                    'title': video['title'],
                    'channel_id': video.get('channel_id'),
                    'channel_name': video.get('channel_name'),
                    'published_at': video.get('published_at'),
                    'analysis': analysis_result.get('analysis', ''),
                    'video_duration': analysis_result.get('video_duration', video.get('duration', 0)),
                    'timestamps_valid': analysis_result.get('timestamps_valid', False),
                    'vaneck_excluded': analysis_result.get('vaneck_excluded', False),
                    'success': analysis_result.get('success', False),
                    'error': analysis_result.get('error'),
                    'batch_analysis_id': batch_id,
                    'created_at': datetime.now()
                }
                
                # Save to database
                if self.db_service.save_analysis(analysis_data):
                    self.db_service.mark_video_analyzed(video_id)
                    results['analyzed'] += 1
                    status = 'success'
                else:
                    results['failed'] += 1
                    status = 'save_failed'
                
                results['videos'].append({
                    'video_id': video_id,
                    'title': video['title'],
                    'status': status
                })
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Error analyzing video {video_id}: {e}")
                results['failed'] += 1
                results['videos'].append({
                    'video_id': video_id,
                    'title': video['title'],
                    'status': 'error',
                    'error': str(e)
                })
        
        results['completed_at'] = datetime.now().isoformat()
        return results