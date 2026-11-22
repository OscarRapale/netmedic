# NetMedic lessons

The curriculum follows the 3-week plan in `SPEC.md`. Each lesson ends with a checkpoint, an
interview check and a commit. Lesson numbers are a guide: split or merge lessons as needed, and
record changes in the progress log.

## Progress log

Update this at the end of every session. Newest entry first.

| Date | Lesson | Status | Notes / next step |
| --- | --- | --- | --- |
| 2026-11-22 | L1 Network model | Done | Dataclass model in `simulator/topology.py`; seeded `build_topology()` in `simulator/generator.py` (2 sites, 6 switches, 12 APs, 3 WLANs, 6 pools, 3 servers, ~150 clients; seed 42 → 141 clients); pyright added; 30 tests (7 invariants × 4 seeds + 2 examples). Fixed missing ruff/pytest config from L0 (B-002). Decisions D-011 to D-014. Next: L2 telemetry (needs AP/client positions for RSSI) |
| 2026-11-20 | L0 Project setup | Done | uv project (Python 3.13, packaged `src/netmedic/` layout), ruff + pytest 9 config, `.gitignore`/`.gitattributes`/`.env.example`, first commit, pushed to public GitHub repo `OscarRapale/netmedic` (branch `main`). Docker Desktop running (≈6.7 GB for Docker). Next: L1 network model |
| 2026-11-19 | Setup | Starter files added | Next: Lesson 0, project setup |

**Open questions** (raised in the spec review on 2026-11-20; decide before the lesson named):

- Scope for 3 weeks: what to trim (fault types, KB size, anomaly detector, kind/CI). Decide by L9.
- Scenario difficulty: add distractors (unrelated noisy AP, daily peaks) so accuracy means
  something. Decide in L3.
- `Diagnosis` model: `root_cause` includes `healthy` and also has `no_fault_found`, which can
  contradict each other; and is `client_low_signal` a "no network fault"? Decide by L8.
- CI smoke eval gate (10 scenarios × 1 run, 10-point threshold) will be flaky and costs money per
  push. Decide in L20.
- LangFuse self-hosted (needs ClickHouse, Redis, blob storage) vs LangFuse Cloud free tier. Check
  before L10. Docker Desktop currently has ≈6.7 GB of memory, shared with Postgres and our services.
- Local embedding/re-ranking libraries may pull in PyTorch (large on Windows and in images);
  consider an ONNX-based library. Check before L13.
- Windows has no `make`: choose a task runner. Decide in L18.

## Curriculum

### Week 1: core loop (Gate 1: the agent solves 3 faults from the CLI)

- [x] **L0. Project setup:** uv, folder layout, ruff, pytest, `.env`, first commit (details below)
- [x] **L1. Network model:** sites, switches, APs, VLANs, clients as typed models; seeded topology
      generation; first tests. Decision: dataclasses vs Pydantic.
- [ ] **L2. Telemetry:** AP metrics with a daily pattern and noise; client connection events;
      switch ports; DHCP pool usage. Simulated time.
- [ ] **L3. Fault injection:** fault base class, ground-truth record, first 3 faults
      (`dhcp_pool_exhausted`, `ap_offline_poe`, `dns_failure`) with tests showing each produces its
      evidence.
- [ ] **L4. Simulator API:** FastAPI with `/reset`, `/faults`, `/state/...`.
- [ ] **L5. MCP server:** what MCP is under the hood; first tool; test it with MCP Inspector; then
      the 6 week-1 tools. Tool description and schema design.
- [ ] **L6. LLM tool calling by hand:** call the Anthropic API directly and run a tool-calling loop
      with no framework, so you understand what LangGraph automates.
- [ ] **L7. LangGraph ReAct agent:** state, nodes, edges; load the MCP tools through
      `langchain-mcp-adapters`; step budget.
- [ ] **L8. Structured diagnosis and CLI:** the `Diagnosis` Pydantic model; a CLI that takes a
      complaint and prints the report. **Gate 1.**

### Week 2: measure and improve (Gate 2: baseline report and one A/B result)

- [ ] **L9. Eval harness:** scenario YAML files, runner, scoring, results report; 3 runs per scenario.
- [ ] **L10. Tracing:** LangFuse self-hosted, spans per node and tool, cost per diagnosis.
- [ ] **L11. Self-correction:** the verify node and the retry loop; measure the effect.
- [ ] **L12. Skills:** `SKILL.md` playbooks, progressive disclosure, first A/B test (skills on vs off).
- [ ] **L13. Knowledge base and ingestion:** write the articles, chunk, embed, load into pgvector.
- [ ] **L14. Hybrid search:** full-text + vector + reciprocal rank fusion + re-ranking; recall@5
      and MRR comparison table; `search_kb` tool.
