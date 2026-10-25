import os
import uuid
import mysql.connector

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory,
    abort,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "trustvault-dev-key-change-before-deployment"
)


# ---------------- UPLOAD SETTINGS ----------------

UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


# ---------------- MYSQL SETTINGS ----------------

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
   "password": os.environ["MYSQL_PASSWORD"],
    "database": "trustvault_db",
}


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def record_audit(cursor, user_id, document_id, action, details=""):
    cursor.execute(
        """
        INSERT INTO audit_logs (user_id, document_id, action, details)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, document_id, action, details),
    )


def is_admin():
    return (
        "user_id" in session
        and session.get("user_role") == "admin"
    )


def login_required():
    return "user_id" in session


def get_dashboard_counts(cursor, user_id):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM documents
        WHERE uploaded_by = %s
        """,
        (user_id,),
    )
    document_count = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM document_permissions
        WHERE user_id = %s
          AND permission IN ('view', 'download')
        """,
        (user_id,),
    )
    shared_count = cursor.fetchone()["total"]

    return document_count, shared_count


# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def home():
    message = None

    if request.args.get("registered"):
        message = "Account created successfully. Please log in."

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, name, password_hash, role
                FROM users
                WHERE email = %s
                """,
                (email,),
            )

            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                session.clear()
                session["user_id"] = user[0]
                session["user_name"] = user[1]
                session["user_role"] = user[3]

                return redirect(url_for("dashboard"))

            message = "Invalid email or password."

        except mysql.connector.Error:
            app.logger.exception("Login database error")
            message = "Unable to log in. Please check the database."

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("login.html", message=message)


# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([name, email, password, confirm_password]):
            message = "Please fill in all fields."

        elif len(password) < 8:
            message = "Password must contain at least 8 characters."

        elif password != confirm_password:
            message = "Passwords do not match."

        else:
            connection = None
            cursor = None

            try:
                connection = get_db_connection()
                cursor = connection.cursor()

                password_hash = generate_password_hash(password)

                cursor.execute(
                    """
                    INSERT INTO users (name, email, password_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (name, email, password_hash),
                )

                connection.commit()

                return redirect(url_for("home", registered="1"))

            except mysql.connector.IntegrityError:
                message = "This email is already registered."

            except mysql.connector.Error:
                if connection and connection.is_connected():
                    connection.rollback()

                app.logger.exception("Signup database error")
                message = "Unable to create your account."

            finally:
                if cursor:
                    cursor.close()

                if connection and connection.is_connected():
                    connection.close()

    return render_template("signup.html", message=message)


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("home"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                d.id,
                d.filename,
                d.uploaded_at,
                u.name AS owner_name,
                'Owner' AS current_permission
            FROM documents d
            JOIN users u ON u.id = d.uploaded_by
            WHERE d.uploaded_by = %s

            UNION ALL

            SELECT
                d.id,
                d.filename,
                d.uploaded_at,
                u.name AS owner_name,
                p.permission AS current_permission
            FROM documents d
            JOIN users u ON u.id = d.uploaded_by
            JOIN document_permissions p ON p.document_id = d.id
            WHERE p.user_id = %s
              AND p.permission IN ('view', 'download')

            ORDER BY uploaded_at DESC
            """,
            (session["user_id"], session["user_id"]),
        )

        documents = cursor.fetchall()

        document_count, shared_count = get_dashboard_counts(
            cursor,
            session["user_id"],
        )

        return render_template(
            "dashboard.html",
            documents=documents,
            document_count=document_count,
            shared_count=shared_count,
            user_name=session.get("user_name"),
            user_role=session.get("user_role"),
            message=request.args.get("message"),
        )

    except mysql.connector.Error:
        app.logger.exception("Dashboard database error")
        return "Unable to load dashboard. Check the application terminal.", 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()



# ---------------- MY DOCUMENTS ----------------


