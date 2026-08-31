import re
from typing import Dict, List, Any, Optional

ZERO_WIDTH_CHARS = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad"]
COMMON_BUZZWORDS = ["synergy", "paradigm", "rockstar", "ninja", "disruptive", "cutting-edge", "game-changer", "world-class", "results-driven", "fast-paced"]


def analyze_resume_authenticity(raw_text: Optional[str], candidate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    text = raw_text or ""
    observations = []
    fraud_flags = []
    authenticity_score = 95.0

    # 1. Hidden characters / zero-width text detection
    hidden_char_count = sum(text.count(c) for c in ZERO_WIDTH_CHARS)
    if hidden_char_count > 5:
        fraud_flags.append(f"Detected {hidden_char_count} invisible / zero-width characters (possible SEO/keyword injection).")
        authenticity_score -= 25.0
    else:
        observations.append("No hidden or zero-width text injection detected.")

    # 2. Repeated buzzword / keyword stuffing analysis
    words = re.findall(r"\b[A-Za-z+#.\-]{3,}\b", text.lower())
    word_freq = {}
    for w in words:
        word_freq[w] = word_freq.get(w, 0) + 1

    stuffing_suspects = [w for w, c in word_freq.items() if c > 18 and w not in ["and", "the", "for", "with", "experience", "developer", "engineering"]]
    if stuffing_suspects:
        fraud_flags.append(f"Potential keyword stuffing detected for terms: {', '.join(stuffing_suspects[:4])}")
        authenticity_score -= 15.0
    else:
        observations.append("Keyword density and distribution are natural.")

    # 3. Duplicate section analysis
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30]
    duplicate_lines = set([x for x in lines if lines.count(x) > 1])
    if len(duplicate_lines) >= 2:
        fraud_flags.append(f"Identified {len(duplicate_lines)} duplicate content paragraphs across resume.")
        authenticity_score -= 15.0
    else:
        observations.append("Structure is non-redundant with distinct role descriptions.")

    # 4. Buzzword intensity
    buzz_count = sum(1 for b in COMMON_BUZZWORDS if b in text.lower())
    if buzz_count > 4:
        observations.append(f"Resume contains {buzz_count} generic corporate buzzwords; candidate should be assessed on technical artifacts.")
    else:
        observations.append("Professional language is concise and technical.")

    return {
        "authenticity_score": max(20.0, authenticity_score),
        "status": "Authentic / Clean" if not fraud_flags else "Flagged for Review",
        "fraud_flags": fraud_flags,
        "observations": observations,
        "hidden_text_detected": hidden_char_count > 5,
        "keyword_stuffing_detected": bool(stuffing_suspects),
        "notes": "Authenticity audit completed across layout, character integrity, and wording density."
    }
