from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError

from requests.auth import HTTPBasicAuth
import requests, logging
import os
import json

_logger = logging.getLogger(__name__)

current = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current, os.pardir))
data_dir = os.path.join(parent_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

JSON_FILE = [
    os.path.join(data_dir, 'qtyUnitCode.json'),
    os.path.join(data_dir, 'pkgUnitCode.json'), 
    os.path.join(data_dir, 'itemClassCode.json'),
    os.path.join(data_dir, 'items.json')
]

ITEM_CODE = {
    'service': 3,
    'product': 2,    
}

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def _update_qty_code(self):
        qty_codes = []
        try:
            with open(JSON_FILE[0], 'r', encoding='utf-8') as f:
                read_data = json.load(f)['data']
            if isinstance(read_data, list):
                for item in read_data:
                    key = item.get('code')
                    value = item.get('name')
                    if (key, value) not in qty_codes: qty_codes.append((key, value))
        except Exception as e:
            return qty_codes
        return qty_codes
    
    @api.model
    def _update_pkg_code(self):
        pkg_codes = []        
        try:
            with open(JSON_FILE[1], 'r', encoding='utf-8') as f:
                read_data = json.load(f)['data']
            if isinstance(read_data, list):
                for item in read_data:
                    key = item.get('code')
                    value = item.get('name')
                    if (key, value) not in pkg_codes: pkg_codes.append((key, value)) 
        except Exception as e:
            return pkg_codes
        return pkg_codes
    
    @api.model
    def _update_item_code(self):
        item_codes = []
        try:
            with open(JSON_FILE[2], 'r', encoding='utf-8') as f:
                read_data = json.load(f)['data']
            if isinstance(read_data, list):
                for item in read_data:
                    key = item.get('code')
                    value = item.get('name')
                    if (key, value) not in item_codes: item_codes.append((key, value)) 
        except Exception as e:
            return item_codes
        return item_codes
    
    product_hs_code = fields.Char('Hs Code', readonly=True, compute='_compute_product_hs_code', store=True)
    qty_code = fields.Selection(selection='_update_qty_code', string='Qty Code')
    pkg_code = fields.Selection(selection='_update_pkg_code', string='Pkg Code')
    item_code = fields.Selection(selection='_update_item_code', string='Item Code')
    
    def _set_vscu_credentials(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('vscu.url')
        username = self.env['ir.config_parameter'].sudo().get_param('vscu.username')
        password = self.env['ir.config_parameter'].sudo().get_param('vscu.password')
        
        if not base_url or not username or not password:
            raise UserError("Kindly setup vscu.url, vscu.username, and vscu.password parameters in system configuration!")
        
        auth = HTTPBasicAuth(username, password)   
        
        return base_url, auth
           
    def _get_qtyUnitCode(self):          
        base_url, auth = self._set_vscu_credentials()
                
        try:
            url = base_url + '/qtyunitcodes'
            response = requests.get(url, auth=auth, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            qtyUnitCode = response.json()
            
            if os.path.exists(JSON_FILE[0]):
                os.remove(JSON_FILE[0])
            _logger.info(f'Unit Codes: {qtyUnitCode, JSON_FILE}')
                
            with open(JSON_FILE[0], 'w', encoding='utf-8') as f:
                json.dump(qtyUnitCode, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise ValidationError(e)

    def _get_pkgUnitCode(self):
        base_url, auth = self._set_vscu_credentials()
        
        try:
            url = base_url + '/pkgunitcodes'
            response = requests.get(url, auth=auth, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            pkgUnitCode = response.json()
            
            if os.path.exists(JSON_FILE[1]):
                os.remove(JSON_FILE[1])                            
            _logger.info(f'Unit Codes: {pkgUnitCode, JSON_FILE}')
                
            with open(JSON_FILE[1], 'w', encoding='utf-8') as f:
                json.dump(pkgUnitCode, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise ValidationError(e)
    
    def _get_itemClassCode(self):
        base_url, auth = self._set_vscu_credentials()
        
        try:
            url = base_url + '/itemcodes'
            response = requests.get(url, auth=auth, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            itemClassCode = response.json()
            
            if os.path.exists(JSON_FILE[2]):
                os.remove(JSON_FILE[2])                            
            _logger.info(f'Unit Codes: {itemClassCode, JSON_FILE}')
                
            with open(JSON_FILE[2], 'w', encoding='utf-8') as f:
                json.dump(itemClassCode, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise ValidationError(e) 
        
    def _get_items(self):
        base_url, auth = self._set_vscu_credentials()
        
        try:
            url = base_url + '/items'
            response = requests.get(url, auth=auth, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            items = response.json()
            
            if os.path.exists(JSON_FILE[3]):
                os.remove(JSON_FILE[3])                           
                
            with open(JSON_FILE[3], 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise ValidationError(e) 
    
    @api.depends('qty_code', 'pkg_code', 'item_code')
    def _compute_product_hs_code(self):
        for product in self:
            try:
                with open(JSON_FILE[3], 'r', encoding='utf-8') as f:
                    read_data = json.load(f)['data']
                if isinstance(read_data, list):
                    for item in read_data:
                        if item['name'] == self.name:
                            product.product_hs_code = item['itemCode']    
            except Exception as e:
                pass
                
    # def action_get_qty_codes(self):
    #     self._get_qtyUnitCode()
        
    # def action_get_pkg_codes(self):
    #     self._get_pkgUnitCode()
        
    # def action_get_item_codes(self):
    #     self._get_itemClassCode()
        
    def action_vscu_data(self):
        self._get_qtyUnitCode()
        self._get_itemClassCode()
        self._get_pkgUnitCode()
        self._get_items()
        
    def action_save_vscu(self):
        """ Payload: {
            "name": "Item B",
            "orgCountryCode": "KE",
            "unitPrice": 100,
            "itemTypeCode": "1",
            "taxCode": "A",
            "qtyUnitCode": "U",
            "pkgUnitCode": "CT",
            "itemClassCode": "99000000",
            "initialStock": 0
        }
        """
        self.ensure_one()
        product = {
            "name": self.name.strip(),
            "orgCountryCode": "KE",
            "unitPrice": self.list_price,
            "itemTypeCode": str(ITEM_CODE[self.detailed_type]),
            "taxCode": self.taxes_id.tax_class,
            "qtyUnitCode": self.qty_code,
            "pkgUnitCode": self.pkg_code,
            "itemClassCode": self.item_code,
            "initialStock": self.qty_available
        }
        
        base_url, auth = self._set_vscu_credentials()
        
        try:
            url = base_url + '/items'                     
            data = requests.post(url, json=product, auth=auth, headers={'Content-Type': 'application/json'})
            data.raise_for_status()
            data = data.json()
            _logger.info(f'VSCU Response: {data, product}')
            self.product_hs_code = data['data']['itemCode']
        except Exception as e:
            raise ValidationError(e)

class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    tax_class = fields.Selection([
        ('A', 'Exempt'),
        ('B', '16%'),
        ('C', 'Zero Rated'),
        ('D', '8%'),
        ('E', '0%'),
        ], string='Tax Class')