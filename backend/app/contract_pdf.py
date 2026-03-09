"""
Contract PDF blueprint: secure view URL (signed token), PDF generation from signup or form data.

Routes: view_contract_for_signup (token + party check), generate_contract (business preview).
"""
import base64
from flask import Blueprint, request, send_file, url_for, current_app, abort
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from datetime import datetime
from flask_login import current_user, login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature

from app.decorators import require_role, require_verified

contract = Blueprint('contract', __name__)

CONTRACT_VIEW_SALT = 'contract-view'
TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 365  # 1 year


def _contract_signer():
    return URLSafeTimedSerializer(
        current_app.config.get('SECRET_KEY'),
        salt=CONTRACT_VIEW_SALT,
    )


def make_contract_token(signup_id):
    """Generate a signed token for viewing the contract for this signup. Only our app can create valid tokens."""
    return _contract_signer().dumps(signup_id)


def verify_contract_token(token, signup_id):
    """Return True if the token is valid and matches the given signup_id."""
    if not token:
        return False
    try:
        payload = _contract_signer().loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
        return payload == signup_id
    except (BadSignature, Exception):
        return False


def contract_view_url(signup_id):
    """Build the secure contract view URL with a signed token. Use in templates for 'View contract' links."""
    token = make_contract_token(signup_id)
    return url_for('contract.view_contract_for_signup', signup_id=signup_id, token=token)


def _wrap_text(c, text, font, size, max_width):
    """Split text into lines that fit within max_width (in points)."""
    if not text:
        return ['']
    words = text.split()
    lines = []
    current = []
    for word in words:
        trial = ' '.join(current + [word])
        if c.stringWidth(trial, font, size) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return lines


def _legal_name(user):
    """Return user's legal name (first + last) or username if names not set."""
    if user.first_name or user.last_name:
        return ' '.join(filter(None, [user.first_name, user.last_name])).strip()
    return user.username or '[Contractor Name]'


