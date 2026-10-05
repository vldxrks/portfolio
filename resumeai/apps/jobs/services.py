from .matching import match_resume_to_vacancy
from .models import JobMatch


def run_match(user, resume, vacancy) -> JobMatch:
    analysis = resume.latest_analysis
    if analysis is None:
        raise ValueError("Analyze the resume first.")
    data = match_resume_to_vacancy(analysis.result, resume.extracted_text, f"{vacancy.title}\n{vacancy.description}")
    return JobMatch.objects.create(user=user, resume=resume, vacancy=vacancy, analysis=analysis, **data)
