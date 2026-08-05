import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SEOScope-Bot/1.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

SAMPLE_DEMOS = {
    'sample-blog.local': """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Tech Insights & Digital Trends Blog 2026 | Tech Guides</title>
    <meta name="description" content="Discover the latest technology trends, web development tutorials, software architecture guides, and artificial intelligence insights on Tech Insights.">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://techinsights.example.com/">
    <meta property="og:title" content="Tech Insights & Digital Trends Blog 2026">
    <meta property="og:description" content="Discover the latest technology trends and software architecture guides.">
    <meta property="og:image" content="https://techinsights.example.com/assets/og-banner.jpg">
</head>
<body>
    <header>
        <h1>Tech Insights: Digital Innovation & Software Development</h1>
    </header>
    <nav>
        <a href="/">Home</a>
        <a href="/articles">Articles</a>
        <a href="/about">About Us</a>
        <a href="/contact">Contact</a>
        <a href="https://external-tech-site.com" rel="noopener noreferrer">Partner Site</a>
    </nav>
    <main>
        <h2>Latest Trends in Artificial Intelligence</h2>
        <p>Artificial intelligence software development is transforming modern technology. Web performance, SEO optimization, and software development practices continue to evolve rapidly.</p>
        <img src="/assets/ai-trends.jpg" alt="Artificial Intelligence trends diagram" width="800" height="400">
        
        <h2>Web Development Best Practices</h2>
        <p>Building high-speed web applications requires proper SEO optimization, fast response time, structured heading hierarchy, and meta tag optimization.</p>
        <img src="/assets/code-editor.png" alt="Code editor screen showing python web application code">
        
        <h2>SEO Optimization and Search Performance</h2>
        <p>On-page SEO optimization focuses on metadata, keywords, internal links, image ALT attributes, and heading structure.</p>
        <img src="/assets/seo-chart.jpg" alt="SEO analytics chart report">
        
        <h3>Key SEO Ranking Factors</h3>
        <ul>
            <li>Title Tag Optimization</li>
            <li>Meta Description Quality</li>
            <li>Page Speed and Response Latency</li>
            <li>Mobile Responsiveness</li>
        </ul>
    </main>
    <footer>
        <p>&copy; 2026 Tech Insights. All rights reserved.</p>
    </footer>
</body>
</html>""",

    'poor-seo-demo.local': """<!DOCTYPE html>
<html>
<head>
    <title>Home</title>
</head>
<body>
    <p>Welcome to our website!</p>
    <p>Check out our products below.</p>
    <img src="/banner.jpg">
    <img src="/photo1.jpg">
    <img src="/photo2.jpg">
    <a href="/page1.html">Click here</a>
    <a href="/page2.html">Read more</a>
    <a href="http://unsecure-external-link.com">External Link</a>
    <h3>Subheading Without H1</h3>
    <p>This page is missing title tags length, meta description, viewport tag, OpenGraph tags, H1 heading, and image ALT attributes.</p>
</body>
</html>"""
}


def fetch_website_content(url):
    """
    Crawls URL and extracts HTML content, status code, response time, and headers.
    Falls back to simulated preset HTML if offline or if URL fetch fails.
    """
    # Clean up URL format
    cleaned_url = url.strip()
    if not cleaned_url.startswith(('http://', 'https://')):
        cleaned_url = 'https://' + cleaned_url

    parsed = urlparse(cleaned_url)
    domain = parsed.netloc.lower() or parsed.path.lower()

    # Check for preset sample demos
    if domain in SAMPLE_DEMOS:
        return {
            'url': cleaned_url,
            'status_code': 200,
            'response_time_ms': 120,
            'html': SAMPLE_DEMOS[domain],
            'headers': {'Content-Type': 'text/html; charset=utf-8'},
            'soup': BeautifulSoup(SAMPLE_DEMOS[domain], 'html.parser'),
            'is_simulated': True,
            'error': None
        }

    # Live HTTP Fetching
    start_time = time.time()
    try:
        response = requests.get(cleaned_url, headers=DEFAULT_HEADERS, timeout=10, verify=False)
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Check content type
        content_type = response.headers.get('Content-Type', '')
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        return {
            'url': response.url,
            'status_code': response.status_code,
            'response_time_ms': elapsed_ms,
            'html': html_content,
            'headers': dict(response.headers),
            'soup': soup,
            'is_simulated': False,
            'error': None
        }
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        # Fallback fallback simulation for demo/testing when network/DNS fails
        fallback_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SEO Audit Analysis for {domain}</title>
    <meta name="description" content="SEO health check and website analysis report generated by SEOScope tool for {domain}.">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    <header>
        <h1>Website Analysis: {domain}</h1>
    </header>
    <main>
        <h2>SEO Diagnostic Report</h2>
        <p>Automated analysis scan results for {cleaned_url}.</p>
        <img src="/logo.png" alt="{domain} Brand Logo">
        <a href="{cleaned_url}">Home Page</a>
    </main>
</body>
</html>"""
        return {
            'url': cleaned_url,
            'status_code': 200,
            'response_time_ms': max(elapsed_ms, 250),
            'html': fallback_html,
            'headers': {'Content-Type': 'text/html'},
            'soup': BeautifulSoup(fallback_html, 'html.parser'),
            'is_simulated': True,
            'error': str(e)
        }
