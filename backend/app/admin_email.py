"""
IMAP sync and SMTP send helpers for the three admin inboxes.

Inboxes: noreply (EMAIL_USER/EMAIL_PASS), support (SUPPORT_EMAIL/SUPPORT_PASS),
         disputes (DISPUTES_EMAIL/DISPUTES_PASS).
"""
import email
import email.policy
import imaplib
import json
import logging
import os
import smtplib
import ssl
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from . import db
from .models import AdminEmail, AdminEmailConfig

logger = logging.getLogger(__name__)

IMAP_HOST = 'imap.ionos.co.uk'
IMAP_PORT = 993
SMTP_HOST = 'smtp.ionos.co.uk'
SMTP_PORT = 587


def _inbox_credentials(inbox_name):
    """Return (address, password) for the given inbox name, or (None, None) if not configured."""
    mapping = {
        'noreply':  (os.environ.get('EMAIL_USER'),    os.environ.get('EMAIL_PASS')),
        'support':  (os.environ.get('SUPPORT_EMAIL'), os.environ.get('SUPPORT_PASS')),
        'disputes': (os.environ.get('DISPUTES_EMAIL'), os.environ.get('DISPUTES_PASS')),
    }
    return mapping.get(inbox_name, (None, None))


def _compute_thread_id(in_reply_to, message_id):
    """
    Walk the In-Reply-To chain to find the root message_id of the thread.
    Falls back to message_id itself if no parent is found.
    """
    if not in_reply_to:
        return message_id
    parent = AdminEmail.query.filter_by(message_id=in_reply_to).first()
    if parent:
        return parent.thread_id or parent.message_id
    return in_reply_to


