---
description: Generate focused, modular project epics based on technical specifications (Universal Template)
globs:
alwaysApply: false
---
# Rule: Generating Modular Project Epics Document (Universal Template)

## Goal

To guide an AI assistant in creating exactly one focused Project Epic Document in YAML format, where the epic corresponds to a specific module or system component. The epics should leverage detailed technical specifications and clearly document cross-module dependencies and integration points.

## Enhanced Modular Approach

### Key Principles
- **One Epic Per Module**: Each epic focuses on a single module's functionality
- **Technical Specification Alignment**: Stories map directly to technical components from module specs
- **Cross-Module Dependencies**: Explicit documentation of inter-module dependencies
- **Integration Coordination**: Separate coordination epic for cross-cutting concerns
- **Specification Traceability**: Direct references to technical specification documents

### Benefits
🎯 **Better Epic Quality**: Each epic has focused technical context
📋 **Clear Dependencies**: Dependencies between modules are explicit
🔗 **Component Mapping**: User stories map directly to technical components
⚡ **Faster Development**: Teams can work independently on focused modules
🔍 **Better Testing**: Module-specific test coverage and validation

## Process

1. **Receive Initial Prompt**: The user provides a brief description or request for new project epics or functionality along with the epic-name. If not given, ask for the epic-name and target module.
2. **Analyze Module Specifications**: Review the project's technical documentation folder and module-specific specification documents to understand module architecture, dependencies, and technical requirements.
3. **Identify Module Boundaries**: Determine which module(s) the epic targets and identify cross-module integration points.
4. **Ask Clarifying Questions**: Before writing the epics document, the AI *must* ask clarifying questions focused on module-specific concerns and cross-module dependencies.
5. **Generate a Single Modular Epic Document**: Create focused epics that align with module specifications and technical architecture.
6. **Save Epics Document**: Save as `epics/{module-name}-{epic-name}.yaml` in `/tasks/` directory.

## Thinking and Guiding Principles

Before generating the modular epics document, consider these enhanced principles:

### Module-Specific Principles
- **Technical Specification Alignment**: Stories should directly implement components defined in module specs
- **API Contract Focus**: Clear definition of module API boundaries and contracts
- **Module Independence**: Stories should be implementable within module boundaries
- **Performance Requirements**: Include module-specific performance and scalability requirements
- **Security Context**: Module-specific security concerns and authentication patterns

### Cross-Module Principles
- **Dependency Mapping**: Explicit mapping of upstream/downstream module dependencies
- **Integration Patterns**: Clear definition of communication patterns between modules
- **Data Flow Documentation**: Document data flow across module boundaries
- **Event Handling**: Define event-driven communication between modules
- **Shared Resource Management**: Handle shared databases, caches, and external services

## Enhanced Clarifying Questions

The AI should adapt questions based on project context, module specifications, and technical architecture:

### Project Context Discovery
- **Project Type**: "What type of system is this project? a) Web Application b) Mobile Application c) API Platform d) Data Processing System e) IoT Platform f) E-commerce Platform g) Enterprise Software h) Other (please specify)"
- **Technology Stack**: "What is the primary technology stack? a) JavaScript/Node.js b) Python/Django/Flask c) Java/Spring d) .NET/C# e) Go f) Ruby on Rails g) PHP h) Mixed/Microservices i) Other"
- **Architecture Pattern**: "What architectural pattern does the project follow? a) Monolithic b) Microservices c) Serverless d) Event-driven e) Layered architecture f) Hexagonal/Clean architecture g) Other"

### Module Identification
- **Module Discovery**: "Please list the main modules/components in your system. If you have technical specifications, reference them. Common patterns include: Frontend, Backend API, Database Layer, Authentication, Business Logic, Integration Layer, Analytics, Infrastructure"
- **Target Module**: "Which module is this epic primarily focused on? Please specify from your project's module list or indicate if this is a new module"
- **Module Scope**: "What specific components within the module need to be implemented? (Reference the module's technical specification if available)"
- **Integration Level**: "Does this epic require integration with other modules? If yes, which ones and what type of integration?"

### Technical Context
- **Architecture Alignment**: "Which technical layers/components should this epic implement? a) Presentation Layer b) API/Service Layer c) Business Logic Layer d) Data Access Layer e) External Integrations f) Infrastructure Components g) All layers h) Custom components"
- **Performance Requirements**: "What are the specific performance requirements? a) Response time targets (specify) b) Throughput requirements (specify) c) Availability targets (specify) d) Scalability requirements e) No specific requirements f) Custom performance criteria"
- **Security Level**: "What security requirements apply to this module? a) Authentication only b) Authorization and role-based access c) Data encryption at rest/transit d) Compliance requirements (specify) e) All security layers f) Custom security requirements"

