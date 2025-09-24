from fastapi import APIRouter, HTTPException
from app.models import VideoAnalysisRequest, VideoAnalysisResponse
from services.gemini_analyzer import GeminiAnalyzer
from services.youtube_service import YouTubeService
from services.database import DatabaseService
from datetime import datetime

router = APIRouter(prefix="/api", tags=["analysis"])

@router.post("/analyze", response_model=VideoAnalysisResponse)
async def analyze_video(request: VideoAnalysisRequest):
    """Analyze a YouTube video for investment recommendations"""
    try:
        # Initialize services
        analyzer = GeminiAnalyzer()
        youtube_service = YouTubeService()
        db_service = DatabaseService()
        
        # Get video info
        video_info = youtube_service.get_video_info(request.video_url)
        if not video_info:
            raise HTTPException(status_code=400, detail="Could not retrieve video information")
        
        video_id = video_info['video_id']
        
        # Check if analysis already exists
        existing_analysis = db_service.get_analysis(video_id)
        if existing_analysis:
            return VideoAnalysisResponse(**existing_analysis)
        
        # Perform analysis
        analysis_result = analyzer.analyze_video(request.video_url)
        
        # Prepare data for storage
        analysis_data = {
            'video_id': video_id,
            'video_url': request.video_url,
            'title': video_info['title'],
            'channel_name': video_info.get('channel_name'),
            'channel_id': video_info.get('channel_id'),
            'published_at': video_info.get('published_at'),
            'analysis': analysis_result.get('analysis', ''),
            'video_duration': analysis_result.get('video_duration', video_info.get('duration', 0)),
            'timestamps_valid': analysis_result.get('timestamps_valid', False),
            'vaneck_excluded': analysis_result.get('vaneck_excluded', False),
            'success': analysis_result.get('success', False),
            'error': analysis_result.get('error'),
            'created_at': datetime.now()
        }
        
        # Save to database
        db_service.save_analysis(analysis_data)
        
        # Mark video as analyzed in discovered_videos table
        db_service.mark_video_analyzed(video_id)
        
        return VideoAnalysisResponse(**analysis_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/results/{video_id}", response_model=VideoAnalysisResponse)
async def get_analysis_result(video_id: str):
    """Get stored analysis result for a video"""
    db_service = DatabaseService()
    analysis = db_service.get_analysis(video_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return VideoAnalysisResponse(**analysis)