def _build_pdf_from_data(data):
    """Generate contract PDF from a dict. SOFTWARE SPRINT & ESCROW AGREEMENT format with Client, Developer, and JRDEV Ltd (Platform)."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin = 40
    bottom_margin = 60
    line_height = 14
    max_text_width = width - (2 * margin)
    y = height - 40

    def ensure_space(needed=line_height):
        nonlocal y
        if y < bottom_margin + needed:
            c.showPage()
            y = height - margin

    def draw_line(text, font="Helvetica", size=11, offset=18):
        nonlocal y
        c.setFont(font, size)
        if not text.strip():
            y -= offset
            return
        for line in _wrap_text(c, text, font, size, max_text_width):
            ensure_space()
            c.drawString(margin, y, line)
            y -= line_height
        y -= (offset - line_height) if offset > line_height else 0

    # Parse date for display (DD / MM / YYYY)
    agreement_date_raw = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    try:
        dt = datetime.strptime(agreement_date_raw, "%Y-%m-%d")
        date_display = f"{dt.day:02d} / {dt.month:02d} / {dt.year}"
    except (ValueError, TypeError):
        date_display = agreement_date_raw

    company_name = data.get("company_name", "[Business Legal Name]")
    company_address = data.get("company_address", "[Registered Address]")
    contractor_name = data.get("contractor_name", "[Developer Legal Name]")
    contractor_address = data.get("contractor_address", "[Registered Address]")
    platform_company_number = data.get("platform_company_number", "[_______]")
    platform_address = data.get("platform_address", "[Address]")
    start_date = data.get("start_date", "________________________")
    end_date = data.get("end_date", "________________________")
    duration_days = data.get("duration_days", "_______")
    duration_weeks = data.get("duration_weeks", "_______")

    pay_raw = data.get("pay", "20")
    try:
        pay_val = float(pay_raw)
        pay = f"{pay_val:.2f}" if pay_val != int(pay_val) else f"{int(pay_val):.2f}"
    except (TypeError, ValueError):
        pay = str(pay_raw)

    mandatory_tasks = data.get("mandatory_tasks") or []
    optional_tasks = data.get("optional_tasks") or []
    tasks = data.get("tasks", [])
    essential_count = int(data.get("essential_deliverables_count", 0) or 0)
    if not mandatory_tasks and not optional_tasks and tasks:
        mandatory_tasks = tasks[:essential_count] if essential_count > 0 else []
        optional_tasks = tasks[essential_count:] if essential_count > 0 else tasks
    elif not mandatory_tasks and not optional_tasks:
        for i in range(1, 20):
            t = data.get(f"task_{i}", "")
            if t and t.strip():
                tasks.append(t.strip())
        if tasks:
            mandatory_tasks = tasks[:essential_count] if essential_count > 0 else []
            optional_tasks = tasks[essential_count:] if essential_count > 0 else tasks

    min_tasks_raw = data.get("min_tasks", "1")
    min_tasks_val = int(min_tasks_raw) if str(min_tasks_raw).isdigit() else 1
    total_count = len(mandatory_tasks) + len(optional_tasks)
    if total_count > 0:
        min_tasks_val = min(min_tasks_val, total_count)

    # Title
    draw_line("SOFTWARE SPRINT & ESCROW AGREEMENT", "Helvetica-Bold", 13, 20)
    draw_line("(Governing Law: England and Wales)", "Helvetica", 10, 24)
    draw_line("")
    draw_line(f"This Agreement is made on [Date: {date_display}]", "Helvetica", 11, 20)
    draw_line("")
    draw_line("BETWEEN", "Helvetica-Bold", 11, 16)
    draw_line(f"{company_name}, of {company_address}, referred to as the \"Client\" or \"1st Party\";", "Helvetica", 11, 16)
    draw_line("")
    draw_line(f"{contractor_name}, of {contractor_address}, referred to as the \"Developer\" or \"2nd Party\"; and", "Helvetica", 11, 16)
    draw_line("")
    draw_line(f"JRDEV Ltd, company number {platform_company_number}, registered in England and Wales, with its principal office at {platform_address}, referred to as \"jrdev\" or the \"Platform\".", "Helvetica", 11, 16)
    draw_line("")
    draw_line("The Client, Developer, and jrdev are collectively referred to as the \"Parties.\"", "Helvetica", 11, 20)
    draw_line("")
    draw_line("I. PURPOSE", "Helvetica-Bold", 11, 20)
    draw_line("This Agreement sets out the terms under which the Developer will perform a software development sprint for the Client, facilitated and administered by jrdev using its escrow and review system.")
    draw_line("")
    draw_line("II. THE SPRINT & COMPENSATION", "Helvetica-Bold", 11, 20)
    draw_line(f"Sprint Start Date: {start_date}", "Helvetica", 11, 16)
    draw_line(f"Sprint End Date: {end_date}", "Helvetica", 11, 16)
    draw_line(f"Duration: {duration_days} days / {duration_weeks} weeks", "Helvetica", 11, 16)
    draw_line(f"Sprint Payment Total: £{pay} (GBP)", "Helvetica", 11, 16)
    draw_line("")
    draw_line("1. Payment Flow", "Helvetica-Bold", 11, 16)
    draw_line("a. Upon sprint launch, the Client shall pay the total Sprint Payment to jrdev Ltd, which will hold the funds in escrow via Stripe until completion.", "Helvetica", 11, 14)
    draw_line("b. jrdev deducts a 15 % (fifteen percent) non-refundable platform/service fee from each sprint payment for escrow, processing, and administrative services.", "Helvetica", 11, 14)
    draw_line("c. The remaining 85 % represents the Developer's payout, subject to Section III completion and review outcomes.", "Helvetica", 11, 20)
    draw_line("")
    draw_line("III. DELIVERABLES", "Helvetica-Bold", 11, 20)
    draw_line("Mandatory Deliverables (required for approval):", "Helvetica-Bold", 11, 16)
    for idx, task in enumerate(mandatory_tasks[:10]):
        draw_line(f"{chr(65 + idx)}. {task}", "Helvetica", 11, 14)
    if len(mandatory_tasks) < 2:
        for idx in range(len(mandatory_tasks), 2):
            draw_line(f"{chr(65 + idx)}. __________________________________________", "Helvetica", 11, 14)
    draw_line("")
    draw_line("Optional Deliverables:", "Helvetica-Bold", 11, 16)
    for idx, task in enumerate(optional_tasks[:10]):
        draw_line(f"{chr(67 + idx)}. {task}", "Helvetica", 11, 14)
    if len(optional_tasks) < 2:
        for idx in range(len(optional_tasks), 2):
            draw_line(f"{chr(67 + idx)}. __________________________________________", "Helvetica", 11, 14)
    draw_line("")
    draw_line(f"Completion Requirement: To receive payment, the Developer must complete all Mandatory items and at least {min_tasks_val} tasks in total (Mandatory + Optional).", "Helvetica", 11, 20)
    draw_line("")
    draw_line("IV. WORK SUBMISSION & REVIEW PROCESS", "Helvetica-Bold", 11, 20)
    draw_line("Developer Submission: At sprint end, the Developer uploads the deliverables and related code to the jrdev platform before the stated Sprint End Date.", "Helvetica", 11, 16)
    draw_line("")
    draw_line("Client Review Period: The Client has three (3) business days to review the uploaded deliverables and either:", "Helvetica", 11, 16)
    draw_line("select \"Approved\", confirming satisfactory completion; or", "Helvetica", 11, 14)
    draw_line("select \"Flag for Review\", triggering jrdev's dispute evaluation process.", "Helvetica", 11, 16)
    draw_line("")
    draw_line("jrdev Review: If flagged, jrdev independently checks whether the delivered work materially meets the scope defined in Section III.", "Helvetica", 11, 16)
    draw_line("If confirmed complete, jrdev releases the Developer's payout (minus the 15 % fee).", "Helvetica", 11, 14)
    draw_line("If substantially incomplete, jrdev issues a refund of the sprint payment (less the 15 % platform fee) to the Client.", "Helvetica", 11, 16)
    draw_line("")
    draw_line("Final Decision: jrdev's determination is final and binding for that sprint cycle.", "Helvetica", 11, 20)
    draw_line("")
    draw_line("V. INTELLECTUAL PROPERTY", "Helvetica-Bold", 11, 20)
    draw_line("Conditional Ownership: Upon successful completion and payment release, ownership of the Software code and deliverables transfers from the Developer to the Client.", "Helvetica", 11, 16)
    draw_line("Incomplete / Refunded Sprints: If a sprint is refunded or fails completion, ownership remains with the Developer.", "Helvetica", 11, 16)
    draw_line("Background IP: The Developer may use pre-existing code, libraries, or frameworks. The Developer grants the Client a non-exclusive licence to use such Background IP only as part of the final deliverables.", "Helvetica", 11, 20)
    draw_line("")
    draw_line("VI. CONFIDENTIALITY & PORTFOLIO RIGHTS", "Helvetica-Bold", 11, 20)
    draw_line("Definition: \"Confidential Information\" includes all non-public business, technical, or financial information exchanged under this Agreement.", "Helvetica", 11, 16)
    draw_line("Obligations: Each Party must keep Confidential Information secret and not use it for any purpose other than delivering or reviewing the sprint.", "Helvetica", 11, 16)
    draw_line("Portfolio Rights: The Developer may identify this engagement as \"Private Contract – Confidential Client\" and list technologies used or task names but may not share any screenshots or proprietary visuals.", "Helvetica", 11, 20)
    draw_line("")
    draw_line("VII. INDEPENDENT RELATIONSHIPS", "Helvetica-Bold", 11, 20)
    draw_line("The Developer acts as an independent contractor, not an employee or agent of the Client or jrdev.", "Helvetica", 11, 16)
    draw_line("jrdev acts solely as a facilitator and escrow/payment intermediary, not as a party to the software project itself.", "Helvetica", 11, 20)
    draw_line("")
    draw_line("VIII. LIABILITY & DISPUTES", "Helvetica-Bold", 11, 20)
    draw_line("Liability Cap: Each Party's total liability shall not exceed the total amount of the Sprint Payment, except for wilful misconduct or confidentiality breaches.", "Helvetica", 11, 16)
    draw_line("Indemnity: The Developer indemnifies the Client and jrdev against third-party intellectual-property claims arising from the delivered work.", "Helvetica", 11, 16)
    draw_line("Good-Faith Mediation: jrdev may require mediation before any formal claim is filed.", "Helvetica", 11, 20)
    draw_line("")
    draw_line("IX. TERMINATION", "Helvetica-Bold", 11, 20)
    draw_line("This Agreement terminates upon release of payment or refund and completion of any associated review.", "Helvetica", 11, 16)
    draw_line("Clauses III–VIII survive termination to protect IP and confidentiality rights.", "Helvetica", 11, 20)
    draw_line("")
    draw_line("X. GOVERNING LAW", "Helvetica-Bold", 11, 20)
    draw_line("This Agreement shall be governed by and construed in accordance with the laws of England and Wales, and the Courts of England and Wales shall have exclusive jurisdiction.", "Helvetica", 11, 20)
    draw_line("")
    draw_line("XI. SIGNATURES", "Helvetica-Bold", 11, 20)
    sig_h = 40
    sig_w = 140
    draw_line("Party", "Helvetica-Bold", 10, 14)
    draw_line("Client (1st Party)", "Helvetica", 10, 12)
    ensure_space(sig_h)
    business_sig = data.get("business_signature_image")
    if business_sig and isinstance(business_sig, str) and business_sig.startswith("data:image"):
        try:
            b64 = business_sig.split(",", 1)[1]
            img = ImageReader(BytesIO(base64.b64decode(b64)))
            c.drawImage(img, margin, y - sig_h, width=sig_w, height=sig_h)
        except Exception:
            c.setFont("Helvetica", 9)
            c.drawString(margin, y - 14, "__________________________")
    else:
        c.setFont("Helvetica", 9)
        c.drawString(margin, y - 14, "__________________________")
    y -= sig_h + 4
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Date: __________  Printed Name: __________________________")
    y -= 28
    draw_line("Developer (2nd Party)", "Helvetica", 10, 12)
    ensure_space(sig_h)
    dev_sig = data.get("developer_signature_image")
    if dev_sig and isinstance(dev_sig, str) and dev_sig.startswith("data:image"):
        try:
            b64 = dev_sig.split(",", 1)[1]
            img = ImageReader(BytesIO(base64.b64decode(b64)))
            c.drawImage(img, margin, y - sig_h, width=sig_w, height=sig_h)
        except Exception:
            c.setFont("Helvetica", 9)
            c.drawString(margin, y - 14, "__________________________")
    else:
        c.setFont("Helvetica", 9)
        c.drawString(margin, y - 14, "__________________________")
    y -= sig_h + 4
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Date: __________  Printed Name: __________________________")
    y -= 28
    draw_line("JRDEV Ltd (Platform)", "Helvetica", 10, 12)
    ensure_space(sig_h)
    c.setFont("Helvetica", 9)
    c.drawString(margin, y - 14, "__________________________")
    y -= sig_h + 4
    c.drawString(margin, y, "Date: __________  Printed Name: __________________________")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf


@contract.route('/contract/signup/<int:signup_id>/view')
@login_required
@require_verified
def view_contract_for_signup(signup_id):
    """View contract PDF for a signup. Access only with a valid signed link (token) and only for the developer or business."""
    from app.models import ListingSignup
    if not current_user.is_authenticated:
        abort(403)
    signup = ListingSignup.query.get_or_404(signup_id)
    listing = signup.listing
    token = request.args.get('token', '')
    has_valid_token = verify_contract_token(token, signup_id)
    is_party = (
        current_user.id == signup.user_id
        or current_user.id == listing.business_id
    )
    if not (has_valid_token and is_party):
        abort(403)

    is_developer_viewing = (current_user.id == signup.user_id)
    developer_has_signed = signup.developer_signed_at is not None

    mandatory_tasks = list(listing.essential_deliverables_list)
    optional_tasks = list(listing.optional_deliverables_list)
    if not mandatory_tasks and not optional_tasks:
        mandatory_tasks = ['As per listing']

    if is_developer_viewing and not developer_has_signed:
        mandatory_tasks = [f'[REDACTED \u2013 sign contract to view mandatory {i+1}]' for i in range(len(mandatory_tasks))]
        optional_tasks = [f'[REDACTED \u2013 sign contract to view optional {i+1}]' for i in range(len(optional_tasks))]

    start_dt = listing.sprint_begins_at
    end_dt = listing.sprint_ends_at
    delta = (end_dt - start_dt).days if end_dt and start_dt else 7
    weeks = max(1, delta // 7)

    contractor_address = getattr(signup, 'developer_registered_address', None) or None
    data = {
        'company_name': listing.company_name,
        'company_address': getattr(listing, 'company_address', None) or None,
        'contractor_name': _legal_name(signup.user),
        'contractor_address': contractor_address,
        'platform_company_number': current_app.config.get('PLATFORM_COMPANY_NUMBER', '[_______]'),
        'platform_address': current_app.config.get('PLATFORM_ADDRESS', '[Address]'),
        'start_date': start_dt.strftime('%Y-%m-%d'),
        'end_date': end_dt.strftime('%Y-%m-%d'),
        'duration_days': str(delta),
        'duration_weeks': str(weeks),
        'pay': f'{listing.pay_for_prototype / 100:.2f}',
        'min_tasks': str(listing.minimum_requirements_for_pay),
        'date': datetime.utcnow().strftime('%Y-%m-%d'),
        'mandatory_tasks': mandatory_tasks,
        'optional_tasks': optional_tasks,
        'developer_signature_image': getattr(signup, 'developer_signature_image', None),
        'business_signature_image': getattr(signup, 'business_signature_image', None),
    }
    buf = _build_pdf_from_data(data)
    return send_file(buf, mimetype='application/pdf', as_attachment=False, download_name='Sprint_Agreement.pdf')


@contract.route('/generate_contract', methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def generate_contract():
    """Generate contract PDF from form data (business dashboard). Company/contractor from session when not in form."""
    form_data = request.form
    tasks = [v.strip() for k, v in sorted(form_data.items()) if k.startswith('task_') and v.strip()]
    company_name = form_data.get('company_name', '').strip() or (current_user.username if current_user.is_authenticated else '[Company Name]')
    contractor_name = form_data.get('contractor_name', '').strip() or '[To be assigned]'
    start_date = form_data.get('start_date', '[Start Date]')
    end_date = form_data.get('end_date', '[End Date]')
    essential_count = int(form_data.get('essential_deliverables_count', 0) or 0)
    mandatory_tasks = tasks[:essential_count] if essential_count > 0 else []
    optional_tasks = tasks[essential_count:] if essential_count > 0 else tasks

    duration_days = '_______'
    duration_weeks = '_______'
    if start_date and end_date and start_date != '[Start Date]' and end_date != '[End Date]':
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            delta = (end_dt - start_dt).days
            duration_days = str(max(1, delta))
            duration_weeks = str(max(1, delta // 7))
        except (ValueError, TypeError):
            pass

    platform_company_number = current_app.config.get('PLATFORM_COMPANY_NUMBER', '[_______]')
    platform_address = current_app.config.get('PLATFORM_ADDRESS', '[Address]')
    data = {
        'company_name': company_name,
        'company_address': form_data.get('company_address', '').strip() or None,
        'contractor_name': contractor_name,
        'contractor_address': None,  # Developer provides at e-sign; use placeholder for preview
        'platform_company_number': form_data.get('platform_company_number', '').strip() or platform_company_number,
        'platform_address': form_data.get('platform_address', '').strip() or platform_address,
        'start_date': start_date,
        'end_date': end_date,
        'duration_days': duration_days,
        'duration_weeks': duration_weeks,
        'pay': form_data.get('pay', '20'),
        'min_tasks': form_data.get('min_tasks', '1'),
        'essential_deliverables_count': str(essential_count),
        'date': form_data.get('date') or datetime.utcnow().strftime('%Y-%m-%d'),
        'mandatory_tasks': mandatory_tasks,
        'optional_tasks': optional_tasks,
        'tasks': tasks,
    }
    buf = _build_pdf_from_data(data)
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name='NDA_Sprint_Agreement.pdf')
