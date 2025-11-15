"""
Backwards-compatibility shim for pagination constants.

Prefer importing from `app.core.config` (the package), not this module.
"""

from app.core.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE  # re-export
