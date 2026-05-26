const STORAGE_KEY = "research-report-team:web-workspace";

const stages = [
  {
    key: "00_task_brief",
    label: "Task Brief",
    role: "Manager",
    file: "00_task_brief.md",
    goal: "사용자의 보고서 요청을 의사결정 가능한 작업 브리프로 정리한다.",
    summary: "보고서 목표, 독자, 범위, 완료 기준을 정리하는 시작 단계입니다.",
    inputs: [],
    output: `# Task Brief

- Title: {{title}}
- User request: {{brief}}
- Workflow: Codex Pro semi-automated workspace.

## Decision Goal

TBD

## Target Reader

TBD

## Scope

TBD

## Acceptance Criteria

- Clarify decision goal and target reader.
- Use source-backed evidence for factual claims.
- Compare options against explicit criteria.
- Deliver a decision-ready final report.
`,
  },
  {
    key: "01_research",
    label: "Research",
    role: "Researcher",
    file: "01_research.md",
    goal: "작업 브리프에 필요한 사실, 맥락, 예시, 출처를 조사한다.",
    summary: "Task Brief를 바탕으로 출처가 있는 조사 결과를 축적합니다.",
    inputs: ["00_task_brief"],
    output: `# Research

## Key Facts

- TBD Source: TBD

## Source Notes

- TBD

## Uncertainties

- TBD
`,
  },
  {
    key: "02_analysis",
    label: "Analysis",
    role: "Analyst",
    file: "02_analysis.md",
    goal: "조사 결과를 기준으로 선택지, 판단 기준, 리스크, 추천안을 도출한다.",
    summary: "조사 결과를 해석해 추천의 근거와 한계를 정리합니다.",
    inputs: ["00_task_brief", "01_research"],
    output: `# Analysis

## Decision Criteria

- TBD

## Options

| Option | Strengths | Risks | Notes |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

## Recommendation

TBD
`,
  },
  {
    key: "03_draft",
    label: "Draft",
    role: "Writer",
    file: "03_draft.md",
    goal: "브리프, 조사, 분석을 바탕으로 보고서 초안을 작성한다.",
    summary: "의사결정자가 읽기 쉬운 보고서 초안을 만듭니다.",
    inputs: ["00_task_brief", "01_research", "02_analysis"],
    output: `# Draft

## Executive Summary

TBD

## Recommendation

TBD

## Evidence

TBD

## Caveats

TBD
`,
  },
  {
    key: "04_review",
    label: "Review",
    role: "Reviewer",
    file: "04_review.md",
    goal: "초안이 목표, 근거, 논리, 형식 기준을 충족하는지 검토한다.",
    summary: "초안을 검토하고 필요한 수정 요청을 명확히 남깁니다.",
    inputs: ["00_task_brief", "01_research", "02_analysis", "03_draft"],
    output: `# Review

## Verdict

TBD

## Rubric Notes

- Goal fit: TBD
- Evidence quality: TBD
- Logic: TBD
- Completeness: TBD
- Format: TBD

## Revision Requests

- TBD
`,
  },
  {
    key: "05_final",
    label: "Final",
    role: "Manager",
    file: "05_final.md",
    goal: "검토 결과를 반영해 최종 보고서를 완성한다.",
    summary: "검토 메모를 반영한 최종 Markdown 보고서를 만듭니다.",
    inputs: ["00_task_brief", "01_research", "02_analysis", "03_draft", "04_review"],
    output: `# Final Report

## Executive Summary

TBD

## Recommendation

TBD

## Key Evidence

TBD

## Caveats

TBD

## Next Actions

TBD
`,
  },
];

const prompts = {
  Manager: `# Manager Prompt

You are the Manager. Clarify intent, define done, split work, inspect outputs, request revisions, and deliver the final report.

Keep artifacts auditable. Use artifacts/00_task_brief.md as the shared context packet.`,
  Researcher: `# Researcher Prompt

You are the Researcher. Gather source-backed facts, context, examples, and evidence for the task brief.

Separate facts from interpretation. Prefer primary or authoritative sources when available. Flag weak evidence and source conflicts.`,
  Analyst: `# Analyst Prompt

You are the Analyst. Compare options, define decision criteria, evaluate tradeoffs, identify implications, and make recommendations.

Show how the recommendation follows from the evidence. Make assumptions and risks visible.`,
  Writer: `# Writer Prompt

You are the Writer. Turn approved findings into a clear report for the target reader.

Use direct structure, concise prose, and make caveats visible.`,
  Reviewer: `# Reviewer Prompt

You are the Reviewer. Check goal fit, evidence quality, source traceability, logic, completeness, and format.

Request targeted revisions when material criteria fail.`,
};

