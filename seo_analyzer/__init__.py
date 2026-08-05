import datetime
from .crawler import fetch_website_content
from .metadata_analyzer import analyze_metadata
from .heading_analyzer import analyze_headings
from .image_analyzer import analyze_images
from .link_analyzer import analyze_links
from .keyword_analyzer import analyze_keywords
from .technical_analyzer import analyze_technical
from .score_calculator import calculate_seo_scores


def run_seo_audit(target_url):
    """
    Executes a complete automated SEO audit on the target URL.
    Returns structured results dictionary.
    """
    # 1. Fetch HTML content
    crawler_res = fetch_website_content(target_url)
    soup = crawler_res['soup']
    final_url = crawler_res['url']

    # 2. Run Module Analyzers
    metadata_res = analyze_metadata(soup, final_url)
    heading_res = analyze_headings(soup)
    image_res = analyze_images(soup)
    link_res = analyze_links(soup, final_url)
    
    title_text = metadata_res['title']['value'] or ''
    meta_desc = metadata_res['description']['value'] or ''
    h1_text = heading_res['headings_data']['h1'][0]['text'] if heading_res['headings_data']['h1'] else ''

    keyword_res = analyze_keywords(soup, title_text, meta_desc, h1_text)
    technical_res = analyze_technical(crawler_res, soup)

    # 3. Calculate Scores & Recommendations
    scores_res = calculate_seo_scores(
        metadata_res,
        heading_res,
        image_res,
        link_res,
        keyword_res,
        technical_res
    )

    audit_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Combine full report payload
    audit_report = {
        'target_url': target_url,
        'final_url': final_url,
        'audit_date': audit_timestamp,
        'is_simulated': crawler_res.get('is_simulated', False),
        'status_code': crawler_res['status_code'],
        'response_time_ms': crawler_res['response_time_ms'],
        'scores': scores_res,
        'metadata': metadata_res,
        'headings': heading_res,
        'images': image_res,
        'links': link_res,
        'keywords': keyword_res,
        'technical': technical_res
    }

    return audit_report
