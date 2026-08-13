"""
services/github_service.py — GitHub API and GitIngest context integration

Fetches top public repositories and code context for a GitHub username.
Independent from HTTP routing and LLM response parsing.
"""

import asyncio
import logging
from typing import Optional
import httpx
from gitingest import ingest

logger = logging.getLogger("ai_ris.github")


async def get_github_summary(username: Optional[str]) -> str:
    """
    Fetch a rich GitHub summary for the given username.
    Returns empty string if username is missing or empty.
    Never raises exceptions — handles errors gracefully.
    """
    if not username or not username.strip():
        return ""

    user = username.strip()
    try:
        # ── Step 1: Repo metadata ─────────────────────────────────────
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://api.github.com/users/{user}/repos",
                params={"sort": "stars", "per_page": 5, "type": "owner"},
                headers={"Accept": "application/vnd.github.v3+json"},
            )

        if resp.status_code == 404:
            return f"GitHub user '{user}' not found."
        if resp.status_code != 200:
            return f"GitHub API returned status {resp.status_code} for user '{user}'."

        repos = resp.json()
        if not isinstance(repos, list) or len(repos) == 0:
            return f"GitHub user: {user} — No public repositories found."

        summary_lines = [f"GitHub Profile: @{user}", "Top Public Repositories:\n"]
        for repo in repos[:5]:
            summary_lines.append(
                f"• {repo.get('name', 'N/A')} "
                f"(⭐ {repo.get('stargazers_count', 0)}, "
                f"Language: {repo.get('language', 'N/A')})"
            )
            if repo.get("description"):
                summary_lines.append(f"  └ {repo['description']}")
            topics = repo.get("topics", [])
            if topics:
                summary_lines.append(f"  └ Topics: {', '.join(topics)}")

        # ── Step 2: GitIngest on top repo ─────────────────────────────
        top_repo = repos[0]
        repo_url = top_repo.get("html_url", "")

        if repo_url:
            try:
                loop = asyncio.get_event_loop()
                ingest_result = await loop.run_in_executor(
                    None,
                    lambda: ingest(
                        repo_url,
                        max_file_size=50_000,
                        include_patterns=["*.md", "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.json"],
                        exclude_patterns=["**/node_modules/**", "**/.git/**", "**/dist/**"],
                    )
                )
                _, _, content = ingest_result

                if content:
                    summary_lines.append(f"\n--- GitIngest: {top_repo.get('name', '')} (top repo code context) ---")
                    summary_lines.append(content[:3000])
                    if len(content) > 3000:
                        summary_lines.append("...[truncated for token efficiency]")

            except Exception as ingest_err:
                logger.warning("GitIngest failed for %s: %s", top_repo.get('name'), ingest_err)
                summary_lines.append(f"\n[GitIngest unavailable for {top_repo.get('name')}: {ingest_err}]")

        return "\n".join(summary_lines)

    except Exception as e:
        logger.warning("GitHub service error for user %s: %s", user, e)
        return f"GitHub summary unavailable: {str(e)}"
