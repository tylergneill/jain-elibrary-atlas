// about.html's scripted behaviour: the theme toggle, the figures in the prose,
// the Data Quality lists, and the growth chart.
//
// The figures come from data/tree.json and data/changelog.json, never from the
// markup -- a number typed into the page is a number that goes stale. Each
// <span data-stat="key"> is filled from deriveStats(); an absent figure renders
// as an em dash rather than a zero. The sibling Atlases have their audit
// pipeline rewrite the digits in place (`audit --update-about`); this Atlas has
// no audit stage yet, so the page derives them itself from the two published
// files, which is also all the Data Quality lists are allowed to read.
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

const TREE_URL = "./data/tree.json";
const CHANGELOG_URL = "./data/changelog.json";

// The text face of the catalogue -- the same root app.js links to.
const SITE_ROOT = "https://jainqq.org";

// ---------------------------------------------------------------------------
// Figures in the prose
// ---------------------------------------------------------------------------

const nf = new Intl.NumberFormat("en-US");

function fillStats(stats) {
  for (const el of document.querySelectorAll("[data-stat]")) {
    const unit = el.dataset.unit;
    let v = stats[el.dataset.stat];
    if (typeof v === "number" && unit === "mb") v = (v / 1e6).toFixed(0);
    else if (typeof v === "number" && unit === "kb") v = (v / 1e3).toFixed(0);
    else if (typeof v === "number") v = nf.format(v);
    el.textContent = v == null || v === "" ? "—" : String(v);
  }
}

const bytesOf = (w) => (w.sizes || {}).transliterated_bytes || 0;
const pct = (n, d) => (d ? (n / d * 100).toFixed(0) : null);
const inQuantum = (w) => (w.sources || []).includes("quantum");
const inApi = (w) => (w.sources || []).includes("api");

// A publication year the catalogue cannot mean: not four digits, or outside
// the span of printed Jain literature and the present.
function oddYear(w) {
  if (!w.publish_year) return false;
  const y = Number(String(w.publish_year).slice(0, 4));
  return !Number.isInteger(y) || y < 1700 || y > new Date().getFullYear();
}

// "Book_Devnagari, , , agam_index" -- a comma list with nothing between two
// of its commas, or after the last.
const hasEmptySlot = (w) => (w.classification || "").split(",").some((t) => !t.trim());

// "Sanskrit, Sanskrit": the tier admits a language string whose tokens are
// all Sanskrit, so a repeat gets in.
const repeatsLanguage = (w) => (w.language || "").includes(",");

