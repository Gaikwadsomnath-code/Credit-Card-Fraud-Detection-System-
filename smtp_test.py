import smtplib

smtp_server = "smtp.gmail.com"
port = 587
sender_email = "Youremailid@gmail.com"
password = "Passkey"

receiver_email = "Youremailid@gmail.com"
message = """\
Subject: SMTP Test Mail

This is a test email from SafeSwipe SMTP config."""

try:
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
        print(" SMTP test: Mail sent successfully.")
except Exception as e:
    print(" SMTP test failed:", e)

