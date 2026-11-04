"""Rebuild 'd1 Figures.docx' from paper/manifest.yaml + paper/build/figures/*.png.

Manifest order sets numbering (main: Figure n, supplementary: Supplementary Figure n).
Built figures get a boxed page + caption placeholder; non-'done' ones carry a gray
status tag; unbuilt ones get a gray placeholder page. Legacy entries not yet
regenerated (and reference images) go on trailing pages.

usage: sync_figures_doc.py <paper_dir> <legacy_png_dir> <out.docx>
"""
import glob, os, sys, yaml
from xml.sax.saxutils import escape
import docx
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from figpath import find_png
from titles import load_titles, load_hidden
from docx.shared import Pt, Inches
from docx.enum.text import WD_BREAK
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame_figures as ff
from build_figures_doc import fit_width, MAX_H_IN

GRAY = '<w:rPr><w:i/><w:color w:val="595959"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
BOLD = '<w:rPr><w:b/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
HL = '<w:rPr><w:i/><w:sz w:val="18"/><w:szCs w:val="18"/><w:highlight w:val="yellow"/></w:rPr>'


def run(rpr, text):
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def para_xml(runs):
    return parse_xml(f'<w:p {nsdecls("w")}><w:pPr><w:keepLines/><w:spacing w:before="120" w:after="0"/></w:pPr>{runs}</w:p>')


def main(paper, legacy_dir, out):
    man = yaml.safe_load(open(f"{paper}/manifest.yaml"))["figures"]
    man = [f for f in man if f["id"] not in load_hidden(paper)]
    cov = yaml.safe_load(open(f"{paper}/legacy/coverage.yaml"))["legacy"]
    cov = [e for e in cov if "legacy:" + e["file"] not in load_hidden(paper)]
    titles = load_titles(paper)
    pending = [e for e in cov if e["kind"] == "reference" or (e["kind"] == "figure" and not e.get("regenerated"))]

    d = docx.Document()
    s = d.sections[0]
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(s, m, Inches(1))
    body = d.element.body
    sect = body.find(qn("w:sectPr"))

    def keep_sect_last():
        body.remove(sect); body.append(sect)

    def text(t, size, **kw):
        r = d.add_paragraph().add_run(t); r.font.size = Pt(size)
        for k, v in kw.items(): setattr(r, k, v)

    def pagebreak():
        d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def boxed(descr, img=None, max_h=MAX_H_IN):
        box = ff.figure_box(descr); body.append(box)
        cell = box.find(".//" + qn("w:tc"))
        if img:
            p = d.add_paragraph(); p.add_run().add_picture(img, width=Inches(fit_width(img, max_h)))
            dp = p._p.find(".//" + qn("wp:docPr")); dp.set("descr", descr); dp.set("name", descr)
            ppr = p._p.get_or_add_pPr()
            ppr.append(parse_xml(f'<w:jc {nsdecls("w")} w:val="center"/>'))
            ppr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
            cell.append(p._p)
        return cell

    text("Hippocampus computational modeling paper — Figures", 14, bold=True)
    text("Companion to the manuscript (d1). One figure per page, numbered to match the text. Figures are generated "
         "by the RatInABox paper/ pipeline and replaced here automatically; write captions in the highlighted lines, "
         "and don't edit the images. Figures not built yet have a gray placeholder so numbering stays aligned; gray "
         "status tags mark figures that are still partial.", 9, italic=True)

    main_n = supp_n = 0
    report = []
    for f in man:
        if f["kind"] == "main":
            main_n += 1; label = f"Figure {main_n}"
        else:
            supp_n += 1; label = f"Supplementary Figure {supp_n}"
        status = str(f.get("status", "")).split()[0]
        if titles.get(f["id"]): label = f"{label}. {titles[f['id']]}"
        _p = find_png(paper, f["id"]); pngs = [_p] if _p else []
        pagebreak()
        if pngs:
            cell = boxed(f["id"], pngs[0])
            runs = run(BOLD, f"{label}. ") + run(HL, f"[Caption for {f['id']} — to be written]")
            if status != "done":
                runs += run(GRAY, f"  (draft — pipeline status: {status})")
            cell.append(para_xml(runs))
            report.append((label, f["id"], status, os.path.basename(pngs[0])))
        else:
            cell = boxed(f["id"])
            cell.append(para_xml(run(BOLD, f"{label}. ") + run(GRAY, f"{f['id']} — not built yet (status: {status}). "
                                                                     "Replaced automatically once the pipeline renders it.")))
            report.append((label, f["id"], status, None))
        keep_sect_last()

    if pending:
        pagebreak(); text("Pending regeneration / reference", 12, bold=True)
        text("Earlier-draft or reference images kept so nothing is lost. Not part of the numbered figures.", 9, italic=True)
        for i, e in enumerate(pending):
            if i: pagebreak()
            cell = boxed("legacy:" + e["file"], f"{legacy_dir}/{e['file']}", max_h=6.8)
            lab = (f"Reference (source paper, not regenerated): {e.get('note', '').strip()}" if e["kind"] == "reference"
                   else f"Pending regeneration → {e['figure']}: {', '.join(e['panels'])}")
            cell.append(para_xml(run(GRAY, lab)))
            keep_sect_last()
    d.save(out)
    for r in report: print(*r)
    print("pending:", [e["file"] for e in pending])


if __name__ == "__main__":
    main(*sys.argv[1:])
