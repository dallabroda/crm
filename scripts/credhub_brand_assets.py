"""Gera os ícones e logos do Cred Hub (marca "C" da CredTech) em todos os tamanhos que o CRM usa.

Uso: python scripts/credhub_brand_assets.py [--frappe CAMINHO_DO_CLONE_DO_FRAPPE]
(a partir da raiz do repositório; precisa de Pillow). Com --frappe, também troca as imagens padrão do
Frappe (favicon, logos, wordmark dos e-mails) mantendo os nomes dos arquivos.

O "C" é desenhado por geometria (dois círculos em OU exclusivo e o recorte da abertura), o mesmo
desenho do SVG em `crm/public/images/logo.svg` e em `frontend/src/components/Icons/CRMLogo.vue`.
A marca CredTech é da CredTech e não está licenciada para terceiros (ver ORIGEM.md).
"""

import argparse
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "crm" / "public"
INK = (17, 17, 17, 255)  # quase preto, como o logo da CredTech
WHITE = (255, 255, 255, 255)

# Geometria num quadrado de 512 (mesma do SVG): círculo A à esquerda, B à direita, recorte à direita
A = (213, 256, 147)
B = (296, 256, 147)
NOTCH = (345, 208, 512, 298)


def mark(size: int, color, scale: float = 1.0) -> Image.Image:
	"""Só o "C", transparente em volta, centralizado num quadrado `size` ocupando `scale` dele."""
	big = size * 4  # desenha grande e reduz (bordas suaves)
	k = big / 512 * scale
	off = big * (1 - scale) / 2

	def circle(c):
		x, y, r = c
		layer = Image.new("L", (big, big), 0)
		ImageDraw.Draw(layer).ellipse(
			[off + (x - r) * k, off + (y - r) * k, off + (x + r) * k, off + (y + r) * k], fill=255
		)
		return layer

	shape = ImageChops.logical_xor(circle(A).convert("1"), circle(B).convert("1")).convert("L")
	notch = Image.new("L", (big, big), 0)
	x0, y0, x1, y1 = NOTCH
	ImageDraw.Draw(notch).rectangle([off + x0 * k, off + y0 * k, off + x1 * k, off + y1 * k], fill=255)
	shape = ImageChops.subtract(shape, notch)
	out = Image.new("RGBA", (big, big), color[:3] + (0,))
	out.putalpha(shape)
	return out.resize((size, size), Image.LANCZOS)


def app_icon(size: int, maskable: bool = False) -> Image.Image:
	"""Quadrado escuro com o "C" branco (área segura maior no maskable)."""
	img = Image.new("RGBA", (size, size), INK)
	c = mark(size, WHITE, scale=0.8 if maskable else 0.95)
	img.alpha_composite(c)
	return img


def splash(w: int, h: int) -> Image.Image:
	img = Image.new("RGB", (w, h), (255, 255, 255))
	side = int(min(w, h) * 0.22)
	img.paste(app_icon(side), ((w - side) // 2, (h - side) // 2), app_icon(side))
	return img


def wordmark(height: int) -> Image.Image:
	"""O "C" seguido de "Cred Hub", para o rodapé dos e-mails."""
	from PIL import ImageFont

	font = None
	for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"):
		try:
			font = ImageFont.truetype(name, int(height * 0.62))
			break
		except OSError:
			continue
	font = font or ImageFont.load_default()
	text = "Cred Hub"
	width = int(ImageDraw.Draw(Image.new("L", (1, 1))).textlength(text, font=font))
	img = Image.new("RGBA", (height + int(height * 0.25) + width + 4, height), (255, 255, 255, 0))
	img.alpha_composite(mark(height, INK))
	ImageDraw.Draw(img).text((height + int(height * 0.25), height / 2), text, font=font, fill=INK, anchor="lm")
	return img


def frappe_images(frappe_root: Path):
	"""Imagens padrão do Frappe com a marca Cred Hub (mesmos nomes: nada no código muda)."""
	images = frappe_root / "frappe" / "public" / "images"
	svg = (PUBLIC / "images" / "logo.svg").read_text(encoding="utf-8")
	for name in ("frappe-favicon.svg", "frappe-framework-logo.svg", "frappe-comp-logo.svg"):
		(images / name).write_text(svg, encoding="utf-8")
	for name, size in (("frappe-framework-logo.png", 128), ("frappe-logo.png", 128), ("framework.png", 256)):
		app_icon(size).save(images / name)
	wordmark(56).save(images / "frappe-wordmark.png")
	print("imagens do Frappe trocadas em", images)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--frappe", type=Path, help="clone do dallabroda/frappe")
	args = parser.parse_args()
	manifest = PUBLIC / "manifest"
	app_icon(192, maskable=True).save(manifest / "manifest-icon-192.maskable.png")
	app_icon(512, maskable=True).save(manifest / "manifest-icon-512.maskable.png")
	app_icon(180).convert("RGB").save(manifest / "apple-icon-180.png")
	for path in manifest.glob("apple-splash-*.jpg"):
		w, h = map(int, re.findall(r"(\d+)-(\d+)", path.stem)[0])
		splash(w, h).save(path, quality=88)
	images = PUBLIC / "images"
	app_icon(512).save(images / "logo.png")
	print("ícones gerados em", manifest, "e", images)
	if args.frappe:
		frappe_images(args.frappe)


if __name__ == "__main__":
	main()
