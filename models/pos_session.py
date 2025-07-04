from odoo import api, models

from odoo import fields, models, api

class PoSPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'
    
    vscu_sign = fields.Boolean('Sign to VSCU?', default=False)
    
    
class PosSession(models.Model):
    _inherit = 'pos.session'
    
    def _loader_params_pos_payment_method(self):
        vals = super()._loader_params_pos_payment_method()
        vals['search_params']['fields'].append('vscu_sign')
        return vals