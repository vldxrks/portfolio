"""Deterministic, explainable resume <-> vacancy matching (no LLM needed for this)."""
from .skills import extract_skills, normalize_skill, related_to


class EmptyVacancy(Exception):
    pass


def collect_resume_skills(analysis_result: dict, resume_text: str) -> set[str]:
    skills: set[str] = set()
    s = analysis_result.get("skills", {})
    for group in s.values():
        for item in group:
            skills.add(normalize_skill(item))
    skills |= set(extract_skills(resume_text or ""))
    for exp in analysis_result.get("experience", []):
        skills |= {normalize_skill(t) for t in exp.get("technologies", [])}
    for pr in analysis_result.get("projects", []):
        skills |= {normalize_skill(t) for t in pr.get("technologies", [])}
    return {x for x in skills if x}


def match_resume_to_vacancy(analysis_result: dict, resume_text: str, vacancy_text: str) -> dict:
    if not vacancy_text or not vacancy_text.strip():
        raise EmptyVacancy("Job description is empty")
    required = extract_skills(vacancy_text)
    if not required:
        raise EmptyVacancy("No known skills were recognised in the job description")

    have = collect_resume_skills(analysis_result, resume_text)
    matched = [s for s in required if s in have]
    missing = [s for s in required if s not in have]
    related = {s: r for s in missing if (r := related_to(s, have))}
    score = round(100 * len(matched) / len(required))

    explanation = []
    if matched:
        explanation.append("Strong matches: " + ", ".join(matched) + ".")
    if missing:
        explanation.append("Not found in the resume: " + ", ".join(missing) + ".")
    for skill, rel in related.items():
        explanation.append(f"{skill} is missing, but you list related technology: {', '.join(rel)}.")
    explanation.append(
        "Score = share of recognised required skills found in the resume. "
        "It is a heuristic, not a prediction of hiring outcome."
    )
    return {
        "score": score,
        "required_skills": required,
        "matched_skills": matched,
        "missing_skills": missing,
        "related_skills": related,
        "explanation": " ".join(explanation),
    }
