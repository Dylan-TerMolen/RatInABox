"""Fig 2 (models): one schematic per model (a), the raw tEBC response types
IM/PDM share (b), each model's combined place+task response by field
distance (c: IM, d: PDM), the arousal-mediated 2x2 grid (e), and real
simulated-data rasters per model (f). Ported from figures.ipynb cells 12-37,
renamed Additive/Dependent -> IM/PDM (see paper/figlib/panels/models.py).

2026-10-23 figure review: (a) schematic boxes are neutral gray now, not
per-model colored ("remove colors from the models" -- the title already
names the model). (e) all 4 panels share one y-axis ("axis should be
standardized across all 4 plots"). (f) each model's raster is one combined
panel over all trials with rows shaded by condition, not separate per-
condition subplots ("show all N trials ... highlight the rows that fit the
condition"). Every gray trace-interval shading in b/e/f now has a legend
entry ("say what the shaded region is"). FIELD_STATE_COLORS' out_of_field is
purple, not orange, for color-blind legibility (paper/figlib/style.py).
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from paper.figlib.io import FigureInputs
from paper.figlib.panels.models import (
    arousal_2x2_grid,
    field_response_grid,
    model_schematic,
    raster_grid,
    raw_response_types,
)
from paper.figlib.panels.setup import panel_label

FIGURE_ID = "models"

MODELS = ("independent", "place_dependent", "arousal_mediated")


def build(inputs: FigureInputs, style) -> plt.Figure:
    style.apply_rc_params()
    sims = {model: inputs.sim[f"bioreal-{model}"] for model in MODELS}
    # Field width is env-area-only (doesn't depend on model), so any of the
    # three artifacts gives the same value -- use independent's for env A.
    width_A = sims["independent"].cells["A"]["place_cell_width"]

    fig = plt.figure(figsize=(style.figure_width_inches("double"), 19.0), constrained_layout=True)
    row_schematics, row_raw, row_im, row_pdm, row_adm, row_raster_im, row_raster_pdm, row_raster_adm = \
        fig.subfigures(8, 1, height_ratios=[0.6, 1.0, 1.0, 1.0, 1.6, 0.8, 0.8, 0.8])

    # (a) model schematics
    axes_schematic = row_schematics.subplots(1, 3)
    for ax, model in zip(axes_schematic, MODELS):
        model_schematic(ax, model)
    panel_label(axes_schematic[0], "a")

    # (b) raw response types (shared by IM/PDM)
    axes_raw = raw_response_types(row_raw)
    panel_label(axes_raw[0], "b")
    row_raw.suptitle("Task-response types, before place modulation", fontsize=8)

    # (c) IM combined field-response grid
    axes_im = field_response_grid(row_im, "independent", width=width_A)
    panel_label(axes_im[0], "c")
    row_im.suptitle(f"{style.MODEL_DISPLAY_NAMES['independent']}: combined response by field distance", fontsize=8)

    # (d) PDM combined field-response grid
    axes_pdm = field_response_grid(row_pdm, "place_dependent", width=width_A)
    panel_label(axes_pdm[0], "d")
    row_pdm.suptitle(f"{style.MODEL_DISPLAY_NAMES['place_dependent']}: combined response by field distance", fontsize=8)

    # (e) ADM 2x2 grid
    axes_adm = arousal_2x2_grid(row_adm)
    panel_label(axes_adm[0, 0], "e")
    row_adm.suptitle(f"{style.MODEL_DISPLAY_NAMES['arousal_mediated']}: field × movement", fontsize=8)

    # (f) rasters from real simulated data, one example cell per model -- each
    # a single combined raster over all trials, rows shaded by condition
    ax_raster_im = raster_grid(row_raster_im, sims["independent"], "independent")
    panel_label(ax_raster_im, "f")
    row_raster_im.suptitle(f"{style.MODEL_DISPLAY_NAMES['independent']}: example cell raster", fontsize=8)

    ax_raster_pdm = raster_grid(row_raster_pdm, sims["place_dependent"], "place_dependent")
    row_raster_pdm.suptitle(f"{style.MODEL_DISPLAY_NAMES['place_dependent']}: example cell raster", fontsize=8)

    ax_raster_adm = raster_grid(row_raster_adm, sims["arousal_mediated"], "arousal_mediated")
    row_raster_adm.suptitle(f"{style.MODEL_DISPLAY_NAMES['arousal_mediated']}: example cell raster", fontsize=8)

    # Named panels for build.py's per-panel export (build/panels/models/<name>.*).
    fig.panel_axes = {
        "a_independent": axes_schematic[0], "a_place_dependent": axes_schematic[1],
        "a_arousal_mediated": axes_schematic[2],
        "b": axes_raw,
        "c": axes_im,
        "d": axes_pdm,
        "e": axes_adm.ravel(),
        "f_independent": ax_raster_im,
        "f_place_dependent": ax_raster_pdm,
        "f_arousal_mediated": ax_raster_adm,
    }

    return fig
