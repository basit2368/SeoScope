import re
from collections import Counter
from bs4 import BeautifulSoup

STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'cannot', 'could',
    'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have',
    'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is',
    'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once',
    'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some',
    'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this',
    'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where',
    'which', 'while', 'who', 'whom', 'why', 'with', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves'
}


def analyze_keywords(soup, title_text='', meta_desc='', h1_text=''):
    """
    Extracts text, calculates total word count, top 1/2/3-word keyword densities, and flags thin content or keyword stuffing.
    """
    # Remove script, style, and head elements
    soup_copy = BeautifulSoup(str(soup), 'html.parser') if hasattr(soup, '__str__') else soup
    for element in soup_copy(['script', 'style', 'head', 'title', 'meta', 'noscript', 'svg']):
        element.extract()

    raw_text = soup_copy.get_text(separator=' ')
    clean_words = re.findall(r'\b[a-zA-Z]{2,}\b', raw_text.lower())
    
    total_words = len(clean_words)
    filtered_words = [w for w in clean_words if w not in STOP_WORDS]

    # Single-word frequency
    word_counts = Counter(filtered_words)
    top_1grams = []
    for word, count in word_counts.most_common(10):
        density = round((count / total_words) * 100, 2) if total_words > 0 else 0
        top_1grams.append({
            'keyword': word,
            'count': count,
            'density': density
        })

    # 2-word n-grams
    bigrams = [' '.join(filtered_words[i:i+2]) for i in range(len(filtered_words)-1)]
    bigram_counts = Counter(bigrams)
    top_2grams = []
    for phrase, count in bigram_counts.most_common(5):
        if count > 1:
            density = round((count / max(1, total_words - 1)) * 100, 2)
            top_2grams.append({'keyword': phrase, 'count': count, 'density': density})

    # 3-word n-grams
    trigrams = [' '.join(filtered_words[i:i+3]) for i in range(len(filtered_words)-2)]
    trigram_counts = Counter(trigrams)
    top_3grams = []
    for phrase, count in trigram_counts.most_common(5):
        if count > 1:
            density = round((count / max(1, total_words - 2)) * 100, 2)
            top_3grams.append({'keyword': phrase, 'count': count, 'density': density})

    issues = []

    # Thin Content Check
    if total_words < 300:
        issues.append({
            'type': 'warning',
            'category': 'Content Optimization',
            'title': 'Thin Body Content Detected',
            'description': f"Page contains only {total_words} words. Search engines generally rank comprehensive content (300+ words) higher.",
            'impact': 'High' if total_words < 100 else 'Medium'
        })

    # Keyword Stuffing Check (>4.5% density)
    stuffed_keywords = [item['keyword'] for item in top_1grams if item['density'] > 4.5 and item['count'] > 5]
    if stuffed_keywords:
        issues.append({
            'type': 'warning',
            'category': 'Content Optimization',
            'title': 'Potential Keyword Stuffing Detected',
            'description': f"Keyword(s) '{', '.join(stuffed_keywords)}' exceed 4.5% density. Avoid unnatural keyword repetition.",
            'impact': 'Medium'
        })

    # Primary Keyword Presence Check (check if top keyword is present in Title & H1)
    primary_keyword = top_1grams[0]['keyword'] if top_1grams else ''
    in_title = primary_keyword and primary_keyword in (title_text or '').lower()
    in_h1 = primary_keyword and primary_keyword in (h1_text or '').lower()
    in_desc = primary_keyword and primary_keyword in (meta_desc or '').lower()

    if primary_keyword and not in_title:
        issues.append({
            'type': 'warning',
            'category': 'Content Optimization',
            'title': 'Top Keyword Missing from Title Tag',
            'description': f"Your most prominent keyword '{primary_keyword}' is missing from the `<title>` tag.",
            'impact': 'Medium'
        })

    return {
        'total_word_count': total_words,
        'filtered_word_count': len(filtered_words),
        'top_keywords_1gram': top_1grams,
        'top_keywords_2gram': top_2grams,
        'top_keywords_3gram': top_3grams,
        'primary_keyword': primary_keyword,
        'placement': {
            'in_title': in_title,
            'in_h1': in_h1,
            'in_description': in_desc
        },
        'issues': issues
    }
