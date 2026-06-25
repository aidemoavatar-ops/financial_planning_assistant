# Product Requirements Document

This document specifies the requirements for a conversational financial planning assistant. It defines what the agent must do, how it should behave, where its data comes from, and the safety and trust boundaries that govern advisory interactions.

# Product Name

**Atlas, Financial Planning Assistant** (Northwind Bank)

# Summary

Atlas is a chat-first, voice-capable conversational planning assistant for Northwind Bank retail customers. It helps people think through everyday money decisions — what to do with a windfall, whether to pay down debt or save first, how to build an emergency fund, how to sequence competing financial priorities — by running a short discovery conversation, reasoning over the customer's own account data, and grounding its explanations in Northwind's financial-education knowledge base.

Atlas is built as a Hybrid Agent on Customer Experience Agent Studio (Gemini Enterprise for CX): Gemini handles language and reasoning, deterministic Python tools handle planning math and flow control, a Data Store handles knowledge retrieval, and a separate guardrail observer enforces the boundary between education and regulated advice.

Atlas **educates and frames tradeoffs**; it does **not** give licensed investment advice or recommend specific securities. When a customer needs a regulated recommendation, Atlas performs a warm handoff to a licensed human advisor, carrying full conversation context. Tone: warm, plain-spoken, trustworthy, and never pushy.

# Problem

Customers regularly face routine but consequential money decisions — a bonus to allocate, a loan to consider paying off early, a savings gap to close — and have nowhere good to turn for a quick, judgment-free first conversation. Branch appointments and phone queues are slow and feel heavyweight for a "help me think this through" question. Web calculators answer a single narrow question without seeing the customer's full picture. Search and generic chatbots give generic answers ungrounded in the customer's actual balances, rates, and goals, and frequently drift into advice the institution is not authorized to give in an unlicensed channel.

The result is that customers either make uninformed decisions, leave money on the table (e.g., cash sitting in low-yield accounts), or disengage entirely. Northwind has the data and the licensed advisors to help, but no scalable, always-on front door that can do the discovery and framing, surface the right opportunity, and route the genuinely regulated questions to a human.

# Goals

- Give customers fast, plain-language guidance on common personal-finance decisions, grounded in their own account data.
- Run a lightweight discovery conversation (goals, time horizon, safety net, highest-cost debt) before offering any framing.
- Explain tradeoffs and present options as comparisons, so the customer can make an informed decision rather than being told what to do.
- Proactively surface personalized, relevant opportunities (e.g., idle cash in a low-yield account) without being pushy or sales-driven.
- Keep every interaction strictly on the education side of the regulated-advice line, and hand off cleanly to a licensed advisor when it isn't.
- Make handoffs warm: the licensed advisor inherits full context so the customer never repeats themselves.
- Be measurably trustworthy — low hallucination, accurate numbers, clear disclosure of what Atlas is and is not.

# Non-Goals

- Do not provide licensed investment, tax, or legal advice, or recommend specific securities, funds, or products to buy.
- Do not execute money movement, open or close accounts, change limits, or modify products directly in v1.
- Do not perform suitability assessments or KYC/onboarding flows that require a licensed advisor.
- Do not impersonate a licensed advisor, financial planner, or any named Northwind employee.
- Do not make forward-looking guarantees about returns, rates, or market performance.
- Do not optimize for product sales; opportunity surfacing must be in the customer's interest, not quota-driven.
- Do not handle complaints, disputes, fraud, or account servicing — those route to existing service channels.

# Target Audience

The product should serve Northwind's retail banking customers across a range of financial literacy and life stages:

- **Windfall recipients** — customers with a one-time inflow (bonus, tax refund, gift, inheritance) deciding how to allocate it.
- **Debt-vs-save decision makers** — customers weighing whether to pay down a loan or build savings.
- **Early-stage savers** — customers with little or no emergency fund who need a starting framework.
- **Goal-oriented planners** — customers saving toward a near-term goal (home, car, large purchase) who need sequencing help.
- **Optimizers** — financially comfortable customers leaving money on the table (idle cash, suboptimal accounts).
- **Lower-confidence customers** — people who want a judgment-free, plain-language conversation before talking to a human advisor.

# Primary Use Cases

## Financial Discovery And Goal Setting

Users can describe a situation in their own words ("I just got a $20k bonus and don't know what to do with it"). Atlas runs a short, structured discovery — near-term goals, current safety net, highest-cost debt — gathering only what it needs to reason responsibly before offering any framing.

## Personalized Tradeoff Analysis

