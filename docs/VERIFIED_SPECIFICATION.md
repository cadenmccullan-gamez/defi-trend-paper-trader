# Verified DeFi Trend-Following Trading Algorithm

> **Axiom Hive Technology**  
> **Technical attribution:** Alexis M. Adams & Nicholas Michael Grossi  
> **Document status:** Corrected product and engineering specification  
> **Verification date:** August 19, 2026 (EDT)

## Scope and verification statement

This document corrects and replaces the attached *DeFi Trend-Following Trading Algorithm* draft after a source-by-source review of its material claims. It defines a **research, backtesting, and paper-trading** system for a narrow DeFi market-data scope. It does not authorize live routing, transaction signing, wallet custody, third-party capital, or investment recommendations. Historical results are research observations, not evidence of future profitability.

The principal corrections concern (1) the distinction between Uniswap v2 and v3 mechanics, (2) point-in-time data and finality handling, (3) cost-model specificity, (4) validation terminology and multiple-testing controls, and (5) current U.S. legal-source citations. The legal material is an engineering issue register, **not legal advice or a legal classification**.

## 1. Verification register

| Original topic | Verification outcome | Corrected requirement |
|---|---|---|
| Time-series momentum supports a DeFi premise | **Supported only as a research hypothesis.** The cited seminal study examined 58 liquid equity-index, currency, commodity, and bond futures instruments, not AMM-pool prices. [1] | Use time-series momentum only to motivate a baseline and testable hypothesis. Do not claim that the finding establishes DeFi or post-cost performance. |
| One AMM family can be described as `Uniswap v2/v3-type` with a single constant-product engine | **Incorrectly generalized.** Uniswap identifies a v2 constant-product invariant, while v3 swaps move through ticks and a price limit; v4 additionally supports hooks. [2] | First release must select **one protocol/version**. Implement either v2 reserve-state simulation or v3 tick/liquidity-state simulation. Do not combine the models. |
| Price impact rises when trade size is large relative to pool liquidity | **Verified.** Uniswap documents that less available liquidity at a price implies higher impact for a given size. [2] | Model impact from the protocol-version-specific state at the actual execution block. |
| Historical gas can be expressed as base fee plus priority fee | **Incomplete.** For EIP-1559, paid cost depends on gas used and the effective gas price. [3] | Use `gas_used × effective_gas_price`, preserve the transaction type, then value ETH in USD using a source and timestamp fixed in the experiment charter. |
| Chainlink records need a round ID and time | **Verified but incomplete.** `latestRoundData` returns round ID, answer, `startedAt`, and `updatedAt`; Chainlink also requires consumer-defined freshness handling. [4] [5] | Preserve proxy and aggregator identity, decimals, all round fields, retrieval block, and configured heartbeat/deviation context. |
| A constant MEV or sandwich haircut is a cost | **Not a universal protocol fact.** Pending transactions can experience execution uncertainty, but an adverse haircut is a stress-model assumption. [2] | Define zero, base, and stress scenario haircuts; document calibration sample and do not represent the haircut as measured unless it was measured. |
| `Embargo` removes overlapping observations | **Terminology is incomplete.** Purging and embargoing have distinct functions in financial-ML practice. | Purge training labels that overlap a held-out interval. Apply an embargo interval after a test block when required by the feature/label dependence design. State the label horizon and embargo length in the charter. |
| The 2019 SEC digital-asset framework is the current primary source | **Outdated.** The SEC labels it withdrawn and superseded by its 2026 interpretive release. [6] [7] | Cite the current 2026 SEC/CFTC interpretation, then obtain legal review for fact-specific token, product, marketing, and operational questions. |
| Paper-only activity categorically establishes an unregulated research posture | **Too categorical.** FinCEN explains that money-transmitter analysis depends on facts and circumstances, including actual acceptance and transmission of value. [8] | State that no-custody/no-signing design removes specified operational features; it does not determine every legal consequence. |
| OFAC screening applies identically regardless of context | **Overbroad.** OFAC describes obligations for U.S. persons and others subject to OFAC jurisdiction and calls for risk-based controls. [9] | Require counsel-led sanctions review before live activity and a documented risk-based control design for any applicable live scope. |
| Paper-traded swaps are taxable digital-asset transactions | **Incorrect.** IRS Notice 2014-21 addresses actual sales, exchanges, and payments using convertible virtual currency. [10] | Maintain a forward-compatible simulated ledger, clearly flagged as non-tax, non-executed activity. |

