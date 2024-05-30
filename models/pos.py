import logging, json, base64, re
from datetime import datetime as dt
from io import BytesIO
from qrcode import QRCode, constants

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_compare
from odoo.addons.ke_etims_tax.models.oscu import *

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
        
    etims_data = fields.Json('eTIMS Data', copy=False, readonly=True)
    etims_receipt_sign = fields.Binary('eTIMS Sign', attachment=True, copy=False, readonly=True, store=True)
    etims_sdc_date = fields.Datetime('eTIMS Date', readonly=True)    
       
    def _generate_item_code(self, product, uom_id):
        itemCd, lengthCd = '', 7
        if product.product_code in ['Raw', 'Finished', 'Service']:                                     
            itemCd = 'KE' + str(PRODUCTTYPE[product.product_code]) + uom_id.etims_packaging + uom_id.etims_uom + '{0}{1}'.format('0'*(lengthCd - len(str(product.id))), str(product.id))
        return itemCd
    
    def _generate_qrcode(self, receipt_sign):
        url = 'https://etims-sbx.kra.go.ke/common/link/etims/receipt/indexEtimsReceiptData?Data=' \
            if self.company_id.etims_env == 'test' else 'https://etims.kra.go.ke/common/link/etims/receipt/indexEtimsReceiptData?Data='
        url += self.company_id.vat + self.company_id.etims_branch_id + receipt_sign
                
        qr = QRCode(version=1, box_size=25, border=6, error_correction=constants.ERROR_CORRECT_L)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        temp_img = BytesIO()
        img.save(temp_img, format='PNG')
        
        return base64.b64encode(temp_img.getvalue())
    
    def _generate_sequence(self, sequence):
        """
            Given record with sequence `Order 00007-012-0001` return `000070120001`
            :param :sequence 
            :return :000070120001
        """
        pattern = r"\d+"
        match = re.findall(pattern, sequence.replace("Order", "").replace("-", ""))
        clean_number = "".join(match)

        return clean_number
                
    
    def _oscu_prepare_data(self):
        self.ensure_one()
        move_state, payment_type, move_type, orgInvcNo = TRANSACTION_STATUS['Approved'], TYPE['Payment']['Other'], TYPE['Sales']['Sale'], 0
       
        invoice_lines = self.lines
        taxblAmtA =  sum([line.price_subtotal for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'A']) 
        taxblAmtB =  sum([line.price_subtotal for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'B'])
        taxblAmtC = sum([line.price_subtotal for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'C'])
        taxblAmtD = sum([line.price_subtotal for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'D'])
        taxblAmtE = sum([line.price_subtotal for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'E'])  
        taxAmtA = sum([line.price_subtotal_incl for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'A']) - taxblAmtA 
        taxAmtB = sum([line.price_subtotal_incl for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'B']) - taxblAmtB 
        taxAmtC = sum([line.price_subtotal_incl for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'C']) - taxblAmtC
        taxAmtD = sum([line.price_subtotal_incl for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'D']) - taxblAmtD 
        taxAmtE = sum([line.price_subtotal_incl for line in invoice_lines if line.tax_ids_after_fiscal_position.etims_tax_code == 'E']) - taxblAmtE    
        move = {
            'invcNo': self._generate_sequence(self.pos_reference), 'trdInvcNo': self.name, 
            'orgInvcNo': orgInvcNo, 'custTin': self.partner_id.vat, 'custNm': self.partner_id.name,
            'rcptTyCd': move_type, 'pmtTyCd': payment_type, 'salesSttsCd': move_state,
            'cfmDt': dt.strftime(self.date_order, '%Y%m%d%H%M%S'), 'salesDt': dt.strftime(self.date_order, '%Y%m%d'),
            'stockRlsDt': dt.strftime(self.date_order, '%Y%m%d%H%M%S'),
            'cnclReDt': None, 'cnclDt': None, 'rfdDt': None,
            'rfdRsnCd': None, 'totItemCnt': len(invoice_lines), 
            'taxblAmtA': taxblAmtA, 'taxblAmtB': taxblAmtB, 'taxblAmtC': taxblAmtC, 'taxblAmtD': taxblAmtD, 'taxblAmtE': taxblAmtE,
            'taxRtA': invoice_lines.tax_ids_after_fiscal_position.filtered(lambda x: x.etims_tax_code == 'A' and x.type_tax_use == 'sale').amount, 
            'taxRtB': invoice_lines.tax_ids_after_fiscal_position.filtered(lambda x: x.etims_tax_code == 'B' and x.type_tax_use == 'sale').amount, 
            'taxRtC': invoice_lines.tax_ids_after_fiscal_position.filtered(lambda x: x.etims_tax_code == 'C' and x.type_tax_use == 'sale').amount, 
            'taxRtD': invoice_lines.tax_ids_after_fiscal_position.filtered(lambda x: x.etims_tax_code == 'D' and x.type_tax_use == 'sale').amount, 
            'taxRtE': invoice_lines.tax_ids_after_fiscal_position.filtered(lambda x: x.etims_tax_code == 'E' and x.type_tax_use == 'sale').amount,
            'taxAmtA': float_round(taxAmtA, precision_digits=2), 
            'taxAmtB': float_round(taxAmtB, precision_digits=2), 
            'taxAmtC': float_round(taxAmtC, precision_digits=2),
            'taxAmtD': float_round(taxAmtD, precision_digits=2), 
            'taxAmtE': float_round(taxAmtE, precision_digits=2), 
            'totTaxblAmt': float_round(self.amount_total - self.amount_tax, precision_digits=2), 'totTaxAmt': float_round(self.amount_tax, precision_digits=2),
            'totAmt': float_round(self.amount_total, precision_digits=2), 'prchrAcptcYn': 'Y', 'remark': None, 'regrId': self.cashier, 'regrNm': self.cashier, 'modrId': self.cashier, 'modrNm': self.cashier
        }
        customer = {
            "custTin": self.partner_id.vat,"custMblNo": self.partner_id.mobile or self.partner_id.phone,"rcptPbctDt": dt.strftime(self.date_order, '%Y%m%d%H%M%S'),
            "trdeNm": self.partner_id.name,"adrs": self.partner_id.contact_address_complete,"topMsg": None,"btmMsg":None,"prchrAcptcYn": "Y",
            "rptNo": self._generate_sequence(self.pos_reference)
        }
        item_seq = 0
        move_lines = [{
            "itemSeq": item_seq,"itemCd": self._generate_item_code(line.product_id, line.product_uom_id), "itemClsCd": line.product_id.product_class, "itemNm": line.product_id.name, 
            "bcd": None,"pkgUnitCd": "NT", "pkg":2,"qtyUnitCd":"U", "qty": line.qty,"prc": float_round(line.price_subtotal_incl, precision_digits=2),
            "splyAmt": float_round(line.price_subtotal_incl, precision_digits=2), "dcRt": line.discount,"dcAmt": line.discount,"isrccCd": None, "isrccNm": None,"isrcRt": None,"isrcAmt": None,
            "taxTyCd": line.tax_ids_after_fiscal_position.etims_tax_code, "taxblAmt": float_round(line.price_subtotal, precision_digits=2),
            "taxAmt": float_round(line.price_subtotal_incl-line.price_subtotal, precision_digits=2), "totAmt": float_round(line.price_subtotal_incl, precision_digits=2)     
        } for line in invoice_lines]
        
        return move, customer, move_lines
                   
    def action_etims_sale(self):
        self.ensure_one()
        
        cmcKey = self.env.company.etims_data.get('data').get('info').get('cmcKey') if self.env.company.etims_env == 'test' else \
            self.env.company.etims_data.get('info').get('cmcKey')
            
        sdcId = self.env.company.etims_data.get('data').get('info').get('sdcId') if self.env.company.etims_env == 'test' else \
            self.env.company.etims_data.get('info').get('sdcId')
            
        oscu = OSCU(self.company_id.etims_env, self.company_id.vat, self.company_id.etims_branch_id, \
                    self.company_id.etims_device_info, cmcKey)
        move, receipt, move_lines = self._oscu_prepare_data()
        try:
            response = oscu.TrnsSalesSaveWr(item=move, receipt=receipt, order_line=move_lines)
            _logger.info(f'KRA Response: {response.json()}')
            if response.json()['resultCd'] == '000':
                data = response.json()['data']
                data['sdcId'] = sdcId + '/' + self._generate_sequence(self.pos_reference)
                self.write({'etims_data': data, 'etims_receipt_sign': self._generate_qrcode(data['rcptSign']), 'etims_sdc_date': dt.strptime(data['sdcDateTime'], '%Y%m%d%H%M%S')})
                # self.message_post(body=f"{self.name} sign to eTIMS successful.")
            else: 
                # self.message_post(body=f"{self.name} sign to eTIMS error: {response.json()}")
                _logger.info(f'KRA ERROR: {response.json()}')
                
        except Exception as e:
            raise UserError(_(f'eTIMS signing raised error {e}'))