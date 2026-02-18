import os
from abc import ABC, abstractmethod
from typing import Any
import anthropic

class LLMProvider(ABC):
    @abstractmethod
    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        ...

class ClaudeProvider(LLMProvider):
    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        prompt = f"""
You are a SQL generator. Convert the user's request into a single SQL query.

Natural language request:
{nl_query}

Schema hint (may be empty):
{schema_hint or "N/A"}

Return ONLY the SQL, no explanation.
"""
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        content = msg.content[0].text.strip()
        return content

class RuleBasedProvider(LLMProvider):
    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        # Extremely simple fallback for common patterns
        q = nl_query.lower()
        if "top" in q and "customers" in q and "revenue" in q:
            return "SELECT customer_id, name, revenue FROM customers ORDER BY revenue DESC LIMIT 10;"
        # Fallback: very naive
        raise ValueError("Rule-based provider cannot handle this query")

def get_llm_provider() -> LLMProvider:
    provider = os.getenv("LLM_PROVIDER", "claude").lower()
    if provider == "claude":
        return ClaudeProvider()
    if provider == "local":
        # Placeholder for your future local model
        raise NotImplementedError("Local provider not implemented yet")
    if provider == "rule":
        return RuleBasedProvider()
    return ClaudeProvider()
