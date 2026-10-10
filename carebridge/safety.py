"""Visible medical-safety and ingestion guardrails; not a clinical triage system."""
import re
from urllib.parse import urlparse

BLOCKED_PATHS = ("/directory", "/staff/", "/patients/", "/login", "/signin", "/portal", "/employee", "/medical-record", "/appointments/")
MEDICAL_PERSONAL = re.compile(r"\b(my|me|i|mine|our|my child|my baby|my husband|my wife|i'm|i am)\b", re.I)
HIGH_STAKES = re.compile(r"\b(should i|get (?:the|a) (?:vaccine|shot)|how many doses|exact dose|dose for|diagnos|treat|prescri|contraindicat|pregnan|immunocompromis|allerg(?:ic|y)|medical history|blood test|cancer treatment|is it safe for|skip (?:a|my)|my symptoms)\b", re.I)
EMERGENCY = re.compile(r"\b(can't breathe|cannot breathe|trouble breathing|difficulty breathing|chest pain|throat swelling|face swelling|anaphylaxis|unconscious|passing out|seizure)\b", re.I)
INJECTION = re.compile(r"ignore (?:all |your |the )?(?:previous |prior |system )?instructions|system prompt|developer instructions|reveal (?:the |your )?secret|api[_ -]?key|you are now", re.I)
PERSONAL_CONTACT = re.compile(r"(?:[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\b(?:\+?1[- .]?)?\(?\d{3}\)?[- .]?\d{3}[- .]?\d{4}\b)", re.I)

def safe_url(url: str) -> bool:
    p = urlparse(url)
    if p.scheme != "https" or p.hostname not in {"www.cdc.gov", "cdc.gov"}:
        return False
    path = p.path.lower()
    return not any(x in path for x in BLOCKED_PATHS) and ("/vaccines/" in path or "/iis/" in path)

def screen_query(question: str) -> str | None:
    q = question.strip()
    if PERSONAL_CONTACT.search(q) or re.search(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b", q):
        return "Please do not include names, contact details, social security numbers, or other personal medical identifiers. Ask a general vaccine-education question instead."
    # Never treat a user's attempt to override safety or citation rules as evidence.
    if INJECTION.search(q) or re.search(r"\binvent (?:a |the )?(?:citation|reference|source)\b",q,re.I):
        return "I cannot follow instructions to invent citations or bypass safety rules. Please ask a factual vaccine-education question."
    if re.search(r"\b(?:private|confidential|neighbor|named patient|patient record|patient's record|medical record|vaccination status of|insurance|co-?pay|pricing|how much|cafeteria|hospital menu|wait time|phone number|cellphone|manufacturing cost|blood test|test results)\b",q,re.I):
        return "I do not have this individual, private, financial, or facility-specific information in the approved public CDC vaccine materials. Please contact the appropriate person or professional."
    if re.search(r"\b(?:should (?:this|that|my|a|the) patient|should (?:i|we|they|he|she) (?:get|receive)|can (?:i|my child) (?:get|receive)|whether this patient)\b",q,re.I):
        return "I cannot decide vaccination for a specific person. A licensed clinician should review the individual's medical history and current guidance."
    # Prevent lexical overlap with generic words like 'time' or 'good' from
    # turning an unrelated question into a cited medical answer.
    if not re.search(r"\b(?:vaccin\w*|immuniz\w*|shot|shots|vis|vaccine information statements?|hpv|mmr|mmrv|tdap|covid(?:[-\s]?19)?|coronavirus|shingles|zoster|pertussis|rubella|measles|hepatitis|influenza|flu|rsv|cdc)\b",q,re.I):
        return "I do not have enough information about that topic in the approved CDC vaccine materials. Please ask a specific general vaccine-information question."
    if PERSONAL_CONTACT.search(q) or re.search(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b", q):
        return "Please do not include names, contact details, social security numbers, or other personal medical identifiers. Ask a general vaccine-education question instead."
    if len(q) > 1000:
        return "Please ask a shorter, general educational question without personal health details."
    if EMERGENCY.search(q):
        return "I cannot assess emergencies. If someone may be having a serious allergic reaction or has difficulty breathing, call 911 in the United States or your local emergency number immediately."
    if MEDICAL_PERSONAL.search(q) and HIGH_STAKES.search(q):
        return "I cannot assess your personal medical history or decide on an individual vaccine or treatment plan. Please speak to a licensed clinician for patient-specific guidance. For general vaccine information, ask what a vaccine protects against."
    if re.search(r"\b(?:diagnose|prescribe|write a prescription|which medication)\b", q, re.I):
        return "CareBridge is an educational reference, not a medical diagnosis or prescribing service. Consult a licensed clinician."
    return None

def safe_document_text(text: str) -> bool:
    return not (INJECTION.search(text) or PERSONAL_CONTACT.search(text))
