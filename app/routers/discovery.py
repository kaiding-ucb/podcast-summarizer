from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models import DiscoveryResponse, VideoInfo, BatchAnalysisRequest, BatchAnalysisResponse, AnalysesResponse, VideoAnalysisResponse, PaginatedAnalysesResponse
from services.youtube_service import YouTubeService
from services.database import DatabaseService
from services.batch_analyzer import BatchAnalyzer
import yaml
import asyncio
from datetime import datetime

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
async def get_recent_analyses(days: int = 7, page: int = 1, page_size: int = 10):
    """Get paginated recent analyses from the last N days"""
    try:
        db_service = DatabaseService()
        
        # For recent analyses, we'll get all recent ones first, then paginate
        # This is simpler than creating a separate paginated recent method
        all_recent = db_service.get_recent_analyses(days=days)
        
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