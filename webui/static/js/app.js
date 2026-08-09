// Minimal, dependency-free canvas plotter. Reads a #plot-data JSON script
// tag (written by results_view.html) and draws a scatter of x vs y with
// axis labels/ticks. No charting library, no CDN.
(function () {
  function drawPlot() {
    const dataEl = document.getElementById("plot-data");
    const canvas = document.getElementById("chart");
    if (!dataEl || !canvas) return;
    const data = JSON.parse(dataEl.textContent);
    const ctx = canvas.getContext("2d");

    const dpr = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth || 800;
    const cssHeight = canvas.clientHeight || 360;
    canvas.width = cssWidth * dpr;
    canvas.height = cssHeight * dpr;
    ctx.scale(dpr, dpr);

    const pad = { top: 20, right: 20, bottom: 46, left: 60 };
    const w = cssWidth - pad.left - pad.right;
    const h = cssHeight - pad.top - pad.bottom;

    const xs = data.x, ys = data.y;
    const xMin = Math.min(...xs), xMax = Math.max(...xs);
    const yMin = Math.min(...ys), yMax = Math.max(...ys);
    const xSpan = xMax - xMin || 1, ySpan = yMax - yMin || 1;

    const toPx = (vx, vy) => [
      pad.left + ((vx - xMin) / xSpan) * w,
      pad.top + h - ((vy - yMin) / ySpan) * h,
    ];

    ctx.fillStyle = "#0b0d12";
    ctx.fillRect(0, 0, cssWidth, cssHeight);

    // axes
    ctx.strokeStyle = "#2a2e38";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.left, pad.top);
    ctx.lineTo(pad.left, pad.top + h);
    ctx.lineTo(pad.left + w, pad.top + h);
    ctx.stroke();

    // ticks (5 each axis)
    ctx.fillStyle = "#8b90a0";
    ctx.font = "11px -apple-system, sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let i = 0; i <= 4; i++) {
      const vy = yMin + (ySpan * i) / 4;
      const [, py] = toPx(xMin, vy);
      ctx.fillText(vy.toPrecision(4), pad.left - 8, py);
      ctx.strokeStyle = "rgba(255,255,255,0.05)";
      ctx.beginPath();
      ctx.moveTo(pad.left, py);
      ctx.lineTo(pad.left + w, py);
      ctx.stroke();
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let i = 0; i <= 4; i++) {
      const vx = xMin + (xSpan * i) / 4;
      const [px] = toPx(vx, yMin);
      ctx.fillText(vx.toPrecision(4), px, pad.top + h + 8);
    }

    // points, connected in index order (works as a line for time-series-like
    // CSVs, still reads fine as a scatter for unordered data)
    ctx.strokeStyle = "#5b9dff88";
    ctx.beginPath();
    xs.forEach((vx, i) => {
      const [px, py] = toPx(vx, ys[i]);
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.stroke();

    ctx.fillStyle = "#5b9dff";
    xs.forEach((vx, i) => {
      const [px, py] = toPx(vx, ys[i]);
      ctx.beginPath();
      ctx.arc(px, py, 2.5, 0, Math.PI * 2);
      ctx.fill();
    });

    // axis labels
    ctx.fillStyle = "#e6e8ec";
    ctx.font = "12px -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(data.x_label, pad.left + w / 2, cssHeight - 14);
    ctx.save();
    ctx.translate(14, pad.top + h / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(data.y_label, 0, 0);
    ctx.restore();
  }

  document.addEventListener("DOMContentLoaded", drawPlot);
  window.addEventListener("resize", drawPlot);
})();
