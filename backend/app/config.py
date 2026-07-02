from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Embedding / Vector DB ---
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384  # bge-small output dim
    qdrant_collection: str = "candidates"

    # --- Ranking weights: FinalScore = a*Ssem + b*Simplicit + g*Svelocity - Phop ---
    weight_semantic: float = 0.5
    weight_implicit: float = 0.2
    weight_velocity: float = 0.3

    # --- Tier sizing (PRD Sec. 2 - 3-Tier Search Funnel) ---
    tier1_pool_size: int = 100
    tier3_top_n: int = 5

    # --- Summarization (Tier 3: "The Polish") ---
    groq_api_key: str | None = None
    groq_model: str = "llama3-8b-8192"

    # --- Synthetic data ---
    synthetic_candidate_count: int = 500
    data_path: str = "app/data/candidates.json"

    # --- CORS ---
    frontend_origin: str = "http://localhost:3000"


settings = Settings()
