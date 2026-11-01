"""gh_farm.py — Local Arena -> GitHub 16 GB Cloud Render Farm Controller.

Reads GitHub token ONLY from `/home/user/.git-credentials` (or `GITHUB_TOKEN` env var)
so zero secrets are ever stored in code or workspace snapshots.

Usage:
  python3 /home/user/studio/gh_farm.py status
  python3 /home/user/studio/gh_farm.py run --mode smoke --out-dir /home/user/studio/samples/cloud_test
  python3 /home/user/studio/gh_farm.py run --mode t1_hq --job-file job.json --out-dir /home/user/studio/samples
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_REPO = "thecattrex/maker-studio"
WORKFLOW_FILE = "cloud_render.yml"


def _load_token() -> str:
    for env_key in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(env_key):
            return os.environ[env_key].strip()
    cred = Path("/home/user/.git-credentials")
    if cred.exists():
        for line in cred.read_text().splitlines():
            line = line.strip()
            if "github.com" in line and "://" in line and "@" in line:
                user_pass = line.split("://", 1)[1].split("@", 1)[0]
                if ":" in user_pass:
                    return user_pass.split(":", 1)[1]
    raise RuntimeError(
        "No GitHub token found in GITHUB_TOKEN or /home/user/.git-credentials"
    )


def _api(method: str, path: str, payload: dict | None = None, repo: str = DEFAULT_REPO):
    tok = _load_token()
    url = path if path.startswith("https://") else f"https://api.github.com/repos/{repo}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "maker-studio-gh-farm",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
        return json.loads(body.decode("utf-8")) if body else {}


def cmd_status(repo: str) -> None:
    info = _api("GET", "", repo=repo)
    runs = _api("GET", "/actions/runs?per_page=5", repo=repo)
    summary = {
        "repo": info["full_name"],
        "private": info["private"],
        "default_branch": info["default_branch"],
        "recent_runs": [
            {
                "id": r["id"],
                "name": r["name"],
                "status": r["status"],
                "conclusion": r["conclusion"],
                "created_at": r["created_at"],
                "url": r["html_url"],
            }
            for r in runs.get("workflow_runs", [])
        ],
    }
    print(json.dumps(summary, indent=2))


def dispatch_and_wait(
    mode: str,
    job_dict: dict | None,
    out_dir: str | None,
    repo: str = DEFAULT_REPO,
    ref: str = "main",
    timeout_s: int = 900,
) -> dict:
    job_b64 = (
        base64.b64encode(json.dumps(job_dict).encode("utf-8")).decode("ascii")
        if job_dict
        else ""
    )

    before = _api("GET", f"/actions/workflows/{WORKFLOW_FILE}/runs?per_page=3", repo=repo)
    seen_ids = {r["id"] for r in before.get("workflow_runs", [])}

    _api(
        "POST",
        f"/actions/workflows/{WORKFLOW_FILE}/dispatches",
        payload={"ref": ref, "inputs": {"mode": mode, "job_b64": job_b64}},
        repo=repo,
    )
    print(f"Dispatched '{mode}' to {repo} ({WORKFLOW_FILE})...")

    # Locate newly created workflow run
    run_id = None
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(4)
        cur = _api("GET", f"/actions/workflows/{WORKFLOW_FILE}/runs?per_page=5", repo=repo)
        for r in cur.get("workflow_runs", []):
            if r["id"] not in seen_ids:
                run_id = r["id"]
                break
        if run_id:
            break

    if not run_id:
        raise RuntimeError("Timed out waiting for GitHub Actions run to appear")

    print(f"Tracking workflow run_id={run_id}...")
    run_obj = {}
    while time.time() < deadline:
        run_obj = _api("GET", f"/actions/runs/{run_id}", repo=repo)
        st, conc = run_obj.get("status"), run_obj.get("conclusion")
        print(f"  status={st} conclusion={conc}")
        if st == "completed":
            break
        time.sleep(8)

    if run_obj.get("status") != "completed":
        raise RuntimeError(f"Run {run_id} did not complete within {timeout_s}s")

    downloaded_files: list[str] = []
    if out_dir:
        arts = _api("GET", f"/actions/runs/{run_id}/artifacts", repo=repo)
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        tok = _load_token()
        for a in arts.get("artifacts", []):
            dl_url = a["archive_download_url"]
            # Download artifact zip (GitHub redirects to Azure blob storage — urllib strips auth on cross-host redirect automatically? Python urllib keeps headers on redirect in older versions, which Azure rejects if Authorization header is forwarded! Handle 302 manually!)
            class _NoRedir(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None

            opener = urllib.request.build_opener(_NoRedir)
            req = urllib.request.Request(
                dl_url,
                headers={
                    "Authorization": f"Bearer {tok}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "maker-studio-gh-farm",
                },
            )
            try:
                resp = opener.open(req, timeout=30)
                zip_bytes = resp.read()
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303, 307, 308):
                    signed_url = e.headers["Location"]
                    zip_bytes = urllib.request.urlopen(signed_url, timeout=120).read()
                else:
                    raise

            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                zf.extractall(dest)
                downloaded_files.extend(str(dest / n) for n in zf.namelist())

    return {
        "run_id": run_id,
        "html_url": run_obj.get("html_url"),
        "conclusion": run_obj.get("conclusion"),
        "downloaded_files": downloaded_files,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_st = sub.add_parser("status")
    p_st.add_argument("--repo", default=DEFAULT_REPO)

    p_run = sub.add_parser("run")
    p_run.add_argument("--repo", default=DEFAULT_REPO)
    p_run.add_argument("--mode", choices=["smoke", "t1_hq", "remotion", "hyperframes", "earshot", "real_sfx", "master", "ironman_edit", "vfx_edit", "aura_edit", "zohair_edit"], default="smoke")
    p_run.add_argument("--job-file", "--job", dest="job_file", default=None)
    p_run.add_argument("--out-dir", default=None)

    args = ap.parse_args()
    if args.cmd == "status":
        cmd_status(args.repo)
    elif args.cmd == "run":
        job = json.loads(Path(args.job_file).read_text()) if args.job_file else None
        res = dispatch_and_wait(args.mode, job, args.out_dir, repo=args.repo)
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
