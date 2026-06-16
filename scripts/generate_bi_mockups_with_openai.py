from __future__ import annotations

import base64
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_FILE = ROOT / "powerbi_notes" / "image_prompts.md"
OUTPUT_DIR = ROOT / "outputs" / "bi_mockups"


def slugify_title(title: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", title.strip())
    return cleaned[:50] or "dashboard_page"


def parse_prompts(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_title and current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line.removeprefix("## ").strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)

    if current_title and current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return [(title, prompt) for title, prompt in sections if prompt]


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY is not set. In Windows PowerShell run: "
            '$env:OPENAI_API_KEY="你的key". If unavailable, use powerbi_notes/image_prompts.md manually.'
        )

    if not PROMPT_FILE.exists():
        raise SystemExit("powerbi_notes/image_prompts.md does not exist. Generate the Power BI plan first.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("Missing dependency: pip install openai") from exc

    prompts = parse_prompts(PROMPT_FILE.read_text(encoding="utf-8"))
    if not prompts:
        raise SystemExit("No image prompts found. Use headings like '## page_01_产品总览'.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=api_key)

    for index, (title, prompt) in enumerate(prompts, start=1):
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1536x1024",
        )
        image_base64 = result.data[0].b64_json
        if not image_base64:
            raise SystemExit(f"No image returned for {title}.")
        filename = f"page_{index:02d}_{slugify_title(title)}.png"
        (OUTPUT_DIR / filename).write_bytes(base64.b64decode(image_base64))
        print(f"Generated {OUTPUT_DIR / filename}")


if __name__ == "__main__":
    main()