- [ ] **L15. Anomaly detection:** statistical detector on telemetry; `detect_anomalies` tool.
- [ ] **L16. Full scenario set:** all 13 fault types, about 40 scenarios, LLM-as-judge calibrated
      against hand grades. **Gate 2.**

### Week 3: ship it (Gate 3: one-command deploy, CI gates evals)

- [ ] **L17. Agent API:** FastAPI `/diagnose` with server-sent events; Prometheus metrics; JSON logs.
- [ ] **L18. Containers:** multi-stage Dockerfiles, docker compose for the full stack.
- [ ] **L19. Kubernetes:** kind cluster, Deployments, Services, ConfigMap, Secret, probes, limits;
      `make deploy`.
- [ ] **L20. CI:** GitHub Actions with lint, tests, image build and a smoke eval gate.
- [ ] **L21. README and demo:** architecture diagram, results table, A/B findings, demo GIF.
      **Gate 3.**

### Stretch

- [ ] AWS deployment (EKS or ECS, Bedrock, OpenSearch Serverless, ECR)
- [ ] Agent memory (past cases as episodic memory), measured with evals
- [ ] Sandboxed code execution for data-analysis steps

---

## Lesson 0: project setup (details)

**Goal:** an empty but well-organized repo that every later lesson builds on.

### Decisions to explain

1. **uv for project management.** It installs Python, creates the virtual environment, manages
   dependencies and writes a lockfile. Alternatives: pip + venv (no lockfile, more manual steps),
   Poetry (slower, and Python versions are managed separately). Why: the lockfile makes laptop, CI
   and Docker install identical versions.
2. **Python 3.13.** Supported by every planned dependency, security support until Oct 2029,
   already installed. 3.12 would also work; 3.15 is too new for some packages (see D-007).
3. **One `pyproject.toml`, one package (`src/netmedic/`) with a subpackage per service.** uv 0.13
   packages apps by default; we kept that (D-008). The alternative is one project per service,
   which is cleaner for Docker images but adds overhead too early. Dependencies get split in week 3.
4. **Add dependencies only when a lesson needs them.**
5. **ruff for lint and format.** One fast tool for bugs, import order and formatting.

### Steps

The repo folder already exists (it holds this file), so initialize uv inside it:

PowerShell (Windows). uv 0.13 creates a packaged project with `src/netmedic/__init__.py` by default.

```powershell
uv --version                                   # install uv first if this fails
uv init --python 3.13 --author-from none       # pyproject.toml, .python-version, src/netmedic/, git init
uv run python --version                        # creates .venv, installs the package: Python 3.13.x
foreach ($p in "simulator","mcp_server","agent","retrieval","detection","evals") {
    New-Item -ItemType Directory -Force -Path "src\netmedic\$p" | Out-Null
    New-Item -ItemType File -Path "src\netmedic\$p\__init__.py" | Out-Null
}
New-Item -ItemType Directory -Force -Path tests | Out-Null
uv add --dev ruff pytest
```

Data folders (`agent/skills`, `retrieval/kb`, `evals/scenarios`, ...) are created in the lessons
that first use them: git doesn't track empty folders.

Add to `pyproject.toml` (checked against ruff 0.17 and pytest 9.2; pytest 9 uses the native-TOML
`[tool.pytest]` table, see D-010):

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest]
testpaths = ["tests"]
addopts = ["--import-mode=importlib"]
strict = true
```

Extend `.gitignore` with `.env`, `.env.*`, `!.env.example` and the tool caches; add
`.gitattributes` (`* text=auto eol=lf`, CRLF only for `.ps1`/`.bat`/`.cmd`, see D-009); add the
committed template `.env.example`, then `Copy-Item .env.example .env`. Don't create these files with
PowerShell 5.1's `Out-File`: it writes a UTF-8 BOM, which corrupts the first key in `.env`.

Check that everything works, then commit:

```powershell
uv run ruff check .               # All checks passed!
uv run ruff format --check .      # 12 files already formatted (ruff also formats .md code blocks)
uv run pytest                     # "no tests ran" (exit code 5): normal for now
git check-ignore -v .env          # .gitignore:13:.env  .env
git add -A
git commit -m "chore: project skeleton"
```

### Checkpoint

Oscar reports his OS and the output of `uv --version`, `uv run python --version`,
`docker --version` and `git log --oneline`, and whether he has an Anthropic API key with a monthly
spending limit set.
