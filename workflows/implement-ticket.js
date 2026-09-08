export const meta = {
  name: 'implement-ticket',
  description: 'Implement one PR from an approved plan, looping developer <-> code-review until no critical findings remain',
  whenToUse: 'Pass args.plan (the full approved plan, for context) and args.pr (the one PR to implement this run). Call this once per PR, after the previous PR has been approved — it implements only args.pr, never the rest of the plan. Loops developer and code-review until the reviewer has no critical findings left for this PR. Nit findings never block approval and fixing them is optional.',
  phases: [
    { title: 'Develop', detail: 'developer agent implements this PR or addresses critical review feedback' },
    { title: 'Review', detail: 'code-review agent splits findings into critical and nit' },
  ],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    criticalFindings: {
      type: 'array',
      items: { type: 'string' },
      description: 'Findings that must be fixed before this PR can ship: incorrect behavior, security leaks, performance leaks, or scope bleeding into a different PR.',
    },
    nitFindings: {
      type: 'array',
      items: { type: 'string' },
      description: 'Optional cleanups: style, naming, minor readability. Never blocks approval.',
    },
  },
  required: ['criticalFindings', 'nitFindings'],
}

if (!args || !args.plan || !args.pr) {
  throw new Error('implement-ticket requires args.plan (the full plan) and args.pr (the one PR to implement this run)')
}

function reviewPrompt(round, devResult) {
  return `Review the current branch against main for correctness, scope, security, and performance.

Full plan, for context only — other PRs in it are out of scope this run:\n${args.plan}

The PR this run is scoped to:\n${args.pr}

Developer's summary of round ${round}'s changes:\n${devResult}

Split every finding into exactly one of two buckets:
- criticalFindings: incorrect behavior, security leaks, performance leaks, or any change that belongs to a different PR in the plan. Each one blocks approval until fixed.
- nitFindings: everything else — style, naming, minor readability. These never block approval; fixing them is optional.
Return an empty criticalFindings array once nothing left requires a fix.`
}

function developPrompt(round, critical, nit) {
  if (round === 1) return `Implement only this PR from the approved plan. Do not implement any other PR in it.\n\nFull plan, for context:\n${args.plan}\n\nThis PR:\n${args.pr}`
  const nitBlock = nit.length
    ? `\n\nThe reviewer also noted these nits. Fixing them is optional — apply them only if cheap to do alongside the critical fixes:\n${nit.map((f) => `- ${f}`).join('\n')}`
    : ''
  return `This PR:\n${args.pr}\n\nA code reviewer found these critical issues in your round ${round - 1} changes — fix all of them:\n${critical.map((f) => `- ${f}`).join('\n')}${nitBlock}`
}

let approved = false
let critical = []
let nit = []
let devResult = null
let round = 0

while (!approved) {
  round++

  phase('Develop')
  devResult = await agent(developPrompt(round, critical, nit), {
    agentType: 'developer',
    phase: 'Develop',
    label: `develop-round-${round}`,
  })

  phase('Review')
  const review = await agent(reviewPrompt(round, devResult), {
    agentType: 'code-review',
    phase: 'Review',
    label: `review-round-${round}`,
    schema: REVIEW_SCHEMA,
  })

  critical = review.criticalFindings || []
  nit = review.nitFindings || []
  approved = critical.length === 0

  log(`Round ${round}: ${approved ? 'approved' : `${critical.length} critical finding(s) remain`}${nit.length ? `, ${nit.length} nit(s) (optional)` : ''}`)
}

return { approved, rounds: round, finalNits: nit, devResult }
