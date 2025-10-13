---
description: 
globs: 
alwaysApply: false
---

# 80-generate-tasks

### **System-Level Test Generation & Task Scoping Optimized Prompt**

---

**Overview:**

You are tasked with creating a comprehensive test management system that includes generating system-level tests (integration, smoke, manual, automated, non-unit tests) and converting task scoping details from Daksh into a robust, actionable spreadsheet for quality tracking and project management.

---

### **Test Generation Protocol**

#### **Phase 1: Discovery Q\&A (Critical Questions for Context)**

Before proceeding with any test generation, ensure that the following questions are fully addressed to understand the project scope and requirements:

1. **What is the purpose of the application or system being tested?**
2. **What are the functional requirements?** (Include or describe the SRS/BRS if available)
3. **What are the non-functional requirements?** (e.g., performance, security, usability)
4. **What is the target platform/environment?** (Web, Mobile, API, Desktop, etc.)
5. **Are there any integrations with external systems?** (e.g., third-party APIs, databases)
6. **Which testing types are in scope?** (Smoke, Regression, Functional, Performance, Integration, Security, Usability, etc.)
7. **What are the acceptance criteria or quality goals?**
8. **What is the priority of different modules/features?**
9. **Are there any constraints or limitations?** (e.g., data limitations, environment restrictions, compliance regulations)
10. **Which areas are feasible for automation vs manual testing only?**
11. **Who will execute the tests, and what tools will be used?** (e.g., Selenium, Postman, JMeter, etc.)
12. **Are there any known risks or fragile areas in the system?** (e.g., legacy modules, third-party dependencies)

---

#### **Phase 2: Test Creation and Task Scoping**

Once the discovery phase is completed, create a **Requirement → Scenario → Test Case mapping table** based on the gathered information. The table will include the following columns:

| **Column**                  | **Description**                                                 |
| --------------------------- | --------------------------------------------------------------- |
| **Req ID**                  | Unique requirement ID (format: REQ-###)                         |
| **Requirement Description** | Short description of the requirement                            |
| **Scenario ID**             | Unique scenario ID (format: SC-XXX-###)                         |
| **Scenario Description**    | High-level description of the test scenario                     |
| **Test Case ID**            | Unique test case ID (format: TC-XXX-###)                        |
| **Test Case Description**   | Specific description of the test case                           |
| **Preconditions**           | Any prerequisites or state required before running the test     |
| **Test Data**               | Test inputs required for the case                               |
| **Expected Result**         | What the system should output when the test is executed         |
| **Test Suite**              | Logical grouping of tests (e.g., Smoke, Regression, Functional) |
| **Priority**                | Priority of the test (High/Medium/Low)                          |
| **Automation Feasible**     | Whether the test is feasible for automation (Y/N)               |
| **Status**                  | Current status of the test (Pass/Fail/Blocked/Not Executed)     |
| **Comments**                | Any additional context or notes related to the test             |

---

### **Test Types**

#### **1. Integration Tests**

* Identify core modules and their dependencies.
* Create scenarios that validate end-to-end workflows across modules, APIs, and data layers.
* Ensure all interfaces, data flow, and error handling are tested between components.

#### **2. Smoke Tests**

* Create a minimal set of tests to verify critical paths of the system after deployment or major updates.
* Test core functionality to ensure the application is stable and operable for further testing.

#### **3. Manual Tests**

* Identify test cases requiring human interaction, UI validation, or exploratory testing.
* Provide detailed steps for testers with expected outcomes.
* Useful for cases where automation cannot fully validate the user experience.

#### **4. Automated Non-Unit Tests**

* Recommend test cases that should be automated for continuous integration, regression, or end-to-end testing.
* Tools like Selenium, Cypress, or Postman should be used for automation where applicable.
* Focus on scenarios that require repeated execution or complex data handling.

#### **5. Performance Tests**

* Identify performance testing scenarios such as load, stress, and scalability testing.
* Recommend tools like JMeter, LoadRunner, or custom scripts.
* Validate system behavior under expected load and stress conditions.

#### **6. Security Tests**

* Test for common security vulnerabilities, such as SQL Injection, XSS, and authentication flaws.
* Recommend tools like OWASP ZAP, Burp Suite, or custom vulnerability scanners.
* Ensure compliance with security standards and best practices.

#### **7. Compatibility and Cross-Browser Tests**

* Create test cases ensuring the system functions across different devices, browsers, and OS versions.
* Identify manual and automated tests for compatibility validation.
* Validate responsiveness and usability on various screen sizes.

---

### **Test Documentation and Task Scoping**

Once all test cases are generated, organize them into the following **task scoping format** for better tracking:

| **Task ID** | **Task Description**                     | **Priority** | **Owner**            | **Status**  | **Deadline** | **Dependencies**    | **Comments**                         |
| ----------- | ---------------------------------------- | ------------ | -------------------- | ----------- | ------------ | ------------------- | ------------------------------------ |
| **TSK-001** | Implement Integration Test for Login     | High         | QA Lead              | In Progress | 2025-09-01   | REQ-101, SC-XXX-001 | Focus on login API integration       |
| **TSK-002** | Create Regression Test for User Profile  | Medium       | QA Tester            | Not Started | 2025-09-05   | REQ-102, SC-XXX-002 | Include edge cases like empty fields |
| **TSK-003** | Set up Performance Test for Load Testing | High         | Performance Engineer | Not Started | 2025-09-10   | REQ-103, SC-XXX-003 | Use JMeter for simulation            |

---

### **Guidelines for Test Scenarios:**

* **Prioritize Core Features:** Focus on critical workflows and high-impact modules.
* **Data-Driven Testing:** For repetitive cases (e.g., login, search), consider using data-driven tests.
* **Realistic Test Data:** Simulate real-world scenarios by using data that mirrors actual user behavior.

---
