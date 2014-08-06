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
            //'keyup input[name=score_name]': 'nameChanged',
            //'keyup input[name=score_value]': 'valueChanged',
            'click button[data-action=save_score]': 'saveScore',
            'hidden.bs.modal': 'destroy',
        },

        init: function() {
            console.log('in init');
        },

        start: function() {
            var last;
            this.$el.modal();
            this.$el.find('#link').select2({
                minimumInputLength: 1,
                placeholder: _t("Crm Score"),
                query: function (q) {
                    if (q.term == last) return;
                    last = q.term;
                    //var VIEWS = new openerp.Model('ir_ui_view');

                    var results = [{"loc":"do"}, {"loc":"request"}, {"loc":"in"}, {"loc":"database"}];
                    var rs = _.map(results, function (r) {
                            return { id: r.loc, text: r.loc, };
                        });
                        
                        q.callback({
                            more: false,
                            results: rs
                        });

                },
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

        saveScore: function (score) {
            var $input = this.$('input[name=score_value]');
            var score = _.isNumber(score) ? score : $input.val();
            console.log(score);
            var obj = this.getMainObject();
            debugger;
            if (!obj) {
                return $.Deferred().reject();
            } else {
                var data = {};
                data.website_score = score
                var model = website.session.model(obj.model);
                model.call('write', [[obj.id], data, website.get_context()]);
            }
        },

        getScore: function () {
            var obj = this.getMainObject();
            var model = website.session.model(obj.model);
            model.call('read', [[obj.id], ['website_score'], website.get_context()]).then(function (data) {
                console.log(data[0].website_score);
            });
        },

        destroy: function () {
            // this.htmlPage.changeKeywords(this.keywordList.keywords());
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
