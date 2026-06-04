#!/usr/bin/env python3
"""Verifica URLs em sitemap(s) do Radar de Preços e identifica erros HTTP.

O script lê sitemap.xml como índice ou urlset, expande sitemaps filhos e testa cada URL
com requisições GET leves. Gera relatórios em JSON e Markdown em reports/.
"""
from __future__ import annotations

import concurrent.futures as futures
import json
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
UA = "RadarDePrecos-SitemapAudit/1.0 (+https://radardeprecos.github.io/)"
TIMEOUT = 20


@dataclass
class UrlCheck:
    url: str
    source_sitemap: str
    status_code: int | None
    ok: bool
    final_url: str | None
    error: str | None
    elapsed_ms: int


def parse_xml(path: Path) -> ET.Element:
    return ET.fromstring(path.read_text(encoding="utf-8"))


def local_path_for_sitemap(loc: str) -> Path | None:
    base = "https://radardeprecos.github.io/"
    if not loc.startswith(base):
        return None
    rel = loc.removeprefix(base)
    p = ROOT / rel
    return p if p.exists() else None


def collect_urls(sitemap_path: Path) -> list[tuple[str, str]]:
    root = parse_xml(sitemap_path)
    tag = root.tag.split("}", 1)[-1]
    urls: list[tuple[str, str]] = []
    if tag == "sitemapindex":
        for loc_el in root.findall("sm:sitemap/sm:loc", NS):
            loc = (loc_el.text or "").strip()
            child = local_path_for_sitemap(loc)
            if child:
                urls.extend(collect_urls(child))
            else:
                urls.append((loc, sitemap_path.name + " (sitemap filho indisponível localmente)"))
    elif tag == "urlset":
        for loc_el in root.findall("sm:url/sm:loc", NS):
            loc = (loc_el.text or "").strip()
            if loc:
                urls.append((loc, sitemap_path.name))
    return urls


def check_one(item: tuple[str, str]) -> UrlCheck:
    url, source = item
    start = time.monotonic()
    try:
        # GET é usado no GitHub Pages porque HEAD pode ser menos representativo em alguns cenários.
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True, stream=True)
        # consumir pouco e fechar a conexão
        try:
            next(resp.iter_content(chunk_size=128), b"")
        except StopIteration:
            pass
        elapsed = int((time.monotonic() - start) * 1000)
        return UrlCheck(
            url=url,
            source_sitemap=source,
            status_code=resp.status_code,
            ok=200 <= resp.status_code < 400,
            final_url=resp.url,
            error=None,
            elapsed_ms=elapsed,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = int((time.monotonic() - start) * 1000)
        return UrlCheck(url=url, source_sitemap=source, status_code=None, ok=False, final_url=None, error=repr(exc), elapsed_ms=elapsed)


def main() -> int:
    sitemap_index = ROOT / "sitemap.xml"
    url_items = collect_urls(sitemap_index)
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    duplicates = 0
    for url, source in url_items:
        if url in seen:
            duplicates += 1
            continue
        seen.add(url)
        deduped.append((url, source))

    with futures.ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(check_one, deduped))

    bad = [r for r in results if not r.ok]
    by_status: dict[str, int] = {}
    for r in results:
        key = str(r.status_code) if r.status_code is not None else "erro"
        by_status[key] = by_status.get(key, 0) + 1

    payload = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_urls_raw": len(url_items),
        "total_urls_unique": len(deduped),
        "duplicates_removed_for_check": duplicates,
        "status_counts": by_status,
        "bad_count": len(bad),
        "bad_urls": [asdict(r) for r in bad],
        "all_results": [asdict(r) for r in results],
    }
    (REPORTS / "sitemap_audit.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Auditoria de Sitemap — Radar de Preços",
        "",
        f"Verificação em UTC: `{payload['checked_at']}`.",
        "",
        f"Foram analisadas **{len(deduped)} URLs únicas** declaradas nos sitemaps, com **{len(bad)} URLs problemáticas**.",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| URLs brutas nos sitemaps | {len(url_items)} |",
        f"| URLs únicas testadas | {len(deduped)} |",
        f"| Duplicatas ignoradas no teste | {duplicates} |",
        f"| URLs com erro/fora de 2xx-3xx | {len(bad)} |",
        "",
        "## Distribuição por status HTTP",
        "",
        "| Status | Quantidade |",
        "|---|---:|",
    ]
    for status, count in sorted(by_status.items(), key=lambda kv: (kv[0] == "erro", kv[0])):
        lines.append(f"| {status} | {count} |")
    lines += ["", "## URLs problemáticas", "", "| Status | Sitemap | URL | Erro |", "|---:|---|---|---|"]
    for r in bad:
        lines.append(f"| {r.status_code if r.status_code is not None else 'erro'} | {r.source_sitemap} | {r.url} | {r.error or ''} |")
    (REPORTS / "sitemap_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({k: payload[k] for k in ["total_urls_unique", "bad_count", "status_counts"]}, ensure_ascii=False, indent=2))
    return 0 if not bad else 2


if __name__ == "__main__":
    raise SystemExit(main())
