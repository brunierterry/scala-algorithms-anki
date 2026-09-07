#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import genanki
from jsonschema import validate
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers.jvm import ScalaLexer

ROOT = Path(__file__).resolve().parents[1]
DECK_PATH = ROOT / "data" / "deck.json"
CARDS_DIR = ROOT / "data" / "cards"
DECK_SCHEMA_PATH = ROOT / "schema" / "deck.schema.json"
CARDS_SCHEMA_PATH = ROOT / "schema" / "cards.schema.json"
DEFAULT_OUTPUT = ROOT / "dist" / "scala-algorithms-anki.apkg"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_source() -> tuple[dict, list[dict]]:
    deck_data = load_json(DECK_PATH)
    deck_schema = load_json(DECK_SCHEMA_PATH)
    cards_schema = load_json(CARDS_SCHEMA_PATH)

    validate(instance=deck_data, schema=deck_schema)

    cards: list[dict] = []
    source_files = sorted(CARDS_DIR.glob("*.json"))
    if not source_files:
        raise ValueError(f"No card source files found in {CARDS_DIR}")

    for source_file in source_files:
        source_cards = load_json(source_file)
        validate(instance=source_cards, schema=cards_schema)
        cards.extend(source_cards)

    ids = [card["id"] for card in cards]
    if len(ids) != len(set(ids)):
        duplicate_ids = sorted({card_id for card_id in ids if ids.count(card_id) > 1})
        raise ValueError(f"Duplicate card ids detected: {duplicate_ids}")

    return deck_data, cards


def highlight_scala(code: str) -> str:
    return highlight(code, ScalaLexer(), HtmlFormatter(cssclass="codehilite"))


def paragraph(text: str) -> str:
    return f'<div class="paragraph">{html.escape(text)}</div>'


def render_answer(answer: dict) -> str:
    parts: list[str] = []

    if reflex := answer.get("reflex"):
        parts.append('<div class="reflex-label">Réflexe</div>')
        parts.append(f'<div class="reflex">{html.escape(reflex)}</div>')

    if template := answer.get("template"):
        parts.append('<div class="section-title">Template</div>')
        parts.append(highlight_scala(template))

    if code := answer.get("code"):
        parts.append(highlight_scala(code))

    if bullets := answer.get("bullets"):
        parts.append('<ul class="bullets">')
        parts.extend(f'<li>{html.escape(item)}</li>' for item in bullets)
        parts.append("</ul>")

    if example := answer.get("example"):
        parts.append('<div class="section-title">Exemple réel</div>')
        if prompt := example.get("prompt"):
            parts.append(paragraph(prompt))
        if example_code := example.get("code"):
            parts.append(highlight_scala(example_code))

    if note := answer.get("note"):
        parts.append(f'<div class="note">{html.escape(note)}</div>')

    return "\n".join(parts)


class StableNote(genanki.Note):
    def __init__(self, card_id: str, *args, **kwargs):
        self.card_id = card_id
        super().__init__(*args, **kwargs)

    @property
    def guid(self):
        return genanki.guid_for("scala-algorithms-anki", self.card_id)


def build(output: Path) -> None:
    deck_data, cards = load_source()

    pygments_css = HtmlFormatter().get_style_defs(".codehilite")
    css = f"""
.card {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 18px;
  line-height: 1.45;
  text-align: left;
  color: #202124;
  background: #ffffff;
}}
.question {{ font-size: 21px; font-weight: 650; margin-bottom: 14px; }}
.card-type {{ font-size: 11px; text-transform: uppercase; letter-spacing: .08em; opacity: .55; margin-bottom: 8px; }}
.reflex-label, .section-title {{ font-size: 12px; text-transform: uppercase; letter-spacing: .08em; opacity: .6; margin-top: 14px; margin-bottom: 4px; }}
.reflex {{ font-weight: 650; margin-bottom: 10px; }}
.paragraph {{ margin: 8px 0 10px; }}
.note {{ margin-top: 12px; padding: 8px 10px; border-left: 3px solid #9aa0a6; font-size: 15px; }}
.bullets {{ margin-top: 8px; }}
.codehilite {{ overflow-x: auto; margin: 8px 0 12px; }}
.codehilite pre {{
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f6f8fa;
  font-family: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 14px;
  line-height: 1.42;
  white-space: pre;
}}
hr#answer {{ margin: 16px 0; border: 0; border-top: 1px solid #dadce0; }}
{pygments_css}

.nightMode .card {{ color: #e8eaed; background: #202124; }}
.nightMode .codehilite pre {{ background: #292a2d; }}
"""

    deck_cfg = deck_data["deck"]
    model = genanki.Model(
        deck_cfg["model_id"],
        "Scala Algorithms — Reflex + Example",
        fields=[
            {"name": "CardId"},
            {"name": "CardType"},
            {"name": "Question"},
            {"name": "FrontCode"},
            {"name": "Answer"},
        ],
        templates=[{
            "name": "Card",
            "qfmt": '<div class="card-type">{{CardType}}</div><div class="question">{{Question}}</div>{{FrontCode}}',
            "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
        }],
        css=css,
        sort_field_index=0,
    )

    deck = genanki.Deck(deck_cfg["deck_id"], deck_cfg["name"])

    for card in cards:
        front_code_html = highlight_scala(card["front_code"]) if card.get("front_code") else ""
        note = StableNote(
            card_id=card["id"],
            model=model,
            fields=[
                html.escape(card["id"]),
                html.escape(card["type"]),
                html.escape(card["question"]),
                front_code_html,
                render_answer(card["answer"]),
            ],
            tags=card["tags"],
        )
        deck.add_note(note)

    output.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(output))
    print(f"Built {len(cards)} cards -> {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Scala algorithms Anki deck from JSON sources.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
