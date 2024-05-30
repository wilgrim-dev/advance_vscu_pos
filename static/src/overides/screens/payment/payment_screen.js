/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    
    async getEtimsData(){
        const order = this.currentOrder;
        const orderName = order.get_name();
        const order_server_id = this.pos.validated_orders_name_server_id_map[orderName];

        await this.orm.call('pos.order', 'action_etims_sale', [[order_server_id]]);

        return new Promise((resolve, reject) => {
            this.orm.searchRead("pos.order", [['pos_reference', '=', this.currentOrder.name]], ['etims_receipt_sign', 'etims_sdc_date', 'etims_data'])
            .then((data) => {
                resolve(data);
            })
            .catch((err) => {
                reject(err);
            })
        }); 
    },

    async afterOrderValidation(suggestToSync = true) {
        let etims;
        try {
            etims = await this.getEtimsData();
            
            this.currentOrder.etims_receipt_sign = etims[0].etims_receipt_sign;
            this.currentOrder.etims_sdc_date = etims[0].etims_sdc_date;
            this.currentOrder.etims_cu = etims[0].etims_data.sdcId.split('/')[0];
            this.currentOrder.etims_invoice = etims[0].etims_data.sdcId;
            this.currentOrder.etims_internal_data = etims[0].etims_data.intrlData;
            this.currentOrder.etims_signature = etims[0].etims_data.rcptSign;
            
        } catch (error) {
            throw error;
        }
        await super.afterOrderValidation(...arguments);
    },

});