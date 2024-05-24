/** @odoo-module **/

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(Order.prototype, {

    getEtimsData(){
        let order = this.pos.get_order();

        return new Promise((resolve, reject) => {
            this.pos.orm.searchRead("pos.order", [['pos_reference', '=', order.name]], ['etims_receipt_sign', 'etims_sdc_date'])
            .then((data) => {
                resolve(data);
            })
            .catch((err) => {
                reject(err);
            })
        }); 
    },
    export_for_printing() {
        const print_data = super.export_for_printing(...arguments);
        this.getEtimsData().then((data) => {
            print_data.etims_receipt_sign = data[0].etims_receipt_sign;
            print_data.etims_sdc_date = data[0].etims_sdc_date;
        });
    }
});