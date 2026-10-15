#!/usr/bin/env python3
"""Generuje tracker.html z applications.json.

Użycie: python3 build_tracker.py [katalog_danych]   (domyślnie ~/Desktop/JobFinder)

Tylko biblioteka standardowa (działa na Pythonie 3.9+).
"""
import html
import json
import sys
from datetime import date, datetime
from pathlib import Path

STATUSES = [
    ("szkic", "Szkic"),
    ("do-recznej", "Do aplikowania ręcznie"),
    ("wyslane", "Wysłane"),
    ("odpowiedz", "Odpowiedź"),
    ("rozmowa", "Rozmowa"),
    ("oferta", "Oferta"),
    ("odrzucone", "Odrzucone"),
]
LABELS = dict(STATUSES)
FOLLOWUP_DAYS = 7


def load(data_dir):
    path = data_dir / "applications.json"
    if not path.exists():
        return {"applications": [], "seen_offers": []}
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("applications", [])
    data.setdefault("seen_offers", [])
    return data


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def needs_followup(app, today):
    if app.get("status") != "wyslane" or app.get("followup_done"):
        return False
    sent = parse_date(app.get("sent_date"))
    return sent is not None and (today - sent).days >= FOLLOWUP_DAYS


def esc(value):
    return html.escape(str(value or ""))


def row(app, today):
    status = app.get("status", "szkic")
    url = app.get("offer_url") or ""
    offer = f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(app.get("position"))}</a>' if url else esc(app.get("position"))
    contact = app.get("contact_email") or app.get("apply_url") or ""
    if app.get("contact_email"):
        contact_html = f'<a href="mailto:{esc(contact)}">{esc(contact)}</a>'
    elif contact:
        contact_html = f'<a href="{esc(contact)}" target="_blank" rel="noopener">formularz</a>'
    else:
        contact_html = "—"
    flag = '<span class="flag">follow-up</span>' if needs_followup(app, today) else ""
    return (
        f'<tr data-status="{esc(status)}">'
        f'<td class="nowrap">{esc(app.get("date"))}</td>'
        f'<td><strong>{esc(app.get("company"))}</strong></td>'
        f"<td>{offer}</td>"
        f'<td>{esc(app.get("source"))}</td>'
        f"<td>{contact_html}</td>"
        f'<td><span class="cv">{esc(app.get("cv_version"))}</span></td>'
        f'<td><span class="status s-{esc(status)}">{esc(LABELS.get(status, status))}</span>{flag}</td>'
        f'<td class="notes">{esc(app.get("notes"))}</td>'
        "</tr>"
    )


def render(data, today):
    apps = sorted(data["applications"], key=lambda a: a.get("date", ""), reverse=True)
    counts = {key: 0 for key, _ in STATUSES}
    for a in apps:
        counts[a.get("status", "szkic")] = counts.get(a.get("status", "szkic"), 0) + 1
    followups = sum(1 for a in apps if needs_followup(a, today))
    buttons = [f'<button class="chip active" data-filter="all">Wszystkie <b>{len(apps)}</b></button>']
    for key, label in STATUSES:
        if counts.get(key):
            buttons.append(f'<button class="chip" data-filter="{key}">{label} <b>{counts[key]}</b></button>')
    rows = "\n".join(row(a, today) for a in apps) or '<tr><td colspan="8" class="empty">Brak aplikacji — zaczynamy!</td></tr>'
    followup_note = f'<p class="alert">{followups} aplikacji czeka na follow-up (wysłane ≥ {FOLLOWUP_DAYS} dni temu, bez odpowiedzi).</p>' if followups else ""
    return TEMPLATE.format(
        updated=today.isoformat(),
        total=len(apps),
        buttons="\n".join(buttons),
        rows=rows,
        followup_note=followup_note,
    )


