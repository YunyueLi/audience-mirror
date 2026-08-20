/* Audience Mirror workbench — Calibrated Projection Room, operate mode.
   Every rendered number comes from the local API or the generated public
   synthetic bundle; the static deployment is visibly read-only.
   Rendering contract: state.experiment is the single source, render* functions
   are pure projections of it, and no aggregate is shown without its scale
   qualifier, evidence reference and calibration status.

   Timeline contract: the ruler, the event cards, the proxy curves and both
   cursors are placed from the same millisecond values inside one scroller, so
   horizontal alignment across the three lanes is a fact rather than a claim. */

const state = {
  health: null,
  experiment: null,
  experimentIndex: [],
  deploymentMode: "local_service",
  selectedEventIndex: 0,
  zoomIndex: 0,
  /* A proportional timeline may need to be wider than its viewport so even the
     shortest real event keeps an honest 48px hit target. */
  timelineFloorPx: 0,
  /* The cue card currently borrowing the light path, if any. Hover and keyboard
     focus preview a route; the selected cue owns it the rest of the time. */
  beamHint: null,
};

const CLASSIFICATION_LABELS = {
  public: "公开素材",
  internal: "内部素材",
  confidential: "机密素材",
  restricted: "受限素材",
};

const MODALITY_LABELS = {
  multimodal: "多模态",
  visual: "画面",
  speech: "语音",
  music: "音乐",
  sound: "声音",
  text: "文本",
  user_annotation: "人工标注",
};

const EPISTEMIC_STATUS_LABELS = {
  human_confirmed: "人工复核事实",
  user_provided: "用户提供事实",
  model_observed: "模型观察",
  model_inferred: "模型推断",
  synthetic_fixture: "合成 Fixture",
};

const REVIEW_STATUS_LABELS = {
  unreviewed: "模型生成，待复核",
  auto_checked: "自动检查，语义待复核",
  human_confirmed: "素材事实已人工复核",
  user_provided: "用户提供，待复核",
  model_reviewed: "模型生成，已复核",
  model_unreviewed: "模型生成，待复核",
};

const REVIEW_STATUS_TONES = {
  human_confirmed: "confirmed",
  model_reviewed: "confirmed",
  unreviewed: "pending",
  model_unreviewed: "pending",
  auto_checked: "pending",
  user_provided: "pending",
};

const EXPERIMENT_STATUS_LABELS = {
  ingested: "已解析",
  analyzed: "已理解",
  complete: "已运行",
  calibrated: "已校准",
};

/* The runtime records reactions and actions as identifiers; readers need words.
   Unknown values fall through unchanged rather than being hidden. */
const REACTION_TYPE_LABELS = {
  understanding: "理解",
  confusion: "困惑",
  delight: "愉悦",
  surprise: "意外",
  boredom: "走神",
};

const ACTION_TYPE_LABELS = {
  continue: "继续观看",
  pause: "暂停",
  skip: "跳过本段",
  rewind_requested: "要求回看",
  abandon: "放弃观看",
};

const RUNTIME_MODE_LABELS = {
  deterministic_engineering_baseline: "工程基线",
  deterministic_fixture: "确定性工程基线",
  deterministic: "工程基线",
  model: "真实模型 Agent",
  model_agent: "真实模型 Agent",
};

const RECEIPT_OUTCOME_LABELS = {
  started: "进行中",
  complete: "已完成",
  failed: "失败",
};

const PAYLOAD_SCOPE_LABELS = {
  full_video_with_audio: "完整视频与音轨",
  "up_to_12_timestamped_local_jpeg_frames; original_video_and_audio_not_sent":
    "最多 12 张带时间戳证据帧；不发送原视频与音轨",
  "timeline_observations_persona_and_prior_memory; original_media_not_sent":
    "Timeline 观察、Persona 与此前记忆；不发送原始媒体",
};

const BUSY_STAGE_COPY = {
  ingest: ["正在建立证据时间轴", "检查链接与权利，在本机解码画面、抽取证据帧与音轨。完成后画面出现在这里，事件出现在下方时间轴。"],
  analyze: ["正在写入多模态事实层", "Provider 正在读取已授权载荷。完成后请在右侧复核推断状态与不确定性。"],
  run: ["AI 观众正在逐段体验", "Persona 按时间顺序独立体验，互不讨论；模型模式受调用上限保护。完成后曲线出现在时间轴下方。"],
  calibrate: ["正在对齐真人锚点", "只统计同任务、同版本的反馈；已撤回同意的记录会被排除。"],
  experiment: ["正在读取实验制品", "从本机 artifacts 恢复时间轴、个体记录与校准报告。"],
};

const INSPECTOR_VIEWS = ["evidence", "response", "traces", "calibration"];
const PANES = ["rail", "stage", "inspector", "deck"];

/* Two themes, both first-class. The first visit is light on purpose; after that
   the person's stored choice wins on every visit and on every device profile. */
const THEME_KEY = "audience-mirror-theme";
const THEME_META = { light: "#f5f3ee", dark: "#0a0d11" };
const THEME_TOGGLE_COPY = {
  light: "切换到深色主题",
  dark: "切换到浅色主题",
};

/* On a page that scrolls, the head navigation is a set of jump targets. */
const PANE_SECTIONS = {
  stage: "#stage",
  inspector: "#evidence-inspector",
  deck: "#deck",
};

/* Zoom keeps long timelines readable without lying about proportions. */
const ZOOM_STEPS = [1, 1.5, 2, 3, 4, 6, 8];
const RULER_STEPS_SECONDS = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600];

/* Curve lane geometry, in the SVG's 0-100 user space. */
const CURVE_TOP = 12;
const CURVE_BOTTOM = 88;

const AGENT_REASONER_MODELS = {
  "codex-cli": [
    { value: "gpt-5.6-sol", label: "GPT-5.6 Sol" },
  ],
  "claude-code": [
    { value: "sonnet", label: "Claude Sonnet" },
    { value: "opus", label: "Claude Opus" },
  ],
};