function deriveStats(tree, log) {
  const works = tree.works || [];
  const stats = { ...(tree.all_stats || {}) };
  // Two text sources: Quantum's public booktext, and the library's own OCR
  // file, fetched behind its login for the items Quantum has no text for.
  const text = works.filter((w) => w.text);
  const publicText = works.filter((w) => w.text === "quantum");
  const libraryOcr = works.filter((w) => w.text === "elibrary");

  stats.no_text = works.length - text.length;
  stats.no_public_text = works.length - publicText.length;
  stats.elibrary_text_count = libraryOcr.length;
  stats.elibrary_text_bytes = libraryOcr.reduce((s, w) => s + bytesOf(w), 0);
  stats.both_sources = works.filter((w) => inQuantum(w) && inApi(w)).length;
  stats.quantum_only = works.filter((w) => inQuantum(w) && !inApi(w)).length;
  stats.api_only = works.filter((w) => !inQuantum(w)).length;
  stats.quantum_no_text = works.filter((w) => inQuantum(w) && w.text !== "quantum").length;
  stats.docx_count = works.filter((w) => w.ocr_docx).length;

  const horizontal = works.filter((w) => w.horizontal);
  stats.horizontal = horizontal.length;
  stats.horizontal_text = horizontal.filter((w) => w.text === "quantum").length;

  const withAuthor = works.filter((w) => w.author);
  stats.author_count = withAuthor.length;
  stats.author_pct = pct(withAuthor.length, works.length);
  stats.authors_distinct = new Set(withAuthor.map((w) => w.author)).size;
  // `editor` is set only where the catalogue names a classical author, the
  // catalogued author then being the modern editor.
  stats.classical_author_count = works.filter((w) => w.editor).length;
  stats.classical_author_pct = pct(stats.classical_author_count, works.length);

  stats.script_devanagari = works.filter((w) => w.script === "Hindi").length;
  stats.script_other = works.length - stats.script_devanagari;
  stats.classification_distinct = new Set(works.map((w) => w.classification)).size;
  stats.classification_empty_slot = works.filter(hasEmptySlot).length;
  stats.canon_pct = pct(stats.canon_count, works.length);

  stats.text_pages = text.reduce((s, w) => s + ((w.sizes || {}).pages || 0), 0);
  stats.iast_pct = pct(stats.transliterated_bytes, stats.content_bytes);
  const sizes = text.map(bytesOf).sort((a, b) => a - b);
  if (sizes.length) {
    const mid = sizes.length >> 1;
    stats.median_bytes = sizes.length % 2 ? sizes[mid] : (sizes[mid - 1] + sizes[mid]) / 2;
  }

  // Where the text stops: the newest accession that has one, and what has
  // been catalogued since, by which face knows it.
  const lastText = publicText.reduce((m, w) => (w.added && w.added > m ? w.added : m), "");
  const since = works.filter((w) => w.added && w.added > lastText);
  stats.last_text_added = lastText.slice(0, 7);
  stats.since_last_text = since.length;
  stats.since_quantum = since.filter(inQuantum).length;
  stats.since_api_only = since.length - stats.since_quantum;
  stats.last_quantum_year = works.filter(inQuantum)
    .reduce((m, w) => (w.added && w.added > m ? w.added : m), "").slice(0, 4);
  stats.first_api_only_year = works.filter((w) => !inQuantum(w) && w.added)
    .reduce((m, w) => (!m || w.added < m ? w.added : m), "").slice(0, 4);

  // The library's own OCR (the login-gated Word copy) runs two years past
  // Quantum's text, so the books after the last text split in two: OCR'd but
  // not public, and not OCR'd at all.
  const lastDocx = works.filter((w) => w.ocr_docx)
    .reduce((m, w) => (w.added && w.added > m ? w.added : m), "");
  stats.last_docx_added = lastDocx.slice(0, 7);
  stats.since_text_docx = since.filter((w) => w.ocr_docx).length;
  stats.since_last_docx = works.filter((w) => w.added && w.added > lastDocx).length;
  stats.docx_no_text = works.filter((w) => w.ocr_docx && w.text !== "quantum").length;
  // The library's OCR files record when they were made: one batch, it turns
  // out, for every item fetched (see Where the Text Stops).
  const created = [...new Set(libraryOcr.map((w) => w.ocr_created).filter(Boolean))].sort();
  stats.ocr_created_dates = created.length;
  stats.ocr_created_first = created[0] || null;
  stats.ocr_created_last = created[created.length - 1] || null;

  const undated = works.filter((w) => !w.added);
  stats.undated_text = undated.filter((w) => w.text === "quantum").length;

  if (log) {
    const periods = log.periods || [];
    stats.changelog_first = periods[0]?.date?.slice(0, 7);
    stats.changelog_last = periods[periods.length - 1]?.date?.slice(0, 7);
    stats.undated_works = log.undated_works;
  }
  return stats;
}

// ---------------------------------------------------------------------------
// Data Quality
// ---------------------------------------------------------------------------
// Each finding is a collapsed <details> in the siblings' audit markup. Rows are
// built as DOM nodes, never as HTML strings: the titles come out of tree.json.

function h(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, v);
  for (const c of children) node.append(c);
  return node;
}

function workLink(work) {
  return h("a", { href: `${SITE_ROOT}/explore/${work.id}/1`, target: "_blank", rel: "noopener" },
    work.title_en || work.title);
}

// A work as an audit row: serial, linked title, and whatever the finding is about.
function workRow(work, detail) {
  return h("span", {}, h("code", {}, work.id), " ", workLink(work), detail ? ` — ${detail}` : "");
}

function auditItem(summary, intro, rows) {
  const details = h("details", {},
    h("summary", { class: "audit-summary" }, h("span", {}, summary)));
  if (intro) details.append(h("p", { style: "margin-left: 1.6em;" }, intro));
  const list = h("ul", { style: "margin-left: 1.6em;" });
  for (const row of rows) list.append(row.tagName === "LI" ? row : h("li", {}, row));
  details.append(list);
  return h("li", { class: "audit-item" }, details);
}

// A finding whose rows are themselves collapsed groups, as the siblings nest
// a long list under its folders.
function nestedItem(summary, intro, groups) {
  const item = auditItem(summary, intro, groups.map(([label, rows]) => {
    const inner = h("ul", { style: "margin-left: 1.6em;" });
    for (const row of rows) inner.append(h("li", {}, row));
    return h("li", { class: "audit-item" }, h("details", {},
      h("summary", { class: "audit-summary" }, h("span", {}, `${label} (${rows.length})`)), inner));
  }));
  item.querySelector("ul").style.cssText = "margin-left: 1.6em; list-style: none; padding-left: 0;";
  return item;
}

