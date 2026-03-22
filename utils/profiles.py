from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from .config import settings

X_HANDLE_PATTERN = re.compile(r"^@?([A-Za-z0-9_]{1,15})$")


class InvalidProfileInputError(ValueError):
    pass


def build_profile(
    profile_input: str,
    manual_notes: str = "",
    manual_posts_text: str = "",
) -> dict[str, Any]:
    normalized = normalize_profile_input(profile_input)

    if normalized["platform"] == "linkedin":
        profile = _build_linkedin_profile(normalized)
    else:
        profile = _build_x_profile(normalized)

    notes = manual_notes.strip()
    manual_posts = [line.strip() for line in manual_posts_text.splitlines() if line.strip()]

    if notes:
        existing_bio = profile.get("bio", "")
        profile["bio"] = f"{existing_bio}\n\nPublic notes added manually:\n{notes}".strip()
        profile["manual_notes"] = notes

    if manual_posts:
        existing_posts = profile.get("recent_posts") or []
        merged_posts = existing_posts + [post for post in manual_posts if post not in existing_posts]
        profile["recent_posts"] = merged_posts

    profile["summary"] = build_profile_summary(profile)
    return profile


def normalize_profile_input(raw_input: str) -> dict[str, str]:
    cleaned = raw_input.strip()
    if not cleaned:
        raise InvalidProfileInputError("Provide a public X handle or LinkedIn profile URL.")

    if "linkedin.com/" in cleaned.lower():
        public_url = _ensure_scheme(cleaned)
        parsed = urlparse(public_url)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2 or parts[0] != "in":
            raise InvalidProfileInputError(
                "Use a public LinkedIn profile URL in the format linkedin.com/in/username."
            )
        slug = parts[1]
        return {
            "platform": "linkedin",
            "raw_input": cleaned,
            "normalized_input": slug,
            "public_url": f"https://www.linkedin.com/in/{slug}/",
        }

    if "x.com/" in cleaned.lower() or "twitter.com/" in cleaned.lower():
        public_url = _ensure_scheme(cleaned)
        parsed = urlparse(public_url)
        parts = [part for part in parsed.path.split("/") if part]
        if not parts:
            raise InvalidProfileInputError("Use a public X profile URL in the format x.com/handle.")
        handle = _normalize_x_handle(parts[0])
        return {
            "platform": "x",
            "raw_input": cleaned,
            "normalized_input": handle,
            "public_url": f"https://x.com/{handle}",
        }

    handle_match = X_HANDLE_PATTERN.match(cleaned)
    if handle_match:
        handle = _normalize_x_handle(cleaned)
        return {
            "platform": "x",
            "raw_input": cleaned,
            "normalized_input": handle,
            "public_url": f"https://x.com/{handle}",
        }

    raise InvalidProfileInputError(
        "Traceify accepts an X handle like @jack or a public LinkedIn profile URL."
    )


def suggested_questions(profile: dict[str, Any]) -> list[str]:
    name = profile.get("display_name") or "this profile"
    common = [
        f"What stands out about {name}?",
        "Give me a short summary in 3 bullet points.",
    ]

    if profile.get("platform") == "linkedin":
        return common + [
            "What can you infer about their work experience?",
            "Do they show any education or skills signals?",
        ]

    return common + [
        "What does their public X presence suggest?",
        "What themes appear in the public notes or posts?",
    ]


def build_profile_summary(profile: dict[str, Any]) -> str:
    parts: list[str] = []
    display_name = profile.get("display_name") or profile.get("normalized_input") or "This person"
    platform = profile.get("platform", "profile")
    parts.append(f"{display_name} is being analyzed from a public {platform} profile.")

    headline = profile.get("headline")
    if headline:
        parts.append(headline.rstrip(".") + ".")

    bio = profile.get("bio")
    if bio:
        parts.append(bio.rstrip(".") + ".")

    location = profile.get("location")
    if location:
        parts.append(f"Location: {location}.")

    followers = profile.get("followers")
    if followers is not None:
        parts.append(f"Followers: {followers}.")

    following = profile.get("following")
    if following is not None:
        parts.append(f"Following: {following}.")

    tweet_count = profile.get("tweet_count")
    if tweet_count is not None:
        parts.append(f"Total posts: {tweet_count}.")

    is_verified = profile.get("is_verified")
    if is_verified is not None:
        parts.append(f"Verified: {'yes' if is_verified else 'no'}.")

    joined_at = profile.get("joined_at")
    if joined_at:
        parts.append(f"Joined: {joined_at}.")

    experience = profile.get("experience") or []
    if experience:
        parts.append("Experience: " + "; ".join(experience[:3]) + ".")

    education = profile.get("education") or []
    if education:
        parts.append("Education: " + "; ".join(education[:2]) + ".")

    skills = profile.get("skills") or []
    if skills:
        parts.append("Skills: " + ", ".join(skills[:6]) + ".")

    recent_posts = profile.get("recent_posts") or []
    if recent_posts:
        parts.append("Recent public content: " + " | ".join(recent_posts[:3]) + ".")

    return " ".join(parts)


