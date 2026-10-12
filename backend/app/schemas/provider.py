from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    name: str
    kind: str = "openai"  # "openai" (OpenAI-compatible) | "ollama" | "claude"
    base_url: str = ""
    api_key: str = ""
    model: str = ""


class ProviderRead(BaseModel):
    id: int
    name: str
    kind: str
    model: str
    configured: bool = Field(default=True)
