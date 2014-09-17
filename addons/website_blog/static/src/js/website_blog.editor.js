$(document).ready(function() {
    "use strict";

    var website = openerp.website;
    var _t = openerp._t;

    website.EditorBarContent.include({
        new_blog_post: function() {
            website.prompt({
                id: "editor_new_blog",
                window_title: _t("New Blog Post"),
                select: "Select Blog",
                init: function (field) {
                    return website.session.model('blog.blog')
                            .call('name_search', [], { context: website.get_context() });
                },
            }).then(function (cat_id) {
                document.location = '/blogpost/new?blog_id=' + cat_id;
            });
        },
    });

    website.EditorBar.include({
        save : function() {
            var res = this._super();
            var $cover = $('#title.cover');
            if ($cover.length) {
                openerp.jsonRpc("/blogpost/change_background", 'call', {
                    'post_id' : $('#blog_post_name').attr('data-oe-id'),
                    'image' : $cover.css('background-image').replace(/url\(|\)|"|'/g,''),
                });
            }
            return res;
        }
    });

    website.snippet.options.website_blog = website.snippet.Option.extend({
        clear : function(type, value, $li) {
            if (type !== 'click') return;

            this.$target.css({"background-image":'none', 'min-height': $(window).height()});
        },
        change : function(type, value, $li) {
            if (type !== 'click') return;

            var self  = this;
            var $image = this.$target.find('.cover-storage');
            var editor  = new website.editor.MediaDialog(this.BuildingBlock.parent, $image[0]);
            editor.appendTo('body');
            $image.on('saved', self, function (o) {
                var url = $image.attr('src');
                self.$target.css({"background-image": !_.isUndefined(url) ? 'url(' + url + ')' : "", 'min-height': $(window).height()});
            });
        },
    });

})();
