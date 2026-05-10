"""
registry.py  –  Bundled model discovery
=========================================
Scans the ``mp_gesture_lib/models/`` directory for all ``*.task`` files
using ``importlib.resources`` so paths resolve correctly both during
local development AND after a ``pip install``.

Adding a new bundled model
--------------------------
Drop any ``*.task`` file into ``mp_gesture_lib/models/`` — it is picked up
automatically on the next import. No code change required.
"""

from __future__ import annotations

import os
from importlib import resources


def get_bundled_model_paths() -> list[str]:
    """
    Return absolute paths to every ``*.task`` file bundled in
    ``mp_gesture_lib/models/``.

    Returns
    -------
    list[str]
        Sorted list of absolute path strings (sorted for determinism).
        Empty list if the models directory exists but contains no ``.task`` files.
    """
    try:
        models_pkg = resources.files("mp_gesture_lib.models")
        paths: list[str] = []

        for item in models_pkg.iterdir():
            # resources.files() returns Traversable objects; convert to str path
            name = item.name
            if name.endswith(".task"):
                # Write to a temp location only if it's a non-filesystem resource
                # (e.g., inside a zip). For normal installs this is a real file path.
                if hasattr(item, "_path"):
                    # Internal attr on _NamespacePath
                    paths.append(str(item._path))
                else:
                    # Standard approach: resolve to string via __str__ / os.fspath
                    resolved = str(item)
                    if os.path.exists(resolved):
                        paths.append(resolved)
                    else:
                        # Fallback: extract to a temp file (zip-installed packages)
                        import tempfile
                        suffix = f"_{name}"
                        tmp = tempfile.NamedTemporaryFile(
                            suffix=suffix, delete=False
                        )
                        tmp.write(item.read_bytes())
                        tmp.close()
                        paths.append(tmp.name)

        return sorted(paths)

    except (ModuleNotFoundError, TypeError, AttributeError) as exc:
        # If package structure is unexpected, return empty list — caller handles it
        import warnings
        warnings.warn(
            f"mp_gesture_lib: could not discover bundled models: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return []
