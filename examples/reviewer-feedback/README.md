# Example: Reviewer Feedback

This example shows how the Reviewer should identify gaps and request targeted revisions.

## Draft Problem

The draft says:

```text
웹앱을 만들면 편리하므로 바로 웹앱을 개발하는 것이 좋다.
```

This is weak because it gives a recommendation without comparing cost, complexity, or current project maturity.

## Reviewer Output

```markdown
## Review

### Score

- Goal fit: 1
- Audience fit: 1
- Evidence quality: 0
- Source traceability: 0
- Analytical clarity: 0
- Recommendation quality: 0
- Risk coverage: 0
- Usability: 1

Total: 3/16

### Required Revisions

- Compare ChatGPT Pro skill workflow and web app/API workflow using the same criteria.
- Explain API cost and implementation complexity as risks.
- Add a near-term recommendation that matches the current project stage.
- Add conditions for revisiting web app development later.
- Separate facts, assumptions, and recommendation.

### Approval Decision

Needs revision.
```

## Improved Recommendation

```text
현재 단계에서는 ChatGPT Pro 기반 skill workflow를 우선한다. 웹앱은 반복 사용량, 자동화 필요성, 모바일 접근 필요성이 충분히 확인된 뒤 검토한다. 이 선택은 추가 API 비용을 피하면서 역할 프롬프트와 보고서 품질 기준을 먼저 검증할 수 있다는 장점이 있다.
```

