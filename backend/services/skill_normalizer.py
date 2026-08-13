"""
backend/services/skill_normalizer.py — Skill Normalization Layer

Normalizes technical skills and tools to standard canonical forms without
aggressive over-matching or semantic distortion.
Preserves strict distinctness (e.g. SQL != PostgreSQL, Java != JavaScript, C != C++).
"""

import re
from typing import Dict, Set

# Canonical mapping for common technical terms (lowercase -> canonical)
SKILL_CANONICAL_MAP: Dict[str, str] = {
    "python": "Python",
    "py": "Python",
    "c++": "C++",
    "c plus plus": "C++",
    "cpp": "C++",
    "c#": "C#",
    "c sharp": "C#",
    "csharp": "C#",
    ".net": ".NET",
    "dotnet": ".NET",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "node": "Node.js",
    "react.js": "React.js",
    "reactjs": "React.js",
    "react js": "React.js",
    "react": "React.js",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud platform": "GCP",
    "google cloud": "GCP",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "docker": "Docker",
    "fastapi": "FastAPI",
    "express.js": "Express.js",
    "expressjs": "Express.js",
    "express": "Express.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "vue": "Vue.js",
    "sql": "SQL",
    "nosql": "NoSQL",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "tailwindcss": "TailwindCSS",
    "tailwind": "TailwindCSS",
    "bootstrap": "Bootstrap",
    "redux": "Redux",
    "graphql": "GraphQL",
    "rest": "REST API",
    "restful": "REST API",
    "rest api": "REST API",
    "grpc": "gRPC",
    "kafka": "Apache Kafka",
    "rabbitmq": "RabbitMQ",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "linux": "Linux",
    "unix": "Unix",
    "bash": "Bash",
    "shell": "Shell",
    "powershell": "PowerShell",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "github actions": "GitHub Actions",
    "jenkins": "Jenkins",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "keras": "Keras",
    "opencv": "OpenCV",
    "nlp": "NLP",
    "spacy": "spaCy",
    "nltk": "NLTK",
    "java": "Java",
    "golang": "Go",
    "go": "Go",
    "rust": "Rust",
    "c": "C",
    "ruby": "Ruby",
    "rails": "Ruby on Rails",
    "ruby on rails": "Ruby on Rails",
    "php": "PHP",
    "laravel": "Laravel",
    "django": "Django",
    "flask": "Flask",
}


def normalize_skill_name(skill: str) -> str:
    """
    Normalize a skill string to its canonical representation if known.
    Otherwise returns trimmed original string.
    Preserves exact terms: C++, C#, .NET, Node.js, React.js, std::vector<T>.
    """
    if not skill:
        return ""

    clean = skill.strip()
    clean_lower = clean.lower()

    if clean_lower in SKILL_CANONICAL_MAP:
        return SKILL_CANONICAL_MAP[clean_lower]

    return clean
