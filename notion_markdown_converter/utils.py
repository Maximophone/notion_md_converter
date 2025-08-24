def extract_page_id(page_id_or_url):
    """
    Extract the 32-character Notion ID from a page or database URL/slug/UUID.

    Accepts:
    - Raw 32-char hex ID
    - Hyphenated UUID (36 chars) → returns 32-char normalized
    - Full URLs (page or database), with or without slugs or query params
    - Slugged URLs ending with ...-<32hex>
    """
    if not page_id_or_url:
        return None

    import re
    try:
        from urllib.parse import urlparse
    except Exception:
        urlparse = None

    s = str(page_id_or_url).strip()

    # Direct ID cases
    if re.fullmatch(r"[0-9a-fA-F]{32}", s):
        return s.lower()
    if re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", s):
        return s.replace('-', '').lower()

    # URL cases
    try:
        if urlparse is not None:
            u = urlparse(s)
            if u.scheme and u.netloc:
                path = u.path or ''
                # Prefer IDs from the path, ignore query string (e.g., view IDs)
                m = re.search(r"([0-9a-fA-F]{32})", path)
                if m:
                    return m.group(1).lower()
                m = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", path)
                if m:
                    return m.group(1).replace('-', '').lower()
                # Fallback to slug tail after '-'
                tail = path.split('-')[-1]
                if re.fullmatch(r"[0-9a-fA-F]{32}", tail):
                    return tail.lower()
    except Exception:
        pass

    # Fallback: first 32-hex sequence anywhere (last resort)
    m = re.search(r"([0-9a-fA-F]{32})", s)
    if m:
        return m.group(1).lower()

    return None