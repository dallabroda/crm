"""Gera os ícones e logos do Cred Hub a partir dos SVGs exportados do Figma (identidade CredTech).

Fontes (não editar à mão; exportadas do Figma IoiEQWKQK5e9WwHgi7kY4F, credtech#74):
- crm/public/images/brand/icon.svg             frame "Profile Picture" (437:4482)
- crm/public/images/brand/logo-horizontal.svg  frame "Full logo horizontal" (437:4697)

Os PNG/JPG são renderizados pelo Chromium (Playwright), nada é redesenhado.

Uso (a partir da raiz do repositório):
    python scripts/credhub_brand_assets.py [--frappe CAMINHO_DO_CLONE_DO_FRAPPE]
Com --frappe, também troca as imagens padrão do Frappe (favicon, logos, logo dos e-mails) mantendo os
nomes dos arquivos. A marca CredTech é da CredTech e não está licenciada para terceiros.
"""

import argparse
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "crm" / "public"
BRAND = PUBLIC / "images" / "brand"


def icon_svg(maskable: bool = False) -> str:
	svg = (BRAND / "icon.svg").read_text(encoding="utf-8")
	if maskable:
		# Android recorta o ícone em círculo: o "C" encolhe para a área segura (80%), o fundo continua inteiro
		svg = svg.replace('<path id="Union" ', '<path id="Union" transform="translate(16 16) scale(0.8)" ', 1)
	return svg


def render(page, svg: str, width: int, height: int, path: Path, background: str = "transparent", box=None):
	"""Desenha `svg` ocupando `box` (x, y, w, h) num quadro width x height e salva em `path`."""
	x, y, w, h = box or (0, 0, width, height)
	svg = re.sub(r'<svg ([^>]*?)width="[^"]*" height="[^"]*"', rf'<svg \1width="{w}" height="{h}"', svg, count=1)
	page.set_viewport_size({"width": width, "height": height})
	page.set_content(
		f"<html><body style='margin:0;background:{background}'>"
		f"<div style='position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;line-height:0'>{svg}</div>"
		"</body></html>"
	)
	opts = {"path": str(path), "omit_background": background == "transparent"}
	if path.suffix == ".jpg":
		opts.update(type="jpeg", quality=90, omit_background=False)
	page.screenshot(**opts)


def cropped_logo(page) -> tuple[str, float]:
	"""Logo horizontal sem a margem do quadro do Figma; devolve o SVG e a proporção largura/altura."""
	svg = (BRAND / "logo-horizontal.svg").read_text(encoding="utf-8")
	page.set_content(svg)
	b = page.evaluate("() => { const r = document.querySelector('svg > g').getBBox(); return {x: r.x, y: r.y, width: r.width, height: r.height} }")
	x, y, w, h = b["x"], b["y"], b["width"], b["height"]
	svg = re.sub(r'viewBox="[^"]*"', f'viewBox="{x:.2f} {y:.2f} {w:.2f} {h:.2f}"', svg, count=1)
	return svg, w / h


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--frappe", type=Path, help="clone do dallabroda/frappe")
	args = parser.parse_args()
	manifest, images = PUBLIC / "manifest", PUBLIC / "images"

	with sync_playwright() as p:
		browser = p.chromium.launch()
		page = browser.new_page()
		render(page, icon_svg(maskable=True), 192, 192, manifest / "manifest-icon-192.maskable.png")
		render(page, icon_svg(maskable=True), 512, 512, manifest / "manifest-icon-512.maskable.png")
		render(page, icon_svg(), 180, 180, manifest / "apple-icon-180.png")
		for path in sorted(manifest.glob("apple-splash-*.jpg")):
			w, h = map(int, re.findall(r"(\d+)-(\d+)", path.stem)[0])
			side = int(min(w, h) * 0.22)
			render(page, icon_svg(), w, h, path, background="#ffffff", box=((w - side) // 2, (h - side) // 2, side, side))
		render(page, icon_svg(), 512, 512, images / "logo.png")
		print("ícones gerados em", manifest, "e", images)

		if args.frappe:
			fimages = args.frappe / "frappe" / "public" / "images"
			svg = (BRAND / "icon.svg").read_text(encoding="utf-8")
			for name in ("frappe-favicon.svg", "frappe-framework-logo.svg", "frappe-comp-logo.svg"):
				(fimages / name).write_text(svg, encoding="utf-8", newline="\n")
			for name, size in (("frappe-framework-logo.png", 128), ("frappe-logo.png", 128), ("framework.png", 256)):
				render(page, icon_svg(), size, size, fimages / name)
			# logo dos e-mails (fundo claro): logo completo horizontal, recortado, 3x de 40px de altura
			logo, ratio = cropped_logo(page)
			height = 120
			render(page, logo, round(height * ratio), height, fimages / "frappe-wordmark.png")
			print("imagens do Frappe trocadas em", fimages)
		browser.close()


if __name__ == "__main__":
	main()
