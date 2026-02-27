# JrDev Platform — Product Vision

## What Is JrDev?

JrDev is a web platform that connects **student developers** with **local businesses** who need affordable, rapid software prototyping. Businesses post sprint briefs; students apply, sign contracts, build prototypes under a deadline, and get paid. The platform handles confidentiality, contracts, payments, and review — so neither side takes on unnecessary risk.

**Tagline:** Rapid prototyping by emerging talent.

---

## User Roles

### DEVELOPER (Student)
- Register, set up 2FA, build a profile (headline, bio, tech stack, links, custom markdown, pinned projects, theme customisation).
- Browse open sprint listings — see technologies required, pay, timeline, rating — but **not** deliverables (confidentiality).
- Apply to a listing → status: `pending`.
- Once accepted by business: e-sign the JrDev contract (canvas signature captured as base64 image).
- After both parties sign: deliverables are revealed; sprint clock starts.
- Submit work: GitHub repo URL, demo video URL, checkbox which deliverables were met.
- Rate the business (1–5) after sprint.
- Withdraw if they cannot complete.
- Profile stats auto-update: `contracts_attempted`, `contracts_won`, `prototypes_completed`, technology usage counts.

### BUSINESS
- Register, set up 2FA.
- Sprint Creator dashboard: write an idea brief, set essential deliverables, optional deliverables, tech stack tags, developer allocation (1–5 devs), sprint timeline (1–7 days), investment per dev (£50–£300), total deliverables count, essential deliverables count.
- Launch Sprint → creates a `SprintListing`.
- View "Your Listings" page: see who applied, accept/deny developers.
- E-sign contracts with accepted developers (canvas signature).
- After sprint ends: review each developer's submission (GitHub, video, deliverables checklist).
- Mark as reviewed (triggers payment), flag for dispute, or approve/refund. **48-hour deadline:** if the business does not review or flag within 48 hours of the developer submitting, payment auto-releases to the developer.
- Rate developers (1–5).
- View any developer's public profile (stack, rating, markdown, pinned projects).
- Billing page with Stripe integration (add card, setup intents).

---

## Core Flow: The 4-Step Sprint

### Step 1 — Define Your Vision
Business fills in project outline on sprint creator: idea description, essential deliverables, optional deliverables, technologies required. Sets budget, timeline, and dev allocation via sidebar sliders. Clicks "Launch Sprint" to publish.

### Step 2 — Developer Screening & Confidentiality
Developers see only the tech stack and basic listing info — **not** the deliverables. They apply. Business reviews applicants (view profiles, accept/deny). Accepted developers must e-sign the NDA + Sprint Agreement before seeing deliverables.

### Step 3 — Rapid Development Sprint
Once contract is fully signed (both parties), the developer sees deliverables and the sprint timer starts. They build against the deadline. They submit GitHub URL, demo video, and mark which deliverables they completed.

### Step 4 — Review
Business reviews submissions through the platform. If essential deliverables are met → approve and release payment. If not → full refund guarantee. Business can flag for dispute. Both parties can rate each other.

**48-hour review deadline:** From the moment a developer submits their prototype (`prototype_submitted_at`), the business has **48 hours** to take a review action (mark as reviewed/approve payment, or flag for dispute). If the business does **not** take any action within 48 hours, **payment is automatically released to the developer**. Any action within the 48 hours (approve or flag) stops the clock and is respected; only when the business does nothing does auto-release apply. This removes the current lack of urgency for the business to review and ensures developers get paid in a predictable timeframe.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt, Flask-Mail, Flask-Migrate, Flask-WTF (CSRF) |
| Database | SQLite (site.db) via SQLAlchemy |
| Frontend | Jinja2 templates, Tailwind CSS (CDN), custom CSS (glassmorphism / liquid-glass design system) |
| JS | Vanilla JS (no framework) — business_dashboard.js, developer_dashboard.js |
| PDF | ReportLab — contract PDF generation |
| Auth | bcrypt passwords, TOTP 2FA (pyotp + qrcode), email verification tokens (itsdangerous) |
| Payments | Stripe (optional, customer creation + SetupIntents for saved cards) |
| Fonts | Space Grotesk (display), Inter (body), Material Icons / Material Symbols |

---

## Database Models

### User
`id, username, email, image_file, password, role (DEVELOPER/BUSINESS), is_verified, two_factor_secret, stripe_customer_id`