### Dependencies & Integration
- **Upstream Dependencies**: "Which components/modules must be completed before this epic can start? a) Infrastructure setup b) Database schema c) Authentication system d) External API integrations e) Shared libraries f) None g) Other (specify)"
- **Downstream Impact**: "Which components/modules will depend on the outputs of this epic? a) User interface components b) Other backend services c) Analytics/reporting d) External systems e) Mobile applications f) All systems g) Other (specify)"
- **Data Dependencies**: "What data does this module need from other components? a) User/account data b) Configuration data c) Business entities d) Analytics data e) External system data f) No external data g) Other (specify)"

### Implementation Strategy
- **Development Approach**: "What implementation approach should be used? a) API-first development b) Database-first approach c) Frontend-first approach d) Test-driven development e) Domain-driven design f) Incremental/iterative builds g) Other methodology"
- **Testing Strategy**: "What testing approach is required? a) Unit tests only b) Integration testing c) End-to-end testing d) Performance testing e) Security testing f) All testing types g) Custom testing requirements"
- **Deployment Strategy**: "How should this module be deployed? a) Independent microservice b) Part of monolithic application c) Serverless functions d) Container-based deployment e) Traditional server deployment f) Hybrid approach g) Other deployment model"

### Business Context
- **Business Priority**: "What is the business priority for this epic? a) Critical path/foundational b) High priority feature c) Medium priority enhancement d) Low priority/nice-to-have e) Technical debt f) Compliance requirement"
- **User Impact**: "Who are the primary users affected by this epic? a) End users/customers b) Internal users/employees c) System administrators d) Developers/API consumers e) External partners f) All user types g) Other stakeholders"
- **Success Metrics**: "How will success be measured? a) Feature completeness b) Performance metrics c) User adoption/engagement d) System reliability e) Cost reduction f) Compliance achievement g) Custom metrics"

## Enhanced Epics Document Structure

### Traceability to Business Requirements
Each user story must include a `traceability` field listing references to functional requirements (FR-IDs) and user use cases (UC-IDs) from the Business Requirements Document (BRD). Example:

traceability:
  use_cases:
    - UC-003
    - UC-007
  functional_requirements:
    - FR-012
    - FR-018

Refer to the BRD to ensure that all stories in the epic can be mapped back to at least one documented use case or requirement. This is mandatory to enforce upstream alignment and completeness.

The generated modular epics document should follow this enhanced YAML format:

