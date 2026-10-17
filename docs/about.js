// about.html's scripted behaviour: the theme toggle and the growth chart.
//
// The figures in the prose and the Data Quality lists are not computed here:
// `make audit-update-about` (pipeline/audit.py) writes them into the page, so
// it reads right with JS off and the audit can be run from a terminal.
//
// The theme icons and handler are duplicated from app.js rather than shared,
// because about.html deliberately doesn't load app.js (which expects a sidebar
// and a tree). Both pages read/write the same localStorage "theme" key.

const SUN_ICON = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 3v2"/><path d="M12 19v2"/><path d="M5 5l1.4 1.4"/><path d="M17.6 17.6L19 19"/><path d="M3 12h2"/><path d="M19 12h2"/><path d="M5 19l1.4-1.4"/><path d="M17.6 6.4L19 5"/></svg>`;
const MOON_ICON = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z"/></svg>`;

function updateThemeToggleLabel() {
  const btn = document.getElementById("themeToggle");
  if (!btn) return;
  const theme = document.documentElement.getAttribute("data-theme") || "dark";
  const icon = theme === "dark" ? SUN_ICON : MOON_ICON;
  const label = theme === "dark" ? "Light" : "Dark";
  btn.innerHTML = `${icon}<span class="toggle-label">${label}</span>`;
}

const themeToggle = document.getElementById("themeToggle");
if (themeToggle) {
  updateThemeToggleLabel();
  themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateThemeToggleLabel();
  });
}

const CHANGELOG_URL = "./data/changelog.json";

// ---------------------------------------------------------------------------
// Growth over time
// ---------------------------------------------------------------------------
// docs/data/changelog.json is built by pipeline/build_changelog.py from the
// day each item went online (the jainelibrary.org API's `web_date`). It
// publishes only the months in which something was added, as running totals;
// this file fills the silent months in (so the x axis is time, not "months
// with news") and takes differences for the per-period view.
//
// Three bands, because the mix is the story: every item has a PDF; Quantum's
// public text stops with items added in mid-2020; the library's own OCR, which
// the Atlas fetched behind its login, carries on to mid-2022; after that,
// nothing has a text.

const BANDS = [
  { key: "text", label: "Quantum text", cls: "gb-text" },
  { key: "library", label: "eLibrary text", cls: "gb-library" },
  { key: "none", label: "PDF only", cls: "gb-pdf" },
];

// Which bands the stack draws. A PDF carries no text, so in `size` the
// PDF-only band is structurally zero and is dropped along with its legend key.
function activeBands() {
  return growthState.metric === "size" ? BANDS.filter((b) => b.key !== "none") : BANDS;
}

// `granularity` is months per group: 1 monthly, 3 quarterly, 12 yearly. Year
// is the default because two hundred monthly bars is a texture, not a reading.
// `prakrit`: chart the changelog's `periods_prakrit` (Sanskrit and Prakrit
// tiers) instead of `periods` (Sanskrit) -- the About page's counterpart of the
// tree page's "include Prakrit" pill, as the Wikisource Atlas pairs its two.
const growthState = { mode: "cumulative", metric: "count", granularity: 12, prakrit: false };

// What one published period says, as running totals per band.
function readPeriod(p) {
  const library = p.cumulative_elibrary_text_count || 0;
  const text = p.cumulative_quantum_text_count ?? (p.cumulative_text_count || 0) - library;
  const libraryBytes = p.cumulative_elibrary_iast_bytes || 0;
  return {
    count: { text, library, none: Math.max(0, (p.cumulative_count || 0) - text - library) },
    bytes: { text: (p.cumulative_iast_bytes_total || 0) - libraryBytes, library: libraryBytes, none: 0 },
  };
}

const ZERO = { count: { text: 0, library: 0, none: 0 }, bytes: { text: 0, library: 0, none: 0 } };

function diffBands(now, before) {
  const out = {};
  for (const b of BANDS) out[b.key] = Math.max(0, (now[b.key] || 0) - (before[b.key] || 0));
  return out;
}