const VIDEO_PROVIDER_MODELS = {
  "codex-frames": [
    { value: "gpt-5.6-sol", label: "GPT-5.6 Sol" },
  ],
  gemini: [
    { value: "gemini-3.7-flash", label: "Gemini 3.7 Flash" },
  ],
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const prefersStillness = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;
const isSinglePane = () => window.matchMedia("(max-width: 899px)").matches;
const zoomFactor = () => ZOOM_STEPS[state.zoomIndex] || 1;
const staticBundle = window.__AUDIENCE_MIRROR_STATIC_DEMO__ || null;

/* ---------- formatting ---------- */

function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatTime(milliseconds) {
  const totalSeconds = Math.max(0, Math.floor(Number(milliseconds || 0) / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function formatPercent(value) {
  return value != null && value !== "" && Number.isFinite(Number(value))
    ? `${Math.round(Number(value) * 100)}%`
    : "—";
}

function formatSpan(milliseconds) {
  const totalSeconds = Math.max(0, Math.round(Number(milliseconds || 0) / 1000));
  if (totalSeconds < 60) return `${totalSeconds}s`;
  return `${Math.floor(totalSeconds / 60)}m${String(totalSeconds % 60).padStart(2, "0")}s`;
}

function formatExperimentDuration(milliseconds) {
  const totalSeconds = Math.max(0, Math.round(Number(milliseconds || 0) / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours) return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function formatCount(value) {
  return value == null ? "—" : Number(value).toLocaleString("zh-CN");
}

function formatStamp(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function epistemicLabel(value) {
  return EPISTEMIC_STATUS_LABELS[value] || value || "来源未标记";
}

function reviewStatusLabel(value) {
  return REVIEW_STATUS_LABELS[value] || value || "未复核";
}

function reactionLabel(value) {
  return REACTION_TYPE_LABELS[value] || value || "—";
}

function actionLabel(value) {
  return ACTION_TYPE_LABELS[value] || value || "—";
}

/* Some runtime reasons restate the action word ("继续观看。" under 继续观看).
   Print the reason only when it adds something. */
function reasonBeyondLabel(reason, label) {
  const trimmed = String(reason || "").replace(/[。.\s]+$/, "");
  return trimmed && trimmed !== label ? reason : "";
}

function unitValue(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.min(1, Math.max(0, numeric)).toFixed(3) : null;
}

function mean(values) {
  const numbers = values.map(Number).filter(Number.isFinite);
  return numbers.length ? numbers.reduce((sum, value) => sum + value, 0) / numbers.length : null;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

/* ---------- Signature 1: the emulsion ----------
   Evidence developing out of noise, stated literally once per picture.

   A Canvas 2D dust field inside the picture well condenses onto the frame's own
   geometry — seven particles in ten settle on the inset border, the rest on the
   horizontal eye line — and is gone again inside 560–760ms. It is not a loop, not
   a hover effect and not a background: it reports that a new picture just
   arrived, and then it stops.

   Performance envelope, all enforced below rather than hoped for:
     · Canvas 2D only, no WebGL, no shader, no new network dependency;
     · <= 136 particles for one condense, DPR clamped to 1.5;
     · exactly one rAF chain, cancelled on the frame the beat completes;
     · document.hidden stops it, resize re-measures it (positions are normalised,
       so a resize mid-beat is a different multiplication and nothing else);
     · pointer-events:none in CSS, so the native video controls keep every pixel;
     · prefers-reduced-motion never opens the loop at all. */

const DPR_CAP = 1.5;
const TAU = Math.PI * 2;

/* Four intensities of the same beat. Boot is the only one a reader meets cold, so
   it is the densest; a cue step is the lightest, because the reader is driving. */
const EMULSION_BEATS = {
  boot: { count: 136, duration: 760 },
  source: { count: 118, duration: 700 },
  slate: { count: 92, duration: 620 },
  cue: { count: 84, duration: 560 },
};

const emulsion = {
  canvas: null,
  ctx: null,
  frame: 0,
  startedAt: 0,
  duration: 0,
  particles: [],
  width: 0,
  height: 0,
  dpr: 0,
  ink: "#f4f5f6",
  accent: "#4fd0e0",
  key: null,
  seen: new Set(),
  booted: false,
};

/* The backing store follows the CSS box and the capped ratio; nothing is resized
   unless one of them actually changed. */
function measureEmulsion() {
  const canvas = emulsion.canvas;
  const ctx = emulsion.ctx;
  if (!canvas || !ctx) return false;
  const box = canvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(box.width));
  const height = Math.max(1, Math.round(box.height));
  const dpr = Math.min(DPR_CAP, window.devicePixelRatio || 1);
  if (width !== emulsion.width || height !== emulsion.height || dpr !== emulsion.dpr) {
    emulsion.width = width;
    emulsion.height = height;
    emulsion.dpr = dpr;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  return width > 8 && height > 8;
}

/* Targets are the picture's own geometry, not a decorative ring. Golden-ratio
   stratification spreads the walk along the border without the clumping a plain
   random walk produces at these counts. */
function emulsionField(count) {
  const particles = [];
  const inset = 0.055;
  const span = 1 - inset * 2;
  for (let index = 0; index < count; index += 1) {
    const walk = (index * 0.6180339887498949) % 1;
    let tx;
    let ty;
    if (index % 10 < 7) {
      const leg = walk * 4;
      if (leg < 1) { tx = inset + span * leg; ty = inset; }
      else if (leg < 2) { tx = 1 - inset; ty = inset + span * (leg - 1); }
      else if (leg < 3) { tx = 1 - inset - span * (leg - 2); ty = 1 - inset; }
      else { tx = inset; ty = 1 - inset - span * (leg - 3); }
    } else {
      tx = 0.12 + 0.76 * walk;
      ty = 0.5 + ((index % 3) - 1) * 0.03;
    }
    const angle = Math.random() * TAU;
    const drift = 0.16 + Math.random() * 0.3;
    particles.push({
      sx: clamp(tx + Math.cos(angle) * drift, -0.06, 1.06),
      sy: clamp(ty + Math.sin(angle) * drift * 0.72, -0.06, 1.06),
      tx,
      ty,
      radius: 0.5 + Math.random() * 0.9,
      delay: ((index % 7) / 7) * 0.24,
      accent: index % 6 === 0,
    });
  }
  return particles;
}

/* The CSS mirror of --ease-grain: gather slowly, set fast. */
function easeGrain(value) {
  return 1 - (1 - value) ** 3.2;
}

function stopEmulsion() {
  if (emulsion.frame) {
    window.cancelAnimationFrame(emulsion.frame);
    emulsion.frame = 0;
  }
  emulsion.particles = [];
  if (!emulsion.canvas) return;
  delete emulsion.canvas.dataset.live;
  emulsion.ctx?.clearRect(0, 0, emulsion.width, emulsion.height);
}

function drawEmulsion(now) {
  const { ctx, width, height } = emulsion;
  if (!ctx) return;
  const life = clamp((now - emulsion.startedAt) / emulsion.duration, 0, 1);
  ctx.clearRect(0, 0, width, height);
  for (const particle of emulsion.particles) {
    const local = clamp((life - particle.delay) / (1 - particle.delay), 0, 1);
    if (local <= 0) continue;
    const travel = easeGrain(local);
    const x = (particle.sx + (particle.tx - particle.sx) * travel) * width;
    const y = (particle.sy + (particle.ty - particle.sy) * travel) * height;
    // Fade in while travelling, then leave: nothing is still painted at the end,
    // so the layer never sits on top of the footage.
    const alpha = Math.sin(Math.PI * Math.min(1, local * 1.06)) ** 0.85;
    ctx.globalAlpha = alpha * (particle.accent ? 0.92 : 0.5);
    ctx.fillStyle = particle.accent ? emulsion.accent : emulsion.ink;
    ctx.beginPath();
    ctx.arc(x, y, particle.radius * (1.6 - travel * 0.6), 0, TAU);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  if (life >= 1) {
    stopEmulsion();
    return;
  }
  emulsion.frame = window.requestAnimationFrame(drawEmulsion);
}

/* A swap inside the same family of surface is a cue change; a swap between
   families, or the first picture of the session, is a source change. */
function emulsionKind(key) {
  const family = String(key).split(":")[0];
  return emulsion.key && String(emulsion.key).split(":")[0] === family ? "cue" : "source";
}

/* The only entry point. Three triggers reach it: the first experiment on screen,
   a finished source or evidence swap, and a cue selection that actually changed
   the picture. Everything else is refused here rather than at the call site. */
function requestEmulsion(key, kind) {
  const canvas = $("#emulsion");
  if (!canvas || !key) return;
  // Reduced motion, a hidden tab or a display:none layer all record the key and
  // stop: the picture arrives, the condense does not.
  if (prefersStillness() || document.hidden || getComputedStyle(canvas).display === "none") {
    emulsion.key = key;
    return;
  }
  if (key === emulsion.key) return;
  // An empty fixture develops once. The slate is the same picture on every cue, so
  // repeating it would be showmanship rather than a report.
  if (kind === "slate") {
    if (emulsion.seen.has(key)) {
      emulsion.key = key;
      return;
    }
    emulsion.seen.add(key);
  }
  emulsion.key = key;
  // Stepping the timeline with the arrow keys must not machine-gun the layer: a
  // cue beat that arrives mid-beat is dropped, not queued.
  if (emulsion.frame && kind === "cue") return;
  emulsion.canvas = canvas;
  if (!emulsion.ctx || emulsion.ctx.canvas !== canvas) {
    emulsion.ctx = canvas.getContext("2d");
    emulsion.dpr = 0;
  }
  if (!emulsion.ctx) return;
  if (!measureEmulsion()) return;
  const beat = EMULSION_BEATS[emulsion.booted ? kind : "boot"] || EMULSION_BEATS.source;
  emulsion.booted = true;
  // Both themes are first-class, so the dust reads its ink off the live tokens.
  const styles = getComputedStyle(canvas);
  emulsion.ink = styles.getPropertyValue("--on-aperture").trim() || "#f4f5f6";
  emulsion.accent = styles.getPropertyValue("--accent-node").trim() || "#4fd0e0";
  emulsion.particles = emulsionField(beat.count);
  emulsion.duration = beat.duration;
  emulsion.startedAt = performance.now();
  canvas.dataset.live = "true";
  window.cancelAnimationFrame(emulsion.frame);
  emulsion.frame = window.requestAnimationFrame(drawEmulsion);
}

/* ---------- transport ---------- */

async function fetchJSON(url, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    const fallback = staticDemoResponse(url, method);
    if (fallback != null) return fallback;
    throw error;
  }
  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = { detail: `服务返回了无法解析的响应（HTTP ${response.status}）。` };
  }
  if (!response.ok) {
    const fallback = staticDemoResponse(url, method);
    if (fallback != null) return fallback;
    throw new Error(payload.detail || payload.error || `请求失败（HTTP ${response.status}）。`);
  }
  return payload;
}

function staticDemoResponse(url, method = "GET") {
  if (!staticBundle || method !== "GET") return null;
  const path = String(url).split("?", 1)[0];
  let payload = null;
  if (path === "/api/health") payload = staticBundle.health;
  else if (path === "/api/experiments") payload = staticBundle.experiment_index;
  else if (path === "/api/experiments/demo") payload = staticBundle.experiment;
  if (payload == null) return null;
  state.deploymentMode = "static_public_demo";
  document.documentElement.dataset.deployment = "static-public-demo";
  return typeof structuredClone === "function"
    ? structuredClone(payload)
    : JSON.parse(JSON.stringify(payload));
}

function blockStaticMutation(action) {
  if (state.deploymentMode !== "static_public_demo") return false;
  setMessage(
    `公开体验版是只读的，${action}不会上传或发送任何内容。请从 GitHub 安装本机工作台后再运行这一步。`,
    "error",
  );
  return true;
}

/* ---------- busy, empty and error states ---------- */

function setBusy(button, busy, busyLabel) {
  if (!button) return;
  const label = $(".button-label", button);
  if (busy) {
    if (busyLabel != null && label) {
      button.dataset.idleLabel = label.textContent;
      label.textContent = busyLabel;
    }
    button.dataset.busy = "true";
    button.setAttribute("aria-busy", "true");
    button.disabled = true;
    return;
  }
  if (button.dataset.idleLabel != null && label) {
    label.textContent = button.dataset.idleLabel;
    delete button.dataset.idleLabel;
  }
  delete button.dataset.busy;
  button.removeAttribute("aria-busy");
  button.disabled = false;
}

function setApertureState(kind, title = "", copy = "") {
  const box = $("#aperture-state");
  if (!box) return;
  const retry = $("#aperture-retry");
  if (!kind) {
    box.hidden = true;
    box.className = "aperture-state";
    retry?.classList.add("is-hidden");
    return;
  }
  box.hidden = false;
  box.className = `aperture-state is-${kind}`;
  const titleTarget = $("#aperture-state-title");
  const copyTarget = $("#aperture-state-copy");
  if (titleTarget) titleTarget.textContent = title;
  if (copyTarget) copyTarget.textContent = copy;
  retry?.classList.toggle("is-hidden", kind !== "error");
}

function setShellBusy(scope) {
  const shell = $("#app-shell");
  if (!shell) return;
  if (scope) {
    shell.dataset.busy = scope;
    shell.setAttribute("aria-busy", "true");
    const [title, copy] = BUSY_STAGE_COPY[scope] || ["正在处理", ""];
    setApertureState("loading", title, copy);
  } else {
    delete shell.dataset.busy;
    shell.removeAttribute("aria-busy");
    setApertureState(null);
  }
}

function renderCueSkeleton() {
  const rail = $("#timeline-rail");
  if (!rail) return;
  rail.innerHTML = Array.from({ length: 5 }, (unused, index) =>
    `<li style="--at:${index * 20}%;--len:19%"><div class="cue-skeleton"></div></li>`).join("");
}

/* ---------- theme ---------- */

function currentTheme() {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

function applyTheme(theme, { persist = false } = {}) {
  const next = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = next;
  const meta = $("#theme-color");
  if (meta) meta.setAttribute("content", THEME_META[next]);
  const toggle = $("#theme-toggle");
  if (toggle) {
    const label = THEME_TOGGLE_COPY[next];
    toggle.setAttribute("aria-label", label);
    toggle.title = label;
    toggle.setAttribute("aria-pressed", String(next === "dark"));
  }
  if (persist) {
    try {
      window.localStorage.setItem(THEME_KEY, next);
    } catch {
      /* Private browsing can refuse storage; the session still keeps the choice. */
    }
  }
}

function setMessage(message, kind = "") {
  const element = $("#setup-message");
  const text = $("#setup-message-text");
  if (!element || !text) return;
  text.textContent = message || "";
  element.className = `form-message${kind ? ` is-${kind}` : ""}`;
  window.clearTimeout(setMessage.timer);
  if (!message) {
    delete element.dataset.open;
    return;
  }
  element.dataset.open = "true";
  if (kind !== "error") {
    setMessage.timer = window.setTimeout(() => { delete element.dataset.open; }, 7000);
  }
}

/* ---------- derived reads ---------- */

function tracesForNode(nodeId) {
  return (state.experiment?.traces || []).filter(trace => trace.timeline?.timeline_node_id === nodeId);
}

/* Individual records reference timeline nodes by id; a reader needs the event
   they can see on the track, with the id kept as the fallback. */
function eventLabelForNode(nodeId) {
  const event = (state.experiment?.events || []).find(candidate => candidate.node_id === nodeId);
  return event ? `${formatTime(event.t_start_ms)} ${event.label}` : nodeId;
}

function eventMetrics(event) {
  const traces = tracesForNode(event.node_id);
  return {
    traces,
    confusion: mean(traces.map(trace => trace.state?.after?.confusion)),
    attention: mean(traces.map(trace => trace.state?.after?.attention_proxy)),
    continueIntent: mean(traces.map(trace => trace.state?.after?.continue_intent)),
  };
}

function evidenceFrameURL(event) {
  const refs = (event.observations || []).flatMap(observation => observation.evidence_refs || []);
  for (const ref of refs) {
    if (ref.object_ref && state.experiment?.frame_urls?.[ref.object_ref]) {
      return state.experiment.frame_urls[ref.object_ref];
    }
  }
  return null;
}

function primaryEvidence(event) {
  for (const observation of event.observations || []) {
    for (const ref of observation.evidence_refs || []) {
      return { observation, ref };
    }
  }
  return null;
}

function timelineDurationMs() {
  const declared = Number(state.experiment?.timeline?.duration_ms);
  if (Number.isFinite(declared) && declared > 0) return declared;
  const events = state.experiment?.events || [];
  return events.length ? Number(events[events.length - 1].t_end_ms || 0) : 0;
}

/* ---------- capability, source and governance controls ---------- */

/* The head reports one word plus a dot. The full capability list belongs in the
   experiment drawer, where there is room to read it. */
function renderHealth() {
  const element = $("#system-state");
  const status = $("#native-model-status");
  const detail = $("#native-model-detail");
  const summary = $("#capability-detail");
  if (!element) return;
  if (!state.health?.capabilities) {
    element.textContent = "服务未连接";
    element.className = "system-state is-error";
    element.title = "读不到本机服务（/api/health）。请确认工作台服务仍在运行，然后刷新页面。";
    if (status) status.textContent = "未知";
    if (detail) detail.textContent = "读不到本机能力清单；请确认工作台服务仍在运行。";
    if (summary) summary.textContent = "读不到本机能力清单。请确认工作台服务仍在运行，然后刷新页面。";
    return;
  }
  const capabilities = state.health.capabilities;
  if (state.health.deployment_mode === "static_public_demo" || capabilities.static_public_demo) {
    state.deploymentMode = "static_public_demo";
    document.documentElement.dataset.deployment = "static-public-demo";
    element.textContent = "公开演示";
    element.className = "system-state is-demo";
    element.title = `只读合成 Fixture；不接收上传、不调用模型、不含真人数据。版本 ${state.health.version || "未知"}。`;
    if (status) status.textContent = "只读演示";
    if (detail) detail.textContent = "当前页面不调用视频模型。下载仓库并启动本机工作台后，才可解析已授权视频。";
    if (summary) summary.textContent = "只读公开演示 · 合成 Fixture · 0 位真人 · 不上传、不调用模型。完整能力需要本机工作台。";
    const deploymentLabel = $("#deployment-label");
    if (deploymentLabel) deploymentLabel.textContent = "公开体验";
    return;
  }
  const available = [
    capabilities.direct_video_url && "链接导入",
    capabilities.platform_video_url && "平台 Adapter",
    capabilities.local_video_decode && "本机解码",
    capabilities.gemini_native_video && "原生视频模型",
    capabilities.codex_frame_analysis && "证据帧分析",
    capabilities.human_calibration && "真人校准",
  ].filter(Boolean);
  const ledger = available.length ? available.join(" · ") : "工程基线";
  element.textContent = "本机就绪";
  element.className = "system-state is-ready";
  element.title = `可用能力：${ledger}。本机版本 ${state.health.version || "未知"}；远程处理默认关闭。`;
  if (summary) summary.textContent = `可用能力：${ledger}。远程处理默认关闭，每次调用都需要你单独授权。`;
  const nativeReady = Boolean(capabilities.gemini_native_video);
  const framesReady = Boolean(capabilities.codex_frame_analysis);
  if (status) status.textContent = nativeReady ? "整片可用" : framesReady ? "证据帧可用" : "未配置";
  if (detail) {
    detail.textContent = nativeReady
      ? "原生整片与证据帧两条路由都可用；发送范围随 Provider 切换。"
      : framesReady
        ? "证据帧路由可用；原生整片未配置，因此帧与帧之间的动作和声音仍是未知。"
        : "未配置远程事实层。本机解析与工程基线仍然可以跑完整流程。";
  }
}

/* The command bar is one clean line until there is something to import. Then the
   rights sentence and the source limits appear under it — never before. */
function updateCommandStage() {
  const form = $("#upload-form");
  if (!form) return;
  const mode = $('input[name="source_mode"]:checked')?.value || "url";
  const filled = mode === "upload"
    ? Boolean($("#video-file")?.files?.length)
    : Boolean($("#video-url")?.value?.trim());
  form.dataset.stage = filled ? "ready" : "idle";
}

function setSourceMode(mode) {
  $$("[data-source-panel]").forEach(panel => {
    const active = panel.dataset.sourcePanel === mode;
    panel.classList.toggle("is-hidden", !active);
    $$("input", panel).forEach(input => {
      input.disabled = !active;
      input.required = active;
    });
  });
  $$("[data-source-hint]").forEach(hint => {
    hint.classList.toggle("is-hidden", hint.dataset.sourceHint !== mode);
  });
  updateCommandStage();
}

/* Both the empty stage and the drawer offer the public sample; one handler. */
async function loadDemoExperiment(trigger) {
  setBusy(trigger, true);
  setMessage("正在载入公开合成样例。");
  try {
    await loadExperiment("demo");
    setPane("stage");
    setMessage("已载入公开合成样例。它没有原始画面，但时间轴、事件与代理量都是真实计算出来的：先选一个事件，再看右侧证据。", "success");
  } catch (error) {
    setMessage(`${error.message} 请确认本机服务仍在运行，然后重试。`, "error");
  } finally {
    setBusy(trigger, false);
  }
}

/* The paste field is the one place every flow starts, so several empty states
   point at it. */
function focusSourceField() {
  const radio = $('input[name="source_mode"][value="url"]');
  if (radio) radio.checked = true;
  setSourceMode("url");
  const input = $("#video-url");
  if (!input) return;
  input.focus();
  input.select();
  if (state.deploymentMode === "static_public_demo") {
    setMessage("公开体验版允许查看导入流程，但不会读取或发送链接；完整导入请运行本机工作台。", "error");
  }
}

function setAgentReasoner(reasoner) {
  const model = $("#agent-model");
  if (!model) return;
  model.innerHTML = (AGENT_REASONER_MODELS[reasoner] || AGENT_REASONER_MODELS["codex-cli"])
    .map(item => `<option value="${item.value}">${item.label}</option>`)
    .join("");
}

function updateVideoGovernance() {
  const provider = $("#provider")?.value || "codex-frames";
  const classification = state.experiment?.timeline?.data_handling?.data_classification || "unknown";
  const governance = $("#remote-governance");
  const scope = $("#video-remote-scope");
  const button = $("#analyze-button");
  if (!governance || !scope || !button) return;
  const heading = $("strong", governance);
  const copy = $("p", governance);
  if (heading) heading.textContent = `本次远程处理边界 · ${CLASSIFICATION_LABELS[classification] || classification}`;
  if (copy) {
    if (classification === "confidential" || classification === "restricted") {
      copy.textContent = "当前为机密／受限素材：公有模型路由会拒绝处理，请切换到经确认的私有部署 Adapter。";
    } else if (provider === "gemini") {
      copy.textContent = "Gemini 会接收完整视频与音轨；调用后请求删除临时文件，服务日志仍受当期 API 条款约束。";
    } else {
      copy.textContent = "Codex 只接收最多 12 张本地解码证据帧及时间戳；不发送原视频或音轨，帧间动作与声音保持未知。";
    }
  }
  scope.textContent = provider === "gemini"
    ? "授权本次把完整视频与音轨发送给 Gemini Native Video。"
    : "授权本次发送最多 12 张带时间戳证据帧；不发送原视频和音轨。";
  const label = $(".button-label", button);
  if (label) label.textContent = provider === "gemini" ? "分析完整视频" : "分析证据帧";
}

function setVideoProvider(provider) {
  const model = $("#provider-model");
  if (!model) return;
  model.innerHTML = (VIDEO_PROVIDER_MODELS[provider] || VIDEO_PROVIDER_MODELS["codex-frames"])
    .map(item => `<option value="${item.value}">${item.label}</option>`)
    .join("");
  updateVideoGovernance();
}

function setRuntimeMode(mode) {
  const isModel = mode === "model";
  $$("[data-model-runtime]").forEach(element => element.classList.toggle("is-hidden", !isModel));
  $$("[data-model-runtime] input").forEach(input => {
    input.disabled = !isModel;
    input.required = isModel;
  });
  $$("[data-model-runtime] select").forEach(select => { select.disabled = !isModel; });
}

/* ---------- shell navigation ---------- */

function revealElement(element, block = "start") {
  if (!element) return;
  const scrollParent = element.closest(".inspector-view, .rail");
  if (scrollParent && !isSinglePane()) {
    const parentBox = scrollParent.getBoundingClientRect();
    const elementBox = element.getBoundingClientRect();
    if (elementBox.top < parentBox.top || elementBox.bottom > parentBox.bottom) {
      element.scrollIntoView({ behavior: prefersStillness() ? "auto" : "smooth", block });
    }
    return;
  }
  element.scrollIntoView({ behavior: prefersStillness() ? "auto" : "smooth", block });
}

/* The experiment context, run settings and fact layer live in an overlay drawer
   on desktop and become a full panel on single-pane widths. */
function setDrawer(open, { focus = false } = {}) {
  const shell = $("#app-shell");
  const rail = $("#rail");
  if (!shell || !rail) return;
  if (isSinglePane()) {
    rail.inert = false;
    if (open) setPane("rail", focus);
    return;
  }
  const wasOpen = shell.dataset.drawer === "rail";
  // Read focus before inert is applied: making an ancestor inert blurs its child.
  const heldFocus = rail.contains(document.activeElement);
  shell.dataset.drawer = open ? "rail" : "closed";
  rail.inert = !open;
  $$("[data-drawer-target]").forEach(button => button.setAttribute("aria-expanded", String(open)));
  if (open && focus) $("#drawer-close")?.focus();
  // Returning focus only matters when the drawer actually held it.
  if (!open && wasOpen && heldFocus) $('[data-drawer-target="rail"]')?.focus();
  scheduleLightPath();
}

function isDrawerOpen() {
  return $("#app-shell")?.dataset.drawer === "rail";
}

function focusPane(pane) {
  if (pane === "inspector") {
    $(".inspector-tabs [role=tab][aria-selected='true']")?.focus({ preventScroll: true });
    return;
  }
  if (pane === "deck") {
    $(".pipeline button")?.focus({ preventScroll: true });
    return;
  }
  if (pane === "stage") {
    $("#timeline-rail button.is-selected")?.focus({ preventScroll: true });
  }
}

function setPane(pane, focus = false) {
  const shell = $("#app-shell");
  if (!shell || !PANES.includes(pane)) return;
  shell.dataset.pane = pane;
  $$("[data-pane-target]").forEach(button => {
    const active = button.dataset.paneTarget === pane;
    button.setAttribute("aria-pressed", String(active));
    if (active && focus) button.focus();
  });
  if (!isSinglePane() && pane === "rail") setDrawer(true);
  scheduleLightPath();
}

/* Desktop scrolls, so the head navigation moves the page instead of swapping
   panes. The inspector is sticky and always on screen; jumping to it means
   handing it the keyboard, not scrolling it into view. */
function scrollToPane(pane) {
  const target = $(PANE_SECTIONS[pane]);
  if (!target || pane === "inspector") return;
  target.scrollIntoView({ behavior: prefersStillness() ? "auto" : "smooth", block: "start" });
}

/* Pressed state reports where the reader actually is: inside the inspector, down
   at the ledger, or up at the picture. */
function syncHeadNav() {
  if (isSinglePane()) return;
  const inspector = $("#evidence-inspector");
  const deck = $("#deck")?.getBoundingClientRect();
  const active = inspector?.contains(document.activeElement)
    ? "inspector"
    : deck && deck.top < window.innerHeight * 0.62
      ? "deck"
      : "stage";
  $$(".head-nav [data-pane-target]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.paneTarget === active));
  });
}

function scheduleHeadNav() {
  window.cancelAnimationFrame(scheduleHeadNav.frame);
  scheduleHeadNav.frame = window.requestAnimationFrame(syncHeadNav);
}

function setInspectorView(view, focus = false) {
  if (!INSPECTOR_VIEWS.includes(view)) return;
  const tab = $(`[data-view="${view}"]`);
  const panel = $(`#view-${view}`);
  if (!tab || !panel) return;
  $$(".inspector-tabs [role=tab]").forEach(button => {
    const active = button === tab;
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  });
  $$(".inspector-view").forEach(candidate => {
    candidate.hidden = candidate !== panel;
  });
  if (focus) panel.focus({ preventScroll: true });
  syncLocation();
  scheduleLightPath();
}

function openRailGroup(selector) {
  const group = $(selector);
  if (!group) return;
  group.open = true;
  setDrawer(true);
  revealElement(group, "start");
}

/* Stage navigation moves the operator to the control that actually advances the
   run, not to a description of it. */
const STAGE_ACTIONS = {
  ingest: () => {
    focusSourceField();
  },
  analyze: () => {
    openRailGroup("#analyze-group");
    $("#provider")?.focus();
  },
  run: () => {
    openRailGroup("#run-group");
    $('select[name="runtime_mode"]')?.focus();
  },
  calibrate: () => {
    if (isSinglePane()) setPane("inspector");
    setInspectorView("calibration", true);
    revealElement($("#calibration-form"), "start");
  },
};

function currentInspectorView() {
  return $(".inspector-tabs [role=tab][aria-selected='true']")?.dataset.view || "evidence";
}

/* Deep links stay shareable: experiment, cue index and inspector view. */
function syncLocation() {
  if (!state.experiment) return;
  const url = new URL(window.location.href);
  url.searchParams.set("experiment", state.experiment.experiment_id);
  if ((state.experiment.events || []).length) {
    url.searchParams.set("cue", String(state.selectedEventIndex + 1));
  } else {
    url.searchParams.delete("cue");
  }
  const view = currentInspectorView();
  if (view === "evidence") url.searchParams.delete("view");
  else url.searchParams.set("view", view);
  const next = `${url.pathname}${url.search}`;
  if (next !== `${window.location.pathname}${window.location.search}`) {
    window.history.replaceState({}, "", next);
  }
}

/* ---------- rail renderers ---------- */

function renderSourceSummary() {
  const target = $("#source-summary");
  if (!target) return;
  const source = state.experiment?.source || {};
  if (!source.source_kind || source.source_kind === "fixture") {
    target.classList.add("is-hidden");
    return;
  }
  const sourceLabel = source.display_url || source.title || state.experiment.source_name || "本地文件";
  const methodLabels = {
    streamed_http: "公共直链",
    yt_dlp_platform_adapter: `${source.platform || "平台"} Adapter`,
    yt_dlp_progressive_adapter: `${source.platform || "平台"} 单文件 Adapter`,
    yt_dlp_split_streams_pyav_mux: `${source.platform || "平台"} 音视频合并 Adapter`,
    multipart_upload: "本地上传",
    local_artifact_recovery: "本地制品恢复",
  };
  const values = [
    sourceLabel,
    methodLabels[source.retrieval_method] || source.retrieval_method || "—",
    source.sensitive_query_parameters_persisted
      ? "包含敏感参数"
      : source.public_content_identifier_persisted
        ? "仅保留公开内容标识"
        : "不保存",
  ];
  $$("dd", target).forEach((element, index) => {
    element.textContent = values[index];
    element.title = values[index];
  });
  target.classList.remove("is-hidden");
}

function renderExperimentIndex() {
  const list = $("#recent-experiment-list");
  const count = $("#recent-experiment-count");
  if (!list || !count) return;
  count.textContent = String(state.experimentIndex.length);
  if (!state.experimentIndex.length) {
    list.innerHTML = state.deploymentMode === "static_public_demo"
      ? '<p class="empty-copy">公开体验版只包含当前合成实验；本机工作台会在这里恢复你自己的实验。</p>'
      : '<p class="empty-copy">还没有可恢复的本机实验。导入第一个视频后，它会出现在这里，随时可以再打开。</p>';
    return;
  }
  list.innerHTML = state.experimentIndex.map(item => {
    const active = item.experiment_id === state.experiment?.experiment_id;
    const status = EXPERIMENT_STATUS_LABELS[item.status] || item.status || "本地实验";
    const meta = [
      formatExperimentDuration(item.duration_ms),
      `${formatCount(item.event_count)} 段`,
      item.deep_personas ? `${formatCount(item.deep_personas)} Persona` : null,
    ].filter(Boolean).join(" · ");
    return `<button class="recent-experiment${active ? " is-current" : ""}" type="button" data-experiment-id="${escapeHTML(item.experiment_id)}" aria-current="${active ? "true" : "false"}">
      <span class="recent-experiment-title">${escapeHTML(item.title || item.experiment_id)}</span>
      <span class="recent-experiment-meta"><b>${escapeHTML(status)}</b>${escapeHTML(meta)}</span>
    </button>`;
  }).join("");
}

async function refreshExperimentIndex() {
  const payload = await fetchJSON("/api/experiments");
  state.experimentIndex = Array.isArray(payload.experiments) ? payload.experiments : [];
  renderExperimentIndex();
}

function renderLimitations() {
  const list = $("#limitations-list");
  const limitations = state.experiment?.limitations || [];
  if (!list || !limitations.length) return;
  list.innerHTML = limitations.map(item => `<li>${escapeHTML(item)}</li>`).join("");
}

function renderPipeline() {
  const experiment = state.experiment;
  let completedThrough = 0;
  if (experiment?.experiment_id && experiment.experiment_id !== "demo") completedThrough = 1;
  if (experiment?.timeline?.extensions?.semantic_analysis_complete) completedThrough = 2;
  if ((experiment?.traces || []).length) completedThrough = 3;
  if (experiment?.calibration) completedThrough = 4;
  const items = $$(".pipeline li");
  items.forEach((item, index) => {
    const complete = index < completedThrough;
    const active = completedThrough < items.length && index === completedThrough;
    item.classList.toggle("is-complete", complete);
    item.classList.toggle("is-active", active);
    const button = $("button", item);
    if (button) {
      if (active) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    }
    const status = $(".stage-status", item);
    if (status) status.textContent = complete ? "· 已完成" : active ? "· 当前" : "· 待开始";
  });
  const scope = $("#pipeline-scope");
  if (scope) {
    scope.textContent = completedThrough >= items.length
      ? `四步已全部完成 · 点任一步可回到对应操作`
      : `已完成 ${completedThrough} / ${items.length} 步 · 点任一步跳到对应操作`;
  }
}

function renderScale() {
  const counts = state.experiment?.counts || {};
  const values = [
    counts.persona_pool_records,
    counts.deep_personas,
    counts.deep_trace_events,
    counts.human_participants,
  ];
  $$("#scale-values [data-count]").forEach((element, index) => {
    element.textContent = formatCount(values[index]);
  });
}

function renderReceipts() {
  const list = $("#receipt-list");
  const count = $("#receipt-count");
  if (!list || !count) return;
  const receipts = state.experiment?.remote_processing_receipts || [];
  count.textContent = String(receipts.length);
  if (!receipts.length) {
    list.innerHTML = '<p class="empty-copy">本实验还没有远程调用，所有解析都在本机完成。一旦你授权某次远程处理，这里会留下可核对的凭据。</p>';
    return;
  }
  list.innerHTML = [...receipts].reverse().map(receipt => {
    const outcome = String(receipt.outcome || "started");
    const scope = PAYLOAD_SCOPE_LABELS[receipt.payload_scope] || receipt.payload_scope || "范围未记录";
    const classification = CLASSIFICATION_LABELS[receipt.data_classification] || receipt.data_classification || "未标记";
    return `<div class="receipt" data-outcome="${escapeHTML(outcome)}">
      <div class="receipt-head">
        <b>${escapeHTML(receipt.provider || "未知 Provider")}${receipt.model ? ` / ${escapeHTML(receipt.model)}` : ""}</b>
        <span>${escapeHTML(RECEIPT_OUTCOME_LABELS[outcome] || outcome)}</span>
      </div>
      <p>${escapeHTML(classification)} · ${escapeHTML(formatStamp(receipt.confirmed_at))}</p>
      <p>${escapeHTML(scope)}</p>
    </div>`;
  }).join("");
}

/* ---------- deck renderers ---------- */

function renderDeckMetrics() {
  const summaries = (state.experiment?.events || []).map(eventMetrics);
  const values = [
    mean(summaries.map(item => item.confusion)),
    mean(summaries.map(item => item.attention)),
    mean(summaries.map(item => item.continueIntent)),
  ];
  $$("#deck-metrics > div").forEach((row, index) => {
    const unit = unitValue(values[index]);
    row.dataset.state = unit == null ? "empty" : "value";
    row.style.setProperty("--v", unit ?? 0);
    const target = $("[data-metric]", row);
    if (target) target.textContent = formatPercent(values[index]);
  });
  const scope = $("#deck-scope");
  if (scope) {
    const traceCount = state.experiment?.traces?.length || 0;
    scope.textContent = traceCount
      ? `${formatCount(state.experiment?.counts?.deep_personas)} 个 AI 观众 · ${formatCount(traceCount)} 条记录 · 未校准`
      : "让 AI 观众逐段体验后显示全片代理量";
  }
}

function renderCalibrationStatus() {
  const target = $("#calibration-status");
  if (!target) return;
  const calibration = state.experiment?.calibration;
  const humans = state.experiment?.counts?.human_participants ?? 0;
  const topRecall = calibration?.top_issue_recall?.recall;
  const timeRecall = calibration?.timestamp_issue_recall?.recall;
  const values = [
    { text: formatCount(humans), empty: !humans },
    { text: topRecall == null ? "未校准" : formatPercent(topRecall), empty: topRecall == null },
    { text: timeRecall == null ? "未校准" : formatPercent(timeRecall), empty: timeRecall == null },
  ];
  $$("dd", target).forEach((element, index) => {
    element.textContent = values[index].text;
    element.dataset.state = values[index].empty ? "empty" : "value";
  });
}

/* ---------- stage: one time coordinate system ---------- */

function timeToPercent(milliseconds, duration) {
  if (!duration) return 0;
  return clamp((Number(milliseconds || 0) / duration) * 100, 0, 100);
}

/* Tick density follows the rendered width so labels never collide. */
function rulerStepMs(duration) {
  const visible = $("#track-scroll")?.clientWidth || 620;
  const trackWidth = Math.max(240, visible * zoomFactor());
  const maxLabels = Math.max(2, Math.floor(trackWidth / 78));
  const target = duration / 1000 / maxLabels;
  const step = RULER_STEPS_SECONDS.find(candidate => candidate >= target);
  return (step || RULER_STEPS_SECONDS[RULER_STEPS_SECONDS.length - 1]) * 1000;
}

/* The ruler is continuous: ticks come from elapsed time, never from card order. */
function renderCueRuler(events) {
  const ruler = $("#cue-ruler");
  if (!ruler) return;
  const duration = timelineDurationMs();
  if (!events.length || !duration) {
    ruler.innerHTML = "";
    return;
  }
  const step = rulerStepMs(duration);
  const ticks = [];
  for (let at = 0; at < duration - step * 0.4; at += step) {
    ticks.push(`<li style="--at:${timeToPercent(at, duration).toFixed(3)}%">${formatTime(at)}</li>`);
  }
  ticks.push(`<li data-edge="end" style="--at:100%">${formatTime(duration)}</li>`);
  ruler.innerHTML = ticks.join("");
}

function renderTimelineRail() {
  const rail = $("#timeline-rail");
  const events = state.experiment?.events || [];
  const scope = $("#cue-scope");
  if (!rail) return;
  // Every card is about to be replaced, so a borrowed aim would point at a
  // detached node.
  state.beamHint = null;
  if (!events.length) {
    state.timelineFloorPx = 0;
    applyTimelineFloor();
    rail.innerHTML = '<li class="empty-copy">还没有事件。导入一个视频，这里会按真实时间排出可点击的事件卡片。</li>';
    if (scope) scope.textContent = "导入素材后，这里按真实时间排布事件。";
    renderCueRuler(events);
    return;
  }
  const duration = timelineDurationMs();
  const shortestSpan = Math.min(...events.map(event =>
    Math.max(1000, Number(event.t_end_ms || 0) - Number(event.t_start_ms || 0))));
  state.timelineFloorPx = duration
    ? clamp(Math.ceil((48 * duration) / shortestSpan), 0, 12000)
    : Math.max(0, events.length * 48);
  applyTimelineFloor();
  rail.innerHTML = events.map((event, index) => {
    const start = Number(event.t_start_ms || 0);
    const end = Number(event.t_end_ms || 0);
    const span = Math.max(1000, end - start);
    const at = duration ? timeToPercent(start, duration) : (index / events.length) * 100;
    const length = duration
      ? Math.max(0.6, Math.min(100 - at, (span / duration) * 100))
      : 100 / events.length;
    const selected = index === state.selectedEventIndex;
    return `<li style="--at:${at.toFixed(3)}%;--len:${length.toFixed(3)}%">
      <button type="button" data-event-index="${index}" data-time="${escapeHTML(formatTime(start))}"
        class="${selected ? "is-selected" : ""}"
        title="${escapeHTML(event.label)}"
        aria-label="事件 ${index + 1}：${escapeHTML(formatTime(start))} 至 ${escapeHTML(formatTime(end))}，时长 ${escapeHTML(formatSpan(span))}，${escapeHTML(event.label)}"
        ${selected ? 'aria-current="true"' : ""}>
        <span class="cue-mark" aria-hidden="true"></span>
        <span class="cue-time">${escapeHTML(formatTime(start))}</span>
        <span class="cue-label">${escapeHTML(event.label)}</span>
        <span class="cue-span">${escapeHTML(formatSpan(span))}</span>
      </button>
    </li>`;
  }).join("");
  if (scope) {
    scope.textContent = `${events.length} 个事件 · 总长 ${formatTime(duration)} · 卡片宽度就是时长；← → 切换事件，Home／End 到首尾`;
  }
  $$("[data-event-index]", rail).forEach(button => {
    button.addEventListener("click", () => selectEvent(Number(button.dataset.eventIndex)));
    // Hover and keyboard focus preview the route to the evidence anchor: the grain
    // says "this row is joined to the picture", the spark says where.
    button.addEventListener("pointerenter", () => aimLightPath(button, { animate: true }));
    button.addEventListener("pointerleave", () => {
      if (state.beamHint === button) aimLightPath(null);
    });
    button.addEventListener("focus", () => {
      if (button.matches(":focus-visible")) aimLightPath(button, { animate: true });
    });
    button.addEventListener("blur", () => {
      if (state.beamHint === button) aimLightPath(null);
    });
    button.addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const current = Number(button.dataset.eventIndex);
      const next = event.key === "Home"
        ? 0
        : event.key === "End"
          ? events.length - 1
          : Math.min(events.length - 1, Math.max(0, current + (event.key === "ArrowRight" ? 1 : -1)));
      selectEvent(next);
      $(`[data-event-index="${next}"]`, rail)?.focus();
    });
  });
  renderCueRuler(events);
}

/* Catmull-Rom through the event midpoints; no interpolation beyond the measured
   points, and nothing is drawn where no trace exists. */
function smoothPath(points) {
  if (!points.length) return "";
  if (points.length === 1) {
    return `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)} L ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;
  }
  let path = `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;
  for (let index = 0; index < points.length - 1; index += 1) {
    const previous = points[Math.max(0, index - 1)];
    const current = points[index];
    const next = points[index + 1];
    const following = points[Math.min(points.length - 1, index + 2)];
    const tension = 0.2;
    const c1x = current.x + (next.x - previous.x) * tension;
    const c1y = current.y + (next.y - previous.y) * tension;
    const c2x = next.x - (following.x - current.x) * tension;
    const c2y = next.y - (following.y - current.y) * tension;
    path += ` C ${c1x.toFixed(2)} ${c1y.toFixed(2)} ${c2x.toFixed(2)} ${c2y.toFixed(2)} ${next.x.toFixed(2)} ${next.y.toFixed(2)}`;
  }
  return path;
}

function curveY(value) {
  const unit = clamp(Number(value), 0, 1);
  return CURVE_BOTTOM - unit * (CURVE_BOTTOM - CURVE_TOP);
}

function renderProxyCurves() {
  const svg = $("#proxy-curve");
  const nodes = $("#curve-nodes");
  const empty = $("#curve-empty");
  const legend = $("#curve-legend");
  if (!svg || !empty) return;
  const events = state.experiment?.events || [];
  const duration = timelineDurationMs();
  const samples = events.map((event, index) => {
    const metrics = eventMetrics(event);
    const middle = (Number(event.t_start_ms || 0) + Number(event.t_end_ms || 0)) / 2;
    return {
      index,
      x: duration ? timeToPercent(middle, duration) : ((index + 0.5) / Math.max(1, events.length)) * 100,
      attention: metrics.attention,
      confusion: metrics.confusion,
      hasData: metrics.traces.length > 0,
    };
  });
  const attention = samples.filter(sample => Number.isFinite(Number(sample.attention)));
  const confusion = samples.filter(sample => Number.isFinite(Number(sample.confusion)));
  if (!attention.length && !confusion.length) {
    svg.innerHTML = "";
    if (nodes) nodes.innerHTML = "";
    empty.hidden = false;
    if (legend) legend.dataset.state = "empty";
    return;
  }
  empty.hidden = true;
  if (legend) legend.dataset.state = "value";
  const selected = samples[state.selectedEventIndex];
  const series = [
    { rows: confusion, key: "confusion", className: "series-confusion", dot: "confusion", area: false },
    { rows: attention, key: "attention", className: "series-attention", dot: "attention", area: true },
  ];
  // currentColor keeps the fill on the accent in both themes: the lane sets the
  // colour in CSS, so no repaint is needed when the theme changes.
  const shapes = [`<defs><linearGradient id="curve-fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="currentColor" stop-opacity=".2"></stop>
      <stop offset="1" stop-color="currentColor" stop-opacity="0"></stop>
    </linearGradient></defs>`];
  const markers = [];
  series.forEach(item => {
    if (!item.rows.length) return;
    const points = item.rows.map(row => ({ x: row.x, y: curveY(row[item.key]) }));
    const line = smoothPath(points);
    // A soft fill under the primary series so a flat reading still reads as a curve.
    if (item.area && points.length > 1) {
      shapes.push(`<path class="series-area" d="${line} L ${points[points.length - 1].x.toFixed(2)} 100 L ${points[0].x.toFixed(2)} 100 Z"></path>`);
    }
    shapes.push(`<path class="${item.className}" vector-effect="non-scaling-stroke" d="${line}"></path>`);
    // Markers live in HTML: the SVG stretches non-uniformly and would oval them.
    item.rows.forEach(row => {
      const isSelected = Boolean(selected && row.index === selected.index);
      markers.push(`<i data-series="${item.dot}"${isSelected ? ' class="is-selected"' : ""} style="left:${row.x.toFixed(3)}%;top:${curveY(row[item.key]).toFixed(3)}%"></i>`);
    });
  });
  svg.innerHTML = shapes.join("");
  if (nodes) nodes.innerHTML = markers.join("");
}

function updatePlayhead() {
  const playhead = $("#track-playhead");
  const label = $("#playhead-time");
  if (!playhead) return;
  const events = state.experiment?.events || [];
  const event = events[state.selectedEventIndex];
  const duration = timelineDurationMs();
  if (!event || !duration) {
    playhead.hidden = true;
    return;
  }
  playhead.hidden = false;
  const at = timeToPercent(event.t_start_ms, duration);
  playhead.style.setProperty("--at", `${at.toFixed(3)}%`);
  playhead.dataset.align = at > 86 ? "end" : "start";
  if (label) label.textContent = formatTime(event.t_start_ms);
}

/* The dashed marker follows real playback, so the picture and the curve agree.
   No source means no playback: null must hide the marker rather than pin it to
   zero, which Number(null) would otherwise do. */
function updatePlaymark(seconds) {
  const mark = $("#track-playmark");
  if (!mark) return;
  const duration = timelineDurationMs();
  if (seconds == null || !Number.isFinite(Number(seconds)) || !duration) {
    mark.hidden = true;
    return;
  }
  mark.hidden = false;
  mark.style.setProperty("--at", `${timeToPercent(Number(seconds) * 1000, duration).toFixed(3)}%`);
}

function setZoom(index) {
  const next = clamp(index, 0, ZOOM_STEPS.length - 1);
  state.zoomIndex = next;
  const track = $("#track");
  if (track) track.style.setProperty("--zoom", String(ZOOM_STEPS[next]));
  applyTimelineFloor();
  const label = $("#zoom-level");
  if (label) label.textContent = `${ZOOM_STEPS[next]}×`;
  const out = $("#zoom-out");
  const zoomIn = $("#zoom-in");
  if (out) out.disabled = next === 0;
  if (zoomIn) zoomIn.disabled = next === ZOOM_STEPS.length - 1;
  renderCueRuler(state.experiment?.events || []);
  keepCueVisible($("#timeline-rail button.is-selected"));
  scheduleLightPath();
}

function applyTimelineFloor() {
  const track = $("#track");
  if (!track) return;
  if (!state.timelineFloorPx) {
    track.style.removeProperty("--track-floor");
    return;
  }
  const scaled = Math.min(30000, state.timelineFloorPx * ZOOM_STEPS[state.zoomIndex]);
  track.style.setProperty("--track-floor", `${Math.ceil(scaled)}px`);
}

function renderApertureChips(event) {
  const classification = state.experiment?.timeline?.data_handling?.data_classification || "unknown";
  const label = CLASSIFICATION_LABELS[classification] || classification;
  const tag = $("#aperture-tag");
  const timecode = $("#aperture-timecode");
  if (timecode) timecode.textContent = event ? formatTime(event.t_start_ms) : "00:00";
  if (!tag) return;
  tag.textContent = state.experiment?.media_url ? `${label} · 原视频` : `${label} · 合成样例`;
  tag.classList.toggle("is-restricted", classification === "confidential" || classification === "restricted");
}

/* Intrinsic aspect keeps portrait and landscape sources fully visible and keeps
   the native control bar aligned with the actual picture instead of the pane. */
function trackMediaAspect(video) {
  const stage = $("#media-stage");
  if (!stage || !video) return;
  const apply = () => {
    if (video.videoWidth > 0 && video.videoHeight > 0) {
      stage.style.setProperty("--media-aspect", `${video.videoWidth} / ${video.videoHeight}`);
    }
  };
  apply();
  video.addEventListener("loadedmetadata", apply);
  video.addEventListener("resize", apply);
}

function trackPlaybackPosition(video) {
  if (!video) return;
  const sync = () => {
    updatePlaymark(video.currentTime);
    const timecode = $("#aperture-timecode");
    if (timecode) timecode.textContent = formatTime(video.currentTime * 1000);
  };
  video.addEventListener("timeupdate", sync);
  video.addEventListener("seeked", sync);
  video.addEventListener("emptied", () => updatePlaymark(null));
}

/* The emulsion canvas has to outlive every source swap, so it is detached, the
   new source is written, and it is re-appended last. Absolute positioning keeps
   it over the picture either way; being last also keeps the DOM honest. */
function setStageSource(stage, html) {
  const canvas = $("#emulsion", stage);
  stage.innerHTML = html;
  if (canvas) stage.append(canvas);
}

function renderMediaEvidence(event, frameURL) {
  const stage = $("#media-stage");
  const links = $("#media-evidence-links");
  const aperture = $("#aperture");
  const mediaURL = state.experiment?.media_url;
  if (!stage || !links || !aperture) return;
  if (mediaURL) {
    let video = $("#source-video", stage);
    if (!video || video.dataset.experimentId !== state.experiment.experiment_id) {
      stage.style.removeProperty("--media-aspect");
      setStageSource(stage, `<video id="source-video" controls playsinline preload="metadata" aria-label="原视频证据，包含声音" data-experiment-id="${escapeHTML(state.experiment.experiment_id)}" src="${escapeHTML(mediaURL)}">浏览器无法播放该原视频；请使用下方原始制品链接。</video>`);
      video = $("#source-video", stage);
      trackMediaAspect(video);
      trackPlaybackPosition(video);
    }
    aperture.dataset.state = "video";
    if (frameURL) video.poster = frameURL;
    const seekSeconds = Number(event.t_start_ms || 0) / 1000;
    const seek = () => {
      if (Number.isFinite(seekSeconds)) video.currentTime = seekSeconds;
      updatePlaymark(seekSeconds);
    };
    if (video.readyState >= 1) seek();
    else video.addEventListener("loadedmetadata", seek, { once: true });
    const audioLink = state.experiment.audio_url
      ? `<a href="${escapeHTML(state.experiment.audio_url)}" target="_blank" rel="noreferrer">抽取音轨 WAV</a>`
      : "<span>源文件里没有可抽取的音轨</span>";
    links.innerHTML = `<a href="${escapeHTML(mediaURL)}" target="_blank" rel="noreferrer">原视频制品</a>${audioLink}`;
    // Trigger 2 and 3: the picture behind this cue is a different frame of the
    // same source, so the well condenses again — lightly.
    const videoKey = `video:${state.experiment.experiment_id}:${event.node_id}`;
    requestEmulsion(videoKey, emulsionKind(videoKey));
    return;
  }
  links.innerHTML = "";
  stage.style.removeProperty("--media-aspect");
  updatePlaymark(null);
  if (frameURL) {
    aperture.dataset.state = "frame";
    setStageSource(stage, `<img src="${escapeHTML(frameURL)}" alt="${escapeHTML(event.label)} 的解码证据帧">`);
    requestEmulsion(`frame:${frameURL}`, emulsionKind(`frame:${frameURL}`));
    return;
  }
  aperture.dataset.state = "slate";
  setStageSource(stage, `<div class="aperture-slate">
    <span class="slate-label">本段没有原始画面</span>
    <strong>${escapeHTML(event.label)}</strong>
    <span class="slate-time">${escapeHTML(formatTime(event.t_start_ms))} – ${escapeHTML(formatTime(event.t_end_ms))}</span>
    <p>${escapeHTML(event.summary || "这份公开样例不含原始画面，只保留事件与观察。")}</p>
    <p class="slate-note">时间轴、事件与代理量都可以照常读。粘贴一个已获授权的链接，这里就会换成真实画面和解码出的证据帧。</p>
    <div class="stage-actions">
      <button class="stage-action" type="button" data-focus-source>粘贴链接开始</button>
    </div>
  </div>`);
  // A synthetic fixture develops once per experiment, never once per cue.
  requestEmulsion(`slate:${state.experiment?.experiment_id || "none"}`, "slate");
}

/* ---------- inspector renderers ---------- */

function renderEvidenceClaim(event, traces) {
  const target = $("#evidence-claim");
  if (!target) return;
  const evidence = primaryEvidence(event);
  if (!evidence) {
    target.innerHTML = '<p class="empty-copy">该时间片没有登记证据引用。</p>';
    return;
  }
  const { observation, ref } = evidence;
  const hash = ref.content_hash ? `${ref.hash_algorithm || "hash"}:${String(ref.content_hash).slice(0, 12)}` : "无哈希";
  const ordered = [...traces].sort((a, b) => (b.state?.after?.confusion || 0) - (a.state?.after?.confusion || 0));
  const focus = ordered[0];
  const quote = focus
    ? `<blockquote class="claim-quote">
        <p>${escapeHTML(focus.reaction?.summary || focus.observation?.summary || "该 Trace 未记录反应摘要。")}</p>
        <footer>${escapeHTML(focus.agent_id)} · ${escapeHTML(focus.segment_id || "未分群")} · 代理量反应，不是真人发言</footer>
      </blockquote>`
    : "";
  target.innerHTML = `
    <div class="claim-hit">
      <time>命中 ${escapeHTML(formatTime(ref.t_start_ms))}</time>
      <span data-epistemic="${escapeHTML(observation.epistemic_status || "")}">${escapeHTML(MODALITY_LABELS[observation.modality] || observation.modality)} · ${escapeHTML(epistemicLabel(observation.epistemic_status))}</span>
    </div>
    <p class="claim-excerpt">${escapeHTML(ref.excerpt || observation.text)}</p>
    <p class="claim-source">${escapeHTML(observation.observation_id)} · ${escapeHTML(hash)}</p>
    ${quote}`;
}

function renderObservations(event) {
  const target = $("#observations");
  if (!target) return;
  const observations = event.observations || [];
  target.innerHTML = observations.length
    ? observations.map(observation => `<li data-epistemic="${escapeHTML(observation.epistemic_status || "")}">${escapeHTML(observation.text)}
        <span class="observation-meta">${escapeHTML(MODALITY_LABELS[observation.modality] || observation.modality)} · <b data-epistemic="${escapeHTML(observation.epistemic_status || "")}">${escapeHTML(epistemicLabel(observation.epistemic_status))}</b> · 置信 ${formatPercent(observation.confidence)}</span>
      </li>`).join("")
    : '<li class="empty-copy">尚无观察。</li>';
}

function renderExtremes(event, traces) {
  const target = $("#event-extremes");
  if (!target) return;
  if (!traces.length) {
    target.className = "empty-copy";
    target.textContent = "让 AI 观众逐段体验之后，这里显示反应最强的 Persona 和一个反例。";
    return;
  }
  const ordered = [...traces].sort((a, b) => (b.state?.after?.confusion || 0) - (a.state?.after?.confusion || 0));
  const high = ordered[0];
  const low = ordered[ordered.length - 1];
  target.className = "";
  target.innerHTML = `
    <div class="extreme-row"><span>高困惑</span><button class="evidence-button" type="button" data-open-agent="${escapeHTML(high.agent_id)}" data-open-trace="${escapeHTML(high.trace_event_id)}">${escapeHTML(high.agent_id)} · ${formatPercent(high.state?.after?.confusion)}</button></div>
    <div class="extreme-row"><span>反例</span><button class="evidence-button" type="button" data-open-agent="${escapeHTML(low.agent_id)}" data-open-trace="${escapeHTML(low.trace_event_id)}">${escapeHTML(low.agent_id)} · ${formatPercent(low.state?.after?.confusion)}</button></div>
  `;
  $$("[data-open-agent]", target).forEach(button => {
    button.addEventListener("click", () => openTrace(button.dataset.openAgent, button.dataset.openTrace));
  });
}

function proxyCell(value) {
  const unit = unitValue(value);
  return `<span class="cell-meter" style="--v:${unit ?? 0}"><b>${formatPercent(value)}</b><span class="meter" aria-hidden="true"></span></span>`;
}

function renderEventTable() {
  const events = state.experiment?.events || [];
  const body = $("#event-table-body");
  if (!body) return;
  if (!events.length) {
    body.innerHTML = '<tr><td colspan="5">尚无时间轴。</td></tr>';
    return;
  }
  body.innerHTML = events.map((event, index) => {
    const metrics = eventMetrics(event);
    const traces = [...metrics.traces].sort((a, b) => (b.state?.after?.confusion || 0) - (a.state?.after?.confusion || 0));
    const high = traces[0];
    const low = traces[traces.length - 1];
    const drill = high
      ? `<small>高：<button type="button" class="evidence-button" data-open-agent="${escapeHTML(high.agent_id)}" data-open-trace="${escapeHTML(high.trace_event_id)}">${escapeHTML(high.agent_id)}</button>${low && low !== high ? ` · 反例：<button type="button" class="evidence-button" data-open-agent="${escapeHTML(low.agent_id)}" data-open-trace="${escapeHTML(low.trace_event_id)}">${escapeHTML(low.agent_id)}</button>` : ""}</small>`
      : "";
    return `<tr>
      <td class="numeric">${formatTime(event.t_start_ms)}</td>
      <td><span class="evidence-cell"><button type="button" class="evidence-button" data-table-event="${index}">${escapeHTML(event.label)}</button>${drill}</span></td>
      <td class="numeric">${proxyCell(metrics.confusion)}</td>
      <td class="numeric">${proxyCell(metrics.attention)}</td>
      <td class="numeric">${proxyCell(metrics.continueIntent)}</td>
    </tr>`;
  }).join("");
  $$("[data-table-event]", body).forEach(button => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.tableEvent);
      selectEvent(index);
      setInspectorView("evidence");
      setPane("stage");
      window.requestAnimationFrame(() => $(`[data-event-index="${index}"]`)?.focus());
    });
  });
  $$("[data-open-agent]", body).forEach(button => {
    button.addEventListener("click", () => openTrace(button.dataset.openAgent, button.dataset.openTrace));
  });
}

function renderTraces() {
  const target = $("#trace-list");
  const filterInput = $("#persona-filter");
  if (!target) return;
  const traces = state.experiment?.traces || [];
  const personas = new Map((state.experiment?.personas || []).map(persona => [persona.persona_id, persona]));
  const filter = (filterInput?.value || "").trim().toLowerCase();
  const currentNode = (state.experiment?.events || [])[state.selectedEventIndex]?.node_id;
  const sessions = new Map();
  traces.forEach(trace => {
    const list = sessions.get(trace.agent_id) || [];
    list.push(trace);
    sessions.set(trace.agent_id, list);
  });
  if (!sessions.size) {
    target.innerHTML = '<p class="empty-copy">还没有个体记录。让 AI 观众逐段体验之后，每个 Persona 都会变成一条可以单独回放的通道。</p>';
    return;
  }
  const visible = [...sessions.entries()].filter(([agentId]) => {
    const persona = personas.get(agentId) || {};
    return !filter || `${agentId} ${persona.segment_id || ""}`.toLowerCase().includes(filter);
  });
  if (!visible.length) {
    target.innerHTML = '<p class="empty-copy">没有匹配的 Persona。清空筛选框即可恢复全部个体记录。</p>';
    return;
  }
  target.innerHTML = visible.map(([agentId, sessionTraces]) => {
    const ordered = [...sessionTraces].sort((a, b) => a.session_sequence_no - b.session_sequence_no);
    const final = ordered[ordered.length - 1];
    const persona = personas.get(agentId) || {};
    const channel = ordered.map(trace => {
      const node = trace.timeline?.timeline_node_id;
      return `<i data-node="${escapeHTML(node)}" class="${node === currentNode ? "is-current" : ""}" style="--v:${unitValue(trace.state?.after?.continue_intent) ?? 0}"></i>`;
    }).join("");
    const rows = ordered.map(trace => `<tr class="trace-event" id="trace-${escapeHTML(trace.trace_event_id)}" tabindex="-1">
      <td class="numeric">${formatTime(trace.timeline.t_start_ms)}</td>
      <td><button type="button" class="evidence-button" data-trace-event-node="${escapeHTML(trace.timeline.timeline_node_id)}" title="回到该事件">${escapeHTML(eventLabelForNode(trace.timeline.timeline_node_id))}</button></td>
      <td>${escapeHTML(reactionLabel(trace.reaction?.reaction_type))}<small>${escapeHTML(trace.reaction?.summary || "")}</small></td>
      <td class="numeric">${formatPercent(trace.state?.after?.confusion)}</td>
      <td class="numeric">${formatPercent(trace.state?.after?.continue_intent)}</td>
      <td>${escapeHTML(actionLabel(trace.action?.action_type))}<small>${escapeHTML(reasonBeyondLabel(trace.action?.reason_summary, actionLabel(trace.action?.action_type)))}</small></td>
      <td><code>${escapeHTML(trace.evidence?.[0]?.timeline_observation_id || "—")}</code></td>
    </tr>`).join("");
    return `<details class="trace-session" id="session-${escapeHTML(agentId)}" data-agent="${escapeHTML(agentId)}">
      <summary>
        <span class="session-name"><strong>${escapeHTML(agentId)}</strong><small>${escapeHTML(persona.segment_id || final.segment_id || "未分群")}</small></span>
        <span class="channel-strip" aria-hidden="true" title="按事件顺序的继续意向代理量">${channel}</span>
        <span class="session-outcome">理解 ${formatPercent(final.state?.after?.comprehension)} · 困惑 ${formatPercent(final.state?.after?.confusion)} · 继续 ${formatPercent(final.state?.after?.continue_intent)}</span>
      </summary>
      <div class="trace-body table-wrap">
        <table><thead><tr><th scope="col">时间</th><th scope="col">事件</th><th scope="col">反应</th><th scope="col">困惑</th><th scope="col">继续</th><th scope="col">动作</th><th scope="col">证据 ID</th></tr></thead><tbody>${rows}</tbody></table>
      </div>
    </details>`;
  }).join("");
  $$("[data-trace-event-node]", target).forEach(button => {
    button.addEventListener("click", () => {
      const index = (state.experiment?.events || []).findIndex(event => event.node_id === button.dataset.traceEventNode);
      if (index >= 0) selectEvent(index);
      setInspectorView("evidence");
      setPane("stage");
      window.requestAnimationFrame(() => $(`[data-event-index="${index}"]`)?.focus());
    });
  });
}

function renderCalibration() {
  const target = $("#calibration-results");
  if (!target) return;
  const calibration = state.experiment?.calibration;
  if (!calibration) {
    target.innerHTML = "<strong>还没有真人数据</strong><p>上传一份同任务的真人锚点文件，这里会报告 Top 问题召回、时间点召回、同名代理量误差和 A/B 方向一致性。在那之前，本页数值都不能当作对现实的预测。</p>";
    return;
  }
  const topRecall = calibration.top_issue_recall?.recall;
  const timeRecall = calibration.timestamp_issue_recall?.recall;
  const mae = calibration.numeric_proxy_alignment?.mean_absolute_error;
  const ab = calibration.ab_direction || {};
  const abText = ab.direction_agreement == null
    ? "无法计算"
    : ab.direction_agreement
      ? "一致"
      : "不一致";
  target.innerHTML = `
    <strong>同任务校准结果</strong>
    <p>${formatCount(calibration.scope?.human_participants)} 位真人与 ${formatCount(calibration.scope?.agent_sessions)} 个 Agent Session 分开报告；已排除 ${formatCount(calibration.scope?.withdrawn_anchors_excluded)} 条撤回锚点。</p>
    <dl>
      <div><dt>Top 问题召回</dt><dd>${topRecall == null ? "无法计算" : formatPercent(topRecall)}</dd></div>
      <div><dt>时间点召回</dt><dd>${timeRecall == null ? "无法计算" : formatPercent(timeRecall)}</dd></div>
      <div><dt>同名代理量 MAE</dt><dd>${mae == null ? "无法计算" : Number(mae).toFixed(3)}</dd></div>
      <div><dt>A/B 方向</dt><dd>${abText}</dd></div>
    </dl>
    <p>${escapeHTML(calibration.numeric_proxy_alignment?.warning || "")}</p>`;
}

/* ---------- selection ---------- */

function renderEmptySelection() {
  const timecode = $("#current-timecode");
  const label = $("#current-label");
  const position = $("#current-position");
  const review = $("#review-status");
  const summary = $("#event-summary");
  const inspectorTitle = $("#inspector-title");
  const inspectorTime = $("#inspector-timecode");
  if (timecode) timecode.textContent = "00:00–00:00";
  if (label) label.textContent = "还没有时间轴";
  if (position) position.textContent = "0 / 0";
  if (inspectorTitle) inspectorTitle.textContent = "还没有选择事件";
  if (inspectorTime) inspectorTime.textContent = "00:00–00:00";
  if (review) {
    review.textContent = "未选择";
    review.removeAttribute("data-tone");
  }
  if (summary) summary.textContent = "先导入一个视频，或载入公开样例；然后在时间轴上选一个事件，这里会显示它的多模态事实。";
  $$("#event-metrics > div").forEach(row => {
    row.dataset.state = "empty";
    row.style.setProperty("--v", 0);
    const value = $("[data-metric]", row);
    if (value) value.textContent = "—";
  });
  const observations = $("#observations");
  if (observations) observations.innerHTML = '<li class="empty-copy">还没有观察记录。</li>';
  const claim = $("#evidence-claim");
  if (claim) claim.innerHTML = '<p class="empty-copy">选中事件后，这里显示该时间片引用的证据与来源标识。</p>';
  const extremes = $("#event-extremes");
  if (extremes) {
    extremes.className = "empty-copy";
    extremes.textContent = "让 AI 观众逐段体验之后，这里显示反应最强的 Persona 和一个反例。";
  }
  const prev = $("#cue-prev");
  const next = $("#cue-next");
  if (prev) prev.disabled = true;
  if (next) next.disabled = true;
  renderApertureChips(null);
  renderProxyCurves();
  updatePlayhead();
  updatePlaymark(null);
  state.beamHint = null;
  $("#light-path")?.classList.remove("is-live", "is-tracing", "is-hint");
}

function keepCueVisible(button) {
  const scroller = $("#track-scroll");
  if (!scroller || !button) return;
  const scrollerBox = scroller.getBoundingClientRect();
  const cueBox = button.getBoundingClientRect();
  const pad = 20;
  if (cueBox.left < scrollerBox.left + pad) {
    scroller.scrollLeft -= scrollerBox.left + pad - cueBox.left;
  } else if (cueBox.right > scrollerBox.right - pad) {
    scroller.scrollLeft += cueBox.right - (scrollerBox.right - pad);
  }
}

function renderSelectedEvent(animate = false) {
  const events = state.experiment?.events || [];
  if (!events.length) {
    renderEmptySelection();
    return;
  }
  state.selectedEventIndex = Math.min(Math.max(state.selectedEventIndex, 0), events.length - 1);
  const event = events[state.selectedEventIndex];
  const metrics = eventMetrics(event);
  const frameURL = evidenceFrameURL(event);
  renderMediaEvidence(event, frameURL);
  renderApertureChips(event);
  const timecode = $("#current-timecode");
  const label = $("#current-label");
  const position = $("#current-position");
  const review = $("#review-status");
  const summary = $("#event-summary");
  const inspectorTitle = $("#inspector-title");
  const inspectorTime = $("#inspector-timecode");
  const slice = `${formatTime(event.t_start_ms)}–${formatTime(event.t_end_ms)}`;
  if (timecode) timecode.textContent = slice;
  if (label) label.textContent = event.label;
  if (position) position.textContent = `${state.selectedEventIndex + 1} / ${events.length}`;
  // The inspector heading names the event it is describing rather than repeating
  // the word "event": eyebrow carries the slice, the title carries the material.
  if (inspectorTitle) inspectorTitle.textContent = event.label;
  if (inspectorTime) inspectorTime.textContent = slice;
  if (review) {
    review.textContent = reviewStatusLabel(event.review_status);
    review.title = "这里描述素材事实的复核状态，不代表已完成真人受众校准。";
    const tone = REVIEW_STATUS_TONES[event.review_status];
    if (tone) review.dataset.tone = tone;
    else review.removeAttribute("data-tone");
  }
  if (summary) summary.textContent = event.summary || "该时间片没有摘要。";
  const metricValues = [metrics.confusion, metrics.attention, metrics.continueIntent];
  $$("#event-metrics > div").forEach((row, index) => {
    const value = metricValues[index];
    const unit = unitValue(value);
    row.dataset.state = unit == null ? "empty" : "value";
    row.style.setProperty("--v", unit ?? 0);
    const target = $("[data-metric]", row);
    if (target) target.textContent = formatPercent(value);
  });
  renderObservations(event);
  renderEvidenceClaim(event, metrics.traces);
  renderExtremes(event, metrics.traces);
  const prev = $("#cue-prev");
  const next = $("#cue-next");
  if (prev) prev.disabled = state.selectedEventIndex <= 0;
  if (next) next.disabled = state.selectedEventIndex >= events.length - 1;
  let selectedCue = null;
  $$("[data-event-index]", $("#timeline-rail")).forEach((button, index) => {
    const selected = index === state.selectedEventIndex;
    button.classList.toggle("is-selected", selected);
    if (selected) {
      button.setAttribute("aria-current", "true");
      selectedCue = button;
    } else {
      button.removeAttribute("aria-current");
    }
  });
  $$("#trace-list .channel-strip i").forEach(bar => {
    bar.classList.toggle("is-current", bar.dataset.node === event.node_id);
  });
  const environment = state.experiment.environment || {};
  const runtime = state.experiment.run_manifest?.runtime;
  const provenance = [
    environment.contract_version || environment.schema_version,
    state.experiment.timeline?.schema_version,
    state.experiment.timeline?.asset?.content_hash?.slice(0, 12),
    runtime?.model_id
      ? `${runtime.model_provider} / ${runtime.model_id}`
      : state.experiment.runtime_mode,
  ];
  $$("#evidence-provenance dd").forEach((element, index) => {
    element.textContent = provenance[index] || "—";
    element.title = provenance[index] || "";
  });
  renderProxyCurves();
  updatePlayhead();
  keepCueVisible(selectedCue);
  updateLightPath({ animate });
}

/* 签名交互：从当前 cue 出发、经过一个观察标记、终止于 Inspector 精确证据的一条证据光路。 */
function orthogonalPath(points, radius = 9) {
  const trimmed = points.filter((point, index, all) =>
    index === 0 || Math.abs(point.x - all[index - 1].x) > 0.5 || Math.abs(point.y - all[index - 1].y) > 0.5);
  if (trimmed.length < 2) return "";
  let path = `M ${trimmed[0].x.toFixed(1)} ${trimmed[0].y.toFixed(1)}`;
  for (let index = 1; index < trimmed.length - 1; index += 1) {
    const previous = trimmed[index - 1];
    const current = trimmed[index];
    const next = trimmed[index + 1];
    const inLength = Math.hypot(current.x - previous.x, current.y - previous.y);
    const outLength = Math.hypot(next.x - current.x, next.y - current.y);
    const corner = Math.max(0, Math.min(radius, inLength / 2, outLength / 2));
    const entry = {
      x: current.x + ((previous.x - current.x) / inLength) * corner,
      y: current.y + ((previous.y - current.y) / inLength) * corner,
    };
    const exit = {
      x: current.x + ((next.x - current.x) / outLength) * corner,
      y: current.y + ((next.y - current.y) / outLength) * corner,
    };
    path += ` L ${entry.x.toFixed(1)} ${entry.y.toFixed(1)} Q ${current.x.toFixed(1)} ${current.y.toFixed(1)} ${exit.x.toFixed(1)} ${exit.y.toFixed(1)}`;
  }
  const last = trimmed[trimmed.length - 1];
  return `${path} L ${last.x.toFixed(1)} ${last.y.toFixed(1)}`;
}

function placeMarker(svg, selector, point) {
  const marker = $(selector, svg);
  if (!marker) return;
  marker.setAttribute("cx", point.x.toFixed(1));
  marker.setAttribute("cy", point.y.toFixed(1));
}

function updateLightPath({ animate = false } = {}) {
  const svg = $("#light-path");
  if (!svg) return;
  // The beam is normally aimed at the selected cue. While a reader hovers or
  // keyboard-focuses another card, that card borrows the aim: the route is the
  // claim being previewed, not the one already open.
  const cue = state.beamHint || $("#timeline-rail button.is-selected");
  const anchor = $("#claim-anchor");
  const inspector = $("#evidence-inspector");
  const evidenceView = $("#view-evidence");
  const frame = svg.getBoundingClientRect();
  if (!cue || !anchor || !inspector || evidenceView?.hidden || frame.width < 2 || getComputedStyle(svg).display === "none") {
    svg.classList.remove("is-live", "is-tracing", "is-hint");
    return;
  }
  const cueBox = cue.getBoundingClientRect();
  const anchorBox = anchor.getBoundingClientRect();
  const inspectorBox = inspector.getBoundingClientRect();
  const scrollerBox = $("#track-scroll")?.getBoundingClientRect();
  const blockBox = $("#cue-block")?.getBoundingClientRect();
  // The cue can be clipped by the timeline scroller; keep the beam origin on the
  // visible part of the card so the path never starts outside the track.
  let startX = cueBox.left + cueBox.width / 2 - frame.left;
  if (scrollerBox) {
    startX = clamp(startX, scrollerBox.left - frame.left + 6, scrollerBox.right - frame.left - 6);
    if (cueBox.right < scrollerBox.left || cueBox.left > scrollerBox.right) {
      svg.classList.remove("is-live", "is-tracing", "is-hint");
      return;
    }
  }
  const start = { x: startX, y: cueBox.top - frame.top };
  const end = { x: anchorBox.left + anchorBox.width / 2 - frame.left, y: anchorBox.top + anchorBox.height / 2 - frame.top };
  // The beam leaves upward and runs above the cue block, so it never crosses the
  // proxy curves it is supposed to help read.
  const blockTop = blockBox ? blockBox.top - frame.top : start.y - 14;
  const channelY = clamp(blockTop - 5, 4, Math.max(4, start.y - 10));
  const gutterX = Math.max(start.x + 24, inspectorBox.left - frame.left - 10);
  const waypoint = { x: (start.x + gutterX) / 2, y: channelY };
  const points = [start, { x: start.x, y: channelY }, waypoint, { x: gutterX, y: channelY }, { x: gutterX, y: end.y }, end];
  const beam = $(".beam", svg);
  const spark = $(".beam-spark", svg);
  svg.setAttribute("viewBox", `0 0 ${frame.width.toFixed(1)} ${frame.height.toFixed(1)}`);
  const route = orthogonalPath(points);
  beam.setAttribute("d", route);
  // The spark rides the same geometry, so the lit segment can never drift off the
  // dotted route it is supposed to be travelling.
  spark?.setAttribute("d", route);
  const length = typeof beam.getTotalLength === "function" ? beam.getTotalLength() : 1200;
  svg.style.setProperty("--beam-length", Math.ceil(length + 4));
  placeMarker(svg, ".beam-source", start);
  placeMarker(svg, ".beam-mark", waypoint);
  placeMarker(svg, ".beam-end", end);
  svg.classList.add("is-live");
  svg.classList.toggle("is-hint", Boolean(state.beamHint));
  if (!animate || prefersStillness()) return;
  // One sweep, cue to evidence, then the layer is static again. Restarting the
  // animation needs the class off, a forced reflow, and the class back on.
  svg.classList.remove("is-tracing");
  void svg.getBoundingClientRect();
  svg.classList.add("is-tracing");
  anchor.classList.add("is-landed");
  window.clearTimeout(updateLightPath.timer);
  updateLightPath.timer = window.setTimeout(() => {
    svg.classList.remove("is-tracing");
    anchor.classList.remove("is-landed");
  }, 520);
}

/* Hover and focus borrow the aim; leaving hands it back to the selected cue. */
function aimLightPath(element, { animate = false } = {}) {
  state.beamHint = element || null;
  updateLightPath({ animate });
}

function scheduleLightPath() {
  window.cancelAnimationFrame(scheduleLightPath.frame);
  scheduleLightPath.frame = window.requestAnimationFrame(() => {
    renderCueRuler(state.experiment?.events || []);
    updateLightPath();
  });
}

function renderExperiment() {
  if (!state.experiment) return;
  const identity = $("#experiment-id");
  const status = $("#experiment-status");
  if (identity) identity.textContent = state.experiment.experiment_id;
  if (status) {
    const sourceTitle = state.experiment.source?.title || state.experiment.source_name;
    const statusLabel = EXPERIMENT_STATUS_LABELS[state.experiment.status] || state.experiment.status;
    const runtimeLabel = RUNTIME_MODE_LABELS[state.experiment.runtime_mode] || state.experiment.runtime_mode;
    status.textContent = [sourceTitle, statusLabel, runtimeLabel].filter(Boolean).join(" · ");
  }
  updateVideoGovernance();
  renderPipeline();
  renderLimitations();
  renderSourceSummary();
  renderScale();
  renderReceipts();
  renderTimelineRail();
  renderTraces();
  renderSelectedEvent();
  renderEventTable();
  renderDeckMetrics();
  renderCalibrationStatus();
  renderCalibration();
  renderExperimentIndex();
  syncLocation();
  scheduleLightPath();
}

function selectEvent(index) {
  const events = state.experiment?.events || [];
  if (!events.length) return;
  state.selectedEventIndex = Math.min(Math.max(Number(index) || 0, 0), events.length - 1);
  renderSelectedEvent(true);
  syncLocation();
}

function openTrace(agentId, traceId) {
  if (isSinglePane()) setPane("inspector");
  setInspectorView("traces");
  const filterInput = $("#persona-filter");
  if (filterInput) filterInput.value = "";
  renderTraces();
  const session = $(`#session-${CSS.escape(agentId)}`);
  if (!session) return;
  session.open = true;
  const trace = traceId ? $(`#trace-${CSS.escape(traceId)}`) : null;
  revealElement(trace || session, "center");
  if (trace) trace.focus({ preventScroll: true });
}

/* ---------- API flows ---------- */

async function loadExperiment(experimentId, { silent = false } = {}) {
  if (!silent) {
    setShellBusy("experiment");
    renderCueSkeleton();
  }
  try {
    state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(experimentId)}`);
    state.selectedEventIndex = 0;
    renderExperiment();
  } finally {
    if (!silent) setShellBusy(null);
  }
}

async function submitUpload(event) {
  event.preventDefault();
  if (blockStaticMutation("链接导入与本地解析")) return;
  const form = event.currentTarget;
  const button = $("#ingest-button");
  const formData = new FormData(form);
  const sourceMode = formData.get("source_mode") || "url";
  formData.delete("source_mode");
  setBusy(button, true, sourceMode === "url" ? "正在读取链接" : "正在上传");
  setShellBusy("ingest");
  renderCueSkeleton();
  setMessage(sourceMode === "url"
    ? "正在检查链接、取回已获授权的视频，并在本机建立证据时间轴。"
    : "正在上传，并在本机解码视频、抽取证据帧与音轨。");
  try {
    state.experiment = await fetchJSON("/api/experiments", { method: "POST", body: formData });
    state.selectedEventIndex = 0;
    await refreshExperimentIndex();
    renderExperiment();
    updateCommandStage();
    const sourceLabel = state.experiment.source?.title || state.experiment.source_name || "视频";
    setMessage(`${sourceLabel} 已导入，切出 ${state.experiment.events.length} 个事件。下一步：在时间轴上选一个事件核对证据，或直接让 AI 观众逐段体验。`, "success");
    setPane("stage");
  } catch (error) {
    setMessage(`${error.message} 素材没有被导入，你可以修正链接后重试。`, "error");
    renderTimelineRail();
  } finally {
    setShellBusy(null);
    setBusy(button, false);
  }
}

async function submitAnalyze(event) {
  event.preventDefault();
  if (blockStaticMutation("多模态模型分析")) return;
  const form = event.currentTarget;
  if (!state.experiment || state.experiment.experiment_id === "demo") {
    setMessage("公开样例没有原始画面，无法分析。请先粘贴链接或上传一个你已获授权的真实视频。", "error");
    focusSourceField();
    return;
  }
  const button = $("#analyze-button");
  const provider = $("#provider")?.value || "codex-frames";
  setBusy(button, true, "正在分析");
  setShellBusy("analyze");
  setMessage(provider === "gemini"
    ? "原生视频模型正在读取完整视频，结果会融合进证据时间轴。请先不要关闭页面。"
    : "Codex 正在分析带时间戳的证据帧。原视频和音轨不会发送，帧与帧之间的内容仍是未知。请先不要关闭页面。");
  try {
    state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(state.experiment.experiment_id)}/analyze`, {
      method: "POST",
      body: new FormData(form),
    });
    await refreshExperimentIndex();
    renderExperiment();
    setMessage("多模态事实层已写入时间轴。下一步：在右侧「当前证据」里核对推断状态与不确定性。", "success");
  } catch (error) {
    setMessage(`${error.message} 时间轴保持原样，没有被改写。`, "error");
  } finally {
    $$('input[name="remote_processing_confirmed"], input[name="provider_policy_confirmed"]', form)
      .forEach(input => { input.checked = false; });
    setShellBusy(null);
    setBusy(button, false);
  }
}