@app.route("/my-documents")
def my_documents():
    if not login_required():
        return redirect(url_for("home"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        
        if session.get("user_role") == "admin":
            cursor.execute(
                """
                SELECT
                    d.id,
                    d.filename,
                    d.uploaded_at,
                    u.name AS owner_name,
                    CASE
                        WHEN d.uploaded_by = %s THEN 'owner'
                        ELSE 'admin'
                    END AS current_permission
                FROM documents d
                JOIN users u ON u.id = d.uploaded_by
                ORDER BY d.uploaded_at DESC
                """,
                (session["user_id"],),
            )
        else:
            cursor.execute(
                """
                SELECT
                    d.id,
                    d.filename,
                    d.uploaded_at,
                    u.name AS owner_name,
                    'owner' AS current_permission
                FROM documents d
                JOIN users u ON u.id = d.uploaded_by
                WHERE d.uploaded_by = %s
                ORDER BY d.uploaded_at DESC
                """,
                (session["user_id"],),
            )

        documents = cursor.fetchall()
        cursor.execute(
            """
            SELECT
                p.id AS permission_id,
                p.document_id,
                u.name AS recipient_name,
                u.email AS recipient_email,
                p.permission
            FROM document_permissions p
            JOIN users u ON u.id = p.user_id
            JOIN documents d ON d.id = p.document_id
            WHERE d.uploaded_by = %s
            ORDER BY p.id DESC
            """,
            (session["user_id"],),
        )

        permissions = cursor.fetchall()

        shared_permissions = {}

        for permission in permissions:
            document_id = permission["document_id"]

            if document_id not in shared_permissions:
                shared_permissions[document_id] = []

            shared_permissions[document_id].append(permission)

        return render_template(
            "documents.html",
            documents=documents,
            shared_permissions=shared_permissions,
            user_name=session.get("user_name"),
            user_role=session.get("user_role"),
            message=request.args.get("message"),
        )

    except mysql.connector.Error:
        app.logger.exception("My Documents database error")
        return "Unable to load your documents.", 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# ---------------- SHARED ACCESS ----------------
# Shows documents shared WITH the logged-in user.

@app.route("/shared-access")
def shared_access():
    if not login_required():
        return redirect(url_for("home"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                d.id,
                d.filename,
                d.uploaded_at,
                u.name AS owner_name,
                p.permission AS current_permission
            FROM document_permissions p
            JOIN documents d
                ON d.id = p.document_id
            JOIN users u
                ON u.id = d.uploaded_by
            WHERE p.user_id = %s
              AND p.permission IN ('view', 'download')
              AND d.uploaded_by <> %s
            ORDER BY d.uploaded_at DESC
            """,
            (session["user_id"], session["user_id"]),
        )

        documents = cursor.fetchall()
        cursor.execute(
        """
        SELECT
                p.id AS permission_id,
                p.document_id,
                u.name AS recipient_name,
                u.email AS recipient_email,
                p.permission
            FROM document_permissions p
            JOIN users u ON u.id = p.user_id
            JOIN documents d ON d.id = p.document_id
            WHERE d.uploaded_by = %s
            ORDER BY p.id DESC
            """,
            (session["user_id"],),
        )

        permissions = cursor.fetchall()

        shared_permissions = {}

        for permission in permissions:
            document_id = permission["document_id"]

            if document_id not in shared_permissions:
                shared_permissions[document_id] = []

            shared_permissions[document_id].append(permission)

        return render_template(
            "shared_access.html",
            documents=documents,
            user_name=session.get("user_name"),
            user_role=session.get("user_role"),
            message=request.args.get(
                "message",
                "Showing documents shared with you.",
            ),
        )

    except Exception:
        app.logger.exception("Shared Access error")
        return "Unable to load shared documents. Check the terminal for the exact error.", 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------- DOCUMENT UPLOAD ----------------

@app.route("/upload", methods=["POST"])
def upload_document():
    if not login_required():
        return redirect(url_for("home"))

    uploaded_file = request.files.get("document")

    if not uploaded_file or not uploaded_file.filename:
        return redirect(url_for(
            "dashboard",
            message="Please select a file.",
        ))

    if not allowed_file(uploaded_file.filename):
        return redirect(url_for(
            "dashboard",
            message="Only PDF, DOCX and TXT files are allowed.",
        ))

    original_filename = secure_filename(uploaded_file.filename)

    if not original_filename:
        return redirect(url_for(
            "dashboard",
            message="Invalid filename.",
        ))

    stored_filename = f"{uuid.uuid4().hex}_{original_filename}"

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        stored_filename,
    )

    connection = None
    cursor = None
    file_saved = False

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        uploaded_file.save(file_path)
        file_saved = True

        cursor.execute(
            """
            INSERT INTO documents
                (filename, stored_filename, uploaded_by)
            VALUES (%s, %s, %s)
            """,
            (
                original_filename,
                stored_filename,
                session["user_id"],
            ),
        )

        document_id = cursor.lastrowid

        record_audit(
            cursor,
            session["user_id"],
            document_id,
            "UPLOAD",
            f"Uploaded {original_filename}",
        )

        connection.commit()

        return redirect(url_for(
            "dashboard",
            message="Document uploaded successfully.",
        ))

    except Exception:
        if connection and connection.is_connected():
            connection.rollback()

        if file_saved and os.path.exists(file_path):
            os.remove(file_path)

        app.logger.exception("Document upload failed")

        return redirect(url_for(
            "dashboard",
            message="Upload failed. Check the terminal for the exact error.",
        ))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------- GRANT DOCUMENT ACCESS ----------------

@app.route("/grant-access/<int:document_id>", methods=["POST"])
def grant_access(document_id):
    if not login_required():
        return redirect(url_for("home"))
    if session.get("user_role") != "owner":
       return redirect(url_for(
        "my_documents",
        message="Only owners can share documents."
    ))

    recipient_email = request.form.get("email", "").strip()
    permission = request.form.get("permission", "").strip().lower()

    if not recipient_email:
        return redirect(url_for(
            "my_documents",
              message="Please enter the recipient email.",
        ))

    if permission not in ("view", "download"):
        return redirect(url_for(
            "my_documents",
            message="Invalid permission.",
        ))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, filename
            FROM documents
            WHERE id = %s AND uploaded_by = %s
            """,
            (document_id, session["user_id"]),
        )

        document = cursor.fetchone()

        if not document:
            return redirect(url_for(
                "my_documents",
                message="Only the document owner can share this document.",
            ))

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (recipient_email,),
        )

        recipient = cursor.fetchone()

        if not recipient:
            return redirect(url_for(
                "my_documents",
                message="Recipient account not found. Ask them to sign up first.",
            ))

        if recipient["id"] == session["user_id"]:
            return redirect(url_for(
                "my_documents",
                message="You already own this document.",
            ))

        cursor.execute(
            """
            SELECT id
            FROM document_permissions
            WHERE document_id = %s AND user_id = %s
            """,
            (document_id, recipient["id"]),
        )

        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE document_permissions
                SET permission = %s,
                    granted_by = %s,
                    granted_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    permission,
                    session["user_id"],
                    existing["id"],
                ),
            )

            action = "UPDATE_PERMISSION"

        else:
            cursor.execute(
                """
                INSERT INTO document_permissions
                    (document_id, user_id, permission, granted_by)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    document_id,
                    recipient["id"],
                    permission,
                    session["user_id"],
                ),
            )

            action = "GRANT_ACCESS"

        record_audit(
            cursor,
            session["user_id"],
            document_id,
            action,
            f"Granted {permission} access to {recipient_email}",
        )

        connection.commit()

        return redirect(url_for(
            "my_documents",
            message=f"{permission.title()} access granted to {recipient_email}.",
        ))

    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Grant access failed")

        return redirect(url_for(
            "my_documents",
            message="Unable to grant document access.",
        ))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()



# ---------------- REVOKE DOCUMENT ACCESS ----------------
# Only the owner of a document can revoke a recipient's permission.

@app.route("/revoke-access/<int:permission_id>", methods=["POST"])
def revoke_access(permission_id):
    if not login_required():
        return redirect(url_for("home"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                p.id,
                p.document_id,
                p.user_id AS recipient_id,
                u.email AS recipient_email,
                d.filename
            FROM document_permissions p
            JOIN documents d
                ON d.id = p.document_id
            JOIN users u
                ON u.id = p.user_id
            WHERE p.id = %s
              AND d.uploaded_by = %s
            """,
            (permission_id, session["user_id"]),
        )

        permission_row = cursor.fetchone()

        if not permission_row:
            return redirect(url_for(
                "my_documents",
                message="Permission not found or you are not the owner.",
            ))

        cursor.execute(
            """
            DELETE FROM document_permissions
            WHERE id = %s
            """,
            (permission_id,),
        )

        record_audit(
            cursor,
            session["user_id"],
            permission_row["document_id"],
            "REVOKE_ACCESS",
            (
                f"Revoked access for {permission_row['recipient_email']} "
                f"to {permission_row['filename']}"
            ),
        )

        connection.commit()

        return redirect(url_for(
            "my_documents",
            message="Document access revoked successfully.",
        ))

    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Revoke access failed")

        return redirect(url_for(
            "my_documents",
            message="Unable to revoke document access.",
        ))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()



