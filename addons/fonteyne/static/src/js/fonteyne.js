openerp.fonteyne = function(instance){
    var module = instance.point_of_sale;
    var QWeb = instance.web.qweb;

    QWeb.add_template('/fonteyne/static/src/xml/fonteyne.xml');

    console.log('Coucou!');

    module.PosWidget.include({
        build_widgets: function(){
            var self = this;
            this._super();
            
            if(!this.pos.fidelity){
                return;
            }

            var discount = $(QWeb.render('DiscountButton'));

            discount.click(function(){
                var order = self.pos.get('selectedOrder');
                if( !order.get('client') ){
                    self.screen_selector.set_current_screen('clientlist');
                }else if( order.getTotalTaxIncluded() < self.pos.fidelity.minimum_sale ){
                    self.screen_selector.show_popup('error',{
                        message: 'Cannot Apply Discount',
                        comment: 'The minimum sale amount eligible for a discount is '+self.format_currency(self.pos.fidelity.minimum_sale), 
                    });
                }else if( !self.pos.fidelity.discount_product_id || 
                          !self.pos.db.get_product_by_id(self.pos.fidelity.discount_product_id[0]) ){
                    self.screen_selector.show_popup('error',{
                        message: 'Configuration Error',
                        comment: 'Either there is no discount product set or it is not available in the Point of Sale. Please contact your System Administrator',
                    });
                }else{
                    order.addProduct(self.pos.db.get_product_by_id(self.pos.fidelity.discount_product_id[0]));
                }
            });

            discount.appendTo(this.$('.control-buttons'));
            this.$('.control-buttons').removeClass('oe_hidden');
        },
    });
};

    
