# Practical Work 6 - Comparison of Task 1 and Task 2

## Comparison table

| # | Criterion | Task 1: Baseline MVP | Task 2: AI-assisted version | Conclusion |
|---|---|---|---|---|
| 1 | Development speed | Slower manual implementation | Faster initial implementation | AI improves speed |
| 2 | Architecture consistency | Depends on developer discipline | Improved with iterative prompt refinement | AI helps, but still needs review |
| 3 | Authentication quality | Secure after manual design | Secure after AI generation plus review | Equal only after review |
| 4 | Access control quality | Explicitly designed and tested | AI proposed structure, manual tests confirmed correctness | Human validation remains mandatory |
| 5 | Input validation | Added deliberately | Generated quickly from prompt requirements | AI accelerates repetitive validation work |
| 6 | Logging quality | Manual secure logging design | AI assisted with coverage ideas and redaction patterns | AI useful for completeness |
| 7 | OWASP awareness | Manual mapping to risks | Faster mapping and remediation checklist generation | AI helps with breadth |
| 8 | Dependency hygiene | Manual pinning and audit | AI suggested pinned dependencies and checks | Similar outcome |
| 9 | Exception handling | Manual neutralization of errors | AI highlighted leak-prone paths | AI useful for edge-case review |
| 10 | Test generation | Manual writing effort | AI assisted in drafting security-focused tests | AI improves coverage speed |
| 11 | Deployment readiness | Manual Compose and health design | AI assisted with Dockerfile and healthcheck boilerplate | AI accelerates deployment artifacts |
| 12 | Risk of insecure defaults | Medium | Higher if generated code is accepted blindly | AI increases review burden |

## Summary conclusions

1. AI-assisted development reduced implementation time.
2. AI-assisted development improved throughput for boilerplate, validation, tests, and documentation.
3. Security quality did not improve automatically from AI usage alone.
4. The decisive factor remained review against Secure SDLC and OWASP Top 10.
5. AI was most useful as a force multiplier, not as a substitute for security engineering judgment.
