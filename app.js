const STATUS = {
  queued: "\ub300\uae30",
  running: "\uc9c4\ud589 \uc911",
  needs_revision: "\uc218\uc815 \ud544\uc694",
  publishing: "\uac8c\uc2dc \uc911",
  completed: "\uc644\ub8cc",
  completed_markdown_only: "Markdown \uc644\ub8cc",
  failed: "\uc2e4\ud328",
  blocked: "\ucc28\ub2e8",
  cancelled: "\ucde8\uc18c",
  intake: "\uc900\ube44",
  needs_clarification: "\ud655\uc778 \ud544\uc694",
};

const TERMINAL_STATES = new Set(["completed", "completed_markdown_only", "failed", "blocked", "cancelled", "needs_clarification"]);

const elements = {
  runForm: document.querySelector("#runForm"),
  titleInput: document.querySelector("#titleInput"),
  briefInput: document.querySelector("#briefInput"),
  runButton: document.querySelector("#runButton"),
  runList: document.querySelector("#runList"),
  workspaceTitle: document.querySelector("#workspaceTitle"),
  statusMessage: document.querySelector("#statusMessage"),
  stepList: document.querySelector("#stepList"),
  selectedRole: document.querySelector("#selectedRole"),
  selectedLabel: document.querySelector("#selectedLabel"),
  selectedTokens: document.querySelector("#selectedTokens"),
  selectedState: document.querySelector("#selectedState"),
  detailViewer: document.querySelector("#detailViewer"),
  subtabs: document.querySelector("#subtabs"),
  subtabDescription: document.querySelector("#subtabDescription"),
};

const ROLE_DESCRIPTIONS = {
  manager: "작업 목표와 산출물 계약을 구조화합니다.",
  researcher: "근거, 출처, 주장, 숫자, 공백을 추출합니다.",
  evidence_auditor: "근거의 사용 가능성과 제한 사항을 판정합니다.",
  analyst: "감사된 근거로 의사결정 모델을 작성합니다.",
  writer: "분석을 독자용 보고서 초안으로 작성합니다.",
  reviewer: "초안의 품질, 근거, 추적성을 감사합니다.",
  revision_writer: "검토자가 지정한 수정만 반영합니다.",
  final_verifier: "최종 후보의 발행 가능 여부를 확인합니다.",
  publisher: "검증된 후보를 최종 산출물로 발행합니다.",
};

const VIEW_DESCRIPTIONS = {
  prompt: "Agent 실행에 사용된 전체 프롬프트입니다.",
  "00_task_contract.json": "작업 진행 여부와 요구사항을 담은 구조화 계약입니다.",
  "00_task_brief.md": "후속 Agent가 공유하는 사람이 읽는 작업 요약입니다.",
  "01_research.md": "조사 계획과 핵심 근거 메모입니다.",
  "01_sources.md": "사용된 출처의 ID, 날짜, 신뢰도, 한계입니다.",
  "01_claims.md": "주장 ID와 출처 ID의 예비 연결표입니다.",
  "01_gaps.md": "근거 공백, 미해결 주장, 후속 검색 항목입니다.",
  "01_numeric_assumptions.md": "숫자, 기간, 단위, 출처를 추적하는 장부입니다.",
  "01_source_provenance.md": "검색어, 접근 경로, URL, 접근일의 출처 이력입니다.",
  "02_evidence_gate.json": "분석 진행 가능 여부를 결정하는 근거 게이트입니다.",
  "02_evidence_audit.md": "근거 사용, 제외, caveat 지침의 사람이 읽는 감사 결과입니다.",
  "03a_decision_frame.md": "의사결정 질문, 옵션, 기준, 제약을 정리합니다.",
  "03b_option_evaluation.md": "옵션별 기준 평가와 근거 ID를 비교합니다.",
  "03c_scenarios_and_recommendation.md": "시나리오, 조정 논리, 추천안을 정리합니다.",
  "03_analysis.md": "Writer가 사용할 분석 요약본입니다.",
  "03_analysis_status.json": "분석 결과가 작성 단계로 넘어갈 수 있는지 나타냅니다.",
  "04_draft.md": "독자에게 보여줄 보고서 초안입니다.",
  "04_writer_trace.md": "초안의 핵심 주장과 근거 ID를 연결한 추적표입니다.",
  "05_review_decision.json": "검토 통과/수정 필요 여부와 수정 ID를 담은 결정값입니다.",
  "05_review.md": "초안 품질에 대한 사람이 읽는 검토 결과입니다.",
  "05_claim_audit.md": "초안 내 주장별 근거 추적성 감사표입니다.",
  "06_revision.md": "필수 수정사항이 반영된 개정 초안입니다.",
  "06_revision_trace.md": "수정 ID별 반영 여부와 변경 위치입니다.",
  "07_final_verification.json": "최종 발행 가능 여부를 결정하는 게이트입니다.",
  "07_final_verification.md": "최종 후보 검증의 사람이 읽는 결과입니다.",
  "08_final.md": "검증된 후보를 복사한 최종 Markdown 보고서입니다.",
  "08_final_manifest.json": "발행 시각, 선택 후보, 해시, caveat, DOCX 상태입니다.",
};

