from flask import Flask, render_template, request, session, redirect
import os
from dotenv import load_dotenv
import sqlite3
from auth import auth, role_required
from agents.database_agent import get_order_details
from agents.escalation_agent import create_ticket
from agents.knowledge_agent import get_faq_response
from agents.sentiment_agent import analyze_sentiment
from agents.priority_agent import get_priority
from agents.coordinator_agent import coordinate
from agents.query_agent import extract_order_id
from agents.response_agent import generate_ai_response

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

app.register_blueprint(auth)

@app.route('/')
def home():
    return redirect('/login')


@app.route('/chat')
def chat():
    return render_template('chatbot.html')

@app.route('/tickets')
@role_required("Support Agent", "Admin")
def tickets():

    search = request.args.get('search', '')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if search:

        cursor.execute(
            """
            SELECT ticket_id, user_query, status, priority, assigned_agent
            FROM tickets
            WHERE user_query LIKE ?
            ORDER BY ticket_id DESC
            """,
            ('%' + search + '%',)
        )

    else:

        cursor.execute(
            """
            SELECT ticket_id, user_query, status, priority, assigned_agent
            FROM tickets
            ORDER BY ticket_id DESC
            """
        )

    tickets = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM tickets"
    )
    total_tickets = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='Open'"
    )
    open_tickets = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='Closed'"
    )
    closed_tickets = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE priority='High'"
    )
    high_priority = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'tickets.html',
        tickets=tickets,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        closed_tickets=closed_tickets,
        high_priority=high_priority,
        user_role=session.get('role')
    )

@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT username, email, phone, role, profile_picture
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    conn.close()

    if not user:
        return redirect('/login')

    username, email, phone, role, profile_picture = user

    return render_template(
        'profile.html',
        username=username,
        email=email,
        phone=phone,
        role=role,
        user_id=user_id,
        profile_picture=profile_picture
    )

@app.route('/ticket/<int:ticket_id>')
@role_required("Support Agent", "Admin")
def ticket_details(ticket_id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get ticket
    cursor.execute("""
        SELECT ticket_id, user_query, status, priority, assigned_agent, user_id
        FROM tickets
        WHERE ticket_id=?
    """, (ticket_id,))

    ticket = cursor.fetchone()

    if not ticket:
        conn.close()
        return "Ticket not found.", 404

    # Support Agent can view only assigned tickets
    if session.get('role') == 'Support Agent':
        if ticket[4] != session.get('username'):
            conn.close()
            return "Access Denied.", 403

    # Customer information
    customer = None

    cursor.execute("""
        SELECT username, email, phone
        FROM users
        WHERE id=?
    """, (ticket[5],))

    customer = cursor.fetchone()

    # Previous tickets of the same customer
    cursor.execute("""
        SELECT ticket_id, user_query, status, priority
        FROM tickets
        WHERE user_id=?
        AND ticket_id != ?
        ORDER BY ticket_id DESC
    """, (ticket[5], ticket[0]))

    customer_tickets = cursor.fetchall()
    # Ticket conversation
    cursor.execute("""
        SELECT sender_role, message, created_at
        FROM ticket_replies
        WHERE ticket_id=?
        ORDER BY reply_id ASC
    """, (ticket_id,))

    replies = cursor.fetchall()

    # Support agents
    cursor.execute("""
        SELECT username
        FROM users
        WHERE role='Support Agent'
    """)

    agents = cursor.fetchall()

    conn.close()

    return render_template(
        'ticket_details.html',
        ticket=ticket,
        agents=agents,
        customer=customer,
        customer_tickets=customer_tickets,
        replies=replies,
        user_role=session.get('role')
    )

@app.route('/my-ticket/<int:ticket_id>')
@role_required("Customer")
def my_ticket_details(ticket_id):

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticket_id, user_query, status, priority
        FROM tickets
        WHERE ticket_id=? AND user_id=?
        """,
        (ticket_id, user_id)
    )

    ticket = cursor.fetchone()

    if not ticket:
        conn.close()
        return "Ticket not found.", 404

    cursor.execute(
        """
        SELECT sender_role, message, created_at
        FROM ticket_replies
        WHERE ticket_id=?
        ORDER BY reply_id ASC
        """,
        (ticket_id,)
    )

    replies = cursor.fetchall()

    conn.close()

    return render_template(
        'my_ticket_details.html',
        ticket=ticket,
        replies=replies
    )

@app.route('/close_ticket/<int:ticket_id>')
@role_required("Support Agent", "Admin")
def close_ticket(ticket_id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tickets
        SET status = 'Closed'
        WHERE ticket_id = ?
        """,
        (ticket_id,)
    )

    conn.commit()
    conn.close()

    return redirect('/tickets')

