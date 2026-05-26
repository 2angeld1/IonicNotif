import re
import base64
from typing import Optional
import httpx


GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/([^/]+)(?:/(.+))?)?$"
)

EXTENSION_MAP: dict[str, str] = {
    ".php": "PHP",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".py": "Python",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
}


class GitHubFile:
    def __init__(self, path: str, content: str, language: str, size: int = 0):
        self.path = path
        self.content = content
        self.language = language
        self.size = size

    def __repr__(self):
        return f"<GitHubFile {self.path} ({self.language})>"


class GitHubReaderError(Exception):
    pass


class GitHubRepoReader:
    BASE = "https://api.github.com"
    TIMEOUT = 15.0

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(self.TIMEOUT),
            follow_redirects=True,
        )

    async def close(self):
        await self._http.aclose()

    def parse_url(self, url: str) -> dict:
        m = GITHUB_URL_RE.match(url)
        if not m:
            raise GitHubReaderError(
                "URL inválida. Usa: https://github.com/usuario/repo o "
                "https://github.com/usuario/repo/tree/rama/ruta"
            )
        owner, repo, branch, path = m.groups()
        repo = repo.replace(".git", "")
        return {"owner": owner, "repo": repo, "branch": branch, "path": path or ""}

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _resolve_branch(self, owner: str, repo: str, branch: Optional[str]) -> str:
        if branch:
            return branch
        try:
            resp = await self._http.get(
                f"{self.BASE}/repos/{owner}/{repo}",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return resp.json().get("default_branch", "main")
        except Exception as e:
            print(f"[GitHubReader] Error resolviendo branch: {e}")
        return "main"

    async def list_files(self, url: str) -> list[GitHubFile]:
        info = self.parse_url(url)
        info["branch"] = await self._resolve_branch(info["owner"], info["repo"], info.get("branch"))
        files: list[GitHubFile] = []
        await self._walk_tree(info["owner"], info["repo"], info["branch"], info["path"], files)
        return files

    async def _walk_tree(self, owner: str, repo: str, branch: str, path: str, files: list[GitHubFile]):
        path_part = f"/{path}" if path else ""
        api_url = f"{self.BASE}/repos/{owner}/{repo}/contents{path_part}?ref={branch}"

        try:
            resp = await self._http.get(api_url, headers=self._headers())
        except httpx.TimeoutException:
            print(f"[GitHubReader] Timeout: {api_url}")
            return
        except Exception as e:
            print(f"[GitHubReader] Error: {api_url} - {e}")
            return

        if resp.status_code == 404:
            print(f"[GitHubReader] 404: {api_url}")
            raise GitHubReaderError("URL o ruta del repositorio no encontrada. Verifica la URL y que el repo sea público.")
        if resp.status_code == 403:
            raise GitHubReaderError("Límite de API de GitHub alcanzado (60 req/h sin token).")

        if resp.status_code != 200:
            return

        items = resp.json()
        if not isinstance(items, list):
            items = [items]

        for item in items:
            item_path: str = item["path"]
            if item["type"] == "dir":
                if item["name"].startswith("."):
                    continue
                await self._walk_tree(owner, repo, branch, item_path, files)
            elif item["type"] == "file":
                ext = "." + item_path.rsplit(".", 1)[-1] if "." in item_path else ""
                lang = EXTENSION_MAP.get(ext)
                if lang is None:
                    continue
                content = await self._fetch_content(item["url"])
                if content is not None:
                    files.append(GitHubFile(
                        path=item_path,
                        content=content,
                        language=lang,
                        size=item.get("size", 0),
                    ))

    async def _fetch_content(self, url: str) -> Optional[str]:
        try:
            resp = await self._http.get(url, headers=self._headers())
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        data = resp.json()
        raw = data.get("content", "")
        if data.get("encoding") == "base64":
            try:
                return base64.b64decode(raw).decode("utf-8", errors="replace")
            except Exception:
                return None
        return raw
