# TrustVault — Secure Document Sharing with a Real Audit Trail

## 1. Project Overview

TrustVault is a secure document-sharing web application built using Python, Flask, and MySQL. It is designed to help users upload, manage, and share documents while controlling access and maintaining an audit trail of important activities.

The project focuses on document ownership, role-based access control, and accountability.

## 2. Problem Statement

Sharing confidential documents without proper access control can expose sensitive information. It can also be difficult to identify who accessed a document or when access permissions changed.

TrustVault aims to address these challenges through controlled document access and activity logging.

## 3. Technology Stack

- **Frontend:** HTML, CSS
- **Backend:** Python, Flask
- **Database:** MySQL
- **Authentication:** Flask sessions and password hashing
- **Version Control:** Git and GitHub

## 4. User Roles

The application is designed around three roles:

- **Admin:** Administrative access according to the permissions implemented in the application.
- **Owner:** Manages documents they own and controls sharing permissions where implemented.
- **Viewer:** Accesses documents shared with them, according to the permissions granted.

Actual permissions depend on the application's implementation.

## 5. Main Features

The application includes pages for:

- User registration and login
- Dashboard
- Document upload
- Document listing
- Shared document access
- Audit logs
- Administrative user management

The availability and behavior of each feature must be verified against the current application before submission.

## 6. Document Upload

The current application configuration allows PDF, DOCX, and TXT files, with a maximum request size of 10 MB.

Uploaded files are stored in the application's upload directory during local development.

## 7. Security Considerations

TrustVault uses password hashing and session-based authentication.

The application is intended to enforce access permissions and record important document activities. These controls must be tested to confirm that unauthorized users cannot access protected documents.

For production deployment, configure secure environment variables, protect uploaded files, and use suitable persistent storage.

## 8. Local Setup

### Prerequisites

- Python
- MySQL Server
- Git

### Steps

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies from `requirements.txt`.
4. Configure the required database connection settings using environment variables.
5. Create and configure the database according to the application's SQL schema.
6. Start the Flask application using the project's configured startup command.

Do not commit passwords, secret keys, or other credentials to GitHub.

## 9. Testing

Test the following before submission:

- Registration and login
- Document upload and listing
- Owner and viewer access restrictions
- Permission granting and revocation
- Audit-log entries for supported activities
- Unauthorized document access
- File integrity checks, if implemented
- Live deployment in a private browser window

## 10. Deployment Status

Add the verified live application URL here after deployment.

Do not claim that deployment or testing is complete until it has been successfully verified.

## 11. Project Status

TrustVault is being developed as a document-sharing application with an emphasis on secure access and accountability.

Any unfinished features or known limitations will be documented honestly in the final submission.