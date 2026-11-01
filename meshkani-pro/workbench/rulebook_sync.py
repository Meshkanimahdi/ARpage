# Rulebook tab sync (user rule 2026-11-02): the sheet tab `Rulebook` mirrors meshkani-pro/RUNBOOK.md, always the
# latest commit. Mahdi: «یه تب جدید تو شیت هم بزن و همین قوانین رانبوک کامل تو اون تب بیاد و همیشه آپدیت هم بشه».
# Run in the Composio workbench AFTER drive_bridge.py, once the current RUNBOOK.md is in Drive:
#   1) workbench: rb_url = open_update(RULEBOOK_FILE_ID, "text/markdown")   (or open_upload the first time)
#   2) local:     bash meshkani-pro/scripts/drive_put.sh meshkani-pro/RUNBOOK.md "$rb_url" text/markdown
#   3) workbench: rulebook_sync(RULEBOOK_FILE_ID, commit="<git short hash>")
# Row 1: last sync (Tehran time) and commit; then one line of RUNBOOK.md per row; headings (#, ##, ###) bold.

SHEET_ID = "1V6PkoiYAprKCEvsfT1ThGkKTouldAVWG7SoM1Ejrfyo"


def _sx(method, endpoint, body=None, params=None):
    """Sheets API through the googlesheets toolkit (drive_bridge's _px is bound to googledrive)."""
    p = [{"name": k, "value": str(v), "type": "query"} for k, v in (params or {}).items()]
    payload = {"toolkit_slug": "googlesheets", "endpoint": endpoint, "method": method}
    if p: payload["parameters"] = p
    if body is not None: payload["body"] = body
    r = requests.post(_BACKEND + "/api/v3/tool_router/internal/proxy_execute", json=payload,
                      headers={"Content-Type": "application/json"}, timeout=120)
    r.raise_for_status(); d = r.json()
    if (d.get("status") or 200) >= 400: raise RuntimeError(f"Sheets API {d.get('status')}: {str(d.get('data'))[:300]}")
    return d
RULEBOOK_TAB = "Rulebook"


def rulebook_sync(file_id, commit=""):
    import datetime
    text = read_text(file_id)
    lines = text.splitlines()
    base = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
    meta_ = _data(_sx("GET", base, params={"fields": "sheets.properties"}))
    tabs = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta_["sheets"]}
    if RULEBOOK_TAB not in tabs:
        r = _data(_sx("POST", base + ":batchUpdate", body={"requests": [{"addSheet": {"properties": {
            "title": RULEBOOK_TAB, "rightToLeft": False, "gridProperties": {"frozenRowCount": 1, "columnCount": 2}}}}]}))
        tabs[RULEBOOK_TAB] = r["replies"][0]["addSheet"]["properties"]["sheetId"]
    sid = tabs[RULEBOOK_TAB]
    now = (datetime.datetime.utcnow() + datetime.timedelta(hours=3, minutes=30)).strftime("%Y-%m-%d %H:%M")
    rows = [[f"RUNBOOK.md — synced {now} Tehran", f"commit {commit}"]] + [[ln, ""] for ln in lines]
    _sx("POST", f"{base}/values/{RULEBOOK_TAB}!A:B:clear", body={})
    for i in range(0, len(rows), 500):
        _sx("PUT", f"{base}/values/{RULEBOOK_TAB}!A{i + 1}", params={"valueInputOption": "RAW"}, body={"values": rows[i:i + 500]})
    reqs = [{"repeatCell": {"range": {"sheetId": sid}, "cell": {"userEnteredFormat": {"textFormat": {"bold": False},
             "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(textFormat.bold,wrapStrategy)"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
             "properties": {"pixelSize": 1100}, "fields": "pixelSize"}}]
    for n, ln in enumerate(lines, start=2):
        if ln.startswith("#") or n == 2:
            reqs.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": n - 1, "endRowIndex": n},
                         "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat.textFormat.bold"}})
    reqs.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                 "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat.textFormat.bold"}})
    _sx("POST", base + ":batchUpdate", body={"requests": reqs})
    back = _data(_sx("GET", f"{base}/values/{RULEBOOK_TAB}!A1:B2"))
    print("rulebook synced:", len(lines), "lines;", back.get("values", [[]])[0])
    return len(lines)
