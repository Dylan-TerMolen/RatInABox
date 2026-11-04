# cowork_sync: manuscript-side figure sync (run by Claude in Cowork, not Claude Code)

Moves built figures from `paper/build/figures/` into the Word figures document and the
"d1 Figure Proofs" artifact. Claude Code never runs these (see CLAUDE.md, "Division of labor").

| Script | What it does |
|---|---|
| `swap_images.py <paper> <in.docx> <out.docx>` | Default. Replaces each image whose alt text = a figure id with its current build PNG, **in place**, resized to fit one page. Leaves every word of text (captions) untouched. Lists built figures that have no image in the doc yet. |
| `sync_figures_doc.py <paper> <legacy_dir> <out.docx>` | Full rebuild: title page, one boxed figure per page in manifest order (Figure n / Supplementary Figure n), caption placeholders, gray draft tags, placeholder pages for unbuilt figures, trailing legacy/reference pages. **Destroys any captions typed into the doc**, so only use it when no captions have been written, or when the user explicitly says so. |
| `gen_proofs.py <paper> <legacy_dir> <synced.docx> <synced_at_iso> <out_dir>` | Builds the proofs page (`out_dir/index.html` + `out_dir/figures/*.png`) and checks every figure against the given .docx by SHA-256 (match / out of date / missing). |
| `frame_figures.py`, `build_figures_doc.py` | Helpers (figure box, caption XML, fit-to-page sizing: max 6.3 in wide, 8.0 in tall). |
| `proofs_template.html` | Page template used by `gen_proofs.py`. |

Needs Python 3 with `python-docx`, `Pillow`, `PyYAML`.
