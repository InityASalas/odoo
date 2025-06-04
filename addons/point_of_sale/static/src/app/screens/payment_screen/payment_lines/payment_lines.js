import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { parseFloat } from "@web/views/fields/parsers";
import { enhancedButtons } from "@point_of_sale/app/components/numpad/numpad";
import { PriceFormatter } from "@point_of_sale/app/components/price_formatter/price_formatter";

export class PaymentScreenPaymentLines extends Component {
    static template = "point_of_sale.PaymentScreenPaymentLines";
    static components = { PriceFormatter };
    static props = {
        paymentLines: { type: Array, optional: true },
        deleteLine: Function,
        selectLine: Function,
        sendForceDone: Function,
        sendPaymentCancel: Function,
        sendPaymentRequest: Function,
        sendPaymentReverse: Function,
        updateSelectedPaymentline: Function,
        isRefundOrder: Boolean,
    };

    setup() {
        this.ui = useService("ui");
        this.pos = usePos();
        this.dialog = useService("dialog");
    }

    selectedLineClass(line) {
        return { "payment-terminal": line.getPaymentStatus() };
    }
    unselectedLineClass(line) {
        return {};
    }
    async selectLine(paymentline) {
        this.props.selectLine(paymentline.uuid);
        if (this.ui.isSmall) {
            this.dialog.add(NumberPopup, {
                title: _t("New amount"),
                buttons: this.isTipPaymentLine(paymentline) ? undefined : enhancedButtons(),
                types: this.isTipPaymentLine(paymentline)
                    ? [
                          { name: "fixed", symbol: this.pos.currency.symbol },
                          { name: "percent", symbol: "%" },
                      ]
                    : undefined,
                startingValue:
                    this.props.tip?.type === "percent"
                        ? this.props.tip.value
                        : this.env.utils.formatCurrency(paymentline.getAmount(), false),
                startingType: this.props.tip?.type || "fixed",
                getPayload: (num, type) => {
                    console.log("getPayload", num, type);
                    let amount = typeof num === "number" ? num : parseFloat(num);
                    if (this.isTipPaymentLine(paymentline)) {
                        if (type === "percent") {
                            const currentOrder = this.pos.getOrder();
                            if (!currentOrder) {
                                amount = 0;
                            } else {
                                const totalLessTip = currentOrder.getTotalWithTax() - paymentline.getAmount();
                                amount = totalLessTip * (amount / 100);
                            }
                        }

                        this.pos.setTip(amount, { type, value: num });
                    }

                    this.props.updateSelectedPaymentline(amount, { tipType: type, tipValue: num });
                },
                formatDisplayedValue: (amount, type) => {
                    if (type === "percent") {
                        return `${amount} %`;
                    }
                    return `${this.pos.currency.symbol} ${amount}`;
                },
            });
        }
    }

    isTipPaymentLine(paymentline) {
        console.log("isTipPaymentLine", paymentline);
        return paymentline.isTipped()
    }
}
