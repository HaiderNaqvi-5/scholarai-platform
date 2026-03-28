Use the repo rules in .codex/AGENTS.md.

Also use docs/scholarai/CODEX_MASTER_PROMPT_V1.md as the governing task specification for ScholarAI repository documentation work.

TASK:
Perform the first repository documentation migration pass for ScholarAI.

GOAL:
Turn the repository documentation into a consistent source of truth for ScholarAI without writing application code yet.

SCOPE OF THIS RUN:
1. Audit the existing documentation in:
   - README.md
   - docs/
   - any architecture, planning, roadmap, research, or setup files
2. Classify existing docs into:
   - aligned
   - partially reusable
   - conflicting
   - obsolete
3. Create or update these files first:
   - docs/scholarai/WORKPLAN.md
   - docs/scholarai/README.md
   - README.md
4. Propose which conflicting docs should be:
   - rewritten
   - archived
   - removed
5. Apply only the safe documentation changes needed for this first pass.
6. Do not generate application code in this run.

REQUIRED OUTPUTS:
- docs/scholarai/WORKPLAN.md
- docs/scholarai/README.md
- updated root README.md
- a migration summary inside the response that lists:
  - files created
  - files updated
  - files rewritten
  - files proposed for archive
  - files proposed for removal
  - reason for each major action

WORKPLAN.md MUST INCLUDE:
- file plan
- section-to-file mapping
- key architecture decisions that must stay consistent
- unresolved assumptions
- document authoring order
- migration order for old docs

docs/scholarai/README.md MUST INCLUDE:
- purpose of the ScholarAI documentation pack
- file tree
- section-to-file mapping
- key architecture decisions summary
- required diagrams list
- glossary of core terms

ROOT README.md MUST INCLUDE:
- what ScholarAI is
- current v0.1 SLC scope
- high-level architecture summary
- documentation entry points
- repo navigation guidance
- implementation status or roadmap summary

CONSTRAINTS:
- 3 developers
- 16 weeks
- limited budget
- SLC-first scope
- modular monolith
- Canada-first scope
- USA only for Fulbright-related scope
- DAAD deferred
- structured validated data is the source of truth

RULES:
- prefer rewriting useful docs over deleting them
- do not silently delete files
- if uncertain whether to remove a doc, propose archiving instead
- avoid hype and filler
- avoid fake metrics, fake datasets, and unsupported claims
- keep everything aligned with .codex/AGENTS.md
- use concrete, implementation-grounded writing

BEFORE FINISHING:
- verify terminology consistency across touched files
- verify README.md aligns with docs/scholarai/
- verify startup features do not leak into v0.1 SLC scope
- verify all new docs include clear assumptions and risks

