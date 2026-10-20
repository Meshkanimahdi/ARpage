# Paste this whole file into one COMPOSIO_REMOTE_WORKBENCH call at the start of
# every run. It defines helpers that use the connected Google Drive account
# through Composio's proxy. Upload sessions it prints are single-file Drive
# resumable-upload URLs: the run's own container PUTs the bytes to them with
# scripts/drive_put.sh. Never paste those URLs into the sheet, logs or reports.
import json, os, time, requests

_BACKEND = os.environ.get("BACKEND_URL", "https://backend.composio.dev")
_API = "https://www.googleapis.com/drive/v3"
_UP = "https://www.googleapis.com/upload/drive/v3"


def _px(method, endpoint, body=None, headers=None, params=None):
    p = [{"name": k, "value": str(v), "type": "header"} for k, v in (headers or {}).items()]
    p += [{"name": k, "value": str(v), "type": "query"} for k, v in (params or {}).items()]
    payload = {"toolkit_slug": "googledrive", "endpoint": endpoint, "method": method}
    if p:
        payload["parameters"] = p
    if body is not None:
        payload["body"] = body
    for attempt in range(6):
        r = requests.post(_BACKEND + "/api/v3/tool_router/internal/proxy_execute",
                          json=payload, headers={"Content-Type": "application/json"}, timeout=120)
        r.raise_for_status()
        d = r.json()
        status = d.get("status", 200) if isinstance(d, dict) else 200
        # Drive's shared per-minute quota answers 403/429 rateLimitExceeded; back off.
        if status in (403, 429, 500, 503) and ("ate" in str(d.get("data")) or status != 403):
            time.sleep(5 * (attempt + 1))
            continue
        if status >= 400:
            raise RuntimeError(f"Drive API {status}: {str(d.get('data'))[:400]}")
        return d
    raise RuntimeError(f"Drive API {status} after retries: {str(d.get('data'))[:400]}")


def _data(d):
    x = d.get("data")
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            return x
    return x


def open_upload(name, parent_id, mime="image/jpeg", description=""):
    """Start a new-file upload; returns the one-time session URL."""
    meta = {"name": name, "parents": [parent_id], "mimeType": mime}
    if description:
        meta["description"] = description
    d = _px("POST", _UP + "/files?uploadType=resumable&supportsAllDrives=true", body=meta,
            headers={"X-Upload-Content-Type": mime})
    h = {k.lower(): v for k, v in (d.get("headers") or {}).items()}
    return h["location"]


def open_update(file_id, mime="application/json"):
    """Start a content replacement for an existing file; returns the session URL."""
    d = _px("PATCH", f"{_UP}/files/{file_id}?uploadType=resumable&supportsAllDrives=true", body={},
            headers={"X-Upload-Content-Type": mime})
    h = {k.lower(): v for k, v in (d.get("headers") or {}).items()}
    return h["location"]


def write_text(file_id, text, mime="application/json"):
    """Replace a small text/JSON file's content in place (state files)."""
    return _data(_px("PATCH", f"{_UP}/files/{file_id}?uploadType=media&supportsAllDrives=true",
                     body=text if isinstance(text, str) else json.dumps(text, ensure_ascii=False),
                     headers={"Content-Type": mime}))


def read_text(file_id):
    d = _px("GET", f"{_API}/files/{file_id}", params={"alt": "media", "supportsAllDrives": "true"})
    x = d.get("data")
    return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)


def meta(file_id, fields="id,name,mimeType,size,md5Checksum,parents,webViewLink,createdTime,modifiedTime,description"):
    return _data(_px("GET", f"{_API}/files/{file_id}", params={"fields": fields, "supportsAllDrives": "true"}))


def children(folder_id, name=None, fields="files(id,name,mimeType,size,md5Checksum,createdTime,description,webViewLink)"):
    q = f"'{folder_id}' in parents and trashed = false"
    if name:
        q += " and name = '" + name.replace("'", "\\'") + "'"
    d = _data(_px("GET", f"{_API}/files", params={"q": q, "fields": fields, "pageSize": 1000,
                                                  "orderBy": "createdTime", "supportsAllDrives": "true",
                                                  "includeItemsFromAllDrives": "true"}))
    return d.get("files", [])


def ensure_folder(name, parent_id):
    found = [f for f in children(parent_id, name) if f["mimeType"] == "application/vnd.google-apps.folder"]
    if found:
        return found[0]["id"]
    d = _data(_px("POST", f"{_API}/files?supportsAllDrives=true",
                  body={"name": name, "parents": [parent_id], "mimeType": "application/vnd.google-apps.folder"}))
    return d["id"]


def create_small_file(name, parent_id, description="", mime="text/plain"):
    """Metadata-only file (used for locks and markers)."""
    d = _data(_px("POST", f"{_API}/files?supportsAllDrives=true&fields=id,createdTime",
                  body={"name": name, "parents": [parent_id], "mimeType": mime, "description": description}))
    return d


def acquire_lock(lock_name, run_id, locks_folder_id, settle_seconds=6):
    """Create a lock marker, wait, then the earliest marker with this name wins.
    Returns (won, winner_description)."""
    create_small_file(lock_name, locks_folder_id, description=run_id)
    time.sleep(settle_seconds)
    files = sorted(children(locks_folder_id, lock_name), key=lambda f: (f["createdTime"], f["id"]))
    winner = files[0].get("description", "")
    return winner == run_id, winner


def share_public(file_id):
    return _data(_px("POST", f"{_API}/files/{file_id}/permissions?supportsAllDrives=true",
                     body={"type": "anyone", "role": "reader", "allowFileDiscovery": False}))


def unshare_public(file_id):
    try:
        _px("DELETE", f"{_API}/files/{file_id}/permissions/anyoneWithLink?supportsAllDrives=true")
        return True
    except Exception as e:
        return str(e)


def public_image_url(file_id):
    return f"https://drive.usercontent.google.com/download?id={file_id}&export=download"


print("drive_bridge ready")
