---
description: 
globs: 
alwaysApply: false
---

# 99-onboard

## Welcome to the Project Onboarding!

This prompt will guide you, as a new contributor, through the essential steps to get started with this project using Daksh.

### 1. Introduction
- Welcome! This project uses Daksh to automate and streamline onboarding, documentation, and development workflows.
- You’ll be guided through setting up your environment, understanding the project structure, and making your first contribution.

### 2. Prerequisites
- Ensure you have Python and all required tools installed (see `README.md`).
- Install project dependencies:  
  - For Python: `pip install -r requirements/dev.txt`  
  - For docs: `pip install -r requirements/docs.txt`
- Familiarize yourself with the `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` files.

### 3. Project Structure Overview
- Source code: `src/`
- Documentation: `docs/`
- Notebooks: `nbs/`
- Tests: `tests/`
- Configuration: `pyproject.toml`, `settings.ini`, etc.

### 4. Using Daksh for Onboarding
- Daksh provides prompts to help you understand and contribute to the project.
- Start with the following prompts in order:
  1. `10-create-vision-doc.md` – Learn about the project vision.
  2. `20-create-happy-flow.md` – Understand the happy flow.
  3. `30-create-business-requirement.md` – Review business requirements.
  4. `40-create-modules-and-specs.md` – Explore modules and technical specs.
  5. `45-create-epics-outline.md` – See the epics outline.
  6. `50-create-module-epic.md` – Dive into module epics.
  7. `60-generate-tasks-from-epic.md` – Generate actionable tasks.
  8. `70-execute-tasks.md` – Learn how to execute tasks.

### 5. First Steps
- Run the onboarding prompts in Daksh chat mode to interactively learn about each part of the project.
- Ask questions in chat mode if you need clarification at any step.

### 6. Next Actions
- After onboarding, try running the test suite:  
  `pytest`
- Explore the codebase and documentation.
- Pick a good first issue or task to work on.

### 7. Need Help?
- Refer to the `CONTRIBUTING.md` for guidelines.
- Reach out to the maintainers or ask in the project chat.
