const elements = {
  runForm: document.querySelector("#runForm"),
  titleInput: document.querySelector("#titleInput"),
  briefInput: document.querySelector("#briefInput"),
  runButton: document.querySelector("#runButton"),
  runList: document.querySelector("#runList"),
  workspaceTitle: document.querySelector("#workspaceTitle"),
  statusMessage: document.querySelector("#statusMessage"),
  stepList: document.querySelector("#stepList"),
  finalState: document.querySelector("#finalState"),
  finalViewer: document.querySelector("#finalViewer"),
  selectedRole: document.querySelector("#selectedRole"),
  selectedLabel: document.querySelector("#selectedLabel"),
  selectedState: document.querySelector("#selectedState"),
  detailViewer: document.querySelector("#detailViewer"),
  subtabs: [...document.querySelectorAll(".subtab")],
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
  elements.runButton.querySelector("span:last-child").textContent = isRunning ? "실행 중..." : "보고서 작업 실행";
}

function render() {
  if (!currentRun) {
    renderEmpty();
    return;
  }

  const { task, status, roles } = currentRun;
  const selectedRole = findSelectedRole();
  const completed = completedRoleKeys(status);

  elements.workspaceTitle.textContent = task.title;
  elements.statusMessage.textContent = status.error || buildStatusMessage(status);
  elements.selectedRole.textContent = selectedRole.display_role || selectedRole.role;
  elements.selectedLabel.textContent = selectedRole.label;
  elements.selectedState.textContent = roleStateLabel(selectedRole, status, completed);
  elements.finalState.textContent = currentRun.files["artifacts/05_final.md"] ? "완료" : "대기";

  renderSteps(roles, status, completed);
  renderSubtabs();
}

function renderEmpty() {
  elements.workspaceTitle.textContent = "보고서 작업을 시작하세요";
  elements.statusMessage.textContent = "제목과 내용을 입력한 뒤 실행하세요.";
  elements.stepList.innerHTML = "";
  elements.detailViewer.textContent = "진행 단계에서 Agent를 선택하세요.";
  elements.finalViewer.textContent = "아직 최종 보고서가 없습니다.";
  elements.selectedState.textContent = "대기";
  elements.finalState.textContent = "대기";
}

function renderRunList(runs) {
  if (!runs.length) {
    elements.runList.innerHTML = `<p class="empty-note">아직 저장된 작업이 없습니다.</p>`;
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
        <strong>${role.display_role || role.role}</strong>
        <small>${state}</small>
      </span>
    `;
    button.addEventListener("click", async () => {
      selectedRoleKey = role.key;
      render();
      await loadVisibleFiles();
    });
    elements.stepList.appendChild(button);
  });
}

function renderSubtabs() {
  elements.subtabs.forEach((button) => {
    button.classList.toggle("active", button.dataset.view === selectedView);
  });
}

async function loadVisibleFiles() {
  if (!currentRun) return;
  const selectedRole = findSelectedRole();
  const path = selectedRole[selectedView];
  const [detail, final] = await Promise.all([
    readRunFile(path),
    readRunFile("artifacts/05_final.md"),
  ]);

  elements.detailViewer.textContent = detail || `${selectedViewLabel(selectedView)} 파일이 아직 생성되지 않았습니다.`;
  elements.finalViewer.textContent = final || "아직 최종 보고서가 없습니다.";
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

function completedRoleKeys(status) {
  return new Set((status.agent_runs || []).map((run) => run.key || roleKeyFromArtifact(run.artifact)));
}

function roleKeyFromArtifact(path) {
  const role = currentRun?.roles.find((item) => item.artifact === path);
  return role?.key || "";
}

function roleStateLabel(role, status, completed) {
  if (completed.has(role.key)) return "완료";
  if (status.state === "failed" && isCurrentRole(role, status)) return "실패";
  if (status.state === "running" && isCurrentRole(role, status)) return "진행중";
  return "대기";
}

function isCurrentRole(role, status) {
  return status.current_role === role.key || status.current_role === role.role || status.current_role === role.display_role;
}

function stateClass(state) {
  return {
    완료: "done",
    진행중: "active",
    실패: "failed",
  }[state] || "";
}

function buildStatusMessage(status) {
  if (status.state === "completed") return "완료";
  if (status.state === "failed") return "실패";
  if (status.state === "running") return "진행중";
  if (status.state === "queued") return "대기";
  return "대기";
}

function translateState(state) {
  return {
    queued: "대기",
    running: "진행중",
    completed: "완료",
    failed: "실패",
  }[state] || "대기";
}

function selectedViewLabel(view) {
  return {
    prompt: "prompt 발송",
    artifact: "AI 회신",
  }[view] || "파일";
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

elements.subtabs.forEach((button) => {
  button.addEventListener("click", async () => {
    selectedView = button.dataset.view;
    renderSubtabs();
    await loadVisibleFiles();
  });
});

loadRuns().catch((error) => {
  elements.statusMessage.textContent = `서버 연결 실패: ${error.message}`;
});
