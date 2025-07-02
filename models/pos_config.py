from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    vscu_config = fields.Boolean('Send to VSCU?', default=False)
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    pos_vscu_config = fields.Boolean(related='pos_config_id.vscu_config', readonly=False)