import sqlite3
import random
import os
import smtplib

from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from dotenv import load_dotenv
from email.message import EmailMessage


# ==========================================
# BLUEPRINT
# ==========================================

auth = Blueprint("auth", __name__)


# ==========================================
# ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# ==========================================
# TEMPORARY OTP STORAGE
# ==========================================

email_otps = {}


# ==========================================
# SEND OTP EMAIL
# ==========================================

def send_otp(email, otp):

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise Exception("Email settings are missing in .env")

    msg = EmailMessage()

    msg["Subject"] = "SmartSupport AI - Email Verification OTP"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    msg.set_content(
        f"""
Hello,

Your SmartSupport AI verification OTP is:

{otp}

Please do not share this OTP with anyone.

Thank you,
SmartSupport AI
"""
    )

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        smtp.send_message(msg)


# ==========================================
# REGISTER
# ==========================================

@auth.route(
    '/register',
    methods=['GET', 'POST']
)
def register():

    if request.method == 'POST':

        username = request.form.get(
            'username',
            ''
        ).strip()

        password = request.form.get(
            'password',
            ''
        )

        email = request.form.get(
            'email',
            ''
        ).strip().lower()

        phone = request.form.get(
            'phone',
            ''
        ).strip()
        role = request.form.get(
            'role',
            'Customer'
        ).strip()

        if (
            not username
            or not password
            or not email
            or not phone
        ):

            return "Please fill all required fields."

        conn = sqlite3.connect(
            'database.db'
        )

        cursor = conn.cursor()

        # Check username
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE username=?
            """,
            (username,)
        )

        if cursor.fetchone():

            conn.close()

            return "Username already exists."

        # Check email
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email)=?
            """,
            (email,)
        )

        if cursor.fetchone():

            conn.close()

            return "This email is already registered."

        conn.close()

        # Save registration information
        session['registration_username'] = username

        session['registration_password'] = (
            generate_password_hash(password)
        )

        session['registration_role'] = role

        session['registration_email'] = email

        session['registration_phone'] = phone

        return redirect(
            '/register'
        )

    return render_template(
        'register.html'
    )


# ==========================================
# SEND EMAIL OTP
# ==========================================

@auth.route(
    '/send-email-otp',
    methods=['POST']
)
def send_email_otp():

    email = request.form.get(
        'email',
        ''
    ).strip().lower()

    username = request.form.get(
        'username',
        ''
    ).strip()

    password = request.form.get(
        'password',
        ''
    )

    phone = request.form.get(
        'phone',
        ''
    ).strip()

    if (
        not username
        or not email
        or not password
        or not phone
    ):

        return jsonify({
            "success": False,
            "message": "Please fill all fields."
        })

    conn = sqlite3.connect(
        'database.db'
    )

    cursor = conn.cursor()

    # Check username
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE username=?
        """,
        (username,)
    )

    if cursor.fetchone():

        conn.close()

        return jsonify({
            "success": False,
            "message": "Username already exists."
        })

    # Check email
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE LOWER(email)=?
        """,
        (email,)
    )

    if cursor.fetchone():

        conn.close()

        return jsonify({
            "success": False,
            "message": "This email is already registered."
        })

    conn.close()

    # Save registration information
    session['registration_username'] = username

    session['registration_password'] = (
        generate_password_hash(password)
    )

    session['registration_role'] = request.form.get(
        'role',
        'Customer'
    ).strip()

    print("SELECTED ROLE:", session['registration_role'])

    session['registration_email'] = email

    session['registration_phone'] = phone

    # Generate OTP
    otp = str(
        random.randint(
            100000,
            999999
        )
    )

    email_otps[email] = otp

    print(
        "EMAIL OTP:",
        otp
    )

    print(
        "OTP EMAIL:",
        email
    )

    print(
        "USERNAME:",
        username
    )

    try:

        send_otp(
            email,
            otp
        )

        return jsonify({
            "success": True,
            "message": "OTP sent successfully"
        })

    except Exception as e:

        print(
            "EMAIL ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to send OTP."
        })


# ==========================================
# VERIFY EMAIL OTP
# ==========================================