### DeveloperProfile
`user_id, headline, bio, location, availability, technologies (comma-separated), github_link, linkedin_link, portfolio_link, custom_markdown, profile_theme, profile_animation, profile_panel_style, profile_background, contracts_attempted, contracts_won, prototypes_completed`

### PinnedProject
`profile_id, title, description, link, tags`

### Project (legacy)
`title, date_posted, content, user_id`

### SprintListing
`business_id, company_name, max_talent_pool, pay_for_prototype, business_rating, technologies_required, deliverables (newline-separated), essential_deliverables (newline-separated), essential_deliverables_count, sprint_timeline_days, signup_ends_at, sprint_begins_at, sprint_ends_at, minimum_requirements_for_pay, status`

### ListingSignup
`listing_id, user_id, joined_at, status (pending/accepted/denied/cancelled), developer_signed_at, business_signed_at, developer_signature_image, business_signature_image, github_submission_url, demo_video_url, prototype_submitted_at, requirements_met, reviewed_at, flagged_for_review, business_rating_of_developer, developer_rating_of_business, developer_withdrew`

---

## Pages & Templates

| Template | Purpose |
|----------|---------|
| `home.html` | Public landing page: hero, 4-step sprint (tabbed + dynamic visuals), Why JrDev, For Students / For Businesses cards, trust/social proof, pricing hint, More Information, CTA. See **Home Page Redesign** below for current redesign goals. |
| `login.html` | Login form |
| `register.html` | Registration form (role selection) |
| `setup_2fa.html` | QR code for TOTP setup |
| `verify_2fa.html` | 2FA token verification |
| `account.html` | Account overview |
| `developer_dashboard.html` | Developer profile, stats, markdown editor, pinned projects |
| `edit_profile.html` | Edit developer profile form |
| `developer_listings.html` | Browse available sprint listings |
| `developer_joined_listings.html` | Developer's joined sprints: status, sign contract, submit work, rate |
| `business_dashboard.html` | Sprint Creator: idea box, deliverables, tech tags, contract form, sidebar sliders |
| `business_my_listings.html` | Business listing overview with developer management |
| `business_dashboard_your-developers.html` | Detailed developer management: accept/deny, sign, review, rate |
| `developer_profile_view.html` | Public developer profile (for businesses) |
| `review_gallery.html` | Business review page |
| `billing.html` | Stripe card management |
| `about.html` | About page |
| `privacy.html` | Privacy policy |
| `terms.html` | Terms & conditions |
| `support.html` | Support page |
| `partials/developer_card.html` | Reusable developer card (video, review, rate) |
| `partials/signature_modal.html` | Canvas signature capture modal |
| `partials/flash_messages.html` | Flash message display |
| `404.html` | Custom 404 page (extends info_layout) |
| `layout.html` | Base layout |
| `auth_layout.html` | Auth page layout |
| `business_layout.html` | Business nav + layout |
| `developer_layout.html` | Developer nav + layout |
| `info_layout.html` | Info pages layout |

---

## Home Page Redesign (Startup Website)

Redesign goals based on external feedback. Implement so the landing feels professional, trustworthy, and conversion-focused.

### First Impressions & Audience Balance
- **Keep**: Headline hierarchy and purple "next generation" contrast on dark background; subheadline clarity. Audience is clear: early-stage founders / non-technical entrepreneurs for budget-friendly V1.
- **Fix**: Hero is heavily business-focused. Students can feel they’re in the wrong place until the bottom. **Segment immediately**: add a small **toggle in the hero** (e.g. "I'm a Business" / "I'm a Developer") or a clear **"Are you a developer? [Apply here]"** link in the top nav so both audiences know where they belong without scrolling.

### Layout & Spacing
- **Tighten hero**: Reduce the gap between subheadline and CTA buttons so the action feels part of the message.
- **4-Step Sprint vs Why JrDev balance**: The 4-Step Sprint section feels **cramped** compared to the vast white space in Why JrDev. Give the 4-Step section more room; reduce the **gap between Why JrDev cards and the "See JrDev in action"** header (currently too large). **Inside Why JrDev cards**: text feels tight — give body text room to breathe (padding/line-height).
- **Section grounding**: Avoid jarring "zebra" striping (dark hero → stark white). Use a **softer transition**: very dark grey or a **subtle gradient** between hero and first light section to keep the premium feel. For light sections, consider **very light lavender/grey** background to tie brand colors together (or dark mode throughout) instead of stark white.