## 2. Corrected product boundary

The first release is an **offline research and isolated paper-trading service**. It reads historical data, builds point-in-time features, produces a bounded target weight, and writes simulated outcomes to an audit ledger. The system shall have no signing key, wallet integration, private-key secret, live transaction broadcaster, or funded RPC execution path in any environment.

| Included in release 1 | Excluded from release 1 |
|---|---|
| One named EVM chain | Cross-chain transfer and bridging logic |
| One named protocol and version | Multi-venue routing, aggregator routing, or v4 hooks |
| Two to five predeclared liquid pools | Long-tail token universe selection |
| Daily or four-hour decision cadence | Mempool, sub-block, or latency-sensitive strategies |
| Historical simulation and paper ledger | Live transaction construction, signing, or broadcast |
| Deterministic risk layer and human kill switch | Third-party assets, custody, or discretionary advice |

A configuration record must state the chain ID, protocol version, contract addresses, token decimals, fee tier, canonical data sources, decision cadence, finality policy, and cost-policy version. A run that cannot resolve this configuration exactly shall fail closed.

## 3. Version-specific market and historical-data contract

Every raw record must be immutable and content-addressed. Derived tables must preserve source dataset IDs, transformation version, source block number, source block hash, chain ID, and `available_at_utc`. A feature is eligible at decision block `B` only if every input was available under the configured finality policy at or before `B`.

| Dataset | Mandatory fields | Quality and point-in-time control |
|---|---|---|
| Canonical blocks | `chain_id`, `block_number`, `block_hash`, `parent_hash`, `block_timestamp`, `finality_status`, `ingested_at_utc` | Reconcile canonical hashes after the configured confirmation/finality condition. Store superseded records rather than overwrite them. |
| Protocol events | `tx_hash`, `log_index`, `contract_address`, event name, decoded fields, block identifiers | Enforce `(chain_id, tx_hash, log_index)` uniqueness. Compare event counts and hashes to an independent source; investigate discrepancies above a chartered threshold. |
| v2 pool state | token addresses/decimals, reserves, fee configuration, swap and sync event state | Use only for a v2 scope. Require positive reserves, correct token ordering, and a reconstructable state transition. |
| v3 pool state | token addresses/decimals, fee tier, `sqrtPriceX96`, tick, active liquidity, initialized ticks crossed, swap state | Use only for a v3 scope. Preserve the tick/liquidity state needed to simulate a trade over its complete price path. A single reserve pair is insufficient. [2] [11] |
| Oracle reference | proxy address, aggregator address/version, decimals, round ID, answer, `startedAt`, `updatedAt`, retrieval block | Check answer reasonableness and freshness against a pool-specific policy. Chainlink explains that feeds are not streaming and may follow heartbeat/deviation update behavior. [4] [5] |
| Fee and gas state | transaction type, gas used, base fee, priority fee, effective gas price, ETH/USD reference source and timestamp | Never infer a universal gas value. Record the historical execution block or a declared delay block. |
| Reference configuration | ABI/source version, pool fee tier, token metadata validity interval, source endpoints | Version every change and reject unknown metadata at a decision block. |

### Finality and availability rules

The selected chain must define a `finality_policy_id`. For example, the policy may require a configured number of confirmations or a chain-native finalized-block condition. The policy must also define the response to a changed canonical block hash: mark affected derived records invalid, re-ingest the chain segment, rebuild dependent features, and retain an audit record of the correction.

The model dataset must include three separate time fields: **market time** (`block_timestamp`), **system availability time** (`available_at_utc`), and **research ingestion time** (`ingested_at_utc`). This prevents a historical reconstruction from silently using data that would not have been available at the simulated decision time.

## 4. Correct execution and cost simulation

### 4.1 Protocol-version gate

The exact-input reserve formula below applies only to a v2-style constant-product pool. Let `x` and `y` be pre-swap reserves, `dx` the input quantity, and `f` the pool fee fraction. The fee-adjusted input is:

```text
dx_effective = dx × (1 − f)
dy_quoted = y × dx_effective / (x + dx_effective)
```

