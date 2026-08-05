def analyze_headings(soup):
    """
    Analyzes document heading structure (H1-H6), checks hierarchy, empty tags, and H1 count.
    """
    headings = {
        'h1': [],
        'h2': [],
        'h3': [],
        'h4': [],
        'h5': [],
        'h6': []
    }
    
    all_heading_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    empty_headings_count = 0
    overly_long_headings_count = 0
    hierarchy_order = []

    for tag in all_heading_tags:
        level = tag.name.lower()
        text = tag.get_text().strip()
        length = len(text)
        hierarchy_order.append((level, text))

        if not text:
            empty_headings_count += 1
            continue

        if length > 75:
            overly_long_headings_count += 1

        headings[level].append({
            'text': text,
            'length': length
        })

    issues = []
    h1_count = len(headings['h1'])

    # H1 Count Rules
    if h1_count == 0:
        issues.append({
            'type': 'critical',
            'category': 'Headings',
            'title': 'Missing H1 Heading',
            'description': "No `<h1>` tag was found on the page. Every page should have exactly one main H1 heading describing its primary subject.",
            'impact': 'High'
        })
    elif h1_count > 1:
        issues.append({
            'type': 'warning',
            'category': 'Headings',
            'title': 'Multiple H1 Headings Detected',
            'description': f"Found {h1_count} `<h1>` tags. Using a single primary H1 heading per page improves content hierarchy clarity for search engines.",
            'impact': 'Medium'
        })

    # Empty Headings Rule
    if empty_headings_count > 0:
        issues.append({
            'type': 'warning',
            'category': 'Headings',
            'title': 'Empty Heading Tags Found',
            'description': f"Detected {empty_headings_count} empty heading element(s) (e.g. `<h2></h2>`). Remove empty heading tags.",
            'impact': 'Low'
        })

    # Long Headings Rule
    if overly_long_headings_count > 0:
        issues.append({
            'type': 'warning',
            'category': 'Headings',
            'title': 'Overly Long Headings',
            'description': f"Found {overly_long_headings_count} heading(s) exceeding 75 characters. Keep headings clear, concise, and scannable.",
            'impact': 'Low'
        })

    # Heading Hierarchy Jump Check (e.g., H1 followed directly by H4)
    skipped_levels = 0
    previous_level = 0
    for tag_name, _ in hierarchy_order:
        curr_level = int(tag_name[1])
        if previous_level > 0 and curr_level > previous_level + 1:
            skipped_levels += 1
        previous_level = curr_level

    if skipped_levels > 0:
        issues.append({
            'type': 'warning',
            'category': 'Headings',
            'title': 'Illogical Heading Hierarchy Skip',
            'description': "Heading hierarchy skips levels (e.g., jump from H1 directly to H3/H4). Maintain incremental heading progression (H1 -> H2 -> H3).",
            'impact': 'Medium'
        })

    total_headings_count = sum(len(v) for v in headings.values())

    return {
        'breakdown': {
            'h1_count': h1_count,
            'h2_count': len(headings['h2']),
            'h3_count': len(headings['h3']),
            'h4_count': len(headings['h4']),
            'h5_count': len(headings['h5']),
            'h6_count': len(headings['h6']),
            'total_count': total_headings_count
        },
        'headings_data': headings,
        'issues': issues
    }