def _build_linkedin_profile(normalized: dict[str, str]) -> dict[str, Any]:
    slug = normalized["normalized_input"]
    public_url = normalized["public_url"]
    profile = {
        "platform": "linkedin",
        "input": normalized["raw_input"],
        "normalized_input": slug,
        "display_name": _display_name_from_slug(slug),
        "headline": "LinkedIn public profile",
        "bio": "",
        "location": None,
        "website": public_url,
        "profile_image_url": None,
        "followers": None,
        "recent_posts": [],
        "experience": [],
        "education": [],
        "skills": [],
        "articles": [],
        "public_url": public_url,
        "source_status": "fallback",
        "errors": [],
    }

    if settings.linkedin_username and settings.linkedin_password:
        try:
            from linkedin_api import Linkedin

            api = Linkedin(settings.linkedin_username, settings.linkedin_password)
            raw_profile = api.get_profile(slug)
            profile.update(_map_linkedin_profile(raw_profile, public_url))
            profile["source_status"] = "live"
        except Exception as exc:
            profile["errors"].append(f"LinkedIn live fetch unavailable: {exc}")
    else:
        profile["errors"].append(
            "LinkedIn credentials are not configured, so Traceify is using URL-derived public metadata."
        )

    return profile


def _build_x_profile(normalized: dict[str, str]) -> dict[str, Any]:
    handle = normalized["normalized_input"]
    return {
        "platform": "x",
        "input": normalized["raw_input"],
        "normalized_input": handle,
        "display_name": f"@{handle}",
        "headline": "Public X profile",
        "bio": "",
        "location": None,
        "website": normalized["public_url"],
        "profile_image_url": None,
        "followers": None,
        "recent_posts": [],
        "experience": [],
        "education": [],
        "skills": [],
        "articles": [],
        "public_url": normalized["public_url"],
        "source_status": "manual",
        "errors": [
            "Automated X enrichment is disabled in this version. Add public notes or posts manually for richer answers."
        ],
    }


def _map_linkedin_profile(raw_profile: dict[str, Any], public_url: str) -> dict[str, Any]:
    first_name = (raw_profile.get("firstName") or "").strip()
    last_name = (raw_profile.get("lastName") or "").strip()
    positions = raw_profile.get("experience") or raw_profile.get("positions") or []
    education = raw_profile.get("education") or raw_profile.get("educations") or []
    skills = raw_profile.get("skills") or []

    return {
        "display_name": " ".join(part for part in [first_name, last_name] if part).strip()
        or _display_name_from_slug(raw_profile.get("public_id") or ""),
        "headline": raw_profile.get("headline") or "LinkedIn member",
        "bio": raw_profile.get("summary") or "",
        "location": raw_profile.get("geoLocationName") or raw_profile.get("locationName"),
        "website": public_url,
        "profile_image_url": _extract_linkedin_image(raw_profile),
        "followers": raw_profile.get("followersCount"),
        "recent_posts": [],
        "experience": [_format_linkedin_position(item) for item in positions if item],
        "education": [_format_linkedin_education(item) for item in education if item],
        "skills": _normalize_strings(skills),
        "articles": _normalize_strings(raw_profile.get("articles") or raw_profile.get("publications") or []),
        "public_url": public_url,
        "errors": [],
    }


def _extract_linkedin_image(raw_profile: dict[str, Any]) -> str | None:
    picture = raw_profile.get("displayPictureUrl")
    if picture:
        return picture

    nested_picture = raw_profile.get("profilePictureDisplayImage")
    if isinstance(nested_picture, dict):
        artifacts = nested_picture.get("artifacts") or []
        root_url = nested_picture.get("rootUrl") or ""
        if root_url and artifacts:
            last_artifact = artifacts[-1]
            file_segment = last_artifact.get("fileIdentifyingUrlPathSegment")
            if file_segment:
                return f"{root_url}{file_segment}"
    return None


def _format_linkedin_position(item: Any) -> str:
    if isinstance(item, str):
        return item

    title = item.get("title") or item.get("position") or "Role"
    company = item.get("companyName") or item.get("company") or "Company"
    return f"{title} at {company}"


def _format_linkedin_education(item: Any) -> str:
    if isinstance(item, str):
        return item

    school = item.get("schoolName") or item.get("school") or "School"
    degree = item.get("degreeName") or item.get("degree") or "Degree"
    return f"{degree} from {school}"


def _normalize_strings(values: list[Any]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip():
            normalized.append(value.strip())
        elif isinstance(value, dict):
            label = value.get("name") or value.get("title")
            if isinstance(label, str) and label.strip():
                normalized.append(label.strip())
    return normalized


def _display_name_from_slug(slug: str) -> str:
    cleaned = slug.replace("-", " ").replace("_", " ").strip()
    return cleaned.title() if cleaned else "LinkedIn Member"


def _ensure_scheme(value: str) -> str:
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value}"


def _normalize_x_handle(handle: str) -> str:
    match = X_HANDLE_PATTERN.match(handle.strip())
    if not match:
        raise InvalidProfileInputError(
            "Use a valid X handle with letters, numbers, or underscores only."
        )
    return match.group(1)
