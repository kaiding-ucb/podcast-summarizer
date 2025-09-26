#!/usr/bin/env python3
"""
Debug script to examine the actual HTML content and understand why sectioning isn't working.
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def debug_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("🔍 Debugging dashboard sectioning...")
            
            # Navigate and wait for content
            await page.goto('http://127.0.0.1:8000/dashboard')
            await page.wait_for_load_state('networkidle')
            await page.wait_for_selector('.analysis-card', timeout=10000)
            
            # Click show full on first analysis
            toggle_buttons = await page.query_selector_all('button[onclick*="toggleAnalysis"]')
            if toggle_buttons:
                await toggle_buttons[0].click()
                await page.wait_for_timeout(2000)
            
            # Get the raw analysis text before formatting
            full_divs = await page.query_selector_all('[id^="full-"]')
            if full_divs:
                first_div = full_divs[0]
                
                # Get raw text content
                raw_text = await first_div.inner_text()
                print("📄 Raw analysis text (first 500 chars):")
                print("=" * 60)
                print(raw_text[:500] + "...")
                print("=" * 60)
                
                # Get HTML content
                html_content = await first_div.inner_html()
                print("\n🏗️  HTML content (first 1000 chars):")
                print("=" * 60)
                print(html_content[:1000] + "...")
                print("=" * 60)
                
                # Check if the text has the expected section patterns
                has_summary = "**Summary:**" in raw_text
                has_recommendation = "**Recommendation:**" in raw_text
                has_rationale = "**Rationale:**" in raw_text
                has_timestamps = bool(re.search(r'\d{1,2}:\d{2}', raw_text))
                
                print(f"\n🔍 Pattern Analysis:")
                print(f"  Has **Summary:** {has_summary}")
                print(f"  Has **Recommendation:** {has_recommendation}")
                print(f"  Has **Rationale:** {has_rationale}")
                print(f"  Has timestamps: {has_timestamps}")
                
                # Check if formatAnalysisText function was called properly
                print(f"\n🧪 HTML Analysis:")
                print(f"  Contains .analysis-section: {'.analysis-section' in html_content}")
                print(f"  Contains .timestamp-link: {'.timestamp-link' in html_content}")
                print(f"  Contains <h3>: {'<h3' in html_content}")
                print(f"  Contains <strong>: {'<strong>' in html_content}")
                print(f"  Contains <br>: {'<br>' in html_content}")
                
                # Let's also check what JavaScript functions are available
                js_functions = await page.evaluate("""
                    () => {
                        return {
                            hasFormatAnalysisText: typeof formatAnalysisText !== 'undefined',
                            hasParseAnalysisSections: typeof parseAnalysisSections !== 'undefined',
                            hasFormatSectionedAnalysis: typeof formatSectionedAnalysis !== 'undefined'
                        };
                    }
                """)
                
                print(f"\n⚙️  JavaScript Functions Available:")
                for func_name, available in js_functions.items():
                    print(f"  {func_name}: {available}")
                
                # Let's try to manually call the function to see what happens
                if js_functions['hasParseAnalysisSections']:
                    try:
                        test_result = await page.evaluate("""
                            (text) => {
                                const sections = parseAnalysisSections(text);
                                return {
                                    sectionsCount: sections.length,
                                    sections: sections.map(s => ({
                                        title: s.title,
                                        contentLength: s.content.length,
                                        isHighlighted: s.isHighlighted
                                    }))
                                };
                            }
                        """, raw_text)
                        
                        print(f"\n🧠 Manual parseAnalysisSections test:")
                        print(f"  Sections found: {test_result['sectionsCount']}")
                        for i, section in enumerate(test_result['sections']):
                            print(f"  Section {i+1}: {section['title']} ({section['contentLength']} chars, highlighted: {section['isHighlighted']})")
                        
                        # Now test the full formatAnalysisText function
                        format_test = await page.evaluate("""
                            (args) => {
                                const { text, videoUrl } = args;
                                const sections = parseAnalysisSections(text);
                                console.log('Sections found:', sections.length);
                                
                                if (sections.length > 0) {
                                    console.log('Using sectioned formatting');
                                    const result = formatSectionedAnalysis(sections, videoUrl);
                                    return { 
                                        used: 'sectioned',
                                        result: result.substring(0, 500),
                                        sectionsLength: sections.length
                                    };
                                } else {
                                    console.log('Using fallback formatting');
                                    return { 
                                        used: 'fallback',
                                        result: 'fallback would be used',
                                        sectionsLength: 0
                                    };
                                }
                            }
                        """, {"text": raw_text, "videoUrl": "https://youtube.com/watch?v=test"})
                        
                        print(f"\n🔧 formatAnalysisText behavior:")
                        print(f"  Used: {format_test['used']} formatting")
                        print(f"  Sections length: {format_test['sectionsLength']}")
                        print(f"  Result (first 500 chars):")
                        print(f"  {format_test['result']}")
                            
                    except Exception as e:
                        print(f"❌ Error testing parseAnalysisSections: {e}")
                
        except Exception as e:
            print(f"❌ Debug error: {e}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dashboard())