const elements = {
  titleInput: document.querySelector("#titleInput"),
  briefInput: document.querySelector("#briefInput"),
  newRunButton: document.querySelector("#newRunButton"),
  exportButton: document.querySelector("#exportButton"),
  stepList: document.querySelector("#stepList"),
  workspaceTitle: document.querySelector("#workspaceTitle"),
  currentRole: document.querySelector("#currentRole"),
  savedState: document.querySelector("#savedState"),
  stepHeadline: document.querySelector("#stepHeadline"),
  stepSummary: document.querySelector("#stepSummary"),
  copyCodexButton: document.querySelector("#copyCodexButton"),
  nextStageButton: document.querySelector("#nextStageButton"),
  downloadMarkdownButton: document.querySelector("#downloadMarkdownButton"),
  artifactRole: document.querySelector("#artifactRole"),
  artifactTitle: document.querySelector("#artifactTitle"),
  artifactState: document.querySelector("#artifactState"),
  artifactEditor: document.querySelector("#artifactEditor"),
  packetTitle: document.querySelector("#packetTitle"),
  requirementList: document.querySelector("#requirementList"),
  packetText: document.querySelector("#packetText"),
  copyPacketSmallButton: document.querySelector("#copyPacketSmallButton"),
  resultInput: document.querySelector("#resultInput"),
  applyResultButton: document.querySelector("#applyResultButton"),
  nextStepHint: document.querySelector("#nextStepHint"),
  tabs: [...document.querySelectorAll(".tab")],
};

let activeStageKey = "00_task_brief";
let state = loadState();

function createState(title = "", brief = "") {
  const base = {
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    title,
    brief,
    activeStageKey,
    contents: {},
  };

  stages.forEach((stage) => {
    base.contents[stage.key] = hydrateTemplate(stage.output, base);
  });

  return base;
}

function loadState() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) return createState("Untitled report", "");

  try {
    const parsed = JSON.parse(saved);
    parsed.contents = parsed.contents || {};
    stages.forEach((stage) => {
      if (!parsed.contents[stage.key]) {
        parsed.contents[stage.key] = hydrateTemplate(stage.output, parsed);
      }
    });
    activeStageKey = parsed.activeStageKey || parsed.activeArtifact || activeStageKey;
    return parsed;
  } catch {
    return createState("Untitled report", "");
  }
}

function hydrateTemplate(template, workspace) {
  return template
    .replaceAll("{{title}}", workspace.title || "Untitled report")
    .replaceAll("{{brief}}", workspace.brief || "TBD");
}

function saveState() {
  state.updatedAt = new Date().toISOString();
  state.activeStageKey = activeStageKey;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  elements.savedState.textContent = "로컬 저장됨";
}

function getStage(key = activeStageKey) {
  return stages.find((stage) => stage.key === key) || stages[0];
}

function hasMeaningfulContent(key) {
  const stage = getStage(key);
  const content = (state.contents[key] || "").trim();
  const template = hydrateTemplate(stage.output, state).trim();
  return content.length > 0 && content !== template && !onlyTbdContent(content);
}

function onlyTbdContent(content) {
  const body = content
    .replace(/^#+\s.*$/gm, "")
    .replace(/[-|:\s]/g, "")
    .replace(/TBD/gi, "")
    .trim();
  return body.length === 0;
}

function getMissingInputs(stage) {
  return stage.inputs.filter((key) => !hasMeaningfulContent(key));
}

function getStageStatus(stage) {
  if (hasMeaningfulContent(stage.key)) return "완료";
  if (stage.key === activeStageKey) return "진행 중";
  if (getMissingInputs(stage).length === 0) return "준비됨";
  return "대기";
}

function render() {
  const stage = getStage();
  const missingInputs = getMissingInputs(stage);
  const packet = buildCodexPrompt(stage, state);

  elements.titleInput.value = state.title;
  elements.briefInput.value = state.brief;
  elements.workspaceTitle.textContent = state.title || "Untitled report";
  elements.currentRole.textContent = stage.role;
  elements.stepHeadline.textContent = `${stage.label} · ${stage.role}`;
  elements.stepSummary.textContent = stage.summary;
  elements.artifactRole.textContent = stage.role;
  elements.artifactTitle.textContent = stage.label;
  elements.artifactEditor.value = state.contents[stage.key] || "";
  elements.artifactState.textContent = getStageStatus(stage);
  elements.packetTitle.textContent = `${stage.role} 실행 지시`;
  elements.packetText.value = packet;
  elements.applyResultButton.disabled = false;
  elements.nextStageButton.disabled = !canMoveToNext(stage);
  elements.nextStageButton.textContent = getNextStageButtonLabel(stage);
  elements.nextStepHint.textContent = buildNextStepHint(stage);

  renderTabs();
  renderSteps();
  renderRequirements(stage, missingInputs);
}

function renderTabs() {
  elements.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.artifact === activeStageKey);
  });
}