TEMPLATE = """<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JobFinder Tracker</title>
<style>
:root {{
  --bg: #f7f7f5; --surface: #ffffff; --text: #1d1d1b; --muted: #6b6b66; --border: #e3e3de;
  --accent: #2f5bd3; --warn-bg: #fff4d6; --warn: #8a5a00;
  --s-szkic: #8a8a84; --s-do-recznej: #b86e00; --s-wyslane: #2f5bd3; --s-odpowiedz: #6a4fc9;
  --s-rozmowa: #0f8a6a; --s-oferta: #138a2e; --s-odrzucone: #b3392f;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #161615; --surface: #1f1f1d; --text: #ececea; --muted: #a0a09a; --border: #33332f;
    --accent: #7b9cff; --warn-bg: #3a2f12; --warn: #f0c46a;
    --s-szkic: #a0a09a; --s-do-recznej: #f0a43a; --s-wyslane: #7b9cff; --s-odpowiedz: #a690ff;
    --s-rozmowa: #45c9a4; --s-oferta: #5fd17a; --s-odrzucone: #ff7a70;
  }}
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--text); font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
main {{ max-width: 1200px; margin: 0 auto; padding: 32px 16px; }}
h1 {{ margin: 0 0 4px; font-size: 26px; }}
.meta {{ color: var(--muted); margin: 0 0 20px; }}
.alert {{ background: var(--warn-bg); color: var(--warn); padding: 10px 14px; border-radius: 8px; }}
.filters {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; }}
.chip {{ border: 1px solid var(--border); background: var(--surface); color: var(--text); border-radius: 999px; padding: 6px 12px; cursor: pointer; font: inherit; }}
.chip.active {{ border-color: var(--accent); color: var(--accent); }}
.wrap {{ overflow-x: auto; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }}
table {{ width: 100%; border-collapse: collapse; min-width: 860px; }}
th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }}
th {{ font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }}
tr:last-child td {{ border-bottom: 0; }}
a {{ color: var(--accent); }}
.nowrap {{ white-space: nowrap; }}
.notes {{ color: var(--muted); max-width: 260px; }}
.cv {{ font-weight: 600; }}
.status {{ font-weight: 600; white-space: nowrap; }}
.s-szkic {{ color: var(--s-szkic); }} .s-do-recznej {{ color: var(--s-do-recznej); }} .s-wyslane {{ color: var(--s-wyslane); }}
.s-odpowiedz {{ color: var(--s-odpowiedz); }} .s-rozmowa {{ color: var(--s-rozmowa); }} .s-oferta {{ color: var(--s-oferta); }}
.s-odrzucone {{ color: var(--s-odrzucone); }}
.flag {{ display: inline-block; margin-left: 6px; font-size: 11px; padding: 1px 6px; border-radius: 4px; background: var(--warn-bg); color: var(--warn); }}
.empty {{ text-align: center; color: var(--muted); padding: 32px; }}
</style>
</head>
<body>
<main>
<h1>JobFinder — aplikacje</h1>
<p class="meta">Zaktualizowano {updated} · łącznie {total}</p>
{followup_note}
<div class="filters">
{buttons}
</div>
<div class="wrap">
<table>
<thead><tr><th>Data</th><th>Firma</th><th>Stanowisko</th><th>Źródło</th><th>Kontakt</th><th>CV</th><th>Status</th><th>Notatki</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>
</main>
<script>
document.querySelectorAll('.chip').forEach(function (chip) {{
  chip.addEventListener('click', function () {{
    document.querySelectorAll('.chip').forEach(function (c) {{ c.classList.remove('active'); }});
    chip.classList.add('active');
    var f = chip.dataset.filter;
    document.querySelectorAll('tbody tr[data-status]').forEach(function (tr) {{
      tr.style.display = (f === 'all' || tr.dataset.status === f) ? '' : 'none';
    }});
  }});
}});
</script>
</body>
</html>
"""


def main():
    data_dir = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "Desktop" / "JobFinder"
    data = load(data_dir)
    out = data_dir / "tracker.html"
    out.write_text(render(data, date.today()), encoding="utf-8")
    followups = [a.get("company") for a in data["applications"] if needs_followup(a, date.today())]
    print(f"Zapisano {out} ({len(data['applications'])} aplikacji)")
    if followups:
        print("Do follow-upu: " + ", ".join(followups))


if __name__ == "__main__":
    main()
