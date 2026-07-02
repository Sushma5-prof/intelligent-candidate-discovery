"""
Hackathon Execution Plan, Step 1: Generate Synthetic Data (Offline).

The PRD suggests using an LLM to generate profiles. To keep this script
runnable with zero API keys / network access (and fully reproducible in
CI), we instead use a seeded procedural generator covering realistic role
titles, tenures, promotions, and skill sets across several tech tracks.
Swap `USE_LLM_GENERATION` + provide a GROQ_API_KEY if you want richer,
LLM-authored bios instead.

Run:
    python -m app.data.generate_synthetic_data
"""
from __future__ import annotations

import json
import random
from pathlib import Path

random.seed(42)

FIRST_NAMES = [
    "Aarav", "Maya", "Liam", "Sofia", "Noah", "Emma", "Kabir", "Zara", "Ethan", "Priya",
    "Lucas", "Ananya", "Mason", "Isla", "Ravi", "Chloe", "Arjun", "Grace", "Dev", "Nina",
    "Omar", "Lily", "Kenji", "Hana", "Marco", "Elena", "Yusuf", "Ivy", "Diego", "Amara",
]
LAST_NAMES = [
    "Sharma", "Patel", "Chen", "Garcia", "Kim", "Müller", "Silva", "Nguyen", "Kaur", "Rossi",
    "Johansson", "Okafor", "Tanaka", "Fischer", "Rodriguez", "Ali", "Novak", "Costa", "Park", "Singh",
]

TRACKS = {
    "frontend": {
        "titles": ["Frontend Engineer", "UI Engineer", "Senior Frontend Engineer", "Staff Frontend Engineer",
                   "Frontend Lead"],
        "skills": ["JavaScript", "React", "Next.js", "TypeScript", "CSS", "Vue", "GraphQL", "REST API"],
    },
    "backend": {
        "titles": ["Backend Engineer", "Software Engineer", "Senior Backend Engineer", "Staff Engineer",
                   "Backend Lead"],
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes", "REST API"],
    },
    "ml": {
        "titles": ["ML Engineer", "Data Scientist", "Senior ML Engineer", "Applied Scientist",
                   "ML Team Lead"],
        "skills": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "Pandas", "Spark", "AWS"],
    },
    "devops": {
        "titles": ["DevOps Engineer", "Site Reliability Engineer", "Senior DevOps Engineer",
                   "Infrastructure Lead", "Platform Engineer"],
        "skills": ["Kubernetes", "Docker", "Terraform", "AWS", "GCP", "Kafka", "Python"],
    },
    "fullstack": {
        "titles": ["Full Stack Engineer", "Software Engineer II", "Senior Full Stack Engineer",
                   "Full Stack Lead", "Founding Engineer"],
        "skills": ["JavaScript", "React", "Node.js", "Python", "PostgreSQL", "AWS", "GraphQL"],
    },
}

LOCATIONS = ["Bengaluru, IN", "San Francisco, US", "Berlin, DE", "London, UK", "Toronto, CA",
             "Singapore, SG", "Austin, US", "Amsterdam, NL", "Pune, IN", "Sydney, AU"]


def generate_candidate(idx: int) -> dict:
    track_name = random.choice(list(TRACKS.keys()))
    track = TRACKS[track_name]

    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    email = f"{name.lower().replace(' ', '.')}{idx}@example.com"
    location = random.choice(LOCATIONS)

    num_roles = random.randint(1, 5)
    roles = []
    for r in range(num_roles):
        title = random.choice(track["titles"])
        # Occasionally simulate extreme job-hopping to exercise the hop penalty
        duration = round(random.choice([0.4, 0.6, 0.8]) if random.random() < 0.12
                          else random.uniform(1.0, 4.5), 1)
        is_promotion = r > 0 and random.random() < 0.4
        roles.append({"title": title, "duration_years": duration, "is_promotion": is_promotion})

    explicit_skills = random.sample(track["skills"], k=min(len(track["skills"]), random.randint(3, 6)))
    total_years = round(sum(r["duration_years"] for r in roles), 1)

    headline = f"{roles[0]['title']} | {track_name.capitalize()} | {total_years}+ yrs"
    summary = (
        f"{name} is a {track_name} engineer with {total_years} years of experience across "
        f"{num_roles} role(s), specializing in {', '.join(explicit_skills[:4])}. "
        f"Most recently worked as {roles[0]['title']} based in {location}."
    )

    return {
        "id": f"cand_{idx:04d}",
        "name": name,
        "email": email,
        "location": location,
        "headline": headline,
        "summary": summary,
        "explicit_skills": explicit_skills,
        "roles": roles,
    }


def main(count: int = 500, out_path: str = None) -> None:
    out_path = out_path or str(Path(__file__).parent / "candidates.json")
    candidates = [generate_candidate(i) for i in range(count)]
    Path(out_path).write_text(json.dumps(candidates, indent=2))
    print(f"Generated {count} synthetic candidates -> {out_path}")


if __name__ == "__main__":
    main()
