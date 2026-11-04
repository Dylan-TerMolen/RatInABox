"""Swap figure images in an existing 'd1 Figures.docx' IN PLACE, keeping all text
(captions the authors have written) untouched. Each image whose alt text (docPr descr)
equals a manifest figure id gets that figure's current build PNG, resized to fit the
same one-page box. Reports figures in the manifest that have a build but no image in
the doc (they need a full rebuild or manual placement).

usage: swap_images.py <paper_dir> <in.docx> <out.docx>
"""
import glob, hashlib, sys, yaml
import docx
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from figpath import find_png
from docx.oxml.ns import qn
from PIL import Image
from build_figures_doc import fit_width

EMU = 914400


def main(paper, src, out):
    man = yaml.safe_load(open(f"{paper}/manifest.yaml"))["figures"]
    from titles import load_hidden
    man = [f for f in man if f["id"] not in load_hidden(paper)]
    d = docx.Document(src)
    seen, changed = set(), []
    for dr in d.element.body.iter(qn("w:drawing")):
        fid = dr.find(".//" + qn("wp:docPr")).get("descr")
        _p = find_png(paper, fid); pngs = [_p] if _p else []
        if not pngs:
            continue
        seen.add(fid)
        blip = dr.find(".//" + qn("a:blip")); old = blip.get(qn("r:embed"))
        new_blob = open(pngs[0], "rb").read()
        if d.part.related_parts[old].blob == new_blob:
            continue
        new, _ = d.part.get_or_add_image(pngs[0])
        blip.set(qn("r:embed"), new)
        w, h = Image.open(pngs[0]).size
        cx = int(fit_width(pngs[0]) * EMU); cy = int(cx * h / w)
        for el in [dr.find(".//" + qn("wp:extent"))] + [e for e in dr.iter(qn("a:ext")) if e.get("cx")]:
            el.set("cx", str(cx)); el.set("cy", str(cy))
        if old != new:
            d.part.drop_rel(old)
        changed.append(fid)
    missing = [f["id"] for f in man if find_png(paper, f["id"]) and f["id"] not in seen]
    d.save(out)
    print("swapped:", changed)
    print("built but not in doc (need rebuild/placement):", missing)


if __name__ == "__main__":
    main(*sys.argv[1:])
