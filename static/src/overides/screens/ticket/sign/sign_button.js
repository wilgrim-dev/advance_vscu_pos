/** @odoo-module */

import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { useAsyncLockedMethod } from "@point_of_sale/app/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

export class SignReceiptButton extends Component {
    static template = "advance_vscu_pos.SignReceiptButton";

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.printer = useService("printer");
        this.click = useAsyncLockedMethod(this.click);
    }
    _showError(msg, title) {
        if (!title) {
            title = _t("VSCU Error");
        }
        this.env.services.popup.add(ErrorPopup, {
            title: title,
            body: _t(msg),
        });
    }    
    async _getVscuData(order){
        var self = this;
        const order_server_id = order.backendId;

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
    }
    async click() {
        if (!this.props.order) {
            return;
        }

        let order = this.props.order;
        let vscuData = await this.orm.searchRead("pos.order", [['pos_reference', '=', order.name]], ['vscu_qr_code', 'vscu_date', 'vscu_data']);

        if (vscuData[0].vscu_data) { 
            order.vscu_qr_code = vscuData[0].vscu_qr_code;
            order.vscu_date = vscuData[0].vscu_date;
            order.vscu_cu = vscuData[0].vscu_serial;
            order.vscu_invoice = vscuData[0].vscu_cu;
            order.vscu_data = vscuData[0].vscu_data;
        } else {
            await this._getVscuData(order);
        }

        // Need to await to have the result in case of automatic skip screen.
        (await this.printer.print(OrderReceipt, {
            data: order.export_for_printing(),
            formatCurrency: this.env.utils.formatCurrency,
        })) || this.pos.showScreen("ReprintReceiptScreen", { order });
    }
}
