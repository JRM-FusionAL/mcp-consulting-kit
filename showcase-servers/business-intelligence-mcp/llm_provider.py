import os
from abc import ABC, abstractmethod
import anthropic
import requests

class LLMProvider(ABC):
    @abstractmethod
    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        ...

SQL_PROMPT = """You are a SQL generator. Convert the user's request into a single SQL query.

Natural language request:
{query}

Schema hint (may be empty):
{schema}

Return ONLY the SQL query, no explanation, no markdown, no backticks."""


class ClaudeProvider(LLMProvider):
    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        prompt = SQL_PROMPT.format(query=nl_query, schema=schema_hint or "N/A")
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()


class LocalProvider(LLMProvider):
    """Uses llama-server (Christopher's local model) for SQL generation.
    Zero API cost. Start llama-server before using the BI server.
    """
    def __init__(self) -> None:
        self.url = os.getenv("LOCAL_LLM_URL", "http://localhost:8080/v1/chat/completions")
        self.model = os.getenv("LOCAL_LLM_MODEL", "local")

    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        prompt = SQL_PROMPT.format(query=nl_query, schema=schema_hint or "N/A")
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
                "temperature": 0.1,
                "stop": ["```", ";;\n", "\n\n"],
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


class RuleBasedProvider(LLMProvider):
    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        q = nl_query.lower()
        if "top" in q and "customers" in q and "revenue" in q:
            return "SELECT customer_id, name, revenue FROM customers ORDER BY revenue DESC LIMIT 10;"
        raise ValueError("Rule-based provider cannot handle this query. Set LLM_PROVIDER=local or claude.")


def get_llm_provider() -> LLMProvider:
    provider = os.getenv("LLM_PROVIDER", "claude").lower()
    if provider == "claude":
        return ClaudeProvider()
    if provider == "local":
        return LocalProvider()
    if provider == "rule":
        return RuleBasedProvider()
    return ClaudeProvider()
