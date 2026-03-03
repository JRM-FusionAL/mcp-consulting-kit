# Engagement → Enterprise Feature Intake Loop

## Purpose

Use every consulting engagement to identify the first governance feature enterprises will pay for, then ship that feature into FusionAL enterprise tier.

## Core Rule

No feature enters the enterprise backlog unless it appears in real customer conversations at least 3 times across 2+ accounts or directly blocks a paid pilot.

## Discovery Questions (Ask Every Call)

1. What compliance or internal policy requirement is currently blocking MCP rollout?
2. What do you need to prove in an audit after an agent uses a tool?
3. Which tool calls should be blocked, limited, or approval-gated?
4. Who needs access segmentation (team, tenant, environment)?
5. What incident would make leadership pause MCP adoption?

## Feature Signal Capture Template

For each call, record:

- account name + industry
- deal stage (discovery / proposal / pilot / live)
- requested governance capability
- urgency (critical / high / medium / low)
- revenue impact (blocks deal, accelerates deal, nice-to-have)
- workaround today
- exact language used by buyer

## Prioritization Score (0-10)

`score = pain_frequency + deal_impact + implementation_speed`

- pain_frequency (0-4): how often it appears
- deal_impact (0-4): effect on pilot close/revenue
- implementation_speed (0-2): can ship in <=2 weeks

Ship the highest score first.

## Initial Candidate Features

- Audit export (JSON/CSV)
- Policy profiles (`strict`, `balanced`, `dev`)
- Tenant-scoped API keys + revocation
- Rate limit presets by team
- Tool allow/deny list with environment scoping

## Weekly Operating Cadence

- Monday: review previous week’s call notes
- Tuesday: lock one feature for current sprint
- Wednesday-Thursday: implement + doc + demo update
- Friday: ship changelog + use in outbound messaging

## Definition of Done (Enterprise Feature)

- implemented in FusionAL core
- documented in README and runbook
- visible in demo flow under 7 minutes
- mapped to one buyer pain statement
- included in proposal language and pricing justification

## Proposal Language Snippet

"This pilot includes governance controls prioritized from live enterprise requirements: [feature]. This directly addresses [risk/compliance concern] and is productionized in your environment (self-hosted)."
