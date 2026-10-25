# TrustVault — AI Prompt and Correction Log

## Purpose

This file documents the use of AI assistance during the development of TrustVault, a secure document-sharing application. It records development questions, AI suggestions, verification steps, corrections, and test results.

Only actual development activities and verified results should be recorded.

---

## Entry 1: Project Structure and Documentation

**Date:** 2026-10-25

**Task:** Understand the TrustVault project structure and prepare project documentation.

**Prompt/Question:** How should I document the TrustVault project, its technologies, features, database, and setup instructions?

**AI Assistance:** AI helped outline the README sections, including the project overview, problem statement, technology stack, security considerations, setup instructions, and testing checklist.

**Verification and Correction:** The documentation must be checked against the actual source code. Features that are not implemented must not be described as completed.

**Test Result:** Documentation review is pending.

**Related Commit:** Add the actual Git commit hash after committing this entry.

---

## Entry 2: Flask Application Configuration

**Date:** 2026-10-25

**Task:** Review the Flask application configuration and file-upload settings.

**Prompt/Question:** How should the Flask application, upload directory, allowed file types, and maximum upload size be configured?

**AI Assistance:** AI explained Flask initialization, upload-directory configuration, allowed file extensions, and request-size limits.

**Verification and Correction:** Check the actual application code and correct configuration issues only when identified. Verify that file uploads behave as expected.

**Test Result:** Add the actual test result after testing.

**Related Commit:** Add the relevant Git commit hash, if applicable.

---

## Entry 3: Authentication and Password Security

**Date:** 2026-10-25

**Task:** Review user authentication and password handling.

**Prompt/Question:** How can password hashing and session-based authentication help protect a Flask application?

**AI Assistance:** AI explained password hashing, password verification, session handling, and secure application-secret configuration.

**Verification and Correction:** Review the actual authentication code. Confirm that passwords are not stored as plain text and that protected pages require valid authentication.

**Test Result:** Record the actual authentication test results.

**Related Commit:** Add the relevant Git commit hash, if applicable.

---

## Entry 4: Role-Based Access Control

**Date:** 2026-10-25

**Task:** Review the Admin, Owner, and Viewer roles in TrustVault.

**Prompt/Question:** How should a document-sharing application enforce role-based permissions and prevent unauthorized document access?

**AI Assistance:** AI explained the importance of checking user roles, document ownership, and granted permissions on protected routes.

**Verification and Correction:** Compare the suggestions with the actual database schema and application routes. Document only the permissions that are implemented and verified.

**Test Result:** Record whether unauthorized-access tests passed or failed after testing.

**Related Commit:** Add the relevant Git commit hash, if applicable.

---

## Entry 5: Document Permissions and Audit Logs

**Date:** 2026-10-25

**Task:** Review document sharing, permission revocation, and audit logging.

**Prompt/Question:** How can a document-sharing application record important actions and control access to shared documents?

**AI Assistance:** AI explained document permissions, access revocation, and the importance of recording relevant activities in an audit log.

**Verification and Correction:** Verify which events are actually recorded by the application. Test the implemented sharing and revocation workflows and inspect the resulting audit records.

**Test Result:** Record the actual results after testing.

**Related Commit:** Add the relevant Git commit hash, if applicable.

---

## Entry 6: Deployment and Environment Configuration

**Date:** 2026-10-25

**Task:** Prepare the Flask application for deployment.

**Prompt/Question:** What configuration is required to deploy a Flask application and connect it to a database securely?

**AI Assistance:** AI explained deployment configuration, environment variables, database connectivity, and the need for persistent storage for uploaded documents.

**Verification and Correction:** Verify the hosting configuration, database connection, and upload-storage behavior. Do not claim successful deployment until the live application has been tested.

**Test Result:** Record the actual deployment status and test results.

**Related Commit:** Add the relevant Git commit hash, if applicable.

---

## AI Usage and Verification Policy

- AI was used as an assistant for understanding code, planning documentation, and reviewing implementation considerations.
- AI-generated suggestions must be checked against the actual application.
- Any incorrect AI suggestion must be described accurately, along with the correction actually made.
- Tests must not be reported as passed unless they were performed.
- Unimplemented features and known limitations must be disclosed honestly.
- Add actual prompts, relevant corrections, test evidence, and Git commit references before final submission.