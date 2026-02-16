# Evaluation Rubric

## Task Quality (40%)

| Score | Criteria |
|-------|----------|
| **Excellent** | Instructions are clear, unambiguous, and well-structured. Task scope is appropriate (solvable in 15-45 min by a skilled engineer). Scenario is realistic and tests genuine SWE skills (debugging, implementation, integration). |
| **Good** | Instructions are mostly clear with minor ambiguities. Scope is reasonable. Task tests relevant skills. |
| **Adequate** | Instructions need some interpretation. Scope is slightly too easy or too hard. Task is somewhat contrived. |
| **Poor** | Instructions are vague or confusing. Scope is way off (trivial or impossibly hard). Task feels like a toy problem. |

## Test Coverage (30%)

| Score | Criteria |
|-------|----------|
| **Excellent** | Tests cover the main path, edge cases, and error handling. Failure messages are informative and pinpoint what went wrong. Tests reliably reject incorrect or incomplete solutions. |
| **Good** | Tests cover main path and some edge cases. Most failure messages are helpful. Tests catch most incorrect solutions. |
| **Adequate** | Tests cover the main path. Failure messages are generic. Some incorrect solutions could pass. |
| **Poor** | Tests only check a trivial case. No edge cases. Incorrect solutions could easily pass. |

## Solution Correctness (15%)

| Score | Criteria |
|-------|----------|
| **Excellent** | Reference solution passes all tests. Code is clean, minimal, and well-structured. Solution demonstrates good engineering practices. |
| **Good** | Solution passes all tests. Code is readable and reasonable. |
| **Adequate** | Solution passes most tests. Code works but is messy or over-engineered. |
| **Poor** | Solution does not pass all tests, or is fundamentally broken. |

## Harbor Format Compliance (15%)

| Score | Criteria |
|-------|----------|
| **Excellent** | All files present and correctly structured. task.toml has accurate metadata. Dockerfile builds cleanly. test.sh correctly writes reward to `/logs/verifier/reward.txt`. Everything works end-to-end with Docker. |
| **Good** | All files present. Minor metadata issues. Docker workflow works. |
| **Adequate** | Missing optional metadata. Dockerfile or test.sh needs minor fixes to work. |
| **Poor** | Missing required files. Docker build fails. Reward not written correctly. |
