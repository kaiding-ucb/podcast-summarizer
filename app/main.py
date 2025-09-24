from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import analysis, discovery

# Create FastAPI app
app = FastAPI(
    title="Podcast Summarizer",
    description="AI-powered YouTube video analysis for investment insights",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(analysis.router)
app.include_router(discovery.router)

# Frontend routes
@app.get("/")
async def home():
    """Redirect home to discover page"""
    return RedirectResponse(url="/discover", status_code=302)

@app.get("/discover", response_class=HTMLResponse)
async def discovery_page(request: Request):
    """Discovery page showing videos from trusted channels"""
    import yaml
    with open("config.yaml", 'r') as file:
        config = yaml.safe_load(file)
    discovery_days_back = config.get('discovery_days_back', 7)
    return templates.TemplateResponse("discover.html", {"request": request, "discovery_days_back": discovery_days_back})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page showing all analyses"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "podcast-summarizer"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=57212)