@auth.route(
    '/verify-email',
    methods=['GET', 'POST']
)
def verify_email():

    if request.method == 'POST':

        entered_otp = request.form.get(
            'otp',
            ''
        ).strip()

        email = session.get(
            'registration_email',
            ''
        ).strip().lower()

        saved_otp = email_otps.get(
            email
        )

        print(
            "ENTERED OTP:",
            entered_otp
        )

        print(
            "SAVED OTP:",
            saved_otp
        )

        print(
            "EMAIL:",
            email
        )

        print(
            "USERNAME:",
            session.get(
                'registration_username'
            )
        )

        # Check OTP
        if entered_otp != saved_otp:

            return jsonify({
                "success": False,
                "message": "Invalid OTP. Please try again."
            })

        username = session.get(
            'registration_username'
        )

        password_hash = session.get(
            'registration_password'
        )

        role = session.get(
            'registration_role',
            'Customer'
        )
        print("ROLE SAVED FOR ACCOUNT:", role)

        phone = session.get(
            'registration_phone',
            ''
        )

        if (
            not username
            or not password_hash
            or not email
        ):

            return jsonify({
                "success": False,
                "message": "Registration information is missing. Please register again."
            })

        conn = sqlite3.connect(
            'database.db'
        )

        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    password,
                    role,
                    email,
                    phone,
                    email_verified

                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    role,
                    email,
                    phone,
                    1
                )
            )

            conn.commit()

            conn.close()

        except sqlite3.IntegrityError:

            conn.close()

            return jsonify({
                "success": False,
                "message": "Username or email is already registered."
            })

        # Remove OTP
        email_otps.pop(
            email,
            None
        )

        # Clear registration session
        session.pop(
            'registration_username',
            None
        )

        session.pop(
            'registration_password',
            None
        )

        session.pop(
            'registration_role',
            None
        )

        session.pop(
            'registration_email',
            None
        )

        session.pop(
            'registration_phone',
            None
        )

        print(
            "ACCOUNT CREATED:",
            username
        )

        return jsonify({
            "success": True,
            "message": "Email verified successfully. Account created.",
            "redirect": "/login"
        })

    return render_template(
        'verify_email.html',
        email=session.get(
            'registration_email'
        )
    )


# ==========================================
# LOGIN
# ==========================================

@auth.route(
    '/login',
    methods=['GET', 'POST']
)
def login():

    if request.method == 'POST':

        username = request.form.get(
            'username',
            ''
        ).strip()

        password = request.form.get(
            'password',
            ''
        )

        conn = sqlite3.connect(
            'database.db'
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                username,
                password,
                role,
                email_verified
            FROM users
            WHERE username=?
            """,
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if not user:

            return render_template(
                'login.html',
                error="Invalid username or password."
            )

        user_id = user[0]
        db_username = user[1]
        password_hash = user[2]
        role = user[3]
        email_verified = user[4]

        if not check_password_hash(
            password_hash,
            password
        ):

            return render_template(
                'login.html',
                error="Invalid username or password."
            )

        # Customer email verification
        if (
            role == "Customer"
            and email_verified != 1
        ):

            return render_template(
                'login.html',
                error="Please verify your email first."
            )

        # Save login session
        session['user_id'] = user_id
        session['username'] = db_username
        session['role'] = role

        # Redirect based on role
        if role == "Admin":

            return redirect(
                '/dashboard'
            )

        elif role == "Support Agent":

            return redirect(
                '/agent-dashboard'
            )

        else:

            return redirect(
                '/chat'
            )

    return render_template(
        'login.html'
    )


# ==========================================
# LOGOUT
# ==========================================

@auth.route('/logout')
def logout():

    session.clear()

    return redirect(
        url_for('auth.login')
    )


# ==========================================
# ROLE PROTECTION
# ==========================================

def role_required(
    *allowed_roles
):

    def decorator(func):

        @wraps(func)
        def wrapper(
            *args,
            **kwargs
        ):

            if 'user_id' not in session:

                return redirect(
                    '/login'
                )

            if session.get(
                'role'
            ) not in allowed_roles:

                return (
                    "Access Denied",
                    403
                )

            return func(
                *args,
                **kwargs
            )

        return wrapper

    return decorator


# ==========================================
# CREATE SUPPORT AGENT
# ==========================================

@auth.route(
    '/create-agent',
    methods=['GET', 'POST']
)
@role_required("Admin")
def create_agent():

    if request.method == 'POST':

        username = request.form.get(
            'username',
            ''
        ).strip()

        password = request.form.get(
            'password',
            ''
        )

        password_hash = (
            generate_password_hash(
                password
            )
        )

        conn = sqlite3.connect(
            'database.db'
        )

        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    password,
                    role
                )
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    "Support Agent"
                )
            )

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return (
                "Username already exists."
            )

        conn.close()

        return redirect(
            '/users'
        )

    return render_template(
        'create_agent.html'
    )

# ==========================================
# UPDATE ADMIN PROFILE
# ==========================================

@auth.route('/update-admin-profile', methods=['POST'])
@role_required("Admin")
def update_admin_profile():

    user_id = session.get('user_id')

    username = request.form.get(
        'username',
        ''
    ).strip()

    email = request.form.get(
        'email',
        ''
    ).strip().lower()

    phone = request.form.get(
        'phone',
        ''
    ).strip()

    profile_picture = request.files.get(
        'profile_picture'
    )

    if not username:
        return "Username cannot be empty."

    # Email must be verified if it is changed
    verified_email = session.get(
        'verified_profile_email'
    )

    conn = sqlite3.connect(
        'database.db'
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT email
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    current_user = cursor.fetchone()

    if not current_user:
        conn.close()
        return "User not found."

    current_email = (
        current_user[0] or ''
    ).lower()

    # New email requires verification
    if email != current_email:

        if verified_email != email:

            conn.close()

            return (
                "Please verify your new email address first."
            )

    try:

        # Update username, email and phone
        cursor.execute(
            """
            UPDATE users
            SET username=?,
                email=?,
                phone=?
            WHERE id=?
            """,
            (
                username,
                email,
                phone,
                user_id
            )
        )

        # Profile picture
        if (
            profile_picture
            and profile_picture.filename
        ):

            filename = secure_filename(
                profile_picture.filename
            )

            upload_folder = os.path.join(
                'static',
                'uploads'
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            profile_picture.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            cursor.execute(
                """
                UPDATE users
                SET profile_picture=?
                WHERE id=?
                """,
                (
                    filename,
                    user_id
                )
            )

        conn.commit()

        session['username'] = username

        session.pop(
            'verified_profile_email',
            None
        )

    except sqlite3.IntegrityError:

        conn.close()

        return "Username or email already exists."

    conn.close()

    return redirect('/settings')

# ==========================================
# ADMIN PROFILE EMAIL OTP
# ==========================================

@auth.route(
    '/send-profile-email-otp',
    methods=['POST']
)
@role_required("Admin")
def send_profile_email_otp():

    email = request.form.get(
        'email',
        ''
    ).strip().lower()

    if not email:
        return jsonify({
            "success": False,
            "message": "Please enter an email address."
        })

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Check whether another user already has this email
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE LOWER(email)=?
        AND id!=?
        """,
        (
            email,
            user_id
        )
    )

    existing_user = cursor.fetchone()

    conn.close()

    if existing_user:

        return jsonify({
            "success": False,
            "message": "This email is already registered."
        })

    # Generate OTP
    otp = str(
        random.randint(
            100000,
            999999
        )
    )

    email_otps[
        "profile_" + email
    ] = otp

    print(
        "PROFILE EMAIL OTP:",
        otp
    )

    try:

        send_otp(
            email,
            otp
        )

        session[
            'profile_email_pending'
        ] = email

        return jsonify({
            "success": True,
            "message": "OTP sent successfully."
        })

    except Exception as e:

        print(
            "PROFILE EMAIL ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to send OTP."
        })


