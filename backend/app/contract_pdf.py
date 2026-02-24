import base64
from flask import Blueprint, request, send_file, url_for, current_app, abort
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from datetime import datetime
from flask_login import current_user, login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature

from app.decorators import require_role

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


def _build_pdf_from_data(data):
    """Generate contract PDF from a dict. Supports mandatory_tasks + optional_tasks, or legacy tasks / task_1..N."""
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

    draw_line("SOFTWARE DEVELOPMENT NON-DISCLOSURE & SPRINT AGREEMENT", "Helvetica-Bold", 13, 28)
    draw_line("")
    draw_line("I. THE PARTIES", "Helvetica-Bold", 11, 20)
    agreement_date = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    draw_line(f'This Agreement, hereinafter known as the "Agreement", is created on {agreement_date} between {data.get("company_name", "[Company Name]")}, hereinafter known as the "1st Party", and {data.get("contractor_name", "[Contractor Name]")}, hereinafter known as the "2nd Party", and collectively known as the "Parties".')
    draw_line("")
    draw_line("II. THE SPRINT & COMPENSATION", "Helvetica-Bold", 11, 20)
    pay = data.get("pay", "20")
    draw_line(f'Sprint Timeframe: One (1) week, commencing on {data.get("start_date", "[Start Date]")} and ending on {data.get("end_date", "[End Date]")}.')
    draw_line(f"Payment Amount: £{pay} (GBP).")
    draw_line("Payment Condition: Payment is triggered only upon the successful completion of the deliverables defined in Section III (see Payment Trigger below).")
    draw_line("")
    draw_line("III. DELIVERABLES SCHEDULE (CUSTOMISABLE)", "Helvetica-Bold", 11, 20)
    mandatory_tasks = data.get("mandatory_tasks") or []
    optional_tasks = data.get("optional_tasks") or []
    tasks = data.get("tasks", [])
    if not tasks and not mandatory_tasks and not optional_tasks:
        for i in range(1, 20):
            t = data.get(f"task_{i}", "")
            if t and t not in (f"[Insert Task {chr(64 + i)}]",):
                tasks.append(t)
    if mandatory_tasks or optional_tasks:
        draw_line('The 2nd Party agrees to work toward the following deliverables regarding the "Software":')
        draw_line("")
        if mandatory_tasks:
            draw_line("Mandatory (Required for Payment):", "Helvetica-Bold", 11, 18)
            for idx, task in enumerate(mandatory_tasks):
                draw_line(f"  {chr(65 + idx)}. {task}")
            draw_line("")
        if optional_tasks:
            draw_line("Optional:", "Helvetica-Bold", 11, 18)
            for idx, task in enumerate(optional_tasks):
                draw_line(f"  {chr(65 + len(mandatory_tasks) + idx)}. {task}")
            draw_line("")
        total_count = len(mandatory_tasks) + len(optional_tasks)
        min_tasks = data.get("min_tasks", "1")
        if mandatory_tasks and optional_tasks:
            draw_line(f'Payment Trigger: To receive the £{pay} payment at the end of the week, the 2nd Party must complete all Mandatory deliverables listed above and at least {min_tasks} task(s) in total (Mandatory + Optional) out of {total_count}.')
        elif mandatory_tasks:
            draw_line(f'Payment Trigger: To receive the £{pay} payment at the end of the week, the 2nd Party must complete all Mandatory deliverables listed above ({len(mandatory_tasks)} task(s)).')
        else:
            draw_line(f'Payment Trigger: To receive the £{pay} payment at the end of the week, the 2nd Party must complete at least {min_tasks} of the {total_count} Optional tasks listed above.')
    else:
        draw_line('The 2nd Party agrees to work toward the following list of tasks regarding the "Software":')
        if not tasks:
            tasks = ["[No deliverables specified]"]
        for idx, task in enumerate(tasks):
            draw_line(f"Task {chr(65 + idx)}: {task}")
        draw_line(f'Payment Trigger: To receive the £{pay} payment at the end of the week, the 2nd Party must complete at least {data.get("min_tasks", "1")} of the {len(tasks)} tasks listed above.')
    draw_line("")
    draw_line("IV. INTELLECTUAL PROPERTY (IP) & TERMINATION", "Helvetica-Bold", 11, 20)
    draw_line("Conditional Ownership: The 1st Party shall have sole ownership of the Software and related source code only upon full payment to the 2nd Party.")
    draw_line("Failed Sprint: If the 2nd Party does not meet the 'Minimum Quantity' of tasks, they are terminated for the sprint. In this case, the 2nd Party retains all rights and ownership to the code produced; the 1st Party shall have no right to use or copy said code.")
    draw_line("Background IP: The 2nd Party may use their own pre-existing libraries/code. They grant the 1st Party a non-exclusive license to use such code only as integrated into the Software deliverables.")
    draw_line("")
    draw_line("V. CONFIDENTIALITY & CV RIGHTS", "Helvetica-Bold", 11, 20)
    draw_line("Confidential Information: Includes source code, business plans, and data not available to the public. It does not include widely used programming practices or algorithms.")
    draw_line("Obligations: The Parties shall maintain information in the strictest confidence. Neither Party shall use the Confidential Information for their sole benefit without written approval.")
    draw_line("CV/Portfolio Rights: Notwithstanding Section V, the 2nd Party is granted the right to list the following:")
    draw_line('Client Identity: Must be referred to as "Private Contract" or "Confidential Client." (Company name remains confidential).')
    draw_line('Attributions: May list the specific Technologies Used and the Task Names from Section III.')
    draw_line('Visuals: No screenshots or UI captures are permitted.')
    draw_line("")
    draw_line("VI. GENERAL TERMS", "Helvetica-Bold", 11, 20)
    draw_line("Relationship: No Party is an employee or partner.")
    draw_line("Time Period: The duty of confidentiality remains until the information no longer qualifies as a trade secret.")
    draw_line("Severability: If any provision is found unenforceable, the remainder remains in effect.")
    draw_line("Governing Law: This Agreement shall be governed under the laws of England and Wales.")
    draw_line("")
    draw_line("Signatures:", "Helvetica-Bold", 11, 20)
    sig_h = 40
    sig_w = 140
    draw_line("1st Party (Company) Signature:", "Helvetica", 10, 16)
    ensure_space(sig_h)
    business_sig = data.get("business_signature_image")
    if business_sig and isinstance(business_sig, str) and business_sig.startswith("data:image"):
        try:
            b64 = business_sig.split(",", 1)[1]
            img = ImageReader(BytesIO(base64.b64decode(b64)))
            c.drawImage(img, margin, y - sig_h, width=sig_w, height=sig_h)
        except Exception:
            pass
    else:
        c.setFont("Helvetica", 9)
        c.drawString(margin, y - 14, "____________________")
    y -= sig_h + 4
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Date: __________  Print Name: ____________________")
    y -= 28
    draw_line("2nd Party (Contractor) Signature:", "Helvetica", 10, 16)
    ensure_space(sig_h)
    dev_sig = data.get("developer_signature_image")
    if dev_sig and isinstance(dev_sig, str) and dev_sig.startswith("data:image"):
        try:
            b64 = dev_sig.split(",", 1)[1]
            img = ImageReader(BytesIO(base64.b64decode(b64)))
            c.drawImage(img, margin, y - sig_h, width=sig_w, height=sig_h)
        except Exception:
            pass
    else:
        c.setFont("Helvetica", 9)
        c.drawString(margin, y - 14, "____________________")
    y -= sig_h + 4
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Date: __________  Print Name: ____________________")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf


