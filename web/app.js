const state = {
  health: null,
  experiment: null,
  selectedEventIndex: 0,
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

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

function formatCount(value) {
  return value == null ? "—" : Number(value).toLocaleString("zh-CN");
}

function mean(values) {
  const numbers = values.map(Number).filter(Number.isFinite);
  return numbers.length ? numbers.reduce((sum, value) => sum + value, 0) / numbers.length : null;
}

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

function setBusy(button, busy, busyLabel) {
  if (!button) return;
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = busyLabel;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.label || button.textContent;
    button.disabled = false;
  }
}

function setMessage(message, kind = "") {
  const element = $("#setup-message");
  element.textContent = message;
  element.className = `form-message${kind ? ` is-${kind}` : ""}`;
}

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
    if (ref.object_ref && state.experiment.frame_urls?.[ref.object_ref]) {
      return state.experiment.frame_urls[ref.object_ref];
    }
  }
  return null;
}

function renderHealth() {
  const element = $("#system-state");
  if (!state.health) {
    element.textContent = "能力检查失败";
    element.className = "system-state is-error";
    return;
  }
  const capabilities = state.health.capabilities;
  const available = [
    capabilities.local_video_decode && "本地视频",
    capabilities.gemini_native_video && "原生视频模型",
    capabilities.human_calibration && "校准",
  ].filter(Boolean);
  element.textContent = available.length ? available.join(" · ") : "工程基线可用";
  element.className = "system-state is-ready";
  $("#native-model-status").textContent = capabilities.gemini_native_video
    ? "API Key 已配置，可在明确授权后调用。"
    : "未配置 Gemini Key；本地解析仍可用。";
}

