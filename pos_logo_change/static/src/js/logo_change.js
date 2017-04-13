odoo.define('pos_logo_change.pos_discount', function (require) {
"use strict";
var chrome = require('point_of_sale.chrome');
var screens = require('point_of_sale.screens');
var models = require('point_of_sale.models');
var PaymentScreenWidget = screens.PaymentScreenWidget;


var _super_order = models.Order.prototype;
models.Order = models.Order.extend({
    initialize: function() {
        _super_order.initialize.apply(this,arguments);
        this.save_to_db();
    },

    is_paid: function(){

        return this.get_due() <= 2;
    },

    });

PaymentScreenWidget.include({
        validate_order: function(force_validation) {
                var self = this;



        var order = this.pos.get_order();

        // FIXME: this check is there because the backend is unable to
        // process empty orders. This is not the right place to fix it.
        if (order.get_orderlines().length === 0) {
            this.gui.show_popup('error',{
                'title': _t('Empty Order'),
                'body':  _t('There must be at least one product in your order before it can be validated'),
            });
            return;
        }

        var plines = order.get_paymentlines();
        for (var i = 0; i < plines.length; i++) {
            if (plines[i].get_type() === 'bank' && plines[i].get_amount() < 0) {
                this.pos_widget.screen_selector.show_popup('error',{
                    'message': _t('Negative Bank Payment'),
                    'comment': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                });
                return;
            }
        }


//        if (!order.is_paid() || this.invoicing) {
//            return;
//        }
//
        var round_value =  this.pos.config.round_value

        if (order.get_due() > round_value || this.invoicing){
            return;
        }
        var balance = order.get_total_with_tax() - order.get_total_paid()
        if ( balance<=round_value && balance >0){
            var product  = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);
            order.add_product(product, { price: -balance });


        }


        // The exact amount must be paid if there is no cash payment method defined.
        if (Math.abs(order.get_total_with_tax() - order.get_total_paid()) > 1) {
            var cash = false;
            for (var i = 0; i < this.pos.cashregisters.length; i++) {
                cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
            }
            if (!cash) {
                this.gui.show_popup('error',{
                    title: _t('Cannot return change without a cash payment method'),
                    body:  _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                });
                return;
            }
        }

        // if the change is too large, it's probably an input error, make the user confirm.
        if (!force_validation && (order.get_total_with_tax() * 1000 < order.get_total_paid())) {
            this.gui.show_popup('confirm',{
                title: _t('Please Confirm Large Amount'),
                body:  _t('Are you sure that the customer wants to  pay') +
                       ' ' +
                       this.format_currency(order.get_total_paid()) +
                       ' ' +
                       _t('for an order of') +
                       ' ' +
                       this.format_currency(order.get_total_with_tax()) +
                       ' ' +
                       _t('? Clicking "Confirm" will validate the payment.'),
                confirm: function() {
                    self.validate_order('confirm');
                },
            });
            return;
        }

        if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) {

                this.pos.proxy.open_cashbox();
        }

        order.initialize_validation_date();

        if (order.is_to_invoice()) {
            var invoiced = this.pos.push_and_invoice_order(order);
            this.invoicing = true;

            invoiced.fail(function(error){
                self.invoicing = false;
                if (error.message === 'Missing Customer') {
                    self.gui.show_popup('confirm',{
                        'title': _t('Please select the Customer'),
                        'body': _t('You need to select the customer before you can invoice an order.'),
                        confirm: function(){
                            self.gui.show_screen('clientlist');
                        },
                    });
                } else if (error.code < 0) {        // XmlHttpRequest Errors
                    self.gui.show_popup('error',{
                        'title': _t('The order could not be sent'),
                        'body': _t('Check your internet connection and try again.'),
                    });
                } else if (error.code === 200) {    // OpenERP Server Errors
                    self.gui.show_popup('error-traceback',{
                        'title': error.data.message || _t("Server Error"),
                        'body': error.data.debug || _t('The server encountered an error while receiving your order.'),
                    });
                } else {                            // ???
                    self.gui.show_popup('error',{
                        'title': _t("Unknown Error"),
                        'body':  _t("The order could not be sent to the server due to an unknown error"),
                    });
                }
            });

            invoiced.done(function(){
                self.invoicing = false;
                order.finalize();
            });
        } else {
            this.pos.push_order(order);
            this.gui.show_screen('receipt');
        }
    },
    });


});


