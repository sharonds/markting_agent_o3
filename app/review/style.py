
import re
SENT_SPLIT = re.compile(r"[.!?]+\s+")
WORD_RE = re.compile(r"[A-Za-z\-']+")
PASSIVE_RE = re.compile(r"\b(is|are|was|were|be|been|being)\b\s+\w+(ed|en)\b", re.I)

def analyze_text(text: str) -> dict:
    text = text.strip()
    sentences = [s.strip() for s in SENT_SPLIT.split(text) if s.strip()]
    words = WORD_RE.findall(text)
    word_count = len(words)
    sent_count = max(1, len(sentences))
    avg_words_per_sentence = word_count / sent_count
    exclamations = text.count("!")
    tokens = [w for w in words if len(w) >= 3]
    all_caps = [w for w in tokens if w.isupper()]
    all_caps_ratio = (len(all_caps) / len(tokens)) if tokens else 0.0
    passive_hits = len(PASSIVE_RE.findall(text))
    passive_per_sentence = passive_hits / sent_count

    flags = []
    if avg_words_per_sentence > 26: flags.append("long_sentences")
    if exclamations > 2: flags.append("too_many_exclamations")
    if all_caps_ratio > 0.03: flags.append("shouting_caps")
    if passive_per_sentence > 0.2: flags.append("passive_voice")

    return {
        "sentences": sent_count,
        "words": word_count,
        "avg_words_per_sentence": round(avg_words_per_sentence, 2),
        "exclamations": exclamations,
        "all_caps_ratio": round(all_caps_ratio, 3),
        "passive_hits": passive_hits,
        "passive_per_sentence": round(passive_per_sentence, 3),
        "flags": flags
    }
