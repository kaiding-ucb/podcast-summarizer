# Changelog

## [1.0.0] - 2025-01-24

### Initial MVP Release

#### Features Implemented

##### Core Video Analysis
- **Gemini 2.5 Flash Integration**: Successfully integrated Google's Gemini 2.5 Flash API for direct YouTube video analysis
  - Configured with `MEDIA_RESOLUTION_LOW` for efficient video processing
  - Implemented exact prompt template for investment insights extraction
  - Analyzes for: Stock recommendations, Sector recommendations, Portfolio strategies
  - Automatically excludes commercials and sponsor content (e.g., VanEck)
  - Returns summaries with clickable timestamps linking directly to video moments

##### Backend Infrastructure
- **FastAPI Web Framework**: Complete REST API implementation
  - `/api/analyze` - Single video analysis endpoint
  - `/api/discover` - Discover videos from trusted channels
  - `/api/batch-analyze` - Batch process multiple videos
  - `/api/analyses` - Retrieve stored analyses with filtering
  - `/api/recent` - Get recently discovered videos
  
- **SQLite Database**: Persistent storage system
  - `video_analyses` table - Stores complete analysis results
  - `discovered_videos` table - Tracks discovered channel videos
  - Performance indexes on published_at, batch_id, and analyzed status
  - Support for channel-filtered queries

- **YouTube Data API v3 Integration**
  - Fetches videos from trusted channels configured in config.yaml
  - Configurable lookback period (default: 7 days)
  - Extracts metadata: title, duration, published date
  - Efficient batch fetching from channel uploads playlists

##### Frontend User Interface
- **Responsive Web Interface**: HTMX-powered dynamic UI
  - **Home Page**: Single video analysis with real-time results
  - **Discovery Page**: Browse and analyze videos from trusted channels
    - Visual indicators for analyzed vs unanalyzed videos
    - "Discover New Videos" button for finding recent content
    - "Analyze All New Episodes" for batch processing
  - **Dashboard Page**: View all stored analyses
    - Filter by channel
    - Sort by date
    - Expandable analysis cards with full content

##### Batch Processing
- **Automated Batch Analysis**: Process multiple videos efficiently
  - Analyzes all unanalyzed videos from configured time period
  - Progress tracking with visual indicators
  - Error handling and retry logic
  - Marks videos as analyzed in database

#### Configuration
- **config.yaml**: Centralized configuration
  ```yaml
  discovery_days_back: 7  # Configurable lookback period
  channels:
    - channel_id: "UCkrwgzhIBKccuDsi_SvZtnQ"
      name: "Forward Guidance"
    - channel_id: "UCFFbwnve3yF62-tVXkTyHqg"
      name: "Meb Faber Research"
  ```

#### Technical Details

##### Dependencies
- google-genai (2.1.0) - Gemini API client
- fastapi - Web framework
- uvicorn - ASGI server
- pyyaml - Configuration management
- google-api-python-client - YouTube API
- jinja2 - Template engine
- sqlite3 - Database (built-in)

##### Project Structure
```
podcast-summarizer/
├── app/
│   ├── main.py           # FastAPI application
│   ├── models.py          # Pydantic models
│   └── routers/
│       ├── analysis.py    # Analysis endpoints
│       └── discovery.py   # Discovery & batch endpoints
├── services/
│   ├── gemini_analyzer.py  # Gemini 2.5 Flash integration
│   ├── youtube_service.py  # YouTube API client
│   ├── database.py         # SQLite operations
│   └── batch_analyzer.py   # Batch processing logic
├── templates/
│   ├── base.html          # Base template
│   ├── index.html         # Home/analysis page
│   ├── discover.html      # Discovery page
│   └── dashboard.html     # Dashboard page
├── static/
│   ├── style.css          # Styling
│   └── app.js             # JavaScript utilities
├── config.yaml            # Configuration file
└── requirements.txt       # Python dependencies
```

### Testing & Verification
- Successfully analyzed multiple test videos:
  - "699dsom_fuM" - Forward Guidance episode
  - "Er6M5gQiLRo" - Meb Faber episode
- Verified commercial exclusion (VanEck sponsors filtered)
- Tested batch analysis with 22 videos from 7-day period
- UI functionality verified with Playwright browser automation
- All API endpoints tested and operational

### Known Working Features
- ✅ Single video analysis via URL input
- ✅ Batch discovery of videos from trusted channels
- ✅ Batch analysis of all unanalyzed videos
- ✅ Persistent storage of analyses
- ✅ Channel-filtered viewing
- ✅ Visual status indicators (analyzed/unanalyzed)
- ✅ Responsive UI with real-time updates
- ✅ Clickable timestamps in analysis results
- ✅ Commercial/sponsor content filtering

### Future Enhancements (Not Implemented)
- Scheduled automatic discovery and analysis
- Email notifications for new recommendations
- Export functionality (CSV, JSON)
- Advanced filtering and search
- User authentication and personalization
- Additional video platforms support

### Notes
- Server runs on port 57212 by default
- All timestamps in analyses link directly to YouTube video moments
- Database automatically created on first run
- No video downloading required - direct streaming analysis via Gemini 2.5 Flash