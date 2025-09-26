from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class VideoAnalysisRequest(BaseModel):
    video_url: str

class VideoAnalysisResponse(BaseModel):
    video_id: str
    video_url: str
    title: str
    analysis: str
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    published_at: Optional[str] = None
    video_duration: int
    timestamps_valid: bool
    vaneck_excluded: bool
    success: bool
    error: Optional[str] = None
    created_at: datetime

class VideoInfo(BaseModel):
    video_id: str
    title: str
    url: str
    channel_name: str
    channel_id: Optional[str] = None
    duration: int
    published_at: str
    analyzed: Optional[bool] = False
    excluded_from_analysis: Optional[bool] = False

class DiscoveryResponse(BaseModel):
    videos: List[VideoInfo]
    total_count: int

class BatchAnalysisRequest(BaseModel):
    days_back: Optional[int] = 7

class BatchAnalyzeSelectedRequest(BaseModel):
    video_urls: List[str]

class BatchAnalysisResponse(BaseModel):
    batch_id: str
    started_at: str
    completed_at: Optional[str] = None
    total_videos: int
    analyzed: int
    failed: int
    videos: List[dict]

class AnalysesResponse(BaseModel):
    analyses: List[VideoAnalysisResponse]
    total_count: int

class PaginatedAnalysesResponse(BaseModel):
    analyses: List[VideoAnalysisResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool