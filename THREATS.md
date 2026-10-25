# TrustVault — Security Threat Model

## 1. Project Overview

TrustVault is a document-sharing web application developed using Python, Flask, and MySQL. It is designed to support controlled document access and accountability through authentication, permissions, and audit logging.

This document identifies potential security threats and describes the controls and tests needed to evaluate them.

**Important:** A control is considered implemented only after it has been verified in the application.

## 2. Assets to Protect

- User accounts and password hashes
- Uploaded documents
- Document ownership information
- Sharing permissions
- Audit logs
- Database credentials and application secret keys
- User sessions

## 3. Potential Threats and Mitigations

### Threat 1: Unauthorized Document Access

**Risk:** A user may try to access a document belonging to another user without permission.

**Mitigation:** Check authentication, document ownership, and explicit access permissions on every protected document route.

**Test:** Sign in as one user and attempt to access another user's document without permission.

**Expected result:** Access should be denied.

**Actual result:** Record the result after testing.

### Threat 2: Privilege Escalation

**Risk:** A Viewer may try to perform actions reserved for an Owner or Admin.

**Mitigation:** Enforce role and permission checks on the server side. Do not rely only on hiding buttons in the interface.

**Test:** Attempt a restricted action while signed in as a user without the required role.

**Expected result:** The application should reject the unauthorized action.

**Actual result:** Record the result after testing.

### Threat 3: Weak Password Handling

**Risk:** Plain-text passwords or insecure authentication may expose user accounts.

**Mitigation:** Use a suitable password-hashing function and verify passwords securely during login.

**Test:** Inspect the stored password value and test valid and invalid login attempts.

**Expected result:** Passwords should not be stored as plain text, and invalid login attempts should not authenticate users.

**Actual result:** Record the result after testing.

### Threat 4: Session Misuse

**Risk:** An attacker may attempt to reuse or misuse an authenticated session.

**Mitigation:** Configure a strong application secret, secure cookie settings, and appropriate session invalidation on logout.

**Test:** Log out and attempt to reuse the application's previous authenticated session.

**Expected result:** Protected pages should require valid authentication.

**Actual result:** Record the result after testing.

### Threat 5: Malicious File Upload

**Risk:** An attacker may upload an unsupported or harmful file.

**Mitigation:** Validate file extensions and size on the server. Consider additional file-content validation and malware scanning where appropriate.

**Test:** Try uploading an unsupported file type and a file exceeding the configured size limit.

**Expected result:** Unsupported files and oversized uploads should be rejected.

**Actual result:** Record the result after testing.

### Threat 6: SQL Injection

**Risk:** Malicious input may alter database queries.

**Mitigation:** Use parameterized SQL queries and avoid constructing SQL statements by concatenating untrusted input.

**Test:** Review database queries and submit unexpected input through relevant forms.

**Expected result:** User input should not alter the intended database query.

**Actual result:** Record the result after testing.

### Threat 7: Unauthorized Permission Changes

**Risk:** A user may try to grant or revoke document access without the required authority.

**Mitigation:** Verify that only authorized users can change sharing permissions.

**Test:** Attempt to modify sharing permissions while signed in as a user who does not own the document and lacks administrative authority.

**Expected result:** The unauthorized change should be rejected.

**Actual result:** Record the result after testing.

### Threat 8: Audit Log Tampering or Missing Events

**Risk:** Important document activities may not be recorded, or users may attempt to modify audit records.

**Mitigation:** Record relevant events on the server side and restrict modification of audit records.

**Test:** Perform supported document actions and inspect the resulting audit entries. Attempt unauthorized access to audit-log routes.

**Expected result:** Supported actions should generate the expected records, and unauthorized users should not access restricted logs.

**Actual result:** Record the result after testing.

### Threat 9: Exposure of Secrets

**Risk:** Database passwords or application secret keys may be exposed through source code or repository history.

**Mitigation:** Store secrets in environment variables or an appropriate secret manager. Never publish credentials in source files.

**Test:** Review the repository and deployment configuration for exposed credentials.

**Expected result:** Secrets should not be exposed in committed application code.

**Actual result:** Record the result after testing.

### Threat 10: Document Integrity and Duplicate Uploads

**Risk:** A document may be altered unexpectedly, or duplicate files may be uploaded.

**Mitigation:** If implemented, use SHA-256 hashes to verify document integrity and detect duplicate content.

**Test:** Upload a test document and compare its calculated hash with the stored hash. Test duplicate detection if supported.

**Expected result:** The result should match the documented behavior of the implemented integrity checks.

**Actual result:** Record the result after testing.

## 4. Security Testing Summary

Complete this table after running the tests.

| Test | Status | Evidence |
|---|---|---|
| Unauthorized document access | Not tested | Add result |
| Role-based restrictions | Not tested | Add result |
| Password handling | Not tested | Add result |
| Session logout | Not tested | Add result |
| File type and size validation | Not tested | Add result |
| SQL injection protection | Not tested | Add result |
| Permission changes | Not tested | Add result |
| Audit-log access | Not tested | Add result |
| Secret exposure review | Not tested | Add result |
| File integrity checks | Not tested | Add result |

## 5. Known Limitations

List any security controls that are incomplete, unimplemented, or not yet tested. Do not claim a threat has been eliminated unless the relevant control has been verified.

## 6. Responsible Testing

Perform security tests only on your own TrustVault application and test accounts. Do not target other candidates, external systems, or services without authorization.