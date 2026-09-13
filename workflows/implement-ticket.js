export const meta = {
  name: 'implement-ticket',
  description: 'Implement one PR from an approved plan, looping developer <-> three parallel reviewers until no critical findings remain',
  whenToUse: 'Pass args.plan and args.pr. Pass args.model whenever the original request names an implementation model. The workflow defaults to kimi-k3, falls back to gpt-5.6-luna, and consolidates parallel opus, grok-4.6, and gpt-5.6-sol reviews.',
  phases: [
    { title: 'Develop', detail: 'developer agent implements this PR or addresses critical review feedback' },
    { title: 'Review', detail: 'three code-review agents review in parallel, then one available model consolidates findings' },
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

const REVIEW_MODELS = ['opus', 'grok-4.6', 'gpt-5.6-sol']

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
    ? `\n\nThe reviewers also noted these nits. Fixing them is optional — apply them only if cheap to do alongside the critical fixes:\n${nit.map((f) => `- ${f}`).join('\n')}`
    : ''
  return `This PR:\n${args.pr}\n\nThe consolidated review found these critical issues in round ${round - 1} — fix all of them:\n${critical.map((f) => `- ${f}`).join('\n')}${nitBlock}`
}

let developerModels = args.model ? [args.model] : ['kimi-k3', 'gpt-5.6-luna']

async function runDeveloper(prompt, round) {
  for (let index = 0; index < developerModels.length; index++) {
    const model = developerModels[index]
    const result = await agent(prompt, { agentType: 'developer', model, effort: 'high', phase: 'Develop', label: `develop-${model}-round-${round}` })
    if (!result) continue
    developerModels = developerModels.slice(index)
    return { model, result }
  }
  throw new Error(`No developer model available: ${developerModels.join(', ')}`)
}

async function runReviews(prompt, round) {
  const reviews = await parallel(REVIEW_MODELS.map((model) => () =>
    agent(prompt, { agentType: 'code-review', model, effort: 'high', phase: 'Review', label: `review-${model}-round-${round}`, schema: REVIEW_SCHEMA })
      .then((result) => result ? { model, result } : null)
  ))
  return reviews.filter(Boolean)
}

async function consolidateReviews(round, reviews) {
  const prompt = consolidationPrompt(round, reviews)
  for (const model of reviews.map((review) => review.model)) {
    const result = await agent(prompt, { agentType: 'code-review', model, effort: 'high', phase: 'Review', label: `consolidate-${model}-round-${round}`, schema: REVIEW_SCHEMA })
    if (result) return result
  }
  throw new Error('No available review model could consolidate the findings')
}

function consolidationPrompt(round, reviews) {
  return `Consolidate independent code reviews for round ${round}.

Full plan, for context only:\n${args.plan}

This PR:\n${args.pr}

Reviewer reports:\n${JSON.stringify(reviews)}

Verify every proposed finding against the actual diff. Deduplicate overlapping findings. Drop findings that do not hold up. Resolve disagreements from the code. Keep critical and nit findings separate under the supplied schema. Return empty arrays when no verified findings remain.`
}

let approved = false
let critical = []
let nit = []
let devResult = null
let developerModel = null
let completedReviewModels = []
let round = 0

while (!approved) {
  round++

  phase('Develop')
  const development = await runDeveloper(developPrompt(round, critical, nit), round)
  devResult = development.result
  developerModel = development.model

  phase('Review')
  const reviews = await runReviews(reviewPrompt(round, devResult), round)
  if (!reviews.length) throw new Error('No code-review model was available')
  completedReviewModels = reviews.map((review) => review.model)
  const review = await consolidateReviews(round, reviews)

  critical = review.criticalFindings || []
  nit = review.nitFindings || []
  approved = critical.length === 0

  log(`Round ${round}: ${approved ? 'approved' : `${critical.length} critical finding(s) remain`}${nit.length ? `, ${nit.length} nit(s) (optional)` : ''}; reviewers: ${completedReviewModels.join(', ')}`)
}

return {
  approved,
  rounds: round,
  developerModel,
  completedReviewModels,
  skippedReviewModels: REVIEW_MODELS.filter((model) => !completedReviewModels.includes(model)),
  finalNits: nit,
  devResult,
}
