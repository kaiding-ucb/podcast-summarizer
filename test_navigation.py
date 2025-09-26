#!/usr/bin/env python3
"""
Playwright test script to diagnose navigation issues in the FastAPI application.
Tests key routes and identifies errors that may be causing link failures.
"""

import asyncio
import sys
from playwright.async_api import async_playwright
import json

BASE_URL = "http://localhost:8001"

ROUTES_TO_TEST = [
    "/",
    "/dashboard",
    "/discover",
    "/health",
    "/api/analyses",
    "/api/discover",
    "/api/recent"
]

async def test_route(page, route):
    """Test a specific route and capture errors"""
    print(f"\n=== Testing route: {route} ===")
    
    # Setup console log capture
    console_messages = []
    def handle_console(msg):
        console_messages.append(f"[{msg.type}] {msg.text}")
    
    # Setup response error capture
    response_errors = []
    def handle_response(response):
        if response.status >= 400:
            response_errors.append({
                'url': response.url,
                'status': response.status,
                'status_text': response.status_text
            })
    
    page.on('console', handle_console)
    page.on('response', handle_response)
    
    try:
        # Navigate to the route
        response = await page.goto(f"{BASE_URL}{route}", timeout=10000)
        
        # Wait for the page to stabilize
        await page.wait_for_load_state('networkidle', timeout=5000)
        
        # Get basic page info
        title = await page.title()
        url = page.url
        
        print(f"✓ Response Status: {response.status}")
        print(f"✓ Page Title: {title}")
        print(f"✓ Final URL: {url}")
        
        # Check for common error elements
        error_elements = await page.query_selector_all('.error, .error-state, [class*="error"]')
        if error_elements:
            print(f"⚠️  Found {len(error_elements)} potential error elements")
            for i, element in enumerate(error_elements[:3]):  # Show first 3
                text = await element.text_content()
                if text and text.strip():
                    print(f"   Error {i+1}: {text.strip()}")
        
        # Check for loading states that might be stuck
        loading_elements = await page.query_selector_all('.loading, .htmx-indicator:not([style*="display: none"])')
        if loading_elements:
            print(f"⚠️  Found {len(loading_elements)} active loading indicators")
        
        # Check for empty states
        empty_elements = await page.query_selector_all('.empty-state')
        if empty_elements:
            print(f"ℹ️  Found {len(empty_elements)} empty state elements")
            for element in empty_elements:
                text = await element.text_content()
                if text and text.strip():
                    print(f"   Empty state: {text.strip()}")
        
        # Report console messages
        if console_messages:
            print(f"📝 Console messages ({len(console_messages)}):")
            for msg in console_messages:
                print(f"   {msg}")
        
        # Report response errors
        if response_errors:
            print(f"🚫 Response errors ({len(response_errors)}):")
            for error in response_errors:
                print(f"   {error['status']} - {error['url']}")
        
        # Test specific functionality for different routes
        await test_route_specific_functionality(page, route)
        
        return {
            'route': route,
            'status': response.status,
            'title': title,
            'url': url,
            'console_messages': console_messages,
            'response_errors': response_errors,
            'success': response.status < 400
        }
        
    except Exception as e:
        print(f"❌ Error testing route {route}: {str(e)}")
        return {
            'route': route,
            'error': str(e),
            'success': False
        }

async def test_route_specific_functionality(page, route):
    """Test specific functionality for different routes"""
    
    if route == "/":
        # Test home page form elements
        form = await page.query_selector('#analyzeForm')
        if form:
            print("✓ Found analysis form")
        else:
            print("❌ Analysis form not found")
            
        video_input = await page.query_selector('#video_url')
        if video_input:
            print("✓ Found video URL input")
        else:
            print("❌ Video URL input not found")
    
    elif route == "/dashboard":
        # Test dashboard loading
        await page.wait_for_timeout(2000)  # Wait for JS to potentially load data
        
        analyses_grid = await page.query_selector('#analyses-grid')
        if analyses_grid:
            print("✓ Found analyses grid")
            content = await analyses_grid.text_content()
            if "Loading" in content:
                print("⚠️  Dashboard still showing loading state")
            elif "No analyses found" in content or "Failed to load" in content:
                print("ℹ️  Dashboard showing empty/error state")
        
    elif route == "/discover":
        # Test discover page elements
        discover_content = await page.query_selector('.container')
        if discover_content:
            print("✓ Found discover page content")

