"""Shared LLM helper (plain HTTP, OpenAI-compatible endpoint) (default model: openai/gpt-oss-20b).

Pick ONE provider by setting an env var:
  Groq (free tier):   export GROQ_API_KEY=...
  OpenRouter:         export OPENROUTER_API_KEY=...        (model id: openai/gpt-oss-20b or openai/gpt-oss-20b:free)
  Ollama (local):     export LLM_BASE_URL=http://localhost:11434/v1 LLM_API_KEY=ollama MODEL=gpt-oss:20b
Or override everything with LLM_BASE_URL / LLM_API_KEY / MODEL.
With no key at all, falls back to a deterministic MOCK (for wiring tests only, not for the real demo).
"""
import os, json, re

try:  # load GROQ_API_KEY etc. from a local .env file if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MODEL = os.environ.get("MODEL", "openai/gpt-oss-20b")

def _provider():
    if os.environ.get("LLM_API_KEY"):
        return os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1"), os.environ["LLM_API_KEY"]
    if os.environ.get("GROQ_API_KEY"):
        return "https://api.groq.com/openai/v1", os.environ["GROQ_API_KEY"]
    if os.environ.get("OPENROUTER_API_KEY"):
        return "https://openrouter.ai/api/v1", os.environ["OPENROUTER_API_KEY"]
    return None, None

BASE_URL, API_KEY = _provider()
USE_MOCK = API_KEY is None

def llm(system: str, user: str, mock=None, max_tokens=1500) -> str:
    # Plain HTTP via the standard library (no `openai` package, no compiled DLLs).
    # max_tokens is generous because gpt-oss is a reasoning model: thinking tokens count toward the limit.
    if USE_MOCK:
        if mock is None:
            raise RuntimeError("No API key set and no mock provided")
        return mock(user)
    import urllib.request, urllib.error, time
    payload = {"model": MODEL, "temperature": 0, "max_tokens": max_tokens,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json",
                 "User-Agent": "memguard-prototype/0.1"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"].get("content") or ""
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:300]
            if e.code == 429 and attempt < 3:      # rate limit: wait and retry
                time.sleep(4 * (attempt + 1))
                continue
            raise RuntimeError(f"LLM HTTP {e.code}: {body}")

def parse_json(text: str) -> dict:
    text = re.sub(r"```json|```", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"No JSON found in model output: {text[:200]!r}")
    return json.loads(m.group(0))