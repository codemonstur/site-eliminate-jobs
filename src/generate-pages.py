#!/usr/bin/env python3
"""Generate one markdown page per profession and per major group.

Reads  : docs/us-occupations-onet-soc.csv  (source of truth)
Writes : arguments/<onet-soc-code>.md       (one per profession)
         arguments/<major-group-code>.md    (major group, page 1)
         arguments/<major-group-code>-pN.md (major group, pages 2+)

`make build` compiles these with pandoc (template: templates/argument.html)
into docs/arguments/, which is where the table links in src/static/app.js point.
Group pages embed a #group mount point that static/group.js fills client-side
with search + pagination identical to the index page (data: professions.js).
"""
import csv
import json
import pathlib
from collections import OrderedDict

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "src" / "docs" / "us-occupations-onet-soc.csv"
OUT_DIR = ROOT / "src" / "arguments"

JOB_ZONE_NOTES = {
    "1-2": "little or moderate preparation",
    "3": "medium preparation",
    "4": "substantial preparation",
    "5": "extensive preparation",
    "n/a": "no job zone assigned",
}

# Potential ways and technologies in development that could reduce or eliminate
# the jobs in each major group. Informational, not a prediction.
TECHNOLOGIES = {
 "11": [
  "AI agents for planning, scheduling, and resource allocation",
  "Automated performance analytics and workforce dashboards",
  "LLM-based decision support and executive briefing",
  "Robotic process automation for approvals and compliance",
  "Autonomous project-management and OKR tracking tools",
 ],
 "13": [
  "AI accounting, audit, and reconciliation automation",
  "Algorithmic trading and robo-advisory",
  "Automated financial reporting and forecasting",
  "LLM tax preparation and compliance review",
  "RPA for invoice and expense processing",
 ],
 "15": [
  "AI code generation and agentic software engineering",
  "Automated testing and bug triage",
  "AutoML and automated model deployment",
  "LLM-assisted data analysis and querying",
  "AI-driven DevOps and incident response",
 ],
 "17": [
  "Generative design and AI-assisted engineering",
  "Building information modeling (BIM) automation",
  "Autonomous surveying with drones and LiDAR",
  "AI structural optimization and simulation",
  "Robotic construction planning and scheduling",
 ],
 "19": [
  "AI literature review and hypothesis generation",
  "Robotic laboratories and automated experiments",
  "Computational modeling and simulation",
  "AI-driven data collection and remote sensing",
  "Automated statistical analysis and reporting",
 ],
 "21": [
  "AI triage chatbots for counseling and intake",
  "Automated case management and eligibility checks",
  "Telehealth triage and remote support",
  "AI-assisted benefit and service navigation",
 ],
 "23": [
  "LLM contract review and legal research",
  "Automated discovery and document analysis",
  "AI drafting of briefs, wills, and filings",
  "Compliance automation and regulatory monitoring",
  "Online dispute resolution platforms",
 ],
 "25": [
  "AI tutors and adaptive learning platforms",
  "Automated grading and feedback",
  "LLM lesson planning and content generation",
  "Virtual classrooms and AI teaching assistants",
  "Personalized curriculum optimization",
 ],
 "27": [
  "Generative AI for image, video, and music",
  "AI editing, dubbing, and post-production",
  "Automated content and copy generation",
  "Virtual influencers and synthetic media",
  "AI game and level design",
 ],
 "29": [
  "AI diagnosis and clinical decision support",
  "Surgical and diagnostic robotics",
  "AI radiology and pathology screening",
  "Ambient AI scribes for medical documentation",
  "AI drug discovery and trial optimization",
 ],
 "31": [
  "Care and service robots",
  "Automated patient monitoring and alerts",
  "Robotic medication dispensing",
  "AI scheduling and task routing",
  "Remote patient monitoring platforms",
 ],
 "33": [
  "AI video analytics and surveillance",
  "Autonomous security robots and drones",
  "Predictive policing and risk scoring",
  "Automated access control and screening",
 ],
 "35": [
  "Kitchen and food-preparation robots",
  "Self-service kiosks and automated ordering",
  "Delivery robots and drones",
  "AI inventory and demand forecasting",
  "Robotic baristas and beverage systems",
 ],
 "37": [
  "Autonomous cleaning and floor-care robots",
  "Robotic lawn mowers and grounds equipment",
  "Automated window and facade cleaning",
  "AI scheduling and route optimization",
 ],
 "39": [
  "Care and companion robots",
  "AI personal assistants and concierges",
  "Automated salon and grooming devices",
  "Wearable health and wellness monitoring",
 ],
 "41": [
  "AI sales agents and chatbots",
  "Automated pricing and promotion optimization",
  "Recommendation and personalization engines",
  "Virtual shopping assistants",
  "AI lead scoring and CRM automation",
 ],
 "43": [
  "Robotic process automation (RPA)",
  "LLM document processing and data entry",
  "AI email drafting and triage",
  "Automated scheduling and calendar management",
  "Voice assistants and transcription",
 ],
 "45": [
  "Precision agriculture and AI crop management",
  "Autonomous tractors and harvesters",
  "Harvesting and picking robots",
  "Drone monitoring and spraying",
  "Automated aquaculture and fishery systems",
 ],
 "47": [
  "Autonomous construction equipment",
  "Robotic bricklaying and 3D-printed buildings",
  "AI site planning and scheduling",
  "Automated surveying and inspection drones",
  "Robotic excavation and tunneling",
 ],
 "49": [
  "Predictive maintenance and AI diagnostics",
  "AR-guided repair and remote assistance",
  "Autonomous inspection drones",
  "Self-diagnosing and self-repairing systems",
  "Robotic maintenance platforms",
 ],
 "51": [
  "Industrial and collaborative robots",
  "AI visual quality control",
  "Automated assembly and packaging",
  "Additive manufacturing (3D printing)",
  "Autonomous warehouse and logistics systems",
 ],
 "53": [
  "Autonomous vehicles and self-driving trucks",
  "Delivery drones and sidewalk robots",
  "Automated ports, cranes, and warehouses",
  "AI routing and fleet optimization",
  "Autonomous forklifts and material handlers",
 ],
 "55": [
  "Autonomous systems and drone swarms",
  "AI command-and-control and decision support",
  "Robotic logistics and resupply",
  "Unmanned vehicles and platforms",
 ],
}

