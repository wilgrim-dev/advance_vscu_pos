/** @odoo-module **/

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(Order.prototype, {
    setup () {
        this.vscu_qr_code = ''; 
        this.vscu_date = '';   
        this.vscu_cu = '';   
        this.vscu_invoice = '';
        this.vscu_data = '';      
        super.setup(...arguments);
    },
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.vscu_qr_code = this.vscu_qr_code;
        result.vscu_date = this.vscu_date;
        result.vscu_cu = this.vscu_cu;
        result.vscu_data = this.vscu_data;
        result.vscu_invoice = this.vscu_invoice;
        return result;
    },
});