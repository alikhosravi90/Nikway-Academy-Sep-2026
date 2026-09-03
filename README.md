# Agentic Army

## Enterprise-grade Agentic Organization System

A coordinated army of AI agents working together to automate software development, architecture, and operations.

## Quick Start

### 1. OpenCode Configuration

Copy `config/system.json` to your OpenCode configuration:

```bash
# Windows
copy E:\AGENTIC-ARMY\config\system.json %USERPROFILE%\.config\opencode\opencode.json

# Or set environment variable
set OPENCODE_CONFIG=E:\AGENTIC-ARMY\config\system.json
```

### 2. Start OpenCode

```bash
opencode
```

### 3. Deploy Agents

```
/deploy commander
/deploy architect
/deploy builder
/deploy reviewer
/deploy researcher
/deploy tester
```

### 4. Assign Tasks

```
/assign "Build a REST API for user management" builder
/assign "Review the authentication module" reviewer
/assign "Research best practices for JWT" researcher
```

## Agent Roster

| Agent | Role | Capabilities |
|-------|------|--------------|
| **Commander** | Orchestration | Task assignment, monitoring, escalation |
| **Architect** | Design | System design, specifications, ADRs |
| **Builder** | Implementation | Code, configuration, deployment |
| **Reviewer** | Quality | Code review, security, compliance |
| **Researcher** | Intelligence | Research, analysis, recommendations |
| **Tester** | Validation | Testing, bug detection, verification |

## Skills

| Skill | Purpose |
|-------|---------|
| `code-review` | Comprehensive code review methodology |
| `system-design` | System design and architecture methodology |

## Workflows

| Workflow | Purpose |
|----------|---------|
| `development` | Standard feature development workflow |

## Directory Structure

```
E:\AGENTIC-ARMY\
├── AGENTS.md           # Army mission and commands
├── README.md           # This file
├── config/             # System configuration
│   └── system.json     # OpenCode configuration
├── agents/             # Agent definitions
│   ├── commander.md    # Mission Commander
│   ├── architect.md    # System Architect
│   ├── builder.md      # Builder
│   ├── reviewer.md     # Code Reviewer
│   ├── researcher.md   # Research Specialist
│   └── tester.md       # QA Specialist
├── skills/             # Skill definitions
│   ├── code-review/
│   │   └── SKILL.md
│   └── system-design/
│       └── SKILL.md
├── workflows/          # Workflow definitions
│   └── development.md
├── philosophy/         # Core philosophy (Persian + English)
│   ├── foundations.md
│   └── foundations-en.md
└── projects/           # Project workspaces
    └── nikway/         # NIKWAY Knowledge Migration Package
        ├── INDEX.md
        └── ...
```

## Commands

| Command | Description |
|---------|-------------|
| `/status` | Show system status |
| `/deploy <agent>` | Deploy specific agent |
| `/list` | List available agents |
| `/assign <task> <agent>` | Assign task to agent |
| `/report` | Get situation report |
| `/escalate <issue>` | Escalate to human |

## Development Workflow

```
Request → Design → Implement → Review → Test → Deploy
```

1. **Request:** Commander receives and analyzes task
2. **Design:** Architect creates technical specification
3. **Implement:** Builder writes code/configuration
4. **Review:** Reviewer ensures quality and security
5. **Test:** Tester validates functionality
6. **Deploy:** Builder deploys to production

## Configuration

### Model Selection

```json
{
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "anthropic/claude-haiku-4-20250514"
}
```

### Permissions

```json
{
  "permission": {
    "*": "ask",
    "bash": {
      "*": "ask",
      "git *": "allow",
      "python *": "allow",
      "rm *": "deny"
    }
  }
}
```

### Policies

```json
{
  "experimental": {
    "policies": [
      { "effect": "deny", "action": "provider.use", "resource": "*" },
      { "effect": "allow", "action": "provider.use", "resource": "anthropic" }
    ]
  }
}
```

## Contributing

1. Add new agents to `agents/` directory
2. Create skills in `skills/` directory
3. Define workflows in `workflows/` directory
4. Update this README with new additions

## License

MIT
# NIKWAY Academy

**NIKWAY Academy — Digital Operating System for Lean, Continuous Improvement, and Operational Excellence**

NIKWAY is an evidence-driven platform designed to help organizations move from operational complexity and fragmented improvement activities toward structured learning, execution, and measurable improvement.

## Vision

**From chaos to structured clarity.**

NIKWAY connects learning, knowledge, execution, assessment, and organizational improvement into a unified digital operating model.

## Core Areas

* Lean & Continuous Improvement
* Operational Excellence
* GMP / Pharmaceutical Operations
* Organizational Learning
* Assessment & Capability Development
* Knowledge Management
* AI-Assisted Workflows
* Evidence-Driven Execution
* Organizational Performance

## Platform Architecture

NIKWAY is being developed as a modular digital platform with a strong focus on:

* Modular Monolith architecture
* API-first backend
* PostgreSQL persistence
* Authentication & authorization
* Organization and resource isolation
* Auditability and traceability
* Object storage
* Workflow automation
* AI-assisted execution
* Automated testing and release verification

## Engineering Principles

NIKWAY follows these principles:

1. **Evidence before assumptions**
2. **Security by default**
3. **Deny by default**
4. **Organization-aware access control**
5. **Auditability by design**
6. **Automated verification**
7. **Incremental delivery**
8. **Release readiness before production**

## Current Development Status

The project is currently in an **engineering and release-readiness phase**.

Local implementation and verification are actively being completed, followed by validation in controlled external environments.

Production readiness is **not claimed by this repository until the required CI, security, staging, integration, and evidence gates are verified**.

## Repository Structure

The repository contains the application source code, infrastructure definitions, automated tests, workflows, verification procedures, and release-readiness evidence required to develop and validate the NIKWAY platform.

## Quality & Release

The project uses automated verification and release gates covering:

* Application tests
* Security tests
* Database migrations
* API contracts
* Authorization
* Audit persistence and integrity
* CI verification
* Vulnerability scanning
* Staging integration
* Release evidence

## Project Status

**Development:** Active
**Release Readiness:** In Progress
**Production:** Not yet released

---

## License

License and distribution terms are currently under review.

---

*NIKWAY Academy — From chaos to structured clarity.*