function countBy(works, keyOf) {
  const counts = new Map();
  for (const w of works) counts.set(keyOf(w), (counts.get(keyOf(w)) || 0) + 1);
  return counts;
}

const items = (n) => `${nf.format(n)} ${n === 1 ? "item" : "items"}`;

function renderAudit(tree) {
  const list = document.getElementById("auditList");
  if (!list) return;
  const works = tree.works || [];
  const bySerial = (a, b) => a.id.localeCompare(b.id);
  list.innerHTML = "";

  const years = works.filter(oddYear).sort(bySerial);
  list.append(auditItem(
    `Publication years that cannot be right (${items(years.length)})`,
    "The catalogued year is not a four-digit year between 1700 and the present.",
    years.map((w) => workRow(w, `"${w.publish_year}"`))));

  const empty = works.filter((w) => w.text && !bytesOf(w)).sort(bySerial);
  list.append(auditItem(
    `Text pages that hold no text (${items(empty.length)})`,
    "Jain Quantum serves a text for these, with page markers, but nothing legible is on the pages.",
    empty.map((w) => workRow(w, `${nf.format((w.sizes || {}).pages || 0)} pages`))));

  const repeats = works.filter(repeatsLanguage).sort(bySerial);
  list.append(auditItem(
    `Language strings that repeat themselves (${items(repeats.length)})`,
    "",
    repeats.map((w) => workRow(w, `"${w.language}"`))));

  const slots = [...countBy(works.filter(hasEmptySlot), (w) => w.classification).entries()]
    .sort((a, b) => b[1] - a[1]);
  list.append(auditItem(
    `Classification strings with empty slots (${nf.format(works.filter(hasEmptySlot).length)} items, ` +
    `${slots.length} distinct strings)`,
    "The classification is a comma-separated list, and these have nothing between two of " +
    "their commas or after the last. Items carrying each string in parentheses.",
    slots.map(([s, n]) => h("span", {}, h("code", {}, s), ` (${n})`))));

  list.append(nestedItem(
    "Items in only one of the two catalogues",
    "Both sites present the same library under the same serials, but neither lists all of it. " +
    "An item known only to Jain Quantum has no accession date; one known only to " +
    "jainelibrary.org has no public text.",
    [
      ["Jain Quantum only", works.filter((w) => inQuantum(w) && !inApi(w)).sort(bySerial).map((w) => workRow(w))],
      ["jainelibrary.org only", works.filter((w) => !inQuantum(w)).sort(bySerial)
        .map((w) => workRow(w, w.added ? `online ${w.added.slice(0, 7)}` : ""))],
    ]));

  const dark = works.filter((w) => inQuantum(w) && !w.text);
  const darkYears = [...countBy(dark, (w) => (w.added || "").slice(0, 4) || "undated").entries()]
    .sort((a, b) => a[0].localeCompare(b[0]));
  const perYear = countBy(works.filter(inQuantum), (w) => (w.added || "").slice(0, 4) || "undated");
  list.append(auditItem(
    `Catalogued on Jain Quantum without a text (${nf.format(dark.length)} items)`,
    "Listed in Quantum's catalog, with a PDF in the library, but no text to read or search. " +
    "By year the item went online, against all of that year's Sanskrit items on Quantum.",
    darkYears.map(([y, n]) => `${y} — ${nf.format(n)} of ${nf.format(perYear.get(y))}`)));
}

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
const growthState = { mode: "cumulative", metric: "count", granularity: 12 };

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
  const src = log.periods || [];
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
  const series = log ? monthlySeries(log) : [];
  if (!series.length) {
    chartEl.textContent = "Growth data unavailable.";
    return;
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
  // The changelog is optional to everything but the chart: without it the
  // prose's growth figures show a dash and the rest of the page still fills.
  let log = null;
  try {
    log = await fetchJson(CHANGELOG_URL);
  } catch (e) {
    console.log("about: could not load changelog", e);
  }
  initGrowth(log);
  try {
    const tree = await fetchJson(TREE_URL);
    fillStats(deriveStats(tree, log));
    renderAudit(tree);
  } catch (e) {
    console.log("about: could not load tree", e);
    fillStats({});
    const list = document.getElementById("auditList");
    if (list) list.textContent = "Data unavailable.";
  }
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
