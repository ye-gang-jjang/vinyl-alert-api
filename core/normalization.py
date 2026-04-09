import re


BRACKET_PATTERN = re.compile(r"\[[^\]]*\]|\([^\)]*\)|\<[^\>]*\>")
NON_WORD_PATTERN = re.compile(r"[^0-9a-zA-Z가-힣]+")
FORMAT_PATTERN = re.compile(r"\b(?:lp|vinyl|1lp|2lp|3lp|컬러반|한정반|예약판매|판매중|품절)\b", re.IGNORECASE)


def normalize_release_text(value: str) -> str:
    normalized = (value or "").strip().lower()
    normalized = BRACKET_PATTERN.sub(" ", normalized)
    normalized = FORMAT_PATTERN.sub(" ", normalized)
    normalized = NON_WORD_PATTERN.sub(" ", normalized)
    return " ".join(normalized.split())
