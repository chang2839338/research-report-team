const STATUS = {
  queued: "\ub300\uae30",
  running: "\uc9c4\ud589 \uc911",
  needs_revision: "\uc218\uc815 \ud544\uc694",
  publishing: "\uac8c\uc2dc \uc911",
  remediating: "\ubcf4\uac15 \uc911",
  continuing_with_issues: "\uc774\uc288 \uc548\uace0 \uc9c4\ud589",
  completed: "\uc644\ub8cc",
  completed_with_unresolved_issues: "\uc870\uac74\ubd80 \uc644\ub8cc",
  completed_markdown_only: "Markdown \uc644\ub8cc",
  failed: "\uc2e4\ud328",
  blocked: "\ucc28\ub2e8",
  cancelled: "\ucde8\uc18c",
  intake: "\uc900\ube44",
  needs_clarification: "\ud655\uc778 \ud544\uc694",
};

const TERMINAL_STATES = new Set(["completed", "completed_with_unresolved_issues", "completed_markdown_only", "failed", "blocked", "cancelled", "needs_clarification"]);

const DISPLAY_LAST_ARTIFACTS = new Set(["01_research.md", "03_analysis.md", "04_draft.md", "05_review.md", "06_revision.md"]);

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
  manager: "사용자의 요청을 읽고 보고서 작업의 기준을 정합니다. 목표, 독자, 범위, 근거 기준, 각 Agent가 해야 할 일을 먼저 정리합니다.",
  researcher: "보고서에 쓸 수 있는 자료를 모으는 담당자입니다. 웹이나 제공된 자료에서 사실, 숫자, 출처, 쟁점, 아직 확인되지 않은 부분을 분리해 정리합니다.",
  evidence_auditor: "Researcher가 모은 자료를 보고 이 근거를 실제 분석에 써도 되는지 판정합니다. 출처가 약하거나 숫자 근거가 불명확하면 제한을 걸거나 제외합니다.",
  analyst: "검증된 근거만 사용해 실제 판단 구조를 만듭니다. 선택지, 평가 기준, 시나리오, 리스크, 추천 논리를 정리합니다.",
  writer: "Analyst가 만든 판단 구조를 읽고 실제 독자가 볼 보고서 초안을 씁니다. 새 근거를 만들지 않고 검증된 내용을 읽기 좋은 문장으로 바꿉니다.",
  reviewer: "보고서 초안이 제대로 작성됐는지 검사합니다. 목표에 맞는지, 근거 없는 주장이 있는지, 숫자와 분석 결론이 추적 가능한지 확인합니다.",
  revision_writer: "Reviewer가 지정한 필수 수정사항만 반영합니다. 전체를 새로 쓰지 않고 지적된 문제를 고친 뒤 수정 이력을 남깁니다.",
  final_verifier: "최종 발행 직전에 보고서 후보를 마지막으로 확인합니다. 필수 수정 반영, 새로 생긴 근거 없는 주장, 빠진 주의 문구가 없는지 봅니다.",
  publisher: "검증이 끝난 보고서 후보를 최종 파일로 포장하는 시스템 단계입니다. 내용을 새로 쓰지 않고 Markdown, Word, 발행 기록을 만듭니다.",
};

