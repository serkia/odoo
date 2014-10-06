(function() {
    "use strict";

    var website = openerp.website;
    var _t = openerp._t;

    website.EditorBarContent.include({
        new_channel: function() {
            website.prompt({
                id: "editor_new_channel",
                window_title: _t("New Channel"),
                input: "Channel Name",
            }).then(function (channel_name) {
                website.session.model('slide.channel')
                    .call('create', [{'name': channel_name}], { context: website.get_context() })
                    .then(function (channel_id) {
                        document.location = '/slides/' + channel_id;
                    });
            });
        },
    });
})();
