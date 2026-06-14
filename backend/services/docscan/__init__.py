"""DeepSec document / malware analysis engine, absorbed as an AppSec service package.

This package holds DeepSec's scanners, extractors, intelligence, sanitizers and utils
(moved here in Phase 1 of the merge). The public entry point — ``scan_document(path)``,
returning AppSec's Finding-dict contract — is added in Phase 2 (``adapter.py``).
Until then this package only exposes the moved subpackages and has no app wiring.
"""
