// Lazily loads each metric's server-rendered surface PNG (see
// webui/sweep_plots.py -- reuses scripts/pull_and_plot_holdover_sweep.py's
// own matplotlib plotting code) the first time its checkbox is toggled on.
// Toggling off just hides the section; the image stays loaded so toggling
// back on doesn't re-fetch it.
(function () {
  function figureFor(metric) {
    return document.querySelector(`.surface-figure[data-metric="${CSS.escape(metric)}"]`);
  }

  function toggleMetric(checkbox) {
    const figure = figureFor(checkbox.dataset.metric);
    if (!figure) return;
    figure.style.display = checkbox.checked ? "" : "none";
    if (!checkbox.checked) return;
    const img = figure.querySelector("img.surface-image");
    if (img && !img.src) img.src = checkbox.dataset.src;
  }

  function init() {
    document.querySelectorAll(".metric-toggle").forEach((checkbox) => {
      checkbox.addEventListener("change", () => toggleMetric(checkbox));
      if (checkbox.checked) toggleMetric(checkbox);
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
