#!/usr/bin/env python3
"""Fetch O*NET summary + task statements for every profession and cache to JSON.

Resumable and rate-limited. Output: src/docs/onet-tasks.json
  { "<code>": {"title":..., "summary":..., "tasks":[...] }, ... }
Group-level codes are categories, not occupations, so only professions are fetched.
"""
import csv, html, json, os, re, sys, time, urllib.request

CACHE = "src/docs/onet-tasks.json"
CSV = "src/docs/us-occupations-onet-soc.csv"
UA = "Mozilla/5.0 (eliminate-jobs static site builder; static site content)"
DELAY = 0.25

def unesc(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def fetch(code):
    url = f"https://www.onetonline.org/link/summary/{code}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    m = re.search(r"<!-- begin content -->\s*<p>(.*?)</p>", data, re.S)
    summary = unesc(m.group(1)) if m else ""
    ti = data.find('id="Tasks"')
    if ti < 0:
        ti = data.find(">Tasks<")
    tasks = []
    if ti >= 0:
        seg = data[ti:ti + 20000]
        bt = seg.find("back to top")
        if bt > 0:
            seg = seg[:bt]
        tasks = [unesc(t) for t in re.findall(r'<div class="order-2 flex-grow-1">(.*?)</div>', seg)]
    return summary, tasks

def main():
    codes = []
    with open(CSV) as f:
        for row in csv.DictReader(f):
            codes.append((row["onet_soc_code"], row["title"]))
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE))
    todo = [c for c, _ in codes if c not in cache or not cache[c].get("summary")]
    print(f"{len(codes)} professions, {len(todo)} to fetch", flush=True)
    for i, code in enumerate(todo):
        try:
            summary, tasks = fetch(code)
            cache[code] = {"summary": summary, "tasks": tasks[:6]}
        except Exception as e:
            print(f"  FAIL {code}: {e}", file=sys.stderr, flush=True)
            cache[code] = {"summary": "", "tasks": []}
        if (i + 1) % 50 == 0:
            json.dump(cache, open(CACHE, "w"))
            print(f"  {i+1}/{len(todo)} saved", flush=True)
        time.sleep(DELAY)
    json.dump(cache, open(CACHE, "w"))
    ok = sum(1 for v in cache.values() if v.get("summary"))
    print(f"DONE. {ok}/{len(codes)} have summaries.", flush=True)

if __name__ == "__main__":
    main()