function renderSteps() {
  elements.stepList.innerHTML = "";
  stages.forEach((stage, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `step-item ${stage.key === activeStageKey ? "active" : ""}`;
    button.dataset.stage = stage.key;
    button.innerHTML = `
      <span class="step-number">${index + 1}</span>
      <span>
        <strong>${stage.label}</strong>
        <small>${stage.role} · ${getStageStatus(stage)}</small>
      </span>
    `;
    button.addEventListener("click", () => switchStage(stage.key));

    const item = document.createElement("li");
    item.appendChild(button);
    elements.stepList.appendChild(item);
  });
}

function renderRequirements(stage, missingInputs) {
  if (stage.inputs.length === 0) {
    elements.requirementList.innerHTML = `<p class="ready-note">필요한 이전 산출물이 없습니다. 바로 Codex Pro에 복사할 수 있습니다.</p>`;
    return;
  }

  const items = stage.inputs
    .map((key) => {
      const inputStage = getStage(key);
      const ready = !missingInputs.includes(key);
      return `<li class="${ready ? "ready" : "missing"}">${inputStage.file} · ${ready ? "준비됨" : "비어 있음"}</li>`;
    })
    .join("");
  elements.requirementList.innerHTML = `<p class="requirement-title">입력 요구사항</p><ul>${items}</ul>`;
}

function switchStage(key) {
  state.contents[activeStageKey] = elements.artifactEditor.value;
  activeStageKey = key;
  elements.resultInput.value = "";
  saveState();
  render();
}

function buildCodexPrompt(stage, workspace) {
  const missingInputs = getMissingInputs(stage);
  const inputContext = stage.inputs
    .map((key) => {
      const inputStage = getStage(key);
      return `## ${inputStage.file}\n\n${workspace.contents[key] || "(비어 있음)"}`;
    })
    .join("\n\n---\n\n");

  const warning =
    missingInputs.length > 0
      ? `\n\n주의: 다음 입력 산출물이 아직 비어 있습니다: ${missingInputs.map((key) => getStage(key).file).join(", ")}. 가능하면 먼저 해당 단계를 채우고 진행하세요.`
      : "";

  return `# Codex Pro 실행 패킷

## 역할

${prompts[stage.role]}

## 목표

${stage.goal}

## 입력 컨텍스트

- 보고서 제목: ${workspace.title || "Untitled report"}
- 사용자 요청 브리프: ${workspace.brief || "TBD"}
- 현재 단계: ${stage.label}
- 출력 파일명: artifacts/${stage.file}${warning}

${inputContext || "이 단계는 이전 artifact 없이 사용자 제목과 요청 브리프만 사용합니다."}

## 출력 형식

- Markdown만 출력하세요.
- 파일명 \`artifacts/${stage.file}\`에 들어갈 본문만 작성하세요.
- 불필요한 설명, 실행 로그, 코드블록 wrapper는 붙이지 마세요.

## 완료 기준

- 사용자의 실제 보고서 목적에 직접 답합니다.
- 사실, 해석, 가정을 구분합니다.
- 현재 정보나 외부 사실이 필요한 경우 출처를 남깁니다.
- 다음 역할이 바로 이어서 사용할 수 있을 만큼 구조화합니다.
`;
}

function buildNextStepHint(stage) {
  const currentIndex = stages.findIndex((item) => item.key === stage.key);
  if (!hasMeaningfulContent(stage.key)) {
    return "Codex Pro 결과를 붙여넣고 Artifact에 반영하면 다음 단계로 이어갈 수 있습니다.";
  }
  if (currentIndex === stages.length - 1) {
    return "최종 보고서가 준비되었습니다. Markdown 또는 JSON으로 내보낼 수 있습니다.";
  }
  return `다음 단계 준비됨: ${stages[currentIndex + 1].label}`;
}