@app.route('/update-ticket/<int:ticket_id>', methods=['POST'])
@role_required("Support Agent", "Admin")
def update_ticket(ticket_id):

    status = request.form.get('status')

    if status not in ["Open", "In Progress", "Closed"]:
        return "Invalid status.", 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tickets
        SET status=?
        WHERE ticket_id=?
        """,
        (status, ticket_id)
    )

    conn.commit()
    conn.close()

    return redirect(f'/ticket/{ticket_id}')

@app.route('/assign-agent/<int:ticket_id>', methods=['POST'])
@role_required("Admin")
def assign_agent(ticket_id):

    agent_name = request.form.get('agent_name')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Check whether selected user is a Support Agent
    cursor.execute("""
        SELECT username
        FROM users
        WHERE username=? AND role='Support Agent'
    """, (agent_name,))

    agent = cursor.fetchone()

    if not agent:
        conn.close()
        return "Invalid Support Agent.", 400

    # Assign ticket
    cursor.execute("""
        UPDATE tickets
        SET assigned_agent=?
        WHERE ticket_id=?
    """, (agent_name, ticket_id))

    conn.commit()
    conn.close()

    return redirect(f'/ticket/{ticket_id}')

@app.route('/reply-ticket/<int:ticket_id>', methods=['POST'])
@role_required("Support Agent", "Admin")
def reply_ticket(ticket_id):

    message = request.form.get('message', '').strip()

    if not message:
        return redirect(f'/ticket/{ticket_id}')

    user_id = session.get('user_id')
    sender_role = session.get('role')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO ticket_replies
        (ticket_id, user_id, sender_role, message)
        VALUES (?, ?, ?, ?)
        """,
        (
            ticket_id,
            user_id,
            sender_role,
            message
        )
    )

    conn.commit()
    conn.close()

    return redirect(f'/ticket/{ticket_id}')

@app.route('/get_response', methods=['POST'])
def get_response():

    message = request.form['message']

    # --------------------------------
    # 1. SENTIMENT AGENT
    # --------------------------------

    sentiment = analyze_sentiment(message)

    # --------------------------------
    # 2. PRIORITY AGENT
    # --------------------------------

    priority = get_priority(sentiment)

    # --------------------------------
    # 3. COORDINATOR AGENT
    # --------------------------------

    route = coordinate(message)

    # --------------------------------
    # 4. ORDER
    # --------------------------------

    if route == "order":

        order_id = extract_order_id(message)

        if order_id:

            order = get_order_details(order_id)

            if order:

                order_id, customer, product, status = order

                context = f"""
Order Details

Order ID: {order_id}
Customer: {customer}
Product: {product}
Status: {status}
"""

                response = generate_ai_response(
                    message,
                    context
                )

                return response.replace("\n", "<br>")

            return f"Sorry, I could not find Order {order_id}."

        return "Please provide your Order ID."


    # --------------------------------
    # 5. FAQ
    # --------------------------------

    elif route == "faq":

        faq_response = get_faq_response(message)

        if faq_response:

            response = generate_ai_response(
                message,
                faq_response
            )

            return response.replace("\n", "<br>")

        return """
        I can help with:

        • Order Tracking
        • Refund Information
        • Payment Methods
        • Delivery Time
        • Order Cancellation
        • Customer Support Tickets

        Please tell me more about your issue.
        """


    # --------------------------------
    # 6. CANCEL
    # --------------------------------

    elif route == "cancel":

        context = """
Orders can be cancelled before shipment.

Please provide your Order ID if you need help checking your order.
"""

        response = generate_ai_response(
            message,
            context
        )

        return response.replace("\n", "<br>")


    # --------------------------------
    # 7. ESCALATION
    # --------------------------------

    elif route == "escalation":

        ticket_id = create_ticket(
            message,
            priority,
            session.get('user_id')
        )

        context = f"""
Issue Escalated Successfully

Ticket ID: TKT{ticket_id}
Status: Open
Priority: {priority}

Our support team will contact you soon.
"""

        response = generate_ai_response(
            message,
            context
        )

        return response.replace("\n", "<br>")


    # --------------------------------
    # 8. GENERAL QUESTION
    # --------------------------------

    context = """
I can help with:

• Order Status
• Refund Policy
• Delivery Time
• Payment Methods
• Order Cancellation
"""

    response = generate_ai_response(
        message,
        context
    )

    return response.replace("\n", "<br>")

