# Analytics + Performance-tab helpers for the Composio workbench (RUNBOOK §6 and §5.x).
# Load AFTER drive_bridge.py (needs _BACKEND, _data, read_text, write_text) in one workbench call:
#   exec(<this file>); then  perf_refresh(label, extra_stories)  or  daily_measure()
# Saved in the repo 2026-11-03 because a sandbox restart lost the in-memory versions.
import json, time, statistics, calendar, datetime as dt, requests
from concurrent.futures import ThreadPoolExecutor

SHEET_ID = "1V6PkoiYAprKCEvsfT1ThGkKTouldAVWG7SoM1Ejrfyo"
ACC = "instagram_beath-billow"
IG_USER_ID = "17841471767180096"
FOLLOWERS_FILE = "1hIW9CVHtBI5WlvgSyeMmTmcHalO77P_j"
INSIGHTS_FILE = "1J2dBDhtfdyQrc2ey_i75IGlEcTEJTQcZ"
SLOTS = "1jQHn346k1fcbGRKktMSH0NrCh_HsR54x"
LOCKS = "15mTVnfp8b6qCXHGfJNhyDiZyqiFLMBMI"
_BASE = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
RM = 'views,reach,likes,comments,shares,saved,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time'
CM = 'views,reach,likes,comments,shares,saved,total_interactions'
SM = 'views,reach,replies,shares,navigation,follows,profile_visits,total_interactions'


def _sx(method, endpoint, body=None, params=None):
    p = [{"name": k, "value": str(v), "type": "query"} for k, v in (params or {}).items()]
    payload = {"toolkit_slug": "googlesheets", "endpoint": endpoint, "method": method}
    if p: payload["parameters"] = p
    if body is not None: payload["body"] = body
    for attempt in range(6):
        r = requests.post(_BACKEND + "/api/v3/tool_router/internal/proxy_execute", json=payload,
                          headers={"Content-Type": "application/json"}, timeout=120)
        r.raise_for_status(); d = r.json(); st = d.get("status") or 200
        if st == 429: time.sleep(6 * (attempt + 1)); continue
        if st >= 400: raise RuntimeError(f"Sheets API {st}: {str(d.get('data'))[:300]}")
        return d
    raise RuntimeError("Sheets API: rate limited")


def vals(rng):
    from urllib.parse import quote
    return _data(_sx("GET", f"{_BASE}/values/{quote(rng)}")).get("values", [])


def put(rng, rows):
    from urllib.parse import quote
    rows = [[("" if c is None else c) for c in r] for r in rows]
    return _sx("PUT", f"{_BASE}/values/{quote(rng)}", params={"valueInputOption": "RAW"}, body={"values": rows})


def append_row(tab, row):
    n = len(vals(f"'{tab}'!A1:A3000")) + 1
    put(f"'{tab}'!A{n}", [row]); return n


