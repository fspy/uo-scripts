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

## Build/Lint/Format Commands

### Code Formatting
- **Format all Python files**: `/home/fspy/.local/share/nvim/mason/bin/ruff format .`
- **Check formatting**: `/home/fspy/.local/share/nvim/mason/bin/ruff format --check .`
- **Format single file**: `/home/fspy/.local/share/nvim/mason/bin/ruff format <file.py>`

### Linting
- **Lint all files**: `/home/fspy/.local/share/nvim/mason/bin/ruff check .`
- **Lint single file**: `/home/fspy/.local/share/nvim/mason/bin/ruff check <file.py>`
- **Fix auto-fixable issues**: `/home/fspy/.local/share/nvim/mason/bin/ruff check --fix .`

### Syntax Verification
- **Check Python syntax**: `python -m py_compile <script.py>`

### Pre-commit Hook
- Python files are automatically formatted on commit via `.git/hooks/pre-commit`
- `API.py` is excluded from formatting (auto-generated)

## Code Style Guidelines

### Imports
- Standard library imports first (e.g., `import time`, `import json`)
- Third-party imports second (e.g., `import API`)
- Local imports last (e.g., `from _lib.utils import Hue`)
- Use absolute imports for lib: `from _lib.items import ...`

### API Import Pattern
```python
# API is injected at runtime by Legion engine
try:
    import API
except (ImportError, NameError):
    pass  # API injected at runtime
```

### Script Execution
- Scripts run inside the TazUO client, never from command line
- **Always call `main()` directly** at the end of scripts
- **Never use `if __name__ == "__main__":`**
- Use `python -m py_compile script.py` only for syntax verification

### Naming Conventions
- **Functions/variables**: `snake_case` (e.g., `find_shovel`, `mine_tile`)
- **Constants**: `UPPER_CASE` (e.g., `SHOVEL_TYPE`, `ORE_TYPES`)
- **Classes**: `PascalCase` (e.g., `Sampire`, `Runebook`)
- **Private/internal**: prefix with `_` (e.g., `_private_func`)

### Formatting (pyproject.toml)
- Line length: **88 characters**
- Quotes: **double quotes** preferred
- Indent: **4 spaces**
- Target Python version: **3.8+**

### Targeting Pattern
- **Never use `API.PreTarget()`** - always use the standard sequence:
```python
API.UseObject(item_serial)
if API.WaitForTarget(timeout=0.5):
    API.Target(target_serial)
```

### Error Handling
- Use descriptive variable names for clarity
- Return early on errors (guard clauses)
- Use `API.SysMsg()` or helper `p()`/`h()` for user feedback
- Check journal messages for operation success/failure
- Implement retry logic with adaptive delays for timing-sensitive operations

### Type Hints
- Use type hints where helpful (optional but encouraged)
- Add `# pyright: basic` comment for editor support
- Use `# pyright:ignore` to suppress false positives on API calls

## Code Search

- Use **ast-grep** for AST-aware code searches (understands Python structure)
  ```bash
  ast-grep --pattern 'def $FUNC($$$)' --lang python .
  ast-grep --pattern 'API.PreTarget($$$)' --lang python .
  ```
- Use **ripgrep** (`rg`) for fast text searches, not `grep`
  ```bash
  rg "pattern" --type py
  rg -i "pattern"  # case insensitive
  ```

## Shared Libraries

Common utilities go in `_lib/` folder:
- `_lib/items.py` - Item manipulation helpers
- `_lib/utils.py` - General utilities (Hue, p(), h(), etc.)
- `_lib/runebook.py` - Runebook travel utilities
- `_lib/persistence.py` - Save/load character settings
- `_lib/spells.py` - Spell timing calculations
- `_lib/weight.py` - Weight management
- `_lib/recovery.py` - Crash recovery helpers

Scripts should import from `_lib` rather than duplicating code.

## Debugging

- Script errors and system messages are logged to journal files
- Location: `/mnt/games/uo/TazUO/TazUO/Data/Client/JournalLogs/`
- Files named like `2026_01_04_13_14_59_CharName_journal.txt`
- Search for errors: `rg "traceback|error|exception" <journal_file>`

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Run ruff linter: `ruff check .`
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
