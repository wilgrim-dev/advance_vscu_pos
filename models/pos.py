import logging, requests, base64, re
from datetime import datetime as dt
from io import BytesIO
from qrcode import QRCode, constants

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_round, float_compare

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
        
    vscu_data = fields.Json('Vscu Data')
    vscu_qr_code = fields.Binary('Vscu QR', attachment=True, copy=False, readonly=True, store=True)
    vscu_cu = fields.Char('CU', copy=False, readonly=True)
    vscu_date = fields.Datetime('Date', copy=False, readonly=True)
    vscu_serial = fields.Char('CU Serial', copy=False, readonly=True)
       
    def _vscu_item_code(self, product, uom_id):
        pass
    
    def _vscu_qrcode(self, url):                
        qr = QRCode(version=1, box_size=25, border=6, error_correction=constants.ERROR_CORRECT_L)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        temp_img = BytesIO()
        img.save(temp_img, format='PNG')
        
        return base64.b64encode(temp_img.getvalue())
    
    def _vscu_sequence(self, sequence):
        """
            Given record with sequence `Order 00007-012-0001` return `000070120001`
            :param :sequence 
            :return :000070120001
        """
        pattern = r"\d+"
        match = re.findall(pattern, sequence.replace("Order", "").replace("-", ""))
        clean_number = "".join(match)

        return clean_number
                
    
    def _vscu_prepare_data(self):
        self.ensure_one()
        """
        :Returns return: {
            "invoice_date":"12/22/21",
            "invoice_number":"SIN-00009279025132",
            "invoice_pin":"P051534464J",
            "customer_pin":"A007650714L",
            "customer_exid":"",
            "grand_total":"435,850",
            "tax_total":"60,117.24",
            "sel_currency":"KSH",
            "rel_doc_number":"",
            "items_list":
            [
               " CATTLE 10 SALT 10KG BAG 30 170.00 5,100.00",
               " CATTLE SALT 50KG BAG 1 650.00 650.00"
            ],
            "net_discount_total":"3,750",
            "net_subtotal":"375,732.76"
        }
        """
        item_list = [line.product_id.product_hs_code.replace('"', '\\"') + ' ' + line.product_id.name.replace('"', '\\"') + f' {line.quantity} {line.price_unit} {line.price_subtotal}' if line.product_id.product_hs_code\
            else line.product_id.name.replace('"', '\\"') + f' {line.quantity} {line.price_unit} {line.price_subtotal}' for line in self.invoice_line_ids]        
        return {
            'invoice_date': dt.strftime(self.invoice_date, '%m/%d/%Y'),
            'invoice_number': self.name,
            'invoice_pin': self.env.company.vat,
            'customer_pin': self.partner_id.vat,
            'sel_currency': 'KSH',
            'grand_total': str(self.amount_total),
            'tax_total': str(self.amount_tax),
            'rel_doc_number': self.reversed_entry_id.vscu_cu if self.reversed_entry_id else '',
            'customer_exid': '',                                
            'items_list': item_list,
            'net_discount_total': str(sum([line.discount for line in self.invoice_line_ids])),
            'net_subtotal': str(self.amount_untaxed)
        }
         
    @api.model          
    def action_vscu_sale(self):
        self.ensure_one()
        """
        Method to send invoice data for signing;
        :response: {
                "invoice_number": "SIN-0000024966",
                "cu_serial_number": "KRAMW004202110009550 11.08.2022 12\:11\:10",
                "invoice_date": "11.08.2022 12\:11\:10",
                "cu_invoice_number": "0040095500000000001",
                "verify_url": "https\://itax.kra.go.ke/KRA-Portal/invoiceChk.htm?actionCode=loadPage&invoiceNo=0040095500000000001",
                "description": "Signed successfully."
            }
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('vscu.url')
        headers = self.env['ir.config_parameter'].sudo().get_param('vscu.auth')
        if not base_url or not headers: raise UserError('Kindly setup ```vscu.url``` or ```vscu.auth``` param in system configuration!')
        try:
            url = ''
            if self.move_type == 'out_invoice': url = base_url + '/api/sign?invoice+1'
            elif self.move_type == 'out_refund': url = base_url + '/api/sign?invoice+2'
            else: url = base_url + '/api/sign?invoice+3'
            
            payload = self._prepare_vscu_payload()
            _logger.info(f'VSCU Payload: {payload}, url {url}')
            
            response = requests.post(url, json=payload, headers={'Authorization': headers})
            data = eval(response.text)
            _logger.info(f'VSCU Response: {data}')
            if data.get('cu_invoice_number'):
                qrcode = self._vscu_generate_qrcode(re.sub(r"\\", "", data.get('verify_url')))
                data['invoice_date'] = data.get('cu_serial_number').split(' ')[1]  + ' ' + re.sub(r"\\", "", data.get('cu_serial_number').split(' ')[2]) 
                data['cu_serial_number'] = data.get('cu_serial_number').split(' ')[0]
                self.write({
                    'vscu_data': data,
                    'vscu_qr_code': qrcode,
                    'vscu_cu': data['cu_invoice_number'],
                    'vscu_date': dt.strptime(data['invoice_date'], '%d.%m.%Y %H:%M:%S'),
                    'vscu_serial': data['cu_serial_number']
                })
                self.message_post(body=f"{data.get('description')} signature {data.get('cu_invoice_number')}")
            else:
                self.message_post(body=f"Unsuccessful sign, message: {data}")
        except Exception as e:
            raise UserError(_(e))