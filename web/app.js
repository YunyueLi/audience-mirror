/* Audience Mirror workbench — Calibrated Projection Room, operate mode.
   Every rendered number comes from the local API; nothing here is mocked.
   Rendering contract: state.experiment is the single source, render* functions
   are pure projections of it, and no aggregate is shown without its scale
   qualifier, evidence reference and calibration status. */

const state = {
  health: null,
  experiment: null,
  experimentIndex: [],
  selectedEventIndex: 0,
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
  ingest: ["正在建立本地时间轴", "检查链接与权利、本地解码证据帧与音轨，完成后进入线索轨道。"],
  analyze: ["多模态事实层正在写入", "Provider 正在读取已授权载荷；完成后请复核推断状态与不确定性。"],
  run: ["Deep Persona 正在顺序体验", "Persona 按时间顺序独立体验，不互相讨论；模型模式受调用上限保护。"],
  calibrate: ["正在对齐 Human Anchors", "只统计同任务、同版本反馈；撤回同意的记录会被排除。"],
  experiment: ["正在读取实验制品", "从本地 artifacts 恢复 Timeline、Trace 与校准报告。"],
};

const INSPECTOR_VIEWS = ["evidence", "response", "traces", "calibration"];
const PANES = ["rail", "stage", "inspector", "deck"];

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

function unitValue(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.min(1, Math.max(0, numeric)).toFixed(3) : null;
}

function mean(values) {
  const numbers = values.map(Number).filter(Number.isFinite);
  return numbers.length ? numbers.reduce((sum, value) => sum + value, 0) / numbers.length : null;
}

/* ---------- transport ---------- */

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, options);
  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = { detail: `服务返回了无法解析的响应（HTTP ${response.status}）。` };
  }
  if (!response.ok) {
    throw new Error(payload.detail || payload.error || `请求失败（HTTP ${response.status}）。`);
  }
  return payload;
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
  rail.innerHTML = Array.from({ length: 5 }, () => '<li><div class="cue-skeleton"></div></li>').join("");
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