async function submitRun(event) {
  event.preventDefault();
  if (blockStaticMutation("Agent 顺序体验")) return;
  const form = event.currentTarget;
  if (!state.experiment) return;
  const button = $("#run-button");
  setBusy(button, true, "正在运行");
  setShellBusy("run");
  setMessage("AI 观众正在按时间顺序体验当前素材。模型模式按事件计费，并受调用上限保护。");
  try {
    state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(state.experiment.experiment_id)}/run`, {
      method: "POST",
      body: new FormData(form),
    });
    await refreshExperimentIndex();
    renderExperiment();
    setMessage(`已完成 ${state.experiment.counts.deep_personas} 个 AI 观众、${state.experiment.counts.deep_trace_events} 条个体记录。这些数值仍是未校准代理量；要得到可信结论，请在「真人校准」里导入真人锚点。`, "success");
  } catch (error) {
    setMessage(`${error.message} 本次运行没有写入结果。`, "error");
  } finally {
    $$('input[name="agent_remote_processing_confirmed"], input[name="agent_provider_policy_confirmed"]', form)
      .forEach(input => { input.checked = false; });
    setShellBusy(null);
    setBusy(button, false);
  }
}

async function submitCalibration(event) {
  event.preventDefault();
  if (blockStaticMutation("真人反馈校准")) return;
  const form = event.currentTarget;
  if (!state.experiment) return;
  const button = $("#calibrate-button");
  const formData = new FormData(form);
  if (!formData.get("agent_ab_direction")) formData.delete("agent_ab_direction");
  setBusy(button, true, "正在校准");
  setShellBusy("calibrate");
  try {
    state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(state.experiment.experiment_id)}/calibrate`, {
      method: "POST",
      body: formData,
    });
    await refreshExperimentIndex();
    renderExperiment();
    setMessage("真人锚点已对齐。AI 观众数与真人数分开报告，不会合并成一个样本量。", "success");
  } catch (error) {
    setMessage(`${error.message} 已有的校准结果没有被改写。`, "error");
  } finally {
    setShellBusy(null);
    setBusy(button, false);
  }
}