### Navigation & Usability
- **Nav bar**: Increase size of logo and nav links for clarity at high resolutions. The **"Get Started"** (or primary CTA) button in the top right is too small — **make it pop more**; it should be the obvious primary goal.
- **4-Step Sprint**: Current tab-style layout **requires clicking** to see value — don’t make users work to understand the process. Use a **vertical timeline** or **larger, clearer icons** so all four steps are visible and scannable at a glance. Ensure the visual below (screenshot/mock) **updates clearly** when switching steps so it doesn’t feel static.

### Conversion & Trust
- **Video**: Replace the gray play-button placeholder with a **YouTube embed** (video URL: `https://www.youtube.com/watch?v=ujdFPoCeFM4`).
- **Copy**: Replace "Cheap Prototyping" with **"Cost-Effective"** or **"Budget-Friendly"** so it doesn’t imply low quality.
- **Pricing**: Add **"Starting at £50"** (or range) so the first question — "Can I afford this?" — is answered. Near CTA or in a pricing hint.
- **Payment model**: Add a **"How it works" for payment** on the page (e.g. per-sprint budget you set, not hourly/subscription). Knowing the financial model upfront reduces "click-fear."
- **Quality / "Junior" stigma**: Over-index on **quality control**. The Developer Screening section is mentioned but the **screenshot next to it is too small to read**. Use a **larger, readable screenshot or visual** so visitors see proof that students are vetted and won’t "break the site." Strengthen copy: **quality oversight**, **hand-picked talent**, or how students are selected.
- **Proof**: Add or strengthen **"Trusted by"** or **"Past Projects"** so visitors see why to trust students with their IP.

### Color & Visual Consistency
- **Hero → body**: The **biggest area for improvement** is the jump from dark hero to white body. Either **dark mode throughout** or **very light lavender/grey** for light sections to tie purple/indigo brand together. No stark white vs dark "zebra."
- **Contrast**: For Students / For Businesses cards — strengthen border or background so they don’t look floating; bullet point text is **quite small** — increase size for readability.
- **Hero sub-headline**: "Rapid prototyping..." is quite thin and grey — **increase font weight or brightness** so it’s readable on all monitors.
- **CTA hierarchy**: Primary CTA (e.g. "Get Started" / "Hire Talent") should clearly dominate; "Join as Developer" secondary. Use **green only for success states**. Stick to **two primary brand colors** (purple/indigo); avoid too many accents.

### Content & Typography
- **Why JrDev**: Body text in the value boxes is quite small vs headers. Increase readability (size or weight) and give text room to breathe.
- **4-Step Sprint**: Use punchier copy (e.g. "We match you with the right developer in 24 hours" instead of "Developers match the project"). Show steps clearly without requiring tabs to parse.
- **Testimonials ("What people say")**: Cards are **different heights** based on text length. Use **min-height** (or similar) so cards are uniform and the section feels symmetrical.

### Content Decisions (confirmed)
- **Video**: Keep "See JrDev in action" and embed: `https://www.youtube.com/watch?v=ujdFPoCeFM4`.
- **Pricing**: Show **"Starting at £50"** and clarify payment model (per-sprint, you set budget when you launch).
- **Trust**: Reviews/testimonials section with **uniform card heights** (min-height); placeholder structure for product owner to fill with real ratings later.

---

## Business Dashboard Improvements

Improvements based on user feedback: prioritize action over data, improve discoverability on the Developers page, increase billing clarity and trust, and polish global UI/UX for the business area.

### 1. Dashboard Page — Prioritize Action over Data

- **Issue**: Dashboard acts as a flat collection of stats; nothing stands out as the most important. Users aren’t clearly told what to do next.
- **Hero metric**: Choose one “North Star” metric (e.g. Active Developers or Total Spend) and make it **twice as large** as the other metrics so hierarchy is obvious.
- **“Attention Required” section**: Add a small notification area at the **top** of the dashboard for urgent items (e.g. “2 Pending Invoices”, “New Applicant for [Role]”). Action-oriented, not buried.
- **Empty states**: For new users, avoid charts that look broken or zeroed out. Use **skeleton loaders** or a **“Get Started”** prompt inside empty chart areas so the UI feels intentional.

