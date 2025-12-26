# GEMINI Workflow Instructions
## Massively Decomposed Agentic Process (MDAP) Framework

This document defines the workflow that should be followed for all complex tasks based on the research paper "Solving a Million-Step LLM Task with Zero Errors" and the MAKER framework.

---

## Core Principles

> [!IMPORTANT]
> The fundamental principle is to achieve **extreme task decomposition** combined with **systematic error correction** to enable reliable execution of complex, multi-step tasks.

### Three Pillars of MDAP

1. **Maximal Agentic Decomposition (MAD)**
2. **First-to-ahead-by-K Error Correction**
3. **Red-flagging for Risk Mitigation**

---

## 1. Maximal Agentic Decomposition (MAD)

### Principle
Break down every complex task into the **smallest possible subtasks**, where each subtask represents a single, focused step that can be executed independently.

### Implementation Guidelines

#### Task Breakdown
- **Decompose to the extreme**: Instead of tackling a task with `s` steps as a monolithic unit, create `s` separate micro-tasks
- **Assign micro-roles**: Each agent/step should have a single, well-defined responsibility (avoid anthropomorphizing with human-level roles)
- **Minimize context**: Each subtask should require minimal context to execute correctly
- **Enable focus**: Design subtasks so that an agent can focus entirely on one specific action without confusion

#### Benefits
- **Reduced context burden**: Each LLM call operates on limited, relevant context
- **Improved reliability**: Smaller, focused tasks have higher per-step accuracy
- **Better error isolation**: Failures are localized to specific subtasks
- **Scalability**: Enables use of smaller, more efficient models

#### Workflow Structure
```
For a task with s steps:
- Create s subtasks (m = 1, where m = steps per subtask)
- Each subtask receives: current state (x_i) → produces: action (a_i) and next state (x_i+1)
- Chain subtasks: x_0 → [subtask_1] → x_1 → [subtask_2] → ... → x_s
```

> [!TIP]
> Ask yourself: "Can this task be broken down further?" If yes, decompose it more.

---

## 2. First-to-ahead-by-K Error Correction

### Principle
Use **voting among multiple independent attempts** to ensure correctness at each subtask level. The modularity from MAD makes this efficient and effective.

### Voting Algorithm

#### How It Works
1. For each subtask, generate multiple independent solutions
2. Count votes for each unique solution
3. Accept the first solution that is ahead by `k` votes
4. If formatted incorrectly, discard and resample (red-flagging)

#### Parameters
- **k**: The "ahead-by" threshold (commonly k=2 or k=3)
  - Higher k = more certainty but more API calls
  - Lower k = faster but less certainty
  
#### Pseudocode
```
For each step:
  Vote_counts ← empty map
  While True:
    solution ← get_vote(current_state, model)
    if solution has red_flags:
      continue  # Skip and resample
    Vote_counts[solution] += 1
    if Vote_counts[solution] >= k + max(other_votes):
      return solution  # This is the winner
```

### Critical Conditions
- **Subtasks must be small enough** that a correct solution is likely to be sampled
- **No incorrect solution should be more likely** than the correct one
- **Solutions must be comparable** (can detect when two solutions are the same)

> [!WARNING]
> Voting only works effectively with proper task decomposition. Without MAD, voting becomes prohibitively expensive.

---

## 3. Red-flagging

### Principle
Immediately discard any response that shows **high-level indicators of risk**, particularly format errors that may correlate with reasoning errors.

### Red Flag Indicators

#### Format Violations
- Incorrect output structure
- Missing required fields
- Unparseable responses
- Invalid syntax

#### Why Format Matters
When an agent makes a **format error**, it often indicates:
- The agent didn't understand the task correctly
- The reasoning process was flawed
- Higher likelihood of **correlated errors** (multiple agents making the same mistake)

### Implementation
```
get_vote(state, model):
  While True:
    response ← model(prompt(state))
    if has_no_red_flags(response):
      return parse_action(response), parse_next_state(response)
    # else: discard and resample
```

> [!CAUTION]
> Do NOT attempt to "fix" malformed outputs. Discard them entirely and resample. A format error is a warning sign of deeper issues.

---

## Complete MDAP Workflow

### Step-by-Step Process

#### Phase 1: Task Analysis and Decomposition
1. **Understand the full task**
   - What is the overall goal?
   - What are the success criteria?
   - How many total steps are estimated?

2. **Identify decomposition boundaries**
   - What is the smallest meaningful unit of work?
   - What state information must be passed between steps?
   - What makes two steps independent?

3. **Design the subtask template**
   - Define input format (state x_i)
   - Define output format (action a_i and next state x_i+1)
   - Create prompt template ϕ(x)
   - Create extractors ψ_a and ψ_x

#### Phase 2: Implementation
1. **Create micro-agents**
   - One agent type per subtask type
   - Each agent has a single, focused role
   - Agents are stateless (receive all needed context in input)

2. **Implement voting mechanism**
   - Set k value (start with k=2 or k=3)
   - Implement vote counting
   - Implement "first-to-ahead-by-k" logic

3. **Define red flags**
   - List all format requirements
   - Create validation function
   - Implement retry logic

#### Phase 3: Execution
```
Initialize: current_state ← initial_state, actions ← []

For each step from 1 to s:
  1. Generate votes using do_voting(current_state, model, k)
  2. Accept winning action
  3. Append action to actions list
  4. Update current_state
  5. Continue to next step

Return: actions (complete solution)
```

