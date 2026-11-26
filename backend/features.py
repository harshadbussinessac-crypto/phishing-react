"""Feature extraction: URL, link-mismatch, and keyword features for emails."""
import re
from urllib.parse import urlparse

import numpy as np
from scipy.sparse import hstack
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"']+", re.IGNORECASE)
# Matches HTML anchors like <a href="http://x">text</a>, and "text (http://x)" style
ANCHOR_RE = re.compile(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
IP_HOST_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "ow.ly", "t.co", "is.gd", "cutt.ly"}
RISKY_TLDS = {"xyz", "top", "club", "online", "info", "tk", "ml", "site", "buzz", "zip", "mov"}
PHISH_WORDS = [
    "verify", "urgent", "suspended", "confirm", "password", "click here",
    "act now", "expire", "unusual activity", "claim", "winner", "refund",
    "immediately", "locked", "update your", "credentials", "within 24 hours",
    "bank details", "card details", "restore access",
]


def _normalize(raw):
    return raw if raw.lower().startswith("http") else "http://" + raw


def _host(raw):
    return (urlparse(_normalize(raw)).hostname or "").lower()


def extract_urls(text):
    return [u.rstrip(".,);") for u in URL_RE.findall(text or "")]


def link_mismatch_count(text):
    """Count anchors whose visible text is a URL pointing to a different host."""
    count = 0
    for href, label in ANCHOR_RE.findall(text or ""):
        shown = re.sub(r"<[^>]+>", "", label).strip()
        if URL_RE.search(shown) and _host(shown) and _host(shown) != _host(href):
            count += 1
    return count


def url_features(text):
    """Fixed-length numeric vector describing links: 9 values."""
    urls = extract_urls(text)
    n = len(urls)
    shortened = ip_links = suspicious = https_missing = risky_tld = 0
    for raw in urls:
        host = _host(raw)
        if host in SHORTENERS or any(host.endswith("." + s) for s in SHORTENERS):
            shortened += 1
        if IP_HOST_RE.match(host):
            ip_links += 1
        if any(w in host for w in ("secure", "verify", "login", "account", "update", "billing")):
            suspicious += 1
        if host.rsplit(".", 1)[-1] in RISKY_TLDS:
            risky_tld += 1
        if not _normalize(raw).lower().startswith("https://"):
            https_missing += 1
    return [n, shortened, ip_links, suspicious, https_missing, risky_tld,
            link_mismatch_count(text), int(n > 0), n - len({_host(u) for u in urls})]


def keyword_features(text):
    text = text or ""
    low = text.lower()
    hits = sum(low.count(w) for w in PHISH_WORDS)
    exclam = text.count("!")
    upper_ratio = sum(c.isupper() for c in text) / max(len(text), 1)
    return [hits, exclam, round(upper_ratio, 4), float(np.log1p(len(text)))]


class EmailFeatures(BaseEstimator, TransformerMixin):
    """Turns raw email strings into numeric URL + keyword features."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = [url_features(t) + keyword_features(t) for t in X]
        return np.asarray(rows, dtype=float)


class TextTfidf(BaseEstimator, TransformerMixin):
    """Word TF-IDF + character n-gram TF-IDF on raw email text.

    Defined here (not in a script) so joblib can unpickle it inside app.py.
    """

    def fit(self, X, y=None):
        self.word_ = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
        self.char_ = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                     sublinear_tf=True, min_df=2)
        self.word_.fit(X)
        self.char_.fit(X)
        return self

    def transform(self, X):
        return hstack([self.word_.transform(X), self.char_.transform(X)]).tocsr()
