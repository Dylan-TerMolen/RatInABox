"""Generate the figure-proofs page (proofs/index.html + proofs/figures/*.png) from
paper/manifest.yaml, paper/build/figures, build.lock.json, legacy/coverage.yaml, and the
currently synced 'd1 Figures.docx' (to report whether each figure in Word matches).

usage: gen_proofs.py <paper_dir> <legacy_dir> <synced_docx> <docx_synced_at> <out_dir>
"""
import glob, hashlib, json, os, shutil, sys
import docx, yaml
from figpath import find_png
from titles import load_titles, load_hidden
from docx.oxml.ns import qn
from PIL import Image

JOURNAL_W_MM = 183          # double-column width the figures are rendered for
WORD_TEXT_W_IN = 6.5        # d1 Figures.docx text column
WORD_MAX_W_IN, WORD_MAX_H_IN = 6.3, 8.0   # same limits sync_figures_doc.py uses
MAX_H_MM = WORD_MAX_H_IN * 25.4           # tallest figure that fits one Word page with its caption


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main(paper, legacy_dir, synced_docx, synced_at, out):
    man = yaml.safe_load(open(f"{paper}/manifest.yaml"))["figures"]
    man = [f for f in man if f["id"] not in load_hidden(paper)]
    cov = yaml.safe_load(open(f"{paper}/legacy/coverage.yaml"))["legacy"]
    cov = [e for e in cov if "legacy:" + e["file"] not in load_hidden(paper)]
    lock = json.load(open(f"{paper}/build/build.lock.json"))
    titles = load_titles(paper)
    d = docx.Document(synced_docx)
    word = {}
    for dr in d.element.body.iter(qn("w:drawing")):
        fid = dr.find(".//" + qn("wp:docPr")).get("descr")
        rid = dr.find(".//" + qn("a:blip")).get(qn("r:embed"))
        word[fid] = sha(d.part.related_parts[rid].blob)

    os.makedirs(f"{out}/figures", exist_ok=True)
    figs, main_n, supp_n = [], 0, 0
    for f in man:
        if f["kind"] == "main":
            main_n += 1; label = f"Figure {main_n}"
        else:
            supp_n += 1; label = f"Supplementary Figure {supp_n}"
        entry = {"label": label, "title": titles.get(f["id"]), "id": f["id"], "kind": f["kind"],
                 "status": str(f.get("status", "")).split()[0], "panels": f.get("panels", []),
                 "rendered_at": lock.get(f["id"], {}).get("rendered_at")}
        _p = find_png(paper, f["id"]); pngs = [_p] if _p else []
        if pngs:
            src = pngs[0]; blob = open(src, "rb").read()
            w, h = Image.open(src).size
            name = f"figures/{os.path.basename(src)}"
            shutil.copy(src, f"{out}/{name}")
            word_w = min(WORD_MAX_W_IN, WORD_MAX_H_IN * w / h)
            entry.update({
                "src": name, "px": [w, h],
                "height_mm": round(JOURNAL_W_MM * h / w),
                "word_width_in": round(word_w, 2),
                "word_scale_pct": round(100 * word_w / (JOURNAL_W_MM / 25.4)),
                "word": ("match" if word.get(f["id"]) == sha(blob) else
                         "missing" if f["id"] not in word else "stale"),
            })
        figs.append(entry)

    extras = []
    for e in cov:
        if e["kind"] == "reference" or (e["kind"] == "figure" and not e.get("regenerated")):
            name = f"figures/legacy_{e['file']}"
            shutil.copy(f"{legacy_dir}/{e['file']}", f"{out}/{name}")
            extras.append({"src": name, "file": e["file"], "kind": e["kind"], "note": (e.get("note") or "").strip(),
                           "target": None if e["kind"] == "reference" else f"{e['figure']}: {', '.join(e['panels'])}"})

    data = {"figures": figs, "extras": extras, "docx_synced_at": synced_at,
            "max_h_mm": round(MAX_H_MM), "journal_w_mm": JOURNAL_W_MM,
            "word_text_w_in": WORD_TEXT_W_IN}
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "proofs_template.html")).read()
    open(f"{out}/index.html", "w").write(tpl.replace("/*__DATA__*/null", json.dumps(data)))
    for fg in figs:
        print(fg["label"], fg["id"], fg["status"], fg.get("height_mm"), fg.get("word"))


if __name__ == "__main__":
    main(*sys.argv[1:])
