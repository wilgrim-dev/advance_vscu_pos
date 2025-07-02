/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    
    async getVscuData(){
        const order = this.currentOrder;
        const orderName = order.get_name();
        const order_server_id = this.pos.validated_orders_name_server_id_map[orderName];

        await this.orm.call('pos.order', 'action_vscu_sale', [[order_server_id]]);

        return new Promise((resolve, reject) => {
            this.orm.searchRead("pos.order", [['pos_reference', '=', this.currentOrder.name]], ['vscu_qr_code', 'vscu_date', 'vscu_data'])
            .then((data) => {
                resolve(data);
            })
            .catch((err) => {
                reject(err);
            })
        }); 
    },

    async afterOrderValidation(suggestToSync = true) {
        let vscu;
        try {
            vscu = await this.getVscuData();
            
            this.currentOrder.vscu_qr_code = vscu[0].vscu_qr_code;
            this.currentOrder.vscu_date = vscu[0].vscu_date;
            this.currentOrder.vscu_cu = vscu[0].vscu_data.sdcId.split('/')[0];
            this.currentOrder.vscu_invoice = vscu[0].vscu_data.sdcId;
            this.currentOrder.vscu_data = vscu[0].vscu_data.intrlData;
            
        } catch (error) {
            throw error;
        }
        await super.afterOrderValidation(...arguments);
    },

});