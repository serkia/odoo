$(document).ready(function () {
        $('.check_coupon').live('click', function (ev) {
            var $el = $("div.coupon_box");
            var promocode = $el.find("input[name='promo']").val();
            openerp.jsonRpc('/shop/apply_coupon','call', {'promo': promocode})
                .then(function(data) {
                    if (data['error']){
                        if (data['error'] == 'no_coupon'){
                            var $warning = $('<div class="alert alert-danger" id="nocoupon_alert">'+
                                '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                                'Coupon '+ promocode + ' does not exist OR applied.' +
                                '</div>');
                        }else if (data['error'] == 'coupon_expired'){
                            var $warning = $('<div class="alert alert-danger" id="nocoupon_alert">'+
                                '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                                'Coupon '+ promocode + ' exist but is expired.' +
                                '</div>')
                        }else if (data['error'] == 'coupon_used'){
                            var $warning = $('<div class="alert alert-danger" id="nocoupon_alert">'+
                                '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                                'Coupon '+ promocode + ' reached limit of usage.' +
                                '</div>')
                        }
                        nocoupon_alert = $el.parent().find("#nocoupon_alert");
                        if (nocoupon_alert.length == 0){
                            $el.append($warning);
                        }
                    }
                    if (data['update_price']){
                        location.reload();
                    }
                });
            return true;
        });
});