/* ---------- wiring ---------- */

function bindEvents() {
  $("#upload-form")?.addEventListener("submit", submitUpload);
  $("#analyze-form")?.addEventListener("submit", submitAnalyze);
  $("#run-form")?.addEventListener("submit", submitRun);
  $("#calibration-form")?.addEventListener("submit", submitCalibration);

  $("#theme-toggle")?.addEventListener("click", () => {
    applyTheme(currentTheme() === "dark" ? "light" : "dark", { persist: true });
  });

  /* The empty stage and the fixture slate are re-rendered from data, so their
     actions are delegated rather than bound to a specific node. */
  document.addEventListener("click", event => {
    const focusTarget = event.target.closest("[data-focus-source]");
    if (focusTarget) {
      event.preventDefault();
      focusSourceField();
      return;
    }
    const demoTarget = event.target.closest("[data-load-demo]");
    if (demoTarget) {
      event.preventDefault();
      loadDemoExperiment(demoTarget);
    }
  });
  $("#aperture-retry")?.addEventListener("click", event => loadDemoExperiment(event.currentTarget));
  $("#recent-experiment-list")?.addEventListener("click", async event => {
    const button = event.target.closest("[data-experiment-id]");
    if (!button) return;
    setBusy(button, true);
    try {
      await loadExperiment(button.dataset.experimentId);
      setMessage("已从本地制品恢复实验。", "success");
      setPane("stage");
      setDrawer(false);
    } catch (error) {
      setMessage(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  });

  $("#persona-filter")?.addEventListener("input", renderTraces);
  $$('input[name="source_mode"]').forEach(input => {
    input.addEventListener("change", () => setSourceMode(input.value));
  });
  $("#video-url")?.addEventListener("input", updateCommandStage);
  $("#video-file")?.addEventListener("change", updateCommandStage);
  $('select[name="runtime_mode"]')?.addEventListener("change", event => setRuntimeMode(event.currentTarget.value));
  $("#agent-reasoner")?.addEventListener("change", event => setAgentReasoner(event.currentTarget.value));
  $("#provider")?.addEventListener("change", event => setVideoProvider(event.currentTarget.value));

  $("#cue-prev")?.addEventListener("click", () => selectEvent(state.selectedEventIndex - 1));
  $("#cue-next")?.addEventListener("click", () => selectEvent(state.selectedEventIndex + 1));
  $("#track-scroll")?.addEventListener("scroll", scheduleLightPath, { passive: true });

  $("#zoom-in")?.addEventListener("click", () => setZoom(state.zoomIndex + 1));
  $("#zoom-out")?.addEventListener("click", () => setZoom(state.zoomIndex - 1));
  $("#zoom-fit")?.addEventListener("click", () => setZoom(0));

  $$(".inspector-tabs [role=tab]").forEach((tab, index, tabs) => {
    tab.addEventListener("click", () => setInspectorView(tab.dataset.view, true));
    tab.addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const nextIndex = event.key === "Home"
        ? 0
        : event.key === "End"
          ? tabs.length - 1
          : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
      setInspectorView(tabs[nextIndex].dataset.view);
      tabs[nextIndex].focus();
    });
  });
  $$("[data-pane-target]").forEach(button => {
    button.addEventListener("click", () => {
      const pane = button.dataset.paneTarget;
      setPane(pane);
      if (isSinglePane()) return;
      scrollToPane(pane);
      focusPane(pane);
      scheduleHeadNav();
    });
  });
  $$("[data-stage-target]").forEach(button => {
    button.addEventListener("click", () => STAGE_ACTIONS[button.dataset.stageTarget]?.());
  });

  $$("[data-drawer-target]").forEach(button => {
    button.addEventListener("click", () => setDrawer(!isDrawerOpen(), { focus: true }));
  });
  $("#drawer-close")?.addEventListener("click", () => setDrawer(false));
  $("#drawer-scrim")?.addEventListener("click", () => setDrawer(false));

  // The run controls live in the drawer; open it when the run form blocks submit.
  $("#run-form")?.addEventListener("invalid", () => setDrawer(true), true);
  $("#run-button")?.addEventListener("click", () => {
    const form = $("#run-form");
    if (form && typeof form.checkValidity === "function" && !form.checkValidity()) setDrawer(true);
  });

  $("#setup-message-dismiss")?.addEventListener("click", () => setMessage(""));

  window.addEventListener("keydown", event => {
    if ((event.metaKey || event.ctrlKey) && !event.altKey && event.key.toLowerCase() === "k") {
      event.preventDefault();
      const radio = $('input[name="source_mode"][value="url"]');
      if (radio) {
        radio.checked = true;
        setSourceMode("url");
      }
      const input = $("#video-url");
      input?.focus();
      input?.select();
      return;
    }
    if (event.key === "Escape" && isDrawerOpen()) {
      event.preventDefault();
      setDrawer(false);
    }
  });

  // Hovering the hit evidence warms the same route from the other end: the reader
  // is asking "where did this come from", and the answer is already drawn.
  const claim = $(".claim-block");
  claim?.addEventListener("pointerenter", () => $("#light-path")?.classList.add("is-warm"));
  claim?.addEventListener("pointerleave", () => $("#light-path")?.classList.remove("is-warm"));

  // A hidden tab has no reader, so the condense stops rather than burning frames
  // no one will see.
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stopEmulsion();
  });

  window.addEventListener("resize", () => {
    const rail = $("#rail");
    if (rail) rail.inert = !isSinglePane() && !isDrawerOpen();
    tuneCommandCopy();
    scheduleLightPath();
    scheduleHeadNav();
    if (emulsion.frame) measureEmulsion();
  });
  // The page scrolls on desktop, so both the beam geometry and the head
  // navigation follow the scroll position instead of a fixed layout.
  window.addEventListener("scroll", () => {
    scheduleLightPath();
    scheduleHeadNav();
  }, { passive: true });
  document.addEventListener("focusin", scheduleHeadNav);
  document.addEventListener("focusout", scheduleHeadNav);
  const workbench = $("#workbench");
  if (typeof ResizeObserver === "function" && workbench instanceof Element) {
    new ResizeObserver(scheduleLightPath).observe(workbench);
  }
  // The well changes height when a source reports its intrinsic ratio, so the
  // backing store follows the box rather than the window.
  const well = $("#media-stage");
  if (typeof ResizeObserver === "function" && well instanceof Element) {
    new ResizeObserver(() => {
      if (emulsion.frame) measureEmulsion();
    }).observe(well);
  }
}

