# utils.py
from flask_mail import Message
from extensions import mail

def send_fraud_alert_email(to_email, transaction_id, amount):
    print(" Trying to send fraud alert email...")  # Debug line

    try:
        msg = Message(
            subject=" Fraud Alert - SafeSwipe",
            sender='Yourmailid',   # Same as MAIL_DEFAULT_SENDER
            recipients=["Mailid"]             # Usually: admin email or fixed recipient
        )
        msg.body = f"""
            Fraud Alert Notification

        A suspicious transaction has been detected:

            Transaction ID: {transaction_id}
            Amount: ₹{amount}

        Please take necessary action immediately.

        - SafeSwipe Security Team
        """
        mail.send(msg)
        print(" Email sent successfully.")

    except Exception as e:
        print(" Failed to send email.")
        print(f" Error: {e}")

