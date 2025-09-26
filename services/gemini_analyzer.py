from google import genai
from google.genai import types
import yaml
import re
from services.youtube_service import YouTubeService

class GeminiAnalyzer:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        self.api_key = config['gemini_api_key']
        self.client = genai.Client(api_key=self.api_key)
        self.youtube_service = YouTubeService(config_path)

    def get_video_duration(self, youtube_url: str) -> int:
        """Get video duration in seconds for timestamp validation using YouTube Data API"""
        try:
            video_info = self.youtube_service.get_video_info(youtube_url)
            if video_info and 'duration' in video_info:
                return video_info['duration']
            else:
                print(f"No video info found for URL: {youtube_url}")
                return 0
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0

    def validate_timestamps(self, analysis_text: str, video_duration: int) -> bool:
        """Validate that no timestamps exceed video length"""
        timestamp_pattern = r'\((\d{1,2}):(\d{2})\)'
        timestamps = re.findall(timestamp_pattern, analysis_text)
        
        for minutes, seconds in timestamps:
            total_seconds = int(minutes) * 60 + int(seconds)
            if total_seconds > video_duration:
                return False
        return True

    def analyze_video(self, youtube_url: str, video_duration: int = None) -> dict:
        """Analyze YouTube video using Gemini with the exact prompt from CLAUDE.md"""
        
        # Get video duration for validation (use provided duration or fetch from API)
        if video_duration is None:
            video_duration = self.get_video_duration(youtube_url)
        else:
            # Use the provided duration to avoid double API call
            pass
        
        # Exact prompt from CLAUDE.md
        prompt = """You're a podcast analyzer who summarize Youtube videos and distills potential invesmtment recommendations.

## You task ##
Analyze if a video has explicit invesment recommendations:
1.  **Stock** Does this video recommend a specific stock and why?
2.  **Sector** Does this video recommend a specific sector and why?
3.  **Portfolio strategy** Does this video recommend a specific portfolio strategy and why?

If none of the above, focus on giving a simple summary of the video with timestamps to key moments. Timestamps should directly link to the video

## Exclude commercials and sponsors##
Exclude commercials and sponsors from the analysis. For example

This episode is brought to you by VanEck Semiconductor ETFs. You'll hear more about the VanEck Semiconductor ETF, ticker SMH, the largest semiconductor
ETF, and its newer VANX Fab Semiconductor ETF, ticker SMHX, later in the show.

## Output format ##
Always present both summary and timestamps of key moments that directly link to the video.

### Example output for videos with recommendations ###

 **Recommendation:** **Concentrated Portfolios (as opposed to Diversified Portfolios)**
    *   **Summary:** The speakers advocate moving away from traditional diversified portfolios towards highly concentrated portfolios.
    *   **Rationale:** They argue that in the current macro environment, dominated by the single, powerful factor of fiat currency debasement, diversification "destroys returns". If one clear macro factor explains the vast majority of asset price movements (90-97% for tech and crypto), then traditional diversification across various asset classes becomes irrelevant and ineffective. The optimal strategy is to concentrate investments in the few assets that are structurally positioned to benefit from this dominant force.
    *   **Timestamps:**
        *   (0:14-0:17) "Diversification just destroys returns now because you've got one clear macro factor." 
        *   (10:12-10:24) "In a macro world, we now think you need concentrated portfolios as opposed to diverse portfolios. In fact, diversification just destroys returns now because you've got one clear macro factor." 
### Example output for videos without recommendations ###
**Recommendation:Other** **What Trump's $100K H-1B Means for AI, Big Tech & U.S. Competitiveness** 
    *   **Summary:** The video, from "The Prof G Pod – Scott Galloway" on September 23rd, 2025, primarily discusses President Donald Trump's new H-1B visa policy and its implications for the U.S. economy, particularly the tech sector and AI competitiveness.
    *   **Timestamps:**
        *   (1:02) President Trump announced a significant change to the H-1B visa program: an entry fee of $100,000, replacing the previous $5,000 lottery fee. The new system will use a "weighted selection process" favoring highest-paid positions, which is expected to cause a huge decline in H-1B workers 
        *  (02:43) Elon Musk himself stated that the H-1B program was crucial for the existence of companies like SpaceX and Tesla in the U.S., and he vowed to "go to war" on the issue. (03:01) Despite his donations to Trump's campaign, the H-1B fee makes the visa largely inaccessible for many workers, as the average H-1B earner makes less than the new fee."""

        try:
            # Use the exact updated approach from CLAUDE.md
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=types.Content(
                    parts=[
                        types.Part(text=prompt),
                        types.Part(file_data=types.FileData(
                            file_uri=youtube_url)),
                    ]
                ),
                config=types.GenerateContentConfig(
                    media_resolution='MEDIA_RESOLUTION_LOW'
                ),
            )
            
            analysis_text = response.text
            
            # Validate timestamps don't exceed video length
            timestamps_valid = self.validate_timestamps(analysis_text, video_duration)
            
            # Check if VanEck content is excluded
            vaneck_excluded = "vaneck" not in analysis_text.lower()
            
            return {
                "analysis": analysis_text,
                "video_duration": video_duration,
                "timestamps_valid": timestamps_valid,
                "vaneck_excluded": vaneck_excluded,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }