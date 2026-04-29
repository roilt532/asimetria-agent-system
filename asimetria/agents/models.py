from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    source: str
    published_at: str
    raw_content: str = ""


@dataclass
class AnalysisResult:
    news_item: NewsItem
    is_asymmetric: bool
    confidence: float
    direction: str          # "bullish" | "bearish" | "neutral"
    reasoning: str
    entities: list = field(default_factory=list)
    asset_mentioned: str = ""


@dataclass
class FilterDecision:
    passes: bool
    reason: str = ""
    flagged_entities: list = field(default_factory=list)