function renderHealth() {
  const element = $("#system-state");
  const status = $("#native-model-status");
  const detail = $("#native-model-detail");
  if (!element) return;
  if (!state.health?.capabilities) {
    element.textContent = "能力检查失败";
    element.className = "system-state is-error";
    element.title = "无法读取 /api/health；本地服务可能未启动。";
    if (status) status.textContent = "未知";
    if (detail) detail.textContent = "无法读取本地能力清单；请确认服务已启动。";
    return;
  }
  const capabilities = state.health.capabilities;
  const available = [
    capabilities.direct_video_url && "链接导入",
    capabilities.platform_video_url && "平台 Adapter",
    capabilities.local_video_decode && "本地解码",
    capabilities.gemini_native_video && "原生视频模型",
    capabilities.codex_frame_analysis && "证据帧分析",
    capabilities.human_calibration && "校准",
  ].filter(Boolean);
  element.textContent = available.length ? available.join(" · ") : "工程基线可用";
  element.className = "system-state is-ready";
  element.title = `本地版本 ${state.health.version || "未知"}；远程处理默认关闭。`;
  const nativeReady = Boolean(capabilities.gemini_native_video);
  const framesReady = Boolean(capabilities.codex_frame_analysis);
  if (status) status.textContent = nativeReady ? "整片可用" : framesReady ? "证据帧可用" : "未配置";
  if (detail) {
    detail.textContent = nativeReady
      ? "原生整片与证据帧路由均可用；发送范围随 Provider 切换。"
      : framesReady
        ? "证据帧路由可用；原生整片未配置，帧间动作与声音保持未知。"
        : "未配置远程事实层；本地解析与工程基线仍可运行。";
  }
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

function setPane(pane, focus = false) {
  const shell = $("#app-shell");
  if (!shell || !PANES.includes(pane)) return;
  shell.dataset.pane = pane;
  $$("[data-pane-target]").forEach(button => {
    const active = button.dataset.paneTarget === pane;
    button.setAttribute("aria-pressed", String(active));
    if (active && focus) button.focus();
  });
  scheduleLightPath();
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
  if (isSinglePane()) setPane("rail");
  revealElement(group, "start");
}

/* Stage navigation moves the operator to the控制 that actually advances the run. */
const STAGE_ACTIONS = {
  ingest: () => {
    setSourceMode("url");
    const input = $("#video-url");
    if (input) {
      const radio = $('input[name="source_mode"][value="url"]');
      if (radio) radio.checked = true;
      input.focus();
    }
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
    list.innerHTML = '<p class="empty-copy">还没有可恢复的本地实验。</p>';
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
    list.innerHTML = '<p class="empty-copy">本实验尚无远程调用；所有解析都在本地完成。</p>';
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
      ? `${formatCount(state.experiment?.counts?.deep_personas)} 个 Deep Persona · ${formatCount(traceCount)} 条 Trace · 未校准`
      : "运行顺序体验后显示全片代理量";
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

/* ---------- stage renderers ---------- */

function renderCueRuler(events) {
  const ruler = $("#cue-ruler");
  const rail = $("#timeline-rail");
  const duration = timelineDurationMs();
  if (!ruler || !rail) return;
  if (!events.length || !duration) {
    ruler.innerHTML = "";
    ruler.classList.add("is-hidden");
    return;
  }
  const steps = 5;
  ruler.innerHTML = Array.from({ length: steps }, (unused, index) =>
    `<li>${formatTime((duration / (steps - 1)) * index)}</li>`).join("");
  // 轨道横向滚动时刻度不再与 cue 对齐，此时隐藏刻度而不是给出错误对位。
  ruler.classList.toggle("is-hidden", rail.scrollWidth > rail.clientWidth + 2);
}

function renderTimelineRail() {
  const rail = $("#timeline-rail");
  const events = state.experiment?.events || [];
  const scope = $("#cue-scope");
  if (!rail) return;
  if (!events.length) {
    rail.innerHTML = '<li class="empty-copy">尚无时间轴事件；装载视频后这里出现 cue。</li>';
    if (scope) scope.textContent = "装载素材后建立 cue。";
    renderCueRuler(events);
    return;
  }
  rail.innerHTML = events.map((event, index) => {
    const span = Math.max(1000, Number(event.t_end_ms || 0) - Number(event.t_start_ms || 0));
    const selected = index === state.selectedEventIndex;
    return `<li style="--cue-grow:${Math.round(span / 1000)}">
      <button type="button" data-event-index="${index}" data-time="${escapeHTML(formatTime(event.t_start_ms))}"
        class="${selected ? "is-selected" : ""}"
        aria-label="cue ${index + 1}：${escapeHTML(formatTime(event.t_start_ms))} 至 ${escapeHTML(formatTime(event.t_end_ms))}，时长 ${escapeHTML(formatSpan(span))}，${escapeHTML(event.label)}"
        ${selected ? 'aria-current="true"' : ""}>
        <span class="cue-mark" aria-hidden="true"></span>
        <span class="cue-time">${escapeHTML(formatTime(event.t_start_ms))}</span>
        <span class="cue-label">${escapeHTML(event.label)}</span>
        <span class="cue-span">${escapeHTML(formatSpan(span))}</span>
      </button>
    </li>`;
  }).join("");
  if (scope) {
    scope.textContent = `${events.length} 个事件 · 总长 ${formatTime(timelineDurationMs())} · 宽度对应时长，← → 切换，Home／End 到首尾`;
  }
  $$("[data-event-index]", rail).forEach(button => {
    button.addEventListener("click", () => selectEvent(Number(button.dataset.eventIndex)));
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

function renderApertureChips(event) {
  const classification = state.experiment?.timeline?.data_handling?.data_classification || "unknown";
  const label = CLASSIFICATION_LABELS[classification] || classification;
  const tag = $("#aperture-tag");
  const timecode = $("#aperture-timecode");
  if (timecode) timecode.textContent = event ? formatTime(event.t_start_ms) : "00:00";
  if (!tag) return;
  tag.textContent = state.experiment?.media_url ? `${label} · 原视频` : `${label} · 合成 Fixture`;
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
      stage.innerHTML = `<video id="source-video" controls playsinline preload="metadata" aria-label="原视频证据，包含声音" data-experiment-id="${escapeHTML(state.experiment.experiment_id)}" src="${escapeHTML(mediaURL)}">浏览器无法播放该原视频；请使用下方原始制品链接。</video>`;
      video = $("#source-video", stage);
      trackMediaAspect(video);
    }
    aperture.dataset.state = "video";
    if (frameURL) video.poster = frameURL;
    const seekSeconds = Number(event.t_start_ms || 0) / 1000;
    const seek = () => {
      if (Number.isFinite(seekSeconds)) video.currentTime = seekSeconds;
    };
    if (video.readyState >= 1) seek();
    else video.addEventListener("loadedmetadata", seek, { once: true });
    const audioLink = state.experiment.audio_url
      ? `<a href="${escapeHTML(state.experiment.audio_url)}" target="_blank" rel="noreferrer">抽取音轨 WAV</a>`
      : "<span>源文件未检测到可抽取音轨</span>";
    links.innerHTML = `<a href="${escapeHTML(mediaURL)}" target="_blank" rel="noreferrer">原视频制品</a>${audioLink}<span>选择 cue 会定位到该段起点，不会自动播放。</span>`;
    return;
  }
  links.innerHTML = "";
  stage.style.removeProperty("--media-aspect");
  if (frameURL) {
    aperture.dataset.state = "frame";
    stage.innerHTML = `<img src="${escapeHTML(frameURL)}" alt="${escapeHTML(event.label)} 的解码证据帧">`;
    return;
  }
  aperture.dataset.state = "slate";
  stage.innerHTML = `<div class="aperture-slate">
    <strong>${escapeHTML(event.label)}</strong>
    <p>${escapeHTML(event.summary || "该公开 Fixture 不包含原始媒体帧。")}</p>
    <span class="slate-time">${escapeHTML(formatTime(event.t_start_ms))} – ${escapeHTML(formatTime(event.t_end_ms))}</span>
  </div>`;
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
    target.textContent = "运行 Deep Persona 后显示高反应与反例。";
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
    target.innerHTML = '<p class="empty-copy">尚无个体 Trace；运行顺序体验后每个 Persona 会成为一条独立回放通道。</p>';
    return;
  }
  const visible = [...sessions.entries()].filter(([agentId]) => {
    const persona = personas.get(agentId) || {};
    return !filter || `${agentId} ${persona.segment_id || ""}`.toLowerCase().includes(filter);
  });
  if (!visible.length) {
    target.innerHTML = '<p class="empty-copy">没有匹配的 Persona；清空筛选可恢复全部 Session。</p>';
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
      <td><button type="button" class="evidence-button" data-trace-event-node="${escapeHTML(trace.timeline.timeline_node_id)}">${escapeHTML(trace.timeline.timeline_node_id)}</button></td>
      <td>${escapeHTML(trace.reaction?.reaction_type || "—")}<small>${escapeHTML(trace.reaction?.summary || "")}</small></td>
      <td class="numeric">${formatPercent(trace.state?.after?.confusion)}</td>
      <td class="numeric">${formatPercent(trace.state?.after?.continue_intent)}</td>
      <td>${escapeHTML(trace.action?.action_type || "—")}<small>${escapeHTML(trace.action?.reason_summary || "")}</small></td>
      <td><code>${escapeHTML(trace.evidence?.[0]?.timeline_observation_id || "—")}</code></td>
    </tr>`).join("");
    return `<details class="trace-session" id="session-${escapeHTML(agentId)}" data-agent="${escapeHTML(agentId)}">
      <summary>
        <span class="session-name"><strong>${escapeHTML(agentId)}</strong><small>${escapeHTML(persona.segment_id || final.segment_id || "未分群")}</small></span>
        <span class="channel-strip" aria-hidden="true" title="按事件顺序的继续意向代理量">${channel}</span>
        <span class="session-outcome">理解 ${formatPercent(final.state?.after?.comprehension)} · 困惑 ${formatPercent(final.state?.after?.confusion)} · 继续 ${formatPercent(final.state?.after?.continue_intent)}</span>
      </summary>
      <div class="trace-body table-wrap">
        <table><thead><tr><th scope="col">时间</th><th scope="col">节点</th><th scope="col">反应</th><th scope="col">困惑</th><th scope="col">继续</th><th scope="col">动作</th><th scope="col">Observation</th></tr></thead><tbody>${rows}</tbody></table>
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
    target.innerHTML = "<strong>尚未导入真人数据</strong><p>校准结果会显示 Top 问题召回、时间点召回、同名代理量误差和 A/B 方向一致性。</p>";
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
  if (timecode) timecode.textContent = "00:00–00:00";
  if (label) label.textContent = "尚无时间轴事件";
  if (position) position.textContent = "0 / 0";
  if (review) {
    review.textContent = "未选择";
    review.removeAttribute("data-tone");
  }
  if (summary) summary.textContent = "装载素材或恢复公开 Demo 后，这里显示当前 cue 的多模态事实。";
  $$("#event-metrics > div").forEach(row => {
    row.dataset.state = "empty";
    row.style.setProperty("--v", 0);
    const value = $("[data-metric]", row);
    if (value) value.textContent = "—";
  });
  const observations = $("#observations");
  if (observations) observations.innerHTML = '<li class="empty-copy">尚无观察。</li>';
  const claim = $("#evidence-claim");
  if (claim) claim.innerHTML = '<p class="empty-copy">选择 cue 后显示该时间片引用的证据与来源标识。</p>';
  const extremes = $("#event-extremes");
  if (extremes) {
    extremes.className = "empty-copy";
    extremes.textContent = "运行 Deep Persona 后显示高反应与反例。";
  }
  const prev = $("#cue-prev");
  const next = $("#cue-next");
  if (prev) prev.disabled = true;
  if (next) next.disabled = true;
  renderApertureChips(null);
  $("#light-path")?.classList.remove("is-live");
}

function keepCueVisible(button) {
  const rail = $("#timeline-rail");
  if (!rail || !button) return;
  const railBox = rail.getBoundingClientRect();
  const cueBox = button.getBoundingClientRect();
  if (cueBox.left < railBox.left) rail.scrollLeft -= railBox.left - cueBox.left + 12;
  else if (cueBox.right > railBox.right) rail.scrollLeft += cueBox.right - railBox.right + 12;
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
  if (timecode) timecode.textContent = `${formatTime(event.t_start_ms)}–${formatTime(event.t_end_ms)}`;
  if (label) label.textContent = event.label;
  if (position) position.textContent = `${state.selectedEventIndex + 1} / ${events.length}`;
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
  const cue = $("#timeline-rail button.is-selected");
  const anchor = $("#claim-anchor");
  const inspector = $("#evidence-inspector");
  const evidenceView = $("#view-evidence");
  const frame = svg.getBoundingClientRect();
  if (!cue || !anchor || !inspector || evidenceView?.hidden || frame.width < 2 || getComputedStyle(svg).display === "none") {
    svg.classList.remove("is-live", "is-tracing");
    return;
  }
  const cueBox = cue.getBoundingClientRect();
  const anchorBox = anchor.getBoundingClientRect();
  const inspectorBox = inspector.getBoundingClientRect();
  const start = { x: cueBox.left + cueBox.width / 2 - frame.left, y: cueBox.bottom - frame.top };
  const end = { x: anchorBox.left + anchorBox.width / 2 - frame.left, y: anchorBox.top + anchorBox.height / 2 - frame.top };
  const channelY = Math.min(frame.height - 6, start.y + 14);
  const gutterX = Math.max(start.x + 24, inspectorBox.left - frame.left - 10);
  const waypoint = { x: (start.x + gutterX) / 2, y: channelY };
  const points = [start, { x: start.x, y: channelY }, waypoint, { x: gutterX, y: channelY }, { x: gutterX, y: end.y }, end];
  const beam = $(".beam", svg);
  svg.setAttribute("viewBox", `0 0 ${frame.width.toFixed(1)} ${frame.height.toFixed(1)}`);
  beam.setAttribute("d", orthogonalPath(points));
  const length = typeof beam.getTotalLength === "function" ? beam.getTotalLength() : 1200;
  svg.style.setProperty("--beam-length", Math.ceil(length + 4));
  placeMarker(svg, ".beam-source", start);
  placeMarker(svg, ".beam-mark", waypoint);
  placeMarker(svg, ".beam-end", end);
  svg.classList.add("is-live");
  if (!animate || prefersStillness()) return;
  svg.classList.remove("is-tracing");
  void svg.getBoundingClientRect();
  svg.classList.add("is-tracing");
  window.clearTimeout(updateLightPath.timer);
  updateLightPath.timer = window.setTimeout(() => svg.classList.remove("is-tracing"), 520);
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
    status.textContent = [sourceTitle, statusLabel, state.experiment.runtime_mode].filter(Boolean).join(" · ");
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
  const form = event.currentTarget;
  const button = $("#ingest-button");
  const formData = new FormData(form);
  const sourceMode = formData.get("source_mode") || "url";
  formData.delete("source_mode");
  setBusy(button, true, sourceMode === "url" ? "正在读取链接" : "正在上传");
  setShellBusy("ingest");
  renderCueSkeleton();
  setMessage(sourceMode === "url"
    ? "正在检查链接、获取已授权视频并建立本地证据时间轴。"
    : "正在上传并本地解码视频、抽取证据帧与音轨。");
  try {
    state.experiment = await fetchJSON("/api/experiments", { method: "POST", body: formData });
    state.selectedEventIndex = 0;
    await refreshExperimentIndex();
    renderExperiment();
    const sourceLabel = state.experiment.source?.title || state.experiment.source_name || "视频";
    setMessage(`${sourceLabel} 已导入：${state.experiment.events.length} 个时间片。`, "success");
    setPane("stage");
  } catch (error) {
    setMessage(error.message, "error");
    renderTimelineRail();
  } finally {
    setShellBusy(null);
    setBusy(button, false);
  }
}

async function submitAnalyze(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!state.experiment || state.experiment.experiment_id === "demo") {
    setMessage("请先粘贴链接或上传已授权的真实视频。", "error");
    return;
  }
  const button = $("#analyze-button");
  const provider = $("#provider")?.value || "codex-frames";
  setBusy(button, true, "正在分析");
  setShellBusy("analyze");
  setMessage(provider === "gemini"
    ? "原生视频模型正在读取完整视频；完成后会融合进证据时间轴。请勿关闭页面。"
    : "Codex 正在分析带时间戳证据帧；原视频和音轨不会发送，帧间内容保持不确定。请勿关闭页面。");
  try {
    state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(state.experiment.experiment_id)}/analyze`, {
      method: "POST",
      body: new FormData(form),
    });
    await refreshExperimentIndex();
    renderExperiment();
    setMessage("多模态事实层已写入 Timeline；请检查推断状态、不确定性和 Provider 限制。", "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    $$('input[name="remote_processing_confirmed"], input[name="provider_policy_confirmed"]', form)
      .forEach(input => { input.checked = false; });
    setShellBusy(null);
    setBusy(button, false);
  }
}

async function submitRun(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!state.experiment) return;
  const button = $("#run-button");
  setBusy(button, true, "正在运行");
  setShellBusy("run");
  setMessage("Persona 正在按时间顺序体验当前素材。模型模式按事件计费并受调用上限保护。");
  try {
    state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(state.experiment.experiment_id)}/run`, {
      method: "POST",
      body: new FormData(form),
    });
    await refreshExperimentIndex();
    renderExperiment();
    setMessage(`完成 ${state.experiment.counts.deep_personas} 个 Deep Persona、${state.experiment.counts.deep_trace_events} 条 Trace。数值仍为未校准代理量。`, "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    $$('input[name="agent_remote_processing_confirmed"], input[name="agent_provider_policy_confirmed"]', form)
      .forEach(input => { input.checked = false; });
    setShellBusy(null);
    setBusy(button, false);
  }
}

async function submitCalibration(event) {
  event.preventDefault();
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
    setMessage("Human Anchors 已对齐；Agent 与真人数量保持独立。", "success");
  } catch (error) {
    setMessage(error.message, "error");
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

  $("#load-demo")?.addEventListener("click", async () => {
    setMessage("正在恢复公开 Demo。");
    try {
      await loadExperiment("demo");
      setMessage("已恢复公开合成 Demo。", "success");
    } catch (error) {
      setMessage(error.message, "error");
    }
  });
  $("#aperture-retry")?.addEventListener("click", async () => {
    try {
      await loadExperiment("demo");
      setMessage("已恢复公开合成 Demo。", "success");
    } catch (error) {
      setMessage(error.message, "error");
    }
  });
  $("#recent-experiment-list")?.addEventListener("click", async event => {
    const button = event.target.closest("[data-experiment-id]");
    if (!button) return;
    setBusy(button, true);
    try {
      await loadExperiment(button.dataset.experimentId);
      setMessage("已从本地制品恢复实验。", "success");
      setPane("stage");
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
  $('select[name="runtime_mode"]')?.addEventListener("change", event => setRuntimeMode(event.currentTarget.value));
  $("#agent-reasoner")?.addEventListener("change", event => setAgentReasoner(event.currentTarget.value));
  $("#provider")?.addEventListener("change", event => setVideoProvider(event.currentTarget.value));

  $("#cue-prev")?.addEventListener("click", () => selectEvent(state.selectedEventIndex - 1));
  $("#cue-next")?.addEventListener("click", () => selectEvent(state.selectedEventIndex + 1));
  $("#timeline-rail")?.addEventListener("scroll", scheduleLightPath, { passive: true });

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
    button.addEventListener("click", () => setPane(button.dataset.paneTarget));
  });
  $$("[data-stage-target]").forEach(button => {
    button.addEventListener("click", () => STAGE_ACTIONS[button.dataset.stageTarget]?.());
  });

  $("#setup-message-dismiss")?.addEventListener("click", () => setMessage(""));

  window.addEventListener("resize", scheduleLightPath);
  const workbench = $("#workbench");
  if (typeof ResizeObserver === "function" && workbench instanceof Element) {
    new ResizeObserver(scheduleLightPath).observe(workbench);
  }
}

function applyDeepLinks(params) {
  const view = params.get("view");
  if (view && INSPECTOR_VIEWS.includes(view)) setInspectorView(view);
  const cue = Number(params.get("cue"));
  if (Number.isFinite(cue) && cue >= 1) selectEvent(cue - 1);
}

async function initialize() {
  bindEvents();
  setSourceMode($('input[name="source_mode"]:checked')?.value || "url");
  setAgentReasoner($("#agent-reasoner")?.value || "codex-cli");
  setVideoProvider($("#provider")?.value || "codex-frames");
  setRuntimeMode($('select[name="runtime_mode"]')?.value || "deterministic");
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
      setMessage(`${error.message} 已恢复公开 Demo。`, "error");
    } catch {
      setMessage(error.message, "error");
      setApertureState("error", "无法读取实验", `${error.message} 请确认本地服务在运行，然后重试。`);
    }
  }
}

initialize();