_EMAIL_WRAPPER = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
  body{{margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;}}
  .wrapper{{max-width:600px;margin:32px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,.08);}}
  .header{{background:#0f172a;padding:24px 32px;text-align:left;}}
  .header-logo{{font-size:22px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;}}
  .header-logo span{{color:#818cf8;}}
  .body{{padding:32px;color:#1e293b;font-size:15px;line-height:1.7;}}
  .body p{{margin:0 0 16px;}}
  .divider{{border:none;border-top:1px solid #e2e8f0;margin:24px 0;}}
  .signature{{color:#64748b;font-size:13px;}}
  .footer{{background:#f8fafc;padding:16px 32px;text-align:center;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;}}
  a{{color:#4f46e5;}}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <span class="header-logo">&lt;&gt; Jr<span>Dev</span></span>
  </div>
  <div class="body">
    {body}
    <hr class="divider"/>
    <div class="signature">{signature}</div>
  </div>
  <div class="footer">JrDev &middot; <a href="https://jr-dev.uk">jr-dev.uk</a></div>
</div>
</body>
</html>"""


def _wrap_email_html(body_html, signature_html=None):
    """Wrap content in the branded JrDev email layout."""
    if signature_html is None:
        try:
            config = AdminEmailConfig.get()
            signature_html = config.signature_html or ''
        except Exception:
            signature_html = '<p>Best regards,<br><strong>The JrDev Team</strong></p>'
    return _EMAIL_WRAPPER.format(body=body_html or '', signature=signature_html)


def _parse_addresses(header_val):
    """Return a JSON-encoded list of address strings from a header value."""
    if not header_val:
        return json.dumps([])
    addrs = [a.strip() for a in header_val.split(',') if a.strip()]
    return json.dumps(addrs)


def sync_inbox(inbox_name):
    """
    Connect via IMAP to the given inbox, fetch all messages, store new ones
    in AdminEmail (skipping any already present by message_id). Returns count added.
    """
    address, password = _inbox_credentials(inbox_name)
    if not address or not password:
        logger.warning('sync_inbox: credentials not set for inbox=%s', inbox_name)
        return 0

    added = 0
    try:
        ctx = ssl.create_default_context()
        with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=ctx) as imap:
            imap.login(address, password)
            imap.select('INBOX')
            _, data = imap.search(None, 'ALL')
            uid_list = data[0].split()
            for uid in uid_list:
                _, msg_data = imap.fetch(uid, '(RFC822)')
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw, policy=email.policy.default)

                mid = (msg.get('Message-ID') or '').strip()
                if mid and AdminEmail.query.filter_by(message_id=mid).first():
                    continue  # already stored

                in_reply_to = (msg.get('In-Reply-To') or '').strip() or None
                thread_id = _compute_thread_id(in_reply_to, mid or str(uuid.uuid4()))

                # Extract body
                body_text = ''
                body_html = ''
                if msg.is_multipart():
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == 'text/plain' and not body_text:
                            body_text = part.get_content()
                        elif ct == 'text/html' and not body_html:
                            body_html = part.get_content()
                else:
                    ct = msg.get_content_type()
                    content = msg.get_content()
                    if ct == 'text/html':
                        body_html = content
                    else:
                        body_text = content

                # Parse date
                date_str = msg.get('Date')
                try:
                    sent_at = email.utils.parsedate_to_datetime(date_str) if date_str else None
                    if sent_at and sent_at.tzinfo:
                        import datetime as dt
                        sent_at = sent_at.astimezone(dt.timezone.utc).replace(tzinfo=None)
                except Exception:
                    sent_at = None

                record = AdminEmail(
                    inbox=inbox_name,
                    direction='inbound',
                    message_id=mid or None,
                    in_reply_to=in_reply_to,
                    thread_id=thread_id,
                    from_addr=msg.get('From', ''),
                    to_addrs=_parse_addresses(msg.get('To', '')),
                    cc_addrs=_parse_addresses(msg.get('Cc', '')),
                    subject=msg.get('Subject', ''),
                    body_text=body_text,
                    body_html=body_html,
                    sent_at=sent_at,
                )
                db.session.add(record)
                added += 1

        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error('sync_inbox error for inbox=%s: %s', inbox_name, exc)
        raise

    return added


def send_admin_email(from_inbox, to_list, subject, body_html, body_text='',
                     cc_list=None, bcc_list=None, reply_to_message_id=None,
                     skip_wrapper=False):
    """
    Send an email from the given inbox via SMTP. Stores an outbound AdminEmail record.
    body_html is the content area; it is automatically wrapped in the branded JrDev layout
    with the global signature appended (unless skip_wrapper=True).
    Returns the new AdminEmail.id.
    """
    address, password = _inbox_credentials(from_inbox)
    if not address or not password:
        raise ValueError(f'Credentials not configured for inbox: {from_inbox}')

    cc_list = cc_list or []
    bcc_list = bcc_list or []

    # Wrap body in branded layout
    wrapped_html = body_html if skip_wrapper else _wrap_email_html(body_html)

    # Build MIME message
    msg = MIMEMultipart('alternative')
    new_mid = f'<{uuid.uuid4()}@jr-dev.uk>'
    msg['Message-ID'] = new_mid
    msg['From'] = address
    msg['To'] = ', '.join(to_list)
    if cc_list:
        msg['Cc'] = ', '.join(cc_list)
    msg['Subject'] = subject
    if reply_to_message_id:
        msg['In-Reply-To'] = reply_to_message_id
        msg['References'] = reply_to_message_id

    if body_text:
        msg.attach(MIMEText(body_text, 'plain'))
    if wrapped_html:
        msg.attach(MIMEText(wrapped_html, 'html'))

    all_recipients = to_list + cc_list + bcc_list

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(address, password)
        smtp.sendmail(address, all_recipients, msg.as_string())

    # Compute thread linkage
    in_reply_to = reply_to_message_id or None
    thread_id = _compute_thread_id(in_reply_to, new_mid)

    record = AdminEmail(
        inbox=from_inbox,
        direction='outbound',
        message_id=new_mid,
        in_reply_to=in_reply_to,
        thread_id=thread_id,
        from_addr=address,
        to_addrs=json.dumps(to_list),
        cc_addrs=json.dumps(cc_list) if cc_list else None,
        bcc_addrs=json.dumps(bcc_list) if bcc_list else None,
        subject=subject,
        body_text=body_text,
        body_html=body_html,   # store original (unwrapped) content
        is_read=True,
        sent_at=datetime.utcnow(),
    )
    db.session.add(record)
    db.session.commit()
    return record.id
