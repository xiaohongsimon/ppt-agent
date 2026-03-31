from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "claude-sonnet-4-5-20250514"
    vlm_model: str = "claude-sonnet-4-5-20250514"
    output_dir: str = "./output"

    class Config:
        env_file = ".env"


settings = Settings()
