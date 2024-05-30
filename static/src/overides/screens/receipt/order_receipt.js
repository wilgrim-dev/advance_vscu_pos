/** @odoo-module **/

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(Order.prototype, {
    setup () {
        this.etims_receipt_sign = ''; 
        this.etims_sdc_date = '';   
        this.etims_cu = '';   
        this.etims_invoice = '';   
        this.etims_internal_data = '';   
        this.etims_signature = '';        
        super.setup(...arguments);
    },
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.etims_receipt_sign = this.etims_receipt_sign;
        result.etims_sdc_date = this.etims_sdc_date;
        result.etims_cu = this.etims_cu;
        result.etims_internal_data = this.etims_internal_data;
        result.etims_invoice = this.etims_invoice;
        result.etims_signature = this.etims_signature;
        return result;
    },
});