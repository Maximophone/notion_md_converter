def extract_page_id(page_id_or_url):
    """
    Extracts the 32-character page ID from a Notion page URL or slug.
    """
    if not page_id_or_url:
        return None
    
    # Take the last part of the slug after the hyphen
    parts = page_id_or_url.split('-')
    
    # The ID is the last part, which is 32 characters long
    potential_id = parts[-1]
    
    if len(potential_id) == 32:
        return potential_id
        
    return page_id_or_url # Return original if it doesn't look like a slug