function canMoveToNext(stage) {
  const currentIndex = stages.findIndex((item) => item.key === stage.key);
  return currentIndex < stages.length - 1 && hasMeaningfulContent(stage.key);
}

function getNextStageButtonLabel(stage) {
  const currentIndex = stages.findIndex((item) => item.key === stage.key);
  if (currentIndex === stages.length - 1) return "최종 단계";
  return `다음: ${stages[currentIndex + 1].label}`;
}

async function copyText(text, button) {
  await navigator.clipboard.writeText(text);
  const previous = button.textContent;
  button.textContent = "복사됨";
  setTimeout(() => {
    button.textContent = previous;
  }, 1200);
}

function downloadFile(filename, content, type = "text/plain") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function exportWorkspace() {
  const artifactMap = {};
  const promptMap = {};

  stages.forEach((stage) => {
    artifactMap[`artifacts/${stage.file}`] = state.contents[stage.key] || "";
    promptMap[stage.role.toLowerCase()] = prompts[stage.role];
  });

  const payload = {
    task: {
      created_at: state.createdAt,
      updated_at: state.updatedAt,
      title: state.title,
      brief: state.brief,
      workflow: "codex-pro-semi-automated-web-workspace",
      api_calls: false,
      roles: [...new Set(stages.map((stage) => stage.role))],
    },
    status: {
      active_stage: activeStageKey,
      completed_stages: stages.filter((stage) => hasMeaningfulContent(stage.key)).map((stage) => stage.key),
      next_step: buildNextStepHint(getStage()),
    },
    artifacts: artifactMap,
    prompts: promptMap,
  };

  downloadFile(`${slugify(state.title)}-workspace.json`, JSON.stringify(payload, null, 2), "application/json");
}

elements.tabs.forEach((tab) => {
  tab.addEventListener("click", () => switchStage(tab.dataset.artifact));
});

elements.titleInput.addEventListener("input", () => {
  state.title = elements.titleInput.value;
  saveState();
  render();
});

elements.briefInput.addEventListener("input", () => {
  state.brief = elements.briefInput.value;
  saveState();
  render();
});

elements.artifactEditor.addEventListener("input", () => {
  state.contents[activeStageKey] = elements.artifactEditor.value;
  elements.savedState.textContent = "저장 중...";
  saveState();
  renderSteps();
  elements.artifactState.textContent = getStageStatus(getStage());
  elements.nextStageButton.disabled = !canMoveToNext(getStage());
  elements.nextStageButton.textContent = getNextStageButtonLabel(getStage());
  elements.nextStepHint.textContent = buildNextStepHint(getStage());
});

elements.newRunButton.addEventListener("click", () => {
  activeStageKey = "00_task_brief";
  state = createState(elements.titleInput.value || "Untitled report", elements.briefInput.value);
  elements.resultInput.value = "";
  saveState();
  render();
});

elements.exportButton.addEventListener("click", () => {
  state.contents[activeStageKey] = elements.artifactEditor.value;
  saveState();
  exportWorkspace();
});

elements.copyCodexButton.addEventListener("click", () => copyText(elements.packetText.value, elements.copyCodexButton));
elements.copyPacketSmallButton.addEventListener("click", () => copyText(elements.packetText.value, elements.copyPacketSmallButton));

elements.nextStageButton.addEventListener("click", () => {
  const currentIndex = stages.findIndex((stage) => stage.key === activeStageKey);
  if (currentIndex >= 0 && currentIndex < stages.length - 1 && hasMeaningfulContent(activeStageKey)) {
    switchStage(stages[currentIndex + 1].key);
  }
});

elements.downloadMarkdownButton.addEventListener("click", () => {
  const stage = getStage();
  state.contents[stage.key] = elements.artifactEditor.value;
  saveState();
  downloadFile(stage.file, state.contents[stage.key], "text/markdown");
});

elements.applyResultButton.addEventListener("click", () => {
  const pasted = elements.resultInput.value.trim();
  if (!pasted) {
    elements.nextStepHint.textContent = "붙여넣은 Codex 결과가 없습니다.";
    return;
  }
  state.contents[activeStageKey] = pasted;
  elements.artifactEditor.value = pasted;
  elements.resultInput.value = "";
  saveState();
  render();
});

function slugify(value) {
  return (value || "research-report")
    .toLowerCase()
    .replace(/[^a-z0-9가-힣]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

render();
