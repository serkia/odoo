openerp.account_analytic_analysis = function(openerp) {
    var QWeb = openerp.web.qweb;
    
    QWeb.add_template('/account_analytic_analysis/static/src/xml/analytic_state.xml');
    openerp.web.form.AnalyticState = openerp.web.form.FieldSelection.extend({
        render_value: function(){
            this._super();
            var found = _.find(this.get("values"), function(el) { return el[0] === this.get("value"); }, this);
            var state = {'draft': 'info','open': 'success', 'pending': 'danger', 'close': 'warning', 'cancelled': 'warning', 'template': 'default'};
            this.$el.html(QWeb.render("Widget_analytic_state", {'value': found, 'state': state}));
        }
    });
    
    openerp.web.form.widgets = openerp.web.form.widgets.extend({
        'analytic_state' : 'openerp.web.form.AnalyticState',
    });
};
