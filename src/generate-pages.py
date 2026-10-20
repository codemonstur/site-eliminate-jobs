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
  {"name": "AI agents for planning, scheduling, and resource allocation", "desc": "Autonomous software agents that optimize staffing, calendars, and budgets without human schedulers.", "links": [("AutoGPT", "https://github.com/Significant-Gravitas/AutoGPT"), ("Microsoft Copilot Studio", "https://www.microsoft.com/en-us/microsoft-copilot/microsoft-copilot-studio")]},
  {"name": "Automated performance analytics and workforce dashboards", "desc": "Systems that continuously track KPIs and surface management insights automatically.", "links": [("Tableau", "https://www.tableau.com/"), ("Power BI", "https://powerbi.microsoft.com/")]},
  {"name": "LLM-based decision support and executive briefing", "desc": "Large language models that synthesize reports and recommend actions for leaders.", "links": [("ChatGPT", "https://chat.openai.com/"), ("Claude", "https://claude.ai/")]},
  {"name": "Robotic process automation for approvals and compliance", "desc": "Bots that route, validate, and approve routine administrative workflows.", "links": [("UiPath", "https://www.uipath.com/"), ("Automation Anywhere", "https://www.automationanywhere.com/")]},
  {"name": "Autonomous project-management and OKR tracking tools", "desc": "Software that plans sprints, tracks objectives, and flags risks automatically.", "links": [("Asana", "https://asana.com/"), ("Monday.com", "https://monday.com/")]},
 ],
 "13": [
  {"name": "AI accounting, audit, and reconciliation automation", "desc": "Systems that categorize transactions, detect anomalies, and reconcile books.", "links": [("QuickBooks", "https://quickbooks.intuit.com/"), ("Xero", "https://www.xero.com/")]},
  {"name": "Algorithmic trading and robo-advisory", "desc": "Automated portfolio management and trade execution driven by models.", "links": [("Betterment", "https://www.betterment.com/"), ("Wealthfront", "https://www.wealthfront.com/")]},
  {"name": "Automated financial reporting and forecasting", "desc": "Tools that generate statements and projections from live data.", "links": [("Anaplan", "https://www.anaplan.com/"), ("Workday Adaptive Planning", "https://www.workday.com/")]},
  {"name": "LLM tax preparation and compliance review", "desc": "Language models that prepare returns and check regulatory compliance.", "links": [("TurboTax", "https://turbotax.intuit.com/"), ("H&R Block", "https://www.hrblock.com/")]},
  {"name": "RPA for invoice and expense processing", "desc": "Bots that capture, validate, and post invoices and expenses.", "links": [("Bill.com", "https://www.bill.com/"), ("Expensify", "https://www.expensify.com/")]},
 ],
 "15": [
  {"name": "AI code generation and agentic software engineering", "desc": "Tools that write, refactor, and ship code from natural-language prompts.", "links": [("GitHub Copilot", "https://github.com/features/copilot"), ("Cursor", "https://cursor.sh/")]},
  {"name": "Automated testing and bug triage", "desc": "AI that generates tests, reproduces failures, and prioritizes bugs.", "links": [("Selenium", "https://www.selenium.dev/"), ("Cypress", "https://www.cypress.io/")]},
  {"name": "AutoML and automated model deployment", "desc": "Platforms that train and deploy ML models with minimal human tuning.", "links": [("Google AutoML", "https://cloud.google.com/automl"), ("H2O.ai", "https://h2o.ai/")]},
  {"name": "LLM-assisted data analysis and querying", "desc": "Natural-language interfaces over databases and datasets.", "links": [("ChatGPT Advanced Data Analysis", "https://chat.openai.com/"), ("Claude", "https://claude.ai/")]},
  {"name": "AI-driven DevOps and incident response", "desc": "Automation for deployment, monitoring, and on-call triage.", "links": [("Datadog", "https://www.datadoghq.com/"), ("PagerDuty", "https://www.pagerduty.com/")]},
 ],
 "17": [
  {"name": "Generative design and AI-assisted engineering", "desc": "AI that proposes optimized structures and components from constraints.", "links": [("Autodesk Generative Design", "https://www.autodesk.com/solutions/generative-design"), ("nTopology", "https://ntopology.com/")]},
  {"name": "Building information modeling (BIM) automation", "desc": "Automated generation and coordination of building models.", "links": [("Autodesk Revit", "https://www.autodesk.com/products/revit/overview"), ("ArchiCAD", "https://graphisoft.com/solutions/archicad")]},
  {"name": "Autonomous surveying with drones and LiDAR", "desc": "Unmanned aerial and laser scanning of sites and terrain.", "links": [("DJI", "https://www.dji.com/"), ("Leica Geosystems", "https://leica-geosystems.com/")]},
  {"name": "AI structural optimization and simulation", "desc": "Machine learning to test and optimize designs under load.", "links": [("Ansys", "https://www.ansys.com/"), ("SimScale", "https://www.simscale.com/")]},
  {"name": "Robotic construction planning and scheduling", "desc": "Automated sequencing and resource planning for builds.", "links": [("Procore", "https://www.procore.com/"), ("PlanGrid", "https://www.plangrid.com/")]},
 ],
 "19": [
  {"name": "AI literature review and hypothesis generation", "desc": "Models that scan research and propose new questions.", "links": [("Elicit", "https://elicit.com/"), ("Semantic Scholar", "https://www.semanticscholar.org/")]},
  {"name": "Robotic laboratories and automated experiments", "desc": "Self-driving labs that run experiments without human hands.", "links": [("Emerald Cloud Lab", "https://www.emeraldcloudlab.com/"), ("Strateos", "https://strateos.com/")]},
  {"name": "Computational modeling and simulation", "desc": "In-silico experiments replacing physical trials.", "links": [("MATLAB", "https://www.mathworks.com/"), ("COMSOL", "https://www.comsol.com/")]},
  {"name": "AI-driven data collection and remote sensing", "desc": "Automated gathering of field and satellite data.", "links": [("Planet Labs", "https://www.planet.com/"), ("Maxar", "https://www.maxar.com/")]},
  {"name": "Automated statistical analysis and reporting", "desc": "Tools that analyze datasets and generate reports.", "links": [("R", "https://www.r-project.org/"), ("Python", "https://www.python.org/")]},
 ],
 "21": [
  {"name": "AI triage chatbots for counseling and intake", "desc": "Conversational agents that assess needs and route cases.", "links": [("Woebot", "https://woebothealth.com/"), ("Wysa", "https://www.wysa.com/")]},
  {"name": "Automated case management and eligibility checks", "desc": "Systems that process applications and verify eligibility.", "links": [("Salesforce Nonprofit", "https://www.salesforce.org/"), ("Casebook", "https://www.casebook.net/")]},
  {"name": "Telehealth triage and remote support", "desc": "Remote assessment and care coordination platforms.", "links": [("Teladoc", "https://www.teladoc.com/"), ("Amwell", "https://business.amwell.com/")]},
  {"name": "AI-assisted benefit and service navigation", "desc": "Guides that match people to programs and services.", "links": [("Benefits Data Trust", "https://bdtrust.org/"), ("mRelief", "https://www.mrelief.com/")]},
 ],
 "23": [
  {"name": "LLM contract review and legal research", "desc": "Models that read contracts and surface risks and precedents.", "links": [("Harvey", "https://www.harvey.ai/"), ("LexisNexis", "https://www.lexisnexis.com/")]},
  {"name": "Automated discovery and document analysis", "desc": "AI that sorts and analyzes large document sets.", "links": [("Relativity", "https://www.relativity.com/"), ("DISCO", "https://www.csdisco.com/")]},
  {"name": "AI drafting of briefs, wills, and filings", "desc": "Generative tools that draft legal documents.", "links": [("LegalZoom", "https://www.legalzoom.com/"), ("DoNotPay", "https://donotpay.com/")]},
  {"name": "Compliance automation and regulatory monitoring", "desc": "Systems that track regulatory changes and compliance status.", "links": [("Thomson Reuters", "https://www.thomsonreuters.com/"), ("ComplyAdvantage", "https://complyadvantage.com/")]},
  {"name": "Online dispute resolution platforms", "desc": "Digital platforms that resolve conflicts without courts.", "links": [("Modria", "https://www.modria.com/"), ("Tyler Technologies", "https://www.tylertech.com/")]},
 ],
 "25": [
  {"name": "AI tutors and adaptive learning platforms", "desc": "Personalized AI instruction that adapts to each learner.", "links": [("Khanmigo", "https://www.khanacademy.org/khan-labs"), ("Duolingo", "https://www.duolingo.com/")]},
  {"name": "Automated grading and feedback", "desc": "AI that scores assignments and gives feedback.", "links": [("Gradescope", "https://www.gradescope.com/"), ("Turnitin", "https://www.turnitin.com/")]},
  {"name": "LLM lesson planning and content generation", "desc": "Models that draft curricula and teaching materials.", "links": [("MagicSchool", "https://www.magicschool.ai/"), ("Eduaide", "https://www.eduaide.ai/")]},
  {"name": "Virtual classrooms and AI teaching assistants", "desc": "Online platforms with AI support for instructors.", "links": [("Zoom", "https://zoom.us/"), ("Google Classroom", "https://classroom.google.com/")]},
  {"name": "Personalized curriculum optimization", "desc": "Adaptive systems that tailor learning paths.", "links": [("Knewton", "https://www.knewton.com/"), ("Carnegie Learning", "https://www.carnegielearning.com/")]},
 ],
 "27": [
  {"name": "Generative AI for image, video, and music", "desc": "Models that create media from text prompts.", "links": [("Midjourney", "https://www.midjourney.com/"), ("Runway", "https://runwayml.com/")]},
  {"name": "AI editing, dubbing, and post-production", "desc": "Automated editing, translation, and voice cloning.", "links": [("Descript", "https://www.descript.com/"), ("ElevenLabs", "https://elevenlabs.io/")]},
  {"name": "Automated content and copy generation", "desc": "AI that writes articles, ads, and marketing copy.", "links": [("Jasper", "https://www.jasper.ai/"), ("Copy.ai", "https://www.copy.ai/")]},
  {"name": "Virtual influencers and synthetic media", "desc": "AI-generated personas and digital avatars.", "links": [("Synthesia", "https://www.synthesia.io/"), ("HeyGen", "https://www.heygen.com/")]},
  {"name": "AI game and level design", "desc": "Procedural and AI-assisted game content creation.", "links": [("Unity", "https://unity.com/"), ("Unreal Engine", "https://www.unrealengine.com/")]},
 ],
 "29": [
  {"name": "AI diagnosis and clinical decision support", "desc": "Models that assist or automate diagnosis.", "links": [("Watson Health", "https://www.ibm.com/watson-health"), ("Ada Health", "https://ada.com/")]},
  {"name": "Surgical and diagnostic robotics", "desc": "Robots that perform or assist in procedures.", "links": [("da Vinci", "https://www.intuitive.com/"), ("Medtronic", "https://www.medtronic.com/")]},
  {"name": "AI radiology and pathology screening", "desc": "Image analysis for detecting disease.", "links": [("Aidoc", "https://www.aidoc.com/"), ("Zebra Medical", "https://www.zebra-med.com/")]},
  {"name": "Ambient AI scribes for medical documentation", "desc": "AI that transcribes clinical encounters.", "links": [("Nuance DAX", "https://www.nuance.com/healthcare/ambient-clinical-intelligence.html"), ("Abridge", "https://www.abridge.com/")]},
  {"name": "AI drug discovery and trial optimization", "desc": "Models that accelerate molecule and trial design.", "links": [("Insilico Medicine", "https://insilico.com/"), ("Recursion", "https://www.recursion.com/")]},
 ],
 "31": [
  {"name": "Care and service robots", "desc": "Robots assisting with patient care tasks.", "links": [("SoftBank Robotics", "https://www.softbankrobotics.com/"), ("Diligent Robotics", "https://www.diligentrobots.com/")]},
  {"name": "Automated patient monitoring and alerts", "desc": "Continuous vitals monitoring with AI alerts.", "links": [("Philips", "https://www.philips.com/"), ("Masimo", "https://www.masimo.com/")]},
  {"name": "Robotic medication dispensing", "desc": "Automated pharmacy and dispensing systems.", "links": [("Omnicell", "https://www.omnicell.com/"), ("BD", "https://www.bd.com/")]},
  {"name": "AI scheduling and task routing", "desc": "Automated staff scheduling and task assignment.", "links": [("QGenda", "https://www.qgenda.com/"), ("TCP", "https://www.tcpsoftware.com/")]},
  {"name": "Remote patient monitoring platforms", "desc": "Home-based monitoring and telehealth.", "links": [("TytoCare", "https://www.tytocare.com/"), ("Biofourmis", "https://www.biofourmis.com/")]},
 ],
 "33": [
  {"name": "AI video analytics and surveillance", "desc": "Computer vision for threat detection.", "links": [("Verkada", "https://www.verkada.com/"), ("Milestone", "https://www.milestone-systems.com/")]},
  {"name": "Autonomous security robots and drones", "desc": "Patrol robots and drones for security.", "links": [("Knightscope", "https://www.knightscope.com/"), ("Cobalt Robotics", "https://www.cobaltrobotics.com/")]},
  {"name": "Predictive policing and risk scoring", "desc": "Data-driven crime prediction and risk assessment.", "links": [("PredPol", "https://www.predpol.com/"), ("Palantir", "https://www.palantir.com/")]},
  {"name": "Automated access control and screening", "desc": "Biometric and automated entry systems.", "links": [("Clear", "https://www.clearme.com/"), ("IDEMIA", "https://www.idemia.com/")]},
 ],
 "35": [
  {"name": "Kitchen and food-preparation robots", "desc": "Robotic cooking and food assembly.", "links": [("Moley Robotics", "https://www.moley.com/"), ("Creator", "https://www.creator.rest/")]},
  {"name": "Self-service kiosks and automated ordering", "desc": "Touchscreen ordering and payment systems.", "links": [("Toast", "https://pos.toasttab.com/"), ("Square", "https://squareup.com/")]},
  {"name": "Delivery robots and drones", "desc": "Autonomous last-mile delivery.", "links": [("Starship", "https://www.starship.xyz/"), ("Zipline", "https://www.flyzipline.com/")]},
  {"name": "AI inventory and demand forecasting", "desc": "Predictive stock and demand management.", "links": [("Blue Yonder", "https://blueyonder.com/"), ("RELEX", "https://www.relexsolutions.com/")]},
  {"name": "Robotic baristas and beverage systems", "desc": "Automated coffee and drink preparation.", "links": [("Cafe X", "https://www.cafexapp.com/"), ("Briggo", "https://www.briggo.com/")]},
 ],
 "37": [
  {"name": "Autonomous cleaning and floor-care robots", "desc": "Robotic vacuums and scrubbers for facilities.", "links": [("iRobot", "https://www.irobot.com/"), ("Tennant", "https://www.tennantco.com/")]},
  {"name": "Robotic lawn mowers and grounds equipment", "desc": "Autonomous mowing and landscaping.", "links": [("Husqvarna", "https://www.husqvarna.com/"), ("John Deere", "https://www.deere.com/")]},
  {"name": "Automated window and facade cleaning", "desc": "Robotic window and building cleaning.", "links": [("Skyline Robotics", "https://www.skylinerobotics.com/"), ("Serbot", "https://www.serbot.ch/")]},
  {"name": "AI scheduling and route optimization", "desc": "Automated task scheduling and routing.", "links": [("ServiceTitan", "https://www.servicetitan.com/"), ("Jobber", "https://getjobber.com/")]},
 ],
 "39": [
  {"name": "Care and companion robots", "desc": "Robots for elderly and personal care.", "links": [("Intuition Robotics", "https://www.intuitionrobotics.com/"), ("PARO", "https://www.parorobots.com/")]},
  {"name": "AI personal assistants and concierges", "desc": "Virtual assistants for personal services.", "links": [("Alexa", "https://www.alexa.com/"), ("Google Assistant", "https://assistant.google.com/")]},
  {"name": "Automated salon and grooming devices", "desc": "Robotic and automated grooming tools.", "links": [("Dyson", "https://www.dyson.com/"), ("Philips", "https://www.philips.com/")]},
  {"name": "Wearable health and wellness monitoring", "desc": "Devices tracking health and fitness.", "links": [("Apple Watch", "https://www.apple.com/apple-watch/"), ("Fitbit", "https://www.fitbit.com/")]},
 ],
 "41": [
  {"name": "AI sales agents and chatbots", "desc": "Conversational AI for sales and support.", "links": [("Drift", "https://www.drift.com/"), ("Intercom", "https://www.intercom.com/")]},
  {"name": "Automated pricing and promotion optimization", "desc": "Dynamic pricing and promotion engines.", "links": [("Prisync", "https://prisync.com/"), ("Competera", "https://competera.net/")]},
  {"name": "Recommendation and personalization engines", "desc": "Systems that personalize product suggestions.", "links": [("Amazon", "https://www.amazon.com/"), ("Netflix", "https://www.netflix.com/")]},
  {"name": "Virtual shopping assistants", "desc": "AI helpers for online shopping.", "links": [("Shopify", "https://www.shopify.com/"), ("Algolia", "https://www.algolia.com/")]},
  {"name": "AI lead scoring and CRM automation", "desc": "Automated lead qualification and CRM updates.", "links": [("Salesforce", "https://www.salesforce.com/"), ("HubSpot", "https://www.hubspot.com/")]},
 ],
 "43": [
  {"name": "Robotic process automation (RPA)", "desc": "Bots that automate repetitive office tasks.", "links": [("UiPath", "https://www.uipath.com/"), ("Blue Prism", "https://www.blueprism.com/")]},
  {"name": "LLM document processing and data entry", "desc": "AI that extracts and enters document data.", "links": [("ABBYY", "https://www.abbyy.com/"), ("Hyperscience", "https://www.hyperscience.com/")]},
  {"name": "AI email drafting and triage", "desc": "AI that writes and sorts email.", "links": [("Superhuman", "https://superhuman.com/"), ("Gmail", "https://mail.google.com/")]},
  {"name": "Automated scheduling and calendar management", "desc": "AI scheduling assistants.", "links": [("Calendly", "https://calendly.com/"), ("Motion", "https://www.usemotion.com/")]},
  {"name": "Voice assistants and transcription", "desc": "Speech-to-text and voice-driven tools.", "links": [("Otter.ai", "https://otter.ai/"), ("Dragon", "https://www.nuance.com/dragon.html")]},
 ],
 "45": [
  {"name": "Precision agriculture and AI crop management", "desc": "Data-driven farming and crop optimization.", "links": [("Climate FieldView", "https://climate.com/"), ("Trimble", "https://www.trimble.com/")]},
  {"name": "Autonomous tractors and harvesters", "desc": "Self-driving farm machinery.", "links": [("John Deere", "https://www.deere.com/"), ("Case IH", "https://www.caseih.com/")]},
  {"name": "Harvesting and picking robots", "desc": "Robots that pick crops.", "links": [("Abundant Robotics", "https://www.abundantrobotics.com/"), ("FFRobotics", "https://www.ffrobotics.com/")]},
  {"name": "Drone monitoring and spraying", "desc": "Aerial crop monitoring and spraying.", "links": [("DJI Agriculture", "https://ag.dji.com/"), ("PrecisionHawk", "https://www.precisionhawk.com/")]},
  {"name": "Automated aquaculture and fishery systems", "desc": "Automated fish farming and monitoring.", "links": [("Cermaq", "https://www.cermaq.com/"), ("InnovaSea", "https://www.innovasea.com/")]},
 ],
 "47": [
  {"name": "Autonomous construction equipment", "desc": "Self-driving bulldozers, excavators, etc.", "links": [("Caterpillar", "https://www.caterpillar.com/"), ("Komatsu", "https://www.komatsu.com/")]},
  {"name": "Robotic bricklaying and 3D-printed buildings", "desc": "Robots that lay bricks and print structures.", "links": [("Hadrian X", "https://www.fbr.com.au/"), ("ICON", "https://www.iconbuild.com/")]},
  {"name": "AI site planning and scheduling", "desc": "Automated construction planning and scheduling.", "links": [("Procore", "https://www.procore.com/"), ("Autodesk Construction Cloud", "https://construction.autodesk.com/")]},
  {"name": "Automated surveying and inspection drones", "desc": "Drones for site survey and inspection.", "links": [("Skycatch", "https://www.skycatch.com/"), ("DroneDeploy", "https://www.dronedeploy.com/")]},
  {"name": "Robotic excavation and tunneling", "desc": "Automated digging and tunneling machines.", "links": [("The Boring Company", "https://www.boringcompany.com/"), ("Herrenknecht", "https://www.herrenknecht.com/")]},
 ],
 "49": [
  {"name": "Predictive maintenance and AI diagnostics", "desc": "AI that predicts equipment failures.", "links": [("Uptake", "https://www.uptake.com/"), ("Augury", "https://www.augury.com/")]},
  {"name": "AR-guided repair and remote assistance", "desc": "Augmented reality for repair guidance.", "links": [("Microsoft HoloLens", "https://www.microsoft.com/hololens"), ("TeamViewer", "https://www.teamviewer.com/")]},
  {"name": "Autonomous inspection drones", "desc": "Drones for equipment inspection.", "links": [("Percepto", "https://percepto.co/"), ("Skydio", "https://www.skydio.com/")]},
  {"name": "Self-diagnosing and self-repairing systems", "desc": "Systems that detect and fix their own faults.", "links": [("Siemens", "https://www.siemens.com/"), ("GE", "https://www.ge.com/")]},
  {"name": "Robotic maintenance platforms", "desc": "Robots for maintenance tasks.", "links": [("Boston Dynamics", "https://www.bostondynamics.com/"), ("ABB", "https://www.abb.com/")]},
 ],
 "51": [
  {"name": "Industrial and collaborative robots", "desc": "Robots for manufacturing and assembly.", "links": [("FANUC", "https://www.fanuc.com/"), ("Universal Robots", "https://www.universal-robots.com/")]},
  {"name": "AI visual quality control", "desc": "Computer vision for defect detection.", "links": [("Cognex", "https://www.cognex.com/"), ("Keyence", "https://www.keyence.com/")]},
  {"name": "Automated assembly and packaging", "desc": "Automated assembly lines and packaging.", "links": [("Bosch", "https://www.bosch.com/"), ("Rockwell Automation", "https://www.rockwellautomation.com/")]},
  {"name": "Additive manufacturing (3D printing)", "desc": "3D printing for production.", "links": [("Stratasys", "https://www.stratasys.com/"), ("3D Systems", "https://www.3dsystems.com/")]},
  {"name": "Autonomous warehouse and logistics systems", "desc": "Automated warehouses and logistics.", "links": [("Amazon Robotics", "https://www.amazonrobotics.com/"), ("Locus Robotics", "https://locusrobotics.com/")]},
 ],
 "53": [
  {"name": "Autonomous vehicles and self-driving trucks", "desc": "Self-driving cars and trucks.", "links": [("Waymo", "https://waymo.com/"), ("Tesla", "https://www.tesla.com/")]},
  {"name": "Delivery drones and sidewalk robots", "desc": "Autonomous delivery systems.", "links": [("Starship", "https://www.starship.xyz/"), ("Zipline", "https://www.flyzipline.com/")]},
  {"name": "Automated ports, cranes, and warehouses", "desc": "Automated port and warehouse operations.", "links": [("Konecranes", "https://www.konecranes.com/"), ("Liebherr", "https://www.liebherr.com/")]},
  {"name": "AI routing and fleet optimization", "desc": "AI for route and fleet management.", "links": [("Samsara", "https://www.samsara.com/"), ("Geotab", "https://www.geotab.com/")]},
  {"name": "Autonomous forklifts and material handlers", "desc": "Self-driving forklifts and handlers.", "links": [("Seegrid", "https://seegrid.com/"), ("OTTO Motors", "https://ottomotors.com/")]},
 ],
 "55": [
  {"name": "Autonomous systems and drone swarms", "desc": "Autonomous military systems and drones.", "links": [("Anduril", "https://www.anduril.com/"), ("Shield AI", "https://shield.ai/")]},
  {"name": "AI command-and-control and decision support", "desc": "AI for military command and decisions.", "links": [("Palantir", "https://www.palantir.com/"), ("Scale AI", "https://scale.com/")]},
  {"name": "Robotic logistics and resupply", "desc": "Robotic supply and logistics.", "links": [("Boston Dynamics", "https://www.bostondynamics.com/"), ("Ghost Robotics", "https://www.ghostrobotics.io/")]},
  {"name": "Unmanned vehicles and platforms", "desc": "Unmanned military vehicles.", "links": [("General Atomics", "https://www.ga.com/"), ("Northrop Grumman", "https://www.northropgrumman.com/")]},
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
    # sort groups alphabetically by their name (without the leading code)
    groups = OrderedDict(sorted(groups.items(), key=lambda kv: kv[1]["full"].split(" ", 1)[-1]))

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
        display_name = full.split(" ", 1)[-1] if " " in full else full
        check_safe(display_name, f"major group name ({gcode})")

        tech_items = TECHNOLOGIES.get(gcode, [])
        tech_lines = []
        for item in tech_items:
            name = item["name"]
            desc = item["desc"]
            links = item.get("links", [])
            if links:
                link_str = " Examples: " + ", ".join("[" + lbl + "](" + url + ")" for lbl, url in links) + "."
            else:
                link_str = ""
            tech_lines.append("- **" + name + "** \u2014 " + desc + link_str)
        tech_block = "\n".join(tech_lines)

        page = f"""---
title: {yaml_str(display_name)}
group_code: {yaml_str(gcode)}
---

Major group `{gcode}` of the U.S. O\\*NET-SOC register, containing
**{len(group['members'])}** of the {total_str} professions listed on this site.

## Ways these jobs could be eliminated

{tech_block}

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
