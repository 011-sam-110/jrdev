"""
Standalone email test script — no Flask required.
Sends a verification-style email to sam.poplett.personal@gmail.com.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- Hardcoded from .env ---
EMAIL_USER = "sam.poplett15@gmail.com"
EMAIL_PASS = "fzqbuqieopwxsflo"
TO = "sam.poplett.personal@gmail.com"
# --------------------------

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Verify your JrDev account</title>
</head>
<body style="margin:0;padding:0;background-color:#0F172A;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;">Please verify your email to get started on JrDev.</div>
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#0F172A;">
  <tr>
    <td align="center" style="padding:24px 16px;">
      <table role="presentation" cellpadding="0" cellspacing="0" width="600" style="max-width:600px;width:100%;background-color:#1E293B;border-radius:8px;overflow:hidden;">
        <tr>
          <td style="background-color:#4f46e5;padding:20px 32px;">
            <span style="font-size:24px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">&lt;&gt; JrDev</span>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 32px 16px 32px;color:#e2e8f0;font-size:16px;line-height:1.6;">
            <p style="margin:0 0 16px 0;color:#e2e8f0;">Hi TestUser,</p>
            <p style="margin:0 0 16px 0;color:#e2e8f0;">Welcome to JrDev! This is a test email to confirm the mail server is working correctly.</p>
            <p style="margin:0 0 8px 0;color:#94a3b8;font-size:14px;">If you received this, email delivery is working.</p>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:8px 32px 32px 32px;">
            <table role="presentation" cellpadding="0" cellspacing="0">
              <tr>
                <td style="background-color:#4f46e5;border-radius:6px;">
                  <a href="https://jrdev.io" target="_blank" style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:16px;font-weight:600;text-decoration:none;">Verify Email</a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px 24px 32px;border-top:1px solid #334155;color:#94a3b8;font-size:13px;line-height:1.5;">
            &mdash; JrDev Team
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""

msg = MIMEMultipart("alternative")
msg["Subject"] = "JrDev — Test Email"
msg["From"] = EMAIL_USER
msg["To"] = TO
msg.attach(MIMEText(HTML, "html"))

print(f"Connecting to smtp.gmail.com:587 as {EMAIL_USER} ...")
try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, TO, msg.as_string())
    print(f"SUCCESS — email sent to {TO}")
except smtplib.SMTPAuthenticationError as e:
    print(f"AUTH FAILED — bad credentials or app password rejected.\n{e}")
except smtplib.SMTPException as e:
    print(f"SMTP ERROR — {e}")
except Exception as e:
    print(f"ERROR — {e}")
