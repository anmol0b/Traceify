"""Orchestrates profile fetching: normalize → cache → fetch → persist (profile before tweets)."""

from __future__ import annotations

import logging
from collections import OrderedDict
from functools import lru_cache
from threading import Lock

from ..config import get_settings
from ..schemas import Profile
from .profiles import build_profile_summary, normalize_x_input
from .repo import Repo, get_repo
from .x_client import XClient, attach_tweets

log = logging.getLogger(__name__)


class ProfileService:
    def __init__(self, repo: Repo, x_client: XClient, tweet_pages: int = 5, memory_size: int = 200):
        self.repo = repo
        self.x = x_client
        self.tweet_pages = tweet_pages
        # Fallback store so chat still works when Supabase isn't configured.
        self._memory: OrderedDict[str, Profile] = OrderedDict()
        self._memory_size = memory_size
        self._lock = Lock()

    def get_cached(self, raw_handle: str) -> Profile | None:
        handle = normalize_x_input(raw_handle)
        return self.repo.get_cached_profile(handle) or self._memory_get(handle)

    def get(self, raw_handle: str) -> tuple[Profile, bool]:
        """Return (profile, from_cache). Raises TraceifyError subclasses on failure."""
        cached = self.get_cached(raw_handle)
        if cached:
            return cached, True
        return self.fetch(normalize_x_input(raw_handle)), False

    def refresh(self, raw_handle: str) -> Profile:
        handle = normalize_x_input(raw_handle)
        self.repo.delete_profile(handle)
        with self._lock:
            self._memory.pop(handle.lower(), None)
        return self.fetch(handle)

    def fetch(self, handle: str) -> Profile:
        profile, rest_id = self.x.fetch_profile(handle)
        tweets = []
        if rest_id:
            tweets = self.x.fetch_tweets(rest_id, profile.handle, pages=self.tweet_pages)
            if not tweets:
                profile.warnings.append("No recent original tweets could be loaded for this account.")
        attach_tweets(profile, tweets)
        profile.summary = build_profile_summary(profile)

        # Order matters: tweets.handle references profiles.handle.
        self.repo.save_profile(profile)
        self.repo.save_tweets(profile.handle, tweets)
        self._memory_put(profile)
        return profile

    def _memory_get(self, handle: str) -> Profile | None:
        with self._lock:
            profile = self._memory.get(handle.lower())
            if profile:
                self._memory.move_to_end(handle.lower())
            return profile

    def _memory_put(self, profile: Profile) -> None:
        with self._lock:
            self._memory[profile.handle.lower()] = profile
            self._memory.move_to_end(profile.handle.lower())
            while len(self._memory) > self._memory_size:
                self._memory.popitem(last=False)


@lru_cache(maxsize=1)
def get_profile_service() -> ProfileService:
    settings = get_settings()
    return ProfileService(get_repo(), XClient(settings.rapidapi_key), tweet_pages=settings.tweet_pages)
