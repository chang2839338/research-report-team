const STORAGE_KEY = "research-report-team:web-workspace";

const artifacts = {
  "00_task_brief": {
    label: "Task Brief",
    role: "Manager",
    file: "00_task_brief.md",
    template: (state) => `# Task Brief

- Title: ${state.title || "Untitled report"}
- User request: ${state.brief || "TBD"}
- Workflow: web workspace.

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
  "01_research": {
    label: "Research",
    role: "Researcher",
    file: "01_research.md",
    template: () => `# Research

## Key Facts

- TBD Source: TBD

## Source Notes

- TBD

## Uncertainties

- TBD
`,
  },
  "02_analysis": {
    label: "Analysis",
    role: "Analyst",
    file: "02_analysis.md",
    template: () => `# Analysis

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
  "03_draft": {
    label: "Draft",
    role: "Writer",
    file: "03_draft.md",
    template: () => `# Draft

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
  "04_review": {
    label: "Review",
    role: "Reviewer",
    file: "04_review.md",
    template: () => `# Review

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
  "05_final": {
    label: "Final",
    role: "Manager",
    file: "05_final.md",
    template: () => `# Final Report

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
};

const prompts = {
  Manager: `# Manager Prompt

You are the Manager. Clarify intent, define done, split work, inspect outputs, request revisions, and deliver the final report.

Keep artifacts auditable. Use artifacts/00_task_brief.md as the shared context packet.`,
  Researcher: `# Researcher Prompt

Gather source-backed facts, context, examples, and evidence for the task brief.

Separate facts from interpretation. Prefer primary or authoritative sources. Flag weak evidence and source conflicts.`,
  Analyst: `# Analyst Prompt

Compare options, define decision criteria, evaluate tradeoffs, identify implications, and make recommendations.

Show how the recommendation follows from the evidence.`,
  Writer: `# Writer Prompt

Turn approved findings into a clear report for the target reader.

Use direct structure, concise prose, and make caveats visible.`,
  Reviewer: `# Reviewer Prompt

Check goal fit, evidence quality, source traceability, logic, completeness, and format.

Request targeted revisions when material criteria fail.`,
};

const elements = {
  titleInput: document.querySelector("#titleInput"),
  briefInput: document.querySelector("#briefInput"),
  newRunButton: document.querySelector("#newRunButton"),
  exportButton: document.querySelector("#exportButton"),
  workspaceTitle: document.querySelector("#workspaceTitle"),
  currentRole: document.querySelector("#currentRole"),
  savedState: document.querySelector("#savedState"),
  artifactRole: document.querySelector("#artifactRole"),
  artifactTitle: document.querySelector("#artifactTitle"),
  artifactEditor: document.querySelector("#artifactEditor"),
  promptTitle: document.querySelector("#promptTitle"),
  promptText: document.querySelector("#promptText"),
  copyPromptButton: document.querySelector("#copyPromptButton"),
  downloadMarkdownButton: document.querySelector("#downloadMarkdownButton"),
  tabs: [...document.querySelectorAll(".tab")],
};

let activeArtifact = "00_task_brief";
let state = loadState();

function createState(title = "", brief = "") {
  const base = {
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    title,
    brief,
    activeArtifact,
    contents: {},
  };

  Object.entries(artifacts).forEach(([key, artifact]) => {
    base.contents[key] = artifact.template(base);
  });

  return base;
}

function loadState() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) {
    return createState("Untitled report", "");
  }

  try {
    const parsed = JSON.parse(saved);
    Object.keys(artifacts).forEach((key) => {
      if (!parsed.contents?.[key]) {
        parsed.contents[key] = artifacts[key].template(parsed);
      }
    });
    activeArtifact = parsed.activeArtifact || activeArtifact;
    return parsed;
  } catch {
    return createState("Untitled report", "");
  }
}

function saveState() {
  state.updatedAt = new Date().toISOString();
  state.activeArtifact = activeArtifact;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  elements.savedState.textContent = "Saved locally";
}

function render() {
  const artifact = artifacts[activeArtifact];
  elements.titleInput.value = state.title;
  elements.briefInput.value = state.brief;
  elements.workspaceTitle.textContent = state.title || "Untitled report";
  elements.currentRole.textContent = artifact.role;
  elements.artifactRole.textContent = artifact.role;
  elements.artifactTitle.textContent = artifact.label;
  elements.artifactEditor.value = state.contents[activeArtifact];
  elements.promptTitle.textContent = artifact.role;
  elements.promptText.textContent = prompts[artifact.role];

  elements.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.artifact === activeArtifact);
  });
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

elements.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    state.contents[activeArtifact] = elements.artifactEditor.value;
    activeArtifact = tab.dataset.artifact;
    saveState();
    render();
  });
});

elements.titleInput.addEventListener("input", () => {
  state.title = elements.titleInput.value;
  saveState();
  render();
});

elements.briefInput.addEventListener("input", () => {
  state.brief = elements.briefInput.value;
  saveState();
});

elements.artifactEditor.addEventListener("input", () => {
  state.contents[activeArtifact] = elements.artifactEditor.value;
  elements.savedState.textContent = "Saving...";
  saveState();
});

elements.newRunButton.addEventListener("click", () => {
  activeArtifact = "00_task_brief";
  state = createState(elements.titleInput.value || "Untitled report", elements.briefInput.value);
  saveState();
  render();
});

elements.exportButton.addEventListener("click", () => {
  state.contents[activeArtifact] = elements.artifactEditor.value;
  saveState();
  downloadFile(
    `${slugify(state.title)}-workspace.json`,
    JSON.stringify(state, null, 2),
    "application/json"
  );
});

elements.downloadMarkdownButton.addEventListener("click", () => {
  state.contents[activeArtifact] = elements.artifactEditor.value;
  saveState();
  downloadFile(artifacts[activeArtifact].file, state.contents[activeArtifact], "text/markdown");
});

elements.copyPromptButton.addEventListener("click", async () => {
  const artifact = artifacts[activeArtifact];
  await navigator.clipboard.writeText(prompts[artifact.role]);
  elements.copyPromptButton.textContent = "복사됨";
  setTimeout(() => {
    elements.copyPromptButton.textContent = "복사";
  }, 1200);
});

function slugify(value) {
  return (value || "research-report")
    .toLowerCase()
    .replace(/[^a-z0-9가-힣]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

render();