// Every calendar month from the first published period to the last. A month
// with no period carries the previous totals forward and adds nothing.
function monthlySeries(log) {
  const src = (growthState.prakrit && log.periods_prakrit) || log.periods || [];
  if (!src.length) return [];
  const byMonth = new Map(src.map((p) => [p.date.slice(0, 7), p]));
  const last = src[src.length - 1].date.slice(0, 7);
  let [y, m] = src[0].date.slice(0, 7).split("-").map(Number);
  const out = [];
  let prev = ZERO;
  for (;;) {
    const key = `${y}-${String(m).padStart(2, "0")}`;
    const cum = byMonth.has(key) ? readPeriod(byMonth.get(key)) : prev;
    out.push({
      period: key,
      cum,
      add: { count: diffBands(cum.count, prev.count), bytes: diffBands(cum.bytes, prev.bytes) },
    });
    prev = cum;
    if (key === last) break;
    m += 1;
    if (m > 12) { m = 1; y += 1; }
  }
  return out;
}

// "2006" at year grouping, "2006-Q3" at quarter -- named for the calendar
// period the group covers, as in the sibling charts.
function groupLabel(first, size) {
  const year = first.period.slice(0, 4);
  if (size >= 12) return year;
  return `${year}-Q${Math.floor((Number(first.period.slice(5, 7)) - 1) / 3) + 1}`;
}

// Calendar chunks of `size` months. Running totals take the chunk's last
// month; additions sum. Mixing those two rules up is the one way this can go
// quietly wrong.
function groupSeries(series, size) {
  if (size <= 1) return series;
  const groups = [];
  let chunk = [], chunkKey = null;
  const flush = () => {
    if (!chunk.length) return;
    const sumBands = (metric) => {
      const out = {};
      for (const b of BANDS) out[b.key] = chunk.reduce((s, p) => s + (p.add[metric][b.key] || 0), 0);
      return out;
    };
    groups.push({
      period: groupLabel(chunk[0], size),
      cum: chunk[chunk.length - 1].cum,
      add: { count: sumBands("count"), bytes: sumBands("bytes") },
    });
    chunk = [];
  };
  for (const p of series) {
    const month = Number(p.period.slice(5, 7)) - 1;
    const key = `${p.period.slice(0, 4)}:${Math.floor(month / size)}`;
    if (key !== chunkKey) flush();
    chunkKey = key;
    chunk.push(p);
  }
  flush();
  return groups;
}

// Bytes, abbreviated, in decimal units (1 MB = 1e6 bytes).
function fmtSize(n) {
  if (n >= 1e9) return `${Number((n / 1e9).toFixed(2))} GB`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(0)} MB`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)} KB`;
  return `${n} B`;
}

function fmtValue(n) {
  return growthState.metric === "size" ? fmtSize(n) : n.toLocaleString();
}

function bandValues(p) {
  const side = growthState.mode === "cumulative" ? p.cum : p.add;
  return side[growthState.metric === "size" ? "bytes" : "count"];
}

// A round number at or above `n`, and the step between gridlines, so the
// tallest bar stops at a labelled tick. Whole steps only: these are counts of
// items or of bytes.
function niceScale(n) {
  const pow = Math.pow(10, Math.floor(Math.log10(n)));
  for (const mult of [0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10]) {
    const step = mult * pow;
    if (!Number.isInteger(step)) continue;
    const intervals = Math.ceil(n / step);
    if (intervals >= 3 && intervals <= 5) return { top: intervals * step, step };
  }
  return { top: Math.ceil(n / pow) * pow, step: pow };
}

