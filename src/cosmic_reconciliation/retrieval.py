from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Iterable

_TOKEN_RE = re.compile(r"[A-Za-z0-9_'-]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def hashed_embedding(text: str, dims: int = 256) -> list[float]:
    """Dependency-free feature hashing for portable semantic-ish retrieval.

    This is intentionally a baseline, not a claim of neural semantic equivalence.
    Applications can inject a real embedding function through MemoryAdapter.
    """
    vec = [0.0] * dims
    counts = Counter(tokenize(text))
    for token, count in counts.items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(digest[:4], "big") % dims
        sign = -1.0 if digest[4] & 1 else 1.0
        vec[idx] += sign * (1.0 + math.log(count))
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: Iterable[float], b: Iterable[float]) -> float:
    aa, bb = list(a), list(b)
    if len(aa) != len(bb):
        raise ValueError("embedding dimensions differ")
    return sum(x * y for x, y in zip(aa, bb))
