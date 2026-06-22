# -*- coding: utf-8 -*-
"""Run Saxon-C (saxonche) XSLT transforms in a fresh subprocess.

saxonche (Saxon-C / GraalVM) binds its isolate to the thread/process that first
initializes the runtime. Odoo imports it at startup (main thread) then calls it
from cron/worker threads (workers=0) or forked workers (workers>0), which aborts
the process with `graal_create_isolate / Failed to enter the specified
IsolateThread context`.

Both `pyfrctc` (CDAR schematron) and the `factur-x` library (Factur-X schematron)
use the same call pattern:

    with saxonche.PySaxonProcessor() as p:
        xslt = p.new_xslt30_processor()
        node = p.parse_xml(xml_text=... | xml_file_name=...)
        exe  = xslt.compile_stylesheet(stylesheet_file=...)
        result = exe.transform_to_string(xdm_node=node)

We replace `saxonche.PySaxonProcessor` with a shim reproducing exactly that
pattern but executing the real transform in a `subprocess.run` (fork+exec → fresh
interpreter, no inherited isolate). This covers every caller without touching them.

Upstream reports: akretion/pyfrctc#3, akretion/fr-einvoicing#9.
"""
import logging
import os
import subprocess
import tempfile

from . import models  # noqa: F401  (UBL normalization for the OCA importer)

_logger = logging.getLogger(__name__)

# Executed by a brand-new python3 (main thread, no inherited isolate).
_CODE = (
    "import sys, saxonche\n"
    "xsl, xmlf = sys.argv[1], sys.argv[2]\n"
    "with saxonche.PySaxonProcessor() as p:\n"
    "    xp = p.new_xslt30_processor()\n"
    "    node = p.parse_xml(xml_file_name=xmlf)\n"
    "    exe = xp.compile_stylesheet(stylesheet_file=xsl)\n"
    "    sys.stdout.write(exe.transform_to_string(xdm_node=node))\n"
)


class _Node:
    def __init__(self, xml_text=None, xml_file_name=None):
        self.xml_text = xml_text
        self.xml_file_name = xml_file_name


class _Executable:
    def __init__(self, stylesheet_file):
        self._xsl = stylesheet_file

    def transform_to_string(self, xdm_node=None, **kw):
        node = xdm_node
        tmp = None
        try:
            if node is not None and node.xml_file_name:
                xml_path = node.xml_file_name
            else:
                tmp = tempfile.NamedTemporaryFile(
                    "w", suffix=".xml", delete=False, encoding="utf-8"
                )
                tmp.write((node.xml_text if node else "") or "")
                tmp.close()
                xml_path = tmp.name
            proc = subprocess.run(
                ["python3", "-c", _CODE, self._xsl, xml_path],
                capture_output=True, text=True, timeout=300,
            )
        finally:
            if tmp is not None:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
        if proc.returncode != 0:
            raise RuntimeError(
                "Saxon subprocess failed (rc=%s): %s"
                % (proc.returncode, (proc.stderr or "")[-1000:])
            )
        return proc.stdout


class _Xslt30:
    def compile_stylesheet(self, stylesheet_file=None, **kw):
        return _Executable(stylesheet_file)


class _SubprocessSaxonProcessor:
    """Drop-in for saxonche.PySaxonProcessor covering the XSLT-transform pattern."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def new_xslt30_processor(self):
        return _Xslt30()

    def parse_xml(self, xml_text=None, xml_file_name=None, **kw):
        return _Node(xml_text=xml_text, xml_file_name=xml_file_name)

    @property
    def version(self):
        return "SaxonC subprocess shim"


# Install the shim (Odoo process only; the subprocess imports the real saxonche).
# Guarded so a missing optional dependency never breaks Odoo startup.
try:
    import saxonche as _saxonche

    _saxonche.PySaxonProcessor = _SubprocessSaxonProcessor
    _logger.info(
        "saxonche.PySaxonProcessor replaced by a subprocess shim (fork/thread-safe)"
    )
except Exception as e:  # noqa: BLE001
    _logger.warning(
        "superpdp_saxon_subprocess: saxonche shim not applied (%s); "
        "incoming e-invoice import may crash if saxonche is used in a worker.",
        e,
    )
