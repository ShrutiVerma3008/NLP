import asyncio
import httpx
from gitingest import ingest


async def get_github_summary(username: str) -> str:
    """
    Fetch a rich GitHub summary for the given username.
    1. Get top 5 repos from GitHub REST API
    2. Use GitIngest on the top repo for deeper code context
    """
    try:
        # ── Step 1: Repo metadata ─────────────────────────────────────
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://api.github.com/users/{username}/repos",
                params={"sort": "stars", "per_page": 5, "type": "owner"},
                headers={"Accept": "application/vnd.github.v3+json"},
            )

        if resp.status_code == 404:
            return f"GitHub user '{username}' not found."
        if resp.status_code != 200:
            return f"GitHub API returned status {resp.status_code} for user '{username}'."

        repos = resp.json()
        if not isinstance(repos, list) or len(repos) == 0:
            return f"GitHub user: {username} — No public repositories found."

        # Build header summary
        summary_lines = [f"GitHub Profile: @{username}", f"Top Public Repositories:\n"]
        for repo in repos[:5]:
            summary_lines.append(
                f"• {repo['name']} "
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
                # Run gitingest in a thread pool (it is synchronous)
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
                    summary_lines.append(f"\n--- GitIngest: {top_repo['name']} (top repo code context) ---")
                    # Trim to 3000 chars to stay within LLM token budget
                    summary_lines.append(content[:3000])
                    if len(content) > 3000:
                        summary_lines.append("...[truncated for token efficiency]")

            except Exception as ingest_err:
                summary_lines.append(f"\n[GitIngest unavailable for {top_repo['name']}: {ingest_err}]")

        return "\n".join(summary_lines)

    except Exception as e:
        return f"GitHub summary unavailable: {str(e)}"
