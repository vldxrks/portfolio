from apps.resumes.models import Resume

from .analysis import create_analysis, file_sha256, process_upload


def create_resume(user, uploaded_file, file_type: str, title: str = "") -> Resume:
    resume = Resume(
        user=user,
        title=title.strip() or uploaded_file.name.rsplit(".", 1)[0][:200],
        original_filename=uploaded_file.name[:255],
        file_type=file_type,
        file_size=uploaded_file.size,
        file_hash=file_sha256(uploaded_file),
    )
    resume.file = uploaded_file
    resume.save()
    process_upload(resume)
    return resume


def create_resume_and_analyze(user, uploaded_file, file_type, title=""):
    resume = create_resume(user, uploaded_file, file_type, title)
    analysis = create_analysis(resume) if resume.status == Resume.Status.COMPLETED else None
    return resume, analysis
