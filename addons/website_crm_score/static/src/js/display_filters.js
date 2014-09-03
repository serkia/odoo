openerp.website_crm_score = function(instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.website_crm_score = {};

    instance.website_crm_score.filters = instance.web_kanban.AbstractField.extend({
        start: function() {
            var val = this.field.raw_value;
            var self = this;
            if (val) {
                _.each(eval(val), function(a){
                    var $span = $('<span class="oe_tag" title=' + a[0] + '>'+ a[2] +'</span>');
                    self.$el.append($span);
                });
            }
        },
    });

    instance.web_kanban.fields_registry.add('filters', 'instance.website_crm_score.filters');
}
