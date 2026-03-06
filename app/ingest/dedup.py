"""Deduplication logic"""
import hashlib
from .normalize import normalize_url, normalize_title, date_bucket

def generate_dedup_key(source: str, url: str, title: str, published_at) -> str:
    """Generate dedup key using SHA256"""
    norm_url = normalize_url(url)
    norm_title = normalize_title(title)
    date_bkt = date_bucket(published_at)
    
    key_string = f"{source}|{norm_url}|{norm_title}|{date_bkt}"
    return hashlib.sha256(key_string.encode()).hexdigest()
