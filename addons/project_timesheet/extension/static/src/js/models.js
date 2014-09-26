function odoo_project_timesheet_models(project_timesheet) {

    project_timesheet.task_activity_model = Backbone.Model.extend({
        initialize: function(attributes, options) {
            Backbone.Model.prototype.initialize.call(this, attributes);
            //this.session = session;
            this.id = options.id || null;
            this.date = options.date || null;
            this.task_id = options.task_id || null;
            this.name = options.name || null; //Actually description field
            this.hours = options.hours || null;
        },
        export_as_json: function() {
            //TO Implement, will return activity record
        },
    });

    project_timesheet.TaskActivityCollection = Backbone.Collection.extend({
        model: project_timesheet.task_activity_model,
    });

    //Note: Regarding project already connected or not ? state: "connecting", //There will be two state, connecting and connected, if record is modified then again state will be changed and localstorage will be updated
    project_timesheet.task_model = Backbone.Model.extend({
        initialize: function(attributes, options) {
            Backbone.Model.prototype.initialize.call(this, attributes);
            //this.session = session;
            this.project_timesheet_widget = attributes.project_timesheet_widget;
            this.id = options.id || null;
            this.name = options.name || null;
            this.project_id = options.project_id || null;
            this.set({
                task_activities: new project_timesheet.TaskActivityCollection(),
            });
            //this.task_activities = new project_timesheet.TaskActivityCollection();
        },
        export_as_json: function() {
            //TO Implement, will return task record along with its activities collection
        },
        add_activity: function(data) {
            //TO Implement, will create new model object of activity and add it into activities collection
            var task_activity = new project_timesheet.task_activity_model({}, {id: data['id'], name: data['name'], task_id: data['task_id'][0], date: data['date'], hours: data['hours']});
            this.get('task_activities').add(task_activity);
        },
    });

    project_timesheet.TaskCollection = Backbone.Collection.extend({
        model: project_timesheet.task_model,
    });

    project_timesheet.project_model = Backbone.Model.extend({
        initialize: function(attributes, options) {
            Backbone.Model.prototype.initialize.call(this, attributes);
            //this.session = session;
            this.id = options.id || null; //If no real id, we will have virtual id, at sync time virtual id will be skipped while sending data to server
            this.name = options.name || null;
            this.set({
                tasks: new project_timesheet.TaskCollection(),
            });
            //this.tasks = new project_timesheet.TaskCollection();
        },
        export_as_json: function() {
            //TO Implement, will return project record along with its task collection
        },
        add_task: function(data) {
            //TO Implement, will create new model object of task and add it into tasks collection
            var task = new project_timesheet.task_model({}, {id: data['task_id'][0], name: data['task_id'][1], project_id: data['project_id'][0]});
            task.add_activity(data);
            this.get('tasks').add(task);
        },
    });

    project_timesheet.ProjectCollection = Backbone.Collection.extend({
        model: project_timesheet.project_model,
    });

    //Once data has been sync, read project, then task and activities and store it into localstorage also
    //While sync read model, this following model's save_to_server will fetch project, and project will fetch task in format such that its one2many

    project_timesheet.project_timesheet_model = Backbone.Model.extend({
        //initialize: function(session, attributes) {
        initialize: function(attributes) {
            var self = this;
            Backbone.Model.prototype.initialize.call(this, attributes);
            this.project_timesheet_widget = attributes.project_timesheet_widget;
            var def = $.Deferred();
            this.set({
                projects: new project_timesheet.ProjectCollection()
            });
            this.project_timesheet_db = new project_timesheet.project_timesheet_db();
            this.screen_data = {};  //see ScreenSelector
            //Try to check localstorage having session, we do not reload session like web module(core.js), instead stored in localstorage
            if(!project_timesheet.session && !_.isEmpty(this.project_timesheet_db.load("session", {}))) {
                var stored_session = this.project_timesheet_db.load("session", {});
                project_timesheet.session = new openerp.Session(undefined, stored_session['origin'], {session_id: stored_session['session_id']});
            }
            //TODO: Check if user is already logged in then load server data and update stored data else use old stored data
            //Try to load server data initially, if rpc fails then no worry we will load stored data in local storage
            if (!_.isEmpty(project_timesheet.session)) {
                def = project_timesheet.session.check_session_id().done(function() {
                    //Important Note: check_session_id may replace session_id each time when server_origin is different then origin,
                    //so we will update the localstorage session
                    self.project_timesheet_db.save("session", project_timesheet.session);
                    console.log("Here we go, you can do rpc, we having session ID.");
                    //Load server data and update localstorage
                    return self.load_server_data();
                });
            } else {
                console.log("Inside elseeee ");
                def.resolve();
            }
            //Always Load locally stored data, whether server is running(or def may fail, because server is not up, still we will load local data)
            $.when(def).always(function() {
                self.load_stored_data();
            });
        },
        add_project: function(data) {
            //TO Implement, will create new object of model if data having virtual_id and add it into collection, then it will call add task for that collection model
            //It also finds project model from collection and add task in that model if project_id passed in data is already available
            //We can find model by id, coolection.get(id of model(e.g. id of project model)), id is magic attribute of model
            var project = new project_timesheet.project_model({}, {id: data['project_id'][0], name: data['project_id'][1]});
            project.add_task(data);
            this.get('projects').add(project);
            this.project_timesheet_db.add_activity(data); //instead of data, use project.exportAsJson();
            console.log("project is ::: ", project);
        },
        load_stored_data: function() {
            //TO Implement, this will load localstorage data and call add project, add project will call add task, add task will call add activity
            //First do group by project and then task and then call add projects with grouped data, so add new project will have proper data, and it can call add_task and so on
        },
        load_server_data: function() {
            var self = this;
            //TO Implement, load last 30 days data and updated localstorage and then reload models(done by load_stored_data method)
            var momObj = new moment();
            var end_date = project_timesheet.datetime_to_str(momObj._d);
            var start_date = project_timesheet.datetime_to_str(momObj.subtract(30, "days")._d);
            return new project_timesheet.Model(project_timesheet.session, "project.task.work").call("search_read", {
                domain: [["date", ">=", start_date], ["date", "<=", end_date]],
            }).then(function(work_activities) {
                var tasks = _.pluck(work_activities, "task_id");
                tasks = _.pluck(_.groupBy(tasks), 0);
                self.project_timesheet_db.save("tasks", tasks);
                return new project_timesheet.Model(project_timesheet.session, "project.task").call("search_read", {
                    domain: [["id", "in", _.map(tasks, function(task) {return task[0];})]],
                    fields: ['id', 'project_id']
                }).then(function(tasks) {
                    var projects = [];
                    //set project_id in activities, where task_id is projects.id
                    _.each(tasks, function(task) {
                        var activities = _.filter(work_activities, function(activity) {return activity.task_id[0] == task.id});
                        _.each(activities, function(activity) {
                            activity['project_id'] = task['project_id'];
                            if (!_.contains(projects, task['project_id'])) {
                                projects.push(task['project_id']);
                            }
                        });
                    });
                    self.project_timesheet_db.save("projects", projects);
                    self.project_timesheet_db.add_activities(work_activities);
                });
            });
        },
        set_screen_data: function(key,value){
            if(arguments.length === 2){
                this.screen_data[key] = value;
            }else if(arguments.length === 1){
                for(key in arguments[0]){
                    this.screen_data[key] = arguments[0][key];
                }
            }
        },
        //return screen data based on key passed
        get_screen_data: function(key){
            return this.screen_data[key];
        },
        save_to_server: function() {
            //TO Implement, this method will save data to server
        },
        flush_data: function() {
            //TO Implement, this method will flush localstorage data once it has been sync
        },
        //Note here
        //Here we will have logic of add projects, which will add project models' instance in this.get('projects').add(project)
    });

}