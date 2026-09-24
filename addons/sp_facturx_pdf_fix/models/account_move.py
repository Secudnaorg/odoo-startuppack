import os
import tempfile

from odoo import models

from facturx import generate_from_file


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_en16931_invoice_bin(self, invoice_format, b64=False):
        """Pass-through to the standard EN16931 generation.

        Kept as an explicit hook. We do NOT force ``chorus_old_xml_syntax``
        (SIRET legal identity) for public recipients: the accredited PDP
        (SuperPDP) binds the session to the SIREN and rejects a seller whose
        legal identity is the SIRET. The standard Factur-X profile already
        carries SIREN as SpecifiedLegalOrganization and SIRET as GlobalID.
        """
        self.ensure_one()
        # SuperPDP requires the seller's SpecifiedLegalOrganization to be the SIREN
        # (schemeID 0002), with the SIRET carried as GlobalID (0009). Forcing
        # chorus_old_xml_syntax put the SIRET as the legal identity, which the PDP
        # rejects (400: session company SIREN != invoice seller SIRET). Verified
        # against the accepted INV/2026/00006 (SIREN). Keep the standard profile.
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
        xml_bytes, _data_dict, attachments = self.generate_en16931_xml(
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