Users can ask Atlas to weigh options. Atlas pulls the customer's real balances, loan APRs, and savings yields, runs the relevant planning math (emergency-fund gap, debt-vs-invest comparison, payoff timelines), and presents the options as a clear side-by-side comparison with the case for each — never a single directive answer.

## Financial Education And Concept Explanation

Users can ask Atlas to explain a concept ("what's an emergency fund," "what does APR mean," "why pay off debt before investing"). Atlas answers from Northwind's vetted financial-education knowledge base, clearly distinguishing general educational principles from the customer's specific numbers.

## Proactive Opportunity Surfacing

Where the customer's account state reveals a clearly beneficial, low-risk opportunity (e.g., a large balance earning near-zero interest while a high-yield product exists), Atlas may surface it once, with the quantified benefit and an offer to explain — framed as education, never as a hard sell.

## Licensed-Advisor Handoff

When a request crosses into regulated advice (specific investment selection, suitability, tax/legal questions) or otherwise exceeds Atlas's scope, Atlas explains the boundary, offers to connect a licensed human advisor, and performs a warm handoff that carries the full conversation context.

## Multilingual Help

Users may speak or write in any supported language. Atlas should match the user's language and maintain the same accuracy, disclosure, and boundary behavior across languages.

# User Experience Requirements

## Conversation First

Responses should be optimized for a back-and-forth advisory conversation, not a one-shot answer dump. Atlas should ask before assuming, keep turns short and scannable, use structured comparisons (tables/short lists) when presenting options, and confirm understanding before moving to the next step. On voice, the same content must degrade gracefully to concise, listenable phrasing without tables.

## Personality

Atlas should be warm, calm, plain-spoken, and genuinely helpful — the trusted friend who is good with money, not a salesperson and not a textbook. It should be encouraging without being patronizing, honest about uncertainty, and quick to say "that's a question for a licensed advisor" when appropriate. It must never shame the customer about their financial situation.

## Identity

Atlas should introduce itself as "Atlas, Northwind's planning assistant," and proactively disclose at the start of substantive interactions that it provides educational guidance and is not a licensed financial advisor. It must never claim to be human or to be a licensed professional.

# Functional Requirements

## Account Data And Personalization

The agent should retrieve the customer's relevant financial state — account balances, savings APY, loan balances and APRs, and recent cash-flow signals — and reason over real values rather than customer estimates. State must be snapshotted to the session before any calculation, and tools must be idempotent so retrieval can be retried safely.

## Planning Calculations And Tradeoff Logic

The agent should run all planning math in deterministic code, not in the model: emergency-fund target and gap, debt-vs-invest comparison (including the "guaranteed return" of debt payoff), payoff timelines, and proposed allocation splits. The calculation tool should return both the results and an explicit instruction for how the agent presents them, so framing is consistent and the model does not invent numbers.

## Financial Education And Knowledge Grounding

The agent should answer conceptual and policy questions from a curated Northwind financial-education knowledge base via retrieval-augmented generation. Educational content must be vendor-neutral and clearly separated from the customer's personalized figures. The agent must not present parametric/model-memory financial claims as Northwind guidance.

## Regulated-Advice Boundary

The agent must detect and refuse requests that constitute licensed advice (specific security/fund selection, suitability determinations, tax or legal advice, market timing, return predictions). The boundary must be enforced by a dedicated guardrail observer in code, independent of prompt phrasing, and the refusal must use a constructive redirect (offer the licensed-advisor path) rather than a flat "I can't."

## Official Resource And Product Guidance

The agent should be able to point customers to official Northwind destinations (product pages, rate disclosures, the advisor scheduling flow) and explain how a product works, without completing the action. It must not quote rates or terms that conflict with the official source of record.

## Licensed-Advisor Escalation

The agent should be able to escalate to a licensed human advisor on request or when the boundary is hit. Escalation routes through the contact-center platform and delivers a generated summary to the advisor — verified context, the discovery answers, any proposed framing, and the open question — so the customer does not repeat themselves.

## Future Escalation

The first release routes regulated questions to licensed advisors via warm handoff and scheduling. Real-time, account-modifying transactions initiated by the agent (account opening, money movement) are out of scope for v1 and gated behind future enhancements.

# Data And Source Requirements

- Account and product data (balances, APRs, APYs, loan terms) should come from the bank's system of record via authenticated tools, never from model memory.
- Financial-education content should come from a curated, reviewed Northwind knowledge base served through a Data Store; the reranked retrieval prompt must be inspectable in logs for testing.
- Product rates and terms must always reflect the official source of record at response time; cached or stale figures must not be quoted.
- All personalized figures must be traceable to a tool call; the agent must not state a number it did not retrieve or compute.
- Licensed-advisor availability and scheduling should come from the advisor routing/calendar system, not be asserted by the agent.

