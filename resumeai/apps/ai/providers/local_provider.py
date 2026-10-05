"""Offline rule-based provider.

Lets the whole pipeline (upload -> extract -> validate -> save -> match) work with no API key,
and powers tests/demo. It is NOT an LLM; switch AI_PROVIDER=openai for real AI analysis.
"""
import json
import re

from apps.jobs.skills import extract_skills

from .base import AIProvider, Usage

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{8,}\d")
URL_RE = re.compile(r"(?:https?://|www\.)\S+|(?:github|linkedin)\.com/\S+", re.IGNORECASE)
DATE_RANGE_RE = re.compile(
    r"((?:\d{1,2}[./])?(?:19|20)\d{2})\s*[-–—]\s*((?:\d{1,2}[./])?(?:19|20)\d{2}|present|now|теперішній|досі|наразі)",
    re.IGNORECASE,
)
SECTIONS = {
    "experience": ("experience", "work experience", "employment", "досвід", "досвід роботи", "опыт"),
    "education": ("education", "освіта", "образование"),
    "projects": ("projects", "проєкти", "проекти", "проекты"),
    "languages": ("languages", "мови", "языки", "мови володіння"),
    "skills": ("skills", "technical skills", "навички", "навыки"),
    "summary": ("summary", "profile", "about", "про себе", "профіль", "о себе"),
}
EDU_WORDS = ("university", "college", "institute", "університет", "коледж", "інститут", "університет")
LANG_LEVELS = re.compile(r"\b(A1|A2|B1|B2|C1|C2|native|рідна|рідна мова|fluent)\b", re.IGNORECASE)
KNOWN_LANGS = ["English", "Ukrainian", "Russian", "German", "Polish", "Spanish", "French",
               "Англійська", "Українська", "Російська", "Німецька", "Польська"]


def _split_sections(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        key = line.strip().strip(":#*").lower()
        found = next((s for s, names in SECTIONS.items() if key in names), None)
        if found:
            current = found
            result.setdefault(current, [])
        elif line.strip():
            result.setdefault(current, []).append(line.strip())
    return result


class LocalHeuristicProvider(AIProvider):
    name = "local"

    def analyze_resume(self, text: str) -> tuple[str, Usage]:
        sec = _split_sections(text)
        header = sec.get("header", [])
        email = (EMAIL_RE.search(text) or [None])[0]
        phone_m = PHONE_RE.search(text)
        links = list(dict.fromkeys(m.group(0).rstrip(".,;)") for m in URL_RE.finditer(text)))[:5]
        name = header[0] if header and len(header[0].split()) <= 4 and "@" not in header[0] else None

        skills = extract_skills(text)
        experience = self._experience(sec.get("experience", []))
        education = self._education(sec.get("education", []))
        projects = self._projects(sec.get("projects", []))
        languages = self._languages(sec.get("languages", []) or sec.get("skills", []))
        cyr = len(re.findall(r"[а-яіїєґА-ЯІЇЄҐ]", text))
        lang = "uk/ru" if cyr > len(text) * 0.2 else "en"

        has_numbers = bool(re.search(r"\d+\s*%|\b\d{2,}\s*(users|користувач|clients|клієнт)", text, re.IGNORECASE))
        scores = {
            "structure": min(100, 30 + 14 * len([k for k in ("experience", "education", "skills", "projects", "summary") if k in sec])),
            "clarity": 80 if 800 < len(text) < 6000 else 55,
            "skills": min(100, 25 + 8 * len(skills)),
            "experience": min(100, 25 + 25 * len(experience)),
            "achievements": 75 if has_numbers else 35,
            "ats_readiness": 85 if email and "experience" in sec and "skills" in sec else 55,
        }

        recs, issues, strengths = [], [], []
        if not email:
            issues.append("No email found")
            recs.append(dict(category="contacts", priority="high", title="Add contact details",
                             description="Add an email and phone so recruiters can reach you."))
        if not has_numbers:
            issues.append("No measurable results found")
            recs.append(dict(category="achievements", priority="high", title="Add measurable impact",
                             description="Add real, verified metrics to your latest role (do not invent numbers).",
                             before="Worked on backend development.",
                             suggested="Developed REST APIs with [technology], [verified result, e.g. response time -X%]."))
        if "summary" not in sec:
            recs.append(dict(category="summary", priority="medium", title="Add a short professional summary",
                             description="2-3 specific sentences about your role, stack and goals."))
        if not any("github" in link.lower() for link in links) and not projects:
            recs.append(dict(category="projects", priority="low", title="Link your projects",
                             description="Add GitHub links to relevant projects."))
        if len(skills) >= 5:
            strengths.append(f"{len(skills)} relevant technologies detected")
        if experience:
            strengths.append("Work experience section is present")
        if education:
            strengths.append("Education section is present")

        data = {
            "language": lang,
            "candidate": {"name": name, "email": email, "phone": phone_m.group(0).strip() if phone_m else None,
                          "location": None, "links": links},
            "summary": " ".join(sec.get("summary", []))[:500] or
                       (f"Candidate with skills in {', '.join(skills[:6])}." if skills else ""),
            "skills": {"technical": skills, "tools": [], "soft": []},
            "experience": experience, "education": education, "projects": projects, "languages": languages,
            "strengths": strengths, "issues": issues, "scores": scores, "recommendations": recs,
        }
        return json.dumps(data, ensure_ascii=False), Usage(model="local-heuristic")

    @staticmethod
    def _experience(lines: list[str]) -> list[dict]:
        items, cur = [], None
        for line in lines:
            m = DATE_RANGE_RE.search(line)
            if m:
                cur = {"company": None, "position": re.sub(DATE_RANGE_RE, "", line).strip(" -–—|,") or None,
                       "start_date": m.group(1), "end_date": m.group(2), "description": "",
                       "technologies": [], "achievements": []}
                items.append(cur)
            elif cur is not None:
                cur["description"] = (cur["description"] + " " + line).strip()
                cur["technologies"] = extract_skills(cur["description"])
            else:
                items.append(cur := {"company": None, "position": line, "start_date": None, "end_date": None,
                                     "description": "", "technologies": [], "achievements": []})
        return items

    @staticmethod
    def _education(lines: list[str]) -> list[dict]:
        out = []
        for line in lines:
            m = DATE_RANGE_RE.search(line)
            if any(w in line.lower() for w in EDU_WORDS) or m:
                out.append({"institution": re.sub(DATE_RANGE_RE, "", line).strip(" -–—|,") or line,
                            "degree": None, "field": None,
                            "start_date": m.group(1) if m else None, "end_date": m.group(2) if m else None})
        return out

    @staticmethod
    def _projects(lines: list[str]) -> list[dict]:
        out = []
        for line in lines:
            if line.startswith(("-", "•", "*")) and out:
                out[-1]["description"] = (out[-1]["description"] or "") + " " + line.lstrip("-•* ")
            else:
                out.append({"name": line[:120], "description": "", "technologies": [], "url": None})
        for p in out:
            p["technologies"] = extract_skills(f"{p['name']} {p['description']}")
        return out[:10]

    @staticmethod
    def _languages(lines: list[str]) -> list[dict]:
        out = []
        for line in lines:
            for lang in KNOWN_LANGS:
                if lang.lower() in line.lower():
                    lvl = LANG_LEVELS.search(line)
                    out.append({"language": lang, "level": lvl.group(0) if lvl else None})
        seen, uniq = set(), []
        for item in out:
            if item["language"] not in seen:
                seen.add(item["language"])
                uniq.append(item)
        return uniq
