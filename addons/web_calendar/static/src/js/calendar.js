/*---------------------------------------------------------
 * OpenERP web_calendar
 *---------------------------------------------------------*/

(function() {
    // Monkey patch dhtml scheduler in order to fix a bug.
    if (this.scheduler) {
        // It manually implements some kind of dbl click event
        // bubbling but fails to do it properly.
        var old_scheduler_dblclick = scheduler._on_dbl_click;
        scheduler._on_dbl_click = function(e, src) {
            if (src && !src.className) {
                return;
            } else {
                old_scheduler_dblclick.apply(this, arguments);
            }
        };

        // It uses the date+time format, leading to month range being between
        // 1/5 08:53 - 1/6 08:52 instead of 1/5 00:00 - 31/5 23:59
        scheduler._click.dhx_cal_today_button = function() {
            if (scheduler.callEvent("onBeforeTodayDisplayed", [])) {
                scheduler.setCurrentView( scheduler.date.date_part(new Date()) );
            }
        };

        // Fix color of timed (i.e != allday) event on month view
        // Those should be displayed in non-inverted colors
        var old_scheduler_render_hbar = scheduler.render_event_bar;
        scheduler.render_event_bar = function (ev) {
            old_scheduler_render_hbar.apply(this, arguments);
            if (ev._timed) {
                // Fix color for month event - needed by terrace dhx theme
                $(this._rendered[this._rendered.length - 1])
                    .css('background-color', '')
                    .css('color', ev.color);
            }
        };

        // Fix vertical event to allow used to drag'n'drop it by clicking
        // anywere on the event. By default you could only drag event by
        // clicking on the header - but as the zone can be really small, this
        // was to difficult to select it
        var old_scheduler_render_vbar = scheduler._render_v_bar;
        scheduler._render_v_bar = function (id, x, y, w, h, style, contentA, contentB, bottom) {
            var container = old_scheduler_render_vbar.apply(this, arguments);
            var event_body = $('.dhx_body', container);
            // Note: dhx_event_move class has to be first, otherwise dnd will not work
            event_body.attr('class', 'dhx_event_move '+event_body.attr('class'));
            return container;
        };
        var old_scheduler_on_mouse_down = scheduler._on_mouse_down;
        scheduler._on_mouse_down = function(e,src) {
            var result = old_scheduler_on_mouse_down.apply(this, arguments);
            this._drag_sstamp = this._drag_mode ? e.timeStamp : null;
            return result;
        };
        var old_scheduler_on_mouse_move = scheduler._on_mouse_move;
        scheduler._on_mouse_move = function(e) {
            if (this._drag_mode && this._drag_sstamp && e.timeStamp - this._drag_sstamp < 150) {
                // less that 150ms between drag start and move, propably an unwanted drag - ignore it
                return;
            }
            return old_scheduler_on_mouse_move.apply(this, arguments);
        };
        scheduler._lame_clone = function(object, cache) {
            var i, t, result; // iterator, types array, result

            cache = cache || [];

            for (i=0; i<cache.length; i+=2)
                if(object === cache[i])
                    return cache[i+1];

            if (object && typeof object == "object") {
                result = {};
                t = [Array,Date,Number,String,Boolean];
                for (i=0; i<t.length; i++) {
                    if (object instanceof t[i])
                        result = i ? new t[i](object) : new t[i](); // first one is array
                }
                cache.push(object, result);
                for (i in object) {
                    if (i == 'oe_view' || i == 'record') {
                        continue;
                    }
                    if (Object.prototype.hasOwnProperty.apply(object, [i]))
                        result[i] = scheduler._lame_clone(object[i], cache)
                }
            }
            return result || object;
        };

        // Fix incompatibility between timeline view (w/ second scale) and minical
        var old_scheduler__render_calendar = scheduler._render_calendar;
        scheduler._render_calendar = function(obj, sd, conf, previous) {
            var mode = scheduler._mode;
            if (scheduler.matrix[mode] && scheduler.matrix[mode]._header_resized) {
                scheduler.xy.scale_height /= 2;
            }
            var d = old_scheduler__render_calendar.apply(this, arguments);
            if (scheduler.matrix[mode] && scheduler.matrix[mode]._header_resized) {
                scheduler.xy.scale_height *= 2;
            }
            return d;
        };


        // Ensure quick-info is correctly hidden when clicking outside of it
        var old_init_quick_info = scheduler._init_quick_info;
        scheduler._init_quick_info = function() {
            var qi_box = old_init_quick_info();
            var $qi_box = $(qi_box);
            if (!$qi_box.attr('tabindex')) {
                $qi_box.attr('tabindex', -1).focusout(function() {
                    var qi = scheduler._quick_info_box;
                    if (qi && qi.parentNode) {
                        scheduler.hideQuickInfo();
                    }
                })
            }
            return qi_box;
        };
        var old_show_quick_info = scheduler._show_quick_info;
        scheduler._show_quick_info = function (pos) {
            old_show_quick_info(pos);
            $(scheduler._quick_info_box).focus();
        };
        var old_hide_quick_info = scheduler.hideQuickInfo;
        scheduler.hideQuickInfo = function(forced) {
            if (!this._quick_info_box_id) {
                // prevent hidding quick-info if it's already hidden
                // this will crash under chrome (DOM element not found)
                return
            }
            return old_hide_quick_info.apply(this, arguments);
        };

        // Tune display of vertical hour scale
        scheduler.templates.hour_scale = function(date) {
            var section_width = Math.floor(scheduler.xy.scale_width/2);
            var minute_height = Math.floor(scheduler.config.hour_size_px/2);
            var html = "<div class='dhx_scale_hour_main' style='width: %spx; line-height: %spx'>%s</div>"
                      +"<div class='dhx_scale_hour_minute' style='line-height: %spx;'><sup>00</sup></div>"
            return _.str.sprintf(html, section_width, minute_height, date.getHours(),
                                       minute_height);
        };

        // Add specific templates to allow user-defined rendering
        scheduler.templates.event_text = function(start_date, end_date, ev) {
            if (ev.oe_view && ev.oe_view.render_has_template('calendar-text-box')) {
                return ev.oe_view.render_event(ev, 'calendar-text-box');
            }
            return ev.text;
        };
        scheduler.templates.event_bar_text = function(start_date, end_date, ev) {
            if (ev.oe_view && ev.oe_view.render_has_template('calendar-text-box')) {
                return ev.oe_view.render_event(ev, 'calendar-text-box');
            }
            return ev.text;
        };
        scheduler.templates.quick_info_title = function(start_date, end_date, ev) {
            if (ev.oe_view && ev.oe_view.render_has_template('calendar-text-box')) {
                return ev.oe_view.render_event(ev, 'calendar-text-box');
            }
             return ev.text.substr(0,50);
        };
        scheduler.templates.quick_info_content = function(start_date, end_date, ev) {
            if (ev.oe_view && ev.oe_view.render_has_template('calendar-info-box')) {
                return ev.oe_view.render_event(ev, 'calendar-info-box');
            }
            return ev.details || ev.text;
        };
    }
}());