const VIEW_DESCRIPTIONS = {
  prompt: "선택한 Agent에게 실제로 입력된 지시문입니다. 실행 맥락, 역할 지침, 이전 단계 산출물, 참고 문서가 함께 들어갑니다.",
  "00_task_contract.json": "프로그램이 다음 단계들을 자동으로 진행하기 위해 읽는 구조화된 작업 지시서입니다. 보고서 목표, 독자, 범위, 근거 기준, 각 Agent가 해야 할 일이 JSON으로 정리됩니다.",
  "00_task_brief.md": "사람이 읽기 쉽게 풀어쓴 작업 지시 설명서입니다. 이후 Agent들이 이번 작업의 목적과 범위를 이해하는 기준 문서입니다.",
  "01_research.md": "조사 결과를 문장으로 정리한 파일입니다. 어떤 사실들이 확인됐는지, 어떤 충돌이나 한계가 있는지 적습니다.",
  "01_sources.md": "사용한 출처 목록입니다. 각 출처에 ID를 붙이고 발행기관, 날짜, 신뢰도, 보고서에 쓸 때의 한계를 적습니다.",
  "01_claims.md": "보고서에 들어갈 수 있는 주장과 그 주장을 뒷받침하는 출처를 연결한 표입니다. 아직 최종 검증 전의 예비 연결 상태를 보여줍니다.",
  "01_gaps.md": "아직 근거가 부족하거나 확인이 어려운 부분을 따로 모은 파일입니다. 후속 조사나 보고서의 주의 문구로 이어질 수 있습니다.",
  "01_numeric_assumptions.md": "보고서에 쓰이는 숫자들을 따로 관리하는 파일입니다. 숫자값, 단위, 기간, 출처, 직접 인용인지 계산값인지 등을 적습니다.",
  "01_source_provenance.md": "각 출처를 어떤 검색어나 경로로 찾았는지 남기는 기록입니다. 나중에 출처 추적과 검증에 사용됩니다.",
  "02_evidence_gate.json": "Researcher가 모은 근거를 실제 분석에 써도 되는지 기계가 읽을 수 있게 판정한 파일입니다. 사용 가능, 주의 문구 필요, 제외, 추가 조사 필요 같은 상태가 들어갑니다.",
  "02_evidence_audit.md": "근거 판정을 사람이 이해할 수 있게 설명한 파일입니다. 어떤 근거는 써도 되고, 어떤 근거는 주의 문구를 붙이거나 제외해야 하는지 정리합니다.",
  "03a_decision_frame.md": "이번 보고서가 풀어야 할 의사결정 질문을 정리한 파일입니다. 비교할 선택지, 평가 기준, 제약조건을 먼저 맞춥니다.",
  "03b_option_evaluation.md": "각 선택지를 같은 기준으로 비교한 표입니다. 평가 내용이 어떤 근거 ID에 기대고 있는지도 함께 보여줍니다.",
  "03c_scenarios_and_recommendation.md": "시나리오별 결과와 추천 방향을 정리한 파일입니다. 추천이 바뀔 수 있는 조건과 주요 리스크도 함께 적습니다.",
  "03_analysis.md": "Writer가 보고서 초안을 쓸 때 바로 참고할 수 있도록 분석 내용을 요약한 파일입니다. 추천 논리, 비교 결과, 반드시 남겨야 할 주의 문구가 들어갑니다.",
  "03_analysis_status.json": "분석이 충분한 근거 위에서 진행됐는지 표시하는 상태 파일입니다. 준비 완료인지, 추가 조사가 필요한지, 차단 사유가 있는지 알려줍니다.",
  "04_draft.md": "독자가 실제로 읽게 될 보고서 초안입니다. 앞 단계에서 검증된 근거와 분석 논리를 바탕으로 작성됩니다.",
  "04_writer_trace.md": "초안 안의 주요 주장들이 어떤 출처, 숫자, 분석 결과에서 왔는지 연결해 둔 추적표입니다. 이 문장이 어디서 나온 말인지 확인할 때 씁니다.",
  "05_review_decision.json": "초안을 승인할지, 일부 수정이 필요한지, 큰 수정이 필요한지 판단한 파일입니다. 수정이 필요하면 R1, R2 같은 수정 항목 ID가 들어갑니다.",
  "05_review.md": "사람이 읽는 검토 의견입니다. 점수, 문제점, 필수 수정사항, 승인 여부가 정리됩니다.",
  "05_claim_audit.md": "보고서 초안의 주요 주장별로 근거가 제대로 연결되어 있는지 확인한 표입니다. 근거 없는 문장이나 추적이 약한 부분을 찾는 데 씁니다.",
  "06_revision.md": "Reviewer가 요구한 필수 수정사항이 반영된 개정 보고서 초안입니다. 새 보고서를 쓰는 것이 아니라 지정된 문제를 고친 결과입니다.",
  "06_revision_trace.md": "각 수정 요청 ID가 실제로 반영됐는지 기록한 파일입니다. 어디가 바뀌었고, 반영하지 못한 항목이 있는지 확인할 수 있습니다.",
  "07_final_verification.json": "최종 발행 가능 여부를 판단한 파일입니다. 발행 가능, 주의사항을 달고 가능, 발행 차단 같은 결과가 들어갑니다.",
  "07_final_verification.md": "최종 검증 결과를 사람이 읽기 쉽게 설명한 파일입니다. 필수 수정 반영, 근거 추적, 주의 문구 보존 여부를 확인합니다.",
  "08_final.md": "검증된 후보를 복사해 만든 최종 Markdown 보고서입니다. 최종본의 기준이 되는 텍스트 파일입니다.",
  "08_evidence_reference.md": "보고서 작성에 사용된 C, N, S ID를 사람이 읽기 쉬운 bullet list로 다시 정리한 참고자료입니다.",
  "08_final_manifest.json": "최종 발행 내역을 기록한 파일입니다. 어떤 후보를 최종본으로 선택했는지, Word 파일 생성 상태와 남은 주의사항은 무엇인지 적습니다.",
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
  const runStatus = formatRunStatus(status, totalUsage, totalDuration);
  const selectedState = roleStateLabel(selectedRole, status, completed);

  elements.workspaceTitle.textContent = task.title;
  elements.statusMessage.textContent = runStatus.text;
  elements.statusMessage.title = runStatus.title;
  elements.statusMessage.dataset.state = status.state || "";
  elements.selectedRole.textContent = formatRoleHeading(selectedRole);
  elements.selectedLabel.textContent = formatRoleDescription(selectedRole);
  elements.selectedTokens.textContent = formatUsageAndDuration(usage, roleDuration);
  elements.selectedTokens.title = formatTokenUsageDetail(usage);
  elements.selectedState.textContent = selectedState;
  elements.selectedState.dataset.state = stateClass(selectedState);

  renderSteps(roles, status, completed);
  renderSubtabs();
}

