def analyze_metadata(soup, url):
    """
    Analyzes title, meta description, viewport, canonical, robots, charset, and social meta tags.
    """
    results = {
        'title': {
            'value': None,
            'length': 0,
            'status': 'missing',  # 'optimal', 'warning', 'missing', 'too_short', 'too_long'
            'message': ''
        },
        'description': {
            'value': None,
            'length': 0,
            'status': 'missing',
            'message': ''
        },
        'viewport': {
            'present': False,
            'value': None,
            'status': 'missing'
        },
        'canonical': {
            'present': False,
            'value': None,
            'status': 'missing'
        },
        'robots': {
            'present': False,
            'value': None,
            'is_noindex': False
        },
        'charset': {
            'present': False,
            'value': None
        },
        'open_graph': {
            'og_title': None,
            'og_description': None,
            'og_image': None,
            'count': 0
        },
        'twitter': {
            'twitter_card': None,
            'twitter_title': None,
            'count': 0
        },
        'issues': []
    }

    # 1. Page Title Analysis
    title_tag = soup.find('title')
    if title_tag and title_tag.string and title_tag.string.strip():
        title_text = title_tag.string.strip()
        length = len(title_text)
        results['title']['value'] = title_text
        results['title']['length'] = length

        if 50 <= length <= 60:
            results['title']['status'] = 'optimal'
            results['title']['message'] = f"Title tag is optimal length ({length} characters)."
        elif 30 <= length < 50:
            results['title']['status'] = 'warning'
            results['title']['message'] = f"Title tag is slightly short ({length} characters). 50-60 characters is recommended."
            results['issues'].append({
                'type': 'warning',
                'category': 'Metadata',
                'title': 'Short Title Tag',
                'description': f"Title tag contains {length} characters. Expand it to 50-60 characters to include target keywords.",
                'impact': 'Medium'
            })
        elif length > 60:
            results['title']['status'] = 'warning'
            results['title']['message'] = f"Title tag is too long ({length} characters). Search engines may truncate it."
            results['issues'].append({
                'type': 'warning',
                'category': 'Metadata',
                'title': 'Overly Long Title Tag',
                'description': f"Title tag contains {length} characters. Keep it under 60 characters to prevent truncation in SERP snippets.",
                'impact': 'Medium'
            })
        else:
            results['title']['status'] = 'too_short'
            results['title']['message'] = f"Title tag is critically short ({length} characters)."
            results['issues'].append({
                'type': 'critical',
                'category': 'Metadata',
                'title': 'Critically Short Title Tag',
                'description': "Title tag is under 30 characters. Provide a descriptive title highlighting core page offerings.",
                'impact': 'High'
            })
    else:
        results['title']['status'] = 'missing'
        results['title']['message'] = "Page title tag is missing!"
        results['issues'].append({
            'type': 'critical',
            'category': 'Metadata',
            'title': 'Missing Title Tag',
            'description': "The page is missing a `<title>` tag in the `<head>` section, which is a major SEO ranking signal.",
            'impact': 'High'
        })

    # 2. Meta Description Analysis
    meta_desc = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
    if meta_desc and meta_desc.get('content', '').strip():
        desc_text = meta_desc['content'].strip()
        length = len(desc_text)
        results['description']['value'] = desc_text
        results['description']['length'] = length

        if 150 <= length <= 160:
            results['description']['status'] = 'optimal'
            results['description']['message'] = f"Meta description is optimal length ({length} characters)."
        elif 100 <= length < 150:
            results['description']['status'] = 'warning'
            results['description']['message'] = f"Meta description is short ({length} characters). 150-160 characters recommended."
            results['issues'].append({
                'type': 'warning',
                'category': 'Metadata',
                'title': 'Short Meta Description',
                'description': f"Meta description is {length} characters long. Aim for 150-160 characters for maximum CTR in Google search results.",
                'impact': 'Medium'
            })
        elif length > 160:
            results['description']['status'] = 'warning'
            results['description']['message'] = f"Meta description is slightly long ({length} characters)."
            results['issues'].append({
                'type': 'warning',
                'category': 'Metadata',
                'title': 'Long Meta Description',
                'description': f"Meta description is {length} characters. Truncation might occur past 160 characters.",
                'impact': 'Low'
            })
        else:
            results['description']['status'] = 'too_short'
            results['description']['message'] = f"Meta description is very short ({length} characters)."
            results['issues'].append({
                'type': 'warning',
                'category': 'Metadata',
                'title': 'Critically Short Meta Description',
                'description': "Meta description is under 100 characters. Expand to summarize page content effectively.",
                'impact': 'Medium'
            })
    else:
        results['description']['status'] = 'missing'
        results['description']['message'] = "Meta description is missing!"
        results['issues'].append({
            'type': 'critical',
            'category': 'Metadata',
            'title': 'Missing Meta Description',
            'description': "No `<meta name=\"description\">` tag found. Adding a clear meta description improves click-through rate in search results.",
            'impact': 'High'
        })

    # 3. Viewport Tag
    viewport = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'viewport'})
    if viewport and viewport.get('content'):
        results['viewport']['present'] = True
        results['viewport']['value'] = viewport['content']
        results['viewport']['status'] = 'passed'
    else:
        results['viewport']['status'] = 'missing'
        results['issues'].append({
            'type': 'critical',
            'category': 'Technical & Mobile',
            'title': 'Missing Viewport Meta Tag',
            'description': "No viewport tag detected (`<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">`). This hurts mobile responsiveness.",
            'impact': 'High'
        })

    # 4. Canonical Link
    canonical = soup.find('link', attrs={'rel': lambda x: x and 'canonical' in x.lower() if isinstance(x, str) else False})
    if canonical and canonical.get('href'):
        results['canonical']['present'] = True
        results['canonical']['value'] = canonical['href']
        results['canonical']['status'] = 'passed'
    else:
        results['canonical']['status'] = 'missing'
        results['issues'].append({
            'type': 'warning',
            'category': 'Metadata',
            'title': 'Missing Canonical Tag',
            'description': "No `<link rel=\"canonical\">` tag found. Canonical URLs prevent duplicate content indexing issues.",
            'impact': 'Medium'
        })

    # 5. Robots Meta Tag
    robots = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'robots'})
    if robots and robots.get('content'):
        results['robots']['present'] = True
        content = robots['content'].lower()
        results['robots']['value'] = content
        if 'noindex' in content:
            results['robots']['is_noindex'] = True
            results['issues'].append({
                'type': 'critical',
                'category': 'Indexability',
                'title': 'Page Set to NoIndex',
                'description': f"Robots meta tag specifies '{content}', preventing search engines from indexing this page!",
                'impact': 'High'
            })

    # 6. Charset
    charset_meta = soup.find('meta', charset=True) or soup.find('meta', attrs={'http-equiv': lambda x: x and x.lower() == 'content-type'})
    if charset_meta:
        results['charset']['present'] = True
        results['charset']['value'] = charset_meta.get('charset') or charset_meta.get('content')

    # 7. Open Graph Tags
    og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
    results['open_graph']['count'] = len(og_tags)
    for tag in og_tags:
        prop = tag.get('property', '').lower()
        val = tag.get('content', '')
        if prop == 'og:title':
            results['open_graph']['og_title'] = val
        elif prop == 'og:description':
            results['open_graph']['og_description'] = val
        elif prop == 'og:image':
            results['open_graph']['og_image'] = val

    if results['open_graph']['count'] == 0:
        results['issues'].append({
            'type': 'warning',
            'category': 'Social Media',
            'title': 'Missing Open Graph Tags',
            'description': "No Open Graph tags (`og:title`, `og:image`, `og:description`) found. Social sharing cards will look unformatted on Facebook/LinkedIn.",
            'impact': 'Low'
        })

    # 8. Twitter Card Tags
    tw_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
    results['twitter']['count'] = len(tw_tags)
    for tag in tw_tags:
        name = tag.get('name', '').lower()
        val = tag.get('content', '')
        if name == 'twitter:card':
            results['twitter']['twitter_card'] = val
        elif name == 'twitter:title':
            results['twitter']['twitter_title'] = val

    return results
