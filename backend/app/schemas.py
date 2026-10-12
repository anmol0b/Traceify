from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Tweet(BaseModel):
    id: str
    text: str
    likes: int = 0
    views: int = 0
    retweets: int = 0
    created_at: str = ""


class TweetStat(BaseModel):
    text: str
    likes: int = 0
    views: int = 0


class TweetInsights(BaseModel):
    total_analyzed: int = 0
    avg_likes: int = 0
    avg_views: int = 0
    top_by_views: list[TweetStat] = Field(default_factory=list)
    top_by_likes: list[TweetStat] = Field(default_factory=list)


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


class ErrorResponse(BaseModel):
    code: str
    message: str
