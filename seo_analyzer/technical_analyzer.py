import requests
from urllib.parse import urlparse

def analyze_technical(crawler_result, soup):
    """
    Analyzes HTTPS/SSL security, server response time, document size, robots.txt, sitemap.xml, and mixed content.
    """
    url = crawler_result['url']
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    is_https = (scheme == 'https')

    response_time_ms = crawler_result['response_time_ms']
    html_content = crawler_result['html']
    doc_size_bytes = len(html_content.encode('utf-8'))
    doc_size_kb = round(doc_size_bytes / 1024, 2)

    issues = []

    # 1. HTTPS / SSL Check
    if not is_https:
        issues.append({
            'type': 'critical',
            'category': 'Technical SEO',
            'title': 'Website Not Using HTTPS/SSL',
            'description': "Website is served over unencrypted HTTP. HTTPS is an explicit Google ranking factor and security standard.",
            'impact': 'High'
        })

    # 2. Server Response Time Rating
    if response_time_ms > 1200:
        issues.append({
            'type': 'warning',
            'category': 'Performance',
            'title': 'Slow Server Response Time',
            'description': f"Server response time was {response_time_ms} ms (recommended < 500 ms). High latency degrades Core Web Vitals.",
            'impact': 'High'
        })
    elif response_time_ms > 600:
        issues.append({
            'type': 'warning',
            'category': 'Performance',
            'title': 'Moderate Server Latency',
            'description': f"Server response time was {response_time_ms} ms. Optimize backend hosting and caching.",
            'impact': 'Medium'
        })

    # 3. Document HTML Size Check
    if doc_size_kb > 500:
        issues.append({
            'type': 'warning',
            'category': 'Performance',
            'title': 'Large HTML Page Size',
            'description': f"HTML size is {doc_size_kb} KB (recommended < 200 KB). Large DOM trees delay parsing.",
            'impact': 'Medium'
        })

    # 4. Robots.txt and Sitemap Check
    domain_root = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{domain_root}/robots.txt"
    sitemap_url = f"{domain_root}/sitemap.xml"

    has_robots = False
    has_sitemap = False

    # Quick detection in soup if sitemap link exists in footer/meta or robots link
    sitemap_link = soup.find('link', attrs={'rel': lambda x: x and 'sitemap' in str(x).lower()})
    if sitemap_link or 'sitemap.xml' in html_content.lower():
        has_sitemap = True

    # If live scan, probe robots.txt
    if not crawler_result.get('is_simulated', False):
        try:
            r = requests.head(robots_url, timeout=3)
            if r.status_code == 200:
                has_robots = True
        except Exception:
            pass

        try:
            r = requests.head(sitemap_url, timeout=3)
            if r.status_code == 200:
                has_sitemap = True
        except Exception:
            pass
    else:
        # Simulated default
        has_robots = True
        has_sitemap = True

    if not has_robots:
        issues.append({
            'type': 'warning',
            'category': 'Technical SEO',
            'title': 'Missing robots.txt File',
            'description': "Could not confirm robots.txt file at `/robots.txt`. A robots.txt guides search engine crawler budget.",
            'impact': 'Medium'
        })

    if not has_sitemap:
        issues.append({
            'type': 'warning',
            'category': 'Technical SEO',
            'title': 'Missing XML Sitemap',
            'description': "Could not locate XML sitemap at `/sitemap.xml`. An XML sitemap helps crawlers index deep pages efficiently.",
            'impact': 'Medium'
        })

    # 5. Mixed Content Check (HTTP assets on HTTPS site)
    mixed_content_count = 0
    if is_https:
        http_assets = soup.find_all(['img', 'script', 'link'], src=lambda s: s and s.startswith('http://'))
        mixed_content_count = len(http_assets)
        if mixed_content_count > 0:
            issues.append({
                'type': 'warning',
                'category': 'Security',
                'title': 'Mixed Content Detected',
                'description': f"Found {mixed_content_count} resource(s) loaded over insecure HTTP on an HTTPS page.",
                'impact': 'Medium'
            })

    return {
        'is_https': is_https,
        'response_time_ms': response_time_ms,
        'doc_size_kb': doc_size_kb,
        'has_robots_txt': has_robots,
        'has_xml_sitemap': has_sitemap,
        'mixed_content_count': mixed_content_count,
        'issues': issues
    }
