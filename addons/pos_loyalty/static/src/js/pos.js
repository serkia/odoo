openerp.pos_loyalty = function(instance){

    var module   = instance.point_of_sale;
    var round_pr = instance.web.round_precision
    var QWeb     = instance.web.qweb;

    QWeb.add_template('/pos_loyalty/static/src/xml/pos.xml');

    var models = module.PosModel.prototype.models;
    for (var i = 0; i < models.length; i++) {
        var model = models[i];
        if (model.model === 'product.product') {
            model.fields.push('loyalty_points');
            model.fields.push('loyalty_override');
        } else if (model.model === 'res.partner') {
            model.fields.push('loyalty_points');
        } else if (model.model === 'pos.config') {
            // load loyalty after pos.config
            models.splice(i+1,0,{
                model: 'loyalty.program',
                condition: function(self){ return !!self.config.loyalty_id[0]; },
                fields: ['name','pp_currency','pp_product','pp_order','rounding'],
                domain: function(self){ return [['id','=',self.config.loyalty_id[0]]]; },
                loaded: function(self,loyalties){ self.loyalty = loyalties[0]; },
            },{
                model: 'loyalty.rule',
                condition: function(self){ return !!self.loyalty; },
                fields: ['name','type','product_id','category_id','override','pp_product','pp_currency'],
                domain: function(self){ return [['loyalty_program_id','=',self.loyalty.id]]; },
                loaded: function(self,rules){ 

                    self.loyalty.rules = rules; 
                    self.loyalty.rules_by_product_id = {};

                    for (var i = 0; i < rules.length; i++){
                        var rule = rules[i];
                        if (!self.loyalty.rules_by_product_id[rule.product_id[0]]) {
                            self.loyalty.rules_by_product_id[rule.product_id[0]] = [rule];
                        } else if (rule.override) {
                            self.loyalty.rules_by_product_id[rule.product_id[0]].unshift(rule);
                        } else {
                            self.loyalty.rules_by_product_id[rule.product_id[0]].push(rule);
                        }
                    }
                },
            },{
                model: 'loyalty.reward',
                condition: function(self){ return !!self.loyalty; },
                fields: ['name','type','minimum_points','gift_product_id','point_cost','discount_product_id','discount'],
                domain: function(self){ return [['loyalty_program_id','=',self.loyalty.id]]; },
                loaded: function(self,rewards){
                    self.loyalty.rewards = rewards; 
                },
            });
        }
    }

    var _super = module.Order;
    module.Order = module.Order.extend({
        get_loyalty_points: function(){
            if (!this.pos.loyalty) {
                return 0;
            }
            
            var orderLines = this.get('orderLines').models;
            var rounding   = this.pos.loyalty.rounding;
            
            var product_sold = 0;
            var total_sold   = 0;
            var total_points = 0;

            for (var i = 0; i < orderLines.length; i++) {
                var line = orderLines[i];
                var product = line.get_product();
                var rules  = this.pos.loyalty.rules_by_product_id[product.id] || [];
                var overriden = false;
                
                for (var j = 0; j < rules.length; j++) {
                    var rule = rules[j];
                    total_points += round_pr(line.get_quantity() * rule.pp_product, rounding);
                    total_points += round_pr(line.get_price_with_tax() * rule.pp_currency, rounding);
                    if (rule.override) {
                        overriden = true;
                        break;
                    }
                }

                if (!overriden) {
                    product_sold += line.get_quantity();
                    total_sold   += line.get_price_with_tax();
                }
            }

            total_points += round_pr( total_sold * this.pos.loyalty.pp_currency, rounding );
            total_points += round_pr( product_sold * this.pos.loyalty.pp_product, rounding );
            total_points += round_pr( this.pos.loyalty.pp_order, rounding );

            return total_points;
        },
        validate: function(){
            var client = this.get('client');
            if( client ){
                client.loyalty_points += this.get_loyalty_points();
            }
            _super.prototype.validate.apply(this,arguments);
        },
        export_for_printing: function(){
            var json = _super.prototype.export_for_printing.apply(this,arguments);
            json.loyalty_points = this.get_loyalty_points();
            return json;
        },
        export_as_JSON: function(){
            var json = _super.prototype.export_as_JSON.apply(this,arguments);
            json.loyalty_points = this.get_loyalty_points();
            return json;
        },
    });

    module.PosWidget.include({
        build_widgets: function(){
            var self = this;
            this._super();
            
            if(!this.pos.loyalty){
                return;
            }

            return;

            var discount = $(QWeb.render('DiscountButton'));

            discount.click(function(){
                var order = self.pos.get('selectedOrder');
                if( !order.get('client') ){
                    self.screen_selector.set_current_screen('clientlist');
                }else if( order.getTotalTaxIncluded() < self.pos.loyalty.minimum_sale ){
                    self.screen_selector.show_popup('error',{
                        message: 'Cannot Apply Discount',
                        comment: 'The minimum sale amount eligible for a discount is '+self.format_currency(self.pos.loyalty.minimum_sale), 
                    });
                }else if( !self.pos.loyalty.discount_product_id || 
                          !self.pos.db.get_product_by_id(self.pos.loyalty.discount_product_id[0]) ){
                    self.screen_selector.show_popup('error',{
                        message: 'Configuration Error',
                        comment: 'Either there is no discount product set or it is not available in the Point of Sale. Please contact your System Administrator',
                    });
                }else{
                    order.addProduct(self.pos.db.get_product_by_id(self.pos.loyalty.discount_product_id[0]));
                }
            });

            discount.appendTo(this.$('.control-buttons'));
            this.$('.control-buttons').removeClass('oe_hidden');
        },
    });

    module.OrderWidget.include({
        update_summary: function(){
            this._super();

            var order = this.pos.get_order();

            var $loypoints = $(this.el).find('.summary .loyalty-points');

            if(this.pos.loyalty && order.get_client()){
                var points        = order.get_loyalty_points();
                var points_total  = order.get_client().loyalty_points + points; 
                var points_str    = this.format_pr(points, this.pos.loyalty.rounding); 
                var total_str     = this.format_pr(points_total, this.pos.loyalty.rounding);
                if( points && points > 0 ){
                    points_str = '+' + points_str;
                }
                $loypoints.replaceWith($(QWeb.render('LoyaltyPoints',{ 
                    widget: this, 
                    totalpoints: total_str, 
                    wonpoints: points_str 
                })));
                $loypoints = $(this.el).find('.summary .loyalty-points');
                $loypoints.removeClass('oe_hidden');

                if(points_total < 0){
                    $loypoints.addClass('negative');
                }else{
                    $loypoints.removeClass('negative');
                }
            }else{
                $loypoints.empty();
                $loypoints.addClass('oe_hidden');
            }
        },
    });
};

    
