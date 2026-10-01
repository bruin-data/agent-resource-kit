#!/usr/bin/env python3
"""Identifier handling and per-actor field extraction.


Two jobs:

1. Turn whatever the user typed (a slug, a full LinkedIn URL, a numeric id, a
   member URN) into the shape a given actor wants, and into a stable cache key.
2. Pull a handful of comparable fields out of each actor's very different
   response, so the CLI can print one manifest shape instead of nine.

**Every extractor here probes a set of aliases rather than one field name.**
These are third-party actors scraping a site that changes. Field names drift
between actor versions (``company_id`` / ``companyId`` / ``company_urn``,
``universal_name`` / ``universalName`` / ``publicIdentifier``), so a missing
field must surface as ``null`` and never as a crash. The raw item always goes
to the cache and to ``--output-dir`` unmodified; the summary is a convenience,
not the data.

Nothing here invents a value. If an actor returns followers as the string
"70K followers", that string is what you get.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------

_RE_LINKEDIN_PREFIX = re.compile(
    r"^(?:https?://)?(?:[a-z]{2,3}\.)?(?:www\.)?linkedin\.com/"
    r"(?:company|school|in)/",
    re.IGNORECASE,
)

# LinkedIn job URLs look like /jobs/view/<title-slug>-<id> or /jobs/view/<id>.
_RE_JOB_ID = re.compile(r"(\d{6,})")


def strip_url(value: str) -> str:
    """Return the path tail after ``linkedin.com/{company,school,in}/``."""
    v = value.strip().rstrip("/")
    v = _RE_LINKEDIN_PREFIX.sub("", v)
    v = v.split("?", 1)[0].split("#", 1)[0]
    return v.split("/", 1)[0]


def slugify(value: str) -> str:
    """A filesystem-safe, lowercase slug from a LinkedIn identifier or URL.

    Lowercased so that case variants of the same vanity URL share one cache
    key; LinkedIn's own canonical identifier is lowercase.
    """
    v = strip_url(value)
    v = re.sub(r"[^A-Za-z0-9_.-]+", "-", v).strip("-").lower()
    return v or "unknown"


def is_company_id(value: str) -> bool:
    """A numeric LinkedIn company id, e.g. '1441'."""
    return value.strip().isdigit()


def is_profile_vmid(value: str) -> bool:
    """A LinkedIn member URN tail. These start with 'ACoA'."""
    v = value.strip()
    return v.startswith("ACoA") or v.startswith("urn:li:fsd_profile:")


def normalise_profile_url(value: str) -> str:
    """Accept a slug, a member URN or a partial URL; return a full profile URL."""
    v = value.strip().rstrip("/")
    if not v:
        return v
    if is_profile_vmid(v):
        tail = v.split(":")[-1] if v.startswith("urn:") else v
        return f"https://www.linkedin.com/in/{tail}"
    if v.startswith("http://") or v.startswith("https://"):
        return v
    if v.startswith("linkedin.com") or v.startswith("www.linkedin.com"):
        return "https://" + v
    if v.startswith("in/"):
        return "https://www.linkedin.com/" + v
    return f"https://www.linkedin.com/in/{v}"


def normalise_username(value: str) -> str:
    """A bare vanity slug from a slug, a full profile URL or an 'in/x' path."""
    v = value.strip().rstrip("/")
    if v.lower().startswith("in/"):
        v = v.split("/", 1)[1]
    return slugify(strip_url(v))


def classify_input(raw: str, kind: str) -> Dict[str, Any]:
    """Describe how to look up and scrape one identifier.

    ``kind`` is 'company' or 'profile'. Classification runs on the URL path
    tail, so a numeric company id or a member URN buried in a full URL is
    treated the same as the bare identifier.
    """
    v = raw.strip()
    tail = strip_url(v)
    rec: Dict[str, Any] = {
        "raw": raw,
        "key_type": "slug",
        "key": slugify(v),
        "slug_hint": slugify(v) or None,
    }
    if kind == "company" and is_company_id(tail):
        rec["key_type"] = "id"
        rec["key"] = tail
        rec["slug_hint"] = None
    elif kind == "profile" and is_profile_vmid(tail):
        rec["key_type"] = "id"
        rec["key"] = tail.split(":")[-1] if tail.startswith("urn:") else tail
        rec["slug_hint"] = None
    return rec


def extract_job_id(raw: str) -> Optional[str]:
    """The numeric LinkedIn job id in ``raw``, from a bare id or a jobs URL."""
    if not isinstance(raw, str):
        return None
    v = raw.strip()
    if not v:
        return None
    if v.isdigit():
        return v
    match = _RE_JOB_ID.search(v)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Small helpers used by the per-actor extractors
# ---------------------------------------------------------------------------


def _pick(sources: List[Dict[str, Any]], *keys: str) -> Optional[Any]:
    for src in sources:
        if not isinstance(src, dict):
            continue
        for key in keys:
            value = src.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                return value
    return None


def _sub(item: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = item.get(key)
    return value if isinstance(value, dict) else {}


def _flatten_location(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        return value.get("full") or value.get("city") or value.get("country")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def display_name(item: Dict[str, Any]) -> Optional[str]:
    """Best-effort display name, for manifests that would otherwise be ids."""
    if not isinstance(item, dict):
        return None
    basic = _sub(item, "basic_info") or _sub(item, "basicInfo")
    return _pick(
        [basic, item], "name", "fullname", "fullName", "full_name", "displayName"
    )


# ---------------------------------------------------------------------------
# company (detail)
# ---------------------------------------------------------------------------


def company_id(item: Dict[str, Any]) -> Optional[str]:
    """The numeric LinkedIn company id, which is the stable key.

    Some actor versions return ``company_urn`` as a bare integer, others as a
    URN string; both shapes are handled.
    """
    for key in ("company_urn", "companyUrn", "companyId", "company_id", "id", "lcid"):
        value = item.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int) and value > 0:
            return str(value)
        if isinstance(value, str) and value.strip().isdigit():
            return value.strip()
    for key in ("company_urn", "companyUrn", "urn", "entityUrn"):
        urn = item.get(key)
        if isinstance(urn, str):
            match = re.search(r":(\d+)\b", urn)
            if match:
                return match.group(1)
    return None


def company_slug(item: Dict[str, Any], fallback: str) -> str:
    basic = _sub(item, "basic_info") or _sub(item, "basicInfo")
    for src in ([basic, item] if basic else [item]):
        value = _pick(
            [src],
            "universal_name",
            "universalName",
            "input_identifier",
            "inputIdentifier",
            "username",
            "publicIdentifier",
            "slug",
        )
        if isinstance(value, str):
            return slugify(value)
        url = _pick([src], "linkedin_url", "linkedinUrl", "url")
        if isinstance(url, str):
            return slugify(url)
    return fallback


def company_input_echo(item: Dict[str, Any]) -> Optional[str]:
    """The echo of the user's input that the company actor preserves.

    Without it, responses that come back out of order cannot be attributed to
    the identifier that asked for them.
    """
    value = _pick([item], "input_identifier", "inputIdentifier")
    return value if isinstance(value, str) else None


def company_attribute(item: Dict[str, Any], fallback: str) -> Tuple[Optional[str], str]:
    return company_id(item), company_slug(item, fallback)


def company_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    basic = _sub(item, "basic_info") or _sub(item, "basicInfo")
    return {
        "name": _pick([basic, item], "name", "company_name", "companyName"),
        "industry": _pick([basic, item], "industry", "industries"),
        "location": _flatten_location(
            basic.get("location") or item.get("location") or item.get("headquarter")
        ),
        "followers": _pick(
            [basic, item], "follower_count", "followerCount", "followers"
        ),
        "employees": _pick(
            [basic, item], "employee_count", "employeeCount", "staff_count", "staffCount"
        ),
        "website": _pick([basic, item], "website", "company_website"),
    }


# ---------------------------------------------------------------------------
# profile (detail)
# ---------------------------------------------------------------------------


def profile_id(item: Dict[str, Any]) -> Optional[str]:
    """The member URN tail, e.g. 'ACoAA...'."""
    for key in ("vmid", "memberId", "member_id", "publicId", "public_id"):
        value = item.get(key)
        if isinstance(value, str) and value.strip().startswith("ACoA"):
            return value.strip()
    for key in ("urn", "entityUrn", "profileUrn", "memberUrn"):
        value = item.get(key)
        if isinstance(value, str):
            match = re.search(r":(ACoA[A-Za-z0-9_-]+)", value)
            if match:
                return match.group(1)
    return None


def profile_slug(item: Dict[str, Any], fallback: str) -> str:
    value = _pick(
        [item],
        "publicIdentifier",
        "public_identifier",
        "username",
        "vanityName",
        "linkedinUrl",
        "url",
        "profileUrl",
    )
    return slugify(value) if isinstance(value, str) else fallback


def profile_attribute(item: Dict[str, Any], fallback: str) -> Tuple[Optional[str], str]:
    return profile_id(item), profile_slug(item, fallback)


def profile_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    basic = _sub(item, "basic_info") or _sub(item, "basicInfo")
    company = basic.get("current_company") or item.get("currentCompany")
    if isinstance(company, dict):
        company = company.get("name") or company.get("companyName")
    return {
        "name": display_name(item),
        "headline": _pick([basic, item], "headline", "summary"),
        "current_job_title": _pick(
            [basic, item], "current_job_title", "currentJobTitle", "jobTitle", "title"
        ),
        "current_company": company if isinstance(company, str) else None,
        "location": _flatten_location(basic.get("location") or item.get("location")),
    }


# ---------------------------------------------------------------------------
# people-search
# ---------------------------------------------------------------------------


def people_search_keys(
    item: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str]]:
    """(slug, member URN) for a people-search hit."""
    basic = _sub(item, "basic_info")
    slug = None
    for src in (basic, item):
        value = _pick(
            [src], "public_identifier", "publicIdentifier", "username", "vanityName"
        )
        if isinstance(value, str):
            slug = slugify(value)
            break
        url = _pick([src], "profile_url", "profileUrl", "url")
        if isinstance(url, str):
            slug = slugify(url)
            break
    linkedin_id = None
    for src in (basic, item):
        value = _pick([src], "vmid", "memberId", "member_id")
        if isinstance(value, str) and value.startswith("ACoA"):
            linkedin_id = value
            break
        for key in ("urn", "entityUrn", "profileUrn", "memberUrn"):
            raw = src.get(key)
            if isinstance(raw, str):
                match = re.search(r"(ACoA[A-Za-z0-9_-]+)", raw)
                if match:
                    linkedin_id = match.group(1)
                    break
        if linkedin_id:
            break
    return slug, linkedin_id


def people_search_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    basic = _sub(item, "basic_info")
    name = _pick([basic, item], "fullname", "fullName", "full_name", "name")
    if not name:
        first = _pick([basic, item], "first_name", "firstname", "firstName")
        last = _pick([basic, item], "last_name", "lastname", "lastName")
        parts = [str(p) for p in (first, last) if p]
        name = " ".join(parts) or None

    company = basic.get("current_company") or item.get("current_company")
    if isinstance(company, dict):
        company = company.get("name") or company.get("companyName")
    elif not isinstance(company, str):
        company = None

    title = _pick(
        [basic, item], "current_job_title", "currentJobTitle", "jobTitle", "title"
    )

    # Some versions leave basic_info.current_company null and put the current
    # role in experience[0] instead.
    experience = item.get("experience")
    if (not company or not title) and isinstance(experience, list) and experience:
        first_role = experience[0] if isinstance(experience[0], dict) else {}
        company = company or _pick(
            [first_role], "company", "company_name", "companyName"
        )
        title = title or _pick([first_role], "title", "jobTitle")

    return {
        "name": name,
        "headline": _pick([basic, item], "headline", "summary", "bio"),
        "current_job_title": title,
        "current_company": company,
        "location": _flatten_location(basic.get("location") or item.get("location")),
        "linkedin_url": _pick(
            [basic, item], "profile_url", "profileUrl", "url", "linkedinUrl"
        ),
    }


def is_empty_people_hit(item: Dict[str, Any]) -> bool:
    """True for the placeholder row this actor returns instead of no results.

    An empty search comes back as one item with every identity field null, not
    as an empty dataset. Treating that as a result is how an agent ends up
    reporting a person who does not exist.
    """
    slug, linkedin_id = people_search_keys(item)
    summary = people_search_summary(item)
    return not slug and not linkedin_id and not summary.get("name")


# ---------------------------------------------------------------------------
# company-search
# ---------------------------------------------------------------------------


def company_search_keys(item: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """(slug, numeric company id) for a company-search hit."""
    cid = _pick([item], "company_id", "companyId", "id")
    linkedin_id = str(cid).strip() if cid not in (None, "") else None

    slug = None
    value = _pick([item], "universal_name", "universalName", "slug", "vanityName")
    if isinstance(value, str):
        slug = slugify(value)
    if not slug:
        url = _pick(
            [item], "company_url", "companyUrl", "url", "linkedin_url", "linkedinUrl"
        )
        if isinstance(url, str):
            match = re.search(r"linkedin\.com/(?:company|school)/([^/?#]+)", url)
            if match:
                slug = slugify(match.group(1))
    return slug, linkedin_id


def company_search_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": _pick([item], "name", "company_name", "companyName"),
        "description": _pick([item], "description", "tagline", "summary"),
        "industry": _pick([item], "industry", "industry_name", "industryName"),
        "location": _flatten_location(
            item.get("location") or item.get("headquarter")
        ),
        "followers": _pick(
            [item],
            "follower_count",
            "followerCount",
            "followers_count",
            "followersCount",
            "followers",
        ),
        "company_size": _pick(
            [item], "company_size", "companySize", "staff_count_range", "staffCountRange"
        ),
        "linkedin_url": _pick(
            [item], "company_url", "companyUrl", "url", "linkedin_url", "linkedinUrl"
        ),
    }


# ---------------------------------------------------------------------------
# post-search
# ---------------------------------------------------------------------------


def post_search_keys(item: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """(post URN tail, author URN).

    The slug slot holds the post URN, not a person or company slug, so two
    searches that surface the same post share one cached row. The id slot holds
    the author URN parsed out of the author's profile URL: an 'ACoA' member URN
    for a person, absent for a company page.
    """
    post_urn = None
    full_urn = item.get("full_urn")
    if isinstance(full_urn, str) and full_urn.strip():
        post_urn = full_urn.strip().split("urn:li:", 1)[-1] or None
    if not post_urn:
        activity = item.get("activity_id") or item.get("urn")
        if activity:
            post_urn = f"activity:{activity}"

    author = _sub(item, "author")
    author_urn = None
    profile_url = author.get("profile_url")
    if isinstance(profile_url, str):
        match = re.search(r"(ACoA[A-Za-z0-9_-]+)", profile_url)
        if match:
            author_urn = match.group(1)
    return post_urn, author_urn


def post_search_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    author = _sub(item, "author")
    stats = _sub(item, "stats")
    content = _sub(item, "content")
    posted_at = _sub(item, "posted_at")

    likes = None
    reactions = stats.get("reactions")
    if isinstance(reactions, list):
        for reaction in reactions:
            if isinstance(reaction, dict):
                if str(reaction.get("type") or "").upper() == "LIKE":
                    likes = reaction.get("count")
                    break

    return {
        "post_url": item.get("post_url"),
        "posted_at": posted_at.get("date") or posted_at.get("display_text"),
        "text": item.get("text"),
        "hashtags": item.get("hashtags") or None,
        "is_reshare": item.get("is_reshare"),
        "author_name": author.get("name"),
        "author_headline": author.get("headline"),
        "author_url": author.get("profile_url"),
        "likes": likes,
        "comments": stats.get("comments"),
        "shares": stats.get("shares"),
        "reactions_total": stats.get("total_reactions"),
        "content_type": content.get("type"),
    }


# ---------------------------------------------------------------------------
# profile-posts
# ---------------------------------------------------------------------------


def flatten_profile_posts(items: List[Any]) -> List[Dict[str, Any]]:
    """One dict per post, whichever wrapper shape this run produced.

    The actor is documented as emitting a single ``{data: {posts: [...]}}``
    object, but live runs have also pushed one post per dataset item. Accept
    both so the cache always stores one row per post.
    """
    out: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        container = None
        if isinstance(item.get("data"), dict) and isinstance(
            item["data"].get("posts"), list
        ):
            container = item["data"]
        elif isinstance(item.get("posts"), list):
            container = item
        if container is not None:
            token = container.get("pagination_token")
            for post in container["posts"]:
                if isinstance(post, dict):
                    copied = dict(post)
                    if token:
                        copied["pagination_token"] = token
                    out.append(copied)
            continue
        out.append(item)
    return out


def profile_posts_keys(item: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """(post URN tail, author username).

    This actor does not expose member URNs, so the id slot holds the author's
    public username. It will not join against anything keyed on an 'ACoA' URN.
    """
    post_urn = None
    full_urn = item.get("full_urn")
    if isinstance(full_urn, str) and full_urn.strip():
        post_urn = full_urn.strip().split("urn:li:", 1)[-1] or None
    if not post_urn:
        bare = item.get("urn")
        if isinstance(bare, str) and bare.strip():
            post_urn = f"activity:{bare.strip()}"

    author = _sub(item, "author")
    username = author.get("username")
    if isinstance(username, str) and username.strip():
        return post_urn, username.strip().lower()
    return post_urn, None


def profile_posts_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    author = _sub(item, "author")
    stats = _sub(item, "stats")
    posted_at = _sub(item, "posted_at")
    media = _sub(item, "media")
    article = _sub(item, "article")
    document = _sub(item, "document")
    reshared = item.get("reshared_post")
    reshared = reshared if isinstance(reshared, dict) else None

    name_parts = [
        value
        for value in (author.get("first_name"), author.get("last_name"))
        if isinstance(value, str) and value.strip()
    ]

    media_type = media.get("type")
    if not media_type and article:
        media_type = "article"
    if not media_type and document:
        media_type = "document"

    return {
        "post_url": item.get("url"),
        "posted_at": posted_at.get("date") or posted_at.get("relative"),
        "post_type": item.get("post_type"),
        "is_reshare": bool(reshared) or item.get("post_type") == "quote",
        "text": item.get("text"),
        "author_name": " ".join(name_parts) or None,
        "author_username": author.get("username"),
        "author_headline": author.get("headline"),
        "likes": stats.get("like"),
        "comments": stats.get("comments"),
        "reposts": stats.get("reposts"),
        "reactions_total": stats.get("total_reactions"),
        "media_type": media_type,
        "reshared_author": (
            _sub(reshared, "author").get("username") if reshared else None
        ),
        "pagination_token": item.get("pagination_token"),
    }


# ---------------------------------------------------------------------------
# job-search and job detail
# ---------------------------------------------------------------------------


def flatten_job_items(items: List[Any]) -> Tuple[List[Dict[str, Any]], Optional[int]]:
    """Job rows plus the actor's own total, from either output shape.

    The actor has been seen yielding one dataset item per posting and yielding
    a single ``{jobsFound, results: [...]}`` wrapper.
    """
    postings: List[Dict[str, Any]] = []
    reported_total: Optional[int] = None
    for item in items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("results"), list):
            if isinstance(item.get("jobsFound"), int):
                reported_total = item["jobsFound"]
            for result in item["results"]:
                if isinstance(result, dict):
                    postings.append(result)
        else:
            postings.append(item)
    return postings, reported_total


def job_search_keys(item: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """(job URL, company name). Job postings have no vanity slug."""
    job_url = _pick([item], "job_url", "jobUrl")
    company = _pick([item], "company", "company_name", "companyName")
    return (
        job_url if isinstance(job_url, str) else None,
        company if isinstance(company, str) else None,
    )


def job_search_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "company": _pick([item], "company", "company_name", "companyName"),
        "company_url": _pick([item], "company_url", "companyUrl"),
        "job_title": _pick([item], "job_title", "jobTitle", "title"),
        "job_url": _pick([item], "job_url", "jobUrl"),
        "location": _pick([item], "location"),
        "remote": item.get("remote"),
        "posted_at": _pick([item], "posted_at", "postedAt"),
        "job_type": _pick([item], "job_type", "jobType"),
        "is_easy_apply": item.get("is_easy_apply", item.get("isEasyApply")),
    }


def job_id_from_item(item: Dict[str, Any]) -> Optional[str]:
    """The numeric posting id an item carries, used to attribute responses."""
    info = _sub(item, "job_info")
    jid = info.get("job_posting_id") or item.get("job_posting_id")
    if isinstance(jid, int):
        return str(jid)
    if isinstance(jid, str) and jid.strip():
        return jid.strip()
    return None


def job_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    info = _sub(item, "job_info")
    company = _sub(item, "company_info")
    salary = _sub(item, "salary_info")
    apply_details = _sub(item, "apply_details")
    return {
        "job_title": _pick([info, item], "title", "job_title"),
        "company": _pick([company, item], "name", "company_name"),
        "location": _pick([info, item], "location"),
        "employment_status": info.get("employment_status"),
        "experience_level": info.get("experience_level"),
        "is_remote_allowed": info.get("is_remote_allowed"),
        "listed_at": info.get("listed_at"),
        "salary_min": salary.get("min_salary"),
        "salary_max": salary.get("max_salary"),
        "salary_currency": salary.get("currency_code"),
        "total_applies": apply_details.get("total_applies"),
    }