def tnow():
    return (dt.datetime.utcnow() + dt.timedelta(hours=3, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')


def teh(ts):
    t = dt.datetime.strptime(ts[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=dt.timezone.utc)
    return t, (t + dt.timedelta(hours=3, minutes=30)).strftime('%Y-%m-%dT%H:%M')


def f(v):
    try: return float(v)
    except Exception: return 0.0


def med(xs):
    v = [a for a in xs if a > 0]; return statistics.median(v) if v else 1


def per1k(a, b):
    try: return round(float(a) / float(b) * 1000, 1) if b else ''
    except Exception: return ''


def _ins(mid, metrics):
    res, err = run_composio_tool('INSTAGRAM_GET_IG_MEDIA_INSIGHTS', {'ig_media_id': mid, 'metric': metrics}, account=ACC)
    if err: return None
    return {it['name']: (it.get('values', [{}])[0].get('value') if it.get('values') else (it.get('total_value') or {}).get('value'))
            for it in (res.get('data') or {}).get('data', [])}


def ins_of(m):
    mt = RM if m.get('media_product_type') == 'REELS' else CM
    return _ins(m['id'], mt) or _ins(m['id'], 'reach,likes,comments,shares,saved') or {'_err': 1}


def list_media(days=30):
    cut = (dt.datetime.utcnow() - dt.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S'); out, after = [], None
    while True:
        a = {'ig_user_id': 'me', 'fields': 'id,media_type,media_product_type,timestamp,permalink,caption,like_count,comments_count', 'limit': 50}
        if after: a['after'] = after
        res, err = run_composio_tool('INSTAGRAM_GET_IG_USER_MEDIA', a, account=ACC)
        if err: break
        d = res['data']; items = d.get('data', []); out += items
        after = (d.get('paging') or {}).get('cursors', {}).get('after')
        if not items or not after or items[-1]['timestamp'][:19] < cut or not (d.get('paging') or {}).get('next'): break
    return [m for m in out if m['timestamp'][:19] >= cut]


def slot_index():
    """media id -> (content_id, duration) and the stories of the last 24 h, from the slot files."""
    with ThreadPoolExecutor(8) as ex:
        sl = [x for x in children(SLOTS) if x['name'].endswith('.json')]
        docs = list(ex.map(lambda x: (lambda t: json.loads(t) if t else None)(read_text(x['id'])), sl))
    cid, dur, sto = {}, {}, []
    lim = (dt.datetime.utcnow() - dt.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
    for d in docs:
        if not d: continue
        r = d.get('reel') or {}
        if r.get('media_id'): cid[str(r['media_id'])] = d.get('content_id'); dur[str(r['media_id'])] = (d.get('video') or {}).get('duration')
        p = d.get('post') or {}
        if isinstance(p, dict) and p.get('media_id'): cid[str(p['media_id'])] = d.get('content_id')
        cands = ([d['story']] if isinstance(d.get('story'), dict) else []) + [x for x in (d.get('stories') or []) if isinstance(x, dict)]
        for s in cands:
            if s.get('media_id') and (s.get('published_at') or '') >= lim:
                sto.append((d.get('content_id'), s['media_id'], s['published_at'], s.get('permalink'), s.get('duration')))
    return cid, dur, sto


def followers():
    res, err = run_composio_tool('INSTAGRAM_GET_USER_INFO', {'ig_user_id': 'me', 'fields': 'followers_count'}, account=ACC)
    return res['data']['followers_count']


def perf_refresh(label, extra_stories=()):
    """Rewrite the whole Performance tab (RUNBOOK §5.x). Returns (rows, followers, rows_list)."""
    now = dt.datetime.now(dt.timezone.utc)
    media = list_media(30)
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(ins_of, media))
    MI = {m['id']: x for m, x in zip(media, res)}
    CID, DUR, STO = slot_index()
    seen = set(); STO = [t for t in list(STO) + list(extra_stories) if not (t[1] in seen or seen.add(t[1]))]
    SI = {t[1]: (_ins(t[1], SM) or {}) for t in STO}
    P = vals("'Performance'!A1:AA400"); old = {x[0]: x + [''] * (27 - len(x)) for x in P[1:]}
    fc = followers(); rows = []
    for m in media:
        x = MI[m['id']]; t, tt = teh(m['timestamp']); o = old.get(m['id'])
        typ = 'reel' if m.get('media_product_type') == 'REELS' else ('carousel' if m.get('media_type') == 'CAROUSEL_ALBUM' else m.get('media_type', '').lower())
        aw = (x.get('ig_reels_avg_watch_time') or 0) / 1000 if typ == 'reel' else None
        du = DUR.get(m['id']) or (f(o[21]) / f(o[22]) * 100 if o and f(o[21]) and f(o[22]) else None)
        ret = round(aw / du * 100, 1) if aw and du else (o[22] if o else '')
        meta_ = o[5:13] if o else [''] * 7 + [(m.get('caption') or '').split('\n')[0][:120]]
        rows.append(dict(id=m['id'], cid=(o[1] if o and o[1] else CID.get(m['id'], 'manual')), type=typ, pub=tt, t=t, link=m.get('permalink'), meta=meta_,
                         age=round((now - t).total_seconds() / 3600, 1), views=x.get('views') or 0, reach=x.get('reach') or 0, likes=x.get('likes') or 0,
                         comments=x.get('comments') or 0, shares=x.get('shares') or 0, saves=x.get('saved') or 0, inter=x.get('total_interactions') or 0,
                         aw=round(aw, 1) if aw else '', ret=ret, fp=(o[23] if o else '')))
    for c, mid, pa, pl, du in STO:
        s = SI.get(mid, {}); t, tt = teh(pa)
        rows.append(dict(id=mid, cid=c, type='story', pub=tt, t=t, link=pl, meta=[''] * 7 + [f'Story of {c}'], age=round((now - t).total_seconds() / 3600, 1),
                         views=s.get('views', 0), reach=s.get('reach', 0), likes='', comments=s.get('replies', 0), shares=s.get('shares', 0), saves='',
                         inter=s.get('total_interactions', 0), aw='', ret='', fp=f"{s.get('follows', 0)}/{s.get('profile_visits', 0)}", nav=s.get('navigation', 0)))
    cut = now - dt.timedelta(days=14)
    for typ in ['reel', 'carousel', 'story']:
        R = [q for q in rows if q['type'] == typ]; W = [q for q in R if q['t'] >= cut] or R
        if not R: continue
        if typ == 'reel':
            mr = med([f(q['ret']) for q in W]); mre = med([q['reach'] for q in W]); mss = med([(q['shares'] + q['saves']) / max(q['reach'], 1) for q in W])
            for q in R: q['score'] = round(50 * (0.35 * min(f(q['ret']) / mr, 3) + 0.25 * min(q['reach'] / mre, 3) + 0.25 * min(((q['shares'] + q['saves']) / max(q['reach'], 1)) / mss, 3) + 0.15), 1)
        elif typ == 'carousel':
            mre = med([q['reach'] for q in W]); mss = med([(q['shares'] + q['saves']) / max(q['reach'], 1) for q in W]); mlc = med([q['likes'] + q['comments'] for q in W])
            for q in R: q['score'] = round(50 * (0.4 * min(q['reach'] / mre, 3) + 0.4 * min(((q['shares'] + q['saves']) / max(q['reach'], 1)) / mss, 3) + 0.2 * min((q['likes'] + q['comments']) / mlc, 3)), 1)
        else:
            for q in R: q['score'] = round(100 * (0.5 * min(q['reach'] / max(fc, 1) * 20, 1) + 0.3 * (1 - min(q.get('nav', 0) / max(q['views'], 1), 1)) + 0.2 * min((f(q['comments']) + q['shares']) / 3, 1)), 1)
    rows.sort(key=lambda q: q['t'], reverse=True)
    out = [P[0][:27]]; sn = set()
    for q in rows:
        sn.add(q['id'])
        out.append([q['id'], q['cid'], q['type'], q['pub'], q['link']] + list(q['meta']) + [q['age'], q['views'], q['reach'], q['likes'], q['comments'], q['shares'],
                   q['saves'], q['inter'], q['aw'], q['ret'], q['fp'], q['score'], per1k(q['shares'], q['reach']), per1k(q['saves'], q['reach']) if q['saves'] != '' else ''])
    for k, o in old.items():
        if k not in sn: out.append(o[:27])
    out = [[('' if c is None else c) for c in r] for r in out]
    _sx("POST", f"{_BASE}/values/'Performance'!A1:AA500:clear", body={})
    _sx("PUT", f"{_BASE}/values/'Performance'!A1", params={"valueInputOption": "RAW"}, body={"values": out})
    nT = (now + dt.timedelta(hours=3, minutes=30)).strftime('%Y-%m-%d %H:%M')
    _sx("PUT", f"{_BASE}/values/'Performance'!AC1", params={"valueInputOption": "RAW"}, body={"values": [["Last refreshed (Tehran)"], [nT + f" ({label})"]]})
    fj = json.loads(read_text(FOLLOWERS_FILE)); fj.setdefault('snapshots', []).append({'at': nT, 'followers': fc, 'after': label})
    write_text(FOLLOWERS_FILE, json.dumps(fj, ensure_ascii=False, indent=1))
    return len(out) - 1, fc, rows


def account_day(day_utc_start):
    """Account insights for one Tehran day; day_utc_start = (y,m,d,20,30,0) of the previous UTC day."""
    since = calendar.timegm(day_utc_start); until = since + 86400
    res, err = run_composio_tool('INSTAGRAM_GET_USER_INSIGHTS', {'ig_user_id': 'me', 'metric': ['reach', 'views', 'accounts_engaged', 'total_interactions', 'profile_views'],
                                 'period': 'day', 'metric_type': 'total_value', 'since': since, 'until': until}, account=ACC)
    if err: return {}
    return {it['name']: (it.get('total_value') or {}).get('value') for it in res['data'].get('data', [])}