function renderEmpty() {
  elements.workspaceTitle.textContent = "\ubcf4\uace0\uc11c \uc791\uc5c5\uc744 \uc2dc\uc791\ud558\uc138\uc694";
  elements.statusMessage.textContent = "\ud1a0\ud070 - \u00b7 \uc18c\uc694\uc2dc\uac04 -";
  elements.statusMessage.title = "";
  delete elements.statusMessage.dataset.state;
  elements.stepList.innerHTML = "";
  renderDetail("\uc9c4\ud589 \ub2e8\uacc4\uc5d0\uc11c Agent\ub97c \uc120\ud0dd\ud558\uc138\uc694.");
  elements.selectedRole.textContent = "Manager";
  elements.selectedLabel.textContent = ROLE_DESCRIPTIONS.manager;
  elements.selectedTokens.textContent = "\ud1a0\ud070 - \u00b7 \uc18c\uc694\uc2dc\uac04 -";
  elements.selectedTokens.title = "";
  elements.selectedState.textContent = "\ub300\uae30";
  delete elements.selectedState.dataset.state;
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
  if (isRevisionSkipped(selectedRole)) {
    renderDetail("Reviewer가 승인하여 Revision 단계는 실행되지 않았습니다.");
    return;
  }
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

function isRevisionSkipped(role) {
  return role?.key === "revision_writer" && currentRun?.status?.revision_status?.status === "not_required";
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
  const artifactViews = (role.artifacts || [{ label: role.label, path: role.artifact }]).map((artifact) => ({
    key: artifact.path,
    label: artifact.label,
    path: artifact.path,
  }));
  return [
    ...(role.prompt ? [{ key: "prompt", label: "Prompt", path: role.prompt }] : []),
    ...orderArtifactViewsForDisplay(artifactViews),
  ];
}

function orderArtifactViewsForDisplay(views) {
  const leading = [];
  const trailing = [];
  views.forEach((view) => {
    const target = DISPLAY_LAST_ARTIFACTS.has(pathKeyForView(view)) ? trailing : leading;
    target.push(view);
  });
  return [...leading, ...trailing];
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
  return sumTokenUsage(roleRunsForRole(role).map((run) => run.usage));
}

function agentRunForRole(role) {
  const runs = roleRunsForRole(role);
  return runs[runs.length - 1] || null;
}

function roleRunsForRole(role) {
  return (currentRun?.status.agent_runs || []).filter((item) => (item.key || roleKeyFromArtifact(item.artifact)) === role.key);
}

function totalTokenUsage(status) {
  return sumTokenUsage((status.agent_runs || []).map((run) => run.usage));
}

function sumTokenUsage(usages) {
  const total = {};
  for (const usage of usages || []) {
    for (const [key, value] of Object.entries(usage || {})) {
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

function formatRunStatus(status, usage, durationMs) {
  const usageText = formatUsageAndDuration(usage, durationMs);
  const state = status?.state || "";
  const title = [status?.error || "", formatTokenUsageDetail(usage)].filter(Boolean).join("\n");
  if (state === "completed_with_unresolved_issues") {
    return { text: usageText, title };
  }
  if (["remediating", "continuing_with_issues"].includes(state)) {
    return { text: `${translateState(state)} \u00b7 ${usageText}`, title };
  }
  if (["blocked", "failed", "cancelled", "needs_clarification"].includes(state)) {
    const reason = formatStopReason(status);
    return {
      text: reason ? `${translateState(state)}: ${reason} \u00b7 ${usageText}` : `${translateState(state)} \u00b7 ${usageText}`,
      title,
    };
  }
  if (["running", "publishing"].includes(state)) {
    return { text: `${translateState(state)} \u00b7 ${usageText}`, title };
  }
  return { text: usageText, title };
}

function formatStopReason(status) {
  const error = String(status?.error || "").split(/\r?\n/)[0].trim();
  let match = /^Evidence gate stopped workflow: (.+)$/.exec(error);
  if (match) return `Evidence Gate ${match[1]}`;
  match = /^Analysis gate stopped workflow: (.+)$/.exec(error);
  if (match) return `Analysis Gate ${match[1]}`;
  if (error === "Final Verifier blocked publication.") return "Final Verifier blocked";
  if (error === "Manager requested clarification before research.") return "Manager \ud655\uc778 \ud544\uc694";
  return truncateText(error, 96);
}

function truncateText(value, maxLength) {
  if (!value || value.length <= maxLength) return value;
  return `${value.slice(0, maxLength - 1)}\u2026`;
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
  return role.display_role || role.role;
}

function formatRoleDescription(role) {
  return ROLE_DESCRIPTIONS[role.key] || "\uc774 \ub2e8\uacc4\uc758 \uc0b0\ucd9c\ubb3c\uc744 \uc0dd\uc131\ud569\ub2c8\ub2e4.";
}

function descriptionForView(view) {
  const pathKey = pathKeyForView(view);
  return VIEW_DESCRIPTIONS[pathKey] || VIEW_DESCRIPTIONS[view.key] || "\uc120\ud0dd\ud55c \uc0b0\ucd9c\ubb3c\uc758 \ub0b4\uc6a9\uc744 \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.";
}

function pathKeyForView(view) {
  return (view.path || view.key || "").replace(/^artifacts\//, "").replace(/^prompts\//, "");
}

function durationForRole(role, status, completed) {
  let total = 0;
  let hasDuration = false;
  for (const run of roleRunsForRole(role)) {
    const duration = durationBetween(run.started_at, run.completed_at);
    if (duration !== null) {
      total += duration;
      hasDuration = true;
    }
  }
  if (isCurrentRole(role, status) && status.current_role_started_at) {
    const current = durationBetween(status.current_role_started_at, new Date().toISOString());
    if (current !== null) {
      total += current;
      hasDuration = true;
    }
  }
  if (hasDuration) return total;
  if (completed.has(role.key)) return 0;
  return null;
}

function durationForRun(task, status) {
  let total = 0;
  let hasDuration = false;
  for (const run of status.agent_runs || []) {
    const duration = durationBetween(run.started_at, run.completed_at);
    if (duration !== null) {
      total += duration;
      hasDuration = true;
    }
  }
  if (!TERMINAL_STATES.has(status.state) && status.current_role_started_at) {
    const current = durationBetween(status.current_role_started_at, new Date().toISOString());
    if (current !== null) {
      total += current;
      hasDuration = true;
    }
  }
  return hasDuration ? total : null;
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
  if (status.state === "remediating" && isCurrentRole(role, status)) return "\ubcf4\uac15 \uc911";
  if (status.state === "continuing_with_issues" && isCurrentRole(role, status)) return "\uc774\uc288 \uc548\uace0 \uc9c4\ud589";
  if (status.state === "completed_with_unresolved_issues" && role.key === "publisher" && completed.has(role.key)) return "\uc870\uac74\ubd80 \uc644\ub8cc";
  if (roleHasUnresolvedIssue(role, status)) return "\uc774\uc288 \uc548\uace0 \uc9c4\ud589";
  const terminalState = terminalStateForRole(role, status);
  if (terminalState) return terminalState;
  if (completed.has(role.key)) return "\uc644\ub8cc";
  if (role.key === "revision_writer" && status.revision_status?.status === "not_required") return "\uc218\uc815 \ubd88\ud544\uc694";
  if (status.state === "failed" && isCurrentRole(role, status)) return "\uc2e4\ud328";
  if (["running", "needs_revision", "publishing", "blocked", "needs_clarification"].includes(status.state) && isCurrentRole(role, status)) return translateState(status.state);
  return "\ub300\uae30";
}

function roleHasUnresolvedIssue(role, status) {
  return (status.unresolved_gate_issues || []).some((issue) => issue.source_role === role.key);
}

function terminalStateForRole(role, status) {
  if (!role || !status) return "";
  if (status.state === "failed" && (isCurrentRole(role, status) || status.failed_role === role.key)) return "\uc2e4\ud328";
  if (status.state === "blocked" && role.key === stoppedRoleKey(status)) return "\ucc28\ub2e8";
  if (status.state === "needs_clarification" && role.key === "manager") return "\ud655\uc778 \ud544\uc694";
  return "";
}

function stoppedRoleKey(status) {
  const error = status?.error || "";
  if (error.startsWith("Evidence gate stopped workflow")) return "evidence_auditor";
  if (error.startsWith("Analysis gate stopped workflow")) return "analyst";
  if (error === "Final Verifier blocked publication.") return "final_verifier";
  if (["blocked", "incomplete"].includes(status.evidence_gate?.decision)) return "evidence_auditor";
  if (["blocked", "needs_research"].includes(status.analysis_gate?.decision)) return "analyst";
  if (status.final_gate?.decision === "blocked" || status.final_gate?.block_publish === true) return "final_verifier";
  return status.failed_role || status.current_role || "";
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
    "\ubcf4\uac15 \uc911": "active",
    "\uc774\uc288 \uc548\uace0 \uc9c4\ud589": "warning",
    "\uc870\uac74\ubd80 \uc644\ub8cc": "warning",
    "\uc218\uc815 \ubd88\ud544\uc694": "done",
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