@app.route('/read-notification/<int:ticket_id>')
@role_required("Admin")
def read_notification(ticket_id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tickets
        SET notification_read=1
        WHERE ticket_id=?
        """,
        (ticket_id,)
    )

    conn.commit()
    conn.close()

    return redirect('/ticket/' + str(ticket_id))

@app.route('/dashboard')
@role_required("Admin")
def dashboard():

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # ================= TICKET STATISTICS =================

    cursor.execute("SELECT COUNT(*) FROM tickets")
    total_tickets = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='Open'"
    )
    open_tickets = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='Closed'"
    )
    closed_tickets = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='In Progress'"
    )
    in_progress_tickets = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE priority='High'"
    )
    high_priority = cursor.fetchone()[0]

    # ================= RECENT TICKETS =================

    cursor.execute(
        """
        SELECT ticket_id,user_query, status, priority
        FROM tickets
        ORDER BY ticket_id DESC
        LIMIT 5
        """
    )

    recent_tickets = cursor.fetchall()
    # ================= RECENT ACTIVITY =================

    cursor.execute(
        """
        SELECT ticket_id, status, priority
        FROM tickets
        ORDER BY ticket_id DESC
        LIMIT 5
        """
    )

    activities = cursor.fetchall()
    # ================= NOTIFICATIONS =================

    cursor.execute(
        """
        SELECT ticket_id, status, priority
        FROM tickets
        WHERE priority='High'
        AND notification_read=0
        ORDER BY ticket_id DESC
        LIMIT 5
        """
    )

    notifications = cursor.fetchall()

    # ================= ADMIN PROFILE =================

    cursor.execute(
        """
        SELECT profile_picture
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    conn.close()

    profile_picture = result[0] if result else None

    return render_template(
        'dashboard.html',
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        closed_tickets=closed_tickets,
        high_priority=high_priority,
        recent_tickets=recent_tickets,
        activities=activities,
        notifications=notifications,
        profile_picture=profile_picture
    )

@app.route('/analytics')
@role_required("Admin")
def analytics():

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Total Tickets
    cursor.execute("SELECT COUNT(*) FROM tickets")
    total_tickets = cursor.fetchone()[0]

    # Open Tickets
    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='Open'"
    )
    open_tickets = cursor.fetchone()[0]

    # In Progress Tickets
    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='In Progress'"
    )
    in_progress_tickets = cursor.fetchone()[0]

    # Closed Tickets
    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='Closed'"
    )
    closed_tickets = cursor.fetchone()[0]

    # High Priority Tickets
    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE priority='High'"
    )
    high_priority = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'analytics.html',
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        closed_tickets=closed_tickets,
        high_priority=high_priority
    )

@app.route('/agent-dashboard')
@role_required("Support Agent")
def agent_dashboard():

    agent_name = session.get('username')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Total assigned tickets
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE assigned_agent=?
    """, (agent_name,))

    total_tickets = cursor.fetchone()[0]

    # Open assigned tickets
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE assigned_agent=?
        AND status='Open'
    """, (agent_name,))

    open_tickets = cursor.fetchone()[0]

    # In Progress assigned tickets
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE assigned_agent=?
        AND status='In Progress'
    """, (agent_name,))

    in_progress_tickets = cursor.fetchone()[0]

    # Closed assigned tickets
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE assigned_agent=?
        AND status='Closed'
    """, (agent_name,))

    closed_tickets = cursor.fetchone()[0]

    # High Priority assigned tickets
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE assigned_agent=?
        AND priority='High'
    """, (agent_name,))

    high_priority = cursor.fetchone()[0]

    # Recent assigned tickets
    cursor.execute("""
        SELECT ticket_id, user_query, status, priority
        FROM tickets
        WHERE assigned_agent=?
        ORDER BY ticket_id DESC
        LIMIT 5
    """, (agent_name,))

    recent_tickets = cursor.fetchall()

    conn.close()

    return render_template(
        'agent_dashboard.html',
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        closed_tickets=closed_tickets,
        high_priority=high_priority,
        recent_tickets=recent_tickets
    )
@app.route('/my-tickets')
@role_required("Customer")
def my_tickets():

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticket_id, user_query, status, priority
        FROM tickets
        WHERE user_id=?
        ORDER BY ticket_id DESC
        """,
        (user_id,)
    )

    tickets = cursor.fetchall()

    conn.close()

    return render_template(
        'my_tickets.html',
        tickets=tickets
    )
