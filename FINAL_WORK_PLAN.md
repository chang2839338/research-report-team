# research-report-team 최종 작업 계획

## 요약

`research-report-team`은 의사결정 리서치와 보고서 작성을 돕는 AI 팀 운영 스킬이다. 현재 개발 방향은 **ChatGPT Pro를 최대한 활용하는 PC 기반 Codex Skill workflow**를 우선한다.

API 호출, 독립 LLM worker, 웹앱은 지금 당장 만들지 않는다. ChatGPT Pro 구독 안에서 Codex와 새 채팅을 활용해 비용을 줄이고, 먼저 스킬의 업무 방식, 역할 분담, 보고서 품질 기준, 산출물 구조를 안정화한다.

## 핵심 결정

- 우선 목표는 웹앱이 아니라 **PC에서 바로 쓸 수 있는 Skill 기반 리서치/보고서 팀**이다.
- 현재 방식은 한 명의 Codex가 Manager 역할을 맡고 Researcher, Analyst, Writer, Reviewer 역할을 순차적으로 수행한다.
- API는 ChatGPT Pro 구독과 별도 과금되므로, 자동화가 꼭 필요한 단계가 오기 전까지 사용하지 않는다.
- 독립 agent runner와 웹앱은 장기 옵션으로 남기되, 현재 roadmap에서는 보류한다.
- GitHub repo는 스킬 배포와 설치, 버전 관리, 이슈 관리 용도로 사용한다.

## 현재 상태

현재 repo에는 1차 Skill MVP가 구현되어 있다.

- `SKILL.md`: Codex가 팀장처럼 동작하도록 하는 메인 스킬 지침.
- `agents/openai.yaml`: Skill UI 메타데이터.
- `references/roles.md`: Manager, Researcher, Analyst, Writer, Reviewer 역할 정의.
- `references/workflow.md`: 질문, 작업 분해, 조사, 분석, 작성, 검수, 수정 루프.
- `references/report-quality-rubric.md`: 보고서 품질 검수 기준.
- `references/output-templates.md`: 의사결정 브리프, 경영 보고서, 리서치 메모 템플릿.
- `scripts/research_team_cli.py`: 작업 폴더와 기본 산출물 파일을 만드는 작은 CLI.

## 단계별 개발 계획

### Phase 1: Skill MVP 정리

상태: 완료.

목표:

- Codex가 리서치/보고서 팀장처럼 일하도록 기본 운영 방식을 정의한다.
- 고정 핵심 역할과 임무별 전문 역할의 기준을 정한다.
- 보고서 품질 기준과 기본 템플릿을 제공한다.

완료 산출물:

- Skill 지침.
- 역할 정의.
- workflow 문서.
- 품질 rubric.
- 보고서 템플릿.
- 기본 CLI.

검증:

- Skill validator 통과.
- CLI 샘플 실행 성공.
- GitHub repo 업로드 완료.

### Phase 2: ChatGPT Pro 사용 가이드 추가

목표:

- 사용자가 ChatGPT Pro와 Codex를 이용해 이 Skill을 실제 업무에 반복 사용할 수 있게 한다.
- 새 PC에 repo를 설치하고 Skill을 인식시키는 절차를 문서화한다.
- API 없이 새 채팅에서 업무를 시작하는 표준 사용법을 정한다.

예상 산출물:

- `references/chatgpt-pro-workflow.md`
- `references/install-and-update.md`
- 새 채팅에서 사용할 기본 업무 지시문 예시.
- Skill 업데이트 방법.

검증:

- 새 PC 또는 깨끗한 폴더 기준으로 설치 절차를 따라 할 수 있다.
- 사용자가 ChatGPT Pro 채팅에서 Skill 기반 업무 지시를 시작할 수 있다.
- API key 없이도 workflow가 설명된다.

### Phase 3: 역할별 프롬프트 팩 정리

목표:

- 현재 Skill 안에 들어 있는 역할 개념을 더 명확한 프롬프트 파일로 분리한다.
- 아직 독립 LLM 호출은 하지 않지만, 나중에 분리할 수 있도록 입력/출력 계약을 고정한다.

예상 산출물:

- `prompts/manager.md`
- `prompts/researcher.md`
- `prompts/analyst.md`
- `prompts/writer.md`
- `prompts/reviewer.md`
- `references/task-contract.md`

검증:

- 각 프롬프트가 역할, 입력, 출력, 실패 기준을 명확히 설명한다.
- 한 개의 샘플 업무를 각 역할 프롬프트에 맞게 분해할 수 있다.
- Codex가 프롬프트 파일을 참고해 일관된 결과를 낼 수 있다.

### Phase 4: CLI를 PC 업무 보조 도구로 개선

목표:

- CLI를 API 실행기가 아니라 **작업 폴더 생성기 및 산출물 정리 도구**로 발전시킨다.
- 사용자는 ChatGPT Pro에서 업무를 수행하되, 로컬 파일 구조는 CLI가 정리하게 한다.

예상 기능:

- 업무 폴더 생성.
- 역할별 prompt 파일 생성.
- `task.json`, `status.json` 생성.
- `artifacts/` 폴더 생성.
- 최종 보고서 파일 위치 고정.

권장 작업 폴더 구조:

```text
research-team-runs/
  <timestamp-task-slug>/
    task.json
    status.json
    prompts/
      manager.md
      researcher.md
      analyst.md
      writer.md
      reviewer.md
    artifacts/
      research.md
      analysis.md
      draft.md
      review.md
      final.md
    sources.md
```

