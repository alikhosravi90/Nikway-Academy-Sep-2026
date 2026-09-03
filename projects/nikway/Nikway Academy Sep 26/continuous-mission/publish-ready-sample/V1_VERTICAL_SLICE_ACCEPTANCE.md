# V1 Vertical Slice Acceptance

## Scenario

An org admin assigns a published journey to a learner. The learner submits text evidence for step one. An assessor accepts it against the criteria. The progression module records advancement to step two. The org admin sees the updated learner and journey completion report.

## Acceptance checks

- The assignment belongs to the authenticated organization.
- The learner can read only their own assignment and evidence.
- The assessor can read assigned evidence and write an assessment.
- An accepted assessment creates exactly one progression event.
- A needs-revision assessment does not advance the learner.
- Every mutation emits an xAPI-shaped event and an audit record.
- Organization B cannot observe or modify any Organization A record.
- Repeating a mutation with the same `Idempotency-Key` does not duplicate the result.

## Failure paths

- Unauthenticated: `401`
- Wrong organization: `404` or `403` without revealing record existence
- Wrong role: `403`
- Invalid evidence: `422`
- Duplicate mutation: return original result
- Missing next step: complete the assignment and emit completion progression