# Characters that would break markdown (table cells, links, emphasis).
UNSAFE = set("|[]`*_<>")


def yaml_str(text: str) -> str:
    """Quote a value as a JSON double-quoted scalar (valid YAML)."""
    return json.dumps(text, ensure_ascii=False)


def check_safe(text: str, where: str) -> None:
    bad = sorted(set(text) & UNSAFE)
    if bad:
        raise SystemExit(f"Unsafe characters {bad!r} in {where}: {text!r}")


def group_section(gcode: str) -> str:
    """Raw-HTML mount point that group.js turns into the paginated list."""
    return f"""<section id="group" data-group="{gcode}">
<div class="toolbar">
  <input id="search" type="search" placeholder="Search within this group &hellip;"
         autocomplete="off" spellcheck="false" aria-label="Search professions in this group">
  <label class="page-size-label">Per page
    <select id="page-size" aria-label="Professions per page">
      <option value="10" selected>10</option>
      <option value="25">25</option>
      <option value="50">50</option>
      <option value="100">100</option>
      <option value="250">250</option>
    </select>
  </label>
</div>

<p id="status" class="status" role="status" aria-live="polite"></p>

<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Profession</th>
        <th>O*NET-SOC code</th>
        <th class="num">Job zone</th>
      </tr>
    </thead>
    <tbody id="rows"></tbody>
  </table>
</div>

<nav class="pagination" id="pagination" aria-label="Pagination"></nav>
</section>"""


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    groups: OrderedDict[str, dict] = OrderedDict()
    for row in rows:
        code, _, name = row["major_group"].partition(" ")
        group = groups.setdefault(
            code, {"code": code, "name": name, "full": row["major_group"], "members": []}
        )
        group["members"].append(row)

    # Sort each group's members alphabetically for the client-side renderer.
    for group in groups.values():
        group["members"].sort(key=lambda r: r["title"].casefold())

    total = len(rows)
    total_str = f"{total:,}"

    OUT_DIR.mkdir(exist_ok=True)
    for stale in OUT_DIR.glob("*.md"):
        stale.unlink()

    for row in rows:
        code = row["onet_soc_code"]
        title = row["title"]
        gcode, _, _ = row["major_group"].partition(" ")
        zone = row["job_zone"]
        zone_note = JOB_ZONE_NOTES.get(zone, "job zone unknown")
        data = "Available" if row["has_onet_data"] == "yes" else "Not available"
        group_link = f"{gcode}.html"

        check_safe(title, f"profession title ({code})")
        check_safe(row["major_group"], f"major group ({code})")

        page = f"""---
title: {yaml_str(title)}
---

A profession in the U.S. Department of Labor's O\\*NET-SOC register — one of
**{total_str}** occupations listed on this site.

| Field | Value |
|---|---|
| O\\*NET-SOC code | `{code}` |
| Major group | [{row['major_group']}]({group_link}) |
| Job zone | {zone} — {zone_note} |
| O\\*NET dataset | {data} |

## In the register

- [Full profile on O\\*NET OnLine](https://www.onetonline.org/link/summary/{code})
- [All professions in {row['major_group']}]({group_link})
- [Browse all professions](../professions.html)
"""
        (OUT_DIR / f"{code}.md").write_text(page, encoding="utf-8")

    for gcode, group in groups.items():
        full = group["full"]
        check_safe(full, f"major group name ({gcode})")

        page = f"""---
title: {yaml_str(full)}
group_code: {yaml_str(gcode)}
---

Major group `{gcode}` of the U.S. O\\*NET-SOC register, containing
**{len(group['members'])}** of the {total_str} professions listed on this site.

## Ways these jobs could be eliminated

{chr(10).join("- " + t for t in TECHNOLOGIES.get(gcode, []))}

```{{=html}}
{group_section(gcode)}
```

## See also

- [Browse all professions](../professions.html)
- [Major group on O\\*NET OnLine](https://www.onetonline.org/find/major?b={gcode})
"""
        (OUT_DIR / f"{gcode}.md").write_text(page, encoding="utf-8")

    print(
        f"Wrote {total} profession pages and {len(groups)} major group pages to {OUT_DIR}"
    )


if __name__ == "__main__":
    main()
