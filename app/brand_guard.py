def check_text(text, banned_phrases):
    hits = [p for p in (banned_phrases or []) if p.lower() in text.lower()]
    return (len(hits)==0, hits)
