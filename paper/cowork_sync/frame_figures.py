"""Wrap each placed figure (image whose alt text is a figure id) in a thin bordered
1x1 table, and add a caption placeholder line under the image inside the box.

Only touches: the image's own (text-free) paragraph, which moves into the box, and
the new caption paragraph. Existing text is never modified. Idempotent: images
already inside a figure box are skipped.
"""
import sys, copy
import docx
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls

EMU_PER_IN = 914400
TEXT_WIDTH_TWIPS = 9360          # 6.5 in text column
CELL_MARGIN_TWIPS = 115          # ~0.08 in
IMAGE_WIDTH_IN = 6.3             # fits inside the box margins
BORDER = '<w:{side} w:val="single" w:sz="6" w:space="0" w:color="7F7F7F"/>'


def figure_box(fig_id):
    borders = "".join(BORDER.format(side=s) for s in ("top", "left", "bottom", "right"))
    return parse_xml(f"""
<w:tbl {nsdecls('w')}>
  <w:tblPr>
    <w:tblW w:w="{TEXT_WIDTH_TWIPS}" w:type="dxa"/>
    <w:jc w:val="center"/>
    <w:tblBorders>{borders}</w:tblBorders>
    <w:tblLayout w:type="fixed"/>
    <w:tblCellMar>
      <w:top w:w="{CELL_MARGIN_TWIPS}" w:type="dxa"/><w:left w:w="{CELL_MARGIN_TWIPS}" w:type="dxa"/>
      <w:bottom w:w="{CELL_MARGIN_TWIPS}" w:type="dxa"/><w:right w:w="{CELL_MARGIN_TWIPS}" w:type="dxa"/>
    </w:tblCellMar>
    <w:tblCaption w:val="figure:{fig_id}"/>
  </w:tblPr>
  <w:tblGrid><w:gridCol w:w="{TEXT_WIDTH_TWIPS}"/></w:tblGrid>
  <w:tr><w:trPr><w:cantSplit/></w:trPr><w:tc><w:tcPr><w:tcW w:w="{TEXT_WIDTH_TWIPS}" w:type="dxa"/></w:tcPr></w:tc></w:tr>
</w:tbl>""")


def caption_paragraph(number, fig_id):
    rpr = '<w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
    bold = '<w:rPr><w:b/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
    hl = '<w:rPr><w:i/><w:sz w:val="18"/><w:szCs w:val="18"/><w:highlight w:val="yellow"/></w:rPr>'
    return parse_xml(f"""
<w:p {nsdecls('w')}>
  <w:pPr><w:keepLines/><w:spacing w:before="120" w:after="0"/></w:pPr>
  <w:r>{bold}<w:t xml:space="preserve">Figure </w:t></w:r>
  <w:fldSimple w:instr=" SEQ Figure \\* ARABIC "><w:r>{bold}<w:t>{number}</w:t></w:r></w:fldSimple>
  <w:r>{bold}<w:t xml:space="preserve">. </w:t></w:r>
  <w:r>{hl}<w:t xml:space="preserve">[Caption for {fig_id} — to be written]</w:t></w:r>
</w:p>""")


def resize(drawing, width_in):
    extent = drawing.find(".//" + qn("wp:extent"))
    cx, cy = int(extent.get("cx")), int(extent.get("cy"))
    new_cx = int(width_in * EMU_PER_IN)
    new_cy = int(cy * new_cx / cx)
    extent.set("cx", str(new_cx)); extent.set("cy", str(new_cy))
    for ext in drawing.iter(qn("a:ext")):
        if ext.get("cx") is not None:
            ext.set("cx", str(new_cx)); ext.set("cy", str(new_cy))


def main(src, out):
    doc = docx.Document(src)
    body = doc.element.body
    number = 0
    for drawing in list(body.iter(qn("w:drawing"))):
        docpr = drawing.find(".//" + qn("wp:docPr"))
        fig_id = docpr.get("descr") if docpr is not None else None
        if not fig_id:
            continue
        number += 1
        para = drawing
        while para.tag != qn("w:p"):
            para = para.getparent()
        if any(a.tag == qn("w:tbl") for a in para.iterancestors()):
            print(f"{fig_id}: already boxed, skipped")
            continue
        text = "".join(t.text or "" for t in para.iter(qn("w:t")))
        if text.strip():
            raise SystemExit(f"{fig_id}: image paragraph contains text {text!r}; not moving it")
        box = figure_box(fig_id)
        para.addprevious(box)
        cell = box.find(".//" + qn("w:tc"))
        cell.append(para)                       # move image paragraph into the box
        ppr = para.find(qn("w:pPr"))
        if ppr is None:
            ppr = parse_xml(f'<w:pPr {nsdecls("w")}/>'); para.insert(0, ppr)
        ppr.append(parse_xml(f'<w:jc {nsdecls("w")} w:val="center"/>'))
        ppr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
        resize(drawing, IMAGE_WIDTH_IN)
        cell.append(caption_paragraph(number, fig_id))
        print(f"{fig_id}: boxed as Figure {number} with caption placeholder")
    doc.save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
