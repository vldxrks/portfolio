"""Skill vocabulary + alias normalisation (Postgres -> PostgreSQL, DRF -> Django REST Framework...)."""
import re

# canonical name -> aliases (lowercase)
SKILLS: dict[str, list[str]] = {
    "Python": ["py", "python3"],
    "Django": [],
    "Django REST Framework": ["drf", "django rest", "django rest framework"],
    "Flask": [],
    "FastAPI": ["fast api"],
    "PostgreSQL": ["postgres", "postgresql", "psql"],
    "MySQL": [],
    "SQLite": [],
    "MongoDB": ["mongo"],
    "Redis": [],
    "Celery": [],
    "Docker": ["docker compose", "docker-compose"],
    "Kubernetes": ["k8s"],
    "AWS": ["amazon web services"],
    "Git": [],
    "GitHub": [],
    "GitHub Actions": ["github actions"],
    "CI/CD": ["ci/cd", "ci cd", "cicd"],
    "Linux": [],
    "REST API": ["rest", "restful", "rest api", "rest apis", "restful api"],
    "GraphQL": [],
    "SQL": [],
    "JavaScript": ["js", "javascript", "ecmascript"],
    "TypeScript": ["ts"],
    "React": ["reactjs", "react.js"],
    "Node.js": ["node", "nodejs"],
    "HTML": ["html5"],
    "CSS": ["css3"],
    "Bootstrap": [],
    "Pytest": [],
    "Pandas": [],
    "NumPy": [],
    "Pygame": [],
    "C++": ["cpp"],
    "C#": ["csharp"],
    "Java": [],
    "Go": ["golang"],
    "PHP": [],
    "Pydantic": [],
    "SQLAlchemy": [],
    "RabbitMQ": [],
    "Nginx": [],
    "OOP": ["object-oriented programming", "object oriented programming", "ооп"],
    "Agile": ["scrum"],
    "UML": [],
    "Microservices": ["microservice"],
}

# loosely related technologies (used to flag "related" skills in matching)
RELATED_GROUPS = [
    {"Django", "Flask", "FastAPI"},
    {"PostgreSQL", "MySQL", "SQLite", "SQL"},
    {"Docker", "Kubernetes"},
    {"AWS", "Docker", "Kubernetes"},
    {"Celery", "RabbitMQ", "Redis"},
    {"JavaScript", "TypeScript", "React", "Node.js"},
]

_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canon, _aliases in SKILLS.items():
    _ALIAS_TO_CANONICAL[_canon.lower()] = _canon
    for _a in _aliases:
        _ALIAS_TO_CANONICAL[_a.lower()] = _canon


def _pattern(term: str) -> re.Pattern:
    return re.compile(r"(?<![\w+#])" + re.escape(term) + r"(?![\w+#])", re.IGNORECASE)


# very short / ambiguous aliases are only matched when written exactly like this
_AMBIGUOUS = {"py", "ts", "js", "go", "node", "rest"}
_PATTERNS = [(term, canon, _pattern(term)) for term, canon in _ALIAS_TO_CANONICAL.items()]


def normalize_skill(name: str) -> str:
    """Map a raw skill string to its canonical name (or return it stripped)."""
    cleaned = name.strip()
    return _ALIAS_TO_CANONICAL.get(cleaned.lower(), cleaned)


def extract_skills(text: str) -> list[str]:
    """Find known skills inside free text (resume or job description)."""
    found: dict[str, None] = {}
    for term, canon, pat in _PATTERNS:
        if term in _AMBIGUOUS and not re.search(r"\b" + re.escape(term) + r"\b", text):
            continue
        if pat.search(text):
            found[canon] = None
    return list(found)


def related_to(skill: str, have: set[str]) -> list[str]:
    out = set()
    for group in RELATED_GROUPS:
        if skill in group:
            out |= (group & have) - {skill}
    return sorted(out)
