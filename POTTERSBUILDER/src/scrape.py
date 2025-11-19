import requests
from bs4 import BeautifulSoup
import re

DDG_HTML = 'https://html.duckduckgo.com/html/'

def ddg_search(query, max_results=5, user_agent=None):
    headers = {'User-Agent': user_agent or 'POTTERSBUILDER/1.0'}
    resp = requests.post(DDG_HTML, data={'q': query}, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'lxml')
    results = []
    for a in soup.select('a.result__a'):
        href = a.get('href')
        if href:
            results.append(href)
        if len(results) >= max_results:
            break
    # Fallback: look for links in other selectors
    if not results:
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http'):
                results.append(href)
            if len(results) >= max_results:
                break
    return results


def fetch_text_from_url(url, user_agent=None):
    headers = {'User-Agent': user_agent or 'POTTERSBUILDER/1.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return None
    soup = BeautifulSoup(r.text, 'lxml')
    # Remove scripts, styles
    for s in soup(['script', 'style', 'noscript', 'header', 'footer', 'aside']):
        s.decompose()
    # Get main text: prioritize article, main, or large paragraphs
    main = soup.find('main') or soup.find('article')
    if main:
        text = ' '.join(p.get_text(separator=' ', strip=True) for p in main.find_all(['p', 'h1', 'h2', 'h3']))
    else:
        paragraphs = soup.find_all('p')
        text = ' '.join(p.get_text(separator=' ', strip=True) for p in paragraphs[:20])
    # Clean whitespace
    text = re.sub(r"\s+", ' ', text).strip()
    if len(text) < 50:
        return None
    return text


def search_and_fetch(query, max_sites=3):
    """Search the web (DuckDuckGo HTML) and fetch textual snippets from top sites.

    Returns list of dicts: {'source': url, 'text': text}
    """
    urls = ddg_search(query, max_results=max_sites)
    results = []
    for u in urls:
        txt = fetch_text_from_url(u)
        if txt:
            results.append({'source': u, 'text': txt})
    return results