async def test_navigation_links(page):
    """Test clicking navigation links"""
    print(f"\n=== Testing Navigation Links ===")
    
    # Start at home page
    await page.goto(f"{BASE_URL}/")
    await page.wait_for_load_state('networkidle')
    
    # Test each navigation link
    nav_links = [
        ("Analyze", "/"),
        ("Discover", "/discover"),
        ("Dashboard", "/dashboard")
    ]
    
    for link_text, expected_path in nav_links:
        print(f"\n--- Testing '{link_text}' link ---")
        try:
            # Find and click the link
            link = await page.query_selector(f'a.nav-link[href="{expected_path}"]')
            if not link:
                print(f"❌ Navigation link '{link_text}' not found")
                continue
                
            # Click and wait for navigation
            await link.click()
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Check if we're on the right page
            current_url = page.url
            if expected_path in current_url:
                print(f"✓ Successfully navigated to {link_text} page")
            else:
                print(f"❌ Expected to be on {expected_path}, but on {current_url}")
                
        except Exception as e:
            print(f"❌ Error clicking '{link_text}' link: {str(e)}")

async def main():
    """Main test function"""
    print("🧪 Starting FastAPI Application Navigation Diagnostics")
    print(f"🎯 Testing application at: {BASE_URL}")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Set a reasonable timeout
        page.set_default_timeout(10000)
        
        # Test all routes
        results = []
        for route in ROUTES_TO_TEST:
            result = await test_route(page, route)
            results.append(result)
        
        # Test navigation links
        await test_navigation_links(page)
        
        # Summary
        print(f"\n{'='*50}")
        print("📊 SUMMARY REPORT")
        print(f"{'='*50}")
        
        successful_routes = [r for r in results if r.get('success', False)]
        failed_routes = [r for r in results if not r.get('success', False)]
        
        print(f"✅ Successful routes: {len(successful_routes)}/{len(results)}")
        print(f"❌ Failed routes: {len(failed_routes)}/{len(results)}")
        
        if failed_routes:
            print(f"\n🚨 FAILED ROUTES:")
            for result in failed_routes:
                route = result['route']
                if 'error' in result:
                    print(f"   {route}: {result['error']}")
                else:
                    print(f"   {route}: HTTP {result.get('status', 'Unknown')}")
        
        if successful_routes:
            print(f"\n✅ SUCCESSFUL ROUTES:")
            for result in successful_routes:
                print(f"   {result['route']}: HTTP {result['status']} - {result.get('title', 'No title')}")
        
        # Identify common issues
        print(f"\n🔍 COMMON ISSUES DETECTED:")
        
        # Check for missing config/API keys
        api_errors = [r for r in results if any('api' in msg.lower() for msg in r.get('console_messages', []))]
        if api_errors:
            print("   • API-related errors detected - check API keys in config.yaml")
        
        # Check for database issues  
        db_errors = [r for r in results if any('database' in msg.lower() or 'db' in msg.lower() for msg in r.get('console_messages', []))]
        if db_errors:
            print("   • Database-related errors detected")
            
        # Check for missing files
        missing_files = [r for r in results if any(err.get('status') == 404 for err in r.get('response_errors', []))]
        if missing_files:
            print("   • 404 errors detected - missing static files or routes")
        
        # Check for server errors
        server_errors = [r for r in results if any(err.get('status', 0) >= 500 for err in r.get('response_errors', []))]
        if server_errors:
            print("   • Server errors detected - check application logs")
        
        await browser.close()
        
        return len(failed_routes) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)