A v2 simulation may calculate the immediate quoted execution rate as `dy_quoted / dx` and compare it with the pre-trade marginal price `y / x`. Its formula, fee behavior, token ordering, and state transition must be unit-tested against known historical swaps. Uniswap states that v2 enforces the constant-product invariant after fees. [2]

A v3 simulation **must not substitute this v2 formula**. It must use the pool’s price, active liquidity, initialized ticks, fee tier, and tick-crossing logic along the simulated swap path. Uniswap’s own description distinguishes v3 swaps through ticks and a price limit. [2] A v3 research release that cannot reconstruct this state shall limit itself to signal research and shall not report executable PnL.

### 4.2 Cost ledger

Each attempted paper trade shall produce a row with the following minimum fields:

| Component | Required representation |
|---|---|
| Decision | decision block, decision timestamp, score, target weight, risk-config version |
| Proposed trade | pool, token direction, input size, reference price, maximum acceptable impact/slippage |
| Execution state | configured delay, attempted execution block, state provenance, finality-policy status |
| AMM quote | quoted output, effective execution price, protocol fee, price impact, model-version ID |
| Gas | gas-used assumption, EIP-1559 effective gas price, ETH/USD reference, USD cost |
| Adverse scenarios | MEV haircut scenario ID, liquidity-shock scenario ID, outage/reorg scenario ID |
| Outcome | filled, reverted, rejected-before-submit, or unavailable; reason code; simulated PnL impact |

For an EIP-1559 transaction, the cost engine shall use `gas_used × effective_gas_price`; EIP-1559 defines the base fee, priority fee, maximum fee, and effective gas-price treatment. [3] A rejected swap should not be recorded as filled. If the paper model represents an attempted onchain transaction that would revert, the charter must state whether simulated gas is charged and why. The same rule must apply in all folds.

MEV is a stress dimension, not a single factual constant. The charter shall define at least `zero`, `base`, and `stress` adverse-execution scenarios. It shall state whether the base haircut is measured from a named historical sample or is merely a conservative assumption. A model may not pass because it performs only under the zero-haircut scenario.

## 5. Signal, label, and validation specification

The model emits a **score**, not an order. A deterministic sizing function converts the score into a capped target weight only after the independent risk layer approves the decision.

### 5.1 Model hierarchy

The first required strategy is a deterministic trend baseline using predeclared trailing-return or moving-average rules. A regularized linear or logistic model and a shallow gradient-boosted model may be tested only as comparators. This sequencing addresses the documented risk that searching many backtests and parameters can inflate selected performance. [12] [13]

The label must state precisely: the decision block `B`, holding horizon `H`, reference exit-state rule, whether the label includes costs, and the exact data required to form it. A label that reaches from `B` to `B+H` is unavailable at `B`; it can be used only for retrospective training/evaluation and must not leak into features or model selection.

### 5.2 Chronological evaluation

| Control | Correct requirement |
|---|---|
| Splits | Use rolling or expanding chronological windows. Never randomize observations across time. |
| Final holdout | Reserve one immutable, chronologically latest holdout period before broad model selection. Do not tune against it. |
| Purging | Remove training observations whose label intervals overlap a validation/test interval. |
| Embargoing | Remove a configured time interval after a test interval when required by the feature/label dependency design. |
| Costs | Apply the same versioned impact, gas, slippage, delay, and adverse-execution model to every candidate and baseline. |
| Trial accounting | Log every tested model, feature set, hyperparameter set, and acceptance decision. Use a multiple-testing control such as a documented Deflated Sharpe Ratio or a comparable method. [13] |
| Failure scenarios | Replay data staleness, changed canonical blocks, indexer/RPC unavailability, and predeclared liquidity shocks. |

The original time-series-momentum reference reports return persistence in its own liquid-futures sample at horizons from one to 12 months and partial reversal at longer horizons. [1] It does not validate a four-hour AMM strategy. Therefore the cadence, feature windows, and universe must be treated as **unproven implementation parameters**.

### 5.3 Acceptance gates

No numerical return target is fixed in this generic document. Instead, the experiment charter must predeclare all thresholds before training. Progress from backtesting to paper operation requires all of the following:

