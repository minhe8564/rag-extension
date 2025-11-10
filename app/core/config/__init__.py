"""
Configuration package exports shared constants.

This module exposes pagination defaults so callers can reliably import
`DEFAULT_PAGE_SIZE` and `MAX_PAGE_SIZE` from `app.core.config`.
"""

# ============================================
# Pagination Constants
# ============================================

# Default number of items per page
DEFAULT_PAGE_SIZE = 20

# Maximum allowed items per page
MAX_PAGE_SIZE = 100