```yaml
{epic-name}:
  meta:
    description: Brief description of the module-specific epic
    project_context:
      project_type: "project-type"
      technology_stack: "primary-tech-stack"
      architecture_pattern: "architecture-pattern"
    module_context:
      primary_module: module-name
      related_modules:
        - module-name-1
        - module-name-2
      technical_spec_reference: "path/to/module/specification.md"
      architecture_alignment:
        - component-1
        - component-2
      business_priority: "priority-level"

  ... 10 other stories ...

  story-name:
    story_id: 11
    business_value: A brief statement of the business value this story delivers
    description: A one liner description of the story
    goals:
      - as a developer ...
      - as a system architect ...
    acceptance_criteria:
      - module structure ...
      - all external ...
    dependent_stories: [1, 3, 4]
    traceability:
      use_cases: [UC-001, UC-002]
      functional_requirements: [FR-003, FR-004]
    relevant_docs:
      - "docs/vision.md"
      - "docs/technical-architecture-overview.md"
      - "docs/business-requirements.md"
      - "docs/technical-specs/module-specification.md"
    cross_module_dependencies:
      upstream:
        module-name-1:
          dependency: "Description of the dependency"
          interface: "Interface details (e.g., API, library, protocol)"
        module-name-2:
          dependency: "Description of the dependency"
      downstream:
        module-name-3:
          dependency: "Description of the dependency"
          interface: "Interface details (e.g., API, library, protocol)"
    risk_mitigation: "Reduces integration complexity and deployment risks"
    outputs:
      path/to/output/where/the/file/will/be/file_1.py:
        classes:
          ClassName:
            attributes:
              - attribute_1: "str: Description of attribute 1"
              - attribute_2: "int: Description of attribute 2"
            methods:
              - method_name: >
                  def method_name(environment: str = "production") -> ModuleConfig:
                      """
                      Load module configuration based on environment
                      Validates all required settings and dependencies
                      """
      path/to/a/different/output/file_2.ts:
        imports:
          - import { ResourceType } from './ResourceType';
          - import { Database } from '../../shared/Database';
          - import { Logger } from '../../shared/Logger';

        global_variables:
          - db: "Database: Shared database instance for resource persistence"
          - logger: "Logger: Global logger for audit and error tracking"

        functions:
          classes:
            ResourceType:
              attributes:
                - id: "string: Unique identifier for the resource"
                - name: "string: Resource name"
                - config: "Record<string, any>: Configuration object for resource"
              methods:
                - constructor: >
                    constructor(id: string, name: string, config: Record<string, any>) {
                      this.id = id;
                      this.name = name;
                      this.config = config;
                    }
                - validateConfig: >
                    validateConfig(): boolean {
                      // Validate resource configuration according to module rules
                      return true;
                    }
      tests:
        path/to/tests/test_module_name.py:
          classes:
            TestModuleInitialization:
              methods:
                - test_config_loading: >
                    def test_config_loading():
                        """Test module configuration loading and validation"""
                - test_dependency_resolution: >
                    def test_dependency_resolution():
                        """Test external dependency connectivity and validation"""
                - test_module_health_check: >
                    def test_module_health_check():
                        """Test module health check endpoints and monitoring"""

  another-story-name:
    story_id: 12
    description: 
    goals:
      - as a client ...
    acceptance_criteria:
      - all API endpoints ...
    dependent_stories: [3, 4, 5, 11]
    relevant_docs:
      - "path/to/doc-1.md"
    cross_module_dependencies:
      upstream:
        - module: "authentication-module"
          dependency: "User authentication and session management"
          interface: "Token-based authentication (specify protocol)"
        - module: "shared-services"
          dependency: "Common utilities and shared libraries"
          interface: "Service layer calls or library imports"
      downstream:
        - module: "monitoring-module"
          dependency: "API usage metrics and logging"
          interface: "Metrics collection (specify protocol)"
    business_value: "Enables integration with other system components and external consumers"
    risk_mitigation: "Provides controlled access to module functionality with proper security"
    outputs:
      path/to/another/file.rs:
        structs:
          - Resource:
              attributes:
                - id: "String: Unique identifier for the resource"
                - name: "String: Resource name"
                - config: "std::collections::HashMap<String, serde_json::Value>: Configuration object for resource"
              methods:
                - new: >
                    pub fn new(id: String, name: String, config: std::collections::HashMap<String, serde_json::Value>) -> Self {
                      Resource { id, name, config }
                    }
                - validate_config: >
                    pub fn validate_config(&self) -> bool {
                      // Validate resource configuration according to module rules
                      true
                    }
        tests/tests_resource.rs:
          structs:
            TestResource:
              methods:
              - test_resource_creation: >
                #[test]
                fn test_resource_creation() {
                  let mut config = std::collections::HashMap::new();
                  config.insert("key".to_string(), serde_json::json!("value"));
                  let resource = Resource::new("id1".to_string(), "TestResource".to_string(), config);
                  assert_eq!(resource.name, "TestResource");
                }
              - test_validate_config: >
                #[test]
                fn test_validate_config() {
                  let config = std::collections::HashMap::new();
                  let resource = Resource::new("id2".to_string(), "ValidResource".to_string(), config);
                  assert!(resource.validate_config());
                }
```


### Structural Validation Rules

These define the mandatory elements and schema constraints for every epic YAML document:

#### Required Sections
- `project_context`: MUST include `project_type`, `technology_stack`, and `architecture_pattern`
- `module_context`: MUST specify `primary_module`, any `related_modules`, and reference technical specs
- At least one user story with:
  - `story_id`, `description`, `business_value`, `goals`, `acceptance_criteria`
  - `dependent_stories`, `traceability`, `relevant_docs`
  - `cross_module_dependencies` with both `upstream` and `downstream`
  - `risk_mitigation`, `outputs`, and `tests`

#### Enforcement Rules
- Every field in the story block is **required**, unless explicitly stated as optional
- If any dependency lists are empty, insert comment `# No dependencies – validate if this is intentional`
- `traceability` MUST reference valid UC and FR IDs from the BRD
- `relevant_docs` MUST include links to vision, BRD, and module specs
- `outputs` MUST show at least one file path and structure (classes/functions/structs)

