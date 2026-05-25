# Example: Research Memo

This example shows how to use `research-report-team` when the user wants to understand a topic before making a decision.

## User Request

```text
research-report-team 스킬을 사용해줘.

ChatGPT Pro 기반으로 업무를 진행하는 방식과 API 기반으로 자동화하는 방식의 차이를 조사해서 리서치 메모로 정리해줘.
비용, 자동화 수준, 구현 난이도, 나중에 웹앱으로 확장할 가능성을 중심으로 봐줘.
```

## Manager Task Brief

- Research question: What is the practical difference between using ChatGPT Pro manually and using API-based automation?
- Target reader: non-developer project owner.
- Output format: research memo.
- Scope: cost model, workflow fit, automation value, future expansion.
- Acceptance criteria:
  - Explain the difference in plain language.
  - Highlight the practical recommendation for the current project.
  - Include caveats about when API automation may become useful.

## Sample Research Memo

# ChatGPT Pro 방식과 API 자동화 방식 리서치 메모

## Question

ChatGPT Pro를 이미 구독한 상태에서, `research-report-team`을 API 없이 운영하는 것이 합리적인가?

## Short Answer

초기에는 합리적이다. 현재 목표가 workflow 검증과 보고서 품질 개선이라면 ChatGPT Pro 기반 skill 방식이 비용과 속도 면에서 유리하다. API 자동화는 반복 업무, 웹앱, 상태 추적, 다중 사용자 사용이 중요해질 때 검토하는 것이 좋다.

## Findings

- ChatGPT Pro 방식은 사용자가 직접 새 채팅을 열고 업무를 지시하는 방식이다.
- API 방식은 프로그램이 모델을 직접 호출하는 방식이며 별도 사용량 비용이 발생할 수 있다.
- Skill 방식은 팀 운영 매뉴얼을 재사용하는 데 강하고, API 방식은 자동 실행과 웹앱 연결에 강하다.
- 현재 repo에는 Skill, 역할 문서, CLI 정리 도구가 있으므로 PC 기반 workflow를 먼저 다듬기 좋다.

## Interpretation

지금은 자동화보다 “좋은 업무 방식”을 찾는 단계다. 따라서 API runner를 먼저 만드는 것보다, ChatGPT Pro에서 반복 사용하며 역할 프롬프트와 보고서 품질 기준을 다듬는 편이 낫다.

## Open Questions

- 한 달에 몇 번 정도 이 workflow를 사용할 것인가?
- 보고서를 혼자 쓸 것인가, 팀원과 공유할 것인가?
- 모바일에서 업무 지시와 보고 확인이 꼭 필요한가?
- 수동 복사/붙여넣기가 어느 시점부터 부담이 되는가?

## Recommendation

당장은 ChatGPT Pro + Codex Skill + CLI 작업 폴더 정리 방식으로 운영한다. API와 웹앱은 반복 사용량과 자동화 필요성이 확인된 뒤 다시 판단한다.