@app.route('/users')
@role_required("Admin")
def users():

    search = request.args.get('search', '').strip()
    role = request.args.get('role', '').strip()

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    query = """
        SELECT id, username, role, profile_picture
        FROM users
        WHERE 1=1
    """

    params = []

    # Search by username or role
    if search:
        query += """
            AND (username LIKE ? OR role LIKE ?)
        """
        params.extend([
            f'%{search}%',
            f'%{search}%'
        ])

    # Filter by role
    if role:
        query += " AND role = ?"
        params.append(role)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)

    users = cursor.fetchall()

    cursor.execute("""
    SELECT profile_picture
    FROM users
    WHERE id=?
""", (session.get('user_id'),))

    admin_picture = cursor.fetchone()

    profile_picture = admin_picture[0] if admin_picture else None

    conn.close()

    return render_template(
        'users.html',
        users=users,
        search=search,
        role=role,
        profile_picture=profile_picture
    )

@app.route('/user/<int:user_id>')
@role_required("Admin")
def user_details(user_id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get user information
    cursor.execute("""
        SELECT id, username, email, phone, role, profile_picture
        FROM users
        WHERE id=?
    """, (user_id,))

    user = cursor.fetchone()

    if not user:
        conn.close()
        return "User not found.", 404

    # Total tickets
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE user_id=?
    """, (user_id,))

    total_tickets = cursor.fetchone()[0]

    # Open tickets
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE user_id=? AND status='Open'
    """, (user_id,))

    open_tickets = cursor.fetchone()[0]

    # Closed tickets
    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE user_id=? AND status='Closed'
    """, (user_id,))

    closed_tickets = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'user_details.html',
        user=user,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        closed_tickets=closed_tickets
    )

@app.route('/delete-user/<int:user_id>')
@role_required("Admin")
def delete_user(user_id):

    if user_id == session.get('user_id'):
        return "You cannot delete your own account."

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return redirect('/users')

@app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@role_required("Admin")
def edit_user(user_id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':

        # Prevent admin from changing their own role
        if user_id == session.get('user_id'):
            conn.close()
            return "You cannot change your own role."

        role = request.form.get('role')

        cursor.execute(
            """
            UPDATE users
            SET role=?
            WHERE id=?
            """,
            (role, user_id)
        )

        conn.commit()
        conn.close()

        return redirect('/users')

    cursor.execute(
        """
        SELECT id, username, role
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    conn.close()

    return render_template(
        'edit_user.html',
        user=user
    )

@app.route('/settings', methods=['GET', 'POST'])
@role_required("Admin")
def settings():

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':

        ticket_notifications = (
            1 if request.form.get('ticket_notifications') else 0
        )

        high_priority_alerts = (
            1 if request.form.get('high_priority_alerts') else 0
        )

        ai_agent_activity = (
            1 if request.form.get('ai_agent_activity') else 0
        )

        cursor.execute("""
            UPDATE settings
            SET ticket_notifications=?,
                high_priority_alerts=?,
                ai_agent_activity=?
            WHERE id=1
        """, (
            ticket_notifications,
            high_priority_alerts,
            ai_agent_activity
        ))

        conn.commit()

    # Get notification settings

    cursor.execute("""
        SELECT ticket_notifications,
               high_priority_alerts,
               ai_agent_activity
        FROM settings
        WHERE id=1
    """)

    settings_data = cursor.fetchone()


    # Get Admin information

    cursor.execute("""
        SELECT username, email, phone, role, profile_picture
        FROM users
        WHERE id=?
    """, (user_id,))

    admin = cursor.fetchone()

    conn.close()

    return render_template(
        'settings.html',
        settings=settings_data,
        admin=admin
    )
@app.route('/update-admin-profile', methods=['POST'])
@role_required("Admin")
def update_admin_profile():

    user_id = session.get('user_id')

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()

    if not username:
        return "Username cannot be empty."

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE users
            SET username=?,
                email=?,
                phone=?
            WHERE id=?
        """, (
            username,
            email,
            phone,
            user_id
        ))

        conn.commit()

        session['username'] = username

    except sqlite3.IntegrityError:

        conn.close()

        return "Username already exists."

    conn.close()

    return redirect('/settings')

@app.route('/edit-profile')
@role_required("Admin")
def edit_profile():

    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, email, phone, profile_picture
        FROM users
        WHERE id=?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    if not user:
        return redirect('/login')

    return render_template(
        'edit_profile.html',
        user=user
    )

if __name__ == "__main__":
    app.run(debug=True)