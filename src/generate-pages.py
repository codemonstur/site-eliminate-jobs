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
  {"name": "AI agents for planning, scheduling, and resource allocation", "paragraphs": ["Autonomous AI agents can take over the coordination tasks that managers perform daily: assigning work, balancing loads, resolving conflicts, and adapting plans as conditions change. Instead of a human manager orchestrating a team, an agent can continuously re-optimize schedules and resource allocation across an organization.", "These systems combine large language models with planning algorithms and access to calendars, HR systems, and budgets. While early versions still require human oversight, the trajectory is toward agents that run operations end-to-end, reducing the need for middle management."], "examples": [("AutoGPT", "https://github.com/Significant-Gravitas/AutoGPT"), ("Microsoft Copilot Studio", "https://www.microsoft.com/en-us/microsoft-copilot/microsoft-copilot-studio"), ("Wikipedia: Intelligent agent", "https://en.wikipedia.org/wiki/Intelligent_agent")]},
  {"name": "Automated performance analytics and workforce dashboards", "paragraphs": ["Performance management is increasingly driven by data rather than human judgment. Automated analytics platforms continuously track KPIs, productivity metrics, and team health, surfacing insights and alerts without a manager compiling reports.", "Dashboards replace periodic reviews with real-time visibility, and AI can recommend interventions such as reallocating staff or adjusting targets. Over time this reduces the need for managers whose primary role is monitoring and reporting."], "examples": [("Tableau", "https://www.tableau.com/"), ("Power BI", "https://powerbi.microsoft.com/"), ("Wikipedia: Business intelligence", "https://en.wikipedia.org/wiki/Business_intelligence")]},
  {"name": "LLM-based decision support and executive briefing", "paragraphs": ["Large language models can synthesize large volumes of information into concise briefings and recommendations for decision-makers. They can draft memos, summarize meetings, and highlight risks, compressing the analytical work that supports executive choices.", "As these systems improve, executives can query organizational data in natural language and receive reasoned recommendations. This erodes the role of analysts and staff who traditionally prepare decision materials."], "examples": [("ChatGPT", "https://chat.openai.com/"), ("Claude", "https://claude.ai/"), ("Wikipedia: Large language model", "https://en.wikipedia.org/wiki/Large_language_model")]},
  {"name": "Robotic process automation for approvals and compliance", "paragraphs": ["RPA bots can handle approval workflows, policy checks, and compliance verification that managers and administrators perform. They validate inputs against rules, route documents, and flag exceptions without human intervention.", "Combined with AI, RPA can interpret unstructured documents and make conditional decisions. This steadily removes the need for humans to oversee routine approvals and audits."], "examples": [("UiPath", "https://www.uipath.com/"), ("Automation Anywhere", "https://www.automationanywhere.com/"), ("Wikipedia: Robotic process automation", "https://en.wikipedia.org/wiki/Robotic_process_automation")]},
  {"name": "Autonomous project-management and OKR tracking tools", "paragraphs": ["Project management software is becoming autonomous: it can plan sprints, assign tasks, track objectives, and flag risks without a human project manager. AI continuously rebalances workloads and timelines as conditions change.", "These tools integrate with code repositories, calendars, and communication platforms to keep projects on track. The coordination and status-reporting functions of management become automated."], "examples": [("Asana", "https://asana.com/"), ("Monday.com", "https://monday.com/"), ("Wikipedia: Project management", "https://en.wikipedia.org/wiki/Project_management")]},
 ],
 "13": [
  {"name": "AI accounting, audit, and reconciliation automation", "paragraphs": ["AI systems can categorize transactions, detect anomalies, and reconcile accounts automatically, performing the core work of bookkeepers and auditors. They learn from historical data and improve accuracy over time.", "Continuous auditing by AI replaces periodic manual reviews. As trust in automated verification grows, the need for human accountants and auditors diminishes."], "examples": [("QuickBooks", "https://quickbooks.intuit.com/"), ("Xero", "https://www.xero.com/"), ("Wikipedia: Accounting", "https://en.wikipedia.org/wiki/Accounting")]},
  {"name": "Algorithmic trading and robo-advisory", "paragraphs": ["Algorithms execute trades and manage portfolios faster and more consistently than human traders. Robo-advisors build and rebalance portfolios automatically based on client goals and risk tolerance.", "These systems remove the need for human traders and financial advisors for routine investment decisions. Human oversight shifts to exceptions and client relationships."], "examples": [("Betterment", "https://www.betterment.com/"), ("Wealthfront", "https://www.wealthfront.com/"), ("Wikipedia: Robo-advisor", "https://en.wikipedia.org/wiki/Robo-advisor")]},
  {"name": "Automated financial reporting and forecasting", "paragraphs": ["Tools that generate financial statements, budgets, and forecasts from live data reduce the manual work of financial analysts. They update projections automatically as new data arrives.", "Predictive models improve accuracy and speed, making the traditional analyst role less necessary for routine reporting."], "examples": [("Anaplan", "https://www.anaplan.com/"), ("Workday Adaptive Planning", "https://www.workday.com/"), ("Wikipedia: Financial forecasting", "https://en.wikipedia.org/wiki/Financial_forecasting")]},
  {"name": "LLM tax preparation and compliance review", "paragraphs": ["Language models can prepare tax returns and check regulatory compliance by interpreting tax codes and financial documents. They reduce the manual work of tax preparers and compliance officers.", "As accuracy improves, routine tax and compliance work can be handled end-to-end by AI, with humans reviewing only edge cases."], "examples": [("TurboTax", "https://turbotax.intuit.com/"), ("H&R Block", "https://www.hrblock.com/"), ("Wikipedia: Tax preparation", "https://en.wikipedia.org/wiki/Tax_preparation")]},
  {"name": "RPA for invoice and expense processing", "paragraphs": ["Bots capture, validate, and post invoices and expenses, replacing manual data entry and verification. They integrate with accounting systems to keep records current.", "This automates the repetitive back-office work of accounts payable and expense management."], "examples": [("Bill.com", "https://www.bill.com/"), ("Expensify", "https://www.expensify.com/"), ("Wikipedia: Accounts payable", "https://en.wikipedia.org/wiki/Accounts_payable")]},
 ],
 "15": [
  {"name": "AI code generation and agentic software engineering", "paragraphs": ["AI tools can write, refactor, and ship code from natural-language descriptions, reducing the need for human programmers for routine development. Agentic systems can plan, implement, and test features autonomously.", "This shifts software engineering toward higher-level design and oversight, with much of the implementation automated."], "examples": [("GitHub Copilot", "https://github.com/features/copilot"), ("Cursor", "https://cursor.sh/"), ("Wikipedia: Code generation", "https://en.wikipedia.org/wiki/Code_generation_(compiler)")]},
  {"name": "Automated testing and bug triage", "paragraphs": ["AI can generate tests, reproduce failures, and prioritize bugs, reducing the manual work of QA engineers. Automated pipelines run continuously and surface issues without human monitoring.", "This compresses the testing phase and reduces the need for large QA teams."], "examples": [("Selenium", "https://www.selenium.dev/"), ("Cypress", "https://www.cypress.io/"), ("Wikipedia: Software testing", "https://en.wikipedia.org/wiki/Software_testing")]},
  {"name": "AutoML and automated model deployment", "paragraphs": ["Platforms that train and deploy machine learning models with minimal human tuning reduce the need for data scientists and ML engineers. They automate feature engineering, model selection, and deployment.", "This democratizes ML and shrinks the specialized workforce needed to build predictive systems."], "examples": [("Google AutoML", "https://cloud.google.com/automl"), ("H2O.ai", "https://h2o.ai/"), ("Wikipedia: Automated machine learning", "https://en.wikipedia.org/wiki/Automated_machine_learning")]},
  {"name": "LLM-assisted data analysis and querying", "paragraphs": ["Natural-language interfaces over databases let non-specialists query and analyze data without SQL or scripting. LLMs translate questions into queries and summarize results.", "This reduces the need for data analysts and report writers for routine analysis."], "examples": [("ChatGPT Advanced Data Analysis", "https://chat.openai.com/"), ("Claude", "https://claude.ai/"), ("Wikipedia: Natural language processing", "https://en.wikipedia.org/wiki/Natural_language_processing")]},
  {"name": "AI-driven DevOps and incident response", "paragraphs": ["Automation handles deployment, monitoring, and on-call triage, reducing the need for DevOps and SRE staff. AI can detect anomalies, diagnose root causes, and even remediate automatically.", "This compresses the operational work of keeping systems running."], "examples": [("Datadog", "https://www.datadoghq.com/"), ("PagerDuty", "https://www.pagerduty.com/"), ("Wikipedia: DevOps", "https://en.wikipedia.org/wiki/DevOps")]},
 ],
 "17": [
  {"name": "Generative design and AI-assisted engineering", "paragraphs": ["AI can propose optimized structures and components from constraints, reducing the manual iteration of engineers. Generative design explores thousands of variants automatically.", "This compresses the design phase and reduces the need for large engineering teams."], "examples": [("Autodesk Generative Design", "https://www.autodesk.com/solutions/generative-design"), ("nTopology", "https://ntopology.com/"), ("Wikipedia: Generative design", "https://en.wikipedia.org/wiki/Generative_design")]},
  {"name": "Building information modeling (BIM) automation", "paragraphs": ["Automated generation and coordination of building models reduces manual drafting and coordination work. AI can detect clashes and optimize layouts.", "This streamlines architecture and engineering workflows."], "examples": [("Autodesk Revit", "https://www.autodesk.com/products/revit/overview"), ("ArchiCAD", "https://graphisoft.com/solutions/archicad"), ("Wikipedia: Building information modeling", "https://en.wikipedia.org/wiki/Building_information_modeling")]},
  {"name": "Autonomous surveying with drones and LiDAR", "paragraphs": ["Unmanned aerial and laser scanning of sites and terrain replaces manual surveying. Drones capture high-resolution data quickly and safely.", "This reduces the need for survey crews and speeds up site assessment."], "examples": [("DJI", "https://www.dji.com/"), ("Leica Geosystems", "https://leica-geosystems.com/"), ("Wikipedia: LiDAR", "https://en.wikipedia.org/wiki/Lidar")]},
  {"name": "AI structural optimization and simulation", "paragraphs": ["Machine learning tests and optimizes designs under load, reducing manual analysis. Simulations run automatically across design variants.", "This compresses engineering analysis and reduces specialist time."], "examples": [("Ansys", "https://www.ansys.com/"), ("SimScale", "https://www.simscale.com/"), ("Wikipedia: Finite element method", "https://en.wikipedia.org/wiki/Finite_element_method")]},
  {"name": "Robotic construction planning and scheduling", "paragraphs": ["Automated sequencing and resource planning for builds reduces manual project planning. AI optimizes schedules and detects conflicts.", "This streamlines construction management."], "examples": [("Procore", "https://www.procore.com/"), ("PlanGrid", "https://www.plangrid.com/"), ("Wikipedia: Construction management", "https://en.wikipedia.org/wiki/Construction_management")]},
 ],
 "19": [
  {"name": "AI literature review and hypothesis generation", "paragraphs": ["Models that scan research and propose new questions reduce the manual work of researchers. They can summarize papers and identify gaps.", "This accelerates the research process and reduces the need for large research teams."], "examples": [("Elicit", "https://elicit.com/"), ("Semantic Scholar", "https://www.semanticscholar.org/"), ("Wikipedia: Literature review", "https://en.wikipedia.org/wiki/Literature_review")]},
  {"name": "Robotic laboratories and automated experiments", "paragraphs": ["Self-driving labs run experiments without human hands, reducing the need for lab technicians. They execute protocols and collect data automatically.", "This compresses experimental work and reduces lab staffing."], "examples": [("Emerald Cloud Lab", "https://www.emeraldcloudlab.com/"), ("Strateos", "https://strateos.com/"), ("Wikipedia: Laboratory automation", "https://en.wikipedia.org/wiki/Laboratory_automation")]},
  {"name": "Computational modeling and simulation", "paragraphs": ["In-silico experiments replace physical trials, reducing the need for field researchers. Models simulate complex systems quickly.", "This shifts research from physical to computational."], "examples": [("MATLAB", "https://www.mathworks.com/"), ("COMSOL", "https://www.comsol.com/"), ("Wikipedia: Computer simulation", "https://en.wikipedia.org/wiki/Computer_simulation")]},
  {"name": "AI-driven data collection and remote sensing", "paragraphs": ["Automated gathering of field and satellite data reduces the need for field researchers. Sensors and satellites collect continuously.", "This compresses data collection and reduces staffing."], "examples": [("Planet Labs", "https://www.planet.com/"), ("Maxar", "https://www.maxar.com/"), ("Wikipedia: Remote sensing", "https://en.wikipedia.org/wiki/Remote_sensing")]},
  {"name": "Automated statistical analysis and reporting", "paragraphs": ["Tools that analyze datasets and generate reports reduce the manual work of analysts. They run analyses and produce insights automatically.", "This compresses analysis and reduces staffing."], "examples": [("R", "https://www.r-project.org/"), ("Python", "https://www.python.org/"), ("Wikipedia: Statistics", "https://en.wikipedia.org/wiki/Statistics")]},
 ],
 "21": [
  {"name": "AI triage chatbots for counseling and intake", "paragraphs": ["Conversational agents assess needs and route cases, reducing the need for intake staff. They handle initial screening and referrals.", "This compresses intake work and reduces staffing."], "examples": [("Woebot", "https://woebothealth.com/"), ("Wysa", "https://www.wysa.com/"), ("Wikipedia: Chatbot", "https://en.wikipedia.org/wiki/Chatbot")]},
  {"name": "Automated case management and eligibility checks", "paragraphs": ["Systems that process applications and verify eligibility reduce the need for case workers. They automate verification and routing.", "This compresses casework and reduces staffing."], "examples": [("Salesforce Nonprofit", "https://www.salesforce.org/"), ("Casebook", "https://www.casebook.net/"), ("Wikipedia: Case management", "https://en.wikipedia.org/wiki/Case_management_(mental_health)")]},
  {"name": "Telehealth triage and remote support", "paragraphs": ["Remote assessment and care coordination platforms reduce the need for in-person staff. They enable remote service delivery.", "This compresses service delivery and reduces staffing."], "examples": [("Teladoc", "https://www.teladoc.com/"), ("Amwell", "https://business.amwell.com/"), ("Wikipedia: Telehealth", "https://en.wikipedia.org/wiki/Telehealth")]},
  {"name": "AI-assisted benefit and service navigation", "paragraphs": ["Guides that match people to programs and services reduce the need for navigators. They automate matching and enrollment.", "This compresses navigation work and reduces staffing."], "examples": [("Benefits Data Trust", "https://bdtrust.org/"), ("mRelief", "https://www.mrelief.com/"), ("Wikipedia: Social work", "https://en.wikipedia.org/wiki/Social_work")]},
 ],
 "23": [
  {"name": "LLM contract review and legal research", "paragraphs": ["Models that read contracts and surface risks and precedents reduce the need for junior lawyers and paralegals. They compress document review.", "This reduces staffing for routine legal work."], "examples": [("Harvey", "https://www.harvey.ai/"), ("LexisNexis", "https://www.lexisnexis.com/"), ("Wikipedia: Legal research", "https://en.wikipedia.org/wiki/Legal_research")]},
  {"name": "Automated discovery and document analysis", "paragraphs": ["AI that sorts and analyzes large document sets reduces the need for document reviewers. It automates classification and extraction.", "This compresses discovery work and reduces staffing."], "examples": [("Relativity", "https://www.relativity.com/"), ("DISCO", "https://www.csdisco.com/"), ("Wikipedia: Electronic discovery", "https://en.wikipedia.org/wiki/Electronic_discovery")]},
  {"name": "AI drafting of briefs, wills, and filings", "paragraphs": ["Generative tools that draft legal documents reduce the need for drafting lawyers. They produce first drafts from templates and facts.", "This compresses drafting work and reduces staffing."], "examples": [("LegalZoom", "https://www.legalzoom.com/"), ("DoNotPay", "https://donotpay.com/"), ("Wikipedia: Legal document", "https://en.wikipedia.org/wiki/Legal_document")]},
  {"name": "Compliance automation and regulatory monitoring", "paragraphs": ["Systems that track regulatory changes and compliance status reduce the need for compliance officers. They automate monitoring and reporting.", "This compresses compliance work and reduces staffing."], "examples": [("Thomson Reuters", "https://www.thomsonreuters.com/"), ("ComplyAdvantage", "https://complyadvantage.com/"), ("Wikipedia: Regulatory compliance", "https://en.wikipedia.org/wiki/Regulatory_compliance")]},
  {"name": "Online dispute resolution platforms", "paragraphs": ["Digital platforms that resolve conflicts without courts reduce the need for litigators. They automate negotiation and mediation.", "This compresses dispute resolution and reduces staffing."], "examples": [("Modria", "https://www.modria.com/"), ("Tyler Technologies", "https://www.tylertech.com/"), ("Wikipedia: Online dispute resolution", "https://en.wikipedia.org/wiki/Online_dispute_resolution")]},
 ],
 "25": [
  {"name": "AI tutors and adaptive learning platforms", "paragraphs": ["Personalized AI instruction that adapts to each learner reduces the need for human tutors. They provide one-on-one support at scale.", "This compresses tutoring work and reduces staffing."], "examples": [("Khanmigo", "https://www.khanacademy.org/khan-labs"), ("Duolingo", "https://www.duolingo.com/"), ("Wikipedia: Intelligent tutoring system", "https://en.wikipedia.org/wiki/Intelligent_tutoring_system")]},
  {"name": "Automated grading and feedback", "paragraphs": ["AI that scores assignments and gives feedback reduces the need for grading teachers. It automates assessment.", "This compresses grading work and reduces staffing."], "examples": [("Gradescope", "https://www.gradescope.com/"), ("Turnitin", "https://www.turnitin.com/"), ("Wikipedia: Educational assessment", "https://en.wikipedia.org/wiki/Educational_assessment")]},
  {"name": "LLM lesson planning and content generation", "paragraphs": ["Models that draft curricula and teaching materials reduce the need for lesson planning. They generate resources automatically.", "This compresses planning work and reduces staffing."], "examples": [("MagicSchool", "https://www.magicschool.ai/"), ("Eduaide", "https://www.eduaide.ai/"), ("Wikipedia: Lesson plan", "https://en.wikipedia.org/wiki/Lesson_plan")]},
  {"name": "Virtual classrooms and AI teaching assistants", "paragraphs": ["Online platforms with AI support for instructors reduce the need for classroom aides. They automate support tasks.", "This compresses support work and reduces staffing."], "examples": [("Zoom", "https://zoom.us/"), ("Google Classroom", "https://classroom.google.com/"), ("Wikipedia: Virtual learning environment", "https://en.wikipedia.org/wiki/Virtual_learning_environment")]},
  {"name": "Personalized curriculum optimization", "paragraphs": ["Adaptive systems that tailor learning paths reduce the need for curriculum designers. They optimize content automatically.", "This compresses design work and reduces staffing."], "examples": [("Knewton", "https://www.knewton.com/"), ("Carnegie Learning", "https://www.carnegielearning.com/"), ("Wikipedia: Adaptive learning", "https://en.wikipedia.org/wiki/Adaptive_learning")]},
 ],
 "27": [
  {"name": "Generative AI for image, video, and music", "paragraphs": ["Models that create media from text prompts reduce the need for human artists and composers. They generate content automatically.", "This compresses creative production and reduces staffing."], "examples": [("Midjourney", "https://www.midjourney.com/"), ("Runway", "https://runwayml.com/"), ("Wikipedia: Generative artificial intelligence", "https://en.wikipedia.org/wiki/Generative_artificial_intelligence")]},
  {"name": "AI editing, dubbing, and post-production", "paragraphs": ["Automated editing, translation, and voice cloning reduce the need for editors and dubbing artists. They process media automatically.", "This compresses post-production and reduces staffing."], "examples": [("Descript", "https://www.descript.com/"), ("ElevenLabs", "https://elevenlabs.io/"), ("Wikipedia: Video editing", "https://en.wikipedia.org/wiki/Video_editing")]},
  {"name": "Automated content and copy generation", "paragraphs": ["AI that writes articles, ads, and marketing copy reduces the need for copywriters. It generates text automatically.", "This compresses content creation and reduces staffing."], "examples": [("Jasper", "https://www.jasper.ai/"), ("Copy.ai", "https://www.copy.ai/"), ("Wikipedia: Copywriting", "https://en.wikipedia.org/wiki/Copywriting")]},
  {"name": "Virtual influencers and synthetic media", "paragraphs": ["AI-generated personas and digital avatars reduce the need for human performers. They create synthetic media automatically.", "This compresses media production and reduces staffing."], "examples": [("Synthesia", "https://www.synthesia.io/"), ("HeyGen", "https://www.heygen.com/"), ("Wikipedia: Virtual influencer", "https://en.wikipedia.org/wiki/Virtual_influencer")]},
  {"name": "AI game and level design", "paragraphs": ["Procedural and AI-assisted game content creation reduces the need for level designers. It generates content automatically.", "This compresses game design and reduces staffing."], "examples": [("Unity", "https://unity.com/"), ("Unreal Engine", "https://www.unrealengine.com/"), ("Wikipedia: Procedural generation", "https://en.wikipedia.org/wiki/Procedural_generation")]},
 ],
 "29": [
  {"name": "AI diagnosis and clinical decision support", "paragraphs": ["Models that assist or automate diagnosis reduce the need for diagnosticians. They analyze symptoms and suggest conditions.", "This compresses diagnosis and reduces staffing."], "examples": [("Watson Health", "https://www.ibm.com/watson-health"), ("Ada Health", "https://ada.com/"), ("Wikipedia: Clinical decision support system", "https://en.wikipedia.org/wiki/Clinical_decision_support_system")]},
  {"name": "Surgical and diagnostic robotics", "paragraphs": ["Robots that perform or assist in procedures reduce the need for surgeons. They operate with precision and consistency.", "This compresses surgical work and reduces staffing."], "examples": [("da Vinci", "https://www.intuitive.com/"), ("Medtronic", "https://www.medtronic.com/"), ("Wikipedia: Surgical robot", "https://en.wikipedia.org/wiki/Surgical_robot")]},
  {"name": "AI radiology and pathology screening", "paragraphs": ["Image analysis for detecting disease reduces the need for radiologists and pathologists. It screens images automatically.", "This compresses screening and reduces staffing."], "examples": [("Aidoc", "https://www.aidoc.com/"), ("Zebra Medical", "https://www.zebra-med.com/"), ("Wikipedia: Radiology", "https://en.wikipedia.org/wiki/Radiology")]},
  {"name": "Ambient AI scribes for medical documentation", "paragraphs": ["AI that transcribes clinical encounters reduces the need for medical scribes. It captures notes automatically.", "This compresses documentation and reduces staffing."], "examples": [("Nuance DAX", "https://www.nuance.com/healthcare/ambient-clinical-intelligence.html"), ("Abridge", "https://www.abridge.com/"), ("Wikipedia: Medical scribe", "https://en.wikipedia.org/wiki/Medical_scribe")]},
  {"name": "AI drug discovery and trial optimization", "paragraphs": ["Models that accelerate molecule and trial design reduce the need for researchers. They predict efficacy and optimize trials.", "This compresses discovery and reduces staffing."], "examples": [("Insilico Medicine", "https://insilico.com/"), ("Recursion", "https://www.recursion.com/"), ("Wikipedia: Drug discovery", "https://en.wikipedia.org/wiki/Drug_discovery")]},
 ],
 "31": [
  {"name": "Care and service robots", "paragraphs": ["Robots assisting with patient care tasks reduce the need for aides. They handle lifting, delivery, and monitoring.", "This compresses care work and reduces staffing."], "examples": [("SoftBank Robotics", "https://www.softbankrobotics.com/"), ("Diligent Robotics", "https://www.diligentrobots.com/"), ("Wikipedia: Care robot", "https://en.wikipedia.org/wiki/Care_robot")]},
  {"name": "Automated patient monitoring and alerts", "paragraphs": ["Continuous vitals monitoring with AI alerts reduces the need for manual monitoring. It detects deterioration early.", "This compresses monitoring and reduces staffing."], "examples": [("Philips", "https://www.philips.com/"), ("Masimo", "https://www.masimo.com/"), ("Wikipedia: Patient monitoring", "https://en.wikipedia.org/wiki/Patient_monitoring")]},
  {"name": "Robotic medication dispensing", "paragraphs": ["Automated pharmacy and dispensing systems reduce the need for pharmacists and technicians. They handle counting and labeling.", "This compresses dispensing and reduces staffing."], "examples": [("Omnicell", "https://www.omnicell.com/"), ("BD", "https://www.bd.com/"), ("Wikipedia: Automated dispensing cabinet", "https://en.wikipedia.org/wiki/Automated_dispensing_cabinet")]},
  {"name": "AI scheduling and task routing", "paragraphs": ["Automated staff scheduling and task assignment reduce the need for coordinators. They optimize shifts and routing.", "This compresses scheduling and reduces staffing."], "examples": [("QGenda", "https://www.qgenda.com/"), ("TCP", "https://www.tcpsoftware.com/"), ("Wikipedia: Nurse scheduling", "https://en.wikipedia.org/wiki/Nurse_scheduling_problem")]},
  {"name": "Remote patient monitoring platforms", "paragraphs": ["Home-based monitoring and telehealth reduce the need for in-person visits. They track patients remotely.", "This compresses in-person care and reduces staffing."], "examples": [("TytoCare", "https://www.tytocare.com/"), ("Biofourmis", "https://www.biofourmis.com/"), ("Wikipedia: Remote patient monitoring", "https://en.wikipedia.org/wiki/Remote_patient_monitoring")]},
 ],
 "33": [
  {"name": "AI video analytics and surveillance", "paragraphs": ["Computer vision for threat detection reduces the need for human monitors. It analyzes footage in real time.", "This compresses surveillance and reduces staffing."], "examples": [("Verkada", "https://www.verkada.com/"), ("Milestone", "https://www.milestone-systems.com/"), ("Wikipedia: Video surveillance", "https://en.wikipedia.org/wiki/Video_surveillance")]},
  {"name": "Autonomous security robots and drones", "paragraphs": ["Patrol robots and drones for security reduce the need for guards. They patrol and detect anomalies.", "This compresses patrol work and reduces staffing."], "examples": [("Knightscope", "https://www.knightscope.com/"), ("Cobalt Robotics", "https://www.cobaltrobotics.com/"), ("Wikipedia: Security robot", "https://en.wikipedia.org/wiki/Security_robot")]},
  {"name": "Predictive policing and risk scoring", "paragraphs": ["Data-driven crime prediction and risk assessment reduce the need for analysts. They forecast and prioritize.", "This compresses analysis and reduces staffing."], "examples": [("PredPol", "https://www.predpol.com/"), ("Palantir", "https://www.palantir.com/"), ("Wikipedia: Predictive policing", "https://en.wikipedia.org/wiki/Predictive_policing")]},
  {"name": "Automated access control and screening", "paragraphs": ["Biometric and automated entry systems reduce the need for security staff. They verify identity and grant access.", "This compresses screening and reduces staffing."], "examples": [("Clear", "https://www.clearme.com/"), ("IDEMIA", "https://www.idemia.com/"), ("Wikipedia: Access control", "https://en.wikipedia.org/wiki/Access_control")]},
 ],
 "35": [
  {"name": "Kitchen and food-preparation robots", "paragraphs": ["Robotic cooking and food assembly reduce the need for cooks and prep staff. They handle repetitive kitchen tasks.", "This compresses food prep and reduces staffing."], "examples": [("Moley Robotics", "https://www.moley.com/"), ("Creator", "https://www.creator.rest/"), ("Wikipedia: Kitchen robot", "https://en.wikipedia.org/wiki/Kitchen_robot")]},
  {"name": "Self-service kiosks and automated ordering", "paragraphs": ["Touchscreen ordering and payment systems reduce the need for cashiers and servers. They handle ordering and payment.", "This compresses ordering and reduces staffing."], "examples": [("Toast", "https://pos.toasttab.com/"), ("Square", "https://squareup.com/"), ("Wikipedia: Self-service", "https://en.wikipedia.org/wiki/Self-service")]},
  {"name": "Delivery robots and drones", "paragraphs": ["Autonomous last-mile delivery reduces the need for delivery drivers. They transport food and goods.", "This compresses delivery and reduces staffing."], "examples": [("Starship", "https://www.starship.xyz/"), ("Zipline", "https://www.flyzipline.com/"), ("Wikipedia: Delivery drone", "https://en.wikipedia.org/wiki/Delivery_drone")]},
  {"name": "AI inventory and demand forecasting", "paragraphs": ["Predictive stock and demand management reduce the need for inventory staff. They forecast and reorder automatically.", "This compresses inventory work and reduces staffing."], "examples": [("Blue Yonder", "https://blueyonder.com/"), ("RELEX", "https://www.relexsolutions.com/"), ("Wikipedia: Demand forecasting", "https://en.wikipedia.org/wiki/Demand_forecasting")]},
  {"name": "Robotic baristas and beverage systems", "paragraphs": ["Automated coffee and drink preparation reduce the need for baristas. They prepare beverages consistently.", "This compresses beverage prep and reduces staffing."], "examples": [("Cafe X", "https://www.cafexapp.com/"), ("Briggo", "https://www.briggo.com/"), ("Wikipedia: Automated cafe", "https://en.wikipedia.org/wiki/Automated_cafe")]},
 ],
 "37": [
  {"name": "Autonomous cleaning and floor-care robots", "paragraphs": ["Robotic vacuums and scrubbers for facilities reduce the need for cleaners. They clean floors automatically.", "This compresses cleaning and reduces staffing."], "examples": [("iRobot", "https://www.irobot.com/"), ("Tennant", "https://www.tennantco.com/"), ("Wikipedia: Robotic vacuum cleaner", "https://en.wikipedia.org/wiki/Robotic_vacuum_cleaner")]},
  {"name": "Robotic lawn mowers and grounds equipment", "paragraphs": ["Autonomous mowing and landscaping reduce the need for groundskeepers. They maintain lawns automatically.", "This compresses grounds care and reduces staffing."], "examples": [("Husqvarna", "https://www.husqvarna.com/"), ("John Deere", "https://www.deere.com/"), ("Wikipedia: Robotic lawn mower", "https://en.wikipedia.org/wiki/Robotic_lawn_mower")]},
  {"name": "Automated window and facade cleaning", "paragraphs": ["Robotic window and building cleaning reduce the need for window cleaners. They clean facades automatically.", "This compresses cleaning and reduces staffing."], "examples": [("Skyline Robotics", "https://www.skylinerobotics.com/"), ("Serbot", "https://www.serbot.ch/"), ("Wikipedia: Window cleaning", "https://en.wikipedia.org/wiki/Window_cleaning")]},
  {"name": "AI scheduling and route optimization", "paragraphs": ["Automated task scheduling and routing reduce the need for coordinators. They optimize routes and tasks.", "This compresses scheduling and reduces staffing."], "examples": [("ServiceTitan", "https://www.servicetitan.com/"), ("Jobber", "https://getjobber.com/"), ("Wikipedia: Vehicle routing problem", "https://en.wikipedia.org/wiki/Vehicle_routing_problem")]},
 ],
 "39": [
  {"name": "Care and companion robots", "paragraphs": ["Robots for elderly and personal care reduce the need for caregivers. They assist with daily tasks and companionship.", "This compresses care work and reduces staffing."], "examples": [("Intuition Robotics", "https://www.intuitionrobotics.com/"), ("PARO", "https://www.parorobots.com/"), ("Wikipedia: Care robot", "https://en.wikipedia.org/wiki/Care_robot")]},
  {"name": "AI personal assistants and concierges", "paragraphs": ["Virtual assistants for personal services reduce the need for concierges. They handle requests and scheduling.", "This compresses service work and reduces staffing."], "examples": [("Alexa", "https://www.alexa.com/"), ("Google Assistant", "https://assistant.google.com/"), ("Wikipedia: Virtual assistant", "https://en.wikipedia.org/wiki/Virtual_assistant")]},
  {"name": "Automated salon and grooming devices", "paragraphs": ["Robotic and automated grooming tools reduce the need for salon staff. They handle grooming tasks.", "This compresses grooming work and reduces staffing."], "examples": [("Dyson", "https://www.dyson.com/"), ("Philips", "https://www.philips.com/"), ("Wikipedia: Hair clipper", "https://en.wikipedia.org/wiki/Hair_clipper")]},
  {"name": "Wearable health and wellness monitoring", "paragraphs": ["Devices tracking health and fitness reduce the need for wellness coaches. They monitor and advise.", "This compresses coaching and reduces staffing."], "examples": [("Apple Watch", "https://www.apple.com/apple-watch/"), ("Fitbit", "https://www.fitbit.com/"), ("Wikipedia: Wearable technology", "https://en.wikipedia.org/wiki/Wearable_technology")]},
 ],
 "41": [
  {"name": "AI sales agents and chatbots", "paragraphs": ["Conversational AI for sales and support reduces the need for sales reps. They handle inquiries and qualification.", "This compresses sales work and reduces staffing."], "examples": [("Drift", "https://www.drift.com/"), ("Intercom", "https://www.intercom.com/"), ("Wikipedia: Chatbot", "https://en.wikipedia.org/wiki/Chatbot")]},
  {"name": "Automated pricing and promotion optimization", "paragraphs": ["Dynamic pricing and promotion engines reduce the need for pricing analysts. They optimize prices automatically.", "This compresses pricing work and reduces staffing."], "examples": [("Prisync", "https://prisync.com/"), ("Competera", "https://competera.net/"), ("Wikipedia: Dynamic pricing", "https://en.wikipedia.org/wiki/Dynamic_pricing")]},
  {"name": "Recommendation and personalization engines", "paragraphs": ["Systems that personalize product suggestions reduce the need for sales staff. They recommend products automatically.", "This compresses selling and reduces staffing."], "examples": [("Amazon", "https://www.amazon.com/"), ("Netflix", "https://www.netflix.com/"), ("Wikipedia: Recommender system", "https://en.wikipedia.org/wiki/Recommender_system")]},
  {"name": "Virtual shopping assistants", "paragraphs": ["AI helpers for online shopping reduce the need for sales associates. They assist customers automatically.", "This compresses sales support and reduces staffing."], "examples": [("Shopify", "https://www.shopify.com/"), ("Algolia", "https://www.algolia.com/"), ("Wikipedia: Virtual assistant", "https://en.wikipedia.org/wiki/Virtual_assistant")]},
  {"name": "AI lead scoring and CRM automation", "paragraphs": ["Automated lead qualification and CRM updates reduce the need for sales ops. They score and route leads automatically.", "This compresses sales ops and reduces staffing."], "examples": [("Salesforce", "https://www.salesforce.com/"), ("HubSpot", "https://www.hubspot.com/"), ("Wikipedia: Customer relationship management", "https://en.wikipedia.org/wiki/Customer_relationship_management")]},
 ],
 "43": [
  {"name": "Robotic process automation (RPA)", "paragraphs": ["Bots that automate repetitive office tasks reduce the need for clerks and admins. They handle routine workflows.", "This compresses office work and reduces staffing."], "examples": [("UiPath", "https://www.uipath.com/"), ("Blue Prism", "https://www.blueprism.com/"), ("Wikipedia: Robotic process automation", "https://en.wikipedia.org/wiki/Robotic_process_automation")]},
  {"name": "LLM document processing and data entry", "paragraphs": ["AI that extracts and enters document data reduces the need for data entry clerks. It processes documents automatically.", "This compresses data entry and reduces staffing."], "examples": [("ABBYY", "https://www.abbyy.com/"), ("Hyperscience", "https://www.hyperscience.com/"), ("Wikipedia: Data entry", "https://en.wikipedia.org/wiki/Data_entry")]},
  {"name": "AI email drafting and triage", "paragraphs": ["AI that writes and sorts email reduces the need for administrative assistants. It handles correspondence automatically.", "This compresses email work and reduces staffing."], "examples": [("Superhuman", "https://superhuman.com/"), ("Gmail", "https://mail.google.com/"), ("Wikipedia: Email", "https://en.wikipedia.org/wiki/Email")]},
  {"name": "Automated scheduling and calendar management", "paragraphs": ["AI scheduling assistants reduce the need for schedulers. They manage calendars and bookings automatically.", "This compresses scheduling and reduces staffing."], "examples": [("Calendly", "https://calendly.com/"), ("Motion", "https://www.usemotion.com/"), ("Wikipedia: Appointment scheduling", "https://en.wikipedia.org/wiki/Appointment_scheduling")]},
  {"name": "Voice assistants and transcription", "paragraphs": ["Speech-to-text and voice-driven tools reduce the need for transcriptionists. They convert speech to text automatically.", "This compresses transcription and reduces staffing."], "examples": [("Otter.ai", "https://otter.ai/"), ("Dragon", "https://www.nuance.com/dragon.html"), ("Wikipedia: Speech recognition", "https://en.wikipedia.org/wiki/Speech_recognition")]},
 ],
 "45": [
  {"name": "Precision agriculture and AI crop management", "paragraphs": ["Data-driven farming and crop optimization reduce the need for manual farm management. They monitor and optimize crops.", "This compresses management and reduces staffing."], "examples": [("Climate FieldView", "https://climate.com/"), ("Trimble", "https://www.trimble.com/"), ("Wikipedia: Precision agriculture", "https://en.wikipedia.org/wiki/Precision_agriculture")]},
  {"name": "Autonomous tractors and harvesters", "paragraphs": ["Self-driving farm machinery reduces the need for equipment operators. They operate autonomously.", "This compresses operation and reduces staffing."], "examples": [("John Deere", "https://www.deere.com/"), ("Case IH", "https://www.caseih.com/"), ("Wikipedia: Autonomous tractor", "https://en.wikipedia.org/wiki/Autonomous_tractor")]},
  {"name": "Harvesting and picking robots", "paragraphs": ["Robots that pick crops reduce the need for pickers. They harvest automatically.", "This compresses harvesting and reduces staffing."], "examples": [("Abundant Robotics", "https://www.abundantrobotics.com/"), ("FFRobotics", "https://www.ffrobotics.com/"), ("Wikipedia: Agricultural robot", "https://en.wikipedia.org/wiki/Agricultural_robot")]},
  {"name": "Drone monitoring and spraying", "paragraphs": ["Aerial crop monitoring and spraying reduce the need for scouts and sprayers. They monitor and treat crops.", "This compresses monitoring and reduces staffing."], "examples": [("DJI Agriculture", "https://ag.dji.com/"), ("PrecisionHawk", "https://www.precisionhawk.com/"), ("Wikipedia: Agricultural drone", "https://en.wikipedia.org/wiki/Agricultural_drone")]},
  {"name": "Automated aquaculture and fishery systems", "paragraphs": ["Automated fish farming and monitoring reduce the need for fishery workers. They manage aquaculture automatically.", "This compresses aquaculture and reduces staffing."], "examples": [("Cermaq", "https://www.cermaq.com/"), ("InnovaSea", "https://www.innovasea.com/"), ("Wikipedia: Aquaculture", "https://en.wikipedia.org/wiki/Aquaculture")]},
 ],
 "47": [
  {"name": "Autonomous construction equipment", "paragraphs": ["Self-driving bulldozers, excavators, etc. reduce the need for operators. They operate autonomously.", "This compresses operation and reduces staffing."], "examples": [("Caterpillar", "https://www.caterpillar.com/"), ("Komatsu", "https://www.komatsu.com/"), ("Wikipedia: Autonomous construction", "https://en.wikipedia.org/wiki/Autonomous_construction")]},
  {"name": "Robotic bricklaying and 3D-printed buildings", "paragraphs": ["Robots that lay bricks and print structures reduce the need for masons. They build automatically.", "This compresses construction and reduces staffing."], "examples": [("Hadrian X", "https://www.fbr.com.au/"), ("ICON", "https://www.iconbuild.com/"), ("Wikipedia: 3D printing in construction", "https://en.wikipedia.org/wiki/3D_printing_in_construction")]},
  {"name": "AI site planning and scheduling", "paragraphs": ["Automated construction planning and scheduling reduce the need for planners. They optimize schedules automatically.", "This compresses planning and reduces staffing."], "examples": [("Procore", "https://www.procore.com/"), ("Autodesk Construction Cloud", "https://construction.autodesk.com/"), ("Wikipedia: Construction management", "https://en.wikipedia.org/wiki/Construction_management")]},
  {"name": "Automated surveying and inspection drones", "paragraphs": ["Drones for site survey and inspection reduce the need for surveyors. They capture data automatically.", "This compresses surveying and reduces staffing."], "examples": [("Skycatch", "https://www.skycatch.com/"), ("DroneDeploy", "https://www.dronedeploy.com/"), ("Wikipedia: Surveying", "https://en.wikipedia.org/wiki/Surveying")]},
  {"name": "Robotic excavation and tunneling", "paragraphs": ["Automated digging and tunneling machines reduce the need for operators. They excavate automatically.", "This compresses excavation and reduces staffing."], "examples": [("The Boring Company", "https://www.boringcompany.com/"), ("Herrenknecht", "https://www.herrenknecht.com/"), ("Wikipedia: Tunnel boring machine", "https://en.wikipedia.org/wiki/Tunnel_boring_machine")]},
 ],
 "49": [
  {"name": "Predictive maintenance and AI diagnostics", "paragraphs": ["AI that predicts equipment failures reduces the need for maintenance staff. It forecasts failures and schedules repairs.", "This compresses maintenance and reduces staffing."], "examples": [("Uptake", "https://www.uptake.com/"), ("Augury", "https://www.augury.com/"), ("Wikipedia: Predictive maintenance", "https://en.wikipedia.org/wiki/Predictive_maintenance")]},
  {"name": "AR-guided repair and remote assistance", "paragraphs": ["Augmented reality for repair guidance reduces the need for expert technicians. It overlays instructions on equipment.", "This compresses repair and reduces staffing."], "examples": [("Microsoft HoloLens", "https://www.microsoft.com/hololens"), ("TeamViewer", "https://www.teamviewer.com/"), ("Wikipedia: Augmented reality", "https://en.wikipedia.org/wiki/Augmented_reality")]},
  {"name": "Autonomous inspection drones", "paragraphs": ["Drones for equipment inspection reduce the need for inspectors. They capture imagery automatically.", "This compresses inspection and reduces staffing."], "examples": [("Percepto", "https://percepto.co/"), ("Skydio", "https://www.skydio.com/"), ("Wikipedia: Unmanned aerial vehicle", "https://en.wikipedia.org/wiki/Unmanned_aerial_vehicle")]},
  {"name": "Self-diagnosing and self-repairing systems", "paragraphs": ["Systems that detect and fix their own faults reduce the need for repair staff. They maintain themselves.", "This compresses repair and reduces staffing."], "examples": [("Siemens", "https://www.siemens.com/"), ("GE", "https://www.ge.com/"), ("Wikipedia: Self-healing", "https://en.wikipedia.org/wiki/Self-healing")]},
  {"name": "Robotic maintenance platforms", "paragraphs": ["Robots for maintenance tasks reduce the need for maintenance staff. They perform upkeep automatically.", "This compresses maintenance and reduces staffing."], "examples": [("Boston Dynamics", "https://www.bostondynamics.com/"), ("ABB", "https://www.abb.com/"), ("Wikipedia: Robot", "https://en.wikipedia.org/wiki/Robot")]},
 ],
 "51": [
  {"name": "Industrial and collaborative robots", "paragraphs": ["Robots for manufacturing and assembly reduce the need for production workers. They handle fabrication and assembly.", "This compresses production and reduces staffing."], "examples": [("FANUC", "https://www.fanuc.com/"), ("Universal Robots", "https://www.universal-robots.com/"), ("Wikipedia: Industrial robot", "https://en.wikipedia.org/wiki/Industrial_robot")]},
  {"name": "AI visual quality control", "paragraphs": ["Computer vision for defect detection reduces the need for inspectors. It checks quality automatically.", "This compresses inspection and reduces staffing."], "examples": [("Cognex", "https://www.cognex.com/"), ("Keyence", "https://www.keyence.com/"), ("Wikipedia: Machine vision", "https://en.wikipedia.org/wiki/Machine_vision")]},
  {"name": "Automated assembly and packaging", "paragraphs": ["Automated assembly lines and packaging reduce the need for assemblers. They handle production automatically.", "This compresses assembly and reduces staffing."], "examples": [("Bosch", "https://www.bosch.com/"), ("Rockwell Automation", "https://www.rockwellautomation.com/"), ("Wikipedia: Automation", "https://en.wikipedia.org/wiki/Automation")]},
  {"name": "Additive manufacturing (3D printing)", "paragraphs": ["3D printing for production reduces the need for machinists and toolmakers. It builds parts layer by layer.", "This compresses manufacturing and reduces staffing."], "examples": [("Stratasys", "https://www.stratasys.com/"), ("3D Systems", "https://www.3dsystems.com/"), ("Wikipedia: 3D printing", "https://en.wikipedia.org/wiki/3D_printing")]},
  {"name": "Autonomous warehouse and logistics systems", "paragraphs": ["Automated warehouses and logistics reduce the need for warehouse workers. They store and retrieve goods automatically.", "This compresses logistics and reduces staffing."], "examples": [("Amazon Robotics", "https://www.amazonrobotics.com/"), ("Locus Robotics", "https://locusrobotics.com/"), ("Wikipedia: Warehouse automation", "https://en.wikipedia.org/wiki/Warehouse_automation")]},
 ],
 "53": [
  {"name": "Autonomous vehicles and self-driving trucks", "paragraphs": ["Self-driving cars and trucks reduce the need for drivers. They navigate and transport automatically.", "This compresses driving and reduces staffing."], "examples": [("Waymo", "https://waymo.com/"), ("Tesla", "https://www.tesla.com/"), ("Wikipedia: Self-driving car", "https://en.wikipedia.org/wiki/Self-driving_car")]},
  {"name": "Delivery drones and sidewalk robots", "paragraphs": ["Autonomous delivery systems reduce the need for couriers. They deliver goods automatically.", "This compresses delivery and reduces staffing."], "examples": [("Starship", "https://www.starship.xyz/"), ("Zipline", "https://www.flyzipline.com/"), ("Wikipedia: Delivery drone", "https://en.wikipedia.org/wiki/Delivery_drone")]},
  {"name": "Automated ports, cranes, and warehouses", "paragraphs": ["Automated port and warehouse operations reduce the need for dockworkers. They handle cargo automatically.", "This compresses port work and reduces staffing."], "examples": [("Konecranes", "https://www.konecranes.com/"), ("Liebherr", "https://www.liebherr.com/"), ("Wikipedia: Automated guided vehicle", "https://en.wikipedia.org/wiki/Automated_guided_vehicle")]},
  {"name": "AI routing and fleet optimization", "paragraphs": ["AI for route and fleet management reduces the need for dispatchers. It optimizes routes and assignments.", "This compresses dispatch and reduces staffing."], "examples": [("Samsara", "https://www.samsara.com/"), ("Geotab", "https://www.geotab.com/"), ("Wikipedia: Vehicle routing problem", "https://en.wikipedia.org/wiki/Vehicle_routing_problem")]},
  {"name": "Autonomous forklifts and material handlers", "paragraphs": ["Self-driving forklifts and handlers reduce the need for operators. They move materials automatically.", "This compresses handling and reduces staffing."], "examples": [("Seegrid", "https://seegrid.com/"), ("OTTO Motors", "https://ottomotors.com/"), ("Wikipedia: Forklift truck", "https://en.wikipedia.org/wiki/Forklift_truck")]},
 ],
 "55": [
  {"name": "Autonomous systems and drone swarms", "paragraphs": ["Autonomous military systems and drones reduce the need for personnel. They operate without human crews.", "This compresses operations and reduces staffing."], "examples": [("Anduril", "https://www.anduril.com/"), ("Shield AI", "https://shield.ai/"), ("Wikipedia: Military robot", "https://en.wikipedia.org/wiki/Military_robot")]},
  {"name": "AI command-and-control and decision support", "paragraphs": ["AI for military command and decisions reduces the need for staff officers. It analyzes and recommends.", "This compresses command work and reduces staffing."], "examples": [("Palantir", "https://www.palantir.com/"), ("Scale AI", "https://scale.com/"), ("Wikipedia: Command and control", "https://en.wikipedia.org/wiki/Command_and_control")]},
  {"name": "Robotic logistics and resupply", "paragraphs": ["Robotic supply and logistics reduce the need for logistics personnel. They handle resupply automatically.", "This compresses logistics and reduces staffing."], "examples": [("Boston Dynamics", "https://www.bostondynamics.com/"), ("Ghost Robotics", "https://www.ghostrobotics.io/"), ("Wikipedia: Military logistics", "https://en.wikipedia.org/wiki/Military_logistics")]},
  {"name": "Unmanned vehicles and platforms", "paragraphs": ["Unmanned military vehicles reduce the need for crews. They operate without onboard personnel.", "This compresses vehicle operation and reduces staffing."], "examples": [("General Atomics", "https://www.ga.com/"), ("Northrop Grumman", "https://www.northropgrumman.com/"), ("Wikipedia: Unmanned combat aerial vehicle", "https://en.wikipedia.org/wiki/Unmanned_combat_aerial_vehicle")]},
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
            paras = item.get("paragraphs", [])
            examples = item.get("examples", [])
            tech_lines.append("### " + name)
            tech_lines.append("")
            for para in paras:
                tech_lines.append(para)
                tech_lines.append("")
            if examples:
                tech_lines.append("**Examples**")
                tech_lines.append("")
                for lbl, url in examples:
                    tech_lines.append("- [" + lbl + "](" + url + ")")
                tech_lines.append("")
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
