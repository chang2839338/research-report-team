# GitHub 이슈 작업 내용 한글 참고본

이 문서는 GitHub에 등록된 `research-report-team` 작업 이슈를 읽기 쉽게 한글로 번역한 참고용 문서다. 실제 작업 관리는 GitHub Issue를 기준으로 한다.

## 전체 진행 순서

```text
#1 ChatGPT Pro 사용/설치 가이드
  ↓
#2 역할별 프롬프트 팩과 작업 계약
  ↓
#3 CLI 로컬 작업 폴더 정리 도구 개선
  ↓
#4 샘플 workflow와 품질 체크리스트
  ↓
#5 API/agent runner/web app 전환 조건 정의
```

## 용어 해설

- AFK: 사람이 중간에 결정하지 않아도 진행 가능한 작업.
- HITL: Human-in-the-loop. 사람의 판단이나 승인이 필요한 작업.
- Blocked by: 먼저 끝나야 하는 선행 작업.
- CLI: 명령어로 실행하는 도구.
- Artifact: 조사 결과, 분석, 초안, 리뷰, 최종 보고서 같은 작업 결과물.
- API: 프로그램이 모델을 직접 호출하는 방식. ChatGPT Pro 구독과 별도로 비용이 발생할 수 있다.

## #1 ChatGPT Pro 기반 사용/설치 가이드 추가

GitHub 원문: https://github.com/chang2839338/research-report-team/issues/1

유형: AFK

### 작업 목표

`research-report-team`을 API 없이 ChatGPT Pro와 Codex로 사용하는 PC 기반 workflow를 문서화한다. GitHub에서 skill을 설치하거나 업데이트하는 방법, 새 ChatGPT/Codex 채팅에서 skill을 활용하는 방법, 의사결정 리서치/보고서 업무를 수동으로 실행하는 방법을 설명한다.

### 완료 기준

- [ ] PC에서 ChatGPT Pro와 Codex로 skill을 사용하는 가이드를 추가한다.
- [ ] 이 workflow에는 API key가 필요 없다는 점을 설명한다.
- [ ] GitHub repo에서 설치/업데이트하는 절차를 포함한다.
- [ ] 새 리서치/보고서 업무를 시작할 때 복사해서 쓸 수 있는 기본 프롬프트를 포함한다.
- [ ] 개발자가 아닌 사용자도 이해할 수 있게 용어를 쉽게 설명한다.

### 선행 작업

없음. 바로 시작 가능.

## #2 역할별 프롬프트 팩과 작업 계약 문서 추가

GitHub 원문: https://github.com/chang2839338/research-report-team/issues/2

유형: AFK

### 작업 목표

Manager, Researcher, Analyst, Writer, Reviewer 역할별 프롬프트 파일과 작업 계약 문서를 만든다. 현재의 단일 Codex workflow가 더 일관되게 작동하도록 하고, 나중에 필요하면 독립 agent로 분리할 수 있게 준비한다. 단, 이 작업은 여전히 ChatGPT Pro skill workflow를 대상으로 하며 API 실행을 구현하지 않는다.

### 완료 기준

- [ ] Manager, Researcher, Analyst, Writer, Reviewer용 프롬프트 파일을 추가한다.
- [ ] 각 프롬프트는 역할 목적, 필요한 입력, 기대 출력, 실패/수정 규칙을 정의한다.
- [ ] 작업 brief와 역할별 산출물 형태를 설명하는 작업 계약 문서를 추가한다.
- [ ] 기존 skill workflow 및 품질 rubric과 일치하도록 작성한다.
- [ ] 사용자 요청이 역할별 작업으로 나뉘는 작은 예시를 포함한다.

### 선행 작업

- #1 완료 필요.

## #3 CLI를 로컬 작업 폴더 정리 도구로 개선

GitHub 원문: https://github.com/chang2839338/research-report-team/issues/3

유형: AFK

### 작업 목표

CLI를 ChatGPT Pro workflow용 로컬 작업 폴더 정리 도구로 개선한다. CLI는 API를 호출하지 않는다. 대신 사용자가 실제 사고와 작성은 ChatGPT Pro에서 진행하고, PC 안의 업무 폴더, 역할별 프롬프트, 상태 정보, 산출물 파일을 체계적으로 관리할 수 있게 한다.

### 완료 기준

- [ ] CLI가 `task.json`, `status.json`, `prompts/`, `artifacts/`, `sources.md`를 포함한 작업 폴더 구조를 만든다.
- [ ] 생성된 역할별 프롬프트 파일에 task brief와 역할별 지침이 포함된다.
- [ ] research, analysis, draft, review, final report용 artifact placeholder가 생성된다.
- [ ] JSON 파일은 유효하고, 나중에 작업을 재개할 수 있을 만큼의 metadata를 포함한다.
- [ ] 기존의 간단한 PowerShell 실행 방식은 유지한다.

### 선행 작업

- #2 완료 필요.

## #4 샘플 workflow와 보고서 품질 체크리스트 추가

GitHub 원문: https://github.com/chang2839338/research-report-team/issues/4

유형: AFK

### 작업 목표

처음 사용하는 사람도 task 접수부터 최종 보고서까지 따라 할 수 있는 실제 예제를 추가한다. 사용자가 ChatGPT Pro에 무엇을 붙여 넣고, 결과물을 로컬 어디에 저장하며, 보고서가 충분히 좋은지 어떻게 판단하는지 보여준다.

### 완료 기준

- [ ] 의사결정 브리프 예제 1개 이상과 리서치 메모 예제 1개 이상을 추가한다.
- [ ] Reviewer 피드백과 수정 요청 예시를 포함한다.
- [ ] 최종 보고서용 간단한 품질 체크리스트를 추가한다.
- [ ] 예제는 근거, 분석, 추천, 위험, 다음 행동을 보여준다.
- [ ] 예제는 역할별 프롬프트와 CLI 작업 폴더 구조와 일치한다.

### 선행 작업

- #2 완료 필요.
- #3 완료 필요.

## #5 API, agent runner, web app 전환 조건 정의

GitHub 원문: https://github.com/chang2839338/research-report-team/issues/5

유형: HITL

### 작업 목표

언제 ChatGPT Pro skill workflow를 넘어 API 호출, 독립 agent runner, 웹앱으로 전환할지 판단 기준을 문서화한다. 이 이슈는 API나 웹앱을 구현하지 않는다. 비용이 발생하는 복잡한 구조로 너무 빨리 넘어가지 않도록 미래의 전환 조건을 명확히 정한다.

### 완료 기준

- [ ] API 사용이 가치 있어지는 조건을 명확히 적는다.
- [ ] 독립 agent runner가 필요한 조건을 명확히 적는다.
- [ ] 웹앱을 시작할 조건을 명확히 적는다.
- [ ] 비용, 자동화 가치, 업무 빈도, 모바일/원격 접근 필요성을 판단 요소로 포함한다.
- [ ] 위 조건이 충족되기 전까지 API/web app 작업은 보류한다고 명시한다.

### 선행 작업

- #4 완료 필요.