function renderPipeline() {
  const experiment = state.experiment;
  const order = ["ingest", "analyze", "run", "calibrate"];
  let completedThrough = 0;
  if (experiment?.experiment_id !== "demo") completedThrough = 1;
  if (experiment?.timeline?.extensions?.semantic_analysis_complete) completedThrough = 2;
  if ((experiment?.traces || []).length) completedThrough = 3;
  if (experiment?.calibration) completedThrough = 4;
  $$(".pipeline li").forEach((item, index) => {
    const complete = index < completedThrough;
    const active = completedThrough < order.length && index === completedThrough;
    item.classList.toggle("is-complete", complete);
    item.classList.toggle("is-active", active);
    if (active) item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
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
  $$("#scale-values dd").forEach((element, index) => {
    element.textContent = formatCount(values[index]);
  });
}

function renderTimelineRail() {
  const rail = $("#timeline-rail");
  const events = state.experiment?.events || [];
  if (!events.length) {
    rail.innerHTML = '<li class="empty-copy">尚无时间轴事件。</li>';
    return;
  }
  rail.innerHTML = events.map((event, index) => `
    <li><button type="button" data-event-index="${index}" data-time="${formatTime(event.t_start_ms)}"
      class="${index === state.selectedEventIndex ? "is-selected" : ""}"
      aria-label="${escapeHTML(formatTime(event.t_start_ms))} ${escapeHTML(event.label)}"
      ${index === state.selectedEventIndex ? 'aria-current="true"' : ""}></button></li>
  `).join("");
  $$('[data-event-index]', rail).forEach(button => {
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
}

function renderMediaEvidence(event, frameURL) {
  const stage = $("#media-stage");
  const links = $("#media-evidence-links");
  const mediaURL = state.experiment?.media_url;
  if (mediaURL) {
    let video = $("#source-video", stage);
    if (!video || video.dataset.experimentId !== state.experiment.experiment_id) {
      stage.innerHTML = `<video id="source-video" controls preload="metadata" aria-label="原视频证据，包含声音" data-experiment-id="${escapeHTML(state.experiment.experiment_id)}" src="${escapeHTML(mediaURL)}">浏览器无法播放该原视频；请使用下方原始制品链接。</video>`;
      video = $("#source-video", stage);
    }
    if (frameURL) video.poster = frameURL;
    const seekSeconds = Number(event.t_start_ms || 0) / 1000;
    const seek = () => {
      if (Number.isFinite(seekSeconds)) video.currentTime = seekSeconds;
    };
    if (video.readyState >= 1) seek();
    else video.addEventListener("loadedmetadata", seek, { once: true });
    const audioLink = state.experiment.audio_url
      ? `<a href="${escapeHTML(state.experiment.audio_url)}" target="_blank" rel="noreferrer">抽取音轨 WAV</a>`
      : '<span>源文件未检测到可抽取音轨</span>';
    links.innerHTML = `<a href="${escapeHTML(mediaURL)}" target="_blank" rel="noreferrer">原视频制品</a>${audioLink}<span>选择时间片会定位到该段起点，不会自动播放。</span>`;
    return;
  }
  links.innerHTML = "";
  stage.innerHTML = frameURL
    ? `<img src="${escapeHTML(frameURL)}" alt="${escapeHTML(event.label)} 的解码证据帧">`
    : `<div class="media-placeholder"><strong>${escapeHTML(event.label)}</strong><span>${escapeHTML(event.summary || "该公开 Fixture 不包含原始媒体帧。")}</span></div>`;
}

function renderSelectedEvent() {
  const events = state.experiment?.events || [];
  if (!events.length) return;
  state.selectedEventIndex = Math.min(Math.max(state.selectedEventIndex, 0), events.length - 1);
  const event = events[state.selectedEventIndex];
  const metrics = eventMetrics(event);
  const frameURL = evidenceFrameURL(event);
  renderMediaEvidence(event, frameURL);
  $("#current-timecode").textContent = `${formatTime(event.t_start_ms)}–${formatTime(event.t_end_ms)}`;
  $("#current-label").textContent = event.label;
  $("#current-position").textContent = `${state.selectedEventIndex + 1} / ${events.length}`;
  $("#review-status").textContent = event.review_status || "未复核";
  $("#event-summary").textContent = event.summary || "该时间片没有摘要。";
  const metricValues = [metrics.confusion, metrics.attention, metrics.continueIntent];
  $$("#event-metrics dd").forEach((element, index) => {
    element.textContent = formatPercent(metricValues[index]);
  });
  const observations = event.observations || [];
  $("#observations").innerHTML = observations.length
    ? observations.map(observation => `<li>${escapeHTML(observation.text)}<span>${escapeHTML(observation.modality)} · ${escapeHTML(observation.epistemic_status)} · 置信 ${formatPercent(observation.confidence)}</span></li>`).join("")
    : "<li>尚无观察。</li>";
  renderExtremes(event, metrics.traces);
  $$("[data-event-index]", $("#timeline-rail")).forEach((button, index) => {
    button.classList.toggle("is-selected", index === state.selectedEventIndex);
    if (index === state.selectedEventIndex) button.setAttribute("aria-current", "true");
    else button.removeAttribute("aria-current");
  });
  const environment = state.experiment.environment || {};
  const provenance = [
    environment.contract_version || environment.schema_version,
    state.experiment.timeline?.schema_version,
    state.experiment.timeline?.asset?.content_hash?.slice(0, 12),
  ];
  $$("#evidence-provenance dd").forEach((element, index) => {
    element.textContent = provenance[index] || "—";
    element.title = provenance[index] || "";
  });
}

function renderExtremes(event, traces) {
  const target = $("#event-extremes");
  if (!traces.length) {
    target.className = "empty-copy";
    target.textContent = "运行 Deep Persona 后显示高反应与反例。";
    return;
  }
  const ordered = [...traces].sort((a, b) => b.state.after.confusion - a.state.after.confusion);
  const high = ordered[0];
  const low = ordered[ordered.length - 1];
  target.className = "";
  target.innerHTML = `
    <div class="extreme-row"><span>高困惑</span><button class="evidence-button" type="button" data-open-agent="${escapeHTML(high.agent_id)}" data-open-trace="${escapeHTML(high.trace_event_id)}">${escapeHTML(high.agent_id)} · ${formatPercent(high.state.after.confusion)}</button></div>
    <div class="extreme-row"><span>反例</span><button class="evidence-button" type="button" data-open-agent="${escapeHTML(low.agent_id)}" data-open-trace="${escapeHTML(low.trace_event_id)}">${escapeHTML(low.agent_id)} · ${formatPercent(low.state.after.confusion)}</button></div>
  `;
  $$('[data-open-agent]', target).forEach(button => {
    button.addEventListener("click", () => openTrace(button.dataset.openAgent, button.dataset.openTrace));
  });
}

function renderEventTable() {
  const events = state.experiment?.events || [];
  const body = $("#event-table-body");
  if (!events.length) {
    body.innerHTML = '<tr><td colspan="6">尚无时间轴。</td></tr>';
    return;
  }
  body.innerHTML = events.map((event, index) => {
    const metrics = eventMetrics(event);
    const traces = [...metrics.traces].sort((a, b) => b.state.after.confusion - a.state.after.confusion);
    const high = traces[0];
    const low = traces[traces.length - 1];
    const evidence = high
      ? `<button type="button" class="evidence-button" data-table-event="${index}">查看时间片</button><small>高：<button type="button" class="evidence-button" data-open-agent="${escapeHTML(high.agent_id)}" data-open-trace="${escapeHTML(high.trace_event_id)}">${escapeHTML(high.agent_id)}</button>${low && low !== high ? ` · 反例：<button type="button" class="evidence-button" data-open-agent="${escapeHTML(low.agent_id)}" data-open-trace="${escapeHTML(low.trace_event_id)}">${escapeHTML(low.agent_id)}</button>` : ""}</small>`
      : `<button type="button" class="evidence-button" data-table-event="${index}">查看时间片</button>`;
    return `<tr>
      <td class="numeric">${formatTime(event.t_start_ms)}–${formatTime(event.t_end_ms)}</td>
      <td><strong>${escapeHTML(event.label)}</strong><small>${escapeHTML(event.summary || "")}</small></td>
      <td class="numeric">${formatPercent(metrics.confusion)}</td>
      <td class="numeric">${formatPercent(metrics.attention)}</td>
      <td class="numeric">${formatPercent(metrics.continueIntent)}</td>
      <td>${evidence}</td>
    </tr>`;
  }).join("");
  $$('[data-table-event]', body).forEach(button => {
    button.addEventListener("click", () => {
      selectEvent(Number(button.dataset.tableEvent));
      $("#workspace").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  $$('[data-open-agent]', body).forEach(button => {
    button.addEventListener("click", () => openTrace(button.dataset.openAgent, button.dataset.openTrace));
  });
}

function renderTraces() {
  const target = $("#trace-list");
  const traces = state.experiment?.traces || [];
  const personas = new Map((state.experiment?.personas || []).map(persona => [persona.persona_id, persona]));
  const filter = $("#persona-filter").value.trim().toLowerCase();
  const sessions = new Map();
  traces.forEach(trace => {
    const list = sessions.get(trace.agent_id) || [];
    list.push(trace);
    sessions.set(trace.agent_id, list);
  });
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
        <span class="session-outcome">理解 ${formatPercent(final.state?.after?.comprehension)} · 困惑 ${formatPercent(final.state?.after?.confusion)} · 继续 ${formatPercent(final.state?.after?.continue_intent)}</span>
      </summary>
      <div class="trace-body table-wrap">
        <table><thead><tr><th>时间</th><th>节点</th><th>反应</th><th>困惑</th><th>继续</th><th>动作</th><th>Observation</th></tr></thead><tbody>${rows}</tbody></table>
      </div>
    </details>`;
  }).join("");
  $$('[data-trace-event-node]', target).forEach(button => {
    button.addEventListener("click", () => {
      const index = (state.experiment.events || []).findIndex(event => event.node_id === button.dataset.traceEventNode);
      if (index >= 0) selectEvent(index);
      $("#workspace").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function renderCalibration() {
  const calibration = state.experiment?.calibration;
  const target = $("#calibration-results");
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
    <p>${formatCount(calibration.scope.human_participants)} 位真人与 ${formatCount(calibration.scope.agent_sessions)} 个 Agent Session 分开报告；已排除 ${formatCount(calibration.scope.withdrawn_anchors_excluded)} 条撤回锚点。</p>
    <dl>
      <div><dt>Top 问题召回</dt><dd>${topRecall == null ? "无法计算" : formatPercent(topRecall)}</dd></div>
      <div><dt>时间点召回</dt><dd>${timeRecall == null ? "无法计算" : formatPercent(timeRecall)}</dd></div>
      <div><dt>同名代理量 MAE</dt><dd>${mae == null ? "无法计算" : Number(mae).toFixed(3)}</dd></div>
      <div><dt>A/B 方向</dt><dd>${abText}</dd></div>
    </dl>
    <p>${escapeHTML(calibration.numeric_proxy_alignment?.warning || "")}</p>`;
}

function renderExperiment() {
  if (!state.experiment) return;
  $("#experiment-id").textContent = state.experiment.experiment_id;
  $("#experiment-status").textContent = `${state.experiment.status} · ${state.experiment.runtime_mode}`;
  const classification = state.experiment.timeline?.data_handling?.data_classification || "unknown";
  const governance = $("#remote-governance");
  $("strong", governance).textContent = `本次远程处理边界 · ${classification}`;
  $("p", governance).textContent = classification === "confidential" || classification === "restricted"
    ? "当前为机密／受限素材：Gemini 公有 API 路由会拒绝处理，请切换到经确认的私有部署 Adapter。"
    : "Gemini 公有 API 由 Provider 管理地域；调用后请求删除远程文件，服务日志仍受当期 API 条款约束；本原型不替你断言训练使用政策。";
  renderPipeline();
  renderScale();
  renderTimelineRail();
  renderSelectedEvent();
  renderEventTable();
  renderTraces();
  renderCalibration();
}

function selectEvent(index) {
  state.selectedEventIndex = index;
  renderSelectedEvent();
}

function openTrace(agentId, traceId) {
  $("#persona-filter").value = "";
  renderTraces();
  const session = $(`#session-${CSS.escape(agentId)}`);
  if (!session) return;
  session.open = true;
  const trace = $(`#trace-${CSS.escape(traceId)}`);
  (trace || session).scrollIntoView({ behavior: "smooth", block: "center" });
  if (trace) trace.focus({ preventScroll: true });
}

async function loadExperiment(experimentId) {
  state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(experimentId)}`);
  state.selectedEventIndex = 0;
  renderExperiment();
}

async function submitUpload(event) {
  event.preventDefault();
  const button = $("#ingest-button");
  const formData = new FormData(event.currentTarget);
  setBusy(button, true, "正在解析");
  setMessage("正在本地解码视频、抽取证据帧与音轨。");
  try {
    state.experiment = await fetchJSON("/api/experiments", { method: "POST", body: formData });
    state.selectedEventIndex = 0;
    renderExperiment();
    setMessage(`解析完成：${state.experiment.events.length} 个时间片。`, "success");
    $("#workspace").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setBusy(button, false);
  }
}

async function submitAnalyze(event) {
  event.preventDefault();
  if (!state.experiment || state.experiment.experiment_id === "demo") {
    setMessage("请先上传已授权的真实视频。", "error");
    return;
  }
  const button = $("#analyze-button");
  setBusy(button, true, "正在分析");
  setMessage("原生视频模型正在读取完整视频；完成后会融合进证据时间轴。请勿关闭页面。");
  try {
    state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(state.experiment.experiment_id)}/analyze`, {
      method: "POST",
      body: new FormData(event.currentTarget),
    });
    renderExperiment();
    setMessage("多模态事实层已写入 Timeline；请检查推断状态与不确定性。", "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    $$('input[name="remote_processing_confirmed"], input[name="provider_policy_confirmed"]', event.currentTarget)
      .forEach(input => { input.checked = false; });
    setBusy(button, false);
  }
}

async function submitRun(event) {
  event.preventDefault();
  if (!state.experiment) return;
  const button = $("#run-button");
  setBusy(button, true, "正在运行");
  setMessage("Persona 正在按时间顺序体验当前素材。模型模式按事件计费并受调用上限保护。");
  try {
    state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(state.experiment.experiment_id)}/run`, {
      method: "POST",
      body: new FormData(event.currentTarget),
    });
    renderExperiment();
    setMessage(`完成 ${state.experiment.counts.deep_personas} 个 Deep Persona、${state.experiment.counts.deep_trace_events} 条 Trace。`, "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setBusy(button, false);
  }
}

async function submitCalibration(event) {
  event.preventDefault();
  if (!state.experiment) return;
  const button = $("#calibrate-button");
  const formData = new FormData(event.currentTarget);
  if (!formData.get("agent_ab_direction")) formData.delete("agent_ab_direction");
  setBusy(button, true, "正在校准");
  try {
    state.experiment = await fetchJSON(`/api/experiments/${encodeURIComponent(state.experiment.experiment_id)}/calibrate`, {
      method: "POST",
      body: formData,
    });
    renderExperiment();
    setMessage("Human Anchors 已对齐；Agent 与真人数量保持独立。", "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setBusy(button, false);
  }
}

function bindEvents() {
  $("#upload-form").addEventListener("submit", submitUpload);
  $("#analyze-form").addEventListener("submit", submitAnalyze);
  $("#run-form").addEventListener("submit", submitRun);
  $("#calibration-form").addEventListener("submit", submitCalibration);
  $("#load-demo").addEventListener("click", async () => {
    setMessage("正在恢复公开 Demo。");
    try {
      await loadExperiment("demo");
      setMessage("已恢复公开合成 Demo。", "success");
    } catch (error) {
      setMessage(error.message, "error");
    }
  });
  $("#persona-filter").addEventListener("input", renderTraces);
}

async function initialize() {
  bindEvents();
  try {
    state.health = await fetchJSON("/api/health");
  } catch {
    state.health = null;
  }
  renderHealth();
  try {
    const requestedExperiment = new URLSearchParams(window.location.search).get("experiment") || "demo";
    await loadExperiment(requestedExperiment);
  } catch (error) {
    setMessage(error.message, "error");
  }
}

initialize();