1. The deterministic baseline and every ML comparator are reproducible from immutable data and a locked configuration.
2. The selected ML comparator meets the chartered statistical and economic criteria **net of all stated costs** across the predeclared out-of-sample windows; it must not merely beat the baseline pre-cost.
3. Results remain within the chartered tolerance under delayed execution, liquidity-shock, and adverse-execution scenarios.
4. Data-integrity, finality/reorg, and failure-scenario tests pass without manual deletion of inconvenient periods.
5. The trial log and holdout report are complete. The final holdout remains untouched until a formal release decision.

## 6. Deterministic control plane and paper-operation controls

The control plane must execute independently of the score and must fail closed on unknown configuration, stale data, missing metadata, non-final data, or breached risk limits.

| Control | Enforceable rule |
|---|---|
| Freshness | Reject the cycle if required pool or oracle inputs exceed the pool-specific maximum age. |
| Canonicality | Reject the cycle when source blocks do not meet `finality_policy_id` or the block-hash reconciliation fails. |
| Exposure | Cap gross and net target exposure per pool and for the aggregate paper portfolio. |
| Liquidity | Cap input size by a protocol-version-specific liquidity measure; for v3, do not use a v2 reserve proxy. |
| Volatility | Apply a predeclared volatility scaler with minimum/maximum bounds. |
| Turnover | Cap decision-to-decision gross notional and count of attempted swaps. |
| Kill switch | Support human activation and automatic triggers. The kill-switch configuration must be versioned, tested, and applied before any paper execution. |
| Credential isolation | CI, research, and paper environments must contain no wallet secret, private key, funded signer, or live broadcast client. |
| Auditability | Write immutable decision, risk, execution-simulation, and configuration records for every accepted or rejected cycle. |

A paper service shall operate for a predeclared observation period, with daily reconciliation of inputs, simulated holdings, and configuration changes. It must label all reports `SIMULATED — NOT EXECUTED`.

## 7. Current U.S. legal and policy issue register

The following is a general source map, not a legal determination. Counsel must assess actual token taxonomy, transactions, users, jurisdictions, marketing, and operational design before live scope is considered.

| Expansion trigger | Current primary source position | Engineering response |
|---|---|---|
| Token classification or offers/sales | The 2019 SEC framework is withdrawn; the effective 2026 SEC interpretive release and associated CFTC guidance are the current cited materials. [6] [7] | Retain token/venue evidence and request fact-specific securities and commodities analysis. |
| Acceptance/transmission or custody of value | FinCEN says money-transmitter status depends on facts and circumstances; it specifically distinguishes development/sale of software from business activity that accepts and transmits value. [8] | Do not add wallets, signing, user funds, settlement, or routing without an AML/BSA and state-law review. |
| Advising outside investors or operating a pool | CFTC materials show that exemptions/exclusions depend on applicable facts and conditions. [14] | Require a CPO/CTA and investment-adviser review before serving external users or capital. |
| Consumer-facing ML or earnings claims | FTC Operation AI Comply demonstrates enforcement attention to alleged deceptive AI and earnings claims. [15] | Prohibit unsupported profitability, passive-income, or guaranteed-return language. Require documented substantiation and legal review for public claims. |
| AI-policy discussion | EO 14365 directs executive-branch actions concerning a national AI policy framework, potential challenges to state laws, possible funding conditions, a contemplated FTC policy statement, and legislative recommendations. It does not itself create a private enforceable right. [16] | Treat this as policy context only; it does not displace financial, consumer-protection, state-law, or other obligations. |
| Sanctions | OFAC states that U.S. persons and others subject to its jurisdiction must avoid unauthorized prohibited transactions and calls for tailored, risk-based compliance controls. [9] | Before any live activity, create a counsel-approved, jurisdiction-specific sanctions-control plan. |
| Tax and records | IRS Notice 2014-21 treats convertible virtual currency as property and describes tax consequences for actual sale, exchange, and payment activity. [10] | Keep simulated paper records separate from real transaction records. If live scope is later approved, obtain tax guidance and add lot, basis, fair-value, and disposition fields. |

## 8. Implementation sequence and testable deliverables