@auth.route(
    '/verify-profile-email',
    methods=['POST']
)
@role_required("Admin")
def verify_profile_email():

    otp = request.form.get(
        'otp',
        ''
    ).strip()

    email = session.get(
        'profile_email_pending',
        ''
    ).strip().lower()

    if not email:

        return jsonify({
            "success": False,
            "message": "Please request a new OTP."
        })

    saved_otp = email_otps.get(
        "profile_" + email
    )

    if otp != saved_otp:

        return jsonify({
            "success": False,
            "message": "Invalid OTP."
        })

    # Mark this email as verified
    session[
        'verified_profile_email'
    ] = email

    email_otps.pop(
        "profile_" + email,
        None
    )

    session.pop(
        'profile_email_pending',
        None
    )

    return jsonify({
        "success": True,
        "message": "Email verified successfully."
    })

# ==========================================
# FORGOT PASSWORD
# ==========================================

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form.get(
            'email',
            ''
        ).strip().lower()

        if not email:
            return render_template(
                'forgot_password.html',
                error="Please enter your email address."
            )

        conn = sqlite3.connect(
            'database.db'
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email)=?
            """,
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if not user:
            return render_template(
                'forgot_password.html',
                error="Email address is not registered."
            )

        # Generate OTP
        otp = str(
            random.randint(
                100000,
                999999
            )
        )

        email_otps[email] = otp

        session['forgot_password_email'] = email

        print(
            "FORGOT PASSWORD OTP:",
            otp
        )

        try:

            send_otp(
                email,
                otp
            )

            return redirect(
                '/reset-password'
            )

        except Exception as e:

            print(
                "EMAIL ERROR:",
                e
            )

            return render_template(
                'forgot_password.html',
                error="Unable to send OTP."
            )

    return render_template(
        'forgot_password.html'
    )
# ==========================================
# RESET PASSWORD
# ==========================================

@auth.route(
    '/reset-password',
    methods=['GET', 'POST']
)
def reset_password():

    if request.method == 'POST':

        otp = request.form.get(
            'otp',
            ''
        ).strip()

        new_password = request.form.get(
            'password',
            ''
        )

        confirm_password = request.form.get(
            'confirm_password',
            ''
        )

        email = session.get(
            'forgot_password_email',
            ''
        ).strip().lower()

        saved_otp = email_otps.get(
            email
        )

        if not email:

            return redirect(
                '/forgot-password'
            )

        if otp != saved_otp:

            return render_template(
                'reset_password.html',
                error="Invalid OTP."
            )

        if new_password != confirm_password:

            return render_template(
                'reset_password.html',
                error="Passwords do not match."
            )

        if not new_password:

            return render_template(
                'reset_password.html',
                error="Please enter a new password."
            )

        password_hash = generate_password_hash(
            new_password
        )

        conn = sqlite3.connect(
            'database.db'
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET password=?
            WHERE LOWER(email)=?
            """,
            (
                password_hash,
                email
            )
        )

        conn.commit()
        conn.close()

        email_otps.pop(
            email,
            None
        )

        session.pop(
            'forgot_password_email',
            None
        )

        return redirect(
            '/login'
        )

    return render_template(
        'reset_password.html'
    )