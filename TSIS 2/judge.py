"""
TSIS 2: Judge Agent — compares PRD vs code submission and outputs a JSON compliance report.
Supports Google Gemini (GOOGLE_API_KEY) or OpenAI (OPENAI_API_KEY) via .env.
Use --dry-run to test the pipeline without API (mock response).
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Load .env; if missing, try .env.example (e.g. when key is stored there)
try:
    from dotenv import load_dotenv
    base_dir = Path(__file__).resolve().parent
    if (base_dir / ".env").exists():
        load_dotenv(base_dir / ".env")
    else:
        load_dotenv(base_dir / ".env.example")
except ImportError:
    pass

def load_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8")

def extract_json(text: str) -> str:
    """Take first {...} block from model output (handles markdown code fences)."""
    text = text.strip()
    # Remove optional markdown code block
    if "```json" in text:
        start = text.find("```json") + len("```json")
        end = text.find("```", start)
        if end == -1:
            end = len(text)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end == -1:
            end = len(text)
        text = text[start:end].strip()
    # Find first { ... } pair
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]


def _run_gemini(api_key: str, system_prompt: str, prd: str, code: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
    )
    user_content = f"""Evaluate the following code submission against the PRD.

=== PRD (Product Requirements Document) ===
{prd}

=== Code submission ===
```python
{code}
```

Output ONLY the compliance report as a single JSON object (no other text)."""
    response = model.generate_content(user_content)
    if not response or not response.text:
        raise RuntimeError("Empty response from Gemini")
    return response.text.strip()


def _run_openai(api_key: str, system_prompt: str, prd: str, code: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    user_content = f"""Evaluate the following code submission against the PRD.

=== PRD (Product Requirements Document) ===
{prd}

=== Code submission ===
```python
{code}
```

Output ONLY the compliance report as a single JSON object (no other text)."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    content = resp.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from OpenAI")
    return content.strip()


def main():
    base = Path(__file__).resolve().parent
    prd_path = base / "prd.txt"
    code_path = base / "code_submission.py"
    system_prompt_path = base / "system_prompt.txt"
    out_path = base / "compliance_report.json"

    prd = load_file(str(prd_path))
    code = load_file(str(code_path))
    system_prompt = load_file(str(system_prompt_path))

    openai_key = os.environ.get("OPENAI_API_KEY")
    google_key = os.environ.get("GOOGLE_API_KEY")
    # Debug: ensure key looks real (OpenAI keys usually start with sk-)
    if openai_key and (openai_key.startswith("your_") or "here" in openai_key.lower()):
        print("Error: OPENAI_API_KEY in .env.example looks like a placeholder. Replace with your real key.", file=sys.stderr)
        sys.exit(1)
    if openai_key:
        raw = _run_openai(openai_key, system_prompt, prd, code)
    elif google_key:
        raw = _run_gemini(google_key, system_prompt, prd, code)
    else:
        print("Error: set OPENAI_API_KEY or GOOGLE_API_KEY in .env or environment.", file=sys.stderr)
        sys.exit(1)
    json_str = extract_json(raw)
    try:
        report = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error: could not parse JSON from model output: {e}", file=sys.stderr)
        print("Raw output:", raw[:500], file=sys.stderr)
        sys.exit(1)

    # Ensure required keys exist
    for key in ("compliance_score", "status", "audit_log", "security_check"):
        if key not in report:
            print(f"Warning: missing key '{key}' in report", file=sys.stderr)

    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Compliance report written to: {out_path}")

if __name__ == "__main__":
    main()
