"""URL and title normalization"""
import re
from urllib.parse import urlparse, parse_qs, urlencode
from datetime import datetime

def normalize_url(url: str) -> str:
    """Remove tracking parameters from URL"""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        # Remove tracking parameters
        clean_params = {k: v for k, v in query_params.items() 
                       if not k.startswith('utm_') and k not in ['ref', 'source', 'medium', 'campaign']}
        clean_query = urlencode(clean_params, doseq=True)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{f'?{clean_query}' if clean_query else ''}"
    except:
        return url

def normalize_title(title: str) -> str:
    """Normalize title for dedup"""
    if not title:
        return ""
    # Lowercase, remove extra whitespace, strip special chars
    title = title.lower().strip()
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[^\w\s\-\(\)]', '', title)
    return title

def date_bucket(dt: datetime) -> str:
    """Get date bucket for dedup (YYYY-MM-DD)"""
    if not dt:
        return datetime.now().strftime('%Y-%m-%d')
    return dt.strftime('%Y-%m-%d')
