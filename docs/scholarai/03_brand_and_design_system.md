# ScholarAI Brand And Design System

## Design Intent
ScholarAI should feel premium, restrained, and deliberate. The product should communicate trust through clarity rather than decoration. The interface must be feasible for one strong frontend developer to implement without falling back to generic dashboard patterns.

## Brand Attributes
| Attribute | Meaning in practice |
|---|---|
| Calm | Dense information is organized without visual noise |
| Precise | Requirements, rankings, and states are legible and structured |
| Modern | The system feels current without chasing trends |
| Credible | The visual language supports trust in validated data |
| Supportive | Guidance feels constructive rather than judgmental |

## Visual Direction
ScholarAI should combine editorial clarity with product-grade utility. Scholarship exploration is an analytical task, so the interface should use strong hierarchy, clean data presentation, and restrained motion. The product should not look like a generic SaaS dashboard or a student-portal template.

## Design Principles
1. Lead with information hierarchy.
2. Use whitespace to separate meaning, not just content blocks.
3. Prefer strong typography over heavy chrome.
4. Make validated data visually distinct from generated guidance.
5. Surface explanations without overwhelming first-time users.

## Typography
| Role | Recommendation | Purpose |
|---|---|---|
| Display | `Sora` | Sharp, contemporary headings and marketing surfaces |
| UI text | `IBM Plex Sans` | Dense product surfaces and data-heavy layouts |
| Monospace | `IBM Plex Mono` | Provenance, states, IDs, and technical labels |

## Color System
### Core palette
| Token | Value | Use |
|---|---|---|
| `ink-950` | `#0C1117` | Primary text and deep contrast |
| `ink-700` | `#334155` | Secondary text |
| `paper-50` | `#F7F5F0` | Main app background |
| `paper-100` | `#EEE9DF` | Surface contrast for cards and panels |
| `sage-600` | `#426B5A` | Trust, validation, confirmed states |
| `amber-600` | `#B7791F` | Caution, review-needed states |
| `coral-600` | `#B94A48` | Error, blocked, invalid states |
| `sky-600` | `#2E5B9A` | Links, active controls, charts |

### Color usage rules
- Use `paper-50` and `paper-100` as the default light surfaces.
- Reserve saturated colors for state changes, emphasis, and charts.
- Do not use gradient-heavy or neon-accent aesthetics in product surfaces.
- Keep validated data states visually distinct from AI-generated guidance states.

## Layout System
| Area | Rule |
|---|---|
| Content width | Default reading width around 72 to 80 characters for narrative copy |
| App shell | Wide content canvas with strong margins on desktop |
| Spacing scale | 4, 8, 12, 16, 24, 32, 48, 64 |
| Corner radius | 10px to 16px on primary surfaces |
| Borders | Thin, low-contrast dividers rather than heavy outlines |

## Component Guidance
| Component | Direction |
|---|---|
| Scholarship cards | Dense but calm; emphasize title, fit summary, deadline, and validation state |
| Filters | Persistent and structured; avoid modal-heavy filtering |
| Explanation panels | Progressive disclosure; show summary first, details on demand |
| Provenance badges | Clearly distinguish `raw`, `validated`, and `published` |
| Document-feedback surfaces | Separate user text, retrieved context, and generated guidance visually |
| Interview feedback | Use sectioned scoring and improvement areas, not conversational clutter |

## Interaction And Motion
- Use small entrance fades and upward motion for primary page sections.
- Use staggered reveal only on high-level landing or overview surfaces.
- Prefer instant UI response for filtering and navigation over decorative animation.
- Keep motion functional: reveal structure, confirm state change, or guide attention.

## Content Voice
| Context | Tone |
|---|---|
| Scholarship facts | Direct, precise, and neutral |
| Guidance copy | Helpful and clear, never overconfident |
| Errors | Specific, non-dramatic, and actionable |
| Empty states | Honest about scope; guide the next best action |

## Accessibility Baseline
1. Maintain strong text contrast on all data surfaces.
2. Do not rely on color alone for provenance, eligibility, or warning states.
3. Keep keyboard navigation intact across search, filters, and detail views.
4. Use motion sparingly and ensure it does not block interaction.
5. Prefer clear labels over icon-only controls in dense workflows.

## Page Archetypes
| Page type | Design emphasis |
|---|---|
| Landing / overview | Product trust, category framing, calm visual depth |
| Search / discovery | Fast scanning, persistent filters, high information density |
| Scholarship detail | Requirements, deadlines, funding, provenance, explanation hooks |
| Recommendation workspace | Ranked list plus explanation panel and action prompts |
| Preparation workflows | Focused single-task surfaces for documents and interviews |
| Admin curation | Validation state management, provenance review, source auditing |

## Separation Of Data And Guidance
ScholarAI must visually separate:
- validated scholarship facts
- user-provided profile data
- generated guidance
- system explanations

This separation is a product trust requirement, not only a design preference.

## MVP Vs Deferred Design Scope
### MVP
- Light theme first.
- Core component library for discovery, detail, explanation, document feedback, interview feedback, and admin validation.
- Strong typography, measured motion, and a restrained palette.

### Future Research Extensions
- More advanced explanation visualizations and trust-study variants.
- Comparative interface experiments for explanation helpfulness.

### Post-MVP Startup Features
- Brand sub-systems for provider and institution products.
- White-label or partner-specific experience layers.

## MVP decision
ScholarAI MVP will use a restrained, premium light-theme design system centered on strong typography, calm surfaces, and clear separation between validated data and generated guidance.

## Deferred items
- Dark mode.
- Advanced animation systems.
- White-label theming and partner brand layers.
- Highly customized visualization libraries beyond core explanation needs.

## Assumptions
- A typography-led light theme is the fastest path to a premium but feasible MVP.
- Most early usage will be document-heavy and desktop-first, even though mobile support remains required.
- Clear visual separation of fact and guidance materially improves trust.

## Risks
- A dense information architecture can become visually flat if hierarchy is weak.
- Over-polishing decorative surfaces can waste scarce frontend capacity.
- If generated guidance is not visually differentiated, users may confuse it with validated scholarship facts.