#### Phase 4: Verification
1. **Validate the complete solution**
   - Does it satisfy all requirements?
   - Are there any errors in the sequence?
   
2. **Measure performance**
   - Success rate
   - Number of API calls
   - Cost efficiency

---

## Practical Guidelines

### When to Use MDAP

✅ **Use MDAP when:**
- Task requires hundreds or thousands of dependent steps
- Error tolerance is very low or zero
- Each step has a clear, verifiable correct answer
- Task can be decomposed into similar repeated subtasks

❌ **Consider alternatives when:**
- Task has fewer than 10-20 steps
- Creative/subjective outputs are needed
- Steps are highly dissimilar and require different expertise
- Real-time response is critical

### Model Selection

> [!TIP]
> You don't need state-of-the-art reasoning models! Smaller, non-reasoning models often suffice when combined with proper decomposition and error correction.

**Recommended approach:**
1. Start with efficient models (e.g., GPT-4-mini, Claude Haiku)
2. Test per-step accuracy
3. Only upgrade to more expensive models if necessary
4. The voting mechanism compensates for individual model weaknesses

### Cost Optimization

**Cost = (steps × votes_per_step × cost_per_call)**

Where `votes_per_step` depends on:
- k value (ahead-by threshold)
- Red flag frequency
- Per-step error rate

**Optimization strategies:**
1. Minimize k while maintaining reliability
2. Reduce red flag frequency through better prompts
3. Use cheaper models where possible
4. Cache and reuse common subtask patterns

---

## Error Handling

### Types of Errors

1. **Format Errors** (Red flags)
   - Action: Discard and resample
   - Never try to fix or parse

2. **Reasoning Errors** (Incorrect but well-formatted)
   - Action: Voting mechanism handles this
   - Correct answer should win

3. **Correlated Errors** (Multiple agents make same mistake)
   - Action: Red-flagging reduces this
   - May require k increase

### Debugging Failed Tasks

If a task fails completely:
1. Check decomposition granularity (are subtasks small enough?)
2. Verify voting parameter k (may need to increase)
3. Review red flag criteria (too strict or too lenient?)
4. Examine prompt template clarity
5. Test per-step accuracy in isolation

---

## Mathematical Formulation

### Probability of Success

For a task with `s` steps, for each step with per-step accuracy `p`:

**Single-agent (no error correction):**
```
P(success) = p^s
```
This decays exponentially → guaranteed failure for large s

**With voting (MDAP):**
```
P(success_per_step) ≈ 1 - (1-p)^n (for n votes)
```
With proper k, can achieve near-100% per-step accuracy → P(success) ≈ 1 even for s = 1,000,000

### Scaling Laws

**Key insight:** Even small improvements in per-step accuracy lead to **exponential improvements** in achievable task lengths.

Example:
- 99% per-step accuracy → fails after ~100 steps
- 99.99% per-step accuracy → succeeds at 10,000+ steps
- MDAP with voting → succeeds at 1,000,000+ steps

---

## Template for Task Execution

```markdown
## Task: [Task Name]

### 1. Decomposition
- Total estimated steps: [s]
- Subtask granularity: [m steps per subtask]
- State representation: [description]
- Action format: [description]

### 2. Subtask Definition
**Input (x_i):**
- [field 1]: [description]
- [field 2]: [description]

**Output (a_i, x_i+1):**
- Action: [format]
- Next state: [format]

### 3. Voting Configuration
- k value: [2 or 3]
- Red flags: [list criteria]

### 4. Execution Plan
1. Initialize with [initial state]
2. For each of [s] steps:
   - Generate votes
   - Apply red-flagging
   - Accept winner
3. Verify complete solution

### 5. Success Criteria
- [criterion 1]
- [criterion 2]
```

---

## Key Takeaways

> [!IMPORTANT]
> **Multi-Agent Advantage**: Some problems are fundamentally unsolvable by a single monolithic agent but become solvable through massively decomposed agentic processes.

### The MDAP Paradigm Shift

**Traditional AI Scaling:**
- Make LLMs smarter and smarter
- More parameters, more training, more reasoning
- Expensive and incremental

**MDAP Scaling:**
- Keep LLMs simple and focused
- Use extreme decomposition + error correction
- Efficient and effective for long-horizon tasks

### Success Formula

```
Extreme Decomposition + Voting + Red-flagging = Zero-Error Million-Step Tasks
```

---

## References

This workflow is based on the MAKER framework from:
**"Solving a Million-Step LLM Task with Zero Errors"**
by Meyerson et al., Cognizant AI Lab & UT Austin

Key concepts:
- **MAKER**: Maximal Agentic decomposition, first-to-ahead-by-K Error correction, and Red-flagging
- **MDAPs**: Massively Decomposed Agentic Processes
- **MAD**: Maximal Agentic Decomposition

---

## Workflow Checklist

When starting any complex task, verify:

- [ ] Task is decomposed to minimal subtasks (MAD)
- [ ] Each subtask has a clear, single responsibility
- [ ] Voting mechanism is implemented (k ≥ 2)
- [ ] Red flag criteria are defined
- [ ] State representation is minimal and clear
- [ ] Success criteria are verifiable
- [ ] Cost estimation is acceptable

**Remember:** The more complex the task, the more critical proper decomposition becomes.
