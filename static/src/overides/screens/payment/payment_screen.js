/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(PaymentScreen.prototype, {

    _showError(msg, title) {
        if (!title) {
            title = _t("VSCU Error");
        }
        this.env.services.popup.add(ErrorPopup, {
            title: title,
            body: _t(msg),
        });
    },
    
    async getVscuData(){
        var self = this;
        const order = this.currentOrder;
        const orderName = order.get_name();
        const order_server_id = this.pos.validated_orders_name_server_id_map[orderName];

        let vscuData = await this.orm.call('pos.order', 'action_vscu_sale', [[order_server_id]]);

        if (vscuData.hasError) {
            return this._showError(vscuData.message?.message || vscuData.message);
        }
        
        return new Promise((resolve, reject) => {
            this.orm.searchRead("pos.order", [['pos_reference', '=', order.name]], ['vscu_qr_code', 'vscu_date', 'vscu_data'])
            .then((data) => {
                if (Object.keys(data).length !== 0) {
                    order.vscu_qr_code = data[0].vscu_qr_code;
                    order.vscu_date = data[0].vscu_date;
                    order.vscu_cu = data[0].vscu_serial;
                    order.vscu_invoice = data[0].vscu_cu;
                    order.vscu_data = data[0].vscu_data;
                }
                resolve(data);
            })
            .catch((err) => {
                self._showError(err);
                reject(err);
            })
        }); 
    },

    async afterOrderValidation(suggestToSync = true) {
        var vscuSign = false;    
        var paymentlines = this.currentOrder.paymentlines;

        for (var i in paymentlines) {
            if (paymentlines[i].payment_method.vscu_sign) { 
                vscuSign = true;
            }
        }
        if (vscuSign) {
            await this.getVscuData();
        }

        await super.afterOrderValidation(...arguments);
    },

});