# NetMedic decision log

Every meaningful technical choice gets an entry, newest at the bottom. Keep entries short. This log
doubles as interview preparation: each entry is an answer to "why did you do it that way?"

## Format

```
## D-000: Title
- **Date / lesson:** YYYY-MM-DD, L#
- **Decision:** what we chose
- **Alternatives:** what else was realistic
- **Why:** the deciding reasons and trade-offs accepted
- **Revisit if:** what would make us change our mind
```

---

## D-001: Simulated network with injected faults
- **Date / lesson:** 2026-11-19, spec
- **Decision:** build a seeded network simulator and inject faults whose root cause is recorded.
- **Alternatives:** real network gear or a home lab; public network datasets; scripted fake answers.
- **Why:** injected faults give ground truth, so a non-deterministic agent can be scored. Seeding
  makes every scenario reproducible. No hardware is needed.
- **Revisit if:** we get access to a real Mist API sandbox to add a live demo.

## D-002: LangGraph as the agent framework
- **Date / lesson:** 2026-11-19, spec
- **Decision:** LangGraph.
- **Alternatives:** LangChain agents, Claude Agent SDK, a hand-written loop.
- **Why:** it's the framework named in the HPE posting. Its explicit graph (nodes, edges, state)
  makes the verify-and-retry loop and step budgets easy to express and trace. L6 still builds a
  hand-written loop first, to understand what the framework automates.
- **Revisit if:** a requirement can't be expressed cleanly as a graph.

## D-003: MCP server over streamable HTTP
- **Date / lesson:** 2026-11-19, spec
- **Decision:** expose network tools through an MCP server (official Python SDK, FastMCP) using the
  streamable HTTP transport, loaded into LangGraph with `langchain-mcp-adapters`.
- **Alternatives:** plain LangChain tools in the agent process; MCP over stdio.
- **Why:** MCP is a posting requirement. HTTP lets the server run as its own versioned,
  independently deployed service in Kubernetes. Stdio only works when the server is a child process.
- **Revisit if:** local development over HTTP becomes painful (stdio can be used locally).

## D-004: Claude through the Anthropic API
- **Date / lesson:** 2026-11-19, spec
- **Decision:** Anthropic API for development.
- **Alternatives:** AWS Bedrock, OpenAI, local open models.
- **Why:** strong tool calling and structured output, simple setup. The same models are on Bedrock
  for the optional AWS version.
- **Revisit if:** cost becomes a problem in full eval runs (try a smaller model for the verify step
  and the judge).

## D-005: Postgres + pgvector for retrieval
- **Date / lesson:** 2026-11-19, spec
- **Decision:** pgvector for vectors and Postgres full-text search for keywords, in one database.
- **Alternatives:** OpenSearch (named in the posting), Chroma, Qdrant.
- **Why:** Oscar already knows Postgres well, and one database does both halves of hybrid search.
  The retrieval code sits behind an interface so OpenSearch Serverless can replace it in the AWS
  version.
- **Revisit if:** we do the AWS stretch goal.

## D-006: kind for Kubernetes
- **Date / lesson:** 2026-11-19, spec
- **Decision:** run Kubernetes locally with kind.
- **Alternatives:** minikube, k3d, a managed cloud cluster (EKS).
- **Why:** free, runs in Docker, and the same manifests work on a real cluster.
- **Revisit if:** we do the AWS stretch goal.

## D-007: Python 3.13
- **Date / lesson:** 2026-11-20, L0
- **Decision:** Python 3.13, managed by uv (`.python-version`, `requires-python = ">=3.13"`).
- **Alternatives:** 3.12 (the original spec; security fixes only, ends Oct 2028); 3.14 (fine, adds
  nothing we need); 3.15 (released Oct 2026, some packages may not ship wheels yet).
- **Why:** every planned dependency supports it, security support runs to Oct 2029, and it was
  already installed. Its headline features (free-threading, JIT) don't matter for an I/O-bound
  agent; the rule is "newest version all dependencies support".
- **Revisit if:** a dependency lacks 3.13 wheels, or we want 3.14 later (switching is cheap:
  `.python-version`, `requires-python`, `uv sync`).

## D-008: One installable package in the src layout
- **Date / lesson:** 2026-11-20, L0
- **Decision:** keep uv 0.13's default: a packaged project (`uv_build` backend) with code in
  `src/netmedic/`, one subpackage per service, tests in `tests/` at the root, and a `netmedic`
  console script. The spec's repo tree was updated to match.
- **Alternatives:** flat, unpackaged folders at the root (the original spec; `uv init --no-package`);
  one project per service.
- **Why:** imports work from anywhere (tests, scripts, containers) without path tweaks; tests run
  against the installed package; the CLI entry point comes for free in L8; one `netmedic.`
  namespace avoids clashes for generic names like `agent` or `evals`. Cost: longer import paths.
- **Revisit if:** per-service images in week 3 need separate dependency sets (use optional
  dependency groups first, before splitting projects).

## D-009: LF line endings enforced by `.gitattributes`
- **Date / lesson:** 2026-11-20, L0
- **Decision:** `* text=auto eol=lf` in a committed `.gitattributes`; CRLF only for
  `.ps1`/`.bat`/`.cmd`. Secrets in a git-ignored `.env`, documented by a committed `.env.example`.
- **Alternatives:** git's per-machine `core.autocrlf` setting; no normalization.
- **Why:** development is on Windows, but CI and Docker images are Linux. CRLF breaks shell scripts
  in containers and makes diffs noisy. `.gitattributes` travels with the repo, so every clone and
  CI runner behaves the same, whatever its local git config.
- **Revisit if:** never likely; add patterns if new Windows-only file types appear.

## D-010: Tool configuration (ruff 0.17, pytest 9)
- **Date / lesson:** 2026-11-20, L0
- **Decision:** ruff with line length 100 and rule families `E`, `F`, `I`, `UP`, `B`; keep ruff's
  default of also formatting Python code blocks in Markdown. pytest configured in the native-TOML
  `[tool.pytest]` table with `testpaths = ["tests"]`, `--import-mode=importlib` and `strict = true`.
- **Alternatives:** black + flake8 + isort; more ruff rule families from day one; restrict ruff to
  `*.py`; pytest's legacy `[tool.pytest.ini_options]` table and default `prepend` import mode.
- **Why:** a small rule set catches real bugs without noise. Formatting doc examples keeps them in
  the same style as real code (see bug B-001 in the study notes). `importlib` mode avoids clashes
  between same-named test files; `strict` turns config and marker typos into errors.
- **Revisit if:** we want stricter linting (`SIM`, `RUF`) once there is real code.
