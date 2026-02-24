from flask import Blueprint, render_template, request, send_file, redirect, url_for
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from flask_login import current_user, login_required

from app.decorators import require_role

contract = Blueprint('contract', __name__)


def _build_pdf_from_data(data):
    """Generate contract PDF from a dict (company_name, contractor_name, start_date, end_date, task_1..4, min_tasks, date)."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 40

    def draw_line(text, font="Helvetica", size=11, offset=18):
        nonlocal y
        c.setFont(font, size)
        c.drawString(40, y, text)
        y -= offset

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
    draw_line("Payment Condition: Payment is triggered only upon the successful completion of the Minimum Quantity of tasks defined in Section III.")
    draw_line("")
    draw_line("III. DELIVERABLES SCHEDULE (CUSTOMISABLE)", "Helvetica-Bold", 11, 20)
    draw_line('The 2nd Party agrees to work toward the following list of tasks regarding the "Software":')
    tasks = data.get("tasks", [])
    if not tasks:
        for i in range(1, 20):
            t = data.get(f"task_{i}", "")
            if t and t not in (f"[Insert Task {chr(64 + i)}]",):
                tasks.append(t)
    if not tasks:
        tasks = ["[No deliverables specified]"]
    for idx, task in enumerate(tasks):
        draw_line(f"Task {chr(65 + idx)}: {task}")
    draw_line(f'The Payment Trigger: To receive the £{pay} payment at the end of the week, the 2nd Party must complete at least {data.get("min_tasks", "1")} of the {len(tasks)} tasks listed above.')
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
    draw_line("1st Party Signature: ____________________ Date: __________ Print Name: ____________________ ")
    draw_line("")
    draw_line("2nd Party Signature: ____________________ Date: __________ Print Name: ____________________ ")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf


@contract.route('/contract/signup/<int:signup_id>/view')
@login_required
def view_contract_for_signup(signup_id):
    """View contract PDF for a signup (developer or business for that listing)."""
    from app.models import ListingSignup
    signup = ListingSignup.query.get_or_404(signup_id)
    listing = signup.listing
    can_view = (
        current_user.id == signup.user_id
        or current_user.id == listing.business_id
    )
    if not can_view:
        from flask import flash
        flash('Access denied.', 'danger')
        if current_user.role == 'DEVELOPER':
            return redirect(url_for('main.developer_joined_listings'))
        return redirect(url_for('main.review_gallery'))

    is_developer_viewing = (current_user.id == signup.user_id)
    developer_has_signed = signup.developer_signed_at is not None

    if listing.deliverables:
        tasks = [t.strip() for t in listing.deliverables.split('\n') if t.strip()]
    else:
        tasks = [t.strip() for t in (listing.technologies_required or '').split(',') if t.strip()]
    if not tasks:
        tasks = ['As per listing']

    if is_developer_viewing and not developer_has_signed:
        tasks = [f'[REDACTED \u2013 sign contract to view deliverable {i+1}]' for i in range(len(tasks))]

    data = {
        'company_name': listing.company_name,
        'contractor_name': signup.user.username,
        'start_date': listing.sprint_begins_at.strftime('%Y-%m-%d'),
        'end_date': listing.sprint_ends_at.strftime('%Y-%m-%d'),
        'pay': str(listing.pay_for_prototype),
        'min_tasks': str(listing.minimum_requirements_for_pay),
        'date': datetime.utcnow().strftime('%Y-%m-%d'),
        'tasks': tasks,
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
