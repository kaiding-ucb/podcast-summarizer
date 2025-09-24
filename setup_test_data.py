#!/usr/bin/env python3
"""
Setup script to populate the database with sample video analysis data for testing
"""

import sys
import os
from datetime import datetime, timedelta
import sqlite3

# Add the current directory to the Python path so we can import services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database import DatabaseService

def create_test_data():
    """Create sample video analysis data for testing"""
    db_service = DatabaseService()
    
    # Sample data with proper metadata
    test_analyses = [
        {
            'video_id': 'test_video_1',
            'video_url': 'https://www.youtube.com/watch?v=test_video_1',
            'title': 'Market Analysis: Tech Stocks Deep Dive',
            'analysis': '''**Summary:**
This video provides a comprehensive analysis of the current tech stock market, focusing on major players like Apple, Google, and Microsoft. The speaker discusses upcoming earnings reports and market trends.

**Key Points:**
- Apple's new product launches expected to drive Q4 revenue
- Google's AI investments showing promising returns
- Microsoft's cloud services continue to dominate

**Recommendation:Strong Buy**
Tech stocks are positioned well for the next quarter with strong fundamentals and growth prospects.''',
            'channel_id': 'UCkrwgzhIBKccuDsi_SvZtnQ',
            'channel_name': 'Forward Guidance',
            'published_at': '2024-01-15T10:30:00Z',
            'video_duration': 1245,  # 20:45
            'timestamps_valid': True,
            'vaneck_excluded': False,
            'success': True,
            'error': None,
            'created_at': datetime.now() - timedelta(days=2)
        },
        {
            'video_id': 'test_video_2', 
            'video_url': 'https://www.youtube.com/watch?v=test_video_2',
            'title': 'Portfolio Strategy: Diversification in 2024',
            'analysis': '''**Summary:**
An in-depth look at portfolio diversification strategies for 2024, covering asset allocation across different sectors and geographic regions.

**Key Topics:**
- International market exposure benefits
- Sector rotation strategies
- Risk management techniques (15:30)
- Rebalancing frequency recommendations (22:10)

**Recommendation:Portfolio strategy**
Implement a 60/40 stock-bond allocation with 20% international exposure for optimal risk-adjusted returns.''',
            'channel_id': 'UC1E1SVcVyU3ntWMSQEp38Yw',
            'channel_name': 'Prof G Markets', 
            'published_at': '2024-01-12T14:15:00Z',
            'video_duration': 1680,  # 28:00
            'timestamps_valid': True,
            'vaneck_excluded': False,
            'success': True,
            'error': None,
            'created_at': datetime.now() - timedelta(days=5)
        },
        {
            'video_id': 'test_video_3',
            'video_url': 'https://www.youtube.com/watch?v=test_video_3', 
            'title': 'Breaking: Federal Reserve Rate Decision Impact',
            'analysis': '''**Summary:**
Analysis of the Federal Reserve's latest interest rate decision and its implications for various asset classes including stocks, bonds, and commodities.

**Market Impact Analysis:**
- Interest rate cut by 0.25% as expected
- Dollar weakening against major currencies
- Bond yields dropping across the curve (8:45)
- Growth stocks likely to benefit most (12:20)

**Recommendation:Sector**
Focus on growth and technology sectors which typically outperform in lower rate environments.''',
            'channel_id': 'UCkrwgzhIBKccuDsi_SvZtnQ',
            'channel_name': 'Forward Guidance',
            'published_at': '2024-01-18T16:00:00Z', 
            'video_duration': 945,  # 15:45
            'timestamps_valid': True,
            'vaneck_excluded': False,
            'success': True,
            'error': None,
            'created_at': datetime.now() - timedelta(days=1)
        },
        {
            'video_id': 'test_video_4',
            'video_url': 'https://www.youtube.com/watch?v=test_video_4',
            'title': 'Cryptocurrency Market Update - Bitcoin & Ethereum',
            'analysis': '''**Summary:** 
Weekly cryptocurrency market analysis covering Bitcoin's recent price action and Ethereum's upcoming network upgrades.

**Analysis Points:**
- Bitcoin testing key resistance at $45,000
- Ethereum merge upgrade implications
- Institutional adoption trends
- Regulatory environment updates (18:30)

**Recommendation:Other**
Crypto markets remain volatile but institutional interest continues to grow. Consider small allocation for diversified portfolios.''',
            'channel_id': 'UC1E1SVcVyU3ntWMSQEp38Yw',  
            'channel_name': 'Prof G Markets',
            'published_at': '2024-01-10T09:45:00Z',
            'video_duration': 1380,  # 23:00
            'timestamps_valid': True,
            'vaneck_excluded': False,
            'success': True, 
            'error': None,
            'created_at': datetime.now() - timedelta(days=7)
        }
    ]
    
    # Add more test data to demonstrate pagination
    additional_test_data = []
    for i in range(5, 16):  # Creates test_video_5 through test_video_15
        additional_test_data.append({
            'video_id': f'test_video_{i}',
            'video_url': f'https://www.youtube.com/watch?v=test_video_{i}',
            'title': f'Market Analysis #{i}: {"Tech Sector" if i % 3 == 0 else "Financial Markets" if i % 2 == 0 else "Economic Outlook"}',
            'analysis': f'''**Summary:**
This is analysis #{i} covering various market topics and investment strategies. The video discusses key trends and provides actionable insights for investors.

**Key Points:**
- Market trend analysis for Q{((i-1) % 4) + 1}
- Risk assessment and management strategies  
- Portfolio optimization recommendations (12:30)
- Economic indicators review (25:15)

**Recommendation:{"Stock" if i % 4 == 0 else "Sector" if i % 3 == 0 else "Portfolio strategy"}**
{"Buy recommendation for specific stocks based on fundamentals." if i % 4 == 0 else "Sector rotation strategy recommended based on current market conditions." if i % 3 == 0 else "Diversified portfolio approach recommended for current market environment."}

**Rationale:**
The analysis shows strong {"fundamentals" if i % 2 == 0 else "technical indicators"} supporting this recommendation with {"low risk" if i % 3 == 0 else "moderate risk"} profile.''',
            'channel_id': 'UCkrwgzhIBKccuDsi_SvZtnQ' if i % 2 == 0 else 'UC1E1SVcVyU3ntWMSQEp38Yw',
            'channel_name': 'Forward Guidance' if i % 2 == 0 else 'Prof G Markets',
            'published_at': f'2024-01-{(i % 28) + 1:02d}T{10 + (i % 12)}:{(i * 5) % 60:02d}:00Z',
            'video_duration': 900 + (i * 60),  # Varying durations
            'timestamps_valid': True,
            'vaneck_excluded': False,
            'success': True,
            'error': None,
            'created_at': datetime.now() - timedelta(days=i)
        })
    
    test_analyses.extend(additional_test_data)
    
    # Insert test data
    success_count = 0
    for analysis in test_analyses:
        if db_service.save_analysis(analysis):
            success_count += 1
            print(f"✅ Created test analysis: {analysis['title']}")
        else:
            print(f"❌ Failed to create test analysis: {analysis['title']}")
    
    print(f"\n✨ Successfully created {success_count}/{len(test_analyses)} test analyses")
    return success_count > 0

if __name__ == "__main__":
    print("🚀 Setting up test data for dashboard testing...")
    success = create_test_data()
    if success:
        print("\n✅ Test data setup completed successfully!")
        print("You can now start the FastAPI app and run Playwright tests.")
    else:
        print("\n❌ Failed to setup test data")
        sys.exit(1)