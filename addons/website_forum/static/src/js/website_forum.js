function open_share_dialog(social_network, text_to_share, url) {
    'use strict';
    var sharing_url, window_height, window_width;

    if (social_network === 'twitter') {
        sharing_url = 'https://twitter.com/intent/tweet?original_referer=' + encodeURIComponent(url) + '&amp;text=' + encodeURIComponent(text_to_share);
        window_height = '300';
        window_width = '600';
    } else if (social_network === 'linked-in') {
        sharing_url = 'https://www.linkedin.com/shareArticle?mini=true&url=' + encodeURIComponent(url) + '&title=' + encodeURIComponent(text_to_share) + '&summary=Odoo Forum&source=Odoo forum';
        window_height = '500';
        window_width = '600';
    } else if (social_network === 'facebook') {
        sharing_url = 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url);
        window_height = '600';
        window_width = '750';
    } else {
        return false;
    }
    window.open(sharing_url, '', 'menubar=no, toolbar=no, resizable=yes, scrollbar=yes, height=' + window_height + ',width=' + window_width);
    return false;
}

function redirect_user(form, isQuestion) {
    "use strict";
    var path = form.data("target"),
        title, body, redirect_url, vals, forum_id, post_id,
        _t = openerp._t;
    $.post(path, form.serializeArray(), function (result) {
        result = JSON.parse(result);
        forum_id = result.forum_id;
        if (isQuestion) {
            title = _t("Thanks for posting your Question !");
            body = _t("On average " + result.stat_data[forum_id].percentage + "% of the <b>questions shared on social networks</b> get an answer within " + result.stat_data[forum_id].average + " hours and questions shared on two social networks <b>have " + result.stat_data[forum_id].probability + "% more chance to get an answer</b> than not shared questions.");
        } else {
            title = _t('Thanks for posting your Answer !');
            body = _t("By sharing your answer, you will get " + result.karma + " additional karma points if your answer is selected as the right one.<a href='/forum/" + forum_id + "/faq'> See what you can do with karma.</a>");
        }
        redirect_url = "/forum/" + result.forum_id + "/question/" + result.question_id;
        $(".modal-title").text(title);
        $(".modal-body").prepend(body);
        if (result.answer_id) {
            post_id = result.answer_id;
        } else {
            post_id = result.question_id;
        }
        $("#share_dialog_box").data({
            "url" : redirect_url,
            "post_id" : post_id
        }).on('hidden.bs.modal', function () {
            window.location = redirect_url;
        }).modal("show");
    });
}

