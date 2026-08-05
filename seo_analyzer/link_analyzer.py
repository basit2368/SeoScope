from urllib.parse import urlparse

def analyze_links(soup, base_url):
    """
    Analyzes internal, external, broken, and non-descriptive links.
    """
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc.lower()

    anchors = soup.find_all('a')
    total_links = len(anchors)

    internal_links = []
    external_links = []
    empty_links = []
    generic_anchor_text = []
    missing_rel_noopener = []
    nofollow_links = []

    generic_phrases = {'click here', 'read more', 'here', 'link', 'more', 'info', 'learn more', 'details', 'website'}

    for a in anchors:
        href = a.get('href', '').strip()
        anchor_text = a.get_text().strip()
        rel = a.get('rel', [])
        if isinstance(rel, str):
            rel = rel.split()
        rel = [r.lower() for r in rel]

        if not href or href == '#' or href.lower().startswith('javascript:'):
            empty_links.append({'text': anchor_text or '(No Anchor Text)', 'href': href})
            continue

        if anchor_text.lower() in generic_phrases:
            generic_anchor_text.append({'text': anchor_text, 'href': href})

        if 'nofollow' in rel:
            nofollow_links.append(href)

        # Classify as internal or external
        parsed_href = urlparse(href)
        if not parsed_href.netloc or parsed_href.netloc.lower() == base_domain:
            internal_links.append({'text': anchor_text, 'href': href})
        else:
            external_links.append({'text': anchor_text, 'href': href, 'rel': rel})
            if 'noopener' not in rel and 'noreferrer' not in rel:
                missing_rel_noopener.append(href)

    issues = []

    if total_links == 0:
        issues.append({
            'type': 'warning',
            'category': 'Links & Architecture',
            'title': 'No Links Found',
            'description': "No `<a>` hyper-links detected on this page. Links are critical for web navigation and search crawler discovery.",
            'impact': 'Medium'
        })
    else:
        if len(internal_links) == 0:
            issues.append({
                'type': 'warning',
                'category': 'Links & Architecture',
                'title': 'No Internal Links Detected',
                'description': "Page does not contain any internal links. Internal links distribute PageRank equity and help crawlers discover pages.",
                'impact': 'Medium'
            })

        if len(empty_links) > 0:
            issues.append({
                'type': 'warning',
                'category': 'Links & Architecture',
                'title': 'Empty or Placeholder Links Found',
                'description': f"Found {len(empty_links)} link(s) with empty or '#' anchor href destinations.",
                'impact': 'Low'
            })

        if len(generic_anchor_text) > 0:
            issues.append({
                'type': 'warning',
                'category': 'Links & Architecture',
                'title': 'Non-Descriptive Anchor Text',
                'description': f"{len(generic_anchor_text)} link(s) use generic text like 'click here' or 'read more'. Use keyword-rich anchor text instead.",
                'impact': 'Medium'
            })

        if len(missing_rel_noopener) > 0:
            issues.append({
                'type': 'warning',
                'category': 'Security & Links',
                'title': 'External Links Missing rel="noopener"',
                'description': f"{len(missing_rel_noopener)} external link(s) lack `rel=\"noopener\"` or `rel=\"noreferrer\"` protection.",
                'impact': 'Low'
            })

    return {
        'total_links': total_links,
        'internal_links_count': len(internal_links),
        'external_links_count': len(external_links),
        'empty_links_count': len(empty_links),
        'generic_anchor_count': len(generic_anchor_text),
        'missing_rel_count': len(missing_rel_noopener),
        'nofollow_links_count': len(nofollow_links),
        'internal_links_sample': internal_links[:10],
        'external_links_sample': external_links[:10],
        'issues': issues
    }
