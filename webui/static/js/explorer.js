// Cell response explorer: ports the place-field and tEBC response equations
// from ratinabox/hsw/{combined_place_tebc.py, independent_model, place_dependent_model,
// arousal_mediated_model}/tebc_response2.py to JS so dragging the rat recomputes and
// redraws every curve instantly, client-side -- no server round trip, no charting
// library, no CDN (same philosophy as sweep_plot.js).
(function () {
  "use strict";

  // ---- Constants shared with the Python source --------------------------
  const CS_DURATION = 0.25;
  const US_START = CS_DURATION + 0.5; // 0.75, all three models' tebc_response2.py agree
  const US_DURATION = 0.10;
  const TRIAL_END = US_START + US_DURATION; // 0.85, when the US pulse itself finishes

  // Normalization window: matches tebc_response2.py's _t_ref exactly (the min/max
  // each response shape is scaled against) -- NOT the plotted x-axis range below.
  const NORMALIZE_T_MIN = -0.1, NORMALIZE_T_MAX = 2.0;
  const NORMALIZE_SAMPLES = 1000; // matches _t_ref's resolution

  // Plotted x-axis range: 0.1s of pre-trial baseline through 0.1s after the trial
  // ends. The only two x-axis indications drawn are trial start (t=0) and trial
  // end (TRIAL_END) -- see drawLineChart.
  const PLOT_T_MIN = -0.1, PLOT_T_MAX = TRIAL_END + 0.1;
  const PLOT_SAMPLES = 120;

  const BASELINE_FR = 0.02 / 30;         // combined_place_tebc.py's near-silent floor
  const TASK_ONLY_BASELINE = 0.02 / 30;  // place_dependent_model/TEBC.py
  const MOVING_THRESHOLD = 0.02;         // m/s, shared by all three models

  // utils.velocity_gain, shared by combined_place_tebc.py's _place_firing_rate
  // and arousal_mediated_model's _modulate_firing_rates_for_velocity: a
  // saturating exponential (rises near the moving threshold, plateaus at
  // r_max) rather than a polynomial, so it never turns over at high speed.
  const VELOCITY_GAIN_R0 = 1.16059441, VELOCITY_GAIN_R_MAX = 11.6, VELOCITY_GAIN_TAU = 13.3;

  function velocityGain(speedCmPerSec) {
    return VELOCITY_GAIN_R0 + (VELOCITY_GAIN_R_MAX - VELOCITY_GAIN_R0) * (1 - Math.exp(-speedCmPerSec / VELOCITY_GAIN_TAU));
  }
  function velocityFiringMultiplier(speedMetersPerSec) {
    return velocityGain(speedMetersPerSec * 100) / 30;
  }

  function linspace(min, max, n) {
    const out = new Array(n);
    for (let i = 0; i < n; i++) out[i] = min + ((max - min) * i) / (n - 1);
    return out;
  }

  function interp(x, xs, ys) {
    // Mirrors numpy.interp: clamps outside [xs[0], xs[last]].
    if (x <= xs[0]) return ys[0];
    if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
    for (let i = 0; i < xs.length - 1; i++) {
      if (x >= xs[i] && x <= xs[i + 1]) {
        const frac = (x - xs[i]) / (xs[i + 1] - xs[i]);
        return ys[i] + frac * (ys[i + 1] - ys[i]);
      }
    }
    return ys[ys.length - 1];
  }

  function gaussianRandom(mean, std) {
    const u1 = Math.random() || 1e-9;
    const u2 = Math.random();
    return mean + std * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  }
  function uniformRandom(min, max) {
    return min + Math.random() * (max - min);
  }

  // ---- Place field --------------------------------------------------
  // Ports ratinabox.Neurons.PlaceCells.get_state's "gaussian" description
  // (min_fr is always 0 in every TEBC model here).
  function gaussianPlaceRate(distance, width, maxFr) {
    return Math.exp(-(distance ** 2) / (2 * width ** 2)) * maxFr;
  }

  // ---- The 8 canonical CS/trace/US response shapes -----------------------
  // independent_model/tebc_response2.py and place_dependent_model/tebc_response2.py
  // write these with different literal constants, but the constants preserve the
  // same ratios for every type (checked by hand against both files) -- so the two
  // models share one normalized shape per type; only the amplitude applied to it
  // (see typeResponse below) differs between models.

  function gaussianPeak(t, magnitude, peakTime, sd, baseline) {
    if (t === 0) return baseline;
    return magnitude * Math.exp(-((t - peakTime) ** 2) / (2 * sd ** 2)) + baseline;
  }
  function bimodalResponse(t, magnitudes, peakTimes, sds, baseline) {
    return gaussianPeak(t, magnitudes[0], peakTimes[0], sds[0], baseline)
         + gaussianPeak(t, magnitudes[1], peakTimes[1], sds[1], baseline);
  }
  function gaussianPeak2(t, magnitude, peakTime, sd, baseline) {
    const response = magnitude * Math.exp(-((t - peakTime) ** 2) / (2 * sd ** 2)) + baseline;
    return t > peakTime - 0.1 ? response : baseline;
  }
  function linearDecayResponse(t, baseline, midTime, endTime, firstMagnitude, secondMagnitude) {
    if (t <= 0) return baseline;
    if (t < 0.2) return ((firstMagnitude - baseline) / 0.2) * t + baseline;
    if (t < 0.85) return ((secondMagnitude - firstMagnitude) / 0.65) * (t - midTime) + firstMagnitude;
    if (t <= endTime + 3) return secondMagnitude;
    return baseline;
  }
  function cellType4Response(t, baseline, csPeak, usPeak, usSd) {
    // Literal port of cell_type_4_response's cascading (non-elif) ifs.
    let response = baseline;
    if (t > 0.05 && t <= 0.78) response = ((csPeak - baseline) / 0.73) * (t - 0.05) + baseline;
    if (t > 0.78 && t <= 1) response = usPeak * Math.exp(-((t - 0.78) ** 2) / (5 * usSd ** 5)) + baseline;
    if (t > 1 && t <= 3) response = csPeak;
    if (t >= 3) response = baseline;
    if (response < csPeak) response = csPeak;
    if (response > usPeak) response = usPeak;
    return response;
  }
  function cellType5Response(t, baseline, usPeak) {
    let response = baseline;
    if (t >= US_START && t < US_START + US_DURATION) response = interp(t, [0.75, 0.78], [baseline, usPeak]);
    if (t >= US_START) response = interp(t, [0.78, 1.2], [usPeak, baseline]);
    return response;
  }
  function noisyResponse(amplitude, noiseLevel) {
    return amplitude + gaussianRandom(-noiseLevel, noiseLevel);
  }
  function gaussianPeak3(t, magnitude, peakTime, sd, duration, baseline) {
    let response = magnitude * Math.exp(-((t - peakTime) ** 2) / (2 * sd ** 2));
    response = (t >= peakTime - 3 * sd && t <= peakTime + duration) ? response : 0;
    return response + baseline;
  }
  function bimodalResponse2(t, magnitudes, peakTimes, sds, baseline) {
    const peak1 = gaussianPeak3(t, magnitudes[0], peakTimes[0], sds[0], CS_DURATION, baseline);
    const peak2 = gaussianPeak3(t, magnitudes[1], peakTimes[1], sds[1], US_DURATION, baseline);
    return Math.max(peak1 + peak2, baseline);
  }
  function type8Decay(t, baseline) {
    if (t <= 0.25) return baseline;
    if (t <= 0.252) return baseline * 0.46;
    if (t < 0.75) return ((baseline * 0.62 - baseline) / (0.75 - 0.252)) * (t - 0.252) + baseline;
    if (t <= 1.5) return ((baseline * 0.38 - baseline) / 0.75) * (t - 0.75) + baseline;
    return baseline;
  }

  // Raw shapes at baseline=1.0 -- place_dependent_model's own literal constants,
  // the ones each type's ratios are defined against.
  const RAW_SHAPES = {
    1: (t) => bimodalResponse(t, [2.14, 5.71], [0.3, 0.85], [0.1, 0.1], 1.0),
    2: (t) => gaussianPeak2(t, 3.14, US_START, 0.15, 1.0),
    3: (t) => linearDecayResponse(t, 1.0, 0.2, 0.85, 0.33, 0.17),
    4: (t) => cellType4Response(t, 1.0, 0.4, 1.1, 0.2),
    5: (t) => cellType5Response(t, 1.0, 3.14),
    7: (t) => bimodalResponse2(t, [1.67, 2.14], [0.3, US_START + 0.05], [0.08, 0.15], 1.0),
    8: (t) => type8Decay(t, 1.0),
  };

  // Min-max normalize each raw shape over the same window tebc_response2.py's
  // _t_ref samples, once, at load.
  const NORMALIZED_SHAPES = {};
  (function buildNormalizedShapes() {
    const tRef = linspace(NORMALIZE_T_MIN, NORMALIZE_T_MAX, NORMALIZE_SAMPLES);
    Object.keys(RAW_SHAPES).forEach((type) => {
      const fn = RAW_SHAPES[type];
      const values = tRef.map(fn);
      const min = Math.min(...values);
      const max = Math.max(...values);
      NORMALIZED_SHAPES[type] = (t) => (fn(t) - min) / (max - min);
    });
  })();

  // Firing rate for a given type/time at the given amplitude. Type 6
  // (noisy_uniform_response) isn't a normalized shape -- it's a flat line at
  // half the amplitude plus small noise, ported as-is (each plotted point
  // draws its own noise sample, unlike the sim which only evaluates it once
  // per timestep).
  function typeResponse(type, t, amplitude) {
    if (type === 6) return noisyResponse(amplitude * 0.5, 0.03 / 30);
    return NORMALIZED_SHAPES[type](t) * amplitude;
  }

  // ---- Arousal-mediated model's own 4 response functions -----------------
  // (arousal_mediated_model/tebc_response2.py, ported verbatim)
  function arousalTypeOne(t, baseline) { // in place field firing, running
    if (t > 0 && t < US_START) return baseline * 1.3;
    if (t >= US_START && t < US_START + US_DURATION) return baseline * 1.5;
    return baseline;
  }
  function arousalTypeTwo(t, baseline) { // out of place field, running
    return (t > 0 && t < US_START + US_DURATION) ? baseline * 1.1 : baseline;
  }
  function arousalTypeThree(t, baseline) { // not moving, in field
    if (t > 0 && t < CS_DURATION) return baseline * 1.5;
    if (t >= CS_DURATION && t < US_START) {
      const decreaseFactor = 1 - (t - CS_DURATION) / (US_START - CS_DURATION);
      return baseline * (1 + 0.5 * decreaseFactor);
    }
    if (t >= US_START && t < US_START + US_DURATION) return baseline * 3;
    return baseline;
  }
  function arousalTypeFour(baseline) { // not moving, out of field
    return baseline + uniformRandom(-0.2, 0.2) * baseline;
  }
  const AROUSAL_FUNCS = { 1: arousalTypeOne, 2: arousalTypeTwo, 3: arousalTypeThree };

  // ---- Model-specific amplitude rules -------------------------------
  // Independent: task amplitude is always the fixed peak rate, regardless of
  // position (independent_model/TEBC.py's _task_amplitudes). Place-dependent:
  // task amplitude for a place+task cell IS its own place firing rate, and a
  // task-only cell (no field to scale off) gets a small constant instead
  // (place_dependent_model/TEBC.py). Both models then blend task_fr against
  // place_fr for place+task cells the same way (combined_place_tebc.py's
  // _combine_by_category).
  function taskAmplitude(model, placeFr, maxFr) {
    return model === "independent" ? maxFr : placeFr;
  }
  function taskOnlyAmplitude(model, maxFr) {
    return model === "independent" ? maxFr : TASK_ONLY_BASELINE;
  }

  function placeFrForCombinedModel(rawFr, speedMps) {
    return speedMps < MOVING_THRESHOLD ? BASELINE_FR : rawFr * velocityFiringMultiplier(speedMps);
  }

  // Place-cell shape is fixed rather than user-adjustable (matches every
  // model's TEBC.py default: place_cell_width=0.20, max_fr=12) -- speed is
  // the one control every model shares, feeding into each model's own
  // velocity-modulation math: velocityFiringMultiplier's saturating exponential (combined_place_tebc.py's
  // _place_firing_rate, shared by independent/place_dependent) for the combined models,
  // and the running/still split for arousal (the one model where in-field-ness AND
  // moving/still both change which of its 4 hand-written response types applies).
  const PLACE_CELL_WIDTH = 0.20;
  const PLACE_CELL_MAX_FR = 12;

  // ---- DOM plumbing ---------------------------------------------------
  const els = {
    fieldCanvas: document.getElementById("field-canvas"),
    speedSlider: document.getElementById("speed-slider"),
    speedValue: document.getElementById("speed-value"),
    balanceSlider: document.getElementById("balance-slider"),
    balanceValue: document.getElementById("balance-value"),
    balanceField: document.getElementById("balance-field"),
    categorySelect: document.getElementById("category-select"),
    arousalNote: document.getElementById("arousal-note"),
    placeOnlyCard: document.getElementById("place-only-card"),
    placeOnlyCanvas: document.getElementById("place-only-canvas"),
    typesGrid: document.getElementById("types-grid"),
    readoutDistance: document.getElementById("readout-distance"),
    readoutRawFr: document.getElementById("readout-raw-fr"),
    readoutPlaceFr: document.getElementById("readout-place-fr"),
    readoutMoving: document.getElementById("readout-moving"),
    readoutInfieldRow: document.getElementById("readout-infield-row"),
    readoutInfield: document.getElementById("readout-infield"),
  };

  const ratPos = { x: 0.5, y: 0.15 }; // start off-centre so field/position effects are visible

  function currentModel() {
    return document.querySelector('input[name="model"]:checked').value;
  }
  function currentCategory() {
    return document.querySelector('input[name="category"]:checked').value;
  }

  function refreshSegmentedStyles() {
    document.querySelectorAll(".segmented label").forEach((label) => {
      label.classList.toggle("active", label.querySelector("input").checked);
    });
  }

  // ---- Canvas drawing ---------------------------------------------------
  const COLORS = {
    bg: "#0b0d12", border: "#2a2e38", text: "#e6e8ec",
    muted: "#8b90a0", accent: "#5b9dff", warn: "#d29922",
  };

  // Place/task component identities -- same blue/orange pair as
  // notebooks/figures.ipynb's PLACE_COMPONENT_COLOR/TASK_COMPONENT_COLOR, softened
  // to translucent rgba() (matching that notebook's own COMPONENT_ALPHA pass) rather
  // than flat opaque paint, and lightened slightly from the notebook's light-mode hex
  // so they still read clearly against this UI's dark canvas background.
  const PLACE_COMPONENT_COLOR = "rgba(88, 156, 230, 0.7)";
  const TASK_COMPONENT_COLOR = "rgba(240, 146, 96, 0.7)";
  const TOTAL_LINE_COLOR = COLORS.text;

  function drawField(canvas, width, maxFr, pos) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const resolution = 48;
    const cell = w / resolution;
    for (let row = 0; row < resolution; row++) {
      for (let col = 0; col < resolution; col++) {
        const cx = (col + 0.5) / resolution;
        const cy = (row + 0.5) / resolution;
        const dist = Math.hypot(cx - 0.5, cy - 0.5);
        const intensity = gaussianPlaceRate(dist, width, maxFr) / maxFr; // 0..1
        ctx.fillStyle = mixColor(COLORS.bg, COLORS.accent, intensity);
        ctx.fillRect(col * cell, row * cell, cell + 0.5, cell + 0.5);
      }
    }

    // Field-centre crosshair.
    const cx = w / 2, cy = h / 2;
    ctx.strokeStyle = COLORS.muted;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx - 6, cy); ctx.lineTo(cx + 6, cy);
    ctx.moveTo(cx, cy - 6); ctx.lineTo(cx, cy + 6);
    ctx.stroke();

    // The rat.
    const rx = pos.x * w, ry = pos.y * h;
    ctx.font = "22px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("\u{1F400}", rx, ry); // 🐀
  }

  function mixColor(hexA, hexB, t) {
    t = Math.max(0, Math.min(1, t));
    const a = hexToRgb(hexA), b = hexToRgb(hexB);
    const r = Math.round(a.r + (b.r - a.r) * t);
    const g = Math.round(a.g + (b.g - a.g) * t);
    const bl = Math.round(a.b + (b.b - a.b) * t);
    return `rgb(${r}, ${g}, ${bl})`;
  }
  function hexToRgb(hex) {
    const n = parseInt(hex.slice(1), 16);
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
  }

  // Fixed axis bounds for a panel, derived from a *reference* curve (e.g. the
  // same curve evaluated with the rat sitting on the field centre) rather than
  // the currently-displayed one -- so the bounds don't move as the rat drags,
  // and a shrinking/rising curve is the model's real behaviour, not axis
  // rescaling. Firing rates are never negative, so the floor is always 0;
  // `padFraction` only pads headroom above the observed max.
  function computeBounds(referenceSamples, padFraction) {
    const ys = referenceSamples.map((s) => (typeof s === "number" ? s : s.y));
    const observedMax = Math.max(0, ...ys);
    const yMax = observedMax > 1e-12 ? observedMax * (1 + (padFraction ?? 0.08)) : 1e-6;
    return { yMin: 0, yMax };
  }

  function formatTick(value) {
    const abs = Math.abs(value);
    if (abs === 0) return "0";
    if (abs < 0.001) return value.toExponential(1);
    if (abs < 1) return value.toFixed(4);
    if (abs < 10) return value.toFixed(2);
    return value.toFixed(1);
  }

  // Clears the canvas and draws everything every chart shares -- background, y-axis
  // gridlines/labels, x-axis trial-start/trial-end ticks -- then hands the caller the
  // coordinate mappers to layer their own curve/fill on top. bounds: {yMin, yMax},
  // fixed by the caller (see computeBounds) so the axes stay put while the data itself
  // changes.
  function drawChartFrame(canvas, bounds) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = COLORS.bg;
    ctx.fillRect(0, 0, w, h);

    const { yMin, yMax } = bounds;
    const marginLeft = 40, marginRight = 6, marginTop = 8, marginBottom = 16;
    const plotW = w - marginLeft - marginRight;
    const plotH = h - marginTop - marginBottom;
    const xToPx = (t) => marginLeft + ((t - PLOT_T_MIN) / (PLOT_T_MAX - PLOT_T_MIN)) * plotW;
    const yToPx = (y) => marginTop + (1 - (y - yMin) / (yMax - yMin)) * plotH;

    ctx.font = "9px ui-monospace, monospace";
    ctx.fillStyle = COLORS.muted;

    // Y-axis gridlines + tick labels (min / mid / max of the fixed range).
    ctx.strokeStyle = COLORS.border;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    [yMin, (yMin + yMax) / 2, yMax].forEach((value) => {
      const y = yToPx(value);
      ctx.beginPath(); ctx.moveTo(marginLeft, y); ctx.lineTo(w - marginRight, y); ctx.stroke();
      ctx.textBaseline = value === yMax ? "top" : value === yMin ? "bottom" : "middle";
      ctx.fillText(formatTick(value), marginLeft - 4, y);
    });

    // X-axis: the only two indications are trial start (t=0) and trial end
    // (US onset + US pulse duration) -- no separate edge/min-max ticks.
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = COLORS.muted;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    [{ t: 0, label: "0" }, { t: TRIAL_END, label: TRIAL_END.toFixed(2) }].forEach(({ t, label }) => {
      const x = xToPx(t);
      ctx.beginPath(); ctx.moveTo(x, marginTop); ctx.lineTo(x, h - marginBottom); ctx.stroke();
      ctx.fillText(label, x, h - marginBottom + 3);
    });
    ctx.setLineDash([]);

    return { ctx, xToPx, yToPx };
  }

  function strokeCurve(ctx, samples, xToPx, yToPx, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    samples.forEach((s, i) => {
      const x = xToPx(s.t), y = yToPx(s.y);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  // samples: [{t, y}, ...].
  function drawLineChart(canvas, samples, bounds, color = COLORS.accent) {
    const { ctx, xToPx, yToPx } = drawChartFrame(canvas, bounds);
    strokeCurve(ctx, samples, xToPx, yToPx, color);
  }

  // Fills the region between two same-length, same-t curves (low underneath, high on
  // top) -- one call per stacked layer in drawStackedChart below.
  function fillBetween(ctx, low, high, xToPx, yToPx, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    low.forEach((s, i) => {
      const x = xToPx(s.t), y = yToPx(s.y);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    for (let i = high.length - 1; i >= 0; i--) {
      ctx.lineTo(xToPx(high[i].t), yToPx(high[i].y));
    }
    ctx.closePath();
    ctx.fill();
  }

  // Place component stacked on the bottom, task component stacked on top of it, total
  // (their exact sum) drawn as a solid line on top of both -- the canvas equivalent of
  // figures.ipynb's plot_composition_panel. weightedPlace/weightedTask/total are
  // [{t, y}, ...] over the same t grid.
  function drawStackedChart(canvas, weightedPlace, weightedTask, total, bounds) {
    const { ctx, xToPx, yToPx } = drawChartFrame(canvas, bounds);
    const zero = weightedPlace.map((s) => ({ t: s.t, y: 0 }));
    fillBetween(ctx, zero, weightedPlace, xToPx, yToPx, PLACE_COMPONENT_COLOR);
    fillBetween(ctx, weightedPlace, total, xToPx, yToPx, TASK_COMPONENT_COLOR);
    strokeCurve(ctx, total, xToPx, yToPx, TOTAL_LINE_COLOR);
  }

  function sampleCurve(fn) {
    const ts = linspace(PLOT_T_MIN, PLOT_T_MAX, PLOT_SAMPLES);
    return ts.map((t) => ({ t, y: fn(t) }));
  }

  // ---- Panel grid (built once per model switch, redrawn on every update) ----
  let currentGridModel = null;

  // Matches tebc_response.py's DEFAULT_TASK_TYPES -- the subset --task_types actually samples
  // from when a simulation doesn't override it. independent/place_dependent support all 8 raw
  // shapes (see RAW_SHAPES above), but only these 4 ever show up in an unconfigured run, so
  // that's what the explorer defaults to as well rather than all 8.
  const DEFAULT_TASK_TYPES = [1, 2, 3, 8];

  function panelSpecsFor(model) {
    if (model === "arousal") {
      return [
        { id: 1, label: "Type 1 — in-field, running" },
        { id: 2, label: "Type 2 — out-of-field, running" },
        { id: 3, label: "Type 3 — in-field, still" },
        { id: 4, label: "Type 4 — out-of-field, still" },
      ];
    }
    return DEFAULT_TASK_TYPES.map((id) => ({ id, label: `Type ${id}` }));
  }

  function rebuildGridIfNeeded(model) {
    if (currentGridModel === model) return;
    currentGridModel = model;
    els.typesGrid.innerHTML = "";
    panelSpecsFor(model).forEach((spec) => {
      const panel = document.createElement("div");
      panel.className = "explorer-type-panel";
      panel.dataset.type = spec.id;
      panel.innerHTML = `<h4>${spec.label}</h4><canvas width="240" height="140"></canvas>`;
      els.typesGrid.appendChild(panel);
    });
  }

  // ---- Main update loop ---------------------------------------------
  function readControls() {
    return {
      model: currentModel(),
      category: currentCategory(),
      width: PLACE_CELL_WIDTH,
      maxFr: PLACE_CELL_MAX_FR,
      speedCmPerSec: parseFloat(els.speedSlider.value),
      balance: parseFloat(els.balanceSlider.value),
    };
  }

  function updateSliderLabels(controls) {
    els.speedValue.textContent = controls.speedCmPerSec.toFixed(0);
    els.balanceValue.textContent = controls.balance.toFixed(2);
  }

  function updateVisibility(controls) {
    const isArousal = controls.model === "arousal";
    els.categorySelect.style.display = isArousal ? "none" : "";
    els.arousalNote.hidden = !isArousal;
    els.readoutInfieldRow.style.display = isArousal ? "" : "none";

    const isPlaceOnly = !isArousal && controls.category === "place_only";
    els.placeOnlyCard.hidden = !isPlaceOnly;
    els.typesGrid.style.display = isPlaceOnly ? "none" : "";
    els.balanceField.hidden = isArousal || controls.category !== "place_task";
  }

  function updateAll() {
    const controls = readControls();
    updateSliderLabels(controls);
    updateVisibility(controls);
    refreshSegmentedStyles();
    rebuildGridIfNeeded(controls.model);

    const distance = Math.hypot(ratPos.x - 0.5, ratPos.y - 0.5);
    const rawFr = gaussianPlaceRate(distance, controls.width, controls.maxFr);
    const speedMps = controls.speedCmPerSec / 100;
    const moving = speedMps >= MOVING_THRESHOLD;

    drawField(els.fieldCanvas, controls.width, controls.maxFr, ratPos);
    els.readoutDistance.textContent = `${distance.toFixed(3)} m`;
    els.readoutRawFr.textContent = `${rawFr.toFixed(2)} Hz`;
    els.readoutMoving.textContent = moving ? "running" : "still";

    if (controls.model === "arousal") {
      updateArousal(controls, rawFr, speedMps, moving);
    } else {
      updateCombinedModel(controls, rawFr, speedMps);
    }
  }

  // type 6's response is randomly noisy every sample, so bounding it from a
  // fresh reference sample would make the axes themselves flicker; its true
  // range is known analytically (amplitude/2 +/- the noise std), so use that
  // instead of sampling.
  function typeSixBounds(referenceAmplitude) {
    const half = referenceAmplitude * 0.5;
    const noiseLevel = 0.03 / 30;
    return computeBounds([half - 3 * noiseLevel, half + 3 * noiseLevel]);
  }

  function updateCombinedModel(controls, rawFr, speedMps) {
    const placeFr = placeFrForCombinedModel(rawFr, speedMps);
    // Reference = rat sitting exactly on the field centre (rawFr === maxFr) --
    // the largest place_fr this width/speed/max_fr combination can ever produce.
    // Used only to size fixed axes; the *displayed* curve still uses placeFr.
    const placeFrMax = placeFrForCombinedModel(controls.maxFr, speedMps);
    els.readoutPlaceFr.textContent = `${placeFr.toFixed(5)} Hz`;

    if (controls.category === "place_only") {
      const bounds = computeBounds([0, placeFrMax]);
      drawLineChart(els.placeOnlyCanvas, sampleCurve(() => placeFr), bounds, PLACE_COMPONENT_COLOR);
      return;
    }

    if (controls.category === "task_only") {
      drawTaskOnlyGrid(controls, els.typesGrid);
      return;
    }

    drawPlaceTaskGrid(controls, placeFr, placeFrMax, els.typesGrid);
  }

  // task-only cells ignore balance/place entirely (taskOnlyAmplitude doesn't depend on
  // position), so each panel is a single task-colored curve, no stacking needed.
  function drawTaskOnlyGrid(controls, typesGrid) {
    const amplitude = taskOnlyAmplitude(controls.model, controls.maxFr);
    typesGrid.querySelectorAll(".explorer-type-panel").forEach((panel) => {
      const type = Number(panel.dataset.type);
      const curve = sampleCurve((t) => typeResponse(type, t, amplitude));
      const bounds = type === 6 ? typeSixBounds(amplitude) : computeBounds(curve);
      drawLineChart(panel.querySelector("canvas"), curve, bounds, TASK_COMPONENT_COLOR);
      panel.classList.remove("active");
    });
  }

  // place+task cells: split the balance*task_fr + (1-balance)*place_fr blend back into
  // its two weighted summands and stack them, mirroring figures.ipynb's
  // weighted_components_additive/dependent. The place component is constant across t
  // here since position/speed are frozen for this snapshot -- only the task component's
  // shape varies with time since CS.
  function drawPlaceTaskGrid(controls, placeFr, placeFrMax, typesGrid) {
    const weightedPlaceCurve = (fr) => sampleCurve(() => (1 - controls.balance) * fr);
    const weightedTaskCurve = (type, amplitude) => sampleCurve((t) => controls.balance * typeResponse(type, t, amplitude));
    const sumCurves = (a, b) => a.map((s, i) => ({ t: s.t, y: s.y + b[i].y }));

    typesGrid.querySelectorAll(".explorer-type-panel").forEach((panel) => {
      const type = Number(panel.dataset.type);
      const amplitude = taskAmplitude(controls.model, placeFr, controls.maxFr);
      const referenceAmplitude = taskAmplitude(controls.model, placeFrMax, controls.maxFr);

      const weightedPlace = weightedPlaceCurve(placeFr);
      const weightedTask = weightedTaskCurve(type, amplitude);
      const total = sumCurves(weightedPlace, weightedTask);

      const referenceTotal = sumCurves(weightedPlaceCurve(placeFrMax), weightedTaskCurve(type, referenceAmplitude));
      const bounds = type === 6 ? typeSixBounds(referenceAmplitude) : computeBounds(referenceTotal);

      drawStackedChart(panel.querySelector("canvas"), weightedPlace, weightedTask, total, bounds);
      panel.classList.remove("active");
    });
  }

  function updateArousal(controls, rawFr, speedMps, moving) {
    const runningRate = rawFr * velocityFiringMultiplier(speedMps);
    const stillRate = rawFr * (0.2 / 30);
    // Reference = rat on the field centre, i.e. rawFr === maxFr.
    const runningMax = controls.maxFr * velocityFiringMultiplier(speedMps);
    const stillMax = controls.maxFr * (0.2 / 30);
    const inField = rawFr >= 0.2;
    els.readoutPlaceFr.textContent = `${(moving ? runningRate : stillRate).toFixed(5)} Hz`;
    els.readoutInfield.textContent = inField ? "yes" : "no";

    const activeType = moving ? (inField ? 1 : 2) : (inField ? 3 : 4);
    els.typesGrid.querySelectorAll(".explorer-type-panel").forEach((panel) => {
      const type = Number(panel.dataset.type);
      const baseline = (type === 1 || type === 2) ? runningRate : stillRate;
      const referenceBaseline = (type === 1 || type === 2) ? runningMax : stillMax;

      let curve, bounds;
      if (type === 4) {
        // type_four_response is a pure random fluctuation (ignores t); bound
        // it analytically (+/-20% of baseline) rather than from noisy samples.
        curve = sampleCurve(() => arousalTypeFour(baseline));
        bounds = computeBounds([referenceBaseline * 0.8, referenceBaseline * 1.2]);
      } else {
        curve = sampleCurve((t) => AROUSAL_FUNCS[type](t, baseline));
        bounds = computeBounds(sampleCurve((t) => AROUSAL_FUNCS[type](t, referenceBaseline)));
      }
      drawLineChart(panel.querySelector("canvas"), curve, bounds);
      panel.classList.toggle("active", type === activeType);
    });
  }

  // ---- Rat dragging ---------------------------------------------------
  function setRatFromEvent(event) {
    const rect = els.fieldCanvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    ratPos.x = Math.min(0.98, Math.max(0.02, x));
    ratPos.y = Math.min(0.98, Math.max(0.02, y));
    scheduleUpdate();
  }

  let updateScheduled = false;
  function scheduleUpdate() {
    if (updateScheduled) return;
    updateScheduled = true;
    requestAnimationFrame(() => { updateScheduled = false; updateAll(); });
  }

  function initDragging() {
    let dragging = false;
    els.fieldCanvas.addEventListener("pointerdown", (event) => {
      dragging = true;
      els.fieldCanvas.setPointerCapture(event.pointerId);
      setRatFromEvent(event);
    });
    els.fieldCanvas.addEventListener("pointermove", (event) => {
      if (dragging) setRatFromEvent(event);
    });
    ["pointerup", "pointercancel"].forEach((type) => {
      els.fieldCanvas.addEventListener(type, () => { dragging = false; });
    });
  }

  function initControls() {
    ["change", "input"].forEach((evt) => {
      document.querySelectorAll('input[name="model"], input[name="category"]').forEach((input) => {
        input.addEventListener(evt, scheduleUpdate);
      });
      [els.speedSlider, els.balanceSlider].forEach((slider) => {
        slider.addEventListener(evt, scheduleUpdate);
      });
    });
  }

  function init() {
    initDragging();
    initControls();
    updateAll();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
