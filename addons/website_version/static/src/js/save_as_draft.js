(function() {
    'use strict';
    var hash = "#advanced-view-editor";
    var _t = openerp._t;
    
    var website=openerp.website;

    website.action= {};
    
    website.EditorBar.include({
        start: function() {
            var self = this;
            $('#master_edit_button').click(function() {
                var m_names = new Array("January", "February", "March", 
                "April", "May", "June", "July", "August", "September", 
                "October", "November", "December");
                var d = new Date();
                var curr_date = d.getDate();
                var curr_month = d.getMonth();
                var curr_year = d.getFullYear();
                
                website.prompt({
                    id: "editor_new_version",
                    window_title: _t("New version"),
                    input: "Version name" ,
                    default :(curr_date + "-" + m_names[curr_month] + "-" + curr_year),
                }).then(function (name) {
                    var context = website.get_context();
                    openerp.jsonRpc( '/website_version/create_snapshot', 'call', { 'name': name }).then(function (result) {
                        $('html').data('snapshot_id', result);
                        self.save();
                        location.reload();
                        alert("You are actually working on "+name+ " version.");
                    }).fail(function(){
                        alert("This name already exists.");
                    });
                });
            
            });
            return this._super();
        },

        edit: function () {
            var self = this;
            var view_id = $('html').attr('data-view-xmlid');
            openerp.jsonRpc( '/website_version/is_master', 'call', { 'view_id': view_id })
                .then(function (result) {
                    if(result){
                        self.$('#master_edit').show();
                    }
                });

            return this._super();
        },

    });

    website.EditorBarContent.include({
        start: function() {
            
            return this._super();
        },

        ab_testing: function() {
            window.location.href = '/web#return_label=Website&action=website_version.action_experiment';
        }
    });

    
})();