function drawGrowth(series, chartEl) {
  const periods = groupSeries(series, growthState.granularity);
  const bands = activeBands();
  const totalOf = (p) => bands.reduce((s, b) => s + (bandValues(p)[b.key] || 0), 0);
  const { top: max, step } = niceScale(Math.max(...periods.map(totalOf), 1));

  chartEl.innerHTML = "";
  const chart = document.createElement("div");
  const dense = periods.length > 30;
  chart.className = "gb-chart" + (dense ? " gb-dense" : "");
  // Label about a dozen columns, whatever the granularity; the tooltip still
  // names every period exactly.
  const labelEvery = Math.max(1, Math.round(periods.length / 12));

  const axis = document.createElement("div");
  axis.className = "gb-axis";
  const grid = document.createElement("div");
  grid.className = "gb-grid";
  grid.setAttribute("aria-hidden", "true");
  for (let v = 0; v <= max; v += step) {
    const tick = document.createElement("div");
    tick.className = "gb-tick";
    tick.style.bottom = `${(v / max) * 100}%`;
    tick.textContent = fmtValue(v);
    axis.prepend(tick);
    const line = document.createElement("div");
    line.className = "gb-line";
    line.style.bottom = `${(v / max) * 100}%`;
    grid.appendChild(line);
  }
  chart.append(axis, grid);

  periods.forEach((p, i) => {
    const col = document.createElement("div");
    col.className = "gb-col";
    const stack = document.createElement("div");
    stack.className = "gb-stack";
    const values = bandValues(p);
    // Stacked bottom-up in BANDS order, so the text band sits on the axis.
    for (const band of [...bands].reverse()) {
      const v = values[band.key] || 0;
      if (!v) continue;
      const seg = document.createElement("div");
      seg.className = `gb-seg ${band.cls}`;
      seg.style.height = `${(v / max) * 100}%`;
      seg.title = `${p.period} — ${band.label}: ${fmtValue(v)}`;
      stack.appendChild(seg);
    }
    col.appendChild(stack);

    const lbl = document.createElement("div");
    lbl.className = "gb-year";
    const showTick = i % labelEvery === 0
      || (i === periods.length - 1 && (periods.length - 1) % labelEvery > labelEvery / 2);
    if (showTick) lbl.textContent = p.period;
    col.appendChild(lbl);

    const unit = growthState.metric === "size" ? "" : " items";
    col.title = `${p.period} — ${growthState.mode === "cumulative" ? "total" : "added"}: ` +
      `${fmtValue(totalOf(p))}${unit}\n` +
      bands.map((b) => `  ${b.label}: ${fmtValue(values[b.key] || 0)}`).join("\n");
    chart.appendChild(col);
  });
  chartEl.appendChild(chart);
}

function renderGrowth(series, chartEl) {
  drawGrowth(series, chartEl);
  for (const btn of document.querySelectorAll("#growthControls button")) {
    // String(...) on both sides: granularity is a number in state and a
    // string in the DOM.
    const on = String(growthState[btn.dataset.axis]) === btn.dataset.value;
    btn.classList.toggle("gb-on", on);
    btn.setAttribute("aria-pressed", String(on));
  }
  // The legend follows the measure: a key for a band that is not drawn would
  // claim a colour the chart is not using.
  const shown = new Set(activeBands().map((b) => b.cls));
  for (const key of document.querySelectorAll(".gb-legend .gb-key")) {
    const swatch = key.querySelector(".gb-swatch");
    key.hidden = swatch
      ? !shown.has([...swatch.classList].find((c) => c !== "gb-swatch")) : false;
  }
}

function initGrowth(log) {
  const chartEl = document.getElementById("growthChart");
  if (!chartEl) return;
  let series = log ? monthlySeries(log) : [];
  if (!series.length) {
    chartEl.textContent = "Growth data unavailable.";
    return;
  }
  const prakritBox = document.getElementById("growthIncludePrakrit");
  if (prakritBox) {
    prakritBox.checked = growthState.prakrit;
    prakritBox.addEventListener("change", () => {
      growthState.prakrit = prakritBox.checked;
      series = monthlySeries(log);
      renderGrowth(series, chartEl);
    });
  }
  const controls = document.getElementById("growthControls");
  if (controls) {
    controls.addEventListener("click", (ev) => {
      const btn = ev.target.closest("button[data-value]");
      if (!btn) return;
      const { axis, value } = btn.dataset;
      growthState[axis] = axis === "granularity" ? Number(value) : value;
      renderGrowth(series, chartEl);
    });
  }
  renderGrowth(series, chartEl);
}

// ---------------------------------------------------------------------------

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return r.json();
}

(async () => {
  let log = null;
  try {
    log = await fetchJson(CHANGELOG_URL);
  } catch (e) {
    console.log("about: could not load changelog", e);
  }
  initGrowth(log);
})();

// The About page's one outbound link to the parent project. The markup carries
// the production URL; when this Atlas is served from localhost the parent is
// too, on the port its own serve_docs.py uses.
const PARENT_LOCAL_PORT = 8000;

// Host test copied from the parent's local-links.js, deliberately identical.
function isLocal(hostname) {
  return hostname === "localhost"
      || hostname === "127.0.0.1"
      || hostname === "[::1]"
      || hostname === "::1"
      || hostname.endsWith(".localhost");
}

if (isLocal(location.hostname)) {
  const parentLink = document.getElementById("parentLink");
  if (parentLink) {
    parentLink.href = `http://${location.hostname}:${PARENT_LOCAL_PORT}/`;
    parentLink.dataset.localized = "true";  // visible in devtools, as in the parent
  }
}