function applyDeepLinks(params) {
  const view = params.get("view");
  if (view && INSPECTOR_VIEWS.includes(view)) setInspectorView(view);
  const cue = Number(params.get("cue"));
  if (Number.isFinite(cue) && cue >= 1) selectEvent(cue - 1);
}

/* The prompt has to stay readable in a 340px slot, so the narrow build names the
   action and drops the platform list rather than truncating mid-word. */
const SOURCE_PLACEHOLDERS = {
  wide: "粘贴一个已获授权的视频链接（公开直链 / YouTube / Bilibili / 抖音）",
  narrow: "粘贴已获授权的视频链接",
};

function tuneCommandCopy() {
  const key = $(".slot-key");
  if (key) {
    const isApple = /Mac|iPhone|iPad|iPod/.test(navigator.userAgent || "");
    key.textContent = isApple ? "⌘K" : "Ctrl K";
  }
  const input = $("#video-url");
  if (input) {
    input.placeholder = window.matchMedia("(max-width: 620px)").matches
      ? SOURCE_PLACEHOLDERS.narrow
      : SOURCE_PLACEHOLDERS.wide;
  }
}

async function initialize() {
  bindEvents();
  applyTheme(currentTheme());
  tuneCommandCopy();
  setSourceMode($('input[name="source_mode"]:checked')?.value || "url");
  updateCommandStage();
  setAgentReasoner($("#agent-reasoner")?.value || "codex-cli");
  setVideoProvider($("#provider")?.value || "codex-frames");
  setRuntimeMode($('select[name="runtime_mode"]')?.value || "deterministic");
  setDrawer(false);
  setZoom(0);
  renderCueSkeleton();

  try {
    state.health = await fetchJSON("/api/health");
  } catch {
    state.health = null;
  }
  renderHealth();

  try {
    await refreshExperimentIndex();
  } catch {
    state.experimentIndex = [];
    renderExperimentIndex();
  }

  const params = new URLSearchParams(window.location.search);
  try {
    await loadExperiment(params.get("experiment") || "demo");
    applyDeepLinks(params);
  } catch (error) {
    try {
      await loadExperiment("demo");
      applyDeepLinks(params);
      setMessage(`${error.message} 已改为载入公开样例，你可以先在样例里试一遍流程。`, "error");
    } catch {
      setMessage(error.message, "error");
      setApertureState("error", "读不到实验", `${error.message} 请确认本机工作台服务仍在运行，然后点下面的按钮重试。`);
    }
  }
  syncHeadNav();
}

initialize();
