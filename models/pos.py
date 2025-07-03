import logging, requests, base64, re
from datetime import datetime as dt
from io import BytesIO
from qrcode import QRCode, constants
from requests.auth import HTTPBasicAuth

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
            "traderInvoiceNo": "123",
            "totalAmount": 2023.68,
            "paymentType": "01",
            "salesTypeCode": "N",
            "receiptTypeCode": "S",
            "salesStatusCode": "01",
            "salesDate": "20240509050115",
            "currency": "KES",
            "exchangeRate": 1.0,
            "salesItems": [
                {
                "itemCode": "KE1UCT0000015",
                "qty": 1,
                "pkg": 0,
                "unitPrice": 193.84,
                "amount": 193.84,
                "discountAmount": 0
                }
            ],
            "customerPin": "P00000000004s"
            }
        """
        item_list = [{
            "itemCode": "KE2UCT0027536" or line.product_id.product_hs_code,
            "qty": line.qty,
            "pkg": 0,
            "unitPrice": line.price_unit,
            "amount": line.price_subtotal_incl,
            "discountAmount": line.discount
        } for line in self.lines]
        
        return {
            "traderInvoiceNo": self._vscu_sequence(self.pos_reference),
            "totalAmount": self.amount_total,
            "paymentType": "01",
            "salesTypeCode": "N",
            "receiptTypeCode": "S",
            "salesStatusCode": "01",
            "salesDate": dt.strftime(self.date_order, '%Y%m%d%H%M%S'),
            "currency": "KES",
            "exchangeRate": 1.0,
            "salesItems": item_list,
            "customerPin": self.partner_id.vat if self.partner_id.vat else ""
        }
        
    @api.model          
    def action_vscu_sale(self, order_id):
        """
        Method to send invoice data for signing;
        :response: {
            "status": 200,
            "statusCode": "SUCCES",
            "message": "Invoice with trader invoice No 123  already exists",
            "data": {
                "invoiceNo": 2,
                "traderInvoiceNo": "123",
                "totalAmount": 193.84,
                "totalTaxableAmount": 193.84,
                "totalTaxAmount": 0,
                "paymentType": "01",
                "salesTypeCode": "N",
                "receiptTypeCode": "S",
                "salesStatusCode": "01",
                "salesDate": "20240607070732",
                "currency": "KES",
                "internalData": "N6L6AMLNWHFDBZK4PIEDWDMO4Y",
                "signature": "5BBQL4WBFUVSPUT7",
                "scdcId": "KRACU0300000288",
                "scuReceiptDate": "20240607070733",
                "scuReceiptNo": 2,
                "invoiceVerificationUrl": "https://etims-sbx.kra.go.ke/common/link/etims/receipt/indexEtimsReceiptData?Data=P051885316K015BBQL4WBFUVSPUT7",
                "salesItems": [
                    {
                        "id": 75,
                        "unitPrice": 193.84,
                        "amount": 193.84,
                        "taxableAmount": 193.84,
                        "taxAmount": 0,
                        "discount": 0,
                        "itemCode": "KE1UCT0000023",
                        "itemClassCode": "99000000",
                        "pkgUnitCode": "CT",
                        "qtyUnitCode": "U",
                        "pkg": 0,
                        "supplyAmount": 193.84,
                        "taxTypeCode": "A",
                        "insuranceCompanyCode": null,
                        "insuranceCompanyName": null,
                        "insuranceRate": null,
                        "insuranceAmount": null,
                        "qty": 1
                    }
                ],
                "customerPin": "",
                "customerName": ""
            }
        }
        """
        response = {}
        self = self.env[self._name].browse(order_id)
        
        base_url = self.env['ir.config_parameter'].sudo().get_param('vscu.url')
        username = self.env['ir.config_parameter'].sudo().get_param('vscu.username')
        password = self.env['ir.config_parameter'].sudo().get_param('vscu.password')
        
        if not (base_url, username, password): 
            return {'hasError': True, 'message': 'Kindly setup ```vscu.url/vscu.username/vscu.password``` param in system configuration!'}
        
        try:
            url = base_url + '/invoices'
            
            payload = self._vscu_prepare_data()
            auth = HTTPBasicAuth(username, password)
            _logger.info(f'VSCU Payload: {payload}, cred {url, username, password}')
            
            data = requests.post(url, json=payload, auth=auth, headers={'Content-Type': 'application/json'}).json()
            
            _logger.info(f'VSCU Response: {data}')
            if data.get('status') == 200:
                signData = data['data']
                qrcode = self._vscu_qrcode(re.sub(r"\\", "", signData.get('invoiceVerificationUrl')))
                self.write({
                    'vscu_data': data,
                    'vscu_qr_code': qrcode,
                    'vscu_cu': signData['scuReceiptNo'],
                    'vscu_date': dt.strptime(signData['scuReceiptDate'], '%Y%m%d%H%M%S'),
                    'vscu_serial': signData['scdcId']
                })
                response.update({'hasError': False, 'message': _(f"{data['message']}")})
            else:
                response.update({'hasError': True, 'message': _(f"Unsuccessful sign, message: {data['message']}")})
        except Exception as e:
            response.update({'hasError': True, 'message': _(e)})
        
        return response