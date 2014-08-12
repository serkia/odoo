(function() {
    "use strict";

    var website = openerp.website;
    var _t = openerp._t;

    website.add_template_file('/website_crm_score/static/src/xml/website.score.xml');

    website.score = {};


    website.score.Creator = openerp.Widget.extend({
        template: 'website.create.score',
        events: {
            'click button[data-action=create_score]': 'createScore',
        },
        init: function(self, name) {
            this.name = name.split("'")[1];
            this.parent = self;
        },

        start: function() {
            this.$el.find('#score_name').text(this.name);
            this.$el.modal();
        },

        createScore: function (event) {
            var self = this;
            var value_input = $('#score_value').val();
            var value = $.isNumeric(value_input) ? value_input : 0;
            var model = website.session.model('website.crm.score');
            model.call('create_score', [{'name':self.name, 'value':value}, website.get_context()]).then(function (data) {
                self.parent.$el.find("#link").select2("data", { id: data, text: self.name });
            }).then(function() {
                self.$el.modal('hide');
            });
        },
    });

    website.seo.Configurator.include({       
        start: function() {
            var last;
            var self = this;
            // var currentScore = this.getCurrentScore(); // to get the place holder
            this.$el.find('#link').select2({
                minimumInputLength: 1,
                // put in placeholder the name of the score currently used
                placeholder: _t("Crm Score"),
                query: function (q) {
                    if (q.term == last) return;
                    last = q.term;

                    $.when(
                        self.score_exists(q.term),
                        self.fetch_scores(q.term)
                    ).then(function (exists, results) {
                        var rs = _.map(results, function (r) {
                            return { id: r.id, text: r.name, };
                        });
                        if (!exists) {
                            rs.push({
                                create: true,
                                id: q.term,
                                text: _.str.sprintf(_t("Create Score '%s'"), q.term),
                            });
                        }
                        q.callback({
                            more: false,
                            results: rs
                        });
                    });
                },
            });
            this.$el.find('#link').on("change", function(e) {
                var data = $('#link').select2('data');
                if (data.create){
                    new website.score.Creator(self, data.text).appendTo($(document.body));
                }
            });
            this._super.apply(this, arguments);
        },

        call: function (method, args, kwargs) {
            var self = this;

            return openerp.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'website.crm.score',
                method: method,
                args: args,
                kwargs: kwargs,
            });
        },

        score_exists: function (term) {
            return this.call('score_exists', [null, term], {
                context: website.get_context(),
            });
        },

        fetch_scores: function (term) {
            return this.call('search_scores', [null, term], {
                limit: 9,
                context: website.get_context(),
            });
        },

        getCurrentScore: function() {
            var obj = website.seo.Configurator.prototype.getMainObject();
            if (!obj) {
                return $.Deferred().reject();
            } else {
                return website.session.model(obj.model).call('read', [[obj.id], ['score_id'], website.get_context()]);
            }
        },

        setScoreToView: function(data) {
            var obj = website.seo.Configurator.prototype.getMainObject();
            if (!obj) {
                return $.Deferred().reject();
            } else {
                if (data){
                    // error here:
// 2014-08-12 06:43:58,787 3238 ERROR lde-test openerp.sql_db: bad query: update ir_ui_view set "website_meta_keywords"='',"website_meta_title"='YourCompany - Homepage',write_uid=1,write_date=(now() at time zone 'UTC') where id IN (317)
// Traceback (most recent call last):
// File "/home/lde/Odoo/git/odoo/openerp/sql_db.py", line 230, in execute
// res = self._obj.execute(query, params)
// TransactionRollbackError: could not serialize access due to concurrent update
                    return website.session.model(obj.model).call('write', [[obj.id], { score_id: data.id }, website.get_context()]);
                }
            }
        },

        update: function () {
            var self = this;
            self._super();
            var data = $('#link').select2('data');
            //debugger;
            this.setScoreToView(data).then( function(xx) {
                console.log("def");
                //debugger;
                
            });
            
        },

    });

})();
