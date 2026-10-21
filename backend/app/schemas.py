from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Bump when the cached profile shape or the ingest analysis changes, so stale cache rows are refetched.
PROFILE_SCHEMA_VERSION = 2


class Tweet(BaseModel):
    id: str
    text: str
    likes: int = 0
    views: int = 0
    retweets: int = 0
    created_at: str = ""
    has_media: bool = False


class TweetStat(BaseModel):
    text: str
    likes: int = 0
    views: int = 0


class TweetInsights(BaseModel):
    total_analyzed: int = 0
    avg_likes: int = 0
    avg_views: int = 0
    median_likes: int = 0
    median_views: int = 0
    posts_per_week: float | None = None
    first_tweet_at: str | None = None  # ISO date of the oldest analyzed tweet
    last_tweet_at: str | None = None  # ISO date of the newest analyzed tweet
    most_active_weekday: str | None = None
    most_active_hour_utc: int | None = None
    top_by_views: list[TweetStat] = Field(default_factory=list)
    top_by_likes: list[TweetStat] = Field(default_factory=list)


class Topic(BaseModel):
    label: str
    tweet_count: int
    share: float  # fraction of analyzed tweets, 0..1
    tweet_ids: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    handle: str
    display_name: str
    bio: str = ""
    location: str | None = None
    website: str | None = None
    profile_image_url: str | None = None
    followers: int | None = None
    following: int | None = None
    tweet_count: int | None = None
    is_verified: bool = False
    joined_at: str | None = None
    public_url: str
    recent_posts: list[str] = Field(default_factory=list)
    insights: TweetInsights = Field(default_factory=TweetInsights)
    summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    # Every analyzed tweet, newest first. Chat cites them as T1..Tn by position in this list.
    tweets: list[Tweet] = Field(default_factory=list)
    topics: list[Topic] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    schema_version: int = 0


class ProfileResponse(BaseModel):
    profile: Profile
    from_cache: bool = False
    starter_message: str
    suggested_questions: list[str]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    handle: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=50)


class FeedbackRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=64)
    handle: str = Field(min_length=1, max_length=64)
    rating: Literal["up", "down"]
    question: str = Field(default="", max_length=1000)
    answer: str = Field(default="", max_length=8000)
    comment: str = Field(default="", max_length=1000)


class ErrorResponse(BaseModel):
    code: str
    message: str