let currentRun = null;
let currentRunId = "";
let selectedRoleKey = "manager";
let selectedView = "prompt";
let pollTimer = null;

async function apiJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json; charset=utf-8" },
    ...options,
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) throw new Error(payload?.error || `Request failed: ${response.status}`);
  return payload;
}

async function apiText(path) {
  const response = await fetch(path);
  return response.ok ? response.text() : "";
}

async function loadRuns() {
  const runs = await apiJson("/api/runs");
  renderRunList(runs);
  if (!currentRunId && runs.length) await loadRun(runs[0].id);
}

async function loadRun(runId) {
  currentRunId = runId;
  currentRun = await apiJson(`/api/runs/${encodeURIComponent(runId)}`);
  markActiveRunItem(runId);
  if (!currentRun.roles.some((role) => role.key === selectedRoleKey)) {
    selectedRoleKey = currentRun.roles[0]?.key || "manager";
  }
  ensureSelectedView();
  render();
  await loadVisibleFiles();
  schedulePolling();
}

async function createRun(title, brief) {
  setRunButton(true);
  try {
    const run = await apiJson("/api/runs", {
      method: "POST",
      body: JSON.stringify({ title, brief, mode: "quality-first" }),
    });
    elements.titleInput.value = "";
    elements.briefInput.value = "";
    selectedRoleKey = "manager";
    selectedView = "prompt";
    await loadRun(run.id);
    await loadRuns();
  } finally {
    setRunButton(false);
  }
}

function setRunButton(isRunning) {
  elements.runButton.disabled = isRunning;
  elements.runButton.querySelector("span:last-child").textContent = isRunning ? "\uc2e4\ud589 \uc911..." : "\uc791\uc5c5 \uc2e4\ud589";
}

function render() {
  if (!currentRun) {
    renderEmpty();
    return;
  }
  const { task, status, roles } = currentRun;
  const selectedRole = findSelectedRole();
  const completed = completedRoleKeys(status);
  const usage = tokenUsageForRole(selectedRole);
  const totalUsage = totalTokenUsage(status);
  const roleDuration = durationForRole(selectedRole, status, completed);
  const totalDuration = durationForRun(task, status);

  elements.workspaceTitle.textContent = task.title;
  elements.statusMessage.textContent = formatUsageAndDuration(totalUsage, totalDuration);
  elements.statusMessage.title = formatTokenUsageDetail(totalUsage);
  elements.selectedRole.textContent = formatRoleHeading(selectedRole);
  elements.selectedLabel.textContent = selectedRole.label;
  elements.selectedTokens.textContent = formatUsageAndDuration(usage, roleDuration);
  elements.selectedTokens.title = formatTokenUsageDetail(usage);
  elements.selectedState.textContent = roleStateLabel(selectedRole, status, completed);

  renderSteps(roles, status, completed);
  renderSubtabs();
}

function renderEmpty() {
  elements.workspaceTitle.textContent = "\ubcf4\uace0\uc11c \uc791\uc5c5\uc744 \uc2dc\uc791\ud558\uc138\uc694";
  elements.statusMessage.textContent = "\ud1a0\ud070 - \u00b7 \uc18c\uc694\uc2dc\uac04 -";
  elements.statusMessage.title = "";
  elements.stepList.innerHTML = "";
  renderDetail("\uc9c4\ud589 \ub2e8\uacc4\uc5d0\uc11c Agent\ub97c \uc120\ud0dd\ud558\uc138\uc694.");
  elements.selectedTokens.textContent = "\ud1a0\ud070 - \u00b7 \uc18c\uc694\uc2dc\uac04 -";
  elements.selectedTokens.title = "";
  elements.selectedState.textContent = "\ub300\uae30";
  renderSubtabs();
}

