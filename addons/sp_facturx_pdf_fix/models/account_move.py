import os
import tempfile

from odoo import models

from facturx import generate_from_file


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_en16931_invoice_bin(self, invoice_format, b64=False):
        """Use the Chorus-Pro CII conventions for French public recipients.

        The public-sector gateway expects the legacy Chorus profile (A1/A2) and
        SIRET legal identifiers.  ``l10n_fr_account_invoice_en16931`` already
        implements this variant behind the ``chorus_old_xml_syntax`` context;
        apply it automatically to outgoing Factur-X documents addressed to a
        public entity.
        """
        self.ensure_one()
        if (
            invoice_format == "facturx"
            and getattr(self, "fr_directory_partner_entity_type", False) == "public"
            and not self.env.context.get("chorus_old_xml_syntax")
        ):
            return super(
                AccountMove, self.with_context(chorus_old_xml_syntax=True)
            )._get_en16931_invoice_bin(invoice_format, b64=b64)
        return super()._get_en16931_invoice_bin(invoice_format, b64=b64)

    def _regular_pdf_invoice_to_en16931_pdf_invoice(self, pdf_bytesio, invoice_format):
        """Embed Factur-X XML without corrupting Odoo's in-memory PDF stream.

        ``facturx.generate_from_file`` expects to replace a filesystem file. When
        given Odoo's ``BytesIO`` report stream, it appends the rewritten PDF while
        retaining offsets relative to the start of the stream. The resulting PDF
        has an invalid cross-reference table and cannot be opened by readers.
        """
        self.ensure_one()
        if not invoice_format.startswith("facturx"):
            return super()._regular_pdf_invoice_to_en16931_pdf_invoice(
                pdf_bytesio, invoice_format
            )

        pdf_metadata = self._prepare_facturx_pdf_metadata()
        lang = self.partner_id.lang and self.partner_id.lang.replace("_", "-") or None
        xml_bytes, attachments = self.generate_en16931_xml(
            "factur-x", "extended", invoice_format
        )

        file_descriptor, output_path = tempfile.mkstemp(suffix=".pdf")
        os.close(file_descriptor)
        try:
            pdf_bytesio.seek(0)
            generate_from_file(
                pdf_bytesio,
                xml_bytes,
                flavor="factur-x",
                level="extended",
                check_xsd=False,
                check_schematron=False,
                pdf_metadata=pdf_metadata,
                lang=lang,
                attachments=attachments,
                output_pdf_file=output_path,
            )
            with open(output_path, "rb") as output_file:
                pdf_bytesio.seek(0)
                pdf_bytesio.truncate(0)
                pdf_bytesio.write(output_file.read())
            pdf_bytesio.seek(0)
        finally:
            os.unlink(output_path)
