#  Core Flask
from flask import Flask, render_template, redirect, url_for, request, flash

#  Flask Extensions
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

#  Config & DB
from config import Config
from models import db, Card ,User,Transaction, FraudAlert



#  Utilities
import pandas as pd
import pickle
from flask import session
from flask import make_response
import uuid
from flask import Response
from sqlalchemy import text
from datetime import datetime

#For mail imp lib
from utils import mail, send_fraud_alert_email
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import Config
from extensions import db, mail

from flask import request, render_template, redirect, url_for, flash, session
from flask_login import login_required
from models import FraudAlert, Transaction
from datetime import datetime, timedelta



#  Global initialization (it should be in top)
mail = Mail()
#db = SQLAlchemy()

#  Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

#initialize mail appa
mail.init_app(app)

#  Initialize database
db.init_app(app)

#  Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


#  User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
     return db.session.get(User, int(user_id))


# ---------------- Routes ---------------- #

#  Home
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/about')
def about():
    return render_template('about.html')


#Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = 'admin'  #  Force admin role for every registered user (if that's what you want)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered")
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("Admin registered successfully!")
        return redirect(url_for('login'))

    return render_template('register.html')


# List all admins
@app.route('/admin_list')
@login_required
def admin_list():
    admins = User.query.all()
    return render_template('admin_list.html', admins=admins)