| Stage | Deliverable | Mandatory gate |
|---|---|---|
| 0. Protocol lock | Named chain, protocol version, pools, contract addresses, finality policy, cost-policy version | No mixed v2/v3 data model; protocol-specific test plan approved. |
| 1. Experiment charter | Hypothesis, baseline, label, features, decision cadence, costs, scenarios, acceptance gates, trial-accounting rule | Charter immutable before training. |
| 2. Raw-data ingest | Block/event/oracle/gas records plus source manifests | Dual-source reconciliation, canonical-hash, schema, and availability-integrity tests pass. |
| 3. State reconstruction | v2 reserve engine **or** v3 tick/liquidity engine | Historical state transitions reproduce a predeclared sample of known events. |
| 4. Baseline backtest | Deterministic trend strategy with all cost scenarios | Reproducible report with no undocumented parameter changes. |
| 5. ML comparison | Limited, logged model comparisons | Net-of-cost out-of-sample evaluation, failure scenarios, and multiple-testing control complete. |
| 6. Isolated paper service | Continuous simulated decision and ledger service | No credentials/live path; reconciliation and kill-switch drills pass. |
| 7. Expansion review | Security, legal, sanctions, tax, and operational reviews | Required before any live-scope design discussion. |

## 9. Definition of done

The specification is implemented correctly only when the repository can demonstrate the following evidence: a reproducible run manifest; raw-source hashes; a versioned point-in-time dataset; protocol-version-specific state reconstruction tests; cost-model unit tests; a chronological fold map; full trial history; out-of-sample and scenario reports; deterministic-control logs; successful kill-switch tests; and an isolated paper-trading ledger. Absence of any item means the release remains in research status.

## References

[1]: [Moskowitz, Ooi, and Pedersen, *Time Series Momentum*, Journal of Financial Economics (2012)](https://www.sciencedirect.com/science/article/pii/S0304405X11002613)
[2]: [Uniswap Developers, *Swaps*](https://developers.uniswap.org/docs/get-started/concepts/traders/swaps)
[3]: [Ethereum Improvement Proposal 1559, *Fee Market Change for ETH 1.0 Chain*](https://eips.ethereum.org/EIPS/eip-1559)
[4]: [Chainlink, *Data Feeds API Reference*](https://docs.chain.link/data-feeds/api-reference)
[5]: [Chainlink, *Data Feeds*](https://docs.chain.link/data-feeds)
[6]: [SEC, *Application of the Federal Securities Laws to Certain Types of Crypto Assets and Certain Transactions Involving Crypto Assets*, Release 33-11412](https://www.sec.gov/rules-regulations/2026/03/s7-2026-09)
[7]: [CFTC, *CFTC Joins SEC to Clarify the Application of Federal Securities Laws to Crypto Assets*](https://www.cftc.gov/PressRoom/PressReleases/9198-26)
[8]: [FinCEN, FIN-2019-G001, *Application of FinCEN’s Regulations to Certain Business Models Involving Convertible Virtual Currencies*](https://www.fincen.gov/system/files/2019-05/FinCEN%20Guidance%20CVC%20FINAL%20508.pdf)
[9]: [OFAC, *Questions on Virtual Currency*](https://ofac.treasury.gov/faqs/topic/1626)
[10]: [IRS, Notice 2014-21, *Virtual Currency Guidance*](https://www.irs.gov/pub/irs-drop/n-14-21.pdf)
[11]: [Uniswap Developers, *Uniswap v3 Architecture*](https://developers.uniswap.org/docs/protocols/v3/concepts/architecture)
[12]: [Bailey, Borwein, López de Prado, and Zhu, *The Probability of Backtest Overfitting*](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253)
[13]: [Bailey and López de Prado, *The Deflated Sharpe Ratio*](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
[14]: [CFTC, *CPO and CTA Exemptions and Exclusions*](https://www.cftc.gov/sites/default/files/tm/tmcpo_cta_exemptions.htm)
[15]: [FTC, *Operation AI Comply: Crackdown on Deceptive AI Claims and Schemes*](https://www.ftc.gov/news-events/news/press-releases/2024/09/ftc-announces-crackdown-deceptive-ai-claims-schemes)
[16]: [The White House, Executive Order 14365, *Ensuring a National Policy Framework for Artificial Intelligence*](https://www.whitehouse.gov/presidential-actions/2025/12/eliminating-state-law-obstruction-of-national-artificial-intelligence-policy/)
