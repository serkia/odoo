(function () {
    'use strict';

    var website = openerp.website;
    var _t = openerp._t;
    openerp.Tour.register({
        id:   'question',
        name: _t("Create a question"),
        steps: [
            {
                title:     _t("Create a Question!"),
                content:   _t("Let's go through the first steps to create a new question."),
                popover:   { next: _t("Start Tutorial"), end: _t("Skip It") },
            },
            {
                element:   '#content-menu-button',
                placement: 'left',
                title:     _t("Add Content"),
                content:   _t("Use this <em>'Content'</em> menu to create a new forum like any other document (page, menu, products, event, ...)."),
                popover:   { fixed: true },
            },
            {
                element:   'a[data-action=new_forum]',
                placement: 'left',
                title:     _t("New Forum"),
                content:   _t("Select this menu item to create a new forum."),
                popover:   { fixed: true },
            },
            {
            	onload:	function(tour){
            		$("#wrap").removeClass("js_forum");
            	},
                element:   '.modal #editor_new_forum input[type=text]',
                sampleText: 'New Forum',
                placement: 'right',
                title:     _t("Forum Name"),
                content:   _t("Enter a name for your new forum then click 'Continue'."),
            },
            {
                waitNot:   '.modal input[type=text]:not([value!=""])',
                element:   '.modal button.btn-primary',
                placement: 'right',
                title:     _t("Create Forum"),
                content:   _t("Click <em>Continue</em> to create the forum."),
            },
            {
                waitFor:   'body:has(button[data-action=edit]):has(.js_forum)',
                title:     _t("New Forum Created"),
                content:   _t("This page contains all the information related to the new forum."),
                popover:   { next: _t("Continue") },
            },
            {
                element:   '.btn-block',
                placement: 'left',
                title:     _t("Ask a Question"),
                content:   _t("Ask the question in this forum by clicking on the button."),
            },
            {
                element:   'input[name=question_name]',
                sampleText:'First Question',
                placement: 'top',
                title:     _t("Question Title"),
                content:   _t("Give your question title."),
            },
            {
                waitNot:   'input[name=question_name]:not([value!=""])',
                element:   '.cke_editor_content',
                placement: 'top',
                title:     _t("Question"),
                content:   _t("Put your question here."),
                onload: function (tour) {
                    $('iframe').removeClass("cke_wysiwyg_frame");
                    $("iframe").contents().find('html').bind({
                        keydown: function(){
                        	$('iframe').addClass("cke_wysiwyg_frame");
                        }
                    });
                },
            },
            {
                waitFor:   'body:has(".cke_wysiwyg_frame")',
                element:   '.load_tags',
                placement: 'top',
                title:     _t("Give Tag"),
                content:   _t("Insert tags related to your question."),
            },
            {
                waitNot:   '.text-wrap input[type=text]:not([value!=""])',
                element:   'button:contains("Post Your Question")',
                placement: 'bottom',
                title:     _t("Post Question"),
                content:   _t("Click to post your question."),
            },
            {
                waitFor:   'body:has(".oe_grey")',
                title:     _t("New Question Created"),
                content:   _t("This page contain new created question."),
                popover:   { next: _t("Continue") },
            },
            {
                element:   '.cke_editor_content',
                placement: 'top',
                title:     _t("Answer"),
                content:   _t("Put your answer here."),
                onload: function (tour) {
                    $('iframe').removeClass("cke_wysiwyg_frame");
                    $("iframe").contents().find('html').bind({
                        keydown: function(){
                        	$('iframe').addClass("cke_wysiwyg_frame");
                        }
                    });
                },
            },
            {
                waitFor:   'body:has(".cke_wysiwyg_frame")',
                element:   'button:contains("Post Your Answer")',
                placement: 'bottom',
                title:     _t("Post Answer"),
                content:   _t("Click to post your answer."),
            },
            {
                waitFor:   'body:has(".fa-check-circle")',
                title:     _t("Answer Posted"),
                content:   _t("This page contain new created question and its answer."),
                popover:   { next: _t("Continue") },
            },
            {
                element:   'a[data-oe-xpath="/t[1]/t[1]/div[2]/div[1]/div[1]/div[1]/a[1]"][data-karma="20"]',
                placement: 'right',
                title:     _t("Accept Answer"),
                content:   _t("Click here to accept this answer."),
            },
            {
                waitFor:   'body:has(".oe_answer_true")',
                title:     _t("Congratulations"),
                content:   _t("Congratulations! You just created and post your first question and answer."),
                popover:   { next: _t("Close Tutorial") },
            },
        ]
    });

    // website.EditorBar.include({
    //     start: function () {
    //         this.registerTour(new website.Tour.Forum(this));
    //         return this._super();
    //     },
    // });

    // website.Tour.Forum = website.Tour.extend({
    //     id: 'question',
    //     name: "Create a question",
    //     testPath: '/forum(/[0-9]+/register)?',
    //     init: function (editor) {
    //         var self = this;
    //         self.steps = [
    //             {
    //                 title:     _t("Create a question"),
    //                 content:   _t("Let's go through the first steps to create a new question."),
    //                 popover:   { next: _("Start Tutorial"), end: _("Skip It") },
    //             },
    //         ];
    //         return this._super();
    //     }
    // });

}());