# ---------------- SECURE DOCUMENT VIEW / DOWNLOAD ----------------

@app.route("/documents/<int:document_id>")
def view_document(document_id):
    if not login_required():
        return redirect(url_for("home"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                d.id,
                d.filename,
                d.stored_filename,
                d.uploaded_by,
                p.permission
            FROM documents d
            LEFT JOIN document_permissions p
                ON p.document_id = d.id
                AND p.user_id = %s
            WHERE d.id = %s
            """,
            (session["user_id"], document_id),
        )

        document = cursor.fetchone()

        if not document:
            abort(404)

        is_owner = document["uploaded_by"] == session["user_id"]
        permission = document["permission"]

        if not is_owner and permission != "download":
            abort(403)

        record_audit(
            cursor,
            session["user_id"],
            document_id,
            "DOWNLOAD",
            f"Downloaded {document['filename']}",
        )
        connection.commit()

        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            document["stored_filename"],
            as_attachment=True,
            download_name=document["filename"],
        )

    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Document download database error")
        return "Unable to access this document.", 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------- SECURE DOCUMENT PREVIEW ----------------

@app.route("/preview-document/<int:document_id>")
def preview_document(document_id):
    if not login_required():
        return redirect(url_for("home"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                d.id,
                d.filename,
                d.stored_filename,
                d.uploaded_by,
                p.permission
            FROM documents d
            LEFT JOIN document_permissions p
                ON p.document_id = d.id
                AND p.user_id = %s
            WHERE d.id = %s
            """,
            (session["user_id"], document_id),
        )

        document = cursor.fetchone()

        if not document:
            abort(404)

        is_owner = document["uploaded_by"] == session["user_id"]
        is_admin = session.get("user_role") == "admin"
        permission = document["permission"]

        if not is_owner and not is_admin and permission not in ("view", "download"):
           abort(403)

        response = send_from_directory(
            app.config["UPLOAD_FOLDER"],
            document["stored_filename"],
            as_attachment=False,
            download_name=document["filename"],
        )

        record_audit(
            cursor,
            session["user_id"],
            document_id,
            "VIEW",
            f"Viewed {document['filename']}",
        )
        connection.commit()

        return response

    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Document preview database error")
        return "Unable to preview this document.", 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------- AUDIT LOGS (ADMIN ONLY) ----------------


@app.route('/admin/users')
def manage_users():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        abort(403)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, email, role, created_at
        FROM users
        ORDER BY created_at DESC
    """)

    users = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('admin_users.html', users=users)


@app.route("/admin/update-role/<int:user_id>", methods=["POST"])
def update_user_role(user_id):
    if not login_required():
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        abort(403)

    new_role = request.form.get("role", "").strip().lower()

    if new_role not in ("owner", "viewer", "admin"):
        abort(400)

    if user_id == session.get("user_id"):
        return redirect(url_for("manage_users"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "UPDATE users SET role = %s WHERE id = %s",
            (new_role, user_id),
        )
        connection.commit()

        return redirect(url_for("manage_users"))

    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("User role update failed")
        return "Unable to update user role.", 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
@app.route("/audit-logs")
def audit_logs():
    if not login_required():
        return redirect(url_for("home"))

    role = session.get("user_role")
    user_id = session.get("user_id")

    if role not in ("admin", "owner", "viewer"):
        abort(403)

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                a.action,
                a.details,
                a.created_at,
                u.name AS user_name,
                d.filename
            FROM audit_logs a
            LEFT JOIN users u ON u.id = a.user_id
            LEFT JOIN documents d ON d.id = a.document_id
        """

        params = ()

        # ADMIN: all activity logs
        
       
        if role == "admin":
            pass

        # OWNER: logs for documents uploaded by this owner
        elif role == "owner":
            query += """
                WHERE EXISTS (
                    SELECT 1
                    FROM documents d2
                    WHERE d2.id = a.document_id
                      AND d2.uploaded_by = %s
                )
            """
            params = (user_id,)

        # VIEWER: logs for documents currently shared with this viewer
        
        # VIEWER: only this viewer's actions on currently shared documents
        elif role == "viewer":
            query += """
                WHERE a.user_id = %s
                  AND a.action IN ('VIEW', 'DOWNLOAD')
                  AND EXISTS (
                      SELECT 1
                      FROM document_permissions p
                      WHERE p.document_id = a.document_id
                        AND p.user_id = %s
                        AND p.permission IN ('view', 'download')
                  )
            """
           

            params = (user_id, user_id)
        query += " ORDER BY a.created_at DESC"

        cursor.execute(query, params)
        logs = cursor.fetchall()

        return render_template(
            "audit_logs.html",
            logs=logs,
            user_name=session.get("user_name"),
            user_role=role,
        )

    except mysql.connector.Error:
        app.logger.exception("Audit log database error")
        return "Unable to load audit logs.", 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------- FORGOT PASSWORD ----------------


# ---------------- FORGOT PASSWORD ----------------

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = request.form.get("email", "").strip().lower()
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not email or not new_password or not confirm_password:
        return render_template(
            "forgot_password.html",
            message="Please fill in all fields."
        )

    if new_password != confirm_password:
        return render_template(
            "forgot_password.html",
            message="Passwords do not match."
        )

    if len(new_password) < 8:
        return render_template(
            "forgot_password.html",
            message="Password must contain at least 8 characters."
        )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check whether the registered email exists
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            return render_template(
                "forgot_password.html",
                message="No account found with this email address."
            )

        # Hash the new password before saving it
        password_hash = generate_password_hash(new_password)

        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, user[0])
        )

        connection.commit()

        return render_template(
            "forgot_password.html",
            message="Password updated successfully. Please log in."
        )

    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Password reset database error")

        return render_template(
            "forgot_password.html",
            message="Unable to reset password. Please try again."
        )

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# ---------------- ERROR HANDLERS ----------------

@app.errorhandler(413)
def file_too_large(error):
    return redirect(url_for(
        "dashboard",
        message="File is too large. Maximum allowed size is 10 MB.",
    ))


# ---------------- START SERVER ----------------

if __name__ == "__main__": 
    app.run(debug=True)