### 2. Developers Page — Search & Filtering

- **Issue**: List view is dense; with many developers (e.g. 50), finding one person is a chore.
- **Search prominence**: Move the search bar to a **more prominent position** (top left or center).
- **Quick filters**: Add filters for status (e.g. **Active**, **Onboarding**, **Offboarding**) so power users can narrow the list quickly.
- **Status indicators**: Use **subtle color-coded pills** for status (e.g. green dot or low-opacity green pill for “Active”) so status is scannable at a glance instead of plain text.
- **Row hover**: When hovering over a developer row, **highlight the row** slightly so the eye can track horizontal data across a wide screen.

### 3. Billing Page — Clarity & Trust

- **Issue**: Invoice history feels generic; “boring is better” in fintech — users want 100% clarity on where their money is going.
- **Direct actions**: Do **not** hide “Download Invoice” / “View PDF” inside a three-dot menu if space allows. Use a **visible icon or small button** on the right side of each row.
- **Next billing date**: Highlight the **upcoming payment** prominently (users care more about what they’re about to pay than past payments).
- **Payment method visibility**: Show a **small card brand icon** (e.g. Visa/Mastercard logo) next to billing settings so users see which account is charged without drilling in.

### 4. General UI/UX Polish (Business Area)

- **Navigation contrast**: The sidebar is dark; the **active** tab (current page) must be **very distinct**. Use a high-contrast accent (e.g. vibrant blue or purple) for the active state.
- **Consistent margins**: Ensure **padding between cards** (white/grey boxes) is **consistent** across dashboard pages. Inconsistent gaps create a “vibrating” effect.
- **Typography**: For data-heavy dashboards, prefer a **geometric sans** (e.g. Inter or Montserrat) over default system fonts; vision already lists Inter for body — ensure business dashboard uses it consistently.

---

## Developer Dashboard Improvements

Professional feedback: sharpen the developer dashboard from "personal project" to "production-ready product" while keeping the Neon/Liquid Glass aesthetic and dark mode. Apply the following improvements.

### 1. Dashboard & Profile Customization

- **Profile image fallback**  
  - **Where**: Circular profile area in the sidebar (and edit-profile where it shows "Profile" or broken image).  
  - **Issue**: Broken image or plain text fallback feels unpolished.  
  - **Improvement**: Use a **stylized SVG avatar or initials** (e.g. "AD" for Aspiring Developer) as the default when no image is uploaded. Same treatment in sidebar and edit-profile.

- **Empty state — Pinned Projects**  
  - **Where**: "Pinned Projects" section on the dashboard.  
  - **Issue**: Dashed border and folder icon feel thin; empty state is easy to miss.  
  - **Improvement**: Use a **more prominent empty-state illustration** or a **clear call-to-action in the center** of the box, not only in the top-right.

### 2. Information Hierarchy & Typography

- **Stats card contrast**  
  - **Where**: "Stats" card on the developer dashboard.  
  - **Issue**: Labels (e.g. "Prototypes Attempted") and numbers (e.g. 0) have similar visual weight; hard to scan.  
  - **Improvement**: Make the **numbers larger** and use a **brighter accent** (Mint/Neon) so they "pop" and read as the primary focus.

- **Deliverables readability (Joined Listings)**  
  - **Where**: Joined Listings page, "Deliverables (From Contract)" section.  
  - **Issue**: Long text (e.g. marketplace UI description) is difficult to scan.  
  - **Improvement**: **Increase line-height (leading)** and **add margin between bullet points** so deliverables are easy to read.

### 3. Form Design & UX

- **Input field styling**  
  - **Where**: All text inputs and textareas (Edit Profile, Submit Work, etc.).  
  - **Issue**: Dark-on-dark makes input boundaries feel "mushy."  
  - **Improvement**: Add a **subtle 1px border** that **brightens on :focus**. Ensure **placeholder text** has enough contrast to be readable but is clearly distinct from user-entered text.

- **Success / action feedback (Upload Prototype)**  
  - **Where**: Transition after submitting work (e.g. from joined listing form to "Under Review" state).  
  - **Issue**: Form just disappears and is replaced by text; feels abrupt.  
  - **Improvement**: Use a **success toast** or **progress indicator**. Keep the "Under Review" badge but make the transition feel **celebratory** (e.g. toast + short confirmation message).

