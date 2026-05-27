const STATUS = {
  queued: "대기",
  running: "진행 중",
  completed: "완료",
  failed: "실패",
};

const BASE_VIEWS = [
  { key: "prompt", label: "프롬프트" },
  { key: "artifact", label: "AI 응답" },
];

const RESEARCH_VIEWS = [
  { key: "prompt", label: "프롬프트" },
  { key: "artifact", label: "연구 메모" },
  { key: "sources", label: "출처" },
  { key: "claims", label: "주장 검증" },
  { key: "gaps", label: "공백/리스크" },
];

const VIEW_LABEL = {
  prompt: "프롬프트",
  artifact: "AI 응답",
  sources: "출처",
  claims: "주장 검증",
  gaps: "공백/리스크",
};

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
  if (!currentRun.roles.some((role) => role.key === selectedRoleKey)) selectedRoleKey = "manager";
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
      body: JSON.stringify({ title, brief }),
    });
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
  elements.runButton.querySelector("span:last-child").textContent = isRunning ? "실행 중..." : "작업 실행";
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

  elements.workspaceTitle.textContent = task.title;
  elements.statusMessage.textContent = status.error ? "실패" : translateState(status.state);
  elements.selectedRole.textContent = selectedRole.display_role || selectedRole.role;
  elements.selectedLabel.textContent = selectedRole.label;
  elements.selectedTokens.textContent = formatTokenUsage(usage);
  elements.selectedTokens.title = formatTokenUsageDetail(usage);
  elements.selectedState.textContent = roleStateLabel(selectedRole, status, completed);

  renderSteps(roles, status, completed);
  renderSubtabs();
}

function renderEmpty() {
  elements.workspaceTitle.textContent = "보고서 작업을 시작하세요";
  elements.statusMessage.textContent = "대기";
  elements.stepList.innerHTML = "";
  renderDetail("진행 단계에서 Agent를 선택하세요.");
  elements.selectedTokens.textContent = "토큰 -";
  elements.selectedTokens.title = "";
  elements.selectedState.textContent = "대기";
  renderSubtabs();
}

function renderRunList(runs) {
  if (!runs.length) {
    elements.runList.innerHTML = `<p class="empty-note">저장된 작업이 없습니다.</p>`;
    return;
  }

  elements.runList.innerHTML = "";
  runs.forEach((run) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `run-item ${run.id === currentRunId ? "active" : ""}`;
    button.innerHTML = `
      <strong>${escapeHtml(run.task.title)}</strong>
      <small>${run.id} · ${translateState(run.status.state)}</small>
    `;
    button.addEventListener("click", () => loadRun(run.id));
    elements.runList.appendChild(button);
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
  elements.subtabs.style.setProperty("--tab-count", String(views.length));

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
}

async function loadVisibleFiles() {
  if (!currentRun) return;
  const selectedRole = findSelectedRole();
  const path = pathForView(selectedRole, selectedView);
  const detail = await readRunFile(path);
  const visibleDetail = selectedView === "prompt" ? summarizePromptInputs(detail) : detail;
  renderDetail(visibleDetail || `${VIEW_LABEL[selectedView] || "파일"} 파일이 아직 생성되지 않았습니다.`);
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
      output.push("(이전 Agent 응답 본문은 화면 표시에서 생략했습니다.)");
      skipInputBody = true;
      continue;
    }

    if (skipInputBody && isPromptSectionHeading(line)) {
      skipInputBody = false;
    }

    if (!skipInputBody) output.push(line);
  }

  return output.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

function isPromptSectionHeading(line) {
  return /^# (Reference:|Final Report Instruction|Role Prompt|Run Context)/.test(line);
}

function readRunFile(path) {
  if (!currentRunId || !path) return "";
  return apiText(`/api/runs/${encodeURIComponent(currentRunId)}/files?path=${encodeURIComponent(path)}`);
}

function schedulePolling() {
  if (pollTimer) clearInterval(pollTimer);
  if (!currentRun || ["completed", "failed"].includes(currentRun.status.state)) return;

  pollTimer = setInterval(async () => {
    if (!currentRunId) return;
    currentRun = await apiJson(`/api/runs/${encodeURIComponent(currentRunId)}`);
    ensureSelectedView();
    render();
    await loadVisibleFiles();
    if (["completed", "failed"].includes(currentRun.status.state)) {
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
  return role?.key === "researcher" ? RESEARCH_VIEWS : BASE_VIEWS;
}

function ensureSelectedView() {
  const views = viewsForRole(currentRun ? findSelectedRole() : null);
  if (!views.some((view) => view.key === selectedView)) {
    selectedView = views[0].key;
  }
}

function pathForView(role, view) {
  if (view === "prompt") return role.prompt;
  if (view === "artifact") return role.artifact;
  const extra = role.extra_artifacts || [];
  return {
    sources: extra.find((path) => path.endsWith("01_sources.md")),
    claims: extra.find((path) => path.endsWith("01_claims.md")),
    gaps: extra.find((path) => path.endsWith("01_gaps.md")),
  }[view] || "";
}

function completedRoleKeys(status) {
  return new Set((status.agent_runs || []).map((run) => run.key || roleKeyFromArtifact(run.artifact)));
}

function roleKeyFromArtifact(path) {
  const role = currentRun?.roles.find((item) => item.artifact === path);
  return role?.key || "";
}

function tokenUsageForRole(role) {
  const run = (currentRun?.status.agent_runs || []).find(
    (item) => (item.key || roleKeyFromArtifact(item.artifact)) === role.key,
  );
  return run?.usage || null;
}

function tokenTotal(usage) {
  if (!usage) return 0;
  return Number(usage.input_tokens || 0) + Number(usage.output_tokens || 0);
}

function formatTokenUsage(usage) {
  if (!usage) return "토큰 -";
  return `토큰 ${formatNumber(tokenTotal(usage))} · 입력 ${formatNumber(usage.input_tokens)} · 출력 ${formatNumber(usage.output_tokens)}`;
}

function formatTokenUsageDetail(usage) {
  if (!usage) return "아직 토큰 사용량이 없습니다.";
  const parts = [
    `총 ${formatNumber(tokenTotal(usage))}`,
    `입력 ${formatNumber(usage.input_tokens)}`,
    `출력 ${formatNumber(usage.output_tokens)}`,
  ];
  if (usage.cached_input_tokens) parts.push(`캐시 ${formatNumber(usage.cached_input_tokens)}`);
  if (usage.reasoning_output_tokens) parts.push(`추론 ${formatNumber(usage.reasoning_output_tokens)}`);
  return parts.join(" · ");
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("ko-KR");
}

function roleStateLabel(role, status, completed) {
  if (completed.has(role.key)) return "완료";
  if (status.state === "failed" && isCurrentRole(role, status)) return "실패";
  if (status.state === "running" && isCurrentRole(role, status)) return "진행 중";
  return "대기";
}

function isCurrentRole(role, status) {
  return status.current_role === role.key || status.current_role === role.role || status.current_role === role.display_role;
}

function stateClass(state) {
  return {
    완료: "done",
    "진행 중": "active",
    실패: "failed",
  }[state] || "";
}

function translateState(state) {
  return STATUS[state] || "대기";
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
    elements.statusMessage.textContent = "보고서 내용을 입력해야 실행할 수 있습니다.";
    return;
  }
  try {
    await createRun(title, brief);
  } catch (error) {
    elements.statusMessage.textContent = error.message;
  }
});

loadRuns().catch((error) => {
  elements.statusMessage.textContent = `서버 연결 실패: ${error.message}`;
});
