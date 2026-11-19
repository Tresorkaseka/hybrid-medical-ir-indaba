#!/usr/bin/env python3
"""Génère la fiche de vérification de la vérité terrain âge/sexe (HTML, puis PDF avec Chrome).

Chaque ligne montre le début du texte TREC, avec les citations qui justifient l'étiquette en
surbrillance, pour qu'un relecteur contrôle en quelques secondes que l'âge et le sexe retenus sont
bien ceux du PATIENT.

Entrées : experiments/exp1_trec_ct/gold/query_demographics_gold.csv, data/processed/queries_*.jsonl
Sortie  : docs/revue_verite_terrain.html
"""
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOLD_PATH = ROOT / "experiments/exp1_trec_ct/gold/query_demographics_gold.csv"
OUTPUT = ROOT / "docs/revue_verite_terrain.html"
UNITS_FR = {"Years": "ans", "Months": "mois", "Weeks": "semaines", "Days": "jours"}
SEX_FR = {"Male": "Homme", "Female": "Femme"}
MIN_CONTEXT, MAX_CONTEXT, TAIL = 200, 420, 60

CSS = """
@page{size:A4;margin:14mm 12mm}
body{font-family:"Instrument Sans",sans-serif;font-size:8.6pt;line-height:1.38;color:#1B1F1D;margin:0}
h1{font-family:"Newsreader",serif;font-weight:500;font-size:17pt;margin:0 0 3mm}
h2{font-size:10.5pt;margin:6mm 0 2mm;color:#1E5C47}
p{margin:0 0 2mm}
table{border-collapse:collapse;width:100%}
th{text-align:left;border-top:1.2px solid #1B1F1D;border-bottom:.6px solid #1B1F1D;padding:1.4mm 1.6mm;font-weight:600}
td{border-bottom:.4px solid #D9D6CC;padding:1.3mm 1.6mm;vertical-align:top}
tr{break-inside:avoid}
mark{background:#CFE6D9;padding:0 .5mm;border-radius:1px}
.id{white-space:nowrap;font-weight:600}
.box{width:8mm;text-align:center}
.flag td{background:#FBF1E3}
.note{background:#EEF3EF;padding:2.5mm 3.5mm;margin:0 0 3mm}
"""


def label_text(row: dict) -> tuple[str, str]:
    age = f"{row['age_value']} {UNITS_FR[row['age_unit']]}"
    sex = SEX_FR[row["sex"]] + (" (par pronom)" if row["sex_basis"] == "pronoun" else "")
    return age, sex


def highlighted_excerpt(text: str, evidences: list[str]) -> str:
    spans = sorted((text.find(e), text.find(e) + len(e)) for e in evidences)
    merged: list[list[int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    stop = min(len(text), max(MIN_CONTEXT, merged[-1][1] + TAIL), MAX_CONTEXT)
    out, cursor = [], 0
    for start, end in merged:
        out.append(html.escape(text[cursor:start]))
        out.append(f"<mark>{html.escape(text[start:end])}</mark>")
        cursor = end
    out.append(html.escape(text[cursor:stop]))
    return "".join(out).strip() + ("…" if stop < len(text) else "")


def is_priority(row: dict) -> bool:
    return row["sex_basis"] == "pronoun"


def table_rows(rows: list[dict], texts: dict) -> str:
    lines = []
    for row in rows:
        text = texts[(int(row["year"]), row["query_id"])]
        age, sex = label_text(row)
        excerpt = highlighted_excerpt(text, [row["age_evidence"], row["sex_evidence"]])
        css = ' class="flag"' if is_priority(row) else ""
        lines.append(
            f'<tr{css}><td class="id">{row["year"]} n°{row["query_id"]}</td><td>{excerpt}</td>'
            f'<td>{age}</td><td>{sex}</td><td class="box">☐</td></tr>'
        )
    return "\n".join(lines)


def main() -> None:
    rows = list(csv.DictReader(open(GOLD_PATH, encoding="utf-8", newline="")))
    texts = {}
    for year in (2021, 2022):
        for line in open(ROOT / f"data/processed/queries_{year}.jsonl", encoding="utf-8"):
            query = json.loads(line)
            texts[(year, query["query_id"])] = query["text"]
    priority = [r for r in rows if is_priority(r)]
    labelers = ", ".join(sorted({r["labeler"] for r in rows}))
    statuses = ", ".join(sorted({r["verification"] for r in rows}))
    head = "<tr><th>Requête</th><th>Début du texte TREC (citation en vert)</th><th>Âge retenu</th><th>Sexe retenu</th><th>OK</th></tr>"
    page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Vérification de la vérité terrain</title>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:wght@500&family=Instrument+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<h1>Vérification de la vérité terrain : âge et sexe des 125 requêtes</h1>
<div class="note"><p><strong>Ce qu'il faut vérifier.</strong> Pour chaque ligne, l'âge et le sexe retenus sont-ils ceux du <strong>patient</strong>
(et pas d'un proche : mère, mari, parent) ? Les citations surlignées sont copiées mot pour mot du texte TREC ; un test automatique
a déjà confirmé qu'elles existent et qu'elles correspondent au sexe indiqué. Reste le sens, que seul un lecteur peut juger.</p>
<p><strong>Cases fond orangé</strong> : sexe déduit des pronoms (« he », « her »), à regarder en priorité.
Dans la requête 2022 n°45, la phrase parle aussi d'une « 39-year-old woman » : c'est la <em>mère</em>, pas la patiente. Dans la 2021 n°14, une « Daughter » (fille) est mentionnée : la citation retenue décrit bien la patiente.</p>
<p>Étiquetage : <strong>{labelers}</strong>. Statut de vérification : <strong>{statuses}</strong>.</p></div>
<h2>À regarder en priorité ({len(priority)} lignes)</h2>
<table>{head}{table_rows(priority, texts)}</table>
<h2>Les {len(rows)} requêtes</h2>
<table>{head}{table_rows(rows, texts)}</table>
</body></html>"""
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"écrit {OUTPUT}")


if __name__ == "__main__":
    main()