@contract.route('/contract/signup/<int:signup_id>/view')
@login_required
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

    data = {
        'company_name': listing.company_name,
        'contractor_name': signup.user.username,
        'start_date': listing.sprint_begins_at.strftime('%Y-%m-%d'),
        'end_date': listing.sprint_ends_at.strftime('%Y-%m-%d'),
        'pay': str(listing.pay_for_prototype),
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
@require_role('BUSINESS')
def generate_contract():
    """Generate contract PDF from form data (business dashboard). Protected and CSRF via form.hidden_tag()."""
    form_data = request.form
    tasks = [v.strip() for k, v in sorted(form_data.items()) if k.startswith('task_') and v.strip()]
    data = {
        'company_name': form_data.get('company_name', '[Company Name]'),
        'contractor_name': form_data.get('contractor_name', '[Contractor Name]'),
        'start_date': form_data.get('start_date', '[Start Date]'),
        'end_date': form_data.get('end_date', '[End Date]'),
        'pay': form_data.get('pay', '20'),
        'min_tasks': form_data.get('min_tasks', '1'),
        'date': form_data.get('date') or datetime.utcnow().strftime('%Y-%m-%d'),
        'tasks': tasks,
    }
    buf = _build_pdf_from_data(data)
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name='NDA_Sprint_Agreement.pdf')