$(document).ready(function () {
    if ($('.website_forum').length){
        if ($("#promote_sharing").length) {
            var sharing_buttons = $("#promote_sharing").data("content");
            $("#promote_sharing_body").append($(sharing_buttons));
            $("#promote_sharing_body > " + sharing_buttons)
                .addClass("text-center").removeClass("collapse oe_comment_grey");
        }

        /*For Questions*/
        $('body').on('click', '.share_question_twitter', function () {
            var text_to_share, url, post_id,
                website_name = $(this).data('website_name'),
                hash_tags = ' #' + website_name + ' #question ';
            if ($(this).data("dialog")) {
                post_id = $("#share_dialog_box").data('post_id');
                url = location.origin + $('#share_dialog_box').data('url');
                text_to_share = $('#question_name_ask').val() + hash_tags + url;
            } else {
                post_id = $(this).data("id");
                url = location.origin + location.pathname;
                text_to_share = $('#question_name').text() + hash_tags + url;
            }
            open_share_dialog('twitter', text_to_share, url);
            if ($('.share_question_twitter').data('shared') === false) {
                openerp.jsonRpc('/forum/' + $(this).data('forum') + '/' + post_id + '/share', 'call', {'media' : 'twitter'})
                    .then(function () {
                        $('.share_question_twitter').data('shared', true);
                        return;
                    });
            }
            return;
        });

        $('body').on('click', ".share_question_facebook", function () {
            var url, post_id;
            if ($(this).data("dialog")) {
                post_id = $("#share_dialog_box").data('post_id');
                url = location.origin + $('#share_dialog_box').data('url') + '/dialog';
            } else {
                post_id = $(this).data("id");
                url = location.origin + location.pathname;
                if ($(this).data("author")) {
                    url = url + "/dialog";
                }
            }
            open_share_dialog('facebook', '', url);
            if ($('.share_question_facebook').data('shared') === false) {
                openerp.jsonRpc('/forum/' + $(this).data('forum') + '/' + post_id + '/share', 'call', {'media' : 'facebook'})
                    .then(function () {
                        $('.share_question_facebook').data('shared', true);
                        return;
                    });
            }
            return;
        });

        $('body').on('click', ".share_question_linked_in", function () {
            var text_to_share, url, post_id;
            if ($(this).data("dialog")) {
                post_id = $("#share_dialog_box").data('post_id');
                url = location.origin + $('#share_dialog_box').data('url');
                text_to_share = $('#question_name_ask').val() + ' : ' + url;
            } else {
                post_id = $(this).data("id");
                url = location.origin + location.pathname;
                text_to_share = $('#question_name').text() + ' : ' + url;
            }
            open_share_dialog('linked-in', text_to_share, url);
            if ($('.share_question_linked_in').data('shared') === false) {
                openerp.jsonRpc('/forum/' + $(this).data('forum') + '/' +  post_id + '/share', 'call', {'media' : 'linked_in'})
                    .then(function () {
                        $('.share_question_linked_in').data('shared', true);
                        return;
                    });
            }
            return;
        });

        /*For Answers*/
        $('body').on('click', ".share_answer_twitter", function () {
            var text_to_share, hash_tag, post_id,
                url = location.origin + location.pathname,
                website_name = $(this).data('website_name') + ' ',
                question_name = $('#question_name').text().replace('?', '');
            if ($(this).data("dialog")) {
                post_id = $("#share_dialog_box").data('post_id');
                hash_tag = "#answered";
            } else {
                post_id = $(this).data("id");
                if ($(this).data("author")) {
                    hash_tag = "#answered";
                } else {
                    hash_tag = "#answer";
                }
            }
            text_to_share = question_name + '? ' + hash_tag + ' #' + website_name + url;
            open_share_dialog('twitter', text_to_share, url);
            if ($('.share_answer_twitter').data('shared') === false) {
                openerp.jsonRpc('/forum/' + $(this).data('forum') + '/' + post_id + '/share', 'call', {'media' : 'twitter'})
                    .then(function () {
                        $('.share_answer_twitter').data('shared', true);
                        return;
                    });
            }
            return;
        });

        $('body').on('click', ".share_answer_facebook", function () {
            var post_id,
                url = location.origin + location.pathname + '/answer/';
            if ($(this).data("dialog")) {
                post_id = $("#share_dialog_box").data('post_id');
                url = url + post_id + '/dialog/no_author';
            } else {
                post_id = $(this).data("id");
                url = url + post_id;
                if ($(this).data("author")) {
                    url = url + '/no_dialog/author';
                } else {
                    url = url + '/no_dialog/no_author';
                }
            }
            open_share_dialog('facebook', '', url);
            if ($('.share_answer_facebook').data('shared') === false) {
                openerp.jsonRpc('/forum/' + $(this).data('forum') + '/' + post_id + '/share', 'call', {'media' : 'facebook'})
                    .then(function () {
                        $('.share_answer_facebook').data('shared', true);
                        return;
                    });
            }
            return;
        });

        $('body').on('click', ".share_answer_linked_in", function () {
            var text, post_id, text_to_share,
                url = location.origin + location.pathname;
            if ($(this).data("dialog")) {
                post_id = $("#share_dialog_box").data('post_id');
                text = 'Find my answer for ';
            } else {
                if ($(this).data("author")) {
                    text = 'Find my answer for ';
                } else {
                    text = 'Find an interesting answer to ';
                }
                post_id = $(this).data("id");
            }
            text_to_share = text + $('#question_name').text() + ' on ' + url;
            open_share_dialog('linked-in', text_to_share, url);
            if ($('.share_answer_linkeg_in').data('shared') === false) {
                openerp.jsonRpc('/forum/' + $(this).data('forum') + '/' + post_id + '/share', 'call', {'media' : 'linked_in'})
                    .then(function () {
                        $('.share_answer_linked_in').data('shared', true);
                        return;
                    });
            }
            return;
        });

        $(":not(li .share_link)").click(function () {
            $("li .share_link").popover("hide");
        });

        $("li .share_link").click(function (e) {
            e.stopPropagation();
        });

        $("li .share_link").each(function () {
            var target = $(this).data('target');
            $(this).popover({
                html : true,
                content : function() {
                    return $(target).html();
                }
            });
        });

        $(".tag_text").submit(function (event) {
            event.preventDefault();
            CKEDITOR.instances['content'].destroy();
            redirect_user($(this), true);
        });

        $("#forum_post_answer").submit(function (event) {
            event.preventDefault();
            var ckeditor = $(this).children('.load_editor').attr('id');
            CKEDITOR.instances[ckeditor].destroy();
            redirect_user($(this), false);
        });

        $('.karma_required').on('click', function (ev) {
            var karma = $(ev.currentTarget).data('karma');
            if (karma) {
                ev.preventDefault();
                var $warning = $('<div class="alert alert-danger alert-dismissable oe_forum_alert" id="karma_alert">'+
                    '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                    karma + ' karma is required to perform this action. You can earn karma by answering questions or having '+
                    'your answers upvoted by the community.</div>');
                var vote_alert = $(ev.currentTarget).parent().find("#vote_alert");
                if (vote_alert.length == 0) {
                    $(ev.currentTarget).parent().append($warning);
                }
            }
        });

        $('.vote_up,.vote_down').not('.karma_required').on('click', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            openerp.jsonRpc($link.data('href'), 'call', {})
                .then(function (data) {
                    if (data['error']){
                        if (data['error'] == 'own_post'){
                            var $warning = $('<div class="alert alert-danger alert-dismissable oe_forum_alert" id="vote_alert">'+
                                '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                                'Sorry, you cannot vote for your own posts'+
                                '</div>');
                        } else if (data['error'] == 'anonymous_user'){
                            var $warning = $('<div class="alert alert-danger alert-dismissable oe_forum_alert" id="vote_alert">'+
                                '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                                'Sorry you must be logged to vote'+
                                '</div>');
                        }
                        vote_alert = $link.parent().find("#vote_alert");
                        if (vote_alert.length == 0) {
                            $link.parent().append($warning);
                        }
                    } else {
                        $link.parent().find("#vote_count").html(data['vote_count']);
                        if (data['user_vote'] == 0) {
                            $link.parent().find(".text-success").removeClass("text-success");
                            $link.parent().find(".text-warning").removeClass("text-warning");
                        } else {
                            if (data['user_vote'] == 1) {
                                $link.addClass("text-success");
                            } else {
                                $link.addClass("text-warning");
                            }
                        }
                    }
                });
            return true;
        });

        $('.accept_answer').not('.karma_required').on('click', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            openerp.jsonRpc($link.data('href'), 'call', {}).then(function (data) {
                if (data['error']) {
                    if (data['error'] == 'anonymous_user') {
                        var $warning = $('<div class="alert alert-danger alert-dismissable" id="correct_answer_alert" style="position:absolute; margin-top: -30px; margin-left: 90px;">'+
                            '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                            'Sorry, anonymous users cannot choose correct answer.'+
                            '</div>');
                    }
                    correct_answer_alert = $link.parent().find("#correct_answer_alert");
                    if (correct_answer_alert.length == 0) {
                        $link.parent().append($warning);
                    }
                } else {
                    if (data) {
                        $link.addClass("oe_answer_true").removeClass('oe_answer_false');
                    } else {
                        $link.removeClass("oe_answer_true").addClass('oe_answer_false');
                    }
                }
            });
            return true;
        });

        $('.favourite_question').on('click', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            openerp.jsonRpc($link.data('href'), 'call', {}).then(function (data) {
                if (data) {
                    $link.addClass("forum_favourite_question")
                } else {
                    $link.removeClass("forum_favourite_question")
                }
            });
            return true;
        });

        $('.comment_delete').on('click', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            openerp.jsonRpc($link.data('href'), 'call', {}).then(function (data) {
                $link.parents('.comment').first().remove();
            });
            return true;
        });

        $('.notification_close').on('click', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            openerp.jsonRpc("/forum/notification_read", 'call', {
                'notification_id': $link.attr("id")})
            return true;
        });

        $('.js_close_intro').on('click', function (ev) {
            ev.preventDefault();
            document.cookie = "no_introduction_message = false";
            return true;
        });

        $('.link_url').on('change', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            if ($link.attr("value").search("^http(s?)://.*")) {
                var $warning = $('<div class="alert alert-danger alert-dismissable" style="position:absolute; margin-top: -180px; margin-left: 90px;">'+
                    '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                    'Please enter valid URl.'+
                    '</div>');
                $link.parent().append($warning);
                $link.parent().find("button#btn_post_your_article")[0].disabled = true;
                $link.parent().find("input[name='content']")[0].value = '';
            } else {
                openerp.jsonRpc("/forum/get_url_title", 'call', {'url': $link.attr("value")}).then(function (data) {
                    $link.parent().find("input[name='content']")[0].value = data;
                    $('button').prop('disabled', false);
                    $('input').prop('readonly', false);
                });
            }
        });

        function set_tags(tags) {
            $("input.load_tags").textext({
                plugins: 'tags focus autocomplete ajax',
                ext: {
                    autocomplete: {
                        onSetSuggestions : function(e, data) {
                            var self        = this,
                                val         = self.val(),
                                suggestions = self._suggestions = data.result;
                            if(data.showHideDropdown !== false)
                                self.trigger(suggestions === null || suggestions.length === 0 && val.length === 0 ? "hideDropdown" : "showDropdown");
                        },
                        renderSuggestions: function(suggestions) {
                            var self = this,
                                val  = self.val();
                            self.clearItems();
                            $.each(suggestions || [], function(index, item) {
                                self.addSuggestion(item);
                            });
                            var lowerCasesuggestions = $.map(suggestions, function(n,i){return n.toLowerCase();});
                            if(jQuery.inArray(val.toLowerCase(), lowerCasesuggestions) ==-1) {
                                self.addSuggestion("Create '" + val + "'");
                            }
                        },
                    },
                    tags: {
                        onEnterKeyPress: function(e) {
                            var self = this,
                                val  = self.val(),
                                tag  = self.itemManager().stringToItem(val);

                            if(self.isTagAllowed(tag)) {
                                tag = tag.replace(/Create\ '|\'|'/g,'');
                                self.addTags([ tag ]);
                                // refocus the textarea just in case it lost the focus
                                self.core().focusInput();
                            }
                        },
                    }
                },
                tagsItems: tags.split(","),
                //Note: The following list of keyboard keys is added. All entries are default except {32 : 'whitespace!'}.
                keys: {8: 'backspace', 9: 'tab', 13: 'enter!', 27: 'escape!', 37: 'left', 38: 'up!', 39: 'right',
                    40: 'down!', 46: 'delete', 108: 'numpadEnter', 32: 'whitespace'},
                ajax: {
                    url: '/forum/get_tags',
                    dataType: 'json',
                    cacheResults: true
                }
            });

            $("input.load_tags").on('isTagAllowed', function(e, data) {
                if (_.indexOf($(this).textext()[0].tags()._formData, data.tag) != -1) {
                    data.result = false;
                }
            });
        }
        if($('input.load_tags').length){
            var tags = $("input.load_tags").val();
            $("input.load_tags").val("");
            set_tags(tags);
        };
        if ($('textarea.load_editor').length) {
            $('textarea.load_editor').each(function () {
                if (this['id']) {
                    CKEDITOR.replace(this['id']).on('instanceReady', CKEDITORLoadComplete);
                }
            });
        }
    }
});


function IsKarmaValid(eventNumber,minKarma){
    "use strict";
    if(parseInt($("#karma").val()) >= minKarma){
        CKEDITOR.tools.callFunction(eventNumber,this);
        return false;
    } else {
        alert("Sorry you need more than " + minKarma + " Karma.");
    }
}

function CKEDITORLoadComplete(){
    "use strict";
    $('.cke_button__link').attr('onclick','IsKarmaValid(33,30)');
    $('.cke_button__unlink').attr('onclick','IsKarmaValid(37,30)');
    $('.cke_button__image').attr('onclick','IsKarmaValid(41,30)');
}
