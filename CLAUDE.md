# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SpecKit** is a structured feature development framework that guides the complete lifecycle from specification to implementation. It integrates Claude Code skills with PowerShell automation scripts and markdown templates to enforce a disciplined workflow that separates "what" (business requirements) from "how" (technical implementation).

## Core Workflow

SpecKit follows a strict phase-based approach:

1. **Specify** (`/speckit.specify "description"`) - Create business-focused feature specification
2. **Clarify** (`/speckit.clarify`) - Resolve ambiguities with targeted questions (max 3)
3. **Plan** (`/speckit.plan`) - Generate technical implementation plan with tech stack decisions
4. **Tasks** (`/speckit.tasks`) - Create dependency-ordered, story-based task list
5. **Implement** (`/speckit.implement`) - Execute tasks with validation and verification
6. **Analyze** (`/speckit.analyze`) - Cross-artifact consistency checking

Additional commands:
- `/speckit.checklist` - Generate domain-specific validation checklists
- `/speckit.taskstoissues` - Convert tasks.md to GitHub Issues
- `/speckit.constitution` - Manage project principles and constraints

## Feature Organization

### Branch & Directory Naming Convention

Features use a numbered format: `###-feature-name` (e.g., `001-user-auth`, `002-payment-flow`)

**Critical**: When creating new features, always check three sources to find the highest existing number for a given short-name:
1. Remote branches: `git ls-remote --heads origin | grep -E 'refs/heads/[0-9]+-<short-name>$'`
2. Local branches: `git branch | grep -E '^[* ]*[0-9]+-<short-name>$'`
3. Spec directories: `specs/[0-9]+-<short-name>`

Use N+1 for the new feature number.

### Feature Directory Structure

Each feature lives in `specs/###-feature-name/`:
- `spec.md` - Business requirements (WHAT & WHY, no technical details)
- `plan.md` - Technical design (tech stack, architecture, file structure)
- `tasks.md` - Implementation tasks organized by user story
- `research.md` - Technical research and decisions (optional)
- `data-model.md` - Entity models and relationships (optional)
- `contracts/` - API contracts/schemas (optional)
- `checklists/` - Validation checklists (e.g., `requirements.md`)

## PowerShell Automation Scripts

Located in `.specify/scripts/powershell/`:

- **create-new-feature.ps1** - Initialize feature structure with branch and directory
  - Usage: `./.specify/scripts/powershell/create-new-feature.ps1 -Json "description" --number N --short-name "feature-name"`
  - Creates feature branch, directory, and initializes spec.md
  - Outputs JSON with BRANCH_NAME, SPEC_FILE paths

- **setup-plan.ps1** - Initialize planning phase
  - Usage: `./.specify/scripts/powershell/setup-plan.ps1 -Json`
  - Outputs JSON with FEATURE_SPEC, IMPL_PLAN paths

- **check-prerequisites.ps1** - Validate environment and locate feature artifacts
  - Usage: `./.specify/scripts/powershell/check-prerequisites.ps1 -Json [-RequireTasks] [-IncludeTasks]`
  - Outputs JSON with FEATURE_DIR, AVAILABLE_DOCS

- **update-agent-context.ps1** - Update AI agent context files
  - Usage: `./.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude`
  - Preserves manual additions between markers

- **common.ps1** - Shared functions (Get-RepoRoot, Get-CurrentBranch, etc.)

**Important**: Always parse JSON output from scripts to get accurate paths. All PowerShell scripts support `-Json` flag for machine-readable output.

## Specification Philosophy

### Core Principles

1. **What, not How** - Specs describe WHAT users need and WHY, avoiding all technical implementation details
2. **Business-First** - Written for non-technical stakeholders, not developers
3. **Test-Driven** - Focus on acceptance scenarios and independent testability
4. **Prioritized** - User stories ordered by importance (P1, P2, P3) for incremental delivery
5. **Measurable** - Success criteria must be quantifiable and technology-agnostic

### Specification Quality Standards

- Maximum 3 `[NEEDS CLARIFICATION]` markers allowed
- Requirements must be testable and unambiguous
- Success criteria must be measurable WITHOUT implementation details
  - ✅ Good: "Users complete checkout in under 3 minutes"
  - ❌ Bad: "API response time under 200ms" (too technical)
