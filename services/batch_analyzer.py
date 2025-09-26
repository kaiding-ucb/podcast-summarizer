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

# In-memory progress tracking
_batch_progress = {}

def get_batch_progress(batch_id: str) -> Dict[str, Any]:
    """Get progress for a specific batch"""
    return _batch_progress.get(batch_id, {})

def update_batch_progress(batch_id: str, completed: int, total: int, current_video: str = None, failed: int = 0):
    """Update progress for a specific batch"""
    _batch_progress[batch_id] = {
        'completed': completed,
        'total': total,
        'failed': failed,
        'current_video': current_video,
        'percent': int((completed / total) * 100) if total > 0 else 0,
        'status': 'completed' if completed == total else 'in_progress',
        'last_updated': datetime.now().isoformat()
    }

class BatchAnalyzer:
    def __init__(self, config_path: str = "config.yaml", mock_mode: bool = False):
        self.analyzer = GeminiAnalyzer(config_path)
        self.youtube_service = YouTubeService(config_path)
        self.db_service = DatabaseService()
        self.mock_mode = mock_mode
        
        # Thread pool for non-blocking analysis
        self.thread_pool = ThreadPoolExecutor(max_workers=8)
        
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
    
    async def analyze_single_video(self, video: Dict[str, Any], batch_id: str, index: int, total: int) -> Dict[str, Any]:
        """Analyze a single video - helper method for parallel processing"""
        video_id = video['video_id']
        video_url = video['url']
        
        # Check if already analyzed
        existing_analysis = self.db_service.get_analysis(video_id)
        if existing_analysis:
            print(f"[{index}/{total}] Skipping {video['title']} - already analyzed")
            return {
                'video_id': video_id,
                'title': video['title'],
                'status': 'already_analyzed'
            }
        
        print(f"[{index}/{total}] Analyzing: {video['title']}")
        
        # Update progress - starting this video
        update_batch_progress(batch_id, index-1, total, current_video=video['title'])
        
        # Mark video as in_progress
        self.db_service.mark_video_in_progress(video_id)
        
        try:
            # Perform analysis using thread pool to avoid blocking
            if self.mock_mode:
                # Use mock analysis that doesn't populate dashboard
                analysis_result = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool, self.mock_analyze_video, video_url
                )
                # Skip database save for mock mode
                print(f"Mock analysis completed for: {video['title']}")
                # Clear in_progress status
                self.db_service.clear_video_in_progress(video_id)
                # Update progress - completed this video
                update_batch_progress(batch_id, index, total, current_video=None)
                return {
                    'video_id': video_id,
                    'title': video['title'],
                    'status': 'mock_completed',
                    'analyzed': True
                }
            else:
                # Real analysis using thread pool with video duration
                video_duration = video.get('duration', 0)
                analysis_result = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool, self.analyzer.analyze_video, video_url, video_duration
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
                # Clear in_progress status
                self.db_service.clear_video_in_progress(video_id)
                # Update progress - completed this video successfully
                update_batch_progress(batch_id, index, total, current_video=None)
                return {
                    'video_id': video_id,
                    'title': video['title'],
                    'status': 'success',
                    'analysis_summary': analysis_result.get('analysis', '')[:200] + '...',
                    'analyzed': True
                }
            else:
                # Clear in_progress status even on save failure
                self.db_service.clear_video_in_progress(video_id)
                # Update progress - failed to save
                update_batch_progress(batch_id, index-1, total, current_video=None, failed=1)
                return {
                    'video_id': video_id,
                    'title': video['title'],
                    'status': 'save_failed',
                    'analyzed': False
                }
                
        except Exception as e:
            print(f"Error analyzing video {video_id}: {e}")
            # Clear in_progress status on error
            self.db_service.clear_video_in_progress(video_id)
            # Update progress - failed with error
            update_batch_progress(batch_id, index-1, total, current_video=None, failed=1)
            return {
                'video_id': video_id,
                'title': video['title'],
                'status': 'error',
                'error': str(e),
                'analyzed': False
            }
    
    async def analyze_recent_videos(self, days_back: int = None) -> Dict[str, Any]:
        """Analyze all recent videos from trusted channels with parallel processing"""
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
        
        # Initialize progress tracking
        update_batch_progress(batch_id, 0, len(recent_videos))
        
        # Save discovered videos to database
        for video in recent_videos:
            self.db_service.save_discovered_video(video)
        
        # Create tasks for parallel processing
        tasks = []
        for i, video in enumerate(recent_videos, 1):
            task = self.analyze_single_video(video, batch_id, i, len(recent_videos))
            tasks.append(task)
            
            # Add a small delay between task creation to avoid overwhelming the API
            # This delay is only for starting tasks, not between completions
            if not self.mock_mode and i < len(recent_videos):
                await asyncio.sleep(0.25)  # Small delay just for task creation
        
        # Process all videos in parallel
        video_results = await asyncio.gather(*tasks)
        
        # Process results
        for result in video_results:
            results['videos'].append(result)
            if result.get('analyzed'):
                results['analyzed'] += 1
            elif result['status'] == 'error' or result['status'] == 'save_failed':
                results['failed'] += 1
        
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