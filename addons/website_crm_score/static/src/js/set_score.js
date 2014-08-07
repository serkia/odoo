(function() {
    "use strict";

    var website = openerp.website;
    var _t = openerp._t;

    // website.EditorBarContent.include({
    //     set_score: function() {
    //         website.prompt({
    //             id: "editor_score",
    //             window_title: _t("New Score"),
    //             input: "Score Value",
    //         }).then(function (name) {
    //             console.log("value");
    //             // website.form('/shop/add_product', 'POST', {
    //             //     name: name
    //             // });
    //         });
    //     },
    // });

    website.add_template_file('/website_crm_score/static/src/xml/website.score.xml');

    website.score = {};

    website.score.Configurator = openerp.Widget.extend({
    	template: 'website.set.score',
        events: {
            'click button[data-action=save_score]': 'saveScore',
            'hidden.bs.modal': 'destroy',
        },
        init: function() {
            console.log('in init');
        },

        start: function() {
            // The popup doesn't close itself...
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
                        if (!exists && false) { // TODO: create a new score
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
                    }, function () { // TODO: check if this is useful and what it does
                        q.callback({more: false, results: []});
                    });
                },
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

        saveScore: function (event) {
            var data = $('#link').select2('data');
            var obj = this.getMainObject();
            if (!obj) {
                return $.Deferred().reject();
            } else {
                // if (data.create){ // should there be another popup that allows the creation of a score ?
                if (data){
                    var id = data.id;
                    console.log(id);
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
        	console.log('in start');
            new website.score.Configurator(this).appendTo($(document.body));
        });
    });


})();