openerp.web_calendar = function(instance) {
var _t = instance.web._t,
   _lt = instance.web._lt;
var QWeb = instance.web.qweb;
instance.web.views.add('calendar', 'instance.web_calendar.CalendarView');
instance.web_calendar.CalendarView = instance.web.View.extend({
    template: "CalendarView",
    display_name: _lt('Calendar'),
// Dhtmlx scheduler ?
    init: function(parent, dataset, view_id, options) {
        var self = this;
        this._super(parent);
        this.ready = $.Deferred();
        this.set_default_options(options);
        this.dataset = dataset;
        this.model = dataset.model;
        this.fields_view = {};
        this.view_id = view_id;
        this.view_type = 'calendar';
        this.has_been_loaded = $.Deferred();
        this.dataset_events = [];
        this.COLOR_PALETTE = ['#f57900', '#cc0000', '#d400a8', '#75507b', '#3465a4', '#73d216', '#c17d11', '#edd400',
             '#fcaf3e', '#ef2929', '#ff00c9', '#ad7fa8', '#729fcf', '#8ae234', '#e9b96e', '#fce94f',
             '#ff8e00', '#ff0000', '#b0008c', '#9000ff', '#0078ff', '#00ff00', '#e6ff00', '#ffff00',
             '#905000', '#9b0000', '#840067', '#510090', '#0000c9', '#009b00', '#9abe00', '#ffc900' ];
        this.color_map = {};
        this.last_search = [];
        this.range_start = null;
        this.range_stop = null;
        this.update_range_dates(Date.today());
        this.selected_filters = [];
        this.is_slow_open = false;
        this.scheduler_events = [];

        // for rgroup_by support
        this.search_group_by_key = null;
        this.search_groups = [];

        /* TODO: add postprocess for m2m fields
           - currently none of them are displayed */
        this.many2manys = [];
        this.qweb = new QWeb2.Engine();
        this.qweb.debug = instance.session.debug;
        this.qweb.default_dict = _.clone(QWeb.default_dict);
    },
    view_loading: function(r) {
        return this.load_calendar(r);
    },
    destroy: function() {
        this.destroy_scheduler();
        this._super();
    },
    load_calendar: function(data) {
        this.fields_view = data;
        this.add_qweb_template();
        this.$el.addClass(this.fields_view.arch.attrs['class']);
        this.calendar_fields = {};
        this.ids = this.dataset.ids;
        this.color_values = [];
        this.info_fields = [];

        this.name = this.fields_view.name || this.fields_view.arch.attrs.string;
        this.view_id = this.fields_view.view_id;

        // mode, one of month, week or day
        this.mode = this.fields_view.arch.attrs.mode;

        // date_start is mandatory, date_delay and date_stop are optional
        this.date_start = this.fields_view.arch.attrs.date_start;
        this.date_delay = this.fields_view.arch.attrs.date_delay;
        this.date_stop = this.fields_view.arch.attrs.date_stop;

        this.day_length = this.fields_view.arch.attrs.day_length || 8;
        this.color_field = this.fields_view.arch.attrs.color;
        this.color_string = this.fields_view.fields[this.color_field] ?
            this.fields_view.fields[this.color_field].string : _t("Filter");

        if (this.color_field && this.selected_filters.length === 0) {
            var default_filter;
            if ((default_filter = this.dataset.context['calendar_default_' + this.color_field])) {
                this.selected_filters.push(default_filter + '');
            }
        }
        this.fields =  this.fields_view.fields;

        if (!this.date_start) {
            throw new Error(_t("Calendar view has not defined 'date_start' attribute."));
        }

        //* Calendar Fields *
        this.calendar_fields.date_start = {'name': this.date_start, 'kind': this.fields[this.date_start].type};

        if (this.date_delay) {
            if (this.fields[this.date_delay].type != 'float') {
                throw new Error(_t("Calendar view has a 'date_delay' type != float"));
            }
            this.calendar_fields.date_delay = {'name': this.date_delay, 'kind': this.fields[this.date_delay].type};
        }
        if (this.date_stop) {
            this.calendar_fields.date_stop = {'name': this.date_stop, 'kind': this.fields[this.date_stop].type};
        }

        for (var fld = 0; fld < this.fields_view.arch.children.length; fld++) {
            this.info_fields.push(this.fields_view.arch.children[fld].attrs.name);
        }

        this.init_scheduler();

        if (!this.sidebar && this.options.$sidebar) {
            this.sidebar = new instance.web_calendar.Sidebar(this);
            this.has_been_loaded.then(this.sidebar.appendTo(this.$el.find('.oe_calendar_sidebar_container')));
        }
        this.trigger('calendar_view_loaded', data);
        return this.has_been_loaded.resolve();
    },
    /*  add_qweb_template
    *   select the nodes into the xml and send to extract_aggregates the nodes with TagName="field"
    */
    add_qweb_template: function() {
        for (var i=0, ii=this.fields_view.arch.children.length; i < ii; i++) {
            var child = this.fields_view.arch.children[i];
            if (child.tag === "templates") {
                this.transform_qweb_template(child);
                this.qweb.add_template(instance.web.json_node_to_xml(child));
                break;
            }
        }
    },
    transform_qweb_template: function(node) {
        var qweb_add_if = function(node, condition) {
            if (node.attrs[QWeb.prefix + '-if']) {
                condition = _.str.sprintf("(%s) and (%s)", node.attrs[QWeb.prefix + '-if'], condition);
            }
            node.attrs[QWeb.prefix + '-if'] = condition;
        };
        // Process modifiers
        if (node.tag && node.attrs.modifiers) {
            var modifiers = JSON.parse(node.attrs.modifiers || '{}');
            if (modifiers.invisible) {
                qweb_add_if(node, _.str.sprintf("!calendar_compute_domain(%s)", JSON.stringify(modifiers.invisible)));
            }
        }
        switch (node.tag) {
            case 'field':
                if (this.fields_view.fields[node.attrs.name].type === 'many2many') {
                    if (_.indexOf(this.many2manys, node.attrs.name) < 0) {
                        this.many2manys.push(node.attrs.name);
                    }
                    node.tag = 'div';
                    node.attrs['class'] = (node.attrs['class'] || '') + ' oe_form_field oe_tags';
                } else {
                    node.tag = QWeb.prefix;
                    node.attrs[QWeb.prefix + '-esc'] = 'record.' + node.attrs['name'] + '.value';
                }
                break;
        }
        if (node.children) {
            for (var i = 0, ii = node.children.length; i < ii; i++) {
                this.transform_qweb_template(node.children[i]);
            }
        }
    },
    transform_record: function(record) {
        var self = this,
            new_record = {},
            calendar_field_names = _(this.calendar_fields).chain()
                                        .values().pluck('name').value(),
            fields = _.uniq(_.keys(self.fields_view.fields)
                            .concat(calendar_field_names));
        _.each(record, function(value, name) {
            if (_.indexOf(fields, name) === -1) {
                return;
            }
            var r = _.clone(self.fields_view.fields[name] || {});
            if ((r.type === 'date' || r.type === 'datetime') && value) {
                r.raw_value = instance.web.auto_str_to_date(value);
            } else {
                r.raw_value = value;
            }
            r.value = instance.web.format_value(value, r);
            new_record[name] = r;
        });
        return new_record;
    },
    render_has_template: function(template_name) {
        return !!this.qweb.templates[template_name]
    },
    render_event: function(ev, template_name) {
        if (!ev.render_cache) {
            ev.render_cache = {};
        }
        // Return cache version if available
        if (ev.render_cache[template_name]) {
            return ev.render_cache[template_name];
        }

        this.qweb_context = {
            instance: instance,
            record: ev.record,
            widget: this,
            read_only_mode: this.options.read_only_mode,
        };
        for (var p in this) {
            if (_.str.startsWith(p, 'calendar_') && _.isFunction(this[p])) {
                this.qweb_context[p] = _.bind(this[p], this);
            }
        }
        var result = this.qweb.render(template_name, this.qweb_context);
        ev.render_cache[template_name] = result;
        return result
    },
    get_calendar_userconfig: function() {
        return {
            day_starts_on: 8, // starts on 08:00
            day_ends_on: 18, // ends on 18:00
            day_time_step: 15, // the interval to snap the event on the calendar - rounding time (in minutes)
            default_event_length: 60, // the default event duration (in minutes),
            show_n_hours_at_a_time: 12,  // only applies to Timeline view,
            show_current_time_mark: true,
        }
    },
    destroy_scheduler: function() {
        scheduler.clearAll();
        this.scheduler_detachAllEvents();
        delete scheduler.matrix['timeline'];
        if (scheduler._mark_now_timer) {
            window.clearInterval(scheduler._mark_now_timer);
            scheduler._mark_now_timer = undefined;
        }
    },
    init_scheduler: function() {
        var self = this;
        scheduler.clearAll();
        if (this.fields[this.date_start]['type'] == 'time') {
            scheduler.config.xml_date = "%H:%M:%S";
        } else {
            scheduler.config.xml_date = "%Y-%m-%d %H:%i";
        }

        var calendar_config = self.get_calendar_userconfig();

        scheduler.config.api_date = "%Y-%m-%d %H:%i";
        scheduler.config.multi_day = true; //Multi day events are not rendered in daily and weekly views
        scheduler.config.mark_now = calendar_config.show_current_time_mark;
        scheduler.config.start_on_monday = Date.CultureInfo.firstDayOfWeek !== 0; //Sunday = Sunday, Others = Monday
        scheduler.config.time_step = calendar_config.day_time_step;
        scheduler.config.scroll_hour = calendar_config.day_starts_on;
        scheduler.config.drag_resize = true;
        scheduler.config.drag_create = true;
        scheduler.config.mark_now = true;
        scheduler.config.day_date = '%l %j';
        scheduler.config.details_on_create = true;
        scheduler.config.details_on_dblclick = true;
        scheduler.xy.bar_height = 20;
        // Limit and marked zone
        scheduler.config.check_limits = true;
        // Quick info popup
        scheduler.config.quick_info_detached = true;
        // Group By support
        scheduler.config.search_group_by_key = this.search_group_by_key;
        scheduler.config.section_hour_size_px = 22;
        scheduler.config.section_width = 150;

        scheduler.locale = {
            date:{
                month_full: Date.CultureInfo.monthNames,
                month_short: Date.CultureInfo.abbreviatedMonthNames,
                day_full: Date.CultureInfo.dayNames,
                day_short: Date.CultureInfo.abbreviatedDayNames
            },
            labels:{
                dhx_cal_today_button: _t("Today"),
                day_tab: _t("Day"),
                week_tab: _t("Week"),
                month_tab: _t("Month"),
                new_event: _t("New event"),
                icon_save: _t("Save"),
                icon_cancel: _t("Cancel"),
                icon_details: _t("Details"),
                icon_edit: _t("Edit"),
                icon_delete: _t("Delete"),
                confirm_closing: "",//Your changes will be lost, are your sure ?
                confirm_deleting: _t("Event will be deleted permanently, are you sure?"),
                section_description: _t("Description"),
                section_time: _t("Time period"),
                full_day: _t("Full day"),

                /*recurring events*/
                confirm_recurring: _t("Do you want to edit the whole set of repeated events?"),
                section_recurring: _t("Repeat event"),
                button_recurring: _t("Disabled"),
                button_recurring_open: _t("Enabled"),

                /*agenda view extension*/
                agenda_tab: _t("Agenda"),
                date: _t("Date"),
                description: _t("Description"),

                /*year view extension*/
                year_tab: _t("Year"),

                /* week agenda extension */
                week_agenda_tab: _t("Agenda")
            }
        };

        scheduler.locale.labels.timeline_tab = "Timeline";
        scheduler.locale.labels.section_custom = "Section";
        var sections = [
            {key: undefined, label: ''},
        ];

        // Show working hours
        scheduler.createTimelineView({
            name:   "timeline",
            x_unit: "hour",
            x_date: "%H:%i",
            x_step: 1,
            x_size: calendar_config.show_n_hours_at_a_time,
            x_start: calendar_config.day_starts_on,
            // x_length: 24,
            second_scale: {
                x_unit: "day",
                x_date: "%F %d",
            },
            y_unit: sections,
            y_property: "section_id",
            dy: 80,
            render: "bar",
            show_unassigned: true,
            round_position: false,
        });

        // // Show weeks
        // scheduler.createTimelineView({
        //     name:   "timeline",
        //     x_unit: "hour",
        //     x_date: "%H:%i",
        //     x_step: 4,
        //     x_size: 6*7, // display 7 days
        //     x_start: 0,
        //     x_length:   6*7, // display 7 days
        //     y_unit: sections,
        //     y_property: "section_id",
        //     render:"bar",
        //     second_scale: {
        //         x_unit: "day", // unit which should be used for second scale
        //         x_date: "%F %d" // date format which should be used for second scale, "July 01"
        //     },
        //     show_unassigned: true,
        // });

        scheduler.init(this.$el.find('.oe_calendar')[0], null, this.mode || 'month');
        this.scheduler_attachEvent('onViewChange', this.proxy('view_changed'));
        this.scheduler_attachEvent('onEventChanged', this.proxy('quick_save'));
        this.scheduler_attachEvent('onEventDeleted', this.proxy('delete_event'));
        this.scheduler_attachEvent('onEventAdded', function(event_id, event_obj) {
            var fn = event_obj._force_slow_create ? 'slow_create' : 'quick_create';
            self[fn].apply(self, arguments);
        });
        this.scheduler_attachEvent('onClick', function(event_id, mouse_event) {
            return true;
        });
        this.scheduler_attachEvent('onDblClick', function(event_id, mouse_event) {
            if (!self.$el.find('.dhx_cal_editor').length) {
                self.open_event(event_id);
            }
        });
        this.scheduler_attachEvent('onEmptyClick', function(start_date, mouse_event) {
            scheduler._loading = false; // Dirty workaround for a dhtmleditor bug I couln't track
            if (!self.$el.find('.dhx_cal_editor').length) {
                var end_date = new Date(start_date);
                end_date.addHours(1);
                scheduler.addEvent({
                    start_date: start_date,
                    end_date: end_date,
                    _force_slow_create: true,
                });
            }
        });
        this.scheduler_attachEvent("onBeforeLightbox", function (event_id) {
            var index = self.dataset.get_id_index(event_id);
            if (index !== null) {
                self.open_event(self.dataset.ids[index]);
            } else {
                self.slow_create(event_id, scheduler.getEvent(event_id));
            }
           return false;
        });

        // Reset scroll hour
        // - this is needed when switching between menu, scrollTop is not
        //   correctly preserved (xal - 2013-06-30)
        var scheduler_scrollTop = scheduler.config.hour_size_px *
                (scheduler.config.scroll_hour - scheduler.config.first_hour);
        scheduler._els['dhx_cal_data'][0].scrollTop  = scheduler_scrollTop;

        // Refresh scheduler (displaying events)
        this.refresh_scheduler();

        // Remove hard coded style attributes from dhtmlx scheduler
        this.$el.find(".dhx_cal_navline").removeAttr('style');
        instance.web.bus.on('resize',this,function(){
            self.$el.find(".dhx_cal_navline").removeAttr('style');
        });
    },
    scheduler_attachEvent: function(name, catcher, callObj) {
        var event_id = scheduler.attachEvent(name, catcher, callObj);
        this.scheduler_events.push(event_id);
    },
    scheduler_detachAllEvents: function () {
        _.each(this.scheduler_events, function (event_id) {
            scheduler.detachEvent(event_id);
        })
        this.scheduler_events = [];
    },
    view_changed: function(mode, date) {
        this.$el.find('.oe_calendar').removeClass('oe_cal_day oe_cal_week oe_cal_month').addClass('oe_cal_' + mode);
        if (!date.between(this.range_start, this.range_stop)) {
            this.update_range_dates(date);
            this.ranged_search();
        }
        this.ready.resolve();
    },
    update_range_dates: function(date) {
        this.range_start = date.clone().moveToFirstDayOfMonth();
        this.range_stop = this.range_start.clone().addMonths(1).addSeconds(-1);
    },
    refresh_scheduler: function() {
        scheduler.config.sections = this.search_groups;
        scheduler.config.section_key = this.search_group_by_key;
        if (this.search_group_by_key) {
            scheduler.config.display_marked_timespans = true;
            scheduler.matrix.timeline.y_unit = this.search_groups;
        } else {
            scheduler.config.display_marked_timespans = true;
            scheduler.matrix.timeline.y_unit = [
                {key: undefined, label: ''},
            ];
        }
        scheduler.setCurrentView(scheduler._date);
    },
    reload_event: function(id) {
        this.dataset.read_ids([id], _.keys(this.fields)).done(this.proxy('events_loaded'));
    },
    get_color: function(key) {
        if (this.color_map[key]) {
            return this.color_map[key];
        }
        var index = _.keys(this.color_map).length % this.COLOR_PALETTE.length;
        var color = this.COLOR_PALETTE[index];
        this.color_map[key] = color;
        return color;
    },
    events_loaded: function(events, fn_filter, no_filter_reload) {
        var self = this;

        //To parse Events we have to convert date Format
        var res_events = [],
            sidebar_items = {};
        var selection_label;
        if(this.fields[this.color_field].selection) {
            selection_label = {};
            _(this.fields[this.color_field].selection).each(function(value){
                selection_label[value[0]] = value[1];
            });
        }
        for (var e = 0; e < events.length; e++) {
            var evt = events[e];
            if (!evt[this.date_start]) {
                break;
            }

            if (this.color_field) {
                var filter = evt[this.color_field];
                if (filter) {
                    if (typeof filter !== 'object') {
                        filter = [filter, filter];
                    }
                    if (selection_label) {
                        filter[1] = selection_label[filter[0]];
                    }
                    var filter_value = filter[0];
                    if (typeof(fn_filter) === 'function' && !fn_filter(filter_value)) {
                        continue;
                    }
                    var filter_item = {
                        value: filter_value,
                        label: filter[1],
                        color: this.get_color(filter_value)
                    };
                    if (!sidebar_items[filter_value]) {
                        sidebar_items[filter_value] = filter_item;
                    }
                    evt.color = filter_item.color;
                    evt.textColor = '#ffffff';
                } else {
                    evt.textColor = '#000000';
                }
            }

            if (this.fields[this.date_start]['type'] == 'date') {
                evt[this.date_start] = instance.web.auto_str_to_date(evt[this.date_start]).set({hour: 9}).toString('yyyy-MM-dd HH:mm:ss');
            }
            if (this.date_stop && evt[this.date_stop] && this.fields[this.date_stop]['type'] == 'date') {
                evt[this.date_stop] = instance.web.auto_str_to_date(evt[this.date_stop]).set({hour: 17}).toString('yyyy-MM-dd HH:mm:ss');
            }
            res_events.push(this.convert_event(evt));
        }
        scheduler.parse(res_events, 'json');
        this.refresh_scheduler();
        if (!no_filter_reload && this.sidebar) {
            this.sidebar.filter.events_loaded(sidebar_items);
        }
    },
    convert_event: function(evt) {
        var date_start = instance.web.str_to_datetime(evt[this.date_start]),
            date_stop = this.date_stop ? instance.web.str_to_datetime(evt[this.date_stop]) : null,
            date_delay = evt[this.date_delay] || 1.0,
            res_text = '';

        if (this.info_fields) {
            res_text = _.map(this.info_fields, function(fld) {
                if(evt[fld] instanceof Array)
                    return evt[fld][1];
                return evt[fld];
            });
            res_text = _.filter(res_text, function(e){return !_.isEmpty(e);});
        }
        if (!date_stop && date_delay) {
            date_stop = date_start.clone().addHours(date_delay);
        }
        var r = {
            'start_date': date_start.toString('yyyy-MM-dd HH:mm:ss'),
            'end_date': date_stop.toString('yyyy-MM-dd HH:mm:ss'),
            'text': res_text.join(', '),
            'id': evt.id,
            'section_key': undefined,
            'oe_view': this,
            'record': this.transform_record(evt),
        };
        r.record = this.transform_record(evt);
        r.oe_view = this;

        if (this.search_group_by_key) {
            var group_value = evt[this.search_group_by_key];
            if (!(group_value instanceof Array)) {
                group_value = {'key': group_value, 'label':  group_value};
            } else {
                group_value = {'key': group_value[0], 'label': group_value[1]}
            }
            if (group_value.key == false) {
                group_value.label = '';
            }
            r.section_key = group_value.key;

            var group_value_idx = -1;
            for (i=0; i < this.search_groups.length; i++) {
                if (this.search_groups[i].key == group_value.key
                    && this.search_groups[i].label == group_value.label) {
                    group_value_idx = i;
                    break;
                }
            }
            if (group_value_idx == -1) {
                group_value_idx = this.search_groups.length;
                this.search_groups.unshift(group_value);
            }
        }

        if (evt.color) {
            r.color = evt.color;
        }
        if (evt.textColor) {
            r.textColor = evt.textColor;
        }
        return r;
    },
    get_event_data: function(event_obj) {
        var data = {
            name: event_obj.text || scheduler.locale.labels.new_event
        };
        if (this.fields[this.date_start].type == 'date') {
            data[this.date_start] = instance.web.date_to_str(event_obj.start_date)
        }else {
            data[this.date_start] = instance.web.datetime_to_str(event_obj.start_date)
        }
        if (this.date_stop) {
            data[this.date_stop] = instance.web.datetime_to_str(event_obj.end_date);
        }
        if (this.date_delay) {
            var diff_seconds = Math.round((event_obj.end_date.getTime() - event_obj.start_date.getTime()) / 1000);
            data[this.date_delay] = diff_seconds / 3600;
        }
        return data;
    },
    do_search: function(domain, context, group_by) {
        this.search_groups = [];
        this.search_group_by_key = (group_by && group_by.length) ? group_by[0] : null;
        console.log('do_search groupby_key', this.search_group_by_key);
        this.last_search = arguments;
        this.ranged_search();
    },
    ranged_search: function() {
        var self = this;
        scheduler.clearAll();
        $.when(this.has_been_loaded, this.ready).done(function() {
            self.dataset.read_slice(_.keys(self.fields), {
                offset: 0,
                domain: self.get_range_domain(),
                context: self.last_search[1]
            }).done(function(events) {
                self.dataset_events = events;
                self.events_loaded(events);
            });
        });
    },
    get_range_domain: function() {
        var format = instance.web.date_to_str;
        var A = format(this.range_start.clone().addDays(-6));
        var B = format(this.range_stop.clone().addDays(6));
        var domain = [
            '&', [this.date_start, '>=', A], [this.date_start, '<=', B]
        ];
        if (this.date_stop) {
            domain.push(
            '&', [this.date_stop, '>=', A], [this.date_stop, '<=', B],
            '&', [this.date_start, '<', A], [this.date_stop, '>', B]);
            domain.unshift("|", "|");
        }
        domain.concat(this.last_search[0].slice(0))
        return domain;
    },
    do_show: function () {
        var self = this;
        $.when(this.has_been_loaded).done(function() {
            self.$el.show();
            self.do_push_state({});
        });
    },
    get_selected_ids: function() {
        // no way to select a record anyway
        return [];
    },
    current_mode: function() {
        return scheduler.getState().mode;
    },

    quick_save: function(event_id, event_obj) {
        var self = this;
        var data = this.get_event_data(event_obj);
        delete(data.name);
        var index = this.dataset.get_id_index(event_id);
        if (index !== null) {
            event_id = this.dataset.ids[index];
            this.dataset.write(event_id, data, {});
        }
    },
    quick_create: function(event_id, event_obj) {
        var self = this;
        var data = this.get_event_data(event_obj);
        this.dataset.create(data).done(function(r) {
            var id = r;
            self.dataset.ids.push(id);
            scheduler.changeEventId(event_id, id);
            self.reload_event(id);
        }).fail(function(r, event) {
            event.preventDefault();
            self.slow_create(event_id, event_obj);
        });
    },
    get_form_popup_infos: function() {
        var parent = this.getParent();
        var infos = {
            view_id: false,
            title: this.name,
        };
        if (parent instanceof instance.web.ViewManager) {
            infos.view_id = parent.get_view_id('form');
            if (parent instanceof instance.web.ViewManagerAction && parent.action && parent.action.name) {
                infos.title = parent.action.name;
            }
        }
        return infos;
    },
    slow_create: function(event_id, event_obj) {
        var self = this;
        // Workaround, some browsers trigger onEmptyClick as well as onBeforeLightbox
        // during drag&drop which calls two slow_create calls, kills the second one
        if (this.is_slow_open) {
            scheduler.deleteEvent(event_id);
            return;
        }
        this.is_slow_open = true;
        if (this.current_mode() === 'month') {
            event_obj['start_date'].addHours(8);
            if (event_obj._length === 1) {
                event_obj['end_date'] = new Date(event_obj['start_date']);
                event_obj['end_date'].addHours(1);
            } else {
                event_obj['end_date'].addHours(-4);
            }
        }
        var defaults = {};
        _.each(this.get_event_data(event_obj), function(val, field_name) {
            defaults['default_' + field_name] = val;
        });
        var something_saved = false;
        var pop = new instance.web.form.FormOpenPopup(this);
        var pop_infos = this.get_form_popup_infos();
        pop.show_element(this.dataset.model, null, this.dataset.get_context(defaults), {
            title: _.str.sprintf(_t("Create: %s"), pop_infos.title),
            disable_multiple_selection: true,
            view_id: pop_infos.view_id,
        });
        pop.on('closed', self, function() {
            this.is_slow_open = false;
            if (!something_saved) {
                scheduler.deleteEvent(event_id);
            }
        });
        pop.on('create_completed', self, function(id) {
            something_saved = true;
            self.dataset.ids.push(id);
            scheduler.changeEventId(event_id, id);
            self.reload_event(id);
        });
        // Hide quick-info if any displayed
        scheduler.hideQuickInfo();
    },
    open_event: function(event_id) {
        var self = this;
        var index = this.dataset.get_id_index(event_id);
        if (index === null) {
            // Some weird behaviour in dhtmlx scheduler could lead to this case
            // eg: making multiple days event in week view, dhtmlx doesn't trigger eventAdded !!??
            // so the user clicks back on the orphan event and we land here. We have to duplicate
            // the dhtmlx internal event because it will delete it on next sheduler refresh.
            var event_obj = scheduler.getEvent(event_id);
            scheduler.deleteEvent(event_id);
            scheduler.addEvent({
                start_date: event_obj.start_date,
                end_date: event_obj.end_date,
                text: event_obj.text,
                _force_slow_create: true,
            });
        } else {
            var pop = new instance.web.form.FormOpenPopup(this);
            var pop_infos = this.get_form_popup_infos();
            var id_from_dataset = this.dataset.ids[index]; // dhtmlx scheduler loses id's type
            pop.show_element(this.dataset.model, id_from_dataset, this.dataset.get_context(), {
                title: _.str.sprintf(_t("Edit: %s"), pop_infos.title),
                view_id: pop_infos.view_id,
            });
            pop.on('write_completed', self, function(){
                self.reload_event(id_from_dataset);
            });
            // Hide quick-info if any displayed
            scheduler.hideQuickInfo();
        }
    },
    delete_event: function(event_id, event_obj) {
        // dhtmlx sends this event even when it does not exist in openerp.
        // Eg: use cancel in dhtmlx new event dialog
        var self = this;
        var index = this.dataset.get_id_index(event_id);
        if (index !== null) {
            this.dataset.unlink(this.dataset.ids[index]);
        }
    },
    calendar_compute_domain: function(domain) {
        return instance.web.form.compute_domain(domain, this.values);
    },
});

instance.web_calendar.Sidebar = instance.web.Widget.extend({
    template: 'CalendarView.sidebar',
    start: function() {
        this._super();
        this.mini_calendar = scheduler.renderCalendar({
            container: this.$el.find('.oe_calendar_mini')[0],
            navigation: true,
            date: scheduler._date,
            handler: function(date, calendar) {
                var mode = scheduler._mode;
                if (scheduler._mode == 'month') {
                    mode = 'week';
                }
                else if (scheduler._mode == 'week') {
                    // switch to day mode if user choose a day within the current range
                    // or stay in week mode if user choose a day outside the current range
                    var week_start = scheduler._date.clone().clearTime();
                    if (week_start.getDay() != Date.CultureInfo.firstDayOfWeek)
                        week_start.moveToDayOfWeek(Date.CultureInfo.firstDayOfWeek, -1);
                    var week_end = week_start.clone().addWeeks(1);
                    if (date.between(week_start, week_end)) {
                        mode = 'day';
                    }
                }
                else if (scheduler._mode == 'day') {
                    // switch back to week mode if user click a 2nd time on the same day
                    if (date.clone().clearTime().equals(scheduler._date.clone().clearTime())) {
                        mode = 'week';
                    }
                }
                scheduler.setCurrentView(date, mode);
            }
        });
        scheduler.linkCalendar(this.mini_calendar);
        this.filter = new instance.web_calendar.SidebarFilter(this, this.getParent());
        this.filter.appendTo(this.$el.find('.oe_calendar_filter'));
    }
});
instance.web_calendar.SidebarFilter = instance.web.Widget.extend({
    events: {
        'change input:checkbox': 'filter_click'
    },
    init: function(parent, view) {
        this._super(parent);
        this.view = view;
    },
    events_loaded: function(filters) {
        var selected_filters = this.view.selected_filters.slice(0);
        this.$el.html(QWeb.render('CalendarView.sidebar.responsible', { filters: filters }));
        this.$('div.oe_calendar_responsible input').each(function() {
            if (_.indexOf(selected_filters, $(this).val()) > -1) {
                $(this).click();
            }
        });
    },
    filter_click: function(e) {
        var self = this,
            responsibles = [],
            $e = $(e.target);
        this.view.selected_filters = [];
        this.$('div.oe_calendar_responsible input:checked').each(function() {
            responsibles.push($(this).val());
            self.view.selected_filters.push($(this).val());
        });
        scheduler.clearAll();
        if (responsibles.length) {
            this.view.events_loaded(this.view.dataset_events, function(filter_value) {
                return _.indexOf(responsibles, filter_value.toString()) > -1;
            }, true);
        } else {
            this.view.events_loaded(this.view.dataset_events, false, true);
        }
    }
});

};

// vim:et fdc=0 fdl=0 foldnestmax=3 fdm=syntax:
