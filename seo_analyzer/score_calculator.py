def calculate_seo_scores(metadata, headings, images, links, keywords, technical):
    """
    Aggregates sub-scores and overall SEO score (0-100), consolidates issues, and generates actionable recommendations.
    """

    # --- 1. Technical Sub-Score (0-100) ---
    tech_points = 100
    if not technical['is_https']:
        tech_points -= 25
    if technical['response_time_ms'] > 1200:
        tech_points -= 20
    elif technical['response_time_ms'] > 600:
        tech_points -= 10
    if not technical['has_robots_txt']:
        tech_points -= 10
    if not technical['has_xml_sitemap']:
        tech_points -= 10
    if metadata['viewport']['status'] == 'missing':
        tech_points -= 20
    if technical['mixed_content_count'] > 0:
        tech_points -= 15
    tech_score = max(0, min(100, tech_points))

    # --- 2. Content Optimization Sub-Score (0-100) ---
    content_points = 100
    if metadata['title']['status'] == 'missing':
        content_points -= 30
    elif metadata['title']['status'] in ('too_short', 'warning'):
        content_points -= 15

    if metadata['description']['status'] == 'missing':
        content_points -= 25
    elif metadata['description']['status'] in ('too_short', 'warning'):
        content_points -= 10

    if headings['breakdown']['h1_count'] == 0:
        content_points -= 25
    elif headings['breakdown']['h1_count'] > 1:
        content_points -= 10

    if keywords['total_word_count'] < 300:
        content_points -= 15

    content_score = max(0, min(100, content_points))

    # --- 3. Image Sub-Score (0-100) ---
    images_score = images['alt_score_percentage']
    if images['generic_alt_count'] > 0:
        images_score -= 10
    if images['missing_dimensions_count'] > 0:
        images_score -= 5
    images_score = max(0, min(100, images_score))

    # --- 4. Link Sub-Score (0-100) ---
    link_points = 100
    if links['total_links'] == 0:
        link_points -= 30
    else:
        if links['internal_links_count'] == 0:
            link_points -= 25
        if links['generic_anchor_count'] > 0:
            link_points -= 15
        if links['missing_rel_count'] > 0:
            link_points -= 10
        if links['empty_links_count'] > 0:
            link_points -= 10
    links_score = max(0, min(100, link_points))

    # --- Overall Score Calculation (Weighted) ---
    # Technical: 30%, Content: 30%, Images: 20%, Links: 20%
    overall_score = round(
        (tech_score * 0.30) +
        (content_score * 0.30) +
        (images_score * 0.20) +
        (links_score * 0.20)
    )

    # Score Rating Grade
    if overall_score >= 85:
        rating_grade = 'Excellent'
        rating_color = '#10b981' # emerald green
    elif overall_score >= 70:
        rating_grade = 'Good'
        rating_color = '#3b82f6' # blue
    elif overall_score >= 50:
        rating_grade = 'Fair'
        rating_color = '#f59e0b' # amber
    else:
        rating_grade = 'Needs Improvement'
        rating_color = '#ef4444' # red

    # Combine all issues
    all_raw_issues = (
        metadata.get('issues', []) +
        headings.get('issues', []) +
        images.get('issues', []) +
        links.get('issues', []) +
        keywords.get('issues', []) +
        technical.get('issues', [])
    )

    critical_issues = [i for i in all_raw_issues if i['type'] == 'critical']
    warning_issues = [i for i in all_raw_issues if i['type'] == 'warning']

    # Generate Passed Checks
    passed_checks = []
    if metadata['title']['status'] == 'optimal':
        passed_checks.append({
            'title': 'Optimal Title Tag Length',
            'description': f"Title tag is {metadata['title']['length']} characters, fitting Google SERP limits.",
            'category': 'Metadata'
        })
    if metadata['description']['status'] == 'optimal':
        passed_checks.append({
            'title': 'Optimal Meta Description Length',
            'description': f"Meta description is {metadata['description']['length']} characters long.",
            'category': 'Metadata'
        })
    if headings['breakdown']['h1_count'] == 1:
        passed_checks.append({
            'title': 'Single H1 Heading Present',
            'description': f"Page features exactly one main H1 tag: \"{headings['headings_data']['h1'][0]['text']}\".",
            'category': 'Headings'
        })
    if technical['is_https']:
        passed_checks.append({
            'title': 'HTTPS/SSL Encryption Active',
            'description': "Website is securely served over encrypted HTTPS connection.",
            'category': 'Security'
        })
    if metadata['viewport']['present']:
        passed_checks.append({
            'title': 'Mobile Viewport Tag Enabled',
            'description': "Mobile viewport tag is properly configured for responsive displays.",
            'category': 'Mobile'
        })
    if images['missing_alt_count'] == 0 and images['total_images'] > 0:
        passed_checks.append({
            'title': '100% Image ALT Coverage',
            'description': "All images on the page contain descriptive ALT attributes.",
            'category': 'Images'
        })
    if links['internal_links_count'] > 0:
        passed_checks.append({
            'title': 'Internal Navigation Links Present',
            'description': f"Found {links['internal_links_count']} internal link(s) aiding site architecture crawlability.",
            'category': 'Links'
        })

    # Generate Actionable Recommendations
    recommendations = []
    
    if metadata['title']['status'] in ('missing', 'too_short', 'warning'):
        recommendations.append({
            'priority': 'High' if metadata['title']['status'] == 'missing' else 'Medium',
            'category': 'Metadata',
            'action': 'Optimize Page Title Tag',
            'how_to_fix': 'Update your page `<title>` in the `<head>` section to be between 50-60 characters. Include primary target keywords near the beginning.'
        })

    if metadata['description']['status'] in ('missing', 'too_short', 'warning'):
        recommendations.append({
            'priority': 'High' if metadata['description']['status'] == 'missing' else 'Medium',
            'category': 'Metadata',
            'action': 'Add/Refine Meta Description',
            'how_to_fix': 'Write a compelling meta description tag (150-160 characters) summarizing your value proposition and including a clear call-to-action.'
        })

    if headings['breakdown']['h1_count'] != 1:
        recommendations.append({
            'priority': 'High',
            'category': 'Headings',
            'action': 'Fix H1 Heading Structure',
            'how_to_fix': 'Ensure your HTML contains exactly one `<h1>` tag at the top of the content body highlighting the main topic.'
        })

    if images['missing_alt_count'] > 0 or images['empty_alt_count'] > 0:
        recommendations.append({
            'priority': 'High',
            'category': 'Images',
            'action': 'Add Descriptive Image ALT Attributes',
            'how_to_fix': 'Add concise, descriptive `alt="..."` attributes to all content images explaining what the image depicts for search engines and visually impaired users.'
        })

    if not technical['is_https']:
        recommendations.append({
            'priority': 'High',
            'category': 'Security',
            'action': 'Migrate Website to HTTPS',
            'how_to_fix': 'Install an SSL certificate (e.g., via Let\'s Encrypt) and redirect all HTTP traffic to HTTPS.'
        })

    if not technical['has_sitemap.xml'] if 'has_sitemap.xml' in technical else not technical.get('has_xml_sitemap', False):
        recommendations.append({
            'priority': 'Medium',
            'category': 'Technical SEO',
            'action': 'Create & Submit XML Sitemap',
            'how_to_fix': 'Generate an XML sitemap (`sitemap.xml`), upload it to your root web directory, and submit it in Google Search Console.'
        })

    if keywords['total_word_count'] < 300:
        recommendations.append({
            'priority': 'Medium',
            'category': 'Content',
            'action': 'Expand Body Content Depth',
            'how_to_fix': 'Expand page body text to at least 300-500 words of high-value, comprehensive content answering target user search intent.'
        })

    if links['generic_anchor_count'] > 0:
        recommendations.append({
            'priority': 'Low',
            'category': 'Links',
            'action': 'Replace Generic Anchor Text',
            'how_to_fix': 'Replace vague link anchors like "click here" or "link" with context-rich phrases describing the linked destination.'
        })

    return {
        'overall_score': overall_score,
        'rating_grade': rating_grade,
        'rating_color': rating_color,
        'category_scores': {
            'technical': tech_score,
            'content': content_score,
            'images': images_score,
            'links': links_score
        },
        'summary': {
            'total_issues': len(all_raw_issues),
            'critical_count': len(critical_issues),
            'warning_count': len(warning_issues),
            'passed_count': len(passed_checks)
        },
        'issues': {
            'critical': critical_issues,
            'warning': warning_issues,
            'passed': passed_checks
        },
        'recommendations': recommendations
    }