function renderRunList(runs) {
  if (!runs.length) {
    elements.runList.innerHTML = `<p class="empty-note">\uc800\uc7a5\ub41c \uc791\uc5c5\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.</p>`;
    return;
  }
  elements.runList.innerHTML = "";
  runs.forEach((run) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.runId = run.id;
    button.className = `run-item ${run.id === currentRunId ? "active" : ""}`;
    button.innerHTML = `
      <strong>${escapeHtml(run.task.title)}</strong>
      <small>${escapeHtml(formatRunTime(run))}</small>
    `;
    button.addEventListener("click", () => loadRun(run.id));
    elements.runList.appendChild(button);
  });
}

function markActiveRunItem(runId) {
  elements.runList.querySelectorAll(".run-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.runId === runId);
  });
}

function renderSteps(roles, status, completed) {
  elements.stepList.innerHTML = "";
  roles.forEach((role, index) => {
    const state = roleStateLabel(role, status, completed);
    const button = document.createElement("button");
    button.type = "button";
    button.className = `step-item ${role.key === selectedRoleKey ? "selected" : ""} ${stateClass(state)}`;
    button.innerHTML = `
      <span class="step-number">${index + 1}</span>
      <span class="step-text">
        <strong>${escapeHtml(role.display_role || role.role)}</strong>
        <small>${state}</small>
      </span>
    `;
    button.addEventListener("click", async () => {
      selectedRoleKey = role.key;
      ensureSelectedView();
      render();
      await loadVisibleFiles();
    });
    elements.stepList.appendChild(button);
  });
}

function renderSubtabs() {
  const selectedRole = currentRun ? findSelectedRole() : null;
  const views = viewsForRole(selectedRole);
  elements.subtabs.innerHTML = "";
  elements.subtabs.style.setProperty("--tab-count", String(Math.max(views.length, 1)));
  views.forEach((view) => {
    const button = document.createElement("button");
    button.className = `subtab ${view.key === selectedView ? "active" : ""}`;
    button.type = "button";
    button.dataset.view = view.key;
    button.textContent = view.label;
    button.addEventListener("click", async () => {
      selectedView = view.key;
      renderSubtabs();
      await loadVisibleFiles();
    });
    elements.subtabs.appendChild(button);
  });
  renderSubtabDescription(views.find((view) => view.key === selectedView) || views[0]);
}

function renderSubtabDescription(view) {
  if (!elements.subtabDescription) return;
  if (!view) {
    elements.subtabDescription.textContent = "";
    return;
  }
  elements.subtabDescription.textContent = `${view.label} : ${descriptionForView(view)}`;
}

async function loadVisibleFiles() {
  if (!currentRun) return;
  const selectedRole = findSelectedRole();
  const view = viewsForRole(selectedRole).find((item) => item.key === selectedView);
  const path = view?.path || "";
  const detail = await readRunFile(path);
  const visibleDetail = selectedView === "prompt" ? summarizePromptInputs(detail) : detail;
  renderDetail(visibleDetail || `${view?.label || "\ud30c\uc77c"} \ud30c\uc77c\uc774 \uc544\uc9c1 \uc0dd\uc131\ub418\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4.`);
}

function renderDetail(markdown) {
  elements.detailViewer.innerHTML = markdownToHtml(markdown);
}

function markdownToHtml(markdown) {
  const lines = String(markdown || "").split(/\r?\n/);
  const html = [];
  let paragraph = [];
  let listOpen = false;

  const closeParagraph = () => {
    if (!paragraph.length) return;
    html.push(`<p>${formatInline(paragraph.join(" "))}</p>`);
    paragraph = [];
  };
  const closeList = () => {
    if (!listOpen) return;
    html.push("</ul>");
    listOpen = false;
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      closeParagraph();
      closeList();
      continue;
    }
    const heading = /^(#{1,4})\s+(.+)$/.exec(trimmed);
    if (heading) {
      closeParagraph();
      closeList();
      const level = Math.min(heading[1].length + 2, 6);
      html.push(`<h${level}>${formatInline(heading[2])}</h${level}>`);
      continue;
    }
    const bullet = /^[-*]\s+(.+)$/.exec(trimmed);
    if (bullet) {
      closeParagraph();
      if (!listOpen) {
        html.push("<ul>");
        listOpen = true;
      }
      html.push(`<li>${formatInline(bullet[1])}</li>`);
      continue;
    }
    paragraph.push(trimmed);
  }
  closeParagraph();
  closeList();
  return html.join("");
}

