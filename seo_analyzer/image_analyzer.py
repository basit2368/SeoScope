def analyze_images(soup):
    """
    Analyzes images for ALT text presence, empty ALT attributes, generic ALT text, and missing dimensions.
    """
    images = soup.find_all('img')
    total_images = len(images)
    
    missing_alt = []
    empty_alt = []
    generic_alt = []
    missing_dimensions = 0
    missing_lazy = 0
    passed_images = []

    generic_terms = {'image', 'img', 'photo', 'picture', 'pic', 'logo', 'banner', 'icon', 'untitled'}

    for img in images:
        src = img.get('src', '').strip()
        alt = img.get('alt')
        width = img.get('width')
        height = img.get('height')
        loading = img.get('loading')

        if not width or not height:
            missing_dimensions += 1

        if not loading or loading != 'lazy':
            missing_lazy += 1

        if alt is None:
            missing_alt.append({'src': src, 'reason': 'Missing ALT attribute entirely'})
        elif alt.strip() == '':
            empty_alt.append({'src': src, 'reason': 'Empty ALT text attribute'})
        else:
            alt_clean = alt.strip().lower()
            if alt_clean in generic_terms or len(alt_clean) < 3:
                generic_alt.append({'src': src, 'alt': alt, 'reason': 'Generic or non-descriptive ALT text'})
            else:
                passed_images.append({'src': src, 'alt': alt})

    issues = []
    total_missing_or_empty_alt = len(missing_alt) + len(empty_alt)

    if total_images == 0:
        issues.append({
            'type': 'passed',
            'category': 'Images & Media',
            'title': 'No Images Found',
            'description': "No `<img>` elements were found on this page.",
            'impact': 'None'
        })
    else:
        if total_missing_or_empty_alt > 0:
            pct = int((total_missing_or_empty_alt / total_images) * 100)
            severity = 'critical' if pct > 50 else 'warning'
            issues.append({
                'type': severity,
                'category': 'Images & Media',
                'title': f"{total_missing_or_empty_alt} Image(s) Missing ALT Text",
                'description': f"{total_missing_or_empty_alt} out of {total_images} image(s) ({pct}%) lack descriptive ALT attributes. Search engines and screen readers rely on ALT attributes to understand image context.",
                'impact': 'High' if severity == 'critical' else 'Medium'
            })

        if len(generic_alt) > 0:
            issues.append({
                'type': 'warning',
                'category': 'Images & Media',
                'title': 'Generic ALT Text Detected',
                'description': f"{len(generic_alt)} image(s) use non-descriptive ALT terms (e.g. 'photo', 'image'). Replace generic words with specific content descriptions.",
                'impact': 'Low'
            })

        if missing_dimensions > 0:
            issues.append({
                'type': 'warning',
                'category': 'Performance & Images',
                'title': 'Missing Explicit Image Dimensions',
                'description': f"{missing_dimensions} image(s) lack `width` or `height` attributes. Explicit dimensions prevent Cumulative Layout Shift (CLS).",
                'impact': 'Low'
            })

    alt_optimization_percentage = 100 if total_images == 0 else int((len(passed_images) / total_images) * 100)

    return {
        'total_images': total_images,
        'missing_alt_count': len(missing_alt),
        'empty_alt_count': len(empty_alt),
        'generic_alt_count': len(generic_alt),
        'optimized_alt_count': len(passed_images),
        'missing_dimensions_count': missing_dimensions,
        'missing_lazy_count': missing_lazy,
        'alt_score_percentage': alt_optimization_percentage,
        'details': {
            'missing_alt': missing_alt[:10],  # cap list preview
            'empty_alt': empty_alt[:10],
            'generic_alt': generic_alt[:10]
        },
        'issues': issues
    }
