/** @odoo-module */
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { SignReceiptButton } from "./sign/sign_button";

TicketScreen.components = {
    ...TicketScreen.components,
    SignReceiptButton
};
