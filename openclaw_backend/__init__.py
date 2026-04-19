"""Compatibility bridge for package-safe backend imports.

This keeps the existing phase-1 and legacy module layout working when the
backend is imported as ``openclaw_backend`` from the repository root.
"""

from importlib import import_module
import sys


_ALIASES = (
    'api',
    'agents',
    'channels',
    'core',
    'sandbox',
    'schemas',
    'tools',
)

for _name in _ALIASES:
    sys.modules.setdefault(_name, import_module(f'{__name__}.{_name}'))
