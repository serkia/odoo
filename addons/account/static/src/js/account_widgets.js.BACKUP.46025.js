/*global _:false */
/*global openerp:false */

openerp.account = function (instance) {
    'use strict';

    openerp.account.quickadd(instance);
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.account = instance.web.account || {};

    // NOTE
    // "implementation classes" must declare a
    // this.childrenWidget = instance.web.account.implementationOfAbstractReconciliationLine
    instance.web.account.abstractReconciliation = instance.web.Widget.extend({
        className: 'oe_reconciliation',
    
        init: function(parent, context) {
            this._super(parent);
            this.max_reconciliations_displayed = 10;
            this.title = context.context.title || _t("Reconciliation"); // TODO : only bank statement ?
            this.formatCurrencies; // Method that formats the currency ; loaded from the server
    
            // Only for statistical purposes
            this.lines_reconciled_with_ctrl_enter = 0; // TODO : only bank statement ?
            this.time_widget_loaded = Date.now();
    
            // Stuff used by the children reconciliationLine
            this.max_move_lines_displayed = 5;
            this.animation_speed = 100; // "Blocking" animations
            this.aestetic_animation_speed = 300; // eye candy
            // We'll need to get the code of an account selected in a many2one (whose value is the id)
            this.map_account_id_code = {};
            this.reconciliation_menu_id = false; // Used to update the needaction badge
        },
    
        start: function() {
            var self = this;
            return $.when(this._super()).then(function(){
                var deferred_promises = [];

                // Create a dict account id -> account code for display facilities
                deferred_promises.push(new instance.web.Model("account.account")
                    .query(['id', 'code'])
                    .all().then(function(data) {
                        _.each(data, function(o) { self.map_account_id_code[o.id] = o.code });
                    })
                );

                // Get the function to format currencies
                deferred_promises.push(new instance.web.Model("res.currency")
                    .call("get_format_currencies_js_function")
                    .then(function(data) {
                        self.formatCurrencies = new Function("amount, currency_id", data);
                    })
                );
                
                // Bind keyboard events TODO : méthode standard ?
                $("body").on("keypress", function (e) {
                    self.keyboardShortcutsHandler(e);
                });
        
                return $.when.apply($, deferred_promises);
            });
        },
    
        keyboardShortcutsHandler: function(e) {},

        displayReconciliation: function() {},
    
        childValidated: function(child) {},
    
        displayDoneMessage: function() {},
    
        updateProgressbar: function() {},
    
        /* reloads the needaction badge */
        doReloadMenuReconciliation: function () {
            var menu = instance.webclient.menu;
            if (!menu || !this.reconciliation_menu_id) {
                return $.when();
            }
            return menu.rpc("/web/menu/load_needaction", {'menu_ids': [this.reconciliation_menu_id]}).done(function(r) {
                menu.on_needaction_loaded(r);
            }).then(function () {
                menu.trigger("need_action_reloaded");
            });
        },

        // adds fields, prefixed with q_, to the move line for qweb rendering
        decorateMoveLine: function(line) {
            /* Seems useless
            line.partial_reconcile = false;
            line.propose_partial_reconcile = false; */
            line.q_due_date = (line.date_maturity === false ? line.date : line.date_maturity);
            line.q_amount = (line.debit !== 0 ? "- "+line.q_debit : "") + (line.credit !== 0 ? line.q_credit : "");
            line.q_label = line.name;
            line.debit_str = this.formatCurrencies(line.debit);
            line.credit_str = this.formatCurrencies(line.credit);
            line.q_popover = QWeb.render("reconciliation_move_line_details", {line: line});
            if (line.has_no_partner)
                line.q_label = line.partner_name + ': ' + line.q_label;
        
            // WARNING : pretty much of a ugly hack
            // The value of account_move.ref is either the move's communication or it's name without the slashes
            if (line.ref && line.ref !== line.name.replace(/\//g,''))
                line.q_label += " : " + line.ref;
        },
    });
    
    instance.web.account.abstractReconciliationLine = instance.web.Widget.extend({
        className: 'oe_reconciliation_line',
    
        init: function(parent, context) {
            this._super(parent);

            this.decorateMoveLine = this.getParent().decorateMoveLine;
            this.formatCurrencies = this.getParent().formatCurrencies;
            if (context.initial_data_provided) {
                // Process data
                _(context.reconciliation_proposition).each(this.decorateMoveLine.bind(this));
                this.set("mv_lines_selected", context.reconciliation_proposition);
                this.partner_id = context.line.partner_id;
            } else {
                this.set("mv_lines_selected", []);
            }

            this.context = context;
            this.max_move_lines_displayed = this.getParent().max_move_lines_displayed;
            this.animation_speed = this.getParent().animation_speed;
            this.aestetic_animation_speed = this.getParent().aestetic_animation_speed;
            this.map_account_id_code = this.getParent().map_account_id_code;
            this.is_valid = true;
            this.is_consistent = true; // Used to prevent bad server requests
            this.filter = "";
        
            this.set("mode", undefined);
            this.on("change:mode", this, this.modeChanged);
            this.set("balance", undefined); // Debit is +, credit is -
            this.on("change:balance", this, this.balanceChanged);
            this.set("pager_index", 0);
            this.on("change:pager_index", this, this.pagerChanged);
            // NB : mv_lines represent the counterpart that will be created to reconcile existing move lines, so debit and credit are inverted
            this.set("mv_lines", []);
            this.on("change:mv_lines", this, this.mvLinesChanged);
            this.on("change:mv_lines_selected", this, this.mvLinesSelectedChanged);

            //all lines associated to current reconciliation
            this.propositions_lines = undefined;
        },
    
        start: function() {
            var self = this;
            return self._super().then(function() {

                // Event handlers are not defined via the shortcut in order
                // not to be overwritten by implementation widgets
                self.$el.on("click", ".mv_line", self.moveLineClickHandler.bind(self));
                self.$el.on("click", ".pager_control_left:not(.disabled)", self.pagerControlLeftHandler.bind(self));
                self.$el.on("click", ".pager_control_right:not(.disabled)", self.pagerControlRightHandler.bind(self));
                self.$el.on("keyup", ".filter", self.filterHandler.bind(self));
                self.$el.on("click", ".line_info_button", function(e){e.stopPropagation()});

                // no animation while loading
                self.animation_speed = 0;
                self.aestetic_animation_speed = 0;
    
                self.is_consistent = false;
                if (self.context.animate_entrance) {
                    self.$el.fadeOut(0);
                    self.$el.slideUp(0);
                }
                return $.when(self.loadData()).then(function(){
                    return $.when(self.render()).then(function(){
                        self.is_consistent = true;
                        // Make an entrance
                        self.animation_speed = self.getParent().animation_speed;
                        self.aestetic_animation_speed = self.getParent().aestetic_animation_speed;
                        if (self.context.animate_entrance) {
                            return self.$el.stop(true, true).fadeIn({ duration: self.aestetic_animation_speed, queue: false }).css('display', 'none').slideDown(self.aestetic_animation_speed); 
                        }
                    });
                });
            });
        },

        loadData: function() {},

        render: function() {},
    
        /** Utils */
    
        bindPopoverTo: function(el) {
            var self = this;
            $(el).addClass("bootstrap_popover");
            el.popover({
                'placement': 'left',
                'container': self.el,
                'html': true,
                'trigger': 'hover',
                'animation': false,
                'toggle': 'popover'
            });
        },
    
        /** Matching */
    
        moveLineClickHandler: function(e) {
            var self = this;
            if (e.currentTarget.dataset.selected === "true") self.deselectMoveLine(e.currentTarget);
            else self.selectMoveLine(e.currentTarget);
        },

        selectMoveLine: function(mv_line) {
            var self = this;
            var line_id = mv_line.dataset.lineid;
            var line = _.find(self.get("mv_lines"), function(o){ return o.id == line_id});
            $(mv_line).attr('data-selected','true');
            self.set("mv_lines_selected", self.get("mv_lines_selected").concat(line));
            this.set("mv_lines", _.reject(this.get("mv_lines"), function(o){return o.id == line_id}));
        },

        deselectMoveLine: function(mv_line) {
            var self = this;
            var line_id = mv_line.dataset.lineid;
            var line = _.find(self.get("mv_lines_selected"), function(o){ return o.id == line_id});
            $(mv_line).attr('data-selected','false');
            self.set("mv_lines_selected",_.filter(self.get("mv_lines_selected"), function(o) { return o.id != line_id }));
            this.set("mv_lines", this.get("mv_lines").concat(line));
            self.set("mode", "match");
        },
    
        /** Matches pagination */
    
        pagerControlLeftHandler: function() {
            this.set("pager_index", this.get("pager_index")-1 );
        },
    
        pagerControlRightHandler: function() {
            this.set("pager_index", this.get("pager_index")+1 );
        },
    
        filterHandler: function() {
            var self = this;
            self.set("pager_index", 0);
            self.filter = self.$(".filter").val();
            self.filterMoveLines();
        },
    
    
        /** Views updating */
    
        updateAccountingViewMatchedLines: function() {
            var self = this;
            $.each(self.$(".tbody_matched_lines .bootstrap_popover"), function(){ $(this).popover('destroy') });
            self.$(".tbody_matched_lines").empty();
    
            _(self.get("mv_lines_selected")).each(function(line){
                var $line = $(QWeb.render("reconciliation_move_line", {line: line, selected: true}));
                self.bindPopoverTo($line.find(".line_info_button"));
                if (line.propose_partial_reconcile) self.bindPopoverTo($line.find(".do_partial_reconcile_button"));
                if (line.partial_reconcile) self.bindPopoverTo($line.find(".undo_partial_reconcile_button"));
                self.$(".tbody_matched_lines").append($line);
            });
        },
    
        updateMatchView: function() {
            var self = this;
            var table = self.$(".match table");
            var nothing_displayed = true;
    
            // Display move lines
            $.each(self.$(".match table .bootstrap_popover"), function(){ $(this).popover('destroy') });
            table.empty();
            var slice_start = self.get("pager_index") * self.max_move_lines_displayed;
            var slice_end = (self.get("pager_index")+1) * self.max_move_lines_displayed;

            var visible = 0;
            _(self.get("mv_lines")).each(function(line){
                if (visible >= slice_start && visible < slice_end) {
                    var $line = $(QWeb.render("reconciliation_move_line", {line: line, selected: false}));
                    self.bindPopoverTo($line.find(".line_info_button"));
                    table.append($line);
                    nothing_displayed = false;
                }
                visible = visible + 1;
            });
            if (nothing_displayed && this.filter !== "")
                table.append(QWeb.render("filter_no_match", {filter_str: self.filter}));
        },
    
        updatePagerControls: function() {
            var self = this;
            if (self.get("pager_index") === 0)
                self.$(".pager_control_left").addClass("disabled");
            else
                self.$(".pager_control_left").removeClass("disabled");
            if (self.get('mv_lines').length <= ((self.get("pager_index")+1) * self.max_move_lines_displayed))
                self.$(".pager_control_right").addClass("disabled");
            else
                self.$(".pager_control_right").removeClass("disabled");
        },
    
    
        /** Properties changed */
    
        // Updates the validation button and the "open balance" line
        balanceChanged: function() {},
    
        modeChanged: function() {},
    
        pagerChanged: function() {
            this.filterMoveLines();
        },
    
        mvLinesChanged: function() {
            var self = this;
    
            // If there is no match to display, disable match view and pass in mode inactive
            if (self.get("mv_lines").length === 0 && self.filter === "") {
                self.$el.addClass("no_match");
                if (self.get("mode") === "match") {
                    self.set("mode", "inactive");
                }
            } else {
                self.$el.removeClass("no_match");
            }
    
            self.updateMatchView();
            self.updatePagerControls();
        },
    
        mvLinesSelectedChanged: function(elt, val) {
            this.updateAccountingViewMatchedLines();
            this.updateBalance();
        },
    
    
        /** Model */
    
        updateBalance: function() {},
    
        loadReconciliationProposition: function() {},

        filterMoveLines: function() {},
    
        // Returns an object that can be passed to process_reconciliation()
        prepareSelectedMoveLineForPersisting: function(line) {
            return {
                name: line.name,
                debit: line.debit,
                credit: line.credit,
                counterpart_move_line_id: line.id,
            };
        },
    
        // Persist data, notify parent view and terminate widget
        persistAndDestroy: function(speed) {
            var self = this;
            speed = (isNaN(speed) ? self.animation_speed : speed);
            if (! self.is_consistent) return;
            
            // Sliding animation
            var height = self.$el.outerHeight();
            var container = $("<div />");
            container.css("height", height)
                     .css("marginTop", self.$el.css("marginTop"))
                     .css("marginBottom", self.$el.css("marginBottom"));
            self.$el.wrap(container);
            var deferred_animation = self.$el.parent().slideUp(speed*height/150);
    
            // RPC
            return $.when(self.makeRPCForPersisting())
                .then(function () {
                    $.each(self.$(".bootstrap_popover"), function(){ $(this).popover('destroy') });
                    return $.when(deferred_animation).then(function(){
                        self.$el.parent().remove();
                        var parent = self.getParent();
                        return $.when(self.destroy()).then(function() {
                            parent.childValidated(self);
                        });
                    });
                }, function(){
                    self.$el.parent().slideDown(speed*height/150, function(){
                        self.$el.unwrap();
                    });
                });
        },

        makeRPCForPersisting: function() {},
    });

    instance.web.client_actions.add('bank_statement_reconciliation_view', 'instance.web.account.bankStatementReconciliation');
    instance.web.account.bankStatementReconciliation = instance.web.account.abstractReconciliation.extend({
    
        init: function(parent, context) {
            this._super(parent, context);

            this.childrenWidget = instance.web.account.bankStatementReconciliationLine;

            this.statement_id = context.context.statement_id;
            this.lines = []; // list of reconciliations identifiers to instantiate children widgets
            this.last_displayed_reconciliation_index = undefined; // Flow control
            this.reconciled_lines = 0; // idem
            this.already_reconciled_lines = 0; // Number of lines of the statement which were already reconciled
            this.presets = {};
            this.model_bank_statement = new instance.web.Model("account.bank.statement");
            this.model_bank_statement_line = new instance.web.Model("account.bank.statement.line");
            // The same move line cannot be selected for multiple resolutions
            this.excluded_move_lines_ids = [];
            this.map_tax_id_amount = {};
            // Description of the fields to initialize in the "create new line" form
            // NB : for presets to work correctly, a field id must be the same string as a preset field
            this.create_form_fields = {
                account_id: {
                    id: "account_id",
                    index: 0,
                    corresponding_property: "account_id", // a account.move field name
                    label: _t("Account"),
                    required: true,
                    tabindex: 10,
                    constructor: instance.web.form.FieldMany2One,
                    field_properties: {
                        relation: "account.account",
                        string: _t("Account"),
                        type: "many2one",
                        domain: [['type','not in',['view', 'closed', 'consolidation']]],
                    },
                },
                label: {
                    id: "label",
                    index: 1,
                    corresponding_property: "label",
                    label: _t("Label"),
                    required: true,
                    tabindex: 11,
                    constructor: instance.web.form.FieldChar,
                    field_properties: {
                        string: _t("Label"),
                        type: "char",
                    },
                },
                tax_id: {
                    id: "tax_id",
                    index: 2,
                    corresponding_property: "tax_id",
                    label: _t("Tax"),
                    required: false,
                    tabindex: 12,
                    constructor: instance.web.form.FieldMany2One,
                    field_properties: {
                        relation: "account.tax",
                        string: _t("Tax"),
                        type: "many2one",
                        domain: [['type_tax_use','in',['purchase', 'all']], ['parent_id', '=', false]],
                    },
                },
                amount: {
                    id: "amount",
                    index: 3,
                    corresponding_property: "amount",
                    label: _t("Amount"),
                    required: true,
                    tabindex: 13,
                    constructor: instance.web.form.FieldFloat,
                    field_properties: {
                        string: _t("Amount"),
                        type: "float",
                    },
                },
                analytic_account_id: {
                    id: "analytic_account_id",
                    index: 4,
                    corresponding_property: "analytic_account_id",
                    label: _t("Analytic Acc."),
                    required: false,
                    tabindex: 14,
                    group:"analytic.group_analytic_accounting",
                    constructor: instance.web.form.FieldMany2One,
                    field_properties: {
                        relation: "account.analytic.account",
                        string: _t("Analytic Acc."),
                        type: "many2one",
                    },
                },
            };
        },
    
        start: function() {
            var self = this;
            return $.when(this._super()).then(function(){
                self.$el.addClass("oe_bank_statement_reconciliation");

                // Retreive statement infos and reconciliation data from the model
                var lines_filter = [['journal_entry_id', '=', false], ['account_id', '=', false]];
                var deferred_promises = [];
        
                if (self.statement_id) {
                    lines_filter.push(['statement_id', '=', self.statement_id]);
                    deferred_promises.push(self.model_bank_statement
                        .query(["name"])
                        .filter([['id', '=', self.statement_id]])
                        .first()
                        .then(function(title){
                            self.title = title.name;
                        })
                    );
                    deferred_promises.push(self.model_bank_statement
                        .call("number_of_lines_reconciled", [self.statement_id])
                        .then(function(num) {
                            self.already_reconciled_lines = num;
                        })
                    );
                }

                deferred_promises.push(new instance.web.Model("account.statement.operation.template")
                    .query(['id','name','account_id','label','amount_type','amount','tax_id','analytic_account_id'])
                    .all().then(function (data) {
                        _(data).each(function(preset){
                            self.presets[preset.id] = preset;
                        });
                    })
                );

                // Create a dict tax id -> amount
                deferred_promises.push(new instance.web.Model("account.tax")
                    .query(['id', 'amount'])
                    .all().then(function(data) {
                        _.each(data, function(o) { self.map_tax_id_amount[o.id] = o.amount });
                    })
                );

                deferred_promises.push(self.model_bank_statement_line
                    .query(['id'])
                    .filter(lines_filter)
                    .order_by('id')
                    .all().then(function (data) {
                        self.lines = _(data).map(function(o){ return o.id });
                    })
                );
        
                // When queries are done, render template and reconciliation lines
                return $.when.apply($, deferred_promises).then(function(){
        
                    // If there is no statement line to reconcile, stop here
                    if (self.lines.length === 0) {
                        self.$el.prepend(QWeb.render("bank_statement_nothing_to_reconcile"));
                        return;
                    }
            
                    new instance.web.Model("ir.model.data")
                        .call("xmlid_to_res_id", ["account.menu_bank_reconcile_bank_statements"])
                        .then(function(data) {
                            self.reconciliation_menu_id = data;
                            self.doReloadMenuReconciliation();
                        });
        
                    // Render and display
                    self.$el.prepend(QWeb.render("bank_statement_reconciliation", {title: self.title, total_lines: self.already_reconciled_lines+self.lines.length}));
                    self.updateProgressbar();
                    var reconciliations_to_show = self.lines.slice(0, self.max_reconciliations_displayed);
                    self.last_displayed_reconciliation_index = reconciliations_to_show.length;
                    self.$(".reconciliation_lines_container").css("opacity", 0);
        
                    // Display the reconciliations
                    return self.model_bank_statement_line
                        .call("get_data_for_reconciliations", [reconciliations_to_show])
                        .then(function (data) {
                            var child_promises = [];
                            _.each(reconciliations_to_show, function(st_line_id){
                                var datum = data.shift();
                                child_promises.push(self.displayReconciliation(st_line_id, 'inactive', false, true, datum.st_line, datum.reconciliation_proposition));
                            });
                            $.when.apply($, child_promises).then(function(){
                                self.getChildren()[0].set("mode", "match");
                                self.$(".reconciliation_lines_container").animate({opacity: 1}, self.aestetic_animation_speed);
                            });
                        });
                });
            });
        },

        updateProgressbar: function() {
            var self = this;
            var done = self.already_reconciled_lines + self.reconciled_lines;
            var total = self.already_reconciled_lines + self.lines.length;
            var prog_bar = self.$(".progress .progress-bar");
            prog_bar.attr("aria-valuenow", done);
            prog_bar.css("width", (done/total*100)+"%");
            self.$(".progress .progress-text .valuenow").text(done);
        },
    
        keyboardShortcutsHandler: function(e) {
            this._super(e);
            var self = this;
            if ((e.which === 13 || e.which === 10) && (e.ctrlKey || e.metaKey)) {
                $.each(self.getChildren(), function(i, o){
                    if (o.is_valid && o.persistAndDestroy()) {
                        self.lines_reconciled_with_ctrl_enter++;
                    }
                });
            }
        },

        displayReconciliation: function(line_id, mode, animate_entrance, initial_data_provided, line, reconciliation_proposition) {
            var self = this;
            animate_entrance = (animate_entrance === undefined ? true : animate_entrance);
            initial_data_provided = (initial_data_provided === undefined ? false : initial_data_provided);
        
            var context = {
                line_id: line_id,
                mode: mode,
                animate_entrance: animate_entrance,
                initial_data_provided: initial_data_provided,
                line: initial_data_provided ? line : undefined,
                reconciliation_proposition: initial_data_provided ? reconciliation_proposition : undefined,
            };
            var widget = new self.childrenWidget(self, context);
            return widget.appendTo(self.$(".reconciliation_lines_container"));
        },

        excludeMoveLines: function(line_ids) {
            var self = this;
            _.each(line_ids, function(line_id){
                line_id = parseInt(line_id);
                if (self.excluded_move_lines_ids.indexOf(line_id) === -1) {
                    self.excluded_move_lines_ids.push(line_id);
                }
            });
            //update all children view
            _.each(self.getChildren(), function(child){
                child.filterMoveLines();
            });
        },

        unexcludeMoveLines: function(line_ids) {
            var self = this;
            var index = -1;
            _.each(line_ids, function(line_id){
                line_id = parseInt(line_id);
                index = self.excluded_move_lines_ids.indexOf(line_id);
                if (index > -1) {
                    self.excluded_move_lines_ids.splice(index,1);
                }
            });
            //update all children view
            _.each(self.getChildren(), function(child){
                child.filterMoveLines();
            });
        },

        childValidated: function(child) {
            var self = this;
            
            self.reconciled_lines++;
            self.updateProgressbar();
            self.doReloadMenuReconciliation();
            
            // Display new line if there are left
            if (self.last_displayed_reconciliation_index < self.lines.length) {
                self.displayReconciliation(self.lines[self.last_displayed_reconciliation_index++], 'inactive');
            }
            // Congratulate the user if the work is done
            if (self.reconciled_lines === self.lines.length) {
                self.displayDoneMessage();
            }
        
            // Put the first line in match mode
            if (self.reconciled_lines !== self.lines.length) {
                var first_child = self.getChildren()[0];
                if (first_child.get("mode") === "inactive") {
                    first_child.set("mode", "match");
                }
            }
        },
    
        displayDoneMessage: function() {
            var self = this;
    
            var sec_taken = Math.round((Date.now()-self.time_widget_loaded)/1000);
            var sec_per_item = Math.round(sec_taken/self.reconciled_lines);
            var achievements = [];
    
            var time_taken;
            if (sec_taken/60 >= 1) time_taken = Math.floor(sec_taken/60) +"' "+ sec_taken%60 +"''";
            else time_taken = sec_taken%60 +" seconds";
    
            var title;
            if (sec_per_item < 5) title = _t("Whew, that was fast !") + " <i class='fa fa-trophy congrats_icon'></i>";
            else title = _t("Congrats, you're all done !") + " <i class='fa fa-thumbs-o-up congrats_icon'></i>";
    
            if (self.lines_reconciled_with_ctrl_enter === self.reconciled_lines)
                achievements.push({
                    title: _t("Efficiency at its finest"),
                    desc: _t("Only use the ctrl-enter shortcut to validate reconciliations."),
                    icon: "fa-keyboard-o"}
                );
    
            if (sec_per_item < 5)
                achievements.push({
                    title: _t("Fast reconciler"),
                    desc: _t("Take on average less than 5 seconds to reconcile a transaction."),
                    icon: "fa-bolt"}
                );
    
            // Render it
            self.$(".protip").hide();
            self.$(".oe_form_sheet").append(QWeb.render("bank_statement_reconciliation_done_message", {
                title: title,
                time_taken: time_taken,
                sec_per_item: sec_per_item,
                transactions_done: self.reconciled_lines,
                done_with_ctrl_enter: self.lines_reconciled_with_ctrl_enter,
                achievements: achievements,
                has_statement_id: self.statement_id !== undefined,
            }));
    
            // Animate it
            var container = $("<div style='overflow: hidden;' />");
            self.$(".done_message").wrap(container).css("opacity", 0).css("position", "relative").css("left", "-50%");
            self.$(".done_message").animate({opacity: 1, left: 0}, self.aestetic_animation_speed*2, "easeOutCubic");
            self.$(".done_message").animate({opacity: 1}, self.aestetic_animation_speed*3, "easeOutCubic");
    
            // Make it interactive
            self.$(".achievement").popover({'placement': 'top', 'container': self.el, 'trigger': 'hover'});
            
            self.$(".button_back_to_statement").click(function() {
                self.do_action({
                    type: 'ir.actions.client',
                    tag: 'history_back',
                });
            });

            if (self.$(".button_close_statement").length !== 0) {
                self.$(".button_close_statement").hide();
                self.model_bank_statement
                    .query(["balance_end_real", "balance_end"])
                    .filter([['id', '=', self.statement_id]])
                    .first()
                    .then(function(data){
                        if (data.balance_end_real === data.balance_end) {
                            self.$(".button_close_statement").show();
                            self.$(".button_close_statement").click(function() {
                                self.$(".button_close_statement").attr("disabled", "disabled");
                                self.model_bank_statement
                                    .call("button_confirm_bank", [[self.statement_id]])
                                    .then(function () {
                                        self.do_action({
                                            type: 'ir.actions.client',
                                            tag: 'history_back',
                                        });
                                    }, function() {
                                        self.$(".button_close_statement").removeAttr("disabled");
                                    });
                            });
                        }
                    });
            }
        },
    });
    
    instance.web.account.bankStatementReconciliationLine = instance.web.account.abstractReconciliationLine.extend({

        events: {
            "click .partner_name": "partnerNameClickHandler",
            "click .button_ok": "persistAndDestroy",
            "click .initial_line": "initialLineClickHandler",
            "click .line_open_balance": "lineOpenBalanceClickHandler",
            "click .add_line": "addLineBeingEdited",
            "click .preset": "presetClickHandler",
            "click .do_partial_reconcile_button": "doPartialReconcileButtonClickHandler",
            "click .undo_partial_reconcile_button": "undoPartialReconcileButtonClickHandler",
        },
    
        init: function(parent, context) {
            this._super(parent, context);
    
            if (context.initial_data_provided) {
                // Process data
                this.st_line = context.line;
                this.decorateStatementLine(this.st_line);
    
                // Exclude selected move lines
                var selected_line_ids = _(context.reconciliation_proposition).map(function(o){ return o.id });
                this.getParent().excludeMoveLines(selected_line_ids);
            } else {
                this.st_line = undefined;
                this.partner_id = undefined;
            }
    
            this.st_line_id = context.line_id;
            this.model_bank_statement_line = new instance.web.Model("account.bank.statement.line");
            this.model_res_users = new instance.web.Model("res.users");
            this.model_tax = new instance.web.Model("account.tax");
            this.map_tax_id_amount = this.getParent().map_tax_id_amount;
            this.presets = this.getParent().presets;
    
            this.set("lines_created", []);
            this.set("line_created_being_edited", [{'id': 0}]);
            this.on("change:lines_created", this, this.createdLinesChanged);
            this.on("change:line_created_being_edited", this, this.createdLinesChanged);
        },
    
        start: function() {
            this.$el.addClass("oe_bank_statement_reconciliation_line");
            return this._super();
        },

        loadData: function() {
            var self = this;
            var deferred_fetch_data = new $.Deferred();
            if (! self.context.initial_data_provided) {
                // Load statement line
                self.model_bank_statement_line
                    .call("get_statement_line_for_reconciliation", [self.st_line_id])
                    .then(function (data) {
                        self.st_line = data;
                        self.decorateStatementLine(self.st_line);
                        self.partner_id = data.partner_id;
                        $.when(self.loadReconciliationProposition()).then(function(){
                            deferred_fetch_data.resolve();
                        });
                    });
            } else {
                deferred_fetch_data.resolve();
            }
            return $.when(deferred_fetch_data).then(function(){
                //load all lines that can be usefull for counterparts
                var deferred_total_move_lines_num = self.model_bank_statement_line
                    .call("get_move_lines_counterparts_id", [self.st_line.id, []])
                    .then(function(lines){
                        _(lines).each(self.decorateMoveLine.bind(self));
                        self.propositions_lines = lines;
                    });
                return deferred_total_move_lines_num;
            });
        },

        render: function() {
            var self = this;
            var presets_array = [];
            for (var id in self.presets)
                if (self.presets.hasOwnProperty(id))
                    presets_array.push(self.presets[id]);
            self.$el.prepend(QWeb.render("bank_statement_reconciliation_line", {
                line: self.st_line,
                mode: self.context.mode,
                presets: presets_array
            }));
            
            // Stuff that require the template to be rendered
            self.$(".match").slideUp(0);
            self.$(".create").slideUp(0);
            if (self.st_line.no_match) self.$el.addClass("no_match");
            if (self.context.mode !== "match") self.filterMoveLines();
            self.bindPopoverTo(self.$(".line_info_button"));
            self.createFormWidgets();
            // Special case hack : no identified partner
            if (self.st_line.has_no_partner) {
                self.$el.css("opacity", "0");
                self.updateBalance();
                self.$(".change_partner_container").show(0);
                self.change_partner_field.$el.find("input").attr("placeholder", _t("Select Partner"));
                self.$(".match").slideUp(0);
                self.$el.addClass("no_partner");
                self.set("mode", self.context.mode);
                self.animation_speed = self.getParent().animation_speed;
                self.aestetic_animation_speed = self.getParent().aestetic_animation_speed;
                self.$el.animate({opacity: 1}, self.aestetic_animation_speed);
                return;
            }
            
            // TODO : the .on handler's returned deferred is lost
            return $.when(self.set("mode", self.context.mode)).then(function(){
                // Make sure the display is OK
                self.balanceChanged();
                self.createdLinesChanged();
                self.updateAccountingViewMatchedLines();
            });
        },
    
        restart: function(mode) {
            var self = this;
            mode = (mode === undefined ? 'inactive' : mode);
            self.$el.css("height", self.$el.outerHeight());
            // Destroy everything
            _.each(self.getChildren(), function(o){ o.destroy() });
            self.is_consistent = false;
            return $.when(self.$el.animate({opacity: 0}, self.animation_speed)).then(function() {
                self.getParent().unexcludeMoveLines(_.map(self.get("mv_lines_selected"), function(o){ return o.id }));
                $.each(self.$(".bootstrap_popover"), function(){ $(this).popover('destroy') });
                self.$el.empty();
                self.$el.removeClass("no_partner");
                self.context.mode = mode;
                self.context.initial_data_provided = false;
                self.is_valid = true;
                self.is_consistent = true;
                self.filter = "";
                self.propositions_lines = [];
                self.set("balance", undefined, {silent: true});
                self.set("mode", undefined, {silent: true});
                self.set("pager_index", 0, {silent: true});
                self.set("mv_lines", [], {silent: true});
                self.set("mv_lines_selected", [], {silent: true});
                self.set("lines_created", [], {silent: true});
                self.set("line_created_being_edited", [{'id': 0}], {silent: true});
                // Rebirth
                return $.when(self.start()).then(function() {
                    self.$el.css("height", "auto");
                    self.is_consistent = true;
                    self.$el.animate({opacity: 1}, self.animation_speed);
                });
            });
        },
    
        /* create form widgets, append them to the dom and bind their events handlers */
        createFormWidgets: function() {
            var self = this;
            var create_form_fields = self.getParent().create_form_fields;
            var create_form_fields_arr = [];
            for (var key in create_form_fields)
                if (create_form_fields.hasOwnProperty(key))
                    create_form_fields_arr.push(create_form_fields[key]);
            create_form_fields_arr.sort(function(a, b){ return b.index - a.index });
    
            // field_manager
            var dataset = new instance.web.DataSet(this, "account.account", self.context);
            dataset.ids = [];
            dataset.arch = {
                attrs: { string: "Stéphanie de Monaco", version: "7.0", class: "oe_form_container" },
                children: [],
                tag: "form"
            };
    
            var field_manager = new instance.web.FormView (
                this, dataset, false, {
                    initial_mode: 'edit',
                    disable_autofocus: false,
                    $buttons: $(),
                    $pager: $()
            });
    
            field_manager.load_form(dataset);
    
            // fields default properties
            var Default_field = function() {
                this.context = {};
                this.domain = [];
                this.help = "";
                this.readonly = false;
                this.required = true;
                this.selectable = true;
                this.states = {};
                this.views = {};
            };
            var Default_node = function(field_name) {
                this.tag = "field";
                this.children = [];
                this.required = true;
                this.attrs = {
                    invisible: "False",
                    modifiers: '{"required":true}',
                    name: field_name,
                    nolabel: "True",
                };
            };
    
            // Append fields to the field_manager
            field_manager.fields_view.fields = {};
            for (var i=0; i<create_form_fields_arr.length; i++) {
                field_manager.fields_view.fields[create_form_fields_arr[i].id] = _.extend(new Default_field(), create_form_fields_arr[i].field_properties);
            }
            field_manager.fields_view.fields["change_partner"] = _.extend(new Default_field(), {
                relation: "res.partner",
                string: _t("Partner"),
                type: "many2one",
                domain: [['parent_id','=',false], '|', ['customer','=',true], ['supplier','=',true]],
            });
    
            // Returns a function that serves as a xhr response handler
            var hideGroupResponseClosureFactory = function(field_widget, $container, obj_key){
                return function(has_group){
                    if (has_group) $container.show();
                    else {
                        field_widget.destroy();
                        $container.remove();
                        delete self[obj_key];
                    }
                };
            };
    
            // generate the create "form"
            self.create_form = [];
            for (var i=0; i<create_form_fields_arr.length; i++) {
                var field_data = create_form_fields_arr[i];
    
                // create widgets
                var node = new Default_node(field_data.id);
                if (! field_data.required) node.attrs.modifiers = "";
                var field = new field_data.constructor(field_manager, node);
                self[field_data.id+"_field"] = field;
                self.create_form.push(field);
    
                // on update : change the last created line
                field.corresponding_property = field_data.corresponding_property;
                field.on("change:value", self, self.formCreateInputChanged);
    
                // append to DOM
                var $field_container = $(QWeb.render("form_create_field", {id: field_data.id, label: field_data.label}));
                field.appendTo($field_container.find("td"));
                self.$(".create_form").prepend($field_container);
    
                // now that widget's dom has been created (appendTo does that), bind events and adds tabindex
                if (field_data.field_properties.type != "many2one") {
                    // Triggers change:value TODO : moche bind ?
                    field.$el.find("input").keyup(function(e, field){ field.commit_value(); }.bind(null, null, field));
                }
                field.$el.find("input").attr("tabindex", field_data.tabindex);
    
                // Hide the field if group not OK
                if (field_data.group !== undefined) {
                    var target = $field_container;
                    target.hide();
                    self.model_res_users
                        .call("has_group", [field_data.group])
                        .then(hideGroupResponseClosureFactory(field, target, (field_data.id+"_field")));
                }
            }
    
            // generate the change partner "form"
            var change_partner_node = new Default_node("change_partner"); change_partner_node.attrs.modifiers = "";
            self.change_partner_field = new instance.web.form.FieldMany2One(field_manager, change_partner_node);
            self.change_partner_field.appendTo(self.$(".change_partner_container"));
            self.change_partner_field.on("change:value", self.change_partner_field, function() {
                self.changePartner(this.get_value());
            });
    
            field_manager.do_show();
        },
    
        /** Utils */
    
        /* TODO : if t-call for attr, all in qweb */
        decorateStatementLine: function(line){
            line.q_popover = QWeb.render("bank_statement_reconciliation_statement_line_details", {line: line});
        },
    
        islineCreatedBeingEditedValid: function() {
            var line = this.get("line_created_being_edited")[0];
            return line.amount // must be defined and not 0
                && line.account_id // must be defined (and will never be 0)
                && line.label; // must be defined and not empty
        },
    
        /* returns the created lines, plus the ones being edited if valid */
        getCreatedLines: function() {
            var self = this;
            var created_lines = self.get("lines_created").slice();
            if (self.islineCreatedBeingEditedValid())
                return created_lines.concat(self.get("line_created_being_edited"));
            else
                return created_lines;
        },
    
        /** Matching */
    
        selectMoveLine: function(mv_line) {
            this._super(mv_line);
            var line_id = mv_line.dataset.lineid;
            this.getParent().excludeMoveLines([line_id]);
        },

        deselectMoveLine: function(mv_line) {
            this._super(mv_line);
            var line_id = mv_line.dataset.lineid;
            var line = _.find(this.get("mv_lines"), function(o) { return o.id == line_id });
            if (line.partial_reconcile) {
                this.unpartialReconcileLine(line);
                line.propose_partial_reconcile = false;
                this.updateMatchView();
            }
            this.getParent().unexcludeMoveLines([line_id]);
        },
    
        /** Creating */
    
        initializeCreateForm: function() {
            var self = this;
    
            _.each(self.create_form, function(field) {
                field.set("value", false);
            });
            self.amount_field.set("value", -1*self.get("balance"));
            self.account_id_field.focus();
        },
    
        addLineBeingEdited: function() {
            var self = this;
            if (! self.islineCreatedBeingEditedValid()) return;
            
            self.set("lines_created", self.get("lines_created").concat(self.get("line_created_being_edited")));
            // Add empty created line
            var new_id = self.get("line_created_being_edited")[0].id + 1;
            self.set("line_created_being_edited", [{'id': new_id}]);
    
            self.initializeCreateForm();
        },
    
        removeLine: function($line) {
            var self = this;
            var line_id = $line.data("lineid");
    
            // if deleting the created line that is being edited, validate it before
            if (line_id === self.get("line_created_being_edited")[0].id) {
                self.addLineBeingEdited();
            }
            self.set("lines_created", _.filter(self.get("lines_created"), function(o) { return o.id != line_id }));
            self.amount_field.set("value", -1*self.get("balance"));
        },
    
        presetClickHandler: function(e) {
            var self = this;
            self.initializeCreateForm();
            var preset = self.presets[e.currentTarget.dataset.presetid];
            for (var key in preset) {
                if (! preset.hasOwnProperty(key) || key === "amount") continue;
                if (self.hasOwnProperty(key+"_field"))
                    self[key+"_field"].set_value(preset[key]);
            }
            var sign = self.amount_field.get_value() < 0 ? -1 : 1;
            if (preset.amount && self.amount_field) {
                if (preset.amount_type === "fixed")
                    self.amount_field.set_value(sign * preset.amount);
                else if (preset.amount_type === "percentage_of_total")
                    self.amount_field.set_value(sign * self.st_line.amount * preset.amount / 100);
                else if (preset.amount_type === "percentage_of_balance") {
                    self.amount_field.set_value(0);
                    self.updateBalance();
                    self.amount_field.set_value(sign * Math.abs(self.get("balance")) * preset.amount / 100);
                }
            }
        },
    
    
        /** Display */
    
        initialLineClickHandler: function() {
            var self = this;
            if (self.get("mode") === "match") {
                self.set("mode", "inactive");
            } else {
                self.set("mode", "match");
            }
        },
    
        lineOpenBalanceClickHandler: function() {
            var self = this;
            if (self.get("mode") === "create") {
                self.addLineBeingEdited();
                self.set("mode", "match");
            } else {
                self.set("mode", "create");
            }
        },
    
        partnerNameClickHandler: function() {
            var self = this;
            self.$(".partner_name").hide();
            self.change_partner_field.$el.find("input").attr("placeholder", self.st_line.partner_name);
            self.$(".change_partner_container").show();
        },
    
    
        /** Views updating */
    
        updateAccountingViewCreatedLines: function() {
            var self = this;
            $.each(self.$(".tbody_created_lines .bootstrap_popover"), function(){ $(this).popover('destroy') });
            self.$(".tbody_created_lines").empty();
    
            _(self.getCreatedLines()).each(function(line){
                var $line = $(QWeb.render("bank_statement_reconciliation_created_line", {line: line}));
                $line.find(".line_remove_button").click(function(){ self.removeLine($(this).closest(".created_line")) });
                self.$(".tbody_created_lines").append($line);
                if (line.no_remove_action) {
                    // Then the previous line's remove button deletes this line too
                    $line.hover(function(){ $(this).prev().addClass("active") },function(){ $(this).prev().removeClass("active") });
                }
            });
        },
    
    
        /** Properties changed */
    
        // Updates the validation button and the "open balance" line
        balanceChanged: function() {
            var self = this;
            var balance = self.get("balance");
            self.$(".tbody_open_balance").empty();
            // Special case hack : no identified partner
            if (self.st_line.has_no_partner) {
                if (Math.abs(balance).toFixed(3) === "0.000") {
                    self.$(".button_ok").addClass("oe_highlight");
                    self.$(".button_ok").removeAttr("disabled");
                    self.$(".button_ok").text("OK");
                    self.is_valid = true;
                } else {
                    self.$(".button_ok").removeClass("oe_highlight");
                    self.$(".button_ok").attr("disabled", "disabled");
                    self.$(".button_ok").text("OK");
                    self.is_valid = false;
                    var debit = (balance > 0 ? self.formatCurrencies(balance, self.st_line.currency_id) : "");
                    var credit = (balance < 0 ? self.formatCurrencies(-1*balance, self.st_line.currency_id) : "");
                    var $line = $(QWeb.render("bank_statement_reconciliation_line_open_balance", {
                        debit: debit,
                        credit: credit,
                        account_code: self.map_account_id_code[self.st_line.open_balance_account_id]
                    }));
                    $line.find('.js_open_balance')[0].innerHTML = "Choose counterpart";
                    self.$(".tbody_open_balance").append($line);
                }
                return;
            }
    
            if (Math.abs(balance).toFixed(3) === "0.000") {
                self.$(".button_ok").addClass("oe_highlight");
                self.$(".button_ok").text("OK");
            } else {
                self.$(".button_ok").removeClass("oe_highlight");
                self.$(".button_ok").text("Keep open");
                var debit = (balance > 0 ? self.formatCurrencies(balance, self.st_line.currency_id) : "");
                var credit = (balance < 0 ? self.formatCurrencies(-1*balance, self.st_line.currency_id) : "");
                var $line = $(QWeb.render("bank_statement_reconciliation_line_open_balance", {
                    debit: debit,
                    credit: credit,
                    account_code: self.map_account_id_code[self.st_line.open_balance_account_id]
                }));
                self.$(".tbody_open_balance").append($line);
            }
        },
    
        modeChanged: function() {
            var self = this;
    
            self.$(".action_pane.active").removeClass("active");
    
            // Special case hack : if no_partner and mode == inactive
            if (self.st_line.has_no_partner) {
                if (self.get("mode") === "inactive") {
                    self.$(".match").slideUp(self.animation_speed);
                    self.$(".create").slideUp(self.animation_speed);
                    self.$(".toggle_match").removeClass("visible_toggle");
                    self.el.dataset.mode = "inactive";
                    return;
                } 
            }
    
            if (self.get("mode") === "inactive") {
                self.$(".match").slideUp(self.animation_speed);
                self.$(".create").slideUp(self.animation_speed);
                self.el.dataset.mode = "inactive";
    
            } else if (self.get("mode") === "match") {
                return $.when(self.filterMoveLines()).then(function() {
                    if (self.$el.hasClass("no_match")) {
                        self.set("mode", "inactive");
                        return;
                    }
                    self.$(".match").slideDown(self.animation_speed);
                    self.$(".create").slideUp(self.animation_speed);
                    self.el.dataset.mode = "match";
                });
    
            } else if (self.get("mode") === "create") {
                self.initializeCreateForm();
                self.$(".match").slideUp(self.animation_speed);
                self.$(".create").slideDown(self.animation_speed);
                self.el.dataset.mode = "create";
            }
        },
    
        mvLinesSelectedChanged: function(elt, val) {
            var added_lines_ids = _.map(_.difference(val.newValue, val.oldValue), function(o){ return o.id });
            var removed_lines_ids = _.map(_.difference(val.oldValue, val.newValue), function(o){ return o.id });
    
            this.getParent().excludeMoveLines(added_lines_ids);
            this.getParent().unexcludeMoveLines(removed_lines_ids);

            this._super(elt, val);
        },
    
        // Generic function for updating the line_created_being_edited
        formCreateInputChanged: function(elt, val) {
            var self = this;
            var line_created_being_edited = self.get("line_created_being_edited");
            line_created_being_edited[0][elt.corresponding_property] = val.newValue;
            line_created_being_edited[0].currency_id = self.st_line.currency_id;
    
            // Specific cases
            if (elt === self.account_id_field)
                line_created_being_edited[0].account_num = self.map_account_id_code[elt.get("value")];
    
            // Update tax line
            var deferred_tax = new $.Deferred();
            if (elt === self.tax_id_field || elt === self.amount_field) {
                var amount = self.amount_field.get("value");
                var tax = self.map_tax_id_amount[self.tax_id_field.get("value")];
                if (amount && tax) {
                    deferred_tax = $.when(self.model_tax
                        .call("compute_for_bank_reconciliation", [self.tax_id_field.get("value"), amount]))
                        .then(function(data){
                            line_created_being_edited[0].amount_with_tax = line_created_being_edited[0].amount;
                            line_created_being_edited[0].amount = (data.total.toFixed(3) === amount.toFixed(3) ? amount : data.total);
                            var current_line_cursor = 1;
                            $.each(data.taxes, function(index, tax){
                                if (tax.amount !== 0.0) {
                                    var tax_account_id = (amount > 0 ? tax.account_collected_id : tax.account_paid_id);
                                    tax_account_id = tax_account_id !== false ? tax_account_id: line_created_being_edited[0].account_id;
                                    line_created_being_edited[current_line_cursor] = {
                                        id: line_created_being_edited[0].id,
                                        account_id: tax_account_id,
                                        account_num: self.map_account_id_code[tax_account_id],
                                        label: tax.name,
                                        amount: tax.amount,
                                        no_remove_action: true,
                                        currency_id: self.st_line.currency_id,
                                        is_tax_line: true
                                    };
                                    current_line_cursor = current_line_cursor + 1;
                                }
                            });
                        }
                    );
                } else {
                    line_created_being_edited[0].amount = amount;
                    line_created_being_edited.length = 1;
                    deferred_tax.resolve();
                }
            } else { deferred_tax.resolve(); }
    
            $.when(deferred_tax).then(function(){
                // Format amounts
                $.each(line_created_being_edited, function(index, val) {
                    if (val.amount)
                        line_created_being_edited[index].amount_str = self.formatCurrencies(Math.abs(val.amount), val.currency_id);
                });
                self.set("line_created_being_edited", line_created_being_edited);
                self.createdLinesChanged(); // TODO For some reason, previous line doesn't trigger change handler
            });
        },
    
        createdLinesChanged: function() {
            var self = this;
            self.updateAccountingViewCreatedLines();
            self.updateBalance();
    
            if (self.islineCreatedBeingEditedValid()) self.$(".add_line").show();
            else self.$(".add_line").hide();
        },
    
    
        /** Model */

        filterMoveLines: function() {
            var self = this;
            var lines_to_show = [];
            _.each(self.propositions_lines, function(line){
                var filter = (line.q_label.toLowerCase().indexOf(self.filter.toLowerCase()) > -1 || line.account_code.toLowerCase().indexOf(self.filter.toLowerCase()) > -1);
                if (self.getParent().excluded_move_lines_ids.indexOf(line.id) === -1 && filter) {
                    lines_to_show.push(line);
                }
            });
            self.set("mv_lines", lines_to_show);
        },
    
        doPartialReconcileButtonClickHandler: function(e) {
            var self = this;
    
            var line_id = $(e.currentTarget).closest("tr").data("lineid");
            var line = _.find(self.get("mv_lines_selected"), function(o) { return o.id == line_id });
            self.partialReconcileLine(line);
    
            $(e.currentTarget).popover('destroy');
            self.updateAccountingViewMatchedLines();
            self.updateBalance();
            e.stopPropagation();
        },
    
        partialReconcileLine: function(line) {
            var self = this;
            var balance = self.get("balance");
            line.initial_amount = line.debit !== 0 ? line.debit : -1 * line.credit;
            if (balance < 0) {
                line.debit += balance;
                line.debit_str = self.formatCurrencies(line.debit, self.st_line.currency_id);
            } else {
                line.credit -= balance;
                line.credit_str = self.formatCurrencies(line.credit, self.st_line.currency_id);
            }
            line.propose_partial_reconcile = false;
            line.partial_reconcile = true;
        },
    
        undoPartialReconcileButtonClickHandler: function(e) {
            var self = this;
    
            var line_id = $(e.currentTarget).closest("tr").data("lineid");
            var line = _.find(self.get("mv_lines_selected"), function(o) { return o.id == line_id });
            self.unpartialReconcileLine(line);
    
            $(e.currentTarget).popover('destroy');
            self.updateAccountingViewMatchedLines();
            self.updateBalance();
            e.stopPropagation();
        },
    
        unpartialReconcileLine: function(line) {
            var self = this;
            if (line.initial_amount > 0) {
                line.debit = line.initial_amount;
                line.debit_str = self.formatCurrencies(line.debit, self.st_line.currency_id);
            } else {
                line.credit = -1 * line.initial_amount;
                line.credit_str = self.formatCurrencies(line.credit, self.st_line.currency_id);
            }
            line.propose_partial_reconcile = true;
            line.partial_reconcile = false;
        },
    
        updateBalance: function() {
            var self = this;
            var mv_lines_selected = self.get("mv_lines_selected");
            var balance = 0;
            balance -= self.st_line.amount;
            _.each(mv_lines_selected, function(o) {
                balance = balance - o.debit + o.credit;
            });
            _.each(self.getCreatedLines(), function(o) {
                balance += o.amount;
            });
            self.set("balance", balance);
    
            // Propose partial reconciliation if necessary
            var lines_selected_num = mv_lines_selected.length;
            var lines_created_num = self.getCreatedLines().length;
            if (lines_selected_num === 1 && lines_created_num === 0 && self.st_line.amount * balance > 0) {
                mv_lines_selected[0].propose_partial_reconcile = true;
                self.updateAccountingViewMatchedLines();
            }
            if (lines_selected_num !== 1 || lines_created_num !== 0) {
                // remove partial reconciliation stuff if necessary
                _.each(mv_lines_selected, function(line) {
                    if (line.partial_reconcile === true) self.unpartialReconcileLine(line);
                    if (line.propose_partial_reconcile === true) line.propose_partial_reconcile = false;
                });
                self.updateAccountingViewMatchedLines();
            }
        },
    
        loadReconciliationProposition: function() {
            var self = this;
            return self.model_bank_statement_line
                .call("get_reconciliation_proposition", [self.st_line.id, self.getParent().excluded_move_lines_ids])
                .then(function (lines) {
                    _(lines).each(self.decorateMoveLine.bind(self));
                    self.set("mv_lines_selected", self.get("mv_lines_selected").concat(lines));
                });
        },

        // Changes the partner_id of the statement_line in the DB and reloads the widget
        changePartner: function(partner_id) {
            var self = this;
            self.is_consistent = false;
            return self.model_bank_statement_line
                // Update model
                .call("write", [[self.st_line_id], {'partner_id': partner_id}])
                .then(function () {
                    return $.when(self.restart(self.get("mode"))).then(function(){
                        self.is_consistent = true;
                    });
                });
        },
    
        // Returns an object that can be passed to process_reconciliation()
        prepareCreatedMoveLineForPersisting: function(line) {
            var dict = {};
            if (dict['account_id'] === undefined)
                dict['account_id'] = line.account_id;
            dict['name'] = line.label;
            var amount = line.tax_id ? line.amount_with_tax: line.amount;
            if (amount > 0) dict['credit'] = amount;
            if (amount < 0) dict['debit'] = -1 * amount;
            if (line.tax_id) dict['account_tax_id'] = line.tax_id;
            if (line.is_tax_line) dict['is_tax_line'] = line.is_tax_line;
            if (line.analytic_account_id) dict['analytic_account_id'] = line.analytic_account_id;
    
            return dict;
        },
    
        // idem
        prepareOpenBalanceForPersisting: function() {
            var balance = this.get("balance");
            var dict = {};
    
            dict['account_id'] = this.st_line.open_balance_account_id;
            dict['name'] = _t("Open balance");
            if (balance > 0) dict['debit'] = balance;
            if (balance < 0) dict['credit'] = -1*balance;
    
            return dict;
        },
    
        makeRPCForPersisting: function() {
            var self = this;
            var mv_line_dicts = [];
            _.each(self.get("mv_lines_selected"), function(o) { mv_line_dicts.push(self.prepareSelectedMoveLineForPersisting(o)) });
            _.each(self.getCreatedLines(), function(o) { mv_line_dicts.push(self.prepareCreatedMoveLineForPersisting(o)) });
            if (Math.abs(self.get("balance")).toFixed(3) !== "0.000") mv_line_dicts.push(self.prepareOpenBalanceForPersisting());
            return self.model_bank_statement_line
                .call("process_reconciliation", [self.st_line_id, mv_line_dicts]);
        },
    });
    

    instance.web.client_actions.add("action_manual_reconciliation_widget_reload_item", "instance.web.action_manual_reconciliation_widget_reload_item");
    // Find the manual reconciliation line identified by the account id (and the partner id) and asks it to update its data
    instance.web.action_manual_reconciliation_widget_reload_item = function(element, action) {
        function nodeTest(node) {
            return instance.web.account.manualReconciliationLine.prototype.isPrototypeOf(node)
                && node.data.account_id === action.account_id
                && (action.partner_id ? node.data.partner_id === action.partner_id : true);
        }
        function findRelevantNode(node, test) {
            if (test(node)) return node;
            var children = node.getChildren();
            for (var i=0; i<children.length; i++) {
                var node = findRelevantNode(children[i], test);
                if (node) return node;
            }
            return false;
        }
        // element is the action manager and the widget we're looking for is a child/descendent
        var widget = findRelevantNode(element, nodeTest);
        if (widget) widget.reloadMoveLines();
        // now close eventual caller wizard
        return {'type': 'ir.actions.act_window_close'};
    };

    instance.web.client_actions.add('manual_reconciliation_view', 'instance.web.account.manualReconciliation');
    instance.web.account.manualReconciliation = instance.web.account.abstractReconciliation.extend({
        
        events: {
            "change input[name='show_reconciliations_type']": "showReconciliationsTypeHandler",
        },

        init: function(parent, context) {
            this._super(parent, context);
            this.childrenWidget = instance.web.account.manualReconciliationLine;
            this.model_aml = new instance.web.Model("account.move.line");
            this.title = "Journal Items to Reconcile";
            this.show_partner_accounts = true;
            this.show_other_accounts = true;
            this.items_partner_accounts = [];
            this.items_other_accounts = [];
            this.num_total_items_partner_accounts;
            this.num_total_items_other_accounts;
            this.num_done_items_partner_accounts = 0;
            this.num_done_items_other_accounts = 0;
        },
    
        start: function() {
            var self = this;
            return $.when(this._super()).then(function(){
                self.$el.addClass("oe_manual_reconciliation");

                // Get data for all reconciliations
                return $.when(self.model_aml.call("get_data_for_manual_reconciliation", [])).then(function(data){

                    // If nothing to reconcile, stop here
                    if (data[0].length + data[1].length === 0) {
                        self.$el.prepend(QWeb.render("manual_reconciliation_nothing_to_reconcile"));
                        return;
                    }

                    // Display interface
                    self.$el.prepend(QWeb.render("manual_reconciliation", {
                        title: self.title,
                        total_lines: 0,
                        show_partner_accounts: self.show_partner_accounts,
                        show_other_accounts: self.show_other_accounts,
                        show_accounts_type_controller: data[0].length !== 0 && data[1].length !== 0
                    }));
                    
                    // Get menu id
                    new instance.web.Model("ir.model.data")
                        .call("xmlid_to_res_id", ["account.menu_bank_manual_reconciliation"])
                        .then(function(data) {
                            self.reconciliation_menu_id = data;
                            self.doReloadMenuReconciliation();
                        });

                    // Process data
                    self.num_total_items_partner_accounts = data[0].length;
                    self.num_total_items_other_accounts = data[1].length;
                    self.items_partner_accounts = {};
                    self.items_other_accounts = {};
                    _.each(data[0], function(o) {
                        o.account_type = 'partner';
                        self.prepareReconciliationData(o);
                        self.items_partner_accounts[' ' + o.partner_id*10000 + o.account_id] = o;
                    });
                    _.each(data[1], function(o) {
                        o.account_type = 'other';
                        self.prepareReconciliationData(o);
                        self.items_other_accounts[o.account_id] = o;
                    });

                    // Instanciate reconciliations
                    self.$(".reconciliation_lines_container").css("opacity", 0);
                    return $.when(self.updateProgress(false)).then(function(){
                        self.$(".reconciliation_lines_container").animate({opacity: 1}, self.aestetic_animation_speed);
                    });
                });
            });
        },

        displayReconciliation: function(data, animate_entrance) {
            var widget = new this.childrenWidget(this, {data: data, animate_entrance: animate_entrance});
            data.displayed = true;
            return widget.appendTo(this.$(".reconciliation_lines_container"));
        },

        showReconciliationsTypeHandler: function(e) {
            var self = this;
            var val = $(e.target).attr("val"); // bof
            if (val === 'partners') {
                self.show_partner_accounts = true;
                self.show_other_accounts = false;
                // détruire les items_other_accounts displayed
            } else if (val === 'others') {
                self.show_partner_accounts = false;
                self.show_other_accounts = true;
                // détruire les items_partner_accounts displayed
            } else if (val === 'both') {
                self.show_partner_accounts = true;
                self.show_other_accounts = true;
            }
            self.updateProgress();
        },

        updateProgress: function(animate_entrance) {
            animate_entrance = (animate_entrance === undefined ? true : animate_entrance);
            var self = this;

            self.updateProgressbar();

            // remove children that should not be displayed
            _.each(self.getChildren(), function(child) {
                if (!self.show_partner_accounts && child.data.account_type === 'partner') {
                    child.$el.slideUp(self.aestetic_animation_speed, function(){ child.destroy() });
                    child.data.displayed = false;
                }
                if (!self.show_other_accounts && child.data.account_type === 'other') {
                    child.$el.slideUp(self.aestetic_animation_speed, function(){ child.destroy() });
                    child.data.displayed = false;
                }
            });
            
            // show next reconciliation(s)
            var reconciliations_to_show = self.max_reconciliations_displayed - self.getChildren().length;
            var child_promises = [];
            if (self.show_partner_accounts) {
                _.each(self.items_partner_accounts, function(item){
                    if (reconciliations_to_show === 0) return;
                    if (! item.displayed) {
                        child_promises.push(self.displayReconciliation(item, animate_entrance));
                        reconciliations_to_show--;
                    }
                });
            }
            if (self.show_other_accounts) {
                _.each(self.items_other_accounts, function(item){
                    if (reconciliations_to_show === 0) return;
                    if (! item.displayed) {
                        child_promises.push(self.displayReconciliation(item, animate_entrance));
                        reconciliations_to_show--;
                    }
                });
            }
            return $.when.apply($, child_promises).then(function(){

                // show or hide done message
                var reconciliations_left = 0;
                if (self.show_partner_accounts)
                    reconciliations_left = reconciliations_left + self.num_total_items_partner_accounts - self.num_done_items_partner_accounts;
                if (self.show_other_accounts)
                    reconciliations_left = reconciliations_left + self.num_total_items_other_accounts - self.num_done_items_other_accounts;
                if (reconciliations_left === 0 && self.$(".done_message").length === 0)
                    return self.showDoneMessage();
                else if (self.$(".done_message").length !== 0)
                    return self.hideDoneMessage();
            });
        },

        updateProgressbar: function() {
            var done = 0;
            var total = 0;
            if (this.show_partner_accounts) {
                done += this.num_done_items_partner_accounts;
                total += this.num_total_items_partner_accounts;
            }
            if (this.show_other_accounts) {
                done += this.num_done_items_other_accounts;
                total += this.num_total_items_other_accounts;
            }
            var prog_bar = this.$(".progress .progress-bar");
            prog_bar.attr("aria-valuenow", done);
            prog_bar.css("width", (done/total*100)+"%");
            this.$(".progress .progress-text .valuenow").text(done);
            this.$(".progress .progress-text .valuemax").text(total);
        },

        showDoneMessage: function() {
            this.$(".oe_form_sheet").append(QWeb.render("manual_reconciliation_done_message", {
                title: "U done !",
            }));
            var container = $("<div style='overflow: hidden;' />");
            this.$(".done_message").wrap(container).css("opacity", 0).css("position", "relative").css("left", "-50%");
            this.$(".done_message").animate({opacity: 1, left: 0}, this.aestetic_animation_speed*2, "easeOutCubic");
            this.$(".done_message").animate({opacity: 1}, this.aestetic_animation_speed*3, "easeOutCubic");
        },

        hideDoneMessage: function() {
            var self = this;
            this.$(".done_message").animate({opacity: 0, left: "-50%"}, this.aestetic_animation_speed*2, "easeOutCubic", function(){
                self.$(".done_message").unwrap().remove();
            });
        },

        prepareReconciliationData: function(data) {
            var self = this;
            data.displayed = false;
            _.each(data.move_lines, function(o){ self.decorateMoveLine(o) });
        },

        childValidated: function(child) {
            if (child.data.account_type === "partner")
                this.num_done_items_partner_accounts++;
            else if (child.data.account_type === "other")
                this.num_done_items_other_accounts++;
            this.updateProgress();
        },
    });
    
    instance.web.account.manualReconciliationLine = instance.web.account.abstractReconciliationLine.extend({

        events: {
            "click .accounting_view thead": "headerClickHandler",
            "click .filler_line": "fillerLineClickHandler",
            "click .button_reconcile": "buttonReconcileClickHandler",
        },
    
        init: function(parent, context) {
            this._super(parent, context);
            this.model_aml = this.getParent().model_aml;
            this.data = context.data;
        },
    
        start: function() {
            this.$el.addClass("oe_manual_reconciliation_line");
            return this._super();
        },

        render: function() {
            var self = this;
            self.$el.prepend(QWeb.render("manual_reconciliation_line", {
                data: self.data,
            }));
            self.updateBalance();
            this.set("mv_lines", this.data.move_lines);
            self.set("mode", "match");
        },

        /* Properties handlers */

        modeChanged: function() {
            var self = this;
            if (self.get("mode") === "inactive") {
                self.$(".match").slideUp(self.animation_speed);
                self.el.dataset.mode = "inactive";
            } else if (self.get("mode") === "match") {
                self.$(".match").slideDown(self.animation_speed);
                self.el.dataset.mode = "match";
            }
        },

        /* Event handlers */

        headerClickHandler: function() {
            if (this.get("mode") === "match") {
                this.set("mode", "inactive");
            } else {
                this.set("mode", "match");
            }
        },

        fillerLineClickHandler: function() {
            this.set("mode", "match");
        },

        buttonReconcileClickHandler: function() {
            var self = this;
            if (this.get("mv_lines_selected").length === 0) { // Maybe in buttonDontReconcileClickHandler
                this.markAsReconciled();
            } else if (Math.abs(this.get("balance")).toFixed(3) === "0.000") {
                this.reconcile(false);
            } else {
                this.reconcile(true);
            }
        },

        /* Views updating */

        updateMatchView: function() {
            this._super();
            // Make sure there's at least one (empty) line in the accounting view so the T appears
            // Should be done in CSS with sth like elt:empty:before { content: "HTML"; }
            // Unfortunately, "Generated content does not alter the document tree"
            if (this.get("mv_lines_selected").length === 0)
                this.$(".tbody_matched_lines").append('<tr class="filler_line"><td class="cell_action"></td><td class="cell_due_date"></td><td class="cell_label"></td><td class="cell_debit"></td><td class="cell_credit"></td><td class="cell_info_popover"></td></tr>');
        },

        /* Model */

        updateBalance: function() {
            var self = this;
            var mv_lines_selected = self.get("mv_lines_selected");
            var balance = 0;
            _.each(mv_lines_selected, function(o) {
                balance = balance - o.debit + o.credit;
            });
            self.set("balance", balance);

            self.$(".button_reconcile").removeClass("oe_highlight");
            if (mv_lines_selected.length === 0) {
                self.$(".button_reconcile").text(_t("Keep Open"));
            } else if (Math.abs(balance).toFixed(3) === "0.000") {
                self.$(".button_reconcile").addClass("oe_highlight");
                self.$(".button_reconcile").text(_t("Full Reconcile"));
            } else {
                self.$(".button_reconcile").text(_t("Partial Reconcile"));
            }
        },

        filterMoveLines: function() {
            var self = this;
            var lines_to_show = self.get("mv_lines");
            _.each(self.propositions_lines, function(line){
                if (line.q_label.toLowerCase().indexOf(self.filter.toLowerCase()) > -1)
                    lines_to_show.push(line);
            });
            self.set("mv_lines", lines_to_show);
        },

        reconcile: function(dialog) {
            var self = this;
            var ids = _.pluck(self.get("mv_lines_selected"), 'id');

            if (dialog) {
                new instance.web.Model("ir.model.data").call("get_object_reference", ["account", "action_view_account_move_line_reconcile"]).then(function(result) {
                    var additional_context = {
                        active_id: ids[0], // TODO : never used ?
                        active_ids: ids,
                        active_model: "account.move.line",
                        account_id: self.data.account_id
                    };
                    if (self.data.partner_id) additional_context['partner_id'] = self.data.partner_id;

                    self.rpc("/web/action/load", {
                        action_id: result[1],
                        context: additional_context
                    }).done(function (result) {
                        result.context = instance.web.pyeval.eval('contexts', [result.context, additional_context]);
                        result.flags = result.flags || {};
                        result.flags.new_window = true;
                        return self.do_action(result);
                        // Beware ! The way the widget is updated when the wizard finished its job is cruel and unusual
                        // The wizard receives the account_id and eventual partner_id in its context. When the reconciliation
                        // is done, it calls the client action action_manual_reconciliation_widget_reload_item passing it
                        // the id(s). This client action then closes the wizard, checks if the widget exists and, if so,
                        // calls its reloadMoveLines method.
                    });
                });
            } else {
                self.model_aml.call("reconcile_partial", [ids, 'manual']).done(function() {
                    self.reloadMoveLines();
                });
            }
        },

        markAsReconciled: function() {
            var self = this;
            if (this.data.account_type === "partner") {
                var id = this.data.partner_id;
                var model = "res.partner";
            } else if (this.data.account_type === "other") {
                var id = this.data.account_id;
                var model = "account.account";
            }
            return new instance.web.Model(model).call("mark_as_reconciled", [[id]]).then(function() {
                return self.persistAndDestroy();
            });
        },

        reloadMoveLines: function() {
            var self = this;
            var params = [self.data.account_id];
            if (self.data.partner_id) params.push(self.data.partner_id);
            return self.model_aml.call("get_move_lines_for_manual_reconciliation_by_account_and_parter", params).then(function(lines) {
                if (lines.length === 0) self.persistAndDestroy();
                else {
                    // TODO : mettre les nouvelles lignes dans l'ordre préexistant
                    var ids_mv_lines_selected = _.pluck(self.get("mv_lines_selected"), 'id');
                    _.each(lines, function(o){ self.getParent().decorateMoveLine(o) });
                    self.set("mv_lines_selected", _.filter(lines, function(o){ return ids_mv_lines_selected.indexOf(o.id) !== -1; }));
                    self.set("mv_lines", _.filter(lines, function(o){ return ids_mv_lines_selected.indexOf(o.id) === -1; }));
                    // change event is not always fired
                    self.mvLinesSelectedChanged();
                    self.mvLinesChanged();
                }
            });
        },
    });
<<<<<<< HEAD
=======
    
>>>>>>> 79b2166351ac4beac7e3cc7a13fa53820eb4c244
};
