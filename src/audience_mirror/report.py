"""Self-contained evidence report for the deterministic local baseline."""

from __future__ import annotations

from collections import Counter, defaultdict
from html import escape
from statistics import fmean
from typing import Any

from .domain import Persona


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def _timecode(milliseconds: int) -> str:
    total_seconds = milliseconds // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def _average(values: list[float]) -> float:
    return fmean(values) if values else 0.0


def _scale_ledger(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    rows = (
        ("Persona Pool", counts["persona_pool_records"], "可检索合成记录；没有被执行"),
        ("Deep Persona", counts["deep_personas"], "完整顺序体验的独立 Session"),
        ("Deep Trace Event", counts["deep_trace_events"], "可回链到 Timeline 证据的事件"),
        ("Broad Sweep", counts["broad_sweep_runs"], "只读取冻结摘要；不是完整观看"),
        ("Projected Record", counts["projected_records"], "规则投影；零逐 Persona LLM 调用"),
        ("Human Participant", counts["human_participants"], "本地 Fixture 没有真人数据"),
    )
    return "".join(
        f"<tr><th scope='row'>{_e(label)}</th><td class='num'>{value:,}</td><td>{_e(meaning)}</td></tr>"
        for label, value, meaning in rows
    )


def _event_rows(timeline: dict[str, Any], traces: list[dict[str, Any]]) -> str:
    traces_by_node: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        traces_by_node[trace["timeline"]["timeline_node_id"]].append(trace)

    rows: list[str] = []
    for node in sorted(
        (item for item in timeline["nodes"] if item["level"] == "event"),
        key=lambda item: item["t_start_ms"],
    ):
        node_traces = traces_by_node[node["node_id"]]
        confusion_values = [item["state"]["after"]["confusion"] for item in node_traces]
        attention_values = [item["state"]["after"]["attention_proxy"] for item in node_traces]
        continue_values = [item["state"]["after"]["continue_intent"] for item in node_traces]
        high_confusion = max(node_traces, key=lambda item: item["state"]["after"]["confusion"])
        low_confusion = min(node_traces, key=lambda item: item["state"]["after"]["confusion"])
        observation_id = node["observations"][0]["observation_id"]
        high_target = f"trace-{high_confusion['trace_event_id']}"
        low_target = f"trace-{low_confusion['trace_event_id']}"
        rows.append(
            "".join(
                (
                    f"<tr id='timeline-{_e(node['node_id'])}'>",
                    f"<td class='time'>{_timecode(node['t_start_ms'])}–{_timecode(node['t_end_ms'])}</td>",
                    f"<td><strong>{_e(node['label'])}</strong><span class='sub' id='observation-{_e(observation_id)}'>{_e(node.get('summary', ''))}</span></td>",
                    f"<td class='num'>{_pct(_average(confusion_values))}</td>",
                    f"<td class='num'>{_pct(_average(attention_values))}</td>",
                    f"<td class='num'>{_pct(_average(continue_values))}</td>",
                    "<td>",
                    f"<span class='sub'>高困惑：<a class='trace-link' href='#{_e(high_target)}' data-trace-target='{_e(high_target)}'>{_e(high_confusion['agent_id'])}</a></span>",
                    f"<span class='sub'>反例：<a class='trace-link' href='#{_e(low_target)}' data-trace-target='{_e(low_target)}'>{_e(low_confusion['agent_id'])}</a></span>",
                    "</td></tr>",
                )
            )
        )
    return "".join(rows)


def _session_rows(personas: list[Persona], traces: list[dict[str, Any]]) -> str:
    persona_by_id = {persona.persona_id: persona for persona in personas}
    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        sessions[trace["session_id"]].append(trace)

    rendered: list[str] = []
    for session_id in sorted(sessions):
        session_traces = sorted(sessions[session_id], key=lambda item: item["session_sequence_no"])
        persona = persona_by_id[session_traces[0]["agent_id"]]
        final = session_traces[-1]
        final_state = final["state"]["after"]
        event_rows = "".join(
            "".join(
                (
                    f"<tr id='trace-{_e(trace['trace_event_id'])}' tabindex='-1'>",
                    f"<td class='time'>{_timecode(trace['timeline']['t_start_ms'])}</td>",
                    f"<td><a class='evidence-link' href='#timeline-{_e(trace['timeline']['timeline_node_id'])}'>{_e(trace['timeline']['timeline_node_id'])}</a></td>",
                    f"<td>{_e(trace['reaction']['reaction_type'])}<span class='sub'>{_e(trace['reaction']['summary'])}</span></td>",
                    f"<td class='num'>{_pct(trace['state']['after']['confusion'])}</td>",
                    f"<td class='num'>{_pct(trace['state']['after']['continue_intent'])}</td>",
                    f"<td>{_e(trace['action']['action_type'])}<span class='sub'>{_e(trace['action']['reason_summary'])}</span></td>",
                    f"<td><a class='evidence-link' href='#observation-{_e(trace['evidence'][0]['timeline_observation_id'])}'><code>{_e(trace['evidence'][0]['timeline_observation_id'])}</code></a></td>",
                    "</tr>",
                )
            )
            for trace in session_traces
        )
        rendered.append(
            f"""
            <article class="session" id="session-{_e(persona.persona_id)}" data-segment="{_e(persona.segment_id)}" data-persona="{_e(persona.persona_id)}">
              <details>
                <summary aria-label="展开 {_e(persona.persona_id)} 的 Trace">
                  <span class="session-title"><strong>{_e(persona.persona_id)}</strong><span>{_e(persona.segment_id)}</span></span>
                  <span class="session-outcome">理解 {_pct(final_state['comprehension'])} · 困惑 {_pct(final_state['confusion'])} · 继续 {_pct(final_state['continue_intent'])}</span>
                </summary>
                <div class="session-meta">
                  <span>观看环境：{_e(persona.attention_context)}</span>
                  <span>Persona 来源：合成 Fixture</span>
                  <span>最终状态：{_e(final['state']['session_status_after'])}</span>
                  <span>模型调用：0</span>
                </div>
                <div class="table-wrap">
                  <table>
                    <thead><tr><th>时间</th><th>Timeline 节点</th><th>反应代理量</th><th>困惑</th><th>继续</th><th>动作</th><th>证据</th></tr></thead>
                    <tbody>{event_rows}</tbody>
                  </table>
                </div>
              </details>
            </article>
            """
        )
    return "".join(rendered)


def _sweep_rows(results: list[dict[str, Any]]) -> str:
    by_segment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_segment[result["segment_id"]].append(result)
    return "".join(
        f"""
        <tr>
          <th scope="row">{_e(segment)}</th>
          <td class="num">{len(items):,}</td>
          <td class="num">{_pct(_average([item['comprehension_proxy'] for item in items]))}</td>
          <td class="num">{_pct(_average([item['continue_intent_proxy'] for item in items]))}</td>
          <td>{_e(dict(Counter(item['dropoff_risk_band'] for item in items)))}</td>
        </tr>
        """
        for segment, items in sorted(by_segment.items())
    )


def _projection_rows(projection: dict[str, Any]) -> str:
    return "".join(
        f"""
        <tr>
          <th scope="row">{_e(row['segment_id'])}</th>
          <td class="num">{row['projected_records']:,}</td>
          <td class="num">{row['low_risk']:,}</td>
          <td class="num">{row['medium_risk']:,}</td>
          <td class="num">{row['high_risk']:,}</td>
        </tr>
        """
        for row in projection["rows"]
    )


def build_report(
    *,
    timeline: dict[str, Any],
    personas: list[Persona],
    traces: list[dict[str, Any]],
    sweep: list[dict[str, Any]],
    projection: dict[str, Any],
    manifest: dict[str, Any],
) -> str:
    """Build an offline, accessible report with inspectable Trace evidence."""

    segment_options = "".join(
        f"<option value='{_e(segment)}'>{_e(segment)}</option>"
        for segment in sorted({persona.segment_id for persona in personas})
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="referrer" content="no-referrer">
  <title>Audience Mirror · 本地合成实验</title>
  <style>
    :root {{
      color-scheme: light dark;
      --canvas: oklch(1 0 0);
      --surface: oklch(.975 .004 250);
      --surface-strong: oklch(.945 .006 250);
      --ink: oklch(.18 .012 250);
      --muted: oklch(.48 .018 250);
      --tertiary: oklch(.41 .016 250);
      --line: oklch(.9 .008 250);
      --control-line: oklch(.54 .022 250);
      --accent: oklch(.5 .19 251);
      --warning: oklch(.92 .045 83);
      --warning-ink: oklch(.35 .07 72);
      --focus: oklch(.68 .17 251);
      --radius: 14px;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --canvas: oklch(.19 .008 250);
        --surface: oklch(.24 .01 250);
        --surface-strong: oklch(.29 .012 250);
        --ink: oklch(.92 .006 250);
        --muted: oklch(.76 .012 250);
        --tertiary: oklch(.75 .012 250);
        --line: oklch(.34 .012 250);
        --control-line: oklch(.68 .018 250);
        --accent: oklch(.77 .13 247);
        --warning: oklch(.3 .04 75);
        --warning-ink: oklch(.88 .07 83);
        --focus: oklch(.78 .13 247);
      }}
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; scroll-padding-top: 70px; }}
    body {{ margin: 0; background: var(--canvas); color: var(--ink); font-size: 15px; line-height: 1.55; }}
    ::selection {{ background: color-mix(in oklch, var(--accent) 28%, transparent); }}
    a {{ color: var(--accent); text-underline-offset: .2em; }}
    a:hover {{ text-decoration-thickness: 2px; }}
    button, input, select, summary {{ font: inherit; }}
    button, input, select {{ color: var(--ink); caret-color: var(--accent); }}
    :focus-visible {{ outline: 3px solid var(--focus); outline-offset: 3px; }}
    .topbar {{ position: sticky; top: 0; z-index: 20; background: color-mix(in oklch, var(--canvas) 94%, transparent); border-bottom: 1px solid var(--line); backdrop-filter: blur(10px); }}
    .topbar-inner {{ width: min(1180px, calc(100% - 40px)); min-height: 54px; margin: auto; display: flex; align-items: center; justify-content: space-between; gap: 24px; }}
    .brand {{ color: var(--ink); font-weight: 650; text-decoration: none; letter-spacing: -.01em; }}
    .topbar nav {{ display: flex; gap: 18px; flex-wrap: wrap; }}
    .topbar nav a {{ display: inline-flex; align-items: center; min-height: 44px; color: var(--muted); font-size: 13px; text-decoration: none; }}
    .topbar nav a:hover, .topbar nav a:active {{ color: var(--ink); }}
    main {{ width: min(1180px, calc(100% - 40px)); margin: 0 auto; padding: 52px 0 80px; }}
    .intro {{ max-width: 76ch; }}
    h1, h2, h3 {{ margin: 0; line-height: 1.2; text-wrap: balance; }}
    h1 {{ max-width: 14ch; font-family: "Songti SC", "Noto Serif CJK SC", "Source Han Serif SC", serif; font-size: clamp(2.25rem, 6vw, 4.8rem); letter-spacing: -.035em; font-weight: 700; }}
    h2 {{ font-size: clamp(1.45rem, 2.5vw, 2.05rem); letter-spacing: -.02em; font-weight: 620; }}
    h3 {{ font-size: 1rem; font-weight: 650; }}
    p {{ max-width: 72ch; text-wrap: pretty; }}
    .lede {{ margin: 20px 0 0; color: var(--muted); font-size: 1.08rem; }}
    .status-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 24px 0 0; }}
    .tag {{ display: inline-flex; align-items: center; min-height: 28px; padding: 3px 10px; border-radius: 999px; background: var(--surface); color: var(--muted); font-size: 12px; font-weight: 600; }}
    .tag.warning {{ background: var(--warning); color: var(--warning-ink); }}
    .notice {{ margin-top: 28px; padding: 16px 18px; border: 1px solid var(--line); border-radius: var(--radius); background: var(--warning); color: var(--warning-ink); }}
    .notice strong {{ display: block; margin-bottom: 4px; }}
    section {{ margin-top: 72px; scroll-margin-top: 70px; }}
    .section-head {{ display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 24px; }}
    .section-head p {{ margin: 8px 0 0; color: var(--muted); }}
    .table-wrap {{ max-width: 100%; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }}
    th, td {{ padding: 11px 14px 11px 0; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    thead th {{ color: var(--tertiary); font-size: 12px; font-weight: 650; white-space: nowrap; }}
    tbody th {{ color: var(--ink); font-weight: 600; }}
    td {{ color: var(--muted); }}
    .num {{ text-align: right; white-space: nowrap; }}
    .time, code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-variant-numeric: tabular-nums; font-size: .86em; }}
    .sub {{ display: block; margin-top: 3px; color: var(--tertiary); font-size: 12px; max-width: 52ch; }}
    .controls {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: end; }}
    label {{ display: grid; gap: 6px; color: var(--muted); font-size: 12px; font-weight: 600; }}
    input, select {{ min-height: 44px; padding: 8px 11px; border: 1px solid var(--control-line); border-radius: 10px; background: var(--canvas); }}
    input:hover, select:hover {{ border-color: var(--accent); }}
    input {{ min-width: min(320px, 74vw); }}
    .session-list {{ border-top: 1px solid var(--line); }}
    .session {{ border-bottom: 1px solid var(--line); }}
    .session[hidden] {{ display: none; }}
    details > summary {{ list-style: none; cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 24px; min-height: 56px; padding: 12px 0; }}
    details > summary:hover {{ color: var(--accent); }}
    details > summary::-webkit-details-marker {{ display: none; }}
    details > summary::after {{ content: ""; flex: none; width: 11px; height: 11px; margin-right: 4px; border-right: 2px solid var(--accent); border-bottom: 2px solid var(--accent); transform: rotate(45deg); transition: transform 160ms cubic-bezier(.22,1,.36,1); }}
    details[open] > summary::after {{ transform: rotate(225deg); }}
    .session-title {{ display: grid; gap: 2px; min-width: 220px; }}
    .session-title span, .session-outcome {{ color: var(--muted); font-size: 12px; }}
    .session-outcome {{ margin-left: auto; font-variant-numeric: tabular-nums; }}
    .session-meta {{ display: flex; gap: 8px 18px; flex-wrap: wrap; padding: 0 0 16px; color: var(--tertiary); font-size: 12px; }}
    .results-status {{ margin: 16px 0; color: var(--muted); font-size: 13px; }}
    .trace-link, .evidence-link {{ font-weight: 600; }}
    tr[id], span[id] {{ scroll-margin-top: 82px; }}
    tr[id]:focus {{ outline: 3px solid var(--focus); outline-offset: -3px; background: color-mix(in oklch, var(--accent) 8%, transparent); }}
    .manifest {{ padding: 18px; border-radius: var(--radius); background: var(--surface); }}
    .manifest dl {{ display: grid; grid-template-columns: minmax(150px, 220px) 1fr; gap: 8px 20px; margin: 0; }}
    .manifest dt {{ color: var(--muted); }}
    .manifest dd {{ margin: 0; overflow-wrap: anywhere; }}
    footer {{ margin-top: 80px; padding-top: 24px; border-top: 1px solid var(--line); color: var(--tertiary); font-size: 12px; }}
    * {{ scrollbar-color: var(--control-line) var(--surface); scrollbar-width: thin; }}
    *::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    *::-webkit-scrollbar-track {{ background: var(--surface); }}
    *::-webkit-scrollbar-thumb {{ border: 2px solid var(--surface); border-radius: 999px; background: var(--control-line); }}
    @media (max-width: 760px) {{
      .topbar-inner {{ width: min(100% - 28px, 1180px); align-items: flex-start; flex-direction: column; gap: 5px; padding: 10px 0; }}
      html {{ scroll-padding-top: 108px; }}
      .topbar nav {{ gap: 12px; }}
      main {{ width: min(100% - 28px, 1180px); padding-top: 36px; }}
      .section-head {{ align-items: flex-start; flex-direction: column; }}
      details > summary {{ align-items: flex-start; }}
      .session-outcome {{ display: none; }}
      .manifest dl {{ grid-template-columns: 1fr; gap: 2px; }}
      .manifest dd + dt {{ margin-top: 8px; }}
      section, tr[id], span[id] {{ scroll-margin-top: 108px; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} details > summary::after {{ transition: none; }} }}
    @media print {{ .topbar, .controls {{ display: none; }} main {{ width: 100%; padding: 0; }} details {{ break-inside: avoid; }} details > * {{ display: block; }} }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <a class="brand" href="#top">Audience Mirror</a>
      <nav aria-label="报告章节">
        <a href="#scope">证据口径</a><a href="#events">时间轴</a><a href="#traces">个体 Trace</a><a href="#scale">规模层</a><a href="#manifest">运行指纹</a>
      </nav>
    </div>
  </header>
  <main id="top">
    <div class="intro">
      <h1>先检查证据，再读结论。</h1>
      <p class="lede">这是一条无需 API Key 的本地工程基线。它证明 Timeline、Persona 分层、Trace 链、成本账本和报告下钻可以一起工作；不证明虚拟用户能预测真人。</p>
      <div class="status-row"><span class="tag warning">合成 Fixture</span><span class="tag">未校准</span><span class="tag">0 次模型调用</span><span class="tag">可复现</span></div>
      <div class="notice"><strong>不能用于业务预测</strong>注意、情绪、继续和付费均为工程代理量。Projection 没有执行独立观看，Deep Persona 也不是真人样本。</div>
    </div>

    <section id="scope">
      <div class="section-head"><div><h2>六种数量，六种证据含义</h2><p>规模数字被刻意拆开，避免把记录、运行、投影和真人混成一个 N。</p></div></div>
      <div class="table-wrap"><table><thead><tr><th>口径</th><th class="num">数量</th><th>能说明什么</th></tr></thead><tbody>{_scale_ledger(manifest)}</tbody></table></div>
    </section>

    <section id="events">
      <div class="section-head"><div><h2>每个问题回到一个具体事件</h2><p>表中展示 Deep Trace 的事件均值，同时保留最高困惑案例和最低困惑反例。</p></div></div>
      <div class="table-wrap"><table><thead><tr><th>时间</th><th>Timeline 事件</th><th class="num">困惑代理量</th><th class="num">注意代理量</th><th class="num">继续意向</th><th>个体差异</th></tr></thead><tbody>{_event_rows(timeline, traces)}</tbody></table></div>
    </section>

    <section id="traces">
      <div class="section-head">
        <div><h2>下钻到每个独立 Session</h2><p>只展示结构化观察与决策依据摘要，不展示或伪造隐藏思维链。</p></div>
        <div class="controls">
          <label>分群<select id="segment-filter"><option value="">全部分群</option>{segment_options}</select></label>
          <label>Persona 搜索<input id="persona-search" type="search" placeholder="例如 synthetic-persona-00001" autocomplete="off"></label>
        </div>
      </div>
      <p id="trace-status" class="results-status" role="status" aria-live="polite">显示 {len(personas)} / {len(personas)} 个 Session。</p>
      <div class="session-list">{_session_rows(personas, traces)}</div>
    </section>

    <section id="scale">
      <div class="section-head"><div><h2>Broad Sweep 与 Projection 不冒充完整观看</h2><p>Sweep 使用冻结摘要；Projection 只运行确定性规则。两者都显示真实调用量和限制。</p></div></div>
      <h3>Broad Sweep</h3>
      <div class="table-wrap"><table><thead><tr><th>分群</th><th class="num">Runs</th><th class="num">理解代理量</th><th class="num">继续意向</th><th>风险带分布</th></tr></thead><tbody>{_sweep_rows(sweep)}</tbody></table></div>
      <h3 style="margin-top: 34px">Population Projection</h3>
      <div class="table-wrap"><table><thead><tr><th>分群</th><th class="num">投影记录</th><th class="num">低风险</th><th class="num">中风险</th><th class="num">高风险</th></tr></thead><tbody>{_projection_rows(projection)}</tbody></table></div>
    </section>

    <section id="manifest">
      <div class="section-head"><div><h2>运行指纹与成本账本</h2><p>模型、Prompt、素材、Persona、代码和成本需要进入同一份可复现实验记录。</p></div></div>
      <div class="manifest"><dl>
        <dt>Experiment</dt><dd><code>{_e(manifest['experiment_id'])}</code></dd>
        <dt>Run</dt><dd><code>{_e(manifest['run_id'])}</code></dd>
        <dt>Timeline hash</dt><dd><code>{_e(manifest['timeline_hash'])}</code></dd>
        <dt>Persona universe</dt><dd><code>{_e(manifest['persona_universe_hash'])}</code></dd>
        <dt>Runtime</dt><dd>{_e(manifest['runtime']['producer'])} · {_e(manifest['runtime']['version'])}</dd>
        <dt>模型调用</dt><dd>{manifest['cost']['model_calls']} · USD {manifest['cost']['estimated_cost_usd']:.2f}</dd>
        <dt>校准状态</dt><dd>{_e(manifest['calibration_status'])}</dd>
        <dt>接受语境</dt><dd>{_e(manifest['reception_context']['condition'])}</dd>
        <dt>结果盲法</dt><dd>{'是' if manifest['reception_context']['outcome_blinded'] else '否'}</dd>
        <dt>代码状态</dt><dd>本地工程基线；尚未绑定 Git Commit</dd>
      </dl></div>
    </section>

    <footer>Audience Mirror local baseline · 所有内容均为合成 Fixture · 不含私密素材、真人记录或第三方 Persona 数据。</footer>
  </main>
  <script>
    (() => {{
      const segment = document.getElementById('segment-filter');
      const search = document.getElementById('persona-search');
      const sessions = Array.from(document.querySelectorAll('.session'));
      const status = document.getElementById('trace-status');
      const apply = () => {{
        const query = search.value.trim().toLowerCase();
        let visible = 0;
        sessions.forEach((session) => {{
          const segmentMatch = !segment.value || session.dataset.segment === segment.value;
          const searchMatch = !query || session.dataset.persona.toLowerCase().includes(query);
          session.hidden = !(segmentMatch && searchMatch);
          if (!session.hidden) visible += 1;
        }});
        status.textContent = visible === 0
          ? '没有符合当前筛选条件的 Session。'
          : `显示 ${{visible}} / ${{sessions.length}} 个 Session。`;
      }};
      segment.addEventListener('change', apply);
      search.addEventListener('input', apply);
      document.querySelectorAll('.trace-link').forEach((link) => {{
        link.addEventListener('click', (event) => {{
          event.preventDefault();
          segment.value = '';
          search.value = '';
          apply();
          const target = document.getElementById(link.dataset.traceTarget);
          if (!target) return;
          const details = target.closest('details');
          if (details) details.open = true;
          target.scrollIntoView({{block: 'center', behavior: 'auto'}});
          target.focus({{preventScroll: true}});
          history.replaceState(null, '', `#${{target.id}}`);
        }});
      }});
      apply();
    }})();
  </script>
</body>
</html>
"""
