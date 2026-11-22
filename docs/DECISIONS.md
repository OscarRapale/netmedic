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

## D-011: Dataclasses inside the simulator, Pydantic at the boundaries
- **Date / lesson:** 2026-11-21, L1
- **Decision:** the simulator's network model uses standard-library dataclasses
  (`slots=True, kw_only=True`, mutable). Pydantic models appear only where data crosses a service
  boundary (simulator API, MCP tool inputs and outputs, the diagnosis report).
- **Alternatives:** Pydantic models everywhere.
- **Why:** "validate at the edges, test the inside". Tool outputs are summaries, so they need their
  own schemas anyway; keeping them separate means simulator refactors can't silently change the
  versioned MCP contract. The topology is built by our own seeded code, so tests guard it better
  than runtime validation on every object. Cost: no runtime type checks (a wrong value like
  `status = "dwon"` is accepted), covered by D-012 and tests.
- **Revisit if:** internal objects start arriving from outside (e.g. loading topologies from files).

## D-012: pyright as the static type checker
- **Date / lesson:** 2026-11-21, L1
- **Decision:** pyright (dev dependency) in `standard` mode, configured in `[tool.pyright]` for
  `src` and `tests`, resolving imports from `.venv`.
- **Alternatives:** mypy; ty (Astral, still 0.0.x beta); no type checker; pyright `strict` mode.
- **Why:** it's the engine behind Pylance, so VS Code, the terminal and CI report the same errors.
  Without a checker, "type hints everywhere" is unchecked documentation. `standard` catches real
  mistakes without strict mode's noise from partly-typed libraries.
- **Revisit if:** ty becomes stable, or we want `strict` for the simulator package only.

## D-013: Deterministic topology generation
- **Date / lesson:** 2026-11-22, L1
- **Decision:** `build_topology(seed)` in `simulator/generator.py`. Each part of the network draws
  from its own stream, `random.Random(f"{seed}:{part}")` (`"devices"`, `"clients"`). Structure
  follows a fixed plan (channel plan, WLANs, servers, pools); randomness only where real networks
  vary (PoE draw, client counts, kinds, MACs, AP choice). Plans are plain tuples and fresh objects
  are built on every call. Invariant tests run over several seeds.
- **Alternatives:** one shared random stream; the global `random` module; random channels and
  structure; module-level model objects.
- **Why:** per-part streams keep old scenarios stable when one part's generation changes. A
  planned structure keeps the healthy baseline healthy (random channels would create
  co-channel evidence, i.e. false alarms). Fresh objects prevent state leaking between topologies.
  Stream names are part of the seed and must not be renamed once scenarios exist.
- **Revisit if:** scenarios need different network shapes (move the constants to a config).

## D-014: Network model scope
- **Date / lesson:** 2026-11-22, L1
- **Decision:** readable string IDs (`ap-1-01`, `pool-2-10`) and references by ID; one DHCP pool
  per site and VLAN (addressing `10.<site>.<vlan>.0/24`, servers in `10.0.0.0/24`); pools count
  leases instead of keeping a lease table; shared DHCP/DNS/RADIUS servers; one radio per AP; no
  `Vlan` class; only in-use switch ports; client/AP positions deferred to L2; `Client.ip` and
  `Client.ap_id` are `None` when missing, because that absence is diagnostic evidence.
- **Alternatives:** UUIDs or integer IDs; object references; one pool per VLAN shared by sites;
  a MAC→IP lease table; multi-radio APs; modelling all 24 ports.
- **Why:** the LLM reads IDs and passes them back to tools, so they must be short and
  unambiguous. Each simplification is stated, not hidden: no planned fault needs the extra detail.
  The spec's example scenario was corrected to VLAN 10 (laptops are on Corp).
- **Revisit if:** a fault needs two radios, a lease table or per-port detail.
