import logging, json, base64, re
from datetime import datetime as dt
from io import BytesIO
from qrcode import QRCode, constants

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_compare

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
        
    vscu_data = fields.Json('VSCU Data', copy=False, readonly=True)
    vscu_receipt_sign = fields.Binary('VSCU Sign', attachment=True, copy=False, readonly=True, store=True)
    vscu_sdc_date = fields.Datetime('VSCU Date', readonly=True)    
       
    def _vscu_item_code(self, product, uom_id):
        pass
    
    def _vscu_qrcode(self, receipt_sign):
        pass
    
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
        pass
                   
    def action_vscu_sale(self):
        self.ensure_one()
        pass