from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models import DiscoveryResponse, VideoInfo, BatchAnalysisRequest, BatchAnalysisResponse, AnalysesResponse, VideoAnalysisResponse, PaginatedAnalysesResponse, BatchAnalyzeSelectedRequest, ReAnalysisRequest, ReAnalyzeFailedResponse
from services.youtube_service import YouTubeService
from services.database import DatabaseService
from services.batch_analyzer import BatchAnalyzer, get_batch_progress
from services.gemini_analyzer import GeminiAnalyzer
import yaml
import asyncio
from datetime import datetime
from googleapiclient.errors import HttpError

router = APIRouter(prefix="/api", tags=["discovery"])

@router.get("/discover", response_model=DiscoveryResponse)
async def discover_new_videos(days_back: int = None):
    """Discover new videos from trusted channels within specified days"""
    try:
        # Load trusted channels from config
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        
        channels = config.get('channels', [])
        if not channels:
            raise HTTPException(status_code=400, detail="No trusted channels configured")
        
        if days_back is None:
            days_back = config.get('discovery_days_back', 7)
        
        # Initialize services
        youtube_service = YouTubeService()
        db_service = DatabaseService()
        
        # Discover videos from the last N days
        discovered_videos = youtube_service.get_recent_channel_videos(channels, days_back=days_back)
        
        # Save discovered videos to database and check if analyzed
        for video in discovered_videos:
            db_service.save_discovered_video(video)
            # Check if video is already analyzed
            analysis = db_service.get_analysis(video['video_id'])
            video['analyzed'] = analysis is not None
        
        # Convert to response format
        video_infos = [VideoInfo(**video) for video in discovered_videos]
        
        return DiscoveryResponse(
            videos=video_infos,
            total_count=len(video_infos)
        )
        
    except HttpError as e:
        if "quotaExceeded" in str(e):
            raise HTTPException(status_code=429, detail="YouTube API quota exceeded. Please wait 24 hours before discovering new videos.")
        else:
            raise HTTPException(status_code=500, detail=f"YouTube API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

@router.get("/recent", response_model=DiscoveryResponse)
async def get_recent_videos(limit: int = 20):
    """Get recently discovered videos from database"""
    try:
        db_service = DatabaseService()
        recent_videos = db_service.get_recent_videos(limit)
        
        # Check if videos are analyzed
        for video in recent_videos:
            analysis = db_service.get_analysis(video['video_id'])
            video['analyzed'] = analysis is not None
        
        video_infos = [VideoInfo(**video) for video in recent_videos]
        
        return DiscoveryResponse(
            videos=video_infos,
            total_count=len(video_infos)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent videos: {str(e)}")

@router.post("/batch-analyze", response_model=BatchAnalysisResponse)
async def batch_analyze_videos(request: BatchAnalysisRequest, background_tasks: BackgroundTasks):
    """Trigger batch analysis of recent videos from trusted channels"""
    try:
        batch_analyzer = BatchAnalyzer()
        
        # Run analysis asynchronously
        result = await batch_analyzer.analyze_recent_videos(days_back=request.days_back)
        
        return BatchAnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.post("/batch-analyze-selected", response_model=BatchAnalysisResponse)
async def batch_analyze_selected_videos(request: BatchAnalyzeSelectedRequest):
    """Trigger batch analysis for specifically selected videos"""
    try:
        batch_analyzer = BatchAnalyzer()
        youtube_service = YouTubeService()
        
        # Create video objects from URLs
        videos_to_analyze = []
        for i, url in enumerate(request.video_urls):
            # Handle test URLs for testing purposes
            if "youtube.com/watch?v=test" in url:
                video_id = url.split("v=")[1]
                videos_to_analyze.append({
                    'video_id': video_id,
                    'url': url,
                    'title': f'Test Video {i+1}',
                    'channel_id': 'test_channel',
                    'channel_name': 'Test Channel',
                    'published_at': '2024-01-01',
                    'duration': 600
                })
            else:
                video_info = youtube_service.get_video_info(url)
                if video_info:
                    videos_to_analyze.append({
                        'video_id': video_info['video_id'],
                        'url': url,
                        'title': video_info['title'],
                        'channel_id': video_info.get('channel_id'),
                        'channel_name': video_info.get('channel_name'),
                        'published_at': video_info.get('published_at'),
                        'duration': video_info.get('duration', 0)
                    })
        
        # Override the discovery to use our selected videos
        batch_analyzer.youtube_service.get_recent_channel_videos = lambda *args, **kwargs: videos_to_analyze
        
        # Run batch analysis
        result = await batch_analyzer.analyze_recent_videos(days_back=1)
        
        return BatchAnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis of selected videos failed: {str(e)}")

@router.post("/mock-batch-analyze", response_model=BatchAnalysisResponse)
async def mock_batch_analyze_videos(request: BatchAnalysisRequest):
    """Trigger MOCK batch analysis for testing latency - doesn't populate dashboard"""
    try:
        # Use mock mode to avoid database writes and API calls
        batch_analyzer = BatchAnalyzer(mock_mode=True)
        
        # Create fake recent videos for testing
        fake_videos = [
            {
                'video_id': f'mock_video_{i}', 
                'url': f'https://youtube.com/watch?v=mock{i}',
                'title': f'Mock Video {i} - Performance Testing',
                'channel_id': 'mock_channel',
                'channel_name': 'Mock Channel',
                'published_at': '2024-01-01',
                'duration': 1200
            } for i in range(10)  # Create 10 mock videos for testing
        ]
        
        # Override the discovery to use our fake videos
        batch_analyzer.youtube_service.get_recent_channel_videos = lambda channels, days_back: fake_videos
        
        # Run mock analysis asynchronously 
        result = await batch_analyzer.analyze_recent_videos(days_back=request.days_back)
        
        return BatchAnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mock batch analysis failed: {str(e)}")

@router.get("/analyses", response_model=PaginatedAnalysesResponse)
async def get_all_analyses(channel_id: str = None, page: int = 1, page_size: int = 10):
    """Get paginated analyses, optionally filtered by channel"""
    try:
        db_service = DatabaseService()
        
        # Validate pagination parameters
        page = max(1, page)  # Ensure page is at least 1
        page_size = max(1, min(50, page_size))  # Ensure page_size is between 1 and 50
        
        paginated_data = db_service.get_paginated_analyses(
            page=page, 
            page_size=page_size, 
            channel_id=channel_id
        )
        
        # Convert to response format
        analysis_responses = []
        for analysis in paginated_data['analyses']:
            # Handle datetime conversion
            if isinstance(analysis.get('created_at'), str):
                analysis['created_at'] = datetime.fromisoformat(analysis['created_at'])
            analysis_responses.append(VideoAnalysisResponse(**analysis))
        
        return PaginatedAnalysesResponse(
            analyses=analysis_responses,
            total_count=paginated_data['total_count'],
            page=paginated_data['page'],
            page_size=paginated_data['page_size'],
            total_pages=paginated_data['total_pages'],
            has_next=paginated_data['has_next'],
            has_prev=paginated_data['has_prev']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analyses: {str(e)}")

@router.get("/analyses/recent", response_model=PaginatedAnalysesResponse)
async def get_recent_analyses(days: int = 7, channel_id: str = None, page: int = 1, page_size: int = 10):
    """Get paginated recent analyses from the last N days, optionally filtered by channel"""
    try:
        db_service = DatabaseService()
        
        # For recent analyses, we'll get all recent ones first, then paginate
        # This is simpler than creating a separate paginated recent method
        all_recent = db_service.get_recent_analyses(days=days, channel_id=channel_id)
        
        # Validate pagination parameters
        page = max(1, page)
        page_size = max(1, min(50, page_size))
        
        # Calculate pagination manually
        total_count = len(all_recent)
        total_pages = (total_count + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_analyses = all_recent[start_idx:end_idx]
        
        # Convert to response format
        analysis_responses = []
        for analysis in paginated_analyses:
            # Handle datetime conversion
            if isinstance(analysis.get('created_at'), str):
                analysis['created_at'] = datetime.fromisoformat(analysis['created_at'])
            analysis_responses.append(VideoAnalysisResponse(**analysis))
        
        return PaginatedAnalysesResponse(
            analyses=analysis_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent analyses: {str(e)}")

@router.get("/batch-progress/{batch_id}")
async def get_batch_analysis_progress(batch_id: str):
    """Get real-time progress for a batch analysis"""
    try:
        progress = get_batch_progress(batch_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch progress: {str(e)}")

@router.get("/channels")
async def get_available_channels():
    """Get all available channels from database and config"""
    try:
        db_service = DatabaseService()

        # Get channels from config
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        config_channels = config.get('channels', [])

        # Only return channels from config.yaml
        channels_list = []
        for ch in config_channels:
            channels_list.append({
                'channel_id': ch['channel_id'],
                'name': ch['name']
            })

        # Sort by name
        channels_list.sort(key=lambda x: x['name'])

        return {"channels": channels_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get channels: {str(e)}")

@router.post("/re-analyze/{video_id}", response_model=VideoAnalysisResponse)
async def re_analyze_video(video_id: str):
    """Re-analyze a single video by video_id"""
    try:
        db_service = DatabaseService()
        youtube_service = YouTubeService()
        analyzer = GeminiAnalyzer()

        # Get existing analysis
        existing_analysis = db_service.get_analysis(video_id)
        if not existing_analysis:
            raise HTTPException(status_code=404, detail=f"No analysis found for video_id: {video_id}")

        video_url = existing_analysis['video_url']

        # Get video info
        video_info = youtube_service.get_video_info(video_url)
        if not video_info:
            raise HTTPException(status_code=400, detail="Could not retrieve video information")

        # Perform re-analysis with retry logic
        analysis_result = analyzer.analyze_video(video_url, video_duration=video_info.get('duration'))

        # Prepare data for storage
        analysis_data = {
            'video_id': video_id,
            'video_url': video_url,
            'title': video_info['title'],
            'analysis': analysis_result.get('analysis', ''),
            'channel_id': video_info.get('channel_id'),
            'channel_name': video_info.get('channel_name'),
            'published_at': video_info.get('published_at'),
            'video_duration': analysis_result.get('video_duration', video_info.get('duration', 0)),
            'timestamps_valid': analysis_result.get('timestamps_valid', False),
            'vaneck_excluded': analysis_result.get('vaneck_excluded', False),
            'success': analysis_result.get('success', False),
            'error': analysis_result.get('error'),
            'created_at': datetime.now()
        }

        # Update database
        db_service.save_analysis(analysis_data)
        db_service.mark_video_analyzed(video_id)

        return VideoAnalysisResponse(**analysis_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-analysis failed: {str(e)}")

@router.post("/re-analyze-failed", response_model=ReAnalyzeFailedResponse)
async def re_analyze_failed_videos():
    """Re-analyze all videos with success=0"""
    try:
        db_service = DatabaseService()
        youtube_service = YouTubeService()
        analyzer = GeminiAnalyzer()

        # Get all failed analyses
        all_analyses = db_service.get_all_analyses()
        failed_analyses = [a for a in all_analyses if not a.get('success', True)]

        total_failed = len(failed_analyses)
        results = []
        re_analyzed = 0
        still_failed = 0

        for analysis in failed_analyses:
            video_id = analysis['video_id']
            video_url = analysis['video_url']

            try:
                # Get fresh video info
                video_info = youtube_service.get_video_info(video_url)
                if not video_info:
                    results.append({
                        'video_id': video_id,
                        'title': analysis['title'],
                        'status': 'failed',
                        'error': 'Could not retrieve video info'
                    })
                    still_failed += 1
                    continue

                # Perform re-analysis with retry logic
                analysis_result = analyzer.analyze_video(video_url, video_duration=video_info.get('duration'))

                # Prepare data for storage
                analysis_data = {
                    'video_id': video_id,
                    'video_url': video_url,
                    'title': video_info['title'],
                    'analysis': analysis_result.get('analysis', ''),
                    'channel_id': video_info.get('channel_id'),
                    'channel_name': video_info.get('channel_name'),
                    'published_at': video_info.get('published_at'),
                    'video_duration': analysis_result.get('video_duration', video_info.get('duration', 0)),
                    'timestamps_valid': analysis_result.get('timestamps_valid', False),
                    'vaneck_excluded': analysis_result.get('vaneck_excluded', False),
                    'success': analysis_result.get('success', False),
                    'error': analysis_result.get('error'),
                    'created_at': datetime.now()
                }

                # Update database
                db_service.save_analysis(analysis_data)
                db_service.mark_video_analyzed(video_id)

                if analysis_result.get('success'):
                    re_analyzed += 1
                    results.append({
                        'video_id': video_id,
                        'title': video_info['title'],
                        'status': 'success'
                    })
                else:
                    still_failed += 1
                    results.append({
                        'video_id': video_id,
                        'title': video_info['title'],
                        'status': 'failed',
                        'error': analysis_result.get('error', 'Unknown error')
                    })

            except Exception as e:
                still_failed += 1
                results.append({
                    'video_id': video_id,
                    'title': analysis.get('title', 'Unknown'),
                    'status': 'failed',
                    'error': str(e)
                })

        return ReAnalyzeFailedResponse(
            total_failed=total_failed,
            re_analyzed=re_analyzed,
            still_failed=still_failed,
            results=results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk re-analysis failed: {str(e)}")