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
    # Employment prevalence (BLS, via O*NET).
    em = re.search(r"Employment\s*<small[^>]*>\((\d{4})\)</small>\s*</dt>\s*<dd[^>]*>\s*([\d,]+)\s*employees", data, re.S)
    employment_year = em.group(1) if em else ""
    employment = int(em.group(2).replace(",", "")) if em else None

    gm = re.search(r"Projected growth\s*<small[^>]*>\((\d{4}-\d{4})\)</small>\s*</dt>\s*<dd[^>]*>(.*?)</dd>", data, re.S)
    projection_period = gm.group(1) if gm else ""
    projected_growth = unesc(gm.group(2)) if gm else ""

    om = re.search(r"Projected job openings\s*<small[^>]*>\((\d{4}-\d{4})\)</small>\s*</dt>\s*<dd[^>]*>\s*([\d,]+)", data, re.S)
    projected_openings = int(om.group(2).replace(",", "")) if om else None

    return summary, tasks, employment, employment_year, projected_growth, projection_period, projected_openings

def main():
    codes = []
    with open(CSV) as f:
        for row in csv.DictReader(f):
            codes.append((row["onet_soc_code"], row["title"]))
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE))
    todo = [c for c, _ in codes if c not in cache or cache[c].get("employment") is None]
    print(f"{len(codes)} professions, {len(todo)} to fetch", flush=True)
    for i, code in enumerate(todo):
        try:
            summary, tasks, employment, employment_year, projected_growth, projection_period, projected_openings = fetch(code)
            cache[code] = {
                "summary": summary,
                "tasks": tasks[:6],
                "employment": employment,
                "employment_year": employment_year,
                "projected_growth": projected_growth,
                "projection_period": projection_period,
                "projected_openings": projected_openings,
            }
        except Exception as e:
            print(f"  FAIL {code}: {e}", file=sys.stderr, flush=True)
            cache[code] = {"summary": "", "tasks": [], "employment": None, "employment_year": "", "projected_growth": "", "projection_period": "", "projected_openings": None}
        if (i + 1) % 50 == 0:
            json.dump(cache, open(CACHE, "w"))
            print(f"  {i+1}/{len(todo)} saved", flush=True)
        time.sleep(DELAY)
    json.dump(cache, open(CACHE, "w"))
    ok = sum(1 for v in cache.values() if v.get("employment") is not None)
    print(f"DONE. {ok}/{len(codes)} have summaries.", flush=True)

if __name__ == "__main__":
    main()
