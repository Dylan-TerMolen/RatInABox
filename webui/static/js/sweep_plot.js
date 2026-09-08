// Lazily loads each metric's server-rendered surface PNG (see
// webui/sweep_plots.py -- reuses scripts/pull_and_plot_holdover_sweep.py's
// own matplotlib plotting code) the first time it becomes visible. A
// metric is visible when its checkbox is checked and -- for place metrics,
// which carry data-task-state/data-measure -- its kind matches the
// currently selected place_task_state/place_measure radio pair; task
// metrics aren't grouped and are always eligible. Hiding a metric (via its
// checkbox or by switching away from its group) never drops the image, so
// coming back to it doesn't re-fetch.
(function () {
  function figureFor(metric) {
    return document.querySelector(`.surface-figure[data-metric="${CSS.escape(metric)}"]`);
  }

  function checkedRadioValue(name) {
    return document.querySelector(`input[name="${name}"]:checked`)?.value;
  }

  function activePlaceGroup() {
    return { taskState: checkedRadioValue("place_task_state"), measure: checkedRadioValue("place_measure") };
  }

  function inActiveGroup(checkbox, group) {
    if (!checkbox.dataset.taskState) return true;  // ungrouped (task) metric
    return checkbox.dataset.taskState === group.taskState && checkbox.dataset.measure === group.measure;
  }

  function lazyLoad(figure, checkbox) {
    const img = figure.querySelector("img.surface-image");
    if (img && !img.src) img.src = checkbox.dataset.src;
  }

  function refreshFigures() {
    const group = activePlaceGroup();
    document.querySelectorAll(".metric-toggle").forEach((checkbox) => {
      const figure = figureFor(checkbox.dataset.metric);
      if (!figure) return;
      const visible = checkbox.checked && inActiveGroup(checkbox, group);
      figure.style.display = visible ? "" : "none";
      if (visible) lazyLoad(figure, checkbox);
    });
  }

  function refreshGroupRows() {
    const group = activePlaceGroup();
    document.querySelectorAll(".place-kind-group").forEach((row) => {
      row.style.display = (row.dataset.taskState === group.taskState && row.dataset.measure === group.measure) ? "" : "none";
    });
  }

  function refreshToggleStyles() {
    document.querySelectorAll(".segmented label").forEach((label) => {
      label.classList.toggle("active", label.querySelector("input").checked);
    });
  }

  function init() {
    document.querySelectorAll(".metric-toggle").forEach((checkbox) => {
      checkbox.addEventListener("change", refreshFigures);
    });
    document.querySelectorAll('input[name="place_task_state"], input[name="place_measure"]').forEach((radio) => {
      radio.addEventListener("change", () => {
        refreshToggleStyles();
        refreshGroupRows();
        refreshFigures();
      });
    });
    refreshToggleStyles();
    refreshGroupRows();
    refreshFigures();
  }

  document.addEventListener("DOMContentLoaded", init);
})();

// Axis-mode toggle (Auto vs Manual x/y/facet selection) on the results
// page's View card. A radio flip must enable/disable the right named
// <select> elements *before* submitting -- a disabled field is excluded
// from the submitted GET querystring, so leaving the old mode's fields
// enabled would carry their stale values across the switch (or, worse,
// duplicate the "facet_var" name between the Auto and Manual facet selects).
(function () {
  function setGroupState(className, enabled) {
    document.querySelectorAll(`.${className}`).forEach((field) => {
      field.hidden = !enabled;
      field.querySelectorAll("select").forEach((select) => { select.disabled = !enabled; });
    });
  }

  function applyAxisMode(mode) {
    setGroupState("auto-only", mode === "auto");
    setGroupState("manual-only", mode === "manual");
  }

  function init() {
    const radios = document.querySelectorAll('input[name="axis_mode"]');
    if (!radios.length) return;
    radios.forEach((radio) => {
      const activate = () => {
        radio.checked = true;
        applyAxisMode(radio.value);
        document.getElementById("axis-form").submit();
      };
      radio.addEventListener("change", activate);
      // Safari doesn't reliably forward a <label> click to a display:none
      // radio the way Chrome does (WebKit's label-activation algorithm
      // skips controls with no rendering box, see .segmented input in
      // style.css) -- handle the label click directly too, so the toggle
      // works cross-browser regardless of that quirk. preventDefault stops
      // the browser's own label-activation from *also* firing (which would
      // otherwise double up with this handler in browsers where forwarding
      // does work).
      const label = radio.closest("label");
      if (label) {
        label.addEventListener("click", (event) => {
          event.preventDefault();
          activate();
        });
      }
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