# Edit admin
@app.route('/edit_admin/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_admin(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        db.session.commit()
        flash("Admin details updated successfully.")
        return redirect(url_for('admin_list'))
    return render_template('edit_admin.html', user=user)

# Delete admin
@app.route('/delete_admin/<int:user_id>', methods=['POST'])
@login_required
def delete_admin(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Admin deleted successfully.")
    return redirect(url_for('admin_list'))


#  Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print(f"User trying to login with: {email}")

        user = User.query.filter_by(email=email).first()

        if user:
            print("User found in DB")
            if check_password_hash(user.password, password):
                print("Password match")
                login_user(user)
                flash("Login successful!")

                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash("Access denied.")
                    return redirect(url_for('login'))
            else:
                print("Incorrect password")
                flash("Invalid password.")
        else:
            print("User not found")
            flash("Invalid email.")

    return render_template('login.html')


#Upload CSV
# Upload CSV (with pagination)
@app.route('/upload')
@login_required
def upload():
    batch_id = session.get('latest_batch_id')
    if not batch_id:
        flash("No uploaded data found.")
        return redirect(url_for('admin_dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Transaction.query.filter_by(batch_id=batch_id).order_by(Transaction.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page)
    transactions = pagination.items

    return render_template('upload.html', transactions=transactions, pagination=pagination)




#Predict CSV
@app.route('/predict_csv', methods=['GET', 'POST'])
@login_required
def predict_csv():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash("No file uploaded.")
            return redirect(request.url)

        df = pd.read_csv(file)
        if 'Class' in df.columns:
            df.drop('Class', axis=1, inplace=True)

        with open('fraud_model.pkl', 'rb') as f:
            model = pickle.load(f)

        predictions = model.predict(df.drop(['user_id', 'card_id', 'merchant_name', 'location', 'amount'], axis=1))
        df['Prediction'] = predictions

        #  Generate new batch ID
        batch_id = str(uuid.uuid4())
        session['latest_batch_id'] = batch_id

        for _, row in df.iterrows():
            #  Check if card exists
            card = Card.query.get(int(row['card_id']))
            if not card:
                card = Card(
                    id=int(row['card_id']),
                    user_id=current_user.id,
                    card_number=f"XXXX-{str(row['card_id'])[-4:]}",
                    bank_name="Unknown",
                    card_type="Visa",
                    status="active"
                )
                db.session.add(card)
                db.session.flush()  # Get card.id

            #  Create Transaction
            txn = Transaction(
                user_id=current_user.id,
                card_id=int(row['card_id']),
                amount=float(row['amount']),
                merchant_name=row['merchant_name'],
                location=row['location'],
                fraud_predicted=bool(row['Prediction']),
                is_fraud=bool(row['Prediction']),  #  Add this line properly!
                flag_reason="Predicted as fraud" if row['Prediction'] == 1 else None,
                batch_id=batch_id,
                is_prediction=True
            )

            db.session.add(txn)
            db.session.flush()

            #  Create Alert if fraud
            if row['Prediction'] == 1:
                alert = FraudAlert(
                    transaction_id=txn.id,
                    confirmed_by_user=None,
                    action_taken="alerted"
                )
                db.session.add(alert)

        db.session.commit()
        flash("Transactions uploaded and predictions saved.")
        return redirect(url_for('upload'))

    return render_template('upload.html')


#Download CSV
@app.route('/download_csv')
@login_required
def download_csv():
    csv_data = session.get('fraud_results_csv')
    if not csv_data:
        flash("No prediction data available to download.")
        return redirect(url_for('predict_csv'))

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=fraud_predictions.csv"}
    )


#Saved Predictions
#  Saved Predictions Route with Filters + Pagination
@app.route('/saved_predictions')
@login_required
def saved_predictions():
    search = request.args.get('search', '').strip()
    is_fraud = request.args.get('is_fraud', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    #query = Transaction.query.filter_by(is_prediction=True)  # सर्व predicted transactions, fraud + genuine

    query = Transaction.query  #  sagle record ghetoy (no is_prediction filter)

    # Search Filter
    if search:
        query = query.filter(
            (Transaction.merchant_name.ilike(f'%{search}%')) |
            (Transaction.location.ilike(f'%{search}%')) |
            (Transaction.amount.cast(db.String).ilike(f'%{search}%'))
        )

    # Fraud Filter
    if is_fraud != '':
        query = query.filter(Transaction.is_fraud == (is_fraud == '1'))

    # Date Filter
    if from_date:
        from_datetime = datetime.strptime(from_date, '%Y-%m-%d')
        query = query.filter(Transaction.timestamp >= from_datetime)

    if to_date:
        to_datetime = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Transaction.timestamp < to_datetime)

    # Sorting by timestamp descending (latest first)
    query = query.order_by(Transaction.timestamp.desc())

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page)
    transactions = pagination.items

    return render_template(
        'saved_predictions.html',
        transactions=transactions,
        pagination=pagination
    )








#Download Saved Predictions
@app.route('/download_saved_predictions')
@login_required
def download_saved_predictions():
    transactions = Transaction.query.order_by(Transaction.datetime.desc()).all()

    if not transactions:
        flash("No transactions found.")
        return redirect(url_for('saved_predictions'))

    data = []
    for txn in transactions:
        data.append({
            'ID': txn.id,
            'User ID': txn.user_id,
            'Card ID': txn.card_id,
            'Amount': txn.amount,
            'Merchant Name': txn.merchant_name,
            'Location': txn.location,
            'DateTime': txn.datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'Fraud Predicted': 'Fraud' if txn.fraud_predicted else 'Safe'
        })

    df = pd.DataFrame(data)

    response = make_response(df.to_csv(index=False))
    response.headers["Content-Disposition"] = "attachment; filename=saved_predictions.csv"
    response.headers["Content-Type"] = "text/csv"
    return response



#  Fraud Alerts
@app.route('/fraud_alerts')
@login_required
def fraud_alerts():
    batch_id = session.get('latest_batch_id')
    if not batch_id:
        flash("No alerts found.")
        return redirect(url_for('admin_dashboard'))

    # Filters
    search = request.args.get('search', '').strip()
    action_filter = request.args.get('action_taken', '')
    confirmation_filter = request.args.get('confirmed_by_user', '')
    sort_order = request.args.get('sort', 'desc')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Base query
    query = FraudAlert.query.join(Transaction).filter(Transaction.batch_id == batch_id)

    # Search
    if search:
        query = query.filter(
            (Transaction.id.cast(db.String).ilike(f"%{search}%")) |
            (FraudAlert.id.cast(db.String).ilike(f"%{search}%")) |
            (Transaction.merchant_name.ilike(f"%{search}%")) |
            (Transaction.location.ilike(f"%{search}%")) |
            (Transaction.amount.cast(db.String).ilike(f"%{search}%"))
        )

    # Action taken filter
    if action_filter:
        query = query.filter(FraudAlert.action_taken == action_filter)

    # Confirmation status filter
    if confirmation_filter == "confirmed":
        query = query.filter(FraudAlert.confirmed_by_user.is_(True))
    elif confirmation_filter == "false_alarm":
        query = query.filter(FraudAlert.confirmed_by_user.is_(False))
    elif confirmation_filter == "unconfirmed":
        query = query.filter(FraudAlert.confirmed_by_user.is_(None))

    #  Date filtering
    if from_date:
        try:
            query = query.filter(FraudAlert.alert_time >= from_date)
        except:
            flash("Invalid From Date")
    if to_date:
        try:
            query = query.filter(FraudAlert.alert_time <= to_date)
        except:
            flash("Invalid To Date")

    # Sorting
    if sort_order == "asc":
        query = query.order_by(FraudAlert.alert_time.asc())
    else:
        query = query.order_by(FraudAlert.alert_time.desc())

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page)
    alerts = pagination.items

    return render_template(
        'fraud_alerts.html',
        alerts=alerts,
        pagination=pagination,
        search=search,
        action_filter=action_filter,
        confirmation_filter=confirmation_filter,
        sort_order=sort_order,
        from_date=request.args.get('from_date', ''),
        to_date=request.args.get('to_date', '')
    )




# Take Action
@app.route('/take_action/<int:alert_id>', methods=['POST'])
@login_required
def take_action(alert_id):
    action = request.form.get('action')  # Get 'confirmed' or 'false_alarm'
    alert = FraudAlert.query.get_or_404(alert_id)
    txn = Transaction.query.get(alert.transaction_id)
    card = Card.query.get(txn.card_id)

    if action == 'confirmed':
        alert.confirmed_by_user = True

    elif action == 'false_alarm':
        alert.confirmed_by_user = False
        if card.status == 'blocked':
            card.status = 'active'  #  If wrongly blocked, unblock

    db.session.commit()
    flash(f" Action recorded: {action} for Alert ID {alert.id}")
    return redirect(url_for('fraud_alerts'))





# Ation Buttone on Fraud Alert
@app.route('/take_action_on_transaction/<int:txn_id>', methods=['POST'])
@login_required
def take_action_on_transaction(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    card = Card.query.get(txn.card_id)
    action = request.form.get('action')

    if action == 'block':
        if card:
            card.status = 'blocked'
            db.session.commit()
            flash(f" Card ID {card.id} has been blocked.")

        # Add or update FraudAlert
        alert = FraudAlert.query.filter_by(transaction_id=txn.id).first()
        if alert:
            alert.action_taken = 'blocked'
        else:
            new_alert = FraudAlert(transaction_id=txn.id, action_taken='blocked')
            db.session.add(new_alert)
        db.session.commit()

    elif action == 'alert':
        existing_alert = FraudAlert.query.filter_by(transaction_id=txn.id).first()
        if existing_alert:
            flash(" Alert sent for this transaction.")
        else:
            print(" No previous alert found. Sending alert now...")
            new_alert = FraudAlert(transaction_id=txn.id, action_taken='alerted')
            db.session.add(new_alert)
            db.session.commit()
            flash(f"Alert sent for transaction ID {txn.id}.")
            #  Send real-time alert email to admin
            send_fraud_alert_email(
                to_email='somamca2025@gmail.com',
                transaction_id=txn.id,
                amount=txn.amount
            )
            flash(f" Alert sent for transaction ID {txn.id}.")

    return redirect(url_for('upload'))




#  Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for('login'))


#  Admin Dashboard
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    total_users = User.query.count()
    total_transactions = Transaction.query.count()
    fraud_alerts = FraudAlert.query.count()
    safe_txns = Transaction.query.filter_by(fraud_predicted=False).count()
    fraud_txns = Transaction.query.filter_by(fraud_predicted=True).count()

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_transactions=total_transactions,
                           fraud_alerts=fraud_alerts,
                           safe_txns=safe_txns,
                           fraud_txns=fraud_txns)


#  App Run
if __name__ == '__main__':
    print(" SafeSwipe is starting...")

    with app.app_context():
        try:
            print(" Checking/Creating all tables...")
            db.create_all()  #  Only creates tables if not exist
            print(" All tables are ready.")
        except Exception as e:
            print(" Error during DB setup:", e)

    app.run(debug=True)



