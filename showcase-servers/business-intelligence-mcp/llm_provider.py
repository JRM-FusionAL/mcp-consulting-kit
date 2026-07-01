import os
from abc import ABC, abstractmethod
import anthropic
import openai
import requests

class LLMProvider(ABC):
    @abstractmethod
    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        ...

DEFAULT_SCHEMA = """
Tables available (SQLite):

services(id INTEGER, name TEXT, port INTEGER, language TEXT, framework TEXT, status TEXT, description TEXT)
integrations(id INTEGER, source_service TEXT, target_service TEXT, protocol TEXT, description TEXT)

Use only these tables. Do not use information_schema or pg_ system tables.
""".strip()

SQL_PROMPT = """You are a SQL generator for a SQLite database. Convert the user's request into a single valid SQLite SELECT query.

Natural language request:
{query}

Schema:
{schema}

Rules:
- SQLite syntax only (no ILIKE, no information_schema, no pg_ tables)
- Return ONLY the SQL query, no explanation, no markdown, no backticks
- Use only the tables listed in the schema above"""


class ClaudeProvider(LLMProvider):
    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        prompt = SQL_PROMPT.format(query=nl_query, schema=schema_hint or DEFAULT_SCHEMA)
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
        prompt = SQL_PROMPT.format(query=nl_query, schema=schema_hint or DEFAULT_SCHEMA)
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


class OpenAICompatProvider(LLMProvider):
    """OpenAI-compatible provider — works with OpenRouter, local llama-server, or any OAI-compat endpoint.

    Env vars (same names as fusional-orch brain):
        LLM_BASE_URL  — e.g. https://openrouter.ai/api/v1
        LLM_API_KEY   — provider API key
        LLM_MODEL     — e.g. meta-llama/llama-3.3-70b-instruct
    """

    def __init__(self) -> None:
        api_key = os.environ.get("LLM_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_API_KEY not set")
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        )
        self.model = os.environ.get("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct")

    def generate_sql(self, nl_query: str, schema_hint: str | None = None) -> str:
        prompt = SQL_PROMPT.format(query=nl_query, schema=schema_hint or DEFAULT_SCHEMA)
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=512,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()


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
    if provider in ("openai", "openrouter", "openai_compat"):
        return OpenAICompatProvider()
    if provider == "local":
        return LocalProvider()
    if provider == "rule":
        return RuleBasedProvider()
    return ClaudeProvider()
