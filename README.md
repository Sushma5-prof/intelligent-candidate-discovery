# Intelligent Candidate Discovery is an AI-powered talent discovery engine that moves beyond rigid keyword matching to evaluate candidates based on implicit skill overlaps and true career momentum. 

Traditional applicant tracking systems measure where a candidate is right now. We built Kinetix to measure where a candidate is going.

## 🧠 Core Architecture
Built for sub-2.5 second latency, Kinetix uses a decoupled **Two-Stage Retrieval Pipeline**:
1. **The Net (Vector Search):** A high-speed Vector Database captures implicit semantic skill overlaps between a Job Description and candidate profiles.
2. **The Filter (Cross-Encoder):** A localized ONNX-compiled Cross-Encoder expertly reranks the top matches, evaluating true semantic fit against a proprietary **Career Velocity** metric.

## 🛠️ Tech Stack
* **Frontend:** Next.js (React), TailwindCSS
* **Backend:** FastAPI (Python)
* **AI/ML:** FastEmbed (Embeddings), ONNX (Reranking Cross-Encoder), Groq API (Explainability)
* **Database:** Vector DB (Qdrant/Milvus)

## ✨ Features
* **Semantic Discovery:** Finds hidden talent by matching inferred skills, not just exact keywords.
* **Trajectory Scoring:** Strictly encapsulated timeline data structures calculate a candidate's career velocity and promotion speed.
* **Explainability Dashboard:** Generates a 2-sentence AI justification for every ranked candidate.
* **Blind Audition Mode:** A single toggle to mathematically strip all PII (names, gender, etc.) to eliminate unconscious bias.

###[Check out the App](https://intelligent-candidate-discovery-pjkmqsiz3tzkkmanvcep4d.streamlit.app/)
