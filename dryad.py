"""Download files from Dryad, which requires an API token since 2025.

Credentials come from ``DRYAD_CLIENT_ID`` and ``DRYAD_CLIENT_SECRET``: log in
to https://datadryad.org with ORCID and create an API account on the
*My account* page. Tokens last 10 hours; one is requested per run.

File metadata (names, sizes, MD5 digests) is public and needs no token, so
``list_files`` works without credentials.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from functools import cache
from typing import Any

API = "https://datadryad.org"


def _get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


@cache
def _token() -> str:
    try:
        client_id = os.environ["DRYAD_CLIENT_ID"]
        secret = os.environ["DRYAD_CLIENT_SECRET"]
    except KeyError as exc:
        raise RuntimeError(
            f"Dryad downloads need an API token: set DRYAD_CLIENT_ID and DRYAD_CLIENT_SECRET ({exc} is unset)"
        ) from None
    body = urllib.parse.urlencode(
        {"client_id": client_id, "client_secret": secret, "grant_type": "client_credentials"}
    ).encode()
    req = urllib.request.Request(f"{API}/oauth/token", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)["access_token"]


def download(file_id: int) -> bytes:
    """Return the bytes of Dryad file ``file_id``."""
    req = urllib.request.Request(f"{API}/api/v2/files/{file_id}/download")
    # Dryad redirects to presigned storage URLs, which reject a second credential.
    req.add_unredirected_header("Authorization", f"Bearer {_token()}")
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read()


def list_files(doi: str) -> list[dict[str, Any]]:
    """Return the files of the latest version of dataset ``doi`` (``10.5061/dryad.xxx``)."""
    dataset = _get_json(f"{API}/api/v2/datasets/{urllib.parse.quote('doi:' + doi, safe='')}")
    url: str | None = API + dataset["_links"]["stash:version"]["href"] + "/files"
    files: list[dict[str, Any]] = []
    while url:
        page = _get_json(url)
        for f in page["_embedded"]["stash:files"]:
            file_id = int(f["_links"]["stash:download"]["href"].split("/")[-2])
            files.append({"id": file_id, "path": f["path"], "size": f["size"], "md5": f.get("digest")})
        nxt = page["_links"].get("next")
        url = API + nxt["href"] if nxt else None
    return files