function formatInline(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function summarizePromptInputs(promptText) {
  if (!promptText) return "";
  const lines = promptText.split(/\r?\n/);
  const output = [];
  let skipInputBody = false;
  for (const line of lines) {
    if (line.startsWith("# Input: artifacts/")) {
      output.push(line);
      output.push("(\uc774\uc804 Agent \uc0b0\ucd9c\ubb3c \ubcf8\ubb38\uc740 \ud654\uba74\uc5d0\uc11c \uc0dd\ub7b5\ud588\uc2b5\ub2c8\ub2e4. \ud574\ub2f9 Agent \ud0ed\uc5d0\uc11c \uc5f4\uc5b4\ubcf4\uc138\uc694.)");
      skipInputBody = true;
      continue;
    }
    if (skipInputBody && isPromptSectionHeading(line)) skipInputBody = false;
    if (!skipInputBody) output.push(line);
  }
  return output.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

function isPromptSectionHeading(line) {
  return /^# (Reference:|Publisher Instruction|Role Prompt|Run Context|Input:)/.test(line);
}

function readRunFile(path) {
  if (!currentRunId || !path) return "";
  return apiText(`/api/runs/${encodeURIComponent(currentRunId)}/files?path=${encodeURIComponent(path)}`);
}

function schedulePolling() {
  if (pollTimer) clearInterval(pollTimer);
  if (!currentRun || TERMINAL_STATES.has(currentRun.status.state)) return;
  pollTimer = setInterval(async () => {
    if (!currentRunId) return;
    currentRun = await apiJson(`/api/runs/${encodeURIComponent(currentRunId)}`);
    ensureSelectedView();
    render();
    await loadVisibleFiles();
    if (TERMINAL_STATES.has(currentRun.status.state)) {
      clearInterval(pollTimer);
      pollTimer = null;
      await loadRuns();
    }
  }, 2500);
}

function findSelectedRole() {
  return currentRun.roles.find((role) => role.key === selectedRoleKey) || currentRun.roles[0];
}

function viewsForRole(role) {
  if (!role) return [];
  return [
    ...(role.prompt ? [{ key: "prompt", label: "Prompt", path: role.prompt }] : []),
    ...(role.artifacts || [{ label: role.label, path: role.artifact }]).map((artifact) => ({
      key: artifact.path,
      label: artifact.label,
      path: artifact.path,
    })),
  ];
}

function ensureSelectedView() {
  const views = viewsForRole(currentRun ? findSelectedRole() : null);
  if (!views.some((view) => view.key === selectedView)) selectedView = views[0]?.key || "prompt";
}

function completedRoleKeys(status) {
  return new Set((status.agent_runs || []).map((run) => run.key || roleKeyFromArtifact(run.artifact)));
}

function roleKeyFromArtifact(path) {
  const role = currentRun?.roles.find((item) => item.artifact === path);
  return role?.key || "";
}

function tokenUsageForRole(role) {
  const run = (currentRun?.status.agent_runs || []).find((item) => (item.key || roleKeyFromArtifact(item.artifact)) === role.key);
  return run?.usage || null;
}

function agentRunForRole(role) {
  return (currentRun?.status.agent_runs || []).find((item) => (item.key || roleKeyFromArtifact(item.artifact)) === role.key) || null;
}

function totalTokenUsage(status) {
  const total = {};
  for (const run of status.agent_runs || []) {
    const usage = run.usage || {};
    for (const [key, value] of Object.entries(usage)) {
      if (typeof value === "number" && Number.isFinite(value)) total[key] = (total[key] || 0) + value;
    }
  }
  return Object.keys(total).length ? total : null;
}

function tokenTotal(usage) {
  if (!usage) return 0;
  return Number(usage.input_tokens || 0) + Number(usage.output_tokens || 0);
}

function formatTokenUsage(usage) {
  if (!usage) return "\ud1a0\ud070 -";
  return `\ud1a0\ud070 ${formatNumber(tokenTotal(usage))} (\uc785\ub825 ${formatNumber(usage.input_tokens)} + \ucd9c\ub825 ${formatNumber(usage.output_tokens)})`;
}

function formatUsageAndDuration(usage, durationMs) {
  return `${formatTokenUsage(usage)} \u00b7 ${formatDuration(durationMs)}`;
}

function formatTokenUsageDetail(usage) {
  if (!usage) return "\uc544\uc9c1 \ud1a0\ud070 \uc0ac\uc6a9\ub7c9\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.";
  const parts = [
    `\ucd1d ${formatNumber(tokenTotal(usage))}`,
    `\uc785\ub825 ${formatNumber(usage.input_tokens)}`,
    `\ucd9c\ub825 ${formatNumber(usage.output_tokens)}`,
  ];
  if (usage.cached_input_tokens) parts.push(`\uce90\uc2dc ${formatNumber(usage.cached_input_tokens)}`);
  if (usage.reasoning_output_tokens) parts.push(`\ucd94\ub860 ${formatNumber(usage.reasoning_output_tokens)}`);
  return parts.join(" \u00b7 ");
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("ko-KR");
}

function formatRoleHeading(role) {
  const name = role.display_role || role.role;
  return `${name} : ${ROLE_DESCRIPTIONS[role.key] || "\uc774 \ub2e8\uacc4\uc758 \uc0b0\ucd9c\ubb3c\uc744 \uc0dd\uc131\ud569\ub2c8\ub2e4."}`;
}

function descriptionForView(view) {
  const pathKey = (view.path || view.key || "").replace(/^artifacts\//, "").replace(/^prompts\//, "");
  return VIEW_DESCRIPTIONS[pathKey] || VIEW_DESCRIPTIONS[view.key] || "\uc120\ud0dd\ud55c \uc0b0\ucd9c\ubb3c\uc758 \ub0b4\uc6a9\uc744 \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.";
}

function durationForRole(role, status, completed) {
  const run = agentRunForRole(role);
  if (run?.started_at && run?.completed_at) return durationBetween(run.started_at, run.completed_at);
  if (isCurrentRole(role, status) && status.current_role_started_at) return durationBetween(status.current_role_started_at, new Date().toISOString());
  if (completed.has(role.key) && run?.completed_at) return 0;
  return null;
}

function durationForRun(task, status) {
  const start = task?.created_at || status?.created_at;
  if (!start) return null;
  const end = TERMINAL_STATES.has(status.state) ? status.updated_at : new Date().toISOString();
  return durationBetween(start, end);
}

function durationBetween(startValue, endValue) {
  const start = new Date(startValue);
  const end = new Date(endValue);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  return Math.max(0, end.getTime() - start.getTime());
}

function formatDuration(ms) {
  if (ms === null || ms === undefined) return "\uc18c\uc694\uc2dc\uac04 -";
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `\uc18c\uc694\uc2dc\uac04 ${formatNumber(minutes)}\ubd84 ${remainingSeconds}\ucd08`;
}

function formatRunTime(run) {
  const iso = run.task?.created_at || run.status?.created_at || "";
  if (iso) return formatDateTime(iso);
  const match = /^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/.exec(run.id || "");
  if (!match) return run.id || "";
  return `${match[1]}-${match[2]}-${match[3]} ${match[4]}:${match[5]}:${match[6]}`;
}

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const parts = new Intl.DateTimeFormat("sv-SE", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);
  const map = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}:${map.second}`;
}

function roleStateLabel(role, status, completed) {
  if (completed.has(role.key)) return "\uc644\ub8cc";
  if (status.state === "failed" && isCurrentRole(role, status)) return "\uc2e4\ud328";
  if (["running", "needs_revision", "publishing", "blocked", "needs_clarification"].includes(status.state) && isCurrentRole(role, status)) return translateState(status.state);
  return "\ub300\uae30";
}

function isCurrentRole(role, status) {
  return status.current_role === role.key || status.current_role === role.role || status.current_role === role.display_role;
}

function stateClass(state) {
  return {
    "\uc644\ub8cc": "done",
    "\uc9c4\ud589 \uc911": "active",
    "\uc218\uc815 \ud544\uc694": "active",
    "\uac8c\uc2dc \uc911": "active",
    "\uc2e4\ud328": "failed",
    "\ucc28\ub2e8": "failed",
    "\ud655\uc778 \ud544\uc694": "active",
  }[state] || "";
}

function translateState(state) {
  return STATUS[state] || "\ub300\uae30";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

elements.runForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = elements.titleInput.value.trim();
  const brief = elements.briefInput.value.trim();
  if (!brief) {
    elements.statusMessage.textContent = "\ubcf4\uace0\uc11c \ub0b4\uc6a9\uc744 \uc785\ub825\ud574\uc57c \uc2e4\ud589\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.";
    return;
  }
  try {
    await createRun(title, brief);
  } catch (error) {
    elements.statusMessage.textContent = error.message;
  }
});

loadRuns().catch((error) => {
  elements.statusMessage.textContent = `\uc11c\ubc84 \uc5f0\uacb0 \uc2e4\ud328: ${error.message}`;
});