# Safety, Brand, And Trust Requirements

- Do not provide licensed investment, tax, or legal advice, and never recommend specific securities or products to buy.
- Do not impersonate a human, a licensed advisor, or any named Northwind employee.
- Disclose the educational (non-advisory) nature of the assistant clearly and early.
- Do not make guarantees or predictions about returns, rates, or markets; frame the future as uncertain.
- Apply strict PII handling — never reveal another person's account details, and sanitize sensitive entities; gate account-data access behind identity verification where required.
- Do not shame, pressure, or upsell; opportunity surfacing must be in the customer's clear interest and offered, not pushed.
- Log every guardrail trigger (which guardrail, the triggering scenario, what the user was trying to do) to identify coverage gaps and tune the instruction layers above it.

# Success Metrics

Success should be measured as a mix of helpfulness, trust, accuracy, and responsible routing:

- **Task helpfulness** — customer-rated usefulness of the guidance and tradeoff framing.
- **Containment vs. correct escalation** — share of questions Atlas can responsibly handle, balanced against clean, appropriate handoffs (escalating a regulated question is a success, not a failure).
- **Numerical accuracy** — zero tolerance for fabricated or incorrect personalized figures; verified against tool outputs.
- **Hallucination rate** — measured on educational and grounded answers via LLM-as-a-judge plus sampling.
- **Boundary integrity** — rate at which regulated-advice requests are correctly refused/redirected, evaluated against an adversarial scenario set.
- **Handoff quality** — advisor-reported completeness of inherited context; customer not having to repeat themselves.
- **Proactive value** — customer take-up and satisfaction with surfaced opportunities, monitored to ensure they remain helpful rather than salesy.

# Launch Scope

## First Release

- Discovery-driven advisory conversation for windfall allocation, debt-vs-save, and emergency-fund decisions.
- Personalized tradeoff analysis grounded in the customer's real account data, with deterministic planning math.
- Financial-education Q&A grounded in the curated Northwind knowledge base.
- Single proactive opportunity-surfacing pattern (idle cash / suboptimal yield), framed as education.
- Regulated-advice guardrail and warm handoff to a licensed advisor with full context summary.

## Future Enhancements

- Agent-initiated transactions (open a high-yield account, schedule a transfer) after suitability and controls work.
- Goal tracking and proactive check-ins over time (anticipatory outreach).
- Broader planning domains (retirement, mortgage readiness, education savings).
- Multilingual coverage expansion and voice-channel parity with chat-first features.

# Acceptance Criteria

- A user can describe a windfall in natural language and Atlas runs discovery before offering any framing.
- Atlas pulls the user's real balances, APRs, and APYs and uses them — not user estimates — in its analysis.
- Atlas presents at least two options as a comparison with the case for each, and never issues a single directive "you should buy X."
- All personalized numbers in a response trace back to a tool call or computation; no fabricated figures.
- Atlas explains a requested financial concept from the knowledge base and visibly separates general principles from the user's specific numbers.
- When the user asks which specific fund/security to buy, Atlas refuses, explains why, and offers the licensed-advisor path.
- On escalation, the licensed advisor receives a context summary covering discovery answers, proposed framing, and the open question.
- Atlas discloses early that it is an educational assistant and not a licensed advisor.
- Atlas surfaces a relevant idle-cash opportunity (when present) once, with the quantified benefit, without pressuring the user.

# Risks

- Account or rate data may be incomplete, delayed, or unavailable, leading to incorrect or stale guidance.
- The model may drift across the education/advice boundary under creative phrasing if guardrails are under-tuned.
- Proactive opportunity surfacing could be perceived as a sales push, eroding trust, if framing or frequency is wrong.
- Customers may over-trust Atlas and treat educational framing as personalized licensed advice.
- Regulatory requirements for unlicensed advisory channels vary by jurisdiction and may constrain features or disclosures.

# Open Questions

- Which exact regulatory and compliance review requirements (disclosures, recordkeeping, jurisdiction limits) apply to an unlicensed advisory assistant for Northwind?
- What is the approved policy for proactive opportunity surfacing — which signals qualify, and what frequency/consent model is acceptable?
- Where is the precise line on tax-adjacent education (e.g., "what is a tax-advantaged account") versus regulated tax advice, and who signs off on it?
