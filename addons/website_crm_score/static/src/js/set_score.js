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
            'keyup input[name=score_name]': 'nameChanged',
            'keyup input[name=score_value]': 'valueChanged',
            'click button[data-action=add_score]': 'saveScore',
            'click button[data-action=get_score]': 'getScore',
            'hidden.bs.modal': 'destroy',
        },

        init: function() {
            console.log('in init');
        },

        start: function() {
            this.$el.modal();
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
            var $input = this.$('input[name=page_score]');
            var score = _.isNumber(score) ? score : $input.val();
            // debugger;
            console.log(score);
            var obj = this.getMainObject();
            // debugger;
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
