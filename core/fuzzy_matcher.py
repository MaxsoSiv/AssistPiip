from rapidfuzz import fuzz, process
import re


def normalize(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


class FuzzyMatcher:
    def __init__(self, threshold: int = 80):
        self.threshold = threshold

    def best_match(self, query: str, candidates: list[str]) -> str | None:
        if not candidates:
            return None
        q = normalize(query)
        if not q:
            return None

        result = process.extractOne(
            q, candidates, scorer=fuzz.WRatio, score_cutoff=self.threshold
        )
        if result is None:
            return None
        return result[0]
