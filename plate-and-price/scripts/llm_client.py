"""Optional LLM calls (Claude or OpenAI) with no SDK dependency.

Keys come from the environment or ROOT/.env: ANTHROPIC_API_KEY, OPENAI_API_KEY.
Models are overridable: CLAUDE_MODEL (default claude-sonnet-5-5), OPENAI_MODEL (default gpt-4.1).
Provider is LLM_PROVIDER (anthropic|openai, default: whichever key exists, Claude first).

    from llm_client import complete
    text = complete("Translate to Spanish: ...", system="You translate cooking captions.")

CLI: python llm_client.py "your prompt" [--provider openai]
"""
import argparse
import json
import os
import urllib.request

from common import load_env

load_env()


def _post(url, headers, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def pick_provider(provider=None):
    provider = provider or os.environ.get("LLM_PROVIDER")
    if provider:
        return provider
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    raise RuntimeError("No LLM key: set ANTHROPIC_API_KEY or OPENAI_API_KEY in the environment or .env")


def complete(prompt, system="", provider=None, model=None, max_tokens=2000):
    provider = pick_provider(provider)
    if provider == "anthropic":
        r = _post("https://api.anthropic.com/v1/messages",
                  {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                  {"model": model or os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"), "max_tokens": max_tokens,
                   "system": system, "messages": [{"role": "user", "content": prompt}]})
        return "".join(b["text"] for b in r["content"] if b["type"] == "text")
    if provider == "openai":
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        r = _post("https://api.openai.com/v1/chat/completions",
                  {"authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
                  {"model": model or os.environ.get("OPENAI_MODEL", "gpt-4.1"), "messages": msgs})
        return r["choices"][0]["message"]["content"]
    raise ValueError(f"unknown provider {provider}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--provider")
    ap.add_argument("--model")
    a = ap.parse_args()
    print(complete(a.prompt, provider=a.provider, model=a.model))
