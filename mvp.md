# Updated Podcast Summarizer MVP - 3-Stage Development Plan

## Codebase Structure
```
podcast-summarizer/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # Data models
│   └── routers/
│       ├── analysis.py      # Video analysis endpoints
│       └── discovery.py     # Video discovery endpoints
├── services/
│   ├── gemini_analyzer.py   # Gemini video analysis service
│   ├── youtube_service.py   # YouTube API integration
│   └── database.py          # Simple SQLite database
├── static/                  # CSS, JS files
├── templates/               # HTML templates
├── plans_tests/             # TDD structure per CLAUDE.md
│   ├── stage1_video_analysis/
│   ├── stage2_fastapi_backend/
│   └── stage3_frontend_discovery/
├── config.yaml              # (existing)
└── requirements.txt
```

## Stage 1: Core Video Analysis Engine
**Goal:** Set up gemini-2.5-flash video analysis with exact prompt requirements

**Features:**
- Gemini client setup with media_resolution='MEDIA_RESOLUTION_LOW'
- Video analysis function using the specified investment recommendation prompt from CLAUDE.md
- YouTube URL validation and processing
- Video duration validation for timestamp checking

**Specific Tests with Success Criteria:**
- **Test Video 1:** https://www.youtube.com/watch?v=699dsom_fuM
- **Test Video 2:** https://www.youtube.com/watch?v=Er6M5gQiLRo

**Success Criteria:**
1. **Format Compliance:** Analysis output must match exact format from CLAUDE.md:
   - Contains "Recommendation:" section
   - Has "Summary:" subsection
   - Has "Timestamps:" subsection with (MM:SS) format
   - Timestamps include quoted excerpts
2. **Timestamp Validation:** No timestamps exceed actual video length
3. **VanEck Ad Exclusion:** Results for both videos must exclude any VanEck ETF commercial content
4. **Investment Classification:** Correctly identifies if video has Stock/Sector/Portfolio strategy recommendations vs "Other"

## Stage 2: FastAPI Backend & Data Management
**Goal:** Create REST API endpoints with YouTube API integration

**Features:**
- FastAPI app with `/analyze` endpoint for video analysis
- SQLite database for storing analysis results
- YouTube API integration using specific endpoints:
  - `channels.list` to get channel's uploads playlist ID
  - `playlistItems.list` to fetch recent videos from trusted channels
  - `videos.list` to get video duration and metadata
- Config loading for trusted channels from config.yaml

**Specific Tests:**
- **API Endpoint Tests:**
  - POST `/analyze` with YouTube URL returns proper JSON response
  - GET `/results/{video_id}` retrieves stored analysis
  - GET `/discover` fetches latest videos from trusted channels
- **Database Tests:**
  - Save analysis results with video_id, title, analysis_text, created_at
  - Retrieve analysis by video_id
  - Handle duplicate video analysis requests
- **YouTube API Tests:**
  - Fetch latest 5 videos from Forward Guidance channel (UCkrwgzhIBKccuDsi_SvZtnQ)
  - Fetch latest 5 videos from Prof G Markets channel (UC1E1SVcVyU3ntWMSQEp38Yw)
  - Get video duration for timestamp validation

## Stage 3: Frontend UI & Discovery Feature
**Goal:** Complete web interface with browser-based testing

**Features:**
- Simple HTML interface for video analysis input
- "Discover New Videos" button for trusted channels
- Results display with clickable YouTube timestamps
- Responsive design with basic CSS styling

**Specific Tests (Manual/Automated):**
- **UI Rendering Tests:**
  - Home page loads with video URL input field
  - "Analyze Video" button is clickable
  - "Discover New Videos" button is present
- **Functionality Tests:**
  - Submit test video URL and verify analysis appears
  - Click "Discover New Videos" and verify channel videos display
  - Click timestamp links and verify they open correct YouTube time positions
- **End-to-End Test:**
  - Complete flow: Discover → Select video → Analyze → View results with working timestamp links

**Technical Implementation Details:**
- Use FastAPI's Jinja2 templates for HTML rendering
- SQLite database with tables: videos, analyses
- YouTube API calls with error handling and rate limiting
- JavaScript for timestamp link formatting: `https://www.youtube.com/watch?v={video_id}&t={seconds}s`