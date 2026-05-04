from __future__ import annotations

import io
import logging
import re
import zipfile
from typing import Optional

import httpx
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# 50 MB compressed cap
_ZIPBALL_MAX_BYTES = 50 * 1024 * 1024  

# 200 KB per individual file
_MAX_FILE_BYTES = 200 * 1024     

# 2 MB concatenated text cap
_MAX_TEXT_BYTES = 2 * 1024 * 1024             

_METADATA_TIMEOUT = httpx.Timeout(15.0, connect=10.0)
_ZIPBALL_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

_ALLOWED_EXTENSIONS = frozenset({
    "md", "markdown", "rst", "txt",
    "py", "js", "mjs", "cjs", "ts", "tsx", "jsx",
    "java", "c", "cpp", "cc", "h", "hpp",
    "go", "rs", "rb", "php", "cs", "kt", "swift",
    "sql", "yaml", "yml", "json", "toml",
    "html", "css", "scss", "sh", "ipynb",
})

_SKIP_PATH_SEGMENTS = (
    ".git/", "node_modules/", "dist/", "build/",
    "__pycache__/", ".venv/", "venv/", ".next/",
    "target/", "vendor/",
)

_GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/"
    r"(?P<owner>[^/\s]+)/"
    r"(?P<repo>[^/\s#?]+?)"
    r"(?:\.git)?"
    r"(?:/(?:tree|blob)/(?P<ref>[^/\s?#]+)(?:/.*)?)?"
    r"/?$",
    re.IGNORECASE,
)

_SANITIZE_RE = re.compile(r"[^a-z0-9]+")

async def fetch_repo_as_text(url: str, ref: Optional[str]) -> tuple[bytes, str]:
    owner, repo, ref_from_url = _parse_github_url(url)

    explicit_ref = (ref or "").strip() or None
    url_ref = ref_from_url or None

    headers = _build_headers()

    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        effective_ref = explicit_ref or url_ref
        if effective_ref is None:
            effective_ref = await _resolve_default_branch(client, owner, repo)

        zip_bytes = await _download_zipball(client, owner, repo, effective_ref)

    text_bytes = _concat_zip_text(zip_bytes)
    filename = _canonical_filename(owner, repo, effective_ref)

    return text_bytes, filename

def _parse_github_url(url: str) -> tuple[str, str, Optional[str]]:
    if not isinstance(url, str) or not url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub URL is required.",
        )

    match = _GITHUB_URL_RE.match(url.strip())

    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a valid github.com HTTPS URL.",
        )

    return match.group("owner"), match.group("repo"), match.group("ref")


def _build_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "capstone-oral-assessment",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    return headers


async def _resolve_default_branch(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
) -> str:
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        resp = await client.get(api_url, timeout=_METADATA_TIMEOUT)

    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timed out contacting GitHub.",
        ) from e
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e}",
        ) from e

    _raise_for_github_status(resp, context="metadata")

    try:
        default_branch = resp.json().get("default_branch")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub returned an unexpected response.",
        ) from e

    if not default_branch:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not determine the repository's default branch.",
        )
    
    return default_branch


async def _download_zipball(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    ref: str,
) -> bytes:
    zipball_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{ref}"

    try:
        async with client.stream("GET", zipball_url, timeout=_ZIPBALL_TIMEOUT) as resp:
            _raise_for_github_status(resp, context="zipball", ref=ref)

            buffer = io.BytesIO()
            total = 0

            async for chunk in resp.aiter_bytes():
                total += len(chunk)
                if total > _ZIPBALL_MAX_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Repository is too large to import (limit: 50 MB compressed).",
                    )
                
                buffer.write(chunk)

    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timed out downloading repository from GitHub.",
        ) from e
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub download failed: {e}",
        ) from e

    return buffer.getvalue()


def _raise_for_github_status(
    resp: httpx.Response,
    *,
    context: str,
    ref: Optional[str] = None,
) -> None:
    if resp.status_code < 400:
        return

    if resp.status_code == 404:
        detail = (
            f"Branch or ref '{ref}' not found."
            if context == "zipball" and ref
            else "Repository not found. Only public repos are supported."
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    if resp.status_code == 403:
        remaining = resp.headers.get("X-RateLimit-Remaining")

        if remaining == "0":
            reset = resp.headers.get("X-RateLimit-Reset")
            logger.warning(
                "GitHub rate limit hit in %s. Reset at epoch=%s", context, reset,
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="GitHub API rate limit reached — try again later.",
            )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub refused the request. Make sure the repository is public.",
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"GitHub API error ({context}): HTTP {resp.status_code}",
    )


def _concat_zip_text(zip_bytes: bytes) -> bytes:
    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))

    except zipfile.BadZipFile as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub returned an unreadable archive.",
        ) from exc

    pieces: list[bytes] = []

    total_bytes = 0
    truncated = False
    matched = 0

    names = sorted(archive.namelist())

    for name in names:
        info = archive.getinfo(name)

        if info.is_dir():
            continue

        relative = _strip_leading_segment(name)

        if not relative:
            continue
        if _should_skip_path(relative):

            continue
        if not _has_allowed_extension(relative):

            continue
        if info.file_size <= 0 or info.file_size > _MAX_FILE_BYTES:
            continue

        try:
            raw = archive.read(info)

        except (KeyError, zipfile.BadZipFile, RuntimeError) as e:
            logger.warning("Skipping unreadable zip entry %s: %s", name, e)
            continue

        decoded = raw.decode("utf-8", errors="replace")
        block = f"=== FILE: {relative} ===\n{decoded}\n\n".encode("utf-8")

        if total_bytes + len(block) > _MAX_TEXT_BYTES:
            truncated = True
            break

        pieces.append(block)
        total_bytes += len(block)
        matched += 1

    archive.close()

    if matched == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text files found in this repository.",
        )

    if truncated:
        logger.warning(
            "github_importer: truncated to %d bytes after %d files (2 MB cap reached)",
            total_bytes, matched,
        )

    return b"".join(pieces)


def _strip_leading_segment(name: str) -> str:
    idx = name.find("/")

    if idx == -1:
        return ""
    
    return name[idx + 1 :]


def _should_skip_path(relative: str) -> bool:
    lowered = relative.lower()

    for segment in _SKIP_PATH_SEGMENTS:
        if lowered.startswith(segment) or f"/{segment}" in lowered:
            return True
        
    return False


def _has_allowed_extension(relative: str) -> bool:
    dot = relative.rfind(".")

    if dot == -1 or dot == len(relative) - 1:
        return False
    
    ext = relative[dot + 1 :].lower()
    return ext in _ALLOWED_EXTENSIONS


def _canonical_filename(owner: str, repo: str, ref: str) -> str:
    owner_part = _sanitize_segment(owner, 32)
    repo_part = _sanitize_segment(repo, 40)
    ref_part = _sanitize_segment(ref, 12)

    return f"github_{owner_part}_{repo_part}_{ref_part}.txt"


def _sanitize_segment(value: str, max_len: int) -> str:
    cleaned = _SANITIZE_RE.sub("_", value.lower()).strip("_")

    if not cleaned:
        cleaned = "unknown"
        
    return cleaned[:max_len]
