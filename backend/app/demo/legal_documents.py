"""Initial legal documents v1.0 (Feature 9.5, PRD §9.5).

Lawsuit-resistant by design:
- Plain-English summary + dense legal body.
- Multi-jurisdiction coverage (PK PDPB, UK DPA, EU GDPR, CA PIPEDA, US CCPA).
- No guarantees of admission, visa, scholarship outcome, or accuracy.
- Liability cap = PKR 1,000 or 6 months of fees (whichever lower).
- Indemnification + arbitration clause + class-action waiver.
- B2B share consent is granular, revocable, and audited.
"""

from __future__ import annotations


LEGAL_DOCUMENTS_V1: list[dict] = [
    {
        "slug": "terms",
        "version": "1.0",
        "body_markdown": """# ScholarAI / GrantPath — Terms of Service v1.0

**What this means in 60 seconds**
- We help Pakistani students discover scholarships, draft SOPs, and practise visa
  interviews. We are not a consultant, lawyer, or licensed immigration adviser.
- Our matches, drafts, and rubric scores are AI-generated estimates. Outcomes are
  decided by universities and visa officers, not by us.
- If you use our content in a real application, you do so at your own risk.
- We cap our financial liability and require disputes go through arbitration.
- You can export your data and delete your account from settings at any time.

## 1. Acceptance
By creating an account or using the service you accept these Terms, the Privacy
Policy, the Cookie Policy, and (where applicable) the B2B Data Use Policy.
These Terms are governed by the laws of Pakistan, with the courts of
Islamabad as venue, subject to the arbitration clause below.

## 2. The service
ScholarAI Inc. ("we") provides an AI-assisted platform branded GrantPath.
The platform includes scholarship discovery, university matching, SOP drafting,
visa interview practice, and document tracking.

## 3. Eligibility and account
You must be at least 16 years old. Users between 16 and 18 require parental
consent. Accounts are personal and non-transferable. You are responsible for
the accuracy of the information you provide.

## 4. Plans and payment
We offer Explorer (free), Pro, Elite, and Institution tiers. Pricing is
displayed in PKR by default and may be shown in GBP, EUR, AED, or USD based
on your billing country. We may change pricing on 30 days' notice; paid
subscribers may cancel before the new price takes effect.

## 5. AI-generated content
Recommendations, SOPs, visa rubric scores, and any other AI output are
estimates produced by automated systems. They may contain factual errors,
omissions, or hallucinations. You must review and verify every word before
using it in a real application, financial declaration, or visa interview.

## 6. No guarantees
We make **no guarantee** of:
- admission to any program;
- award of any scholarship;
- approval of any visa;
- the accuracy, completeness, or timeliness of scholarship deadlines or
  funding figures;
- the suitability of an AI-generated SOP, email, or transcript for your
  specific case.

We are **not** an immigration consultant under Pakistan MoOP&HRD, the UK
OISC, ICCRC Canada, or any other licensing authority. We do not represent
you before any visa or admissions authority.

## 7. Limitation of liability
To the maximum extent permitted by law, our aggregate liability to you for
any claim arising out of or related to the service shall not exceed the
lesser of:
- PKR 1,000; or
- the total amount you paid us in the six months immediately preceding the
  claim.

We exclude liability for consequential, special, indirect, incidental, or
punitive damages, including without limitation loss of opportunity, loss of
admission, loss of scholarship, application-fee refunds, and visa refusal
costs.

Where applicable jurisdictions (e.g., EU consumer law) do not permit such a
cap, the cap is reduced to the minimum amount permitted by law, and the
remainder of these Terms remains in full force.

## 8. Indemnification
You agree to indemnify and hold us harmless from claims by third parties
arising out of:
- content you upload (transcripts, SOPs, photos, identification);
- misrepresentation in applications or visa interviews;
- your use of AI-generated material in real applications.

## 9. Arbitration and class-action waiver
Any dispute that cannot be resolved informally within 30 days shall be
referred to confidential arbitration administered by the London Court of
International Arbitration (LCIA) under its Rules, with a single arbitrator
sitting in Islamabad (in person or remotely). For Pakistan-resident
consumers the small-claims jurisdiction of Pakistani courts is preserved.
You waive any right to participate in a class, collective, or
representative action against us.

## 10. Service availability and force majeure
We do not commit to any uptime SLA on the Explorer tier. For Pro and Elite,
the sole remedy for extended downtime is a pro-rata refund. We are not
liable for events outside our reasonable control (natural disasters, war,
internet outages, government action, third-party API failures).

## 11. Termination and suspension
We may suspend or terminate accounts that breach these Terms, attempt to
manipulate or scrape the service, or pose a security risk. You may close
your account at any time; deletion runs through the 30-day window described
in the Privacy Policy.

## 12. Changes to the Terms
We may amend these Terms on 30 days' written notice (email or in-app). If
you do not accept the new Terms you must close your account before they
take effect; continued use after the effective date is acceptance.

## 13. Severability and entire agreement
If any provision is unenforceable, the rest of the Terms remain in full
force. These Terms, together with the Privacy Policy, Cookie Policy, and
Acceptable Use Policy, constitute the entire agreement between us and you.
""",
    },
    {
        "slug": "privacy",
        "version": "1.0",
        "body_markdown": """# ScholarAI / GrantPath — Privacy Policy v1.0

**What this means in 60 seconds**
- We collect the data you give us (profile, documents, interview answers) and
  technical data needed to run the service.
- We never sell your data. We only share with a university if you explicitly
  toggle the B2B consent and that university has signed a Data Processing
  Agreement with us.
- You can export every byte we hold about you and request deletion at any
  time. Deletion is scheduled 30 days out so you can cancel.
- We treat consent as the legal basis: you can revoke any consent and we
  log every change.

## 1. Who we are
ScholarAI Inc. ("we", "us") is the data controller. The product is also
known as GrantPath.

## 2. What we collect
- **Identifiers**: email, full name, password hash, date of birth, billing
  country, IP address, user-agent.
- **Profile**: CGPA, IELTS/TOEFL, GRE, target degree, target countries and
  fields, Pakistani university, city, family financial flags.
- **B2B contact (opt-in)**: phone, WhatsApp, LinkedIn/GitHub URLs.
- **Activity**: tracker items, generated SOPs, interview transcripts,
  consent grants and revokes.
- **Sensitive data we do NOT collect**: religion, political views, biometric
  data. Pakistani PDPB sensitive-data carve-outs apply.

## 3. Why we use it
- Run the matching, drafting, and interview features you asked for.
- Compute a lead score used internally to prioritise B2B outreach (only when
  b2b_share_consent is true).
- Comply with legal obligations (consent records, breach notification,
  retention).
- Improve the service in aggregate, anonymised form.

## 4. Legal bases
- **Consent**: marketing, B2B share, optional analytics cookies.
- **Contract**: running the features you paid for.
- **Legitimate interest**: anti-abuse, fraud prevention, internal analytics
  (anonymised).
- **Legal obligation**: retention of consent audit logs and tax records.

## 5. B2B sharing (off by default)
Profile data is **never** sold or shared with third parties unless the
b2b_share_consent toggle is on. With consent we may share a point-in-time
snapshot of your profile with universities that have signed a Data
Processing Agreement (DPA). Each share is logged in your "Shared With"
list. You may revoke consent at any time; revocation stops future shares,
but past shares cannot be unsent (this is disclosed in the consent dialog).

## 6. International transfers
Our services may store and process data in Pakistan, the EU/EEA, the UK,
and the United States. We rely on Standard Contractual Clauses, UK
International Data Transfer Addendum, and PDPB cross-border safeguards
where applicable.

## 7. Retention
- Application data: 5 years after last login (lets you re-use it).
- SOP and interview transcripts: 2 years.
- Consent audit log: 7 years (for legal defensibility).
- Server logs and IP addresses: 90 days.
- Anonymised analytics records: indefinite, no PII.

## 8. Your rights
You can: access, export, correct, delete, restrict, port, and object.
The product surfaces these through "Settings → Privacy" and:
- `POST /api/v1/privacy/data-export` for a full ZIP of your data;
- `POST /api/v1/privacy/account-deletion` (scheduled 30 days out, cancel
  any time).

To exercise rights specifically under GDPR, UK DPA 2018, PDPB, PIPEDA, or
CCPA/CPRA, write to **privacy@scholarai.pk**. We respond within 30 days.

## 9. Children
Minimum age 16. Users 16–18 must provide a parental consent email which
we verify before unlocking premium features.

## 10. Breach notification
If a breach is likely to affect you we notify you and the relevant
regulators (PTA Pakistan, ICO UK, EU DPAs) within 72 hours of discovery.

## 11. Cookies
See the Cookie Policy. Strictly-necessary cookies require no consent;
analytics and marketing cookies are opt-in.

## 12. Contact
privacy@scholarai.pk — Data Protection Officer
""",
    },
    {
        "slug": "cookies",
        "version": "1.0",
        "body_markdown": """# Cookie Policy v1.0

We use three categories of cookies. Strictly-necessary cookies require no
consent. Analytics and marketing cookies are off by default.

| Category | Purpose | Examples | Lifetime |
|---|---|---|---|
| Strictly necessary | Authentication, CSRF, load balancing | session, csrf | 30 minutes |
| Analytics (opt-in) | Aggregate product usage | _ga, _gid | 1 year |
| Marketing (opt-in) | Campaign attribution | fbp, _gcl_au | 90 days |

Manage preferences any time via the cookie banner or "Settings → Privacy".
""",
    },
    {
        "slug": "dpa",
        "version": "1.0",
        "body_markdown": """# Data Processing Addendum (DPA) v1.0

**What this means in 60 seconds**
- This addendum governs how we, and any university or partner you choose to
  share with, process personal data.
- We act as data controller for your account; partners who receive your data
  act as independent controllers under a signed DPA.
- No partner receives anything until they sign this DPA and you switch on the
  B2B share consent. Each share is a point-in-time snapshot, never a live feed.

This policy applies to universities, schools, and recruitment partners that
receive student lead data from ScholarAI.

1. **DPA required**. No data is shared until a Data Processing Agreement
   incorporating GDPR Article 28, UK DPA 2018, and PDPB equivalents is
   signed and recorded in `institutions.dpa_signed_at`.
2. **Snapshot only**. Each lead is a point-in-time JSON snapshot. Future
   profile changes do not retro-update past shares.
3. **Purpose limitation**. Use is restricted to admissions and scholarship
   outreach to the specific student concerned. No onward transfer, no
   resale, no model training.
4. **Retention**. Partners delete or return data within 12 months unless
   the student becomes an enrolled applicant.
5. **Sensitive categories not shared**. Religion, political views, and
   biometric data are not collected and cannot be requested.
6. **Audit rights**. We may audit DPA-signing partners on 30 days' notice.
""",
    },
    {
        "slug": "aup",
        "version": "1.0",
        "body_markdown": """# Acceptable Use Policy v1.0

You agree not to:
- scrape or systematically extract content from the service;
- submit forged transcripts, fake bank statements, or AI-generated identity
  documents intended to deceive admissions or visa authorities;
- use the platform to send unsolicited bulk messaging;
- reverse-engineer the matching engine or rubric weights;
- impersonate another user or an admissions officer.

Breach of this policy may result in account suspension or termination.
""",
    },
    {
        "slug": "refund",
        "version": "1.0",
        "body_markdown": """# Refund & Cancellation Policy v1.0

**What this means in 60 seconds**
- The Explorer tier is free forever — nothing to refund.
- Paid plans (Pro, Elite, Institution) renew until you cancel. Cancel any time
  from "Settings → Billing"; you keep access until the end of the paid period.
- We do not refund for dissatisfaction with AI-generated matches, SOPs, or
  rubric scores — these are clearly labelled estimates you must verify.
- EU/UK consumers get a 14-day cooling-off refund on a first paid subscription.
- Extended downtime on a paid tier is refunded pro-rata.

## 1. Free tier
The Explorer tier is provided at no cost. There is no charge and therefore no
refund associated with it.

## 2. Paid subscriptions
Pro, Elite, and Institution are recurring subscriptions billed in advance in
PKR by default (or GBP, EUR, AED, USD based on your billing country). Each
billing period renews automatically until you cancel.

## 3. Cancellation
You may cancel at any time from "Settings → Billing". Cancellation stops the
next renewal; you retain paid features until the end of the period already
paid for. We do not pro-rate a partially used period on voluntary
cancellation, except where local consumer law requires it.

## 4. Cooling-off (EU / UK consumers)
If you are a consumer in the EU or UK, you may cancel a **first** paid
subscription within 14 days of purchase for a full refund, unless you have
substantially consumed metered features (for example, generated your SOP
quota or completed Elite interview feedback) within that window. Requesting
immediate access waives the unused-service portion to the extent permitted by
law.

## 5. What we do not refund
- Dissatisfaction with AI-generated content. Matches, SOPs, professor emails,
  and rubric scores are estimates produced by automated systems and are
  labelled as such. You must review and verify them before any real use.
- Outcomes decided by third parties — admission, scholarship award, or visa
  approval. We make no guarantee of any outcome (see Terms §6).
- Charges older than the current and immediately preceding billing period.

## 6. Service downtime
For Pro and Elite, the sole remedy for extended downtime (as defined in Terms
§10) is a pro-rata refund of the affected period. The Explorer tier carries no
uptime commitment.

## 7. Price changes
We may change prices on 30 days' notice. If you do not accept a new price you
may cancel before it takes effect; amounts already paid are not refunded for
periods already served.

## 8. How to request a refund
Email **billing@scholarai.pk** from your account email with your invoice
reference. Eligible refunds are issued to the original payment method within
14 days of approval. Currency-conversion differences and payment-processor
fees are not refundable.

## 9. Chargebacks
Please contact us before raising a chargeback. A chargeback raised without
first contacting us may result in account suspension pending resolution.
""",
    },
]
