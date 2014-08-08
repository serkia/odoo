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
            'hidden.bs.modal': 'destroy', //buggy, don't know why
        },
        init: function(self, name) {
            this.name = name.split("'")[1];
            this.parent = self;
        },

        start: function() {
            // this.$el.find('#score_name').attr('placeholder',this.name);
            this.$el.find('#score_name').text(this.name);
            this.$el.modal();
        },

        createScore: function (event) {
            var self = this;
            // var name_input = $('#score_name').val();
            // var name = name_input ? name_input : this.name;
            var value_input = $('#score_value').val();
            var value = $.isNumeric(value_input) ? value_input : 0;
            var model = website.session.model('website.crm.score');
            model.call('create_score', [{'name':self.name, 'value':value}, website.get_context()]).then(function (data) { 
                self.parent.setScoreToView({'id':data});
            }).then(function() {
                self.$el.modal('hide'); 
            });
        },

        destroy: function () {
            this._super();
        },
    });

    website.score.Configurator = openerp.Widget.extend({
    	template: 'website.set.score',
        events: {
            'click button[data-action=save_score]': 'saveScore',
            'hidden.bs.modal': 'destroy', //buggy, don't know why
        },

        start: function() {
            var last;
            var self = this;
            this.$el.modal();
            this.$el.find('#link').select2({
                minimumInputLength: 1,
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
                    self.$el.modal('hide');
                }
            });
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

        getMainObject: function () {
            var repr = $('html').data('main-object');
            var m = repr.match(/(.+)\((\d+),(.*)\)/);
            if (!m) {
                return null;
            } else {
                return {
                    model: m[1],
                    id: m[2]|0
                };
            }
        },

        saveScore: function(event) {
            var self = this;
            var data = $('#link').select2('data');
            this.setScoreToView(data);
            self.$el.modal('hide'); // error : Uncaught TypeError: Cannot read property 'callbackList' of undefined
        },

        setScoreToView: function(data) {
            var obj = this.getMainObject();
            if (!obj) {
                return $.Deferred().reject();
            } else {
                if (data){
                    var id = data.id;
                    var model = website.session.model(obj.model);
                    var towrite = { score_id: data.id }
                    model.call('write', [[obj.id], towrite, website.get_context()]); 
                }
            }
        },

        destroy: function () {
            this._super();
        },

    });

    website.ready().done(function() {
        $(document.body).on('click', 'a[data-action=set_score]', function() {
            new website.score.Configurator(this).appendTo($(document.body));
        });
    });


})();