#### Formatting Constraints
- Use proper YAML indentation (2 spaces)
- Maintain `{ext}` placeholder unless language is explicitly known
- Avoid mixing object styles (no collapsing of maps into inline syntax)

#### Integration Guidance
- Dependencies must describe `dependency` and `interface` explicitly
- Output must be clearly organized by file path
- Tests must align with outputs and cover major logic/contract boundaries

> These rules enforce consistency and guarantee that each YAML epic can be consumed by downstream systems like Jira importers and architecture validators.


## Documentation Source Mapping for Modular Epics

Before generating a modular epic, identify the relevant source documents and how each contributes to the structure of the YAML output. Use this mapping to ensure traceability, accuracy, and alignment with the upstream documentation.

### Document-to-YAML Field Mapping

| YAML Field                    | Source Document           | Source Section or ID Type               |
|-------------------------------|---------------------------|------------------------------------------|
| project_context               | Vision Document           | Project Type, Tech Stack, Architecture   |
| module_context                | Module Spec               | Module Definitions, Component Mapping    |
| story.description             | BRD / Module Spec         | Functional Requirements, Feature Notes   |
| story.business_value          | BRD                       | Business Priority, Value Justification   |
| story.traceability.use_cases  | BRD                       | Use Case IDs (UC-###)                    |
| story.traceability.functional_requirements | BRD          | Functional Requirement IDs (FR-###)      |
| relevant_docs                 | All                       | Should include links to vision, BRD, spec|
| cross_module_dependencies     | Architecture Doc          | Dependency Diagrams, Integration Specs   |
| outputs                       | Module Spec               | Implementation Details, Interfaces       |
| tests                         | QA Strategy / Module Spec | Required test coverage per module        |

### Consumption Order

1. **Vision Document** – Establish project goals, type, and architecture.
2. **Business Requirements Document (BRD)** – Extract use cases and FRs for traceability.
3. **Module Specifications** – Identify components, outputs, and data structures.
4. **Architecture Documentation** – Trace module boundaries and integration dependencies.
5. **QA/Test Plans** – Align test scaffolding and coverage.

### Validation Guidance

- If a story cannot be linked to at least one UC and one FR → halt and request clarification.
- If outputs or tests are vague or missing → refer back to module spec or QA guidelines.
- If no `cross_module_dependencies` exist → AI must confirm this is intentional.

> This mapping is mandatory to ensure alignment across documentation artifacts and guarantees that each epic is both verifiable and spec-compliant.

## Target Audience for Modular Epics

Modular Epic documents are consumed, reviewed, and validated by different stakeholders, each with specific responsibilities. Below is a role-to-responsibility mapping with corresponding YAML sections of interest.

### Primary Authors and Consumers

| Role               | Responsibilities                                                        | Relevant YAML Sections                                  |
|--------------------|---------------------------------------------------------------------------|----------------------------------------------------------|
| **Tech Lead / Architect** | Define structure, ensure architectural alignment, own module boundaries | `project_context`, `module_context`, `architecture_alignment`, `cross_module_dependencies` |
| **Backend Developer**     | Implement logic, generate outputs, ensure module independence          | `outputs`, `story.description`, `goals`, `dependent_stories`, `relevant_docs` |
| **QA Engineer**           | Validate acceptance criteria and test coverage                         | `acceptance_criteria`, `tests`, `risk_mitigation`        |

### Secondary Reviewers

| Role               | Responsibilities                                                        | Relevant YAML Sections                                  |
|--------------------|---------------------------------------------------------------------------|----------------------------------------------------------|
| **DevOps Engineer**       | Validate deployment implications, infrastructure outputs                | `outputs`, `risk_mitigation`, `cross_module_dependencies` |
| **Integration Engineer** | Review upstream/downstream contract and interface definitions          | `cross_module_dependencies`, `traceability`, `interface` |
| **Product Manager**      | Ensure business alignment, check traceability to features and value    | `business_value`, `traceability`, `story.description`     |

### Tertiary Validators

| Role               | Responsibilities                                                        | Relevant YAML Sections                                  |
|--------------------|---------------------------------------------------------------------------|----------------------------------------------------------|
| **Security Engineer**     | Validate module-level and integration security scope                  | `risk_mitigation`, `security_context`, `relevant_docs`   |
| **Performance Engineer**  | Validate performance considerations and scalability                  | `goals`, `risk_mitigation`, `outputs`                    |
| **Business Analyst**      | Trace requirements from BRD, identify unlinked features              | `traceability`, `business_value`, `relevant_docs`        |

> Each stakeholder must validate and/or approve their relevant sections before the epic can be finalized for execution or import.

## Enhanced Output Requirements

### File Naming Convention

Filenames must follow a strict, machine-parseable pattern. All epics must align with their internal `epic_name` and module context.

#### Naming Syntax

```
tasks/epics/{scope}/{domain}-{subject}[.v{version}|.{yyyy-mm-dd}].yaml
```

#### Components
- `{scope}`: One of `module` (module), `integration` (integration), `shared`, or `platform`
- `{domain}`: System area or concern (e.g., `auth`, `analytics`, `user`, `infra`)
- `{subject}`: Specific feature or objective (e.g., `login`, `telemetry`, `sync`)
- `[.vX]` or `[.YYYY-MM-DD]`: Optional version or timestamp suffix
  
#### Examples
- `tasks/epics/module/auth-login.yaml`
- `tasks/epics/integration/analytics-kafka.yaml`
- `tasks/epics/shared/logging.v2.yaml`
- `tasks/epics/platform/infra-deploy.2025-07-19.yaml`

#### Validation Rules
- Filename must match `epic_name` inside the YAML
- Filenames must be unique within `/tasks/epics/` directory
- For epics with multiple parts: use suffixes `-part1`, `-part2`, etc.
- If alternate approaches exist for the same subject, use `-alt`, `-fallback`, etc.

> This convention ensures alignment between file naming, content traceability, version control, and automation pipelines.

### Directory Structure Template

```
/tasks/epics/
├── module/
│   ├── auth-login.yaml
│   ├── user-profile.v1.yaml
│   └── invoice-generator.2025-07-19.yaml
├── integration/
│   ├── analytics-kafka.yaml
│   └── auth-sync.yaml
├── shared/
│   ├── logging.yaml
│   └── metrics.v2.yaml
└── platform/
    ├── infra-deploy.yaml
    └── monitoring.2025-07-19.yaml
```

## Final Enhanced Instructions

**DO NOT DEVIATE — THESE ARE NON-NEGOTIABLE EXECUTION CONTRACTS**

### Preconditions
1. DO NOT begin epic generation until all required project-specific and module-specific clarifications are collected.
2. DO NOT assume epic-name or module-name — halt if missing.
3. ALWAYS review the vision, BRD, architecture, and module spec before starting.

### YAML Generation Rules
4. MUST generate only one epic per run.
5. MUST use the enhanced YAML schema exactly as defined.
6. MUST include the following required fields in every story:
   - story_id
   - description
   - goals
   - acceptance_criteria
   - dependent_stories
   - traceability (UC and FR IDs)
   - relevant_docs
   - cross_module_dependencies (both upstream and downstream)
   - business_value
   - risk_mitigation
   - outputs
   - tests

### Traceability & Cross-Module Alignment
7. MUST align stories with components in the module spec.
8. MUST include traceability references (`UC-###`, `FR-###`) to the BRD.
9. MUST describe cross_module_dependencies with both dependency and interface details.
10. If any dependencies are empty, insert comment: `# No dependencies – validate if this is intentional`

### Output Hygiene
11. DO NOT generate implementation code beyond output structure definitions.
12. MUST include file paths, classes, functions, or structs under `outputs`
13. MUST align test structure with outputs and acceptance criteria.
14. MUST use the correct `{ext}` or language-specific file extensions in all paths.
14.1 AVOID unnecessary use of double quotes in YAML unless required for disambiguation (e.g., special characters, booleans, or leading/trailing whitespace).
15. MUST name the YAML file using the format: `tasks/epics/{scope}/{serial_number}-{domain}-{subject}[.vX|.YYYY-MM-DD].yaml`
16. MUST ensure filename matches internal `epic_name` and is unique in its directory.

### Confirmation & Review Flow
17. After generating the list of stories → pause and wait for confirmation.
18. For each story: generate tasks → pause → generate tests → pause → continue.
19. Each stakeholder must review and approve their respective YAML sections.

### Failure Conditions
- If traceability cannot be established → abort and prompt for clarification.
- If module context or architecture alignment is ambiguous → abort.

> Deviation from these instructions will invalidate the epic for downstream systems including Jira import, QA validation, and architecture audit.
