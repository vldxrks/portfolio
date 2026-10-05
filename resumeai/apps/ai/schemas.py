"""Pydantic schemas: every AI answer must pass through these before it is saved."""
from typing import Literal

from pydantic import BaseModel, Field


class Candidate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[str] = []


class Skills(BaseModel):
    technical: list[str] = []
    tools: list[str] = []
    soft: list[str] = []


class Experience(BaseModel):
    company: str | None = None
    position: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    technologies: list[str] = []
    achievements: list[str] = []


class Education(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class Project(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = []
    url: str | None = None


class Language(BaseModel):
    language: str
    level: str | None = None


class Scores(BaseModel):
    structure: int = Field(ge=0, le=100)
    clarity: int = Field(ge=0, le=100)
    skills: int = Field(ge=0, le=100)
    experience: int = Field(ge=0, le=100)
    achievements: int = Field(ge=0, le=100)
    ats_readiness: int = Field(ge=0, le=100)

    @property
    def overall(self) -> int:
        vals = [self.structure, self.clarity, self.skills, self.experience, self.achievements, self.ats_readiness]
        return round(sum(vals) / len(vals))


class Recommendation(BaseModel):
    category: str
    priority: Literal["high", "medium", "low"]
    title: str
    description: str
    before: str | None = None  # weak phrase found in the CV
    suggested: str | None = None  # rewrite WITHOUT invented facts/numbers


class ResumeAnalysisSchema(BaseModel):
    language: str | None = None
    candidate: Candidate = Candidate()
    summary: str = ""
    skills: Skills = Skills()
    experience: list[Experience] = []
    education: list[Education] = []
    projects: list[Project] = []
    languages: list[Language] = []
    strengths: list[str] = []
    issues: list[str] = []
    scores: Scores
    recommendations: list[Recommendation] = []
