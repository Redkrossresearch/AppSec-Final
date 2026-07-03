"""Structural PDF sanitizer.

The previous implementation read the file, ``decode(errors="ignore")``-d it, regex
-deleted strings like ``/JavaScript``, then re-encoded. That was unsafe two ways:

1. It rewrote the whole byte stream through a lossy text round-trip, corrupting binary
   object streams *even on clean files*.
2. A hex-escaped name such as ``/J#61vaScript`` — which every PDF reader decodes back to
   ``/JavaScript`` — sailed past the regex, so the output could look sanitized while
   still armed.

This version parses the PDF object model with :mod:`pikepdf` and removes the active
content structurally, then saves a freshly rebuilt file. Because pikepdf normalizes name
encodings, hex-escaped variants are caught. It returns a *report* of exactly what was
neutralized so "sanitized" is a provable claim rather than an assumption.
"""

import os

import pikepdf

# Dictionary keys that carry active / auto-triggered content or embedded payloads.
# Any of these found on any object is removed. pikepdf has already decoded hex-escaped
# names (e.g. /J#61vaScript -> /JavaScript) by the time we inspect keys, closing the
# regex-bypass hole in the old implementation.
_DANGEROUS_KEYS = (
    "/OpenAction",     # action run when the document opens
    "/AA",             # additional-actions (fire JS on open/close/page events)
    "/JavaScript",     # document-level JS name tree (under /Names) or JS action
    "/JS",             # inline JavaScript payload on an action
    "/Launch",         # launch external program action
    "/EmbeddedFiles",  # document-level embedded-file name tree (under /Names)
    "/EF",             # embedded-file streams on a file specification
)

# Action subtypes (/S) whose whole action we defang.
_DANGEROUS_ACTIONS = {"/JavaScript", "/Launch"}


def _neutralize(obj, path, removed, visited):
    """Recursively strip active content from ``obj`` and everything it references.

    Walks the full object graph (not just ``pdf.objects``, which yields only *indirect*
    objects) so active content nested in inline dictionaries — e.g. the ``/Names ->
    /JavaScript`` and ``/Names -> /EmbeddedFiles`` name trees hanging directly off the
    catalog — is reached. Indirect objects are visited once via ``visited`` to break
    cycles. ``path`` is a human-readable location used in the removal report.
    """
    if isinstance(obj, pikepdf.Array):
        for i, item in enumerate(obj):
            _neutralize(item, f"{path}[{i}]", removed, visited)
        return

    if not isinstance(obj, (pikepdf.Dictionary, pikepdf.Stream)):
        return

    try:
        if obj.is_indirect:
            gen = obj.objgen
            if gen in visited:
                return
            visited.add(gen)
    except Exception:
        pass

    # Defang actions whose subtype is dangerous (leaves an inert action shell that its
    # referrer can still point at harmlessly).
    try:
        subtype = obj.get("/S")
    except Exception:
        subtype = None
    if subtype is not None and str(subtype) in _DANGEROUS_ACTIONS:
        try:
            del obj["/S"]
            removed.append(f"Neutralized {str(subtype)} action at {path}")
        except Exception:
            pass

    # Remove dangerous keys present on this object.
    for key in list(obj.keys()):
        if key in _DANGEROUS_KEYS:
            try:
                del obj[key]
                removed.append(f"Removed {key} at {path}")
            except Exception:
                pass

    # Recurse into whatever survives.
    for key in list(obj.keys()):
        try:
            child = obj[key]
        except Exception:
            continue
        _neutralize(child, f"{path}{key}", removed, visited)


def sanitize_pdf(source, output_folder=None):
    """Parse ``source``, strip active content, and write a rebuilt PDF.

    Keeps the original ``(source, output_folder=None)`` signature. Returns a report
    dict::

        {"output_file": <path or None>, "removed": [<neutralized item>, ...]}

    On a parse failure the function does **not** emit a false-clean copy: it returns
    ``output_file=None`` plus an ``"error"`` message so callers can tell that
    sanitization did not actually happen.
    """

    # Default keeps standalone behaviour; callers (the docscans route) pass a
    # per-scan directory like reports/<scan_id>/sanitized/ instead of the repo root.
    if output_folder is None:
        output_folder = "sanitized/pdf"

    os.makedirs(output_folder, exist_ok=True)

    filename = os.path.basename(source)
    output_file = os.path.join(output_folder, filename)

    removed = []

    try:
        pdf = pikepdf.open(source)
    except Exception as exc:
        return {
            "output_file": None,
            "removed": [],
            "error": f"Could not parse PDF, not sanitized: {exc}",
        }

    with pdf:
        # Walk the whole object graph from the catalog so active content is caught
        # wherever it hides — catalog, page /AA, annotation actions, AcroForm fields,
        # and the /Names JavaScript / EmbeddedFiles name trees.
        visited = set()
        _neutralize(pdf.Root, "/Root", removed, visited)
        # Belt-and-braces: catch any indirect object not reachable from the catalog.
        for obj in list(pdf.objects):
            _neutralize(obj, "object", removed, visited)

        pdf.save(output_file)

    return {"output_file": output_file, "removed": removed}
