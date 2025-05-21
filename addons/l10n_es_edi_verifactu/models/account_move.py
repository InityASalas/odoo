from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_es_edi_verifactu_required = fields.Boolean(
        string="Veri*Factu Required",
        compute='_compute_l10n_es_edi_verifactu_required',
    )
    l10n_es_edi_verifactu_document_ids = fields.One2many(
        comodel_name='l10n_es_edi_verifactu.document',
        inverse_name='move_id',
        string="Veri*Factu Documents",
    )
    l10n_es_edi_verifactu_state = fields.Selection(
        string="Veri*Factu Status",
        selection=[
            ('rejected', "Rejected"),
            ('registered_with_errors', "Registered with Errors"),
            ('accepted', "Accepted"),
            ('cancelled', "Cancelled"),
        ],
        compute='_compute_l10n_es_edi_verifactu_state', store=True,
        tracking=True,
        help="""- Rejected: Successfully sent to the AEAT, but it was rejected during validation
                - Registered with Errors: Registered at the AEAT, but the AEAT has some issues with the sent document
                - Accepted: Registered by the AEAT without errors
                - Cancelled: Registered by the AEAT as cancelled""",
    )
    l10n_es_edi_verifactu_warning = fields.Html(
        string="Veri*Factu Warning",
        compute="_compute_l10n_es_edi_verifactu_warning"
    )
    l10n_es_edi_verifactu_error_level = fields.Selection(
        string="Veri*Factu Error Level",
        selection=[
            ('rejected', "Rejected"),
            ('registered_with_errors', "Registered with Errors"),
        ],
        compute="_compute_l10n_es_edi_verifactu_errors_and_error_level"
    )
    l10n_es_edi_verifactu_errors = fields.Html(
        string="Veri*Factu Errors",
        compute="_compute_l10n_es_edi_verifactu_errors_and_error_level"
    )
    l10n_es_edi_verifactu_qr_code = fields.Char(
        string="Veri*Factu QR Code",
        compute='_compute_l10n_es_edi_verifactu_qr_code',
        help="This QR code is mandatory for Veri*Factu invoices.",
    )
    l10n_es_edi_verifactu_show_cancel_button = fields.Boolean(
        string="Show Veri*Factu Cancel Button",
        compute='_compute_l10n_es_edi_verifactu_show_cancel_button',
    )
    l10n_es_edi_verifactu_operation_type = fields.Selection(
        string="Veri*Factu Operation Type",
        selection='_l10n_es_edi_verifactu_operation_type_selection',
        compute='_compute_l10n_es_edi_verifactu_operation_type', store=True, readonly=False,
    )

    @api.model
    def _l10n_es_edi_verifactu_operation_type_selection(self):
        return [
            # Format: '{impuesto}_{clave_regimen}' (the clave regimen only appplies for VAT and IGIC)
            # VAT
            ('01_01', '(IVA) Operación de régimen general'),
            ('01_02', '(IVA) Exportación'),
            ('01_03', '(IVA) Operaciones a las que se aplique el régimen especial de bienes usados, objetos de arte, antigüedades y objetos de colección'),
            ('01_04', '(IVA) Régimen especial del oro de inversión'),
            ('01_05', '(IVA) Régimen especial de las agencias de viajes'),
            ('01_06', '(IVA) Régimen especial grupo de entidades en IVA (Nivel Avanzado)'),
            ('01_07', '(IVA) Régimen especial del criterio de caja'),
            ('01_08', '(IVA) Operaciones sujetas al IPSI  / IGIC (Impuesto sobre la Producción, los Servicios y la Importación  / Impuesto General Indirecto Canario)'),
            ('01_09', '(IVA) Facturación de las prestaciones de servicios de agencias de viaje que actúan como mediadoras en nombre y por cuenta ajena (D.A.4ª RD1619/2012)'),
            ('01_10', '(IVA) Cobros por cuenta de terceros de honorarios profesionales o de derechos derivados de la propiedad industrial, de autor u otros por cuenta de sus socios, asociados o colegiados efectuados por sociedades, asociaciones, colegios profesionales u otras entidades que realicen estas funciones de cobro'),
            ('01_11', '(IVA) Operaciones de arrendamiento de local de negocio'),
            ('01_14', '(IVA) Factura con IVA pendiente de devengo en certificaciones de obra cuyo destinatario sea una Administración Pública'),
            ('01_15', '(IVA) Factura con IVA pendiente de devengo en operaciones de tracto sucesivo'),
            ('01_17', '(IVA) Operación acogida a alguno de los regímenes previstos en el Capítulo XI del Título IX (OSS e IOSS)'),
            ('01_18', '(IVA) Recargo de equivalencia'),
            ('01_19', '(IVA) Operaciones de actividades incluidas en el Régimen Especial de Agricultura, Ganadería y Pesca (REAGYP)'),
            ('01_20', '(IVA) Régimen simplificado'),
            # IPSI
            ('02_', '(IPSI)'),
            # IGIC
            ('03_01', '(IGIC) Operación de régimen general'),
            ('03_02', '(IGIC) Exportación'),
            ('03_03', '(IGIC) Operaciones a las que se aplique el régimen especial de bienes usados, objetos de arte, antigüedades y objetos de colección'),
            ('03_04', '(IGIC) Régimen especial del oro de inversión'),
            ('03_05', '(IGIC) Régimen especial de las agencias de viajes'),
            ('03_06', '(IGIC) Régimen especial grupo de entidades en IGIC (Nivel Avanzado)'),
            ('03_07', '(IGIC) Régimen especial del criterio de caja'),
            ('03_08', '(IGIC) Operaciones sujetas al IPSI / IVA (Impuesto sobre la Producción, los Servicios y la Importación / Impuesto sobre el Valor Añadido)'),
            ('03_09', '(IGIC) Facturación de las prestaciones de servicios de agencias de viaje que actúan como mediadoras en nombre y por cuenta ajena (D.A.4ª RD1619/2012)'),
            ('03_10', '(IGIC) Cobros por cuenta de terceros de honorarios profesionales o de derechos derivados de la propiedad industrial, de autor u otros por cuenta de sus socios, asociados o colegiados efectuados por sociedades, asociaciones, colegios profesionales u otras entidades que realicen estas funciones de cobro'),
            ('03_11', '(IGIC) Operaciones de arrendamiento de local de negocio'),
            ('03_14', '(IGIC) Factura con IGIC pendiente de devengo en certificaciones de obra cuyo destinatario sea una Administración Pública'),
            ('03_15', '(IGIC) Factura con IGIC pendiente de devengo en operaciones de tracto sucesivo'),
            ('03_17', '(IGIC) Régimen especial de comerciante minorista'),
            ('03_18', '(IGIC) Régimen especial del pequeño empresario o profesional'),
            ('03_19', '(IGIC) Operaciones interiores exentas por aplicación artículo 25 Ley 19/1994'),
            # other
            ('05_', '(Otros)'),
        ]

    @api.depends('invoice_line_ids.tax_ids')
    def _compute_l10n_es_edi_verifactu_operation_type(self):
        verifactu_tax_type_map = self.env['account.tax']._l10n_es_edi_verifactu_get_tax_types_map()
        for move in self:
            taxes = self.invoice_line_ids.tax_ids.flatten_taxes_hierarchy()
            recargo_taxes = taxes.filtered(lambda tax: tax.l10n_es_type == 'recargo')
            l10n_es_tax_types = (taxes - recargo_taxes).mapped('l10n_es_type')
            if not l10n_es_tax_types:
                move.l10n_es_edi_verifactu_operation_type = False
                continue
            # We only support one operation type for the whole invoice.
            # We pick the first one for the computation.
            # TODO: Add validation that we do not mix VAT and IGIC?
            l10n_es_tax_type = l10n_es_tax_types[0]

            verifactu_tax_type = verifactu_tax_type_map.get(l10n_es_tax_type)
            if not verifactu_tax_type:
                move.l10n_es_edi_verifactu_operation_type = False
                continue

            regimen_key = None
            VAT = verifactu_tax_type == '01'
            IGIC = verifactu_tax_type == '03'
            if not (VAT or IGIC):
                move.l10n_es_edi_verifactu_operation_type = f'{verifactu_tax_type}_'
                continue

            oss_tag = self.env.ref('l10n_eu_oss.tag_oss', raise_if_not_found=False)
            if move.move_type == 'out_invoice':
                repartition_lines = taxes.invoice_repartition_line_ids
            else:
                # move.move_type == 'out_refund'
                repartition_lines = taxes.refund_repartition_line_ids
            company_in_simplified_regime = move.company_id.l10n_es_edi_verifactu_special_vat_regime == 'simplified'

            if VAT and company_in_simplified_regime and move.l10n_es_is_simplified:
                # simplified
                regimen_key = '20'
            if VAT and recargo_taxes:
                # recargo
                regimen_key = '18'
            elif VAT and oss_tag and oss_tag in repartition_lines.tag_ids:
                # oss
                regimen_key = '17'
            elif taxes.filtered(lambda tax: tax.l10n_es_type == 'exento' and tax.l10n_es_exempt_reason == 'E2'):
                # export
                regimen_key = '02'
            else:
                regimen_key = '01'

            move.l10n_es_edi_verifactu_operation_type = f'{verifactu_tax_type}_{regimen_key}'

    @api.depends('country_code')
    def _compute_l10n_es_edi_verifactu_required(self):
        for move in self:
            move.l10n_es_edi_verifactu_required = move.country_code == 'ES' and move.company_id.l10n_es_edi_verifactu_required

    @api.depends('l10n_es_edi_verifactu_document_ids', 'l10n_es_edi_verifactu_document_ids.state', 'l10n_es_edi_verifactu_document_ids.errors')
    def _compute_l10n_es_edi_verifactu_errors_and_error_level(self):
        for move in self:
            last_document = move.l10n_es_edi_verifactu_document_ids.sorted()[:1]
            error_level = False if last_document.state == 'accepted' else last_document.state
            move.l10n_es_edi_verifactu_error_level = error_level
            move.l10n_es_edi_verifactu_errors = last_document.errors

    @api.depends('l10n_es_edi_verifactu_document_ids', 'l10n_es_edi_verifactu_document_ids.state')
    def _compute_l10n_es_edi_verifactu_state(self):
        for move in self:
            state = move.l10n_es_edi_verifactu_document_ids._get_state()
            move.l10n_es_edi_verifactu_state = state

    @api.depends('l10n_es_edi_verifactu_document_ids', 'l10n_es_edi_verifactu_document_ids.record_identifier')
    def _compute_l10n_es_edi_verifactu_qr_code(self):
        for move in self:
            url = move.l10n_es_edi_verifactu_document_ids._get_last('submission')._get_qr_code_img_url()
            move.l10n_es_edi_verifactu_qr_code = url

    @api.depends('l10n_es_edi_verifactu_state', 'l10n_es_edi_verifactu_document_ids', 'l10n_es_edi_verifactu_document_ids.state')
    def _compute_l10n_es_edi_verifactu_warning(self):
        for move in self:
            warning = False
            if move.state == 'draft' and move.l10n_es_edi_verifactu_document_ids.json_attachment_id:
                warning = _("You are modifying a journal entry for which a Veri*Factu document has been succesfully generated already.")
            move.l10n_es_edi_verifactu_warning = warning

    @api.depends('l10n_es_edi_verifactu_state')
    def _compute_l10n_es_edi_verifactu_show_cancel_button(self):
        for move in self:
            move.l10n_es_edi_verifactu_show_cancel_button = move.l10n_es_edi_verifactu_state in ('registered_with_errors', 'accepted')

    @api.depends('l10n_es_edi_verifactu_state', 'l10n_es_edi_verifactu_document_ids', 'l10n_es_edi_verifactu_document_ids.state')
    def _compute_show_reset_to_draft_button(self):
        """
        Disallow resetting to draft in the following cases:
        * The move is cancelled
        * We are waiting to sent a cancellation document to the AEAT
        """
        # EXTENDS 'account'
        super()._compute_show_reset_to_draft_button()
        for move in self:
            if move.l10n_es_edi_verifactu_state == 'cancelled':
                move.show_reset_to_draft_button = False
                continue
            waiting_documents = move.l10n_es_edi_verifactu_document_ids._filter_waiting()
            if any(doc.document_type == 'cancellation' for doc in waiting_documents):
                move.show_reset_to_draft_button = False

    def l10n_es_edi_verifactu_button_cancel(self):
        created_documents = self._l10n_es_edi_verifactu_mark_for_next_batch(cancellation=True)
        skipped_moves = self.filtered(lambda move: not created_documents.get(move))
        if skipped_moves and len(self) == 1:
            # TODO: not correct in case we skip for concurrency case
            raise UserError(_("We are waiting to send a Veri*Factu record to the AEAT already."))
        # In other cases we just silently skip them

    def _l10n_es_edi_verifactu_check(self, cancellation=False):
        self.ensure_one()
        errors = []

        if self.state != 'posted':
            errors.append(_("The journal entry has to be posted."))

        refunded_move = self.reversed_entry_id
        refunded_document = refunded_move.l10n_es_edi_verifactu_document_ids._get_last('submission')
        if refunded_move and not refunded_document:
            # TODO: could also be cancellation without prior registration
            errors.append(_("The refunded journal entry has no Veri*Factu document yet."))

        if not self.l10n_es_edi_verifactu_operation_type:
            errors.append(_("The journal entry has no Veri*Factu Operation Type."))

        return errors

    def _l10n_es_edi_verifactu_get_record_values(self, cancellation=False):
        self.ensure_one()

        errors = self._l10n_es_edi_verifactu_check(cancellation=cancellation)
        if errors:
            return {'errors': errors}

        company = self.company_id
        documents = self.l10n_es_edi_verifactu_document_ids
        document_type = 'cancellation' if cancellation else 'submission'
        # Just checking whether the last document was rejected is enough; we do not allow to submit the same record
        # again after a cancellation (else we get the error '[3000] Registro de facturación duplicado.').
        rejected_before = documents._get_last(document_type).state == 'rejected'
        is_simplified = self.l10n_es_is_simplified

        verifactu_tax_type, clave_regimen = self.l10n_es_edi_verifactu_operation_type.split('_', 1)

        vals = {
            'cancellation': cancellation,
            'record': self,
            'rejected_before': rejected_before,
            'verifactu_state': self.l10n_es_edi_verifactu_state,
            'company': company,
            'delivery_date': self.delivery_date,
            'description': self.invoice_origin[:500] if self.invoice_origin else None,
            'invoice_date': self.invoice_date,
            'is_simplified': is_simplified,
            'move_type': self.move_type,
            'name': self.name,
            'partner': self.commercial_partner_id,
            'refunded_document': self.reversed_entry_id.l10n_es_edi_verifactu_document_ids._get_last('submission'),
            'documents': documents,
            'verifactu_tax_type': verifactu_tax_type,
            'clave_regimen': clave_regimen or None,
        }

        tax_details_functions = self.env['account.tax']._l10n_es_edi_verifactu_get_tax_details_functions(company)

        vals['tax_details'] = self._prepare_invoice_aggregated_taxes(
            filter_invl_to_apply=tax_details_functions['full_filter_invl_to_apply'],
            filter_tax_values_to_apply=tax_details_functions['filter_to_apply'],
            grouping_key_generator=tax_details_functions['grouping_key_generator'],
        )

        vals['document_vals'] = {
            'move_id': self.id,
            'company_id': company.id,
            'document_type': document_type,
        }

        vals['errors'] = self.env['l10n_es_edi_verifactu.document']._check_record_values(vals)

        return vals

    def _l10n_es_edi_verifactu_create_document(self, cancellation=False, previous_record_identifier=None):
        self.ensure_one()

        record_values = self._l10n_es_edi_verifactu_get_record_values(cancellation=cancellation)

        return self.env['l10n_es_edi_verifactu.document']._create_for_record(
            record_values, previous_record_identifier=previous_record_identifier,
        )

    def _l10n_es_edi_verifactu_mark_for_next_batch(self, cancellation=False):
        record_values_list = [
            move._l10n_es_edi_verifactu_get_record_values(cancellation=cancellation)
            for move in self
        ]
        return self.env['l10n_es_edi_verifactu.document']._mark_records_for_next_batch(record_values_list)