### 4. Visual Consistency — Glow Effect

- **Where**: "About Me" card vs "Pinned Projects" and other cards.  
- **Issue**: "About Me" has a heavy purple outer glow; others don't — page feels lopsided.  
- **Improvement**: Either apply a **very subtle glow to all cards** for consistency, or **reserve glow only for active states or the primary CTA** so it's purposeful, not random.

### 5. Mobile & Responsiveness

- **Sidebar layout**  
  - **Where**: Developer dashboard (left sidebar + right content).  
  - **Issue**: On tablets/small screens the sidebar can squash content.  
  - **Improvement**: Add a **breakpoint** where the sidebar either **moves to the top** (under the header) or becomes a **collapsible drawer** so content has room on small viewports.

---

## Design System

- **Glassmorphism / Liquid Glass**: translucent panels with backdrop blur, subtle gradients, inner glow borders.
- **Design tokens (canonical):** Primary: `--primary-mint` (#4f46e5). Secondary: `--secondary-purple` (#0d9488). Dark navy: `#0F172A` / `--bg-navy`. **Source of truth:** `backend/app/static/css/liquid-glass.css`. All agents and styles should use these tokens; do not hardcode conflicting hex in skills or copy. **Home page:** favour two primary brand colours; green for success only.
- **CSS files**: `liquid-glass.css` (shared glass tokens), `home.css` (home page animations + sprint section + comparison + trust bar), `main.css`, `developer_themes.css`.
- **Animations**: scroll-reveal, gradient text shimmer, badge pulse, hover lifts; sprint tab content must update visually when steps change.
- **Home landing**: Hero CTA "Hire Talent" (primary), "Join as Developer" (secondary); softer hero-to-body transition (dark grey/gradient or light lavender-grey sections, no stark zebra); nav CTA prominent; no empty video block; trust/pricing/quality copy and layout as per Home Page Redesign.
- **Themes**: Developer profiles support `mint, ocean, sunset, neon, rose, amber` + animation/panel/background options.

---

## Known Gaps / Incomplete Features

1. ~~**Email verification**~~ — Implemented: verification email sent on register; login blocked until verified; resend link on verify_email_sent page. 2FA is optional (set up from Account).
2. **2FA on login** — optional; login does not require 2FA. Users with 2FA enabled do not yet get a second step at login (session['2fa_user_id'] flow exists but login route logs in directly).
3. **Stripe payments** — customer creation and card saving work; actual charging/escrow is not implemented. When implemented, **48-hour review rule** applies: if the business does not review or flag within 48 hours of `prototype_submitted_at`, payment auto-releases to the developer.
4. **Refund flow** — UI mentions refunds but no backend logic exists.
5. **Business rating field** on SprintListing (`business_rating`) — exists in model but never populated from aggregated developer ratings.
6. **Project model** — legacy, not actively used (home route queries it but nothing creates new entries through UI).
7. **Mobile hamburger menu** — implemented: home, layout, business, developer, and info layouts have working hamburger + mobile menu with toggle JS.
8. ~~**"More Information" section** — placeholder text only.~~ Replaced with real copy (who can join, payments/refunds, links to Terms/About/Support).

---

## File Structure

```
JrDev/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # App factory, extensions, format_rating filter
│   │   ├── models.py            # All SQLAlchemy models
│   │   ├── routes.py            # All Flask routes (~786 lines)
│   │   ├── forms.py             # Registration + Login forms
│   │   ├── profile_forms.py     # Edit profile, markdown, pinned project forms
│   │   ├── decorators.py        # require_role decorator
│   │   ├── utils.py             # URL helpers, rating, theme defaults
│   │   ├── signup_helpers.py    # Signup access control + rating helper
│   │   ├── contract_pdf.py      # Contract PDF blueprint (ReportLab)
│   │   ├── templates/           # 29 Jinja2 templates (see table above)
│   │   └── static/
│   │       ├── css/             # liquid-glass.css, home.css, main.css, developer_themes.css
│   │       ├── js/              # business_dashboard.js, developer_dashboard.js
│   │       └── favicon.svg      # Site favicon
│   ├── instance/site.db         # SQLite database
│   └── run.py / wsgi entry      # App runner
├── .env                         # Environment variables
└── .cursor/skills/              # Agent skills (this folder)
```
