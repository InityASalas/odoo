import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    /**
     * @override
     */
    setup() {
        super.setup();
        if (
            !this.payment_methods_from_config.some(
                (pm) =>
                    pm.id ===
                    this.currentOrder.refunded_order_id?.payment_ids[0].payment_method_id.id
            ) &&
            ["Kiosk", "Self-Order"].some((keyword) =>
                this.currentOrder.refunded_order_id?.pos_reference.includes(keyword)
            ) &&
            this.currentOrder.refunded_order_id?.payment_ids[0].online_account_payment_id
        ) {
            this.payment_methods_from_config = [
                ...this.payment_methods_from_config,
                this.pos.config.self_order_online_payment_method_id,
            ];
        }
        this.pollingTimeout = null;
    },
    /**
     * @override
     */
    async validateOrder(isForceValidate) {
        if (this.currentOrder.refunded_order_id?.payment_ids[0].online_account_payment_id) {
            const onlinePMIds = this.payment_methods_from_config
                .filter((method) => method.is_online_payment)
                .map((method) => method.id);
            this.env.services.ui.block();
            for (const line of this.currentOrder.payment_ids) {
                if (onlinePMIds.includes(line.payment_method_id.id)) {
                    const paymentTransactionId = await this.pos.data.orm.call(
                        "account.payment",
                        "send_refund_request",
                        [
                            this.currentOrder.refunded_order_id.payment_ids[0]
                                .online_account_payment_id.id,
                            Math.abs(line.amount),
                        ]
                    );
                    if (!paymentTransactionId) {
                        this.pos.notification.add(
                            _t("Refund request failed try with another payment method."),
                            {
                                type: "danger",
                                sticky: false,
                            }
                        );
                        this.env.services.ui.unblock();
                        return;
                    }
                    let accountPaymentId = await this.refundOnlineOrder(paymentTransactionId);
                    if (!accountPaymentId) {
                        this.pos.notification.add(
                            _t("Refund request failed try with another payment method."),
                            {
                                type: "danger",
                                sticky: false,
                            }
                        );
                        this.env.services.ui.unblock();
                        return;
                    }
                    accountPaymentId = await this.pos.data.searchRead("account.payment", [
                        ["id", "=", accountPaymentId],
                    ]);
                    line.online_account_payment_id = accountPaymentId[0];
                }
            }
            this.env.services.ui.unblock();
        }
        return await super.validateOrder(...arguments);
    },
    async refundOnlineOrder(paymentTransactionId) {
        let retryCount = 0;
        return new Promise((resolve, reject) => {
            const tryFetch = async () => {
                try {
                    const accountPaymentId = await this.pos.data.orm.call(
                        "account.payment",
                        "get_account_payment_id",
                        [false, paymentTransactionId]
                    );
                    if (accountPaymentId) {
                        return resolve(accountPaymentId);
                    }
                    if (retryCount >= 5) {
                        return resolve(false);
                    }
                    retryCount++;
                    this.pollingTimeout = setTimeout(tryFetch, 5000);
                } catch (error) {
                    reject(error);
                }
            };
            tryFetch();
        });
    },
});
