from __future__ import annotations

from typing import Any
import httpx
from utils.profiles import build_profile_summary


def fetch_linkedin_profile(url: str, rapidapi_key: str) -> dict[str, Any]:
    slug = _extract_slug(url)
    public_url = f"https://www.linkedin.com/in/{slug}/"

    profile = _empty_linkedin_profile(slug, public_url)

    if not rapidapi_key:
        profile["errors"] = ["RAPIDAPI_KEY is not set."]
        profile["summary"] = build_profile_summary(profile)
        return profile

    try:
        response = httpx.get(
            "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile",
            params={"linkedin_url": public_url, "include_skills": "true"},
            headers={
                "x-rapidapi-key": rapidapi_key,
                "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        if not data:
            profile["errors"] = ["Empty response from LinkedIn API."]
            profile["summary"] = build_profile_summary(profile)
            return profile

        experiences = [
            f"{e.get('title', '')} at {e.get('company', '')}"
            for e in (data.get("experiences") or [])[:5]
            if e.get("title")
        ]
        education = [
            f"{e.get('degree', '')} from {e.get('school', '')}"
            for e in (data.get("education") or [])[:3]
            if e.get("school")
        ]
        skills = [
            s.get("name", "") for s in (data.get("skills") or [])[:10]
            if s.get("name")
        ]

        profile.update({
            "display_name": data.get("full_name") or slug,
            "headline": data.get("headline") or "LinkedIn member",
            "bio": data.get("summary") or "",
            "location": data.get("location"),
            "profile_image_url": data.get("profile_pic_url"),
            "followers": data.get("followers_count"),
            "experience": experiences,
            "education": education,
            "skills": skills,
            "source_status": "live",
            "errors": [],
        })
        profile["summary"] = build_profile_summary(profile)
        return profile

    except Exception as exc:
        profile["errors"] = [str(exc)]
        profile["summary"] = build_profile_summary(profile)
        return profile


def _extract_slug(url: str) -> str:
    url = url.strip().rstrip("/")
    if "linkedin.com/in/" in url:
        return url.split("linkedin.com/in/")[-1].split("/")[0]
    return url.lstrip("@").strip()


def _empty_linkedin_profile(slug: str, public_url: str) -> dict[str, Any]:
    return {
        "platform": "linkedin",
        "input": public_url,
        "normalized_input": slug,
        "display_name": slug.replace("-", " ").title(),
        "headline": "LinkedIn profile",
        "bio": "",
        "location": None,
        "website": public_url,
        "profile_image_url": None,
        "followers": None,
        "following": None,
        "tweet_count": None,
        "is_verified": None,
        "joined_at": None,
        "recent_posts": [],
        "experience": [],
        "education": [],
        "skills": [],
        "articles": [],
        "public_url": public_url,
        "source_status": "fallback",
        "errors": [],
    }