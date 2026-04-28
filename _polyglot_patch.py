"""
Patch for polyglot-hello compatibility with Python 3.14+.
In Python 3.14, Traversable was moved from importlib.abc to collections.abc.
"""
import sys

def patch_traversable():
    """Patch importlib.abc to include Traversable for backward compatibility."""
    if sys.version_info >= (3, 9):
        import importlib.abc
        if not hasattr(importlib.abc, 'Traversable'):
            try:
                from collections.abc import Traversable
                importlib.abc.Traversable = Traversable
            except ImportError:
                # Fallback for even older versions
                from importlib.resources.abc import Traversable
                importlib.abc.Traversable = Traversable

patch_traversable()
