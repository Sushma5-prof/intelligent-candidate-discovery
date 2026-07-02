"""
Phase A - Implicit Skill Mapping (PRD Sec. 2).

A candidate stating "React" implicitly signals "JavaScript". This is
intentionally a shallow, 1-degree graph (not transitive/recursive) to keep
inference explainable: every implicit tag can be traced back to exactly one
explicit skill the candidate actually listed.
"""
from typing import Dict, List, Set

# explicit_skill (lowercased) -> [implicit skills it signals]
SKILL_GRAPH: Dict[str, List[str]] = {
    "react": ["javascript", "html", "css"],
    "next.js": ["react", "javascript", "node.js"],
    "vue": ["javascript", "html", "css"],
    "angular": ["javascript", "typescript", "html", "css"],
    "typescript": ["javascript"],
    "node.js": ["javascript"],
    "django": ["python"],
    "flask": ["python"],
    "fastapi": ["python"],
    "pandas": ["python"],
    "pytorch": ["python", "machine learning"],
    "tensorflow": ["python", "machine learning"],
    "scikit-learn": ["python", "machine learning"],
    "spring boot": ["java"],
    "hibernate": ["java", "sql"],
    "rails": ["ruby"],
    "laravel": ["php"],
    ".net": ["c#"],
    "asp.net": ["c#", ".net"],
    "kubernetes": ["docker", "devops"],
    "docker": ["devops"],
    "terraform": ["devops", "cloud"],
    "airflow": ["python", "data engineering"],
    "spark": ["data engineering"],
    "kafka": ["data engineering", "distributed systems"],
    "postgresql": ["sql"],
    "mysql": ["sql"],
    "mongodb": ["nosql"],
    "redis": ["nosql"],
    "aws": ["cloud"],
    "gcp": ["cloud"],
    "azure": ["cloud"],
    "graphql": ["api design"],
    "rest api": ["api design"],
}


def expand_skills(explicit_skills: List[str]) -> Set[str]:
    """Return the union of explicit skills + their 1-degree implicit skills, lowercased."""
    normalized = {s.strip().lower() for s in explicit_skills if s.strip()}
    implicit: Set[str] = set()
    for skill in normalized:
        implicit.update(SKILL_GRAPH.get(skill, []))
    return normalized | implicit


def implicit_only(explicit_skills: List[str]) -> Set[str]:
    """Return only the *inferred* skills (excludes anything explicitly stated)."""
    normalized = {s.strip().lower() for s in explicit_skills if s.strip()}
    implicit: Set[str] = set()
    for skill in normalized:
        implicit.update(SKILL_GRAPH.get(skill, []))
    return implicit - normalized
