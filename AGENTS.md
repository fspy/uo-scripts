# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Code Guidelines

### Script Execution
- Scripts run inside the TazUO client, never from command line
- Always call `main()` directly at the end of scripts - **never use `if __name__ == "__main__":`**
- Command line may be used to verify syntax/parsing: `python -m py_compile script.py`

### Targeting
- **Never use `API.PreTarget()`** - always use the standard sequence:
  ```python
  API.UseObject(item_serial)
  if API.WaitForTarget(timeout=0.5):
      API.Target(target_serial)
  ```

### Code Search
- Use **ast-grep** for AST-aware code searches (understands Python structure)
  ```bash
  ast-grep --pattern 'def $FUNC($$$)' --lang python .
  ast-grep --pattern 'API.PreTarget($$$)' --lang python .
  ```
- Use **ripgrep** (`rg`) for fast text searches, not `grep`

### Shared Libraries
- Common utilities go in `lib/` folder
- Scripts should import from lib rather than duplicating code
- Existing libs: `lib/items.py`, `Runebook.py`

### Debugging
- Script errors and system messages are logged to journal files
- Location: `/mnt/games/uo/TazUO/TazUO/Data/Client/JournalLogs/`
- Files named like `2026_01_04_13_14_59_CharName_journal.txt`
- Search for errors: `rg "traceback|error|exception" <journal_file>`

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

