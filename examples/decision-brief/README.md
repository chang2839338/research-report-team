# Example: Decision Brief

This example shows how to use `research-report-team` to choose between two operating models.

## User Request

```text
research-report-team 스킬을 사용해줘.

AI agent 팀을 지금 웹앱으로 만들지, 아니면 ChatGPT Pro 기반 PC skill workflow로 먼저 운영할지 의사결정 보고서를 작성해줘.
비용, 구현 난이도, 자동화 가치, 향후 확장성을 기준으로 비교해줘.
```

## Manager Task Brief

- Decision goal: choose the near-term operating model for the research-report-team project.
- Target reader: project owner.
- Output format: decision brief.
- Scope: ChatGPT Pro skill workflow, API/agent runner/web app option, cost and complexity.
- Exclusions: building the web app now, calling paid APIs now.
- Acceptance criteria:
  - Compare both options.
  - Recommend a near-term path.
  - Explain when to revisit API/web app work.

## Role Plan

- Researcher: collect evidence about cost separation, workflow constraints, and installation needs.
- Analyst: compare options by cost, complexity, automation value, and extensibility.
- Writer: draft a Korean decision brief.
- Reviewer: check whether the recommendation is supported and action-ready.

## Sample Final Report

# AI Agent Team 운영 방식 의사결정 브리프

## Executive Summary

현재 단계에서는 웹앱이나 API 기반 자동화보다 **ChatGPT Pro 기반 PC skill workflow**를 우선하는 것이 적합하다. 이유는 추가 API 비용 없이 바로 실험할 수 있고, 아직 역할/프롬프트/보고서 품질 기준을 검증하는 단계이기 때문이다. 웹앱은 반복 사용 패턴과 자동화 필요성이 충분히 확인된 뒤 다시 검토하는 것이 좋다.

## Decision To Make

`research-report-team`을 지금 웹앱/API 기반 시스템으로 발전시킬지, 아니면 먼저 ChatGPT Pro와 Codex Skill 중심으로 운영할지 결정해야 한다.

## Recommendation

단기적으로는 **ChatGPT Pro + Codex Skill + 로컬 CLI 정리 도구** 조합을 선택한다.

## Options Compared

| Option | Strengths | Weaknesses | Best Fit | Key Risk |
| --- | --- | --- | --- | --- |
| ChatGPT Pro skill workflow | 추가 API 비용 없음, 빠른 실험, 쉬운 수정 | 완전 자동화 아님, 수동 복사/정리 필요 | MVP, workflow 검증 | 장기적으로 반복 업무가 많아지면 비효율 |
| API/agent runner/web app | 자동화, 상태 추적, 모바일 접근 가능 | API 비용, 개발 복잡도, 운영 부담 | 제품화/반복 업무 | 너무 일찍 만들면 과설계 |

## Evidence

- ChatGPT Pro 구독과 API 사용량은 별도 과금 체계로 운영된다.
- 현재 repo는 Skill, 역할 정의, workflow, CLI 초안을 이미 갖추고 있다.
- 독립 agent runner와 web app은 역할 계약과 산출물 구조가 안정된 뒤 만드는 편이 안전하다.

## Risks And Caveats

- ChatGPT Pro workflow는 사용자가 직접 채팅을 시작하고 결과를 저장해야 한다.
- 여러 사용자가 동시에 쓰거나 모바일 접근이 중요해지면 web app 필요성이 커질 수 있다.
- 반복 업무가 늘어나면 API 비용보다 자동화 가치가 더 커질 수 있다.

## Next Actions

1. ChatGPT Pro 사용/설치 가이드를 정리한다.
2. 역할별 프롬프트와 작업 계약을 고정한다.
3. CLI를 로컬 작업 폴더 정리 도구로 개선한다.
4. 샘플 workflow와 품질 체크리스트를 추가한다.
5. API/web app 전환 조건을 별도로 문서화한다.