- Each user story must be independently testable and deliverable

### User Story Organization

User stories should be:
- **Independently implementable** - Can develop one without others
- **Independently testable** - Each delivers standalone value
- **Prioritized** - P1 = MVP, P2/P3 = incremental enhancements
- **Mapped to tasks** - One phase per story in tasks.md

## Task Generation

Tasks in `tasks.md` follow strict format:
```
- [ ] [T###] [P?] [Story?] Description with file path
```

- **T###** - Sequential task ID
- **[P]** - Parallelizable marker (different files, no dependencies)
- **[Story]** - User story label ([US1], [US2], etc.) for story-phase tasks only
- File paths required for all implementation tasks

**Phase Structure**:
- Phase 1: Setup (project initialization)
- Phase 2: Foundational (blocking prerequisites)
- Phase 3+: User Stories (one phase per story, priority order)
- Final: Polish & Cross-Cutting Concerns

## Templates

Located in `.specify/templates/`:
- `spec-template.md` - Feature specification structure
- `plan-template.md` - Technical implementation plan
- `tasks-template.md` - Task list with dependency graph
- `checklist-template.md` - Validation checklist structure
- `constitution-template.md` - Project principles document
- `agent-file-template.md` - AI agent context file

Templates define mandatory and optional sections. Do not create placeholder sections marked "N/A" - remove sections that don't apply.

## MCP Integration

The project uses **Serena MCP Server** for semantic code operations:
- Configuration: `.mcp.json`
- Installation: `uvx --from git+https://github.com/oraios/serena`
- Command: `serena start-mcp-server`
- Provides symbol-level code analysis and manipulation tools

## Environment

- **Platform**: Windows with Bash shell (use Unix shell syntax)
- **Required**: Git, PowerShell 7+, uvx, Claude Code CLI
- **Working Directory**: C:\Users\Admin\ProyectosIA\proyectoPersonal
- **Language**: Español (documentation and content)

## Key Constraints

1. **Always fetch before branch checks**: Run `git fetch --all --prune` before checking for existing feature branches
2. **Parse script JSON output**: Scripts with `-Json` flag return structured data - always parse it for accurate paths
3. **Respect workflow phases**: Don't jump ahead (e.g., no implementation details in specs, no skipping plan phase)
4. **Validate before implementation**: Check checklists in `checklists/` directory before running `/speckit.implement`
5. **Single script execution**: Only run `create-new-feature.ps1` once per feature
6. **Quote handling**: For single quotes in script arguments, use escape syntax `'I'\''m'` or double-quote: `"I'm"`

## Constitution & Governance

Project constitution lives at `.specify/memory/constitution.md` (template). Features must be validated against constitutional principles during planning phase. The plan.md includes a "Constitution Check" section that must evaluate feature compliance with core principles.

## Common Patterns

### Creating a New Feature
1. Fetch remotes: `git fetch --all --prune`
2. Generate short-name from description (2-4 words, kebab-case)
3. Find highest number across remotes, locals, and specs/ for that short-name
4. Run create-new-feature.ps1 with N+1 and short-name
5. Parse JSON output for BRANCH_NAME and SPEC_FILE
6. Write spec.md following template structure
7. Generate and validate checklists/requirements.md

### Technical Planning
1. Run setup-plan.ps1 to initialize
2. Phase 0: Research unknowns, document in research.md
3. Phase 1: Create data-model.md, contracts/, update agent context
4. Validate against constitution
5. Document tech stack, architecture, file structure in plan.md

### Task Execution
1. Check prerequisites with check-prerequisites.ps1
2. Validate checklists (all must be complete or user acknowledges)
3. Process tasks by phase, respecting dependencies
4. Mark tasks with `[X]` when completed
5. Create ignore files (.gitignore, .dockerignore, etc.) based on tech stack

## Handoff Flow

Skills have defined handoffs (in their YAML frontmatter):
- `/speckit.specify` → `/speckit.clarify` or `/speckit.plan`
- `/speckit.plan` → `/speckit.tasks` or `/speckit.checklist`
- `/speckit.tasks` → `/speckit.implement` or `/speckit.analyze`

Each handoff provides suggested next steps with context.
