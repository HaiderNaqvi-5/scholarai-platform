<!-- Context: core/update | Priority: medium | Version: 1.0 | Updated: 2026-02-15 -->

# Update Operation

**Purpose**: Update context when APIs, frameworks, or contracts change

**Last Updated**: 2026-01-06

---

## When to Use

- Framework version updates (Next.js 14 → 15)
- API changes (breaking changes, deprecations)
- New features added to existing topics
- Migration guides needed

---

## 8-Stage Workflow

### Stage 1: Identify Changes (APPROVAL REQUIRED)
**Action**: User describes what changed (API changes, deprecations, new features, breaking changes)

**Validation**: MUST get user input before proceeding

---

### Stage 2: Find Affected Files
**Action**: Grep for topic references across all context; show file list with reference counts

**Validation**: Present impact summary before continuing

---

### Stage 3: Preview Changes (APPROVAL REQUIRED)
**Action**: Show line-by-line diff for each affected file; allow per-line approval

**Validation**: MUST get approval before proceeding

---

### Stage 4: Backup
**Action**: Create backup before updating

**Location**: `.tmp/backup/update-{topic}-{timestamp}/`

**Purpose**: Enable rollback if updates cause issues

---

### Stage 5: Update Files
**Action**: Apply approved changes

**Process**:
1. Update concepts, examples, guides, lookups
2. Maintain MVI format (<200 lines)
3. Update "Last Updated" dates
4. Preserve file structure

**Enforcement**: `@critical_rules.mvi_strict`

---

### Stage 6: Add Migration Notes
**Action**: Add migration guide to errors/

**Format**:
```markdown
## Migration: {Old Version} → {New Version}

**Breaking Changes**:
- Change 1
- Change 2

**Migration Steps**:
1. Step 1
2. Step 2

**Reference**: [Link to changelog]
```

**Location**: `{category}/errors/{topic}-errors.md`

---

### Stage 7: Validate
**Action**: Check all references and links

**Checks**:
- All internal references still work
- No broken links
- All files still <200 lines
- MVI format maintained

---

### Stage 8: Report
**Action**: Confirm updated files, reference counts, line totals, backup location, and rollback availability

---

## Change Types

- **API Changes**: Method signatures, parameters, return types
- **Deprecations**: Marked features, replacements, removal timeline
- **New Features**: New capabilities, APIs, patterns
- **Breaking Changes**: Incompatible changes requiring migration

---

## Examples

### Framework Update
```bash
/context update for Next.js 15
/context update for React 19
```

### API Changes
```bash
/context update for Stripe API v2024
/context update for OpenAI API breaking changes
```

### Library Update
```bash
/context update for Tailwind CSS v4
```

---

## Success Criteria

- [ ] User described changes?
- [ ] All affected files found?
- [ ] Diff preview shown?
- [ ] User approved changes?
- [ ] Backup created?
- [ ] Migration notes added?
- [ ] All references validated?
- [ ] All files still <200 lines?

---

## Related

- guides/workflows.md - Interactive diff examples
- standards/mvi.md - Maintain MVI format
- operations/error.md - Adding migration notes
