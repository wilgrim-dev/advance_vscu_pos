from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    vscu_config = fields.Boolean('Send to VSCU?', default=False)