검증:

- 샘플 brief로 업무 폴더가 생성된다.
- 생성된 prompt 파일에 task context가 포함된다.
- 생성된 JSON 파일이 유효하다.
- 사용자가 ChatGPT Pro 결과물을 artifacts에 붙여 넣어 관리할 수 있다.

### Phase 5: 샘플 업무와 품질 점검 세트 추가

목표:

- 이 Skill을 처음 쓰는 사용자가 바로 따라 할 수 있는 예제를 제공한다.
- 좋은 결과와 부족한 결과를 구분하는 기준을 실제 예시로 보여준다.

예상 산출물:

- `examples/decision-brief/`
- `examples/research-memo/`
- `examples/reviewer-feedback/`
- `references/quality-checklist.md`

검증:

- 예제 하나를 따라 하면 최종 보고서까지 도달할 수 있다.
- Reviewer 기준으로 부족한 부분을 발견하고 수정 요청을 만들 수 있다.
- 최종 보고서가 의사결정에 쓸 수 있는 형태다.

### Phase 6: 독립 agent runner/API/web app 검토

상태: 보류.

검토 조건:

- Skill 기반 workflow를 여러 번 사용해 보고 반복 업무가 충분히 확인된다.
- 수동 복사/붙여넣기보다 자동 실행의 가치가 커진다.
- API 비용을 감당할 만큼 사용 빈도와 효과가 높다.
- PC/모바일 어디서든 업무 지시가 필요한 시점이 온다.

그때 검토할 항목:

- 독립 LLM agent runner.
- API server.
- background worker.
- database.
- PC/모바일 web app.
- 알림 기능.

## Agent 운영 방식

### 현재 방식

한 명의 Codex가 Manager 역할을 맡고, 내부적으로 Researcher, Analyst, Writer, Reviewer 역할을 나누어 수행한다.

장점:

- ChatGPT Pro 구독을 활용하므로 추가 API 비용이 없다.
- 구현과 사용이 빠르다.
- 프롬프트와 품질 기준을 실험하기 쉽다.
- 실패 원인을 추적하기 쉽다.

한계:

- 진짜 병렬 agent 실행은 아니다.
- 역할별 독립성이 완전하지 않다.
- 웹앱 자동화에는 한계가 있다.

### 장기 방식

각 역할을 별도 LLM 호출 또는 worker로 실행한다.

장점:

- 역할별 독립 실행.
- 작업 상태 추적.
- 웹앱/모바일앱 연결.
- 병렬 처리.

단점:

- API 비용이 별도로 발생한다.
- 구현 복잡도가 높다.
- 상태 저장, 재시도, 오류 처리, 보안 설계가 필요하다.

현재 결정:

- 장기 방식은 보류한다.
- 먼저 ChatGPT Pro + Codex Skill workflow를 안정화한다.

## 품질 기준

최종 보고서는 다음 기준을 만족해야 한다.

- 사용자의 의사결정 또는 보고 목적에 직접 답한다.
- 대상 독자에게 맞는 깊이와 문체를 사용한다.
- 사실, 해석, 가정, 추천을 구분한다.
- 최신 사실 또는 외부 정보에는 출처를 붙인다.
- 선택지를 명확한 기준으로 비교한다.
- 주요 위험과 한계를 숨기지 않는다.
- 실행 가능한 다음 행동을 제시한다.

시스템 자체는 다음 기준을 만족해야 한다.

- Skill이 검증된다.
- 새 PC에 설치할 수 있다.
- ChatGPT Pro에서 API 없이 사용할 수 있다.
- 작업 산출물을 로컬 폴더에 정리할 수 있다.
- GitHub issue로 단계별 개발을 추적할 수 있다.

## 테스트 계획

Skill 검증:

```powershell
python "C:\Users\SINI\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
```

CLI 검증:

```powershell
python .\scripts\research_team_cli.py "AI agent team 업무 방식 의사결정 보고서" --title "AI Agent Team Decision Brief" --out .\tmp-cli-test
```

GitHub 검증:

```powershell
git status --short
git log --oneline -3
git push
```

## 용어 해설

- Skill: Codex가 특정 방식으로 일하도록 알려주는 작업 매뉴얼.
- Codex: 코딩과 파일 작업을 도와주는 ChatGPT 기반 작업 agent.
- ChatGPT Pro: 사용자가 이미 가입한 유료 ChatGPT 구독. API 과금과는 별도다.
- API: 프로그램이 모델을 직접 호출하기 위한 연결 통로. 사용량에 따라 별도 비용이 발생한다.
- CLI: 명령어로 실행하는 작은 프로그램.
- Agent runner: 여러 역할 agent를 실제로 실행하고 결과를 저장하는 실행 엔진.
- Artifact: 작업 결과물 파일. 예: 조사 결과, 분석 문서, 초안, 리뷰, 최종 보고서.
- Rubric: 결과물을 평가하기 위한 점수표 또는 기준표.

## 기본 가정

- repo 이름은 `research-report-team`을 유지한다.
- 당분간 API 호출은 추가하지 않는다.
- 웹앱 개발은 필요성이 커진 뒤 다시 검토한다.
- 기본 실행 환경은 사용자의 PC와 ChatGPT Pro다.
- GitHub는 배포, 버전 관리, 이슈 관리 용도로 사용한다.

