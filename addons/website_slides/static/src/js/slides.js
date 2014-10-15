(function () {
    "use strict";
    var website = openerp.website;
    var _t = openerp._t;
    website.slide = {};
    website.slide.template = website.add_template_file('/website_slides/static/src/xml/website_slides.xml');
    website.slide.Dialog = openerp.Widget.extend({
        template: 'website.slide.dialog',
        events: {
            'hidden.bs.modal': 'destroy',
            'click button.save': 'save',
            'click button[data-dismiss="modal"]': 'cancel',
            'change .slide-upload': 'slide_upload',
            'change .slide-url': 'slide_url',
            'click .list-group-item': function (ev) {
                this.$('.list-group-item').removeClass('active');
                $(ev.target).closest('li').addClass('active');
            }
        },
        init: function (el, channel_id, category_id) {
            this._super();
            this.channel_id = parseInt(channel_id, 10);
            this.category_id = parseInt(category_id) || false;
            this.file = {};
            this.index_content = "";
        },
        set_category: function () {
            var self = this;
            this.$('.load-category').show();
            this.$('.modal-footer, .modal-body').hide();

            return openerp.jsonRpc('/slides/get_category/' + self.channel_id, 'call')
                .then(function (data) {
                    self.$('.load-category').hide();
                    self.$('.modal-footer, .modal-body').show();
                    _.each(data, function (category) {
                        self.$('#category').append($('<option>', {
                            value: category.id,
                            text: category.name
                        }));
                    });
                    if (self.category_id) {
                        self.$('#category').val(self.category_id);
                    }
                });
        },
        start: function () {
            this.$el.modal({
                backdrop: 'static'
            });
            this.set_category();
            this.set_tags();
        },
        slide_url: function (ev) {
            var self = this;
            var url = $(ev.target).val();
            this.$('.url-error').hide();
            var video_id = this.url_parser(url);
            if (!video_id && url) {
                this.$('.url-error').show();
            } else {
                var constraint = this.check_constraint({
                    'video_id': video_id
                });
                var api_url = "https://www.googleapis.com/youtube/v3/videos?id=" + video_id + " &key=AIzaSyBKDzf7KjjZqwPWAME6JOeHzzBlq9nrpjk&part=snippet&fields=items(snippet/title, snippet/thumbnails/high/url)";
                $.getJSON(api_url, function (data) {
                    var title = data.items[0].snippet.title;
                    var image_src = data.items[0].snippet.thumbnails.high.url;
                    constraint.then(function (url) {
                        if (url) {
                            $('<div class="alert alert-warning" role="alert">This video already exists in this channel <a target="_blank" href=' + url + '>click here to view it </a></div>').insertBefore(self.$('form'));
                        } else {
                            self.$('#name').val(title);
                        }
                    });
                    self.$("#slide-image").attr("src", image_src);
                });
            }
        },
        check_constraint: function (values) {
            var self = this;
            _.extend(values, {
                'channel_id': self.channel_id
            });
            return openerp.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'ir.attachment',
                method: 'check_constraint',
                args: [false, values],
                kwargs: {},
            });
        },
        url_parser: function (url) {
            var regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*/;
            var match = url.match(regExp);
            return (match && match[7].length == 11) ? match[7] : false;
        },
        slide_upload: function (ev) {
            var self = this;
            var file = ev.target.files[0];
            this.file.name = file.name;
            this.file.type = file.type;
            var loaded = false;
            var BinaryReader = new FileReader();
            // file read as DataURL
            BinaryReader.readAsDataURL(file);
            BinaryReader.onloadend = function (upload) {
                var buffer = upload.target.result;

                self.$("#slide-image").attr("src", buffer);
                buffer = buffer.split(',')[1];
                self.file.data = buffer;
            };

            if (file.type === 'application/pdf') {
                var ArrayReader = new FileReader();
                this.$('.save').button('loading');
                // file read as ArrayBuffer for PDFJS get_Document API
                ArrayReader.readAsArrayBuffer(file);
                ArrayReader.onload = function (evt) {
                    var buffer = evt.target.result;
                    //PDFJS.workerSrc = '/website_slides/static/lib/pdfjs/build/pdf.worker.js';

                    PDFJS.getDocument(buffer).then(function getPdf(pdf) {
                        pdf.getPage(1).then(function getFirstPage(page) {
                            var scale = 1;
                            var viewport = page.getViewport(scale);
                            var canvas = document.getElementById('the-canvas');
                            var context = canvas.getContext('2d');
                            canvas.height = viewport.height;
                            canvas.width = viewport.width;
                            // Render PDF page into canvas context
                            page.render({
                                canvasContext: context,
                                viewport: viewport
                            }).then(function () {
                                var image_data = self.$('#the-canvas')[0].toDataURL();
                                self.$("#slide-image").attr("src", image_data);
                                if (loaded) {
                                    self.$('.save').button('reset');
                                }
                                loaded = true;

                            });
                        });
                        var maxPages = pdf.pdfInfo.numPages;
                        self.index_content = "";
                        for (var j = 1; j <= maxPages; j++) {
                            var page = pdf.getPage(j);
                            page.then(function (p) {
                                var page_number = p.pageInfo.pageIndex + 1;
                                p.getTextContent().then(function (data) {
                                    var page_content = '';
                                    _.each(data.items, function (obj) {
                                        page_content = page_content + obj.str + " ";
                                    });
                                    self.index_content = self.index_content + page_number + ". " + page_content + '\n';
                                    if (maxPages == page_number) {
                                        if (loaded) {
                                            self.$('.save').button('reset');
                                        }
                                        loaded = true;
                                    }
                                });
                            });
                        }
                    });
                };
            }

            var input = file.name;
            var input_val = input.substr(0, input.lastIndexOf('.')) || input;
            this.$('.alert-warning').remove();
            this.check_constraint({
                'file_name': input_val
            }).then(function (value) {
                if (value) {
                    $('<div class="alert alert-warning" role="alert">Channel contains the given title, please change before Save or Publish.</div>').insertBefore(self.$('form'));
                }
                self.$('#name').val(input_val);
            });
        },
        set_tags: function () {
            var self = this;
            this.$("input.slide-tags").textext({
                plugins: 'tags focus autocomplete ajax',
                keys: {
                    8: 'backspace',
                    9: 'tab',
                    13: 'enter!',
                    27: 'escape!',
                    37: 'left',
                    38: 'up!',
                    39: 'right',
                    40: 'down!',
                    46: 'delete',
                    108: 'numpadEnter',
                    32: 'whitespace!'
                },
                ajax: {
                    url: '/slides/get_tags',
                    dataType: 'json',
                    cacheResults: true,
                },
            });
            // Adds: create tags on space + blur
            $("input.slide-tags").on('whitespaceKeyDown blur', function () {
                $(this).textext()[0].tags().addTags([$(this).val()]);
                $(this).val("");
            });
            $("input.slide-tags").on('isTagAllowed', function (e, data) {
                if (_.indexOf($(this).textext()[0].tags()._formData, data.tag) != -1) {
                    data.result = false;
                }
            });

        },
        get_value: function () {
            var self = this;
            var default_val = {
                'is_slide': true,
                'website_published': false
            };
            var values = {};
            var canvas = this.$('#the-canvas')[0];
            if (self.file.type === 'application/pdf') {
                _.extend(values, {
                    'image': canvas.toDataURL().split(',')[1],
                    'width': canvas.width,
                    'height': canvas.height,
                    'index_content': self.index_content
                });
            }
            _.extend(values, {
                'name': this.$('#name').val(),
                'tag_ids': this.$('.slide-tags').textext()[0].tags()._formData,
                'datas': self.file.data || '',
                'datas_fname': self.file.name || '',
                'mimetype': self.file.type,
                'url': this.$('#url').val(),
                'channel_id': self.channel_id || '',
                'category_id': this.$('#category').val(),
                'description': this.$('#description').val()
            });
            return _.extend(values, default_val);
        },
        validate: function () {
            this.$('.control-group').removeClass('has-error');
            if (!this.$('#name').val()) {
                this.$('#name').closest('.control-group').addClass('has-error');
                return false;
            }
            if (!(this.file.name || this.$('#url').val())) {
                this.$('#url').closest('.control-group').addClass('has-error');
                return false;
            }
            return true;
        },
        save: function (ev) {
            var self = this;
            if (this.validate()) {
                var values = this.get_value();
                if ($(ev.target).data('published')) {
                    _.extend(values, {
                        'website_published': true
                    });
                }
                this.$('.slide-loading').show();
                this.$('.modal-footer, .modal-body').hide();
                openerp.jsonRpc("/slides/add_slide", 'call', values).then(function (data) {
                    if (data.error) {
                        self.$('.alert-warning').remove();
                        $('<div class="alert alert-danger" role="alert">' + data.error + '</div>').insertBefore(self.$('form'));
                        self.$('.slide-loading').hide();
                        self.$('.modal-footer, .modal-body').show();

                    } else {
                        window.location = data.url;
                    }
                });
            }
        },
        cancel: function () {
            this.trigger("cancel");
        },
    });



    website.slide.PDFViewer_Launcher = function ($PDFViewer) {
        website.slide.template.then(function () {
            var file = $PDFViewer.attr('file'),
                id = $PDFViewer.attr('slide-id');
            if (file) {
                var PDFViewer = new website.slide.PDFViewer(id, file);
                PDFViewer.replace($PDFViewer);
                website.slide.PDFViewer_inst = PDFViewer;
            }
        });

    };

    website.slide.PDFViewer = openerp.Widget.extend({
        template: 'website.slide.PDFViewer',
        events: {
            'click #next': 'next',
            'click #previous': 'previous',
            'click #last': 'last',
            'click #first': 'first',
            'click #fullscreen': 'fullscreen',
            'change #page_number': 'change_page_number',
        },
        init: function (id, file) {
            this.id = id;
            this.file = file;
            this.file_content = null;
            this.scale = 1.5;
            this.page_number = 1;
            this.rendering = false;
            this.loaded = false;
        },
        start: function () {
            this.canvas = this.$('canvas')[0];
            this.ctx = this.canvas.getContext('2d');
            this.load_file();
        },
        load_file: function () {
            var self = this;
            PDFJS.getDocument(this.file).then(function (file_content) {
                self.file_content = file_content;
                self.page_count = file_content.numPages;
                self.loaded = true;
                self.$('#PDFLoading, #PDFLoader').hide();
                self.$('#PDFViewer').show();
                self.$('#page_count').text(self.page_count);
                self.render_page();
            });
        },
        is_loaded: function(){
            if(!this.loaded){
                this.$('#PDFLoading').show();
                this.$('#PDFViewer-image').css({'opacity':0.2});
                return false;
            }
            return true;
        },
        render_page: function (page_number) {
            var self = this;
            var page_num = page_number || self.page_number;
            this.file_content.getPage(page_num).then(function (page) {
                var viewport = page.getViewport(self.scale);
                self.canvas.width = viewport.width;
                self.canvas.height = viewport.height;

                var renderContext = {
                    canvasContext: self.ctx,
                    viewport: viewport
                };
                self.rendering = true;
                page.render(renderContext).then(function () {
                    self.rendering = false;
                    self.$('#page_number').val(page_num);
                    self.page_number = page_num;
                });
            });
        },
        next: function (ev) {
            ev.preventDefault();
            if (!this.is_loaded()){
                return;
            }
            if (this.page_number === this.page_count) {
                this.fetch_next_slide();
            }
            if (this.page_number >= this.page_count) {
                return;
            }
            this.page_number += 1;
            if (!this.rendering) {
                this.render_page();
            }
        },
        fetch_next_slide: function () {
            var self = this;
            var id = parseInt(self.id, 10);
            var context = website.get_context();
            openerp.jsonRpc('/slides/overlay/' + id, 'call')
                .then(function (data) {
                    self.$(".slide-overlay").remove();
                    $(openerp.qweb.render("website.slide.overlay", {
                        slides: data
                    })).appendTo(self.$(".slide-wrapper"));
                    self.$('.slide-thumbnail').hover(
                        function () {
                            $(this).find('.slide-caption').stop().slideDown(250); //.fadeIn(250)
                        },
                        function () {
                            $(this).find('.slide-caption').stop().slideUp(250); //.fadeOut(205)
                        }
                    );
                });
        },
        previous: function (ev) {
            ev.preventDefault();
            if (!this.is_loaded()){
                return;
            }
            if (this.page_number <= 1) {
                return;
            }
            this.page_number -= 1;
            if (!this.rendering) {
                this.render_page();
            }
        },
        first: function (ev) {
            ev.preventDefault();
            if (!this.is_loaded()){
                return;
            }
            this.page_number = 1;
            if (!this.rendering) {
                this.render_page();
            }
        },
        last: function (ev) {
            ev.preventDefault();
            if (!this.is_loaded()){
                return;
            }
            this.page_number = this.page_count;
            if (!this.rendering) {
                this.render_page();
            }
        },
        fullscreen: function (ev) {
            ev.preventDefault();
            //TODO: Display warning when broswer not support native fullscreen API
            website.fullScreenAPI.requestFullScreen(this.canvas);
        },
        change_page_number: function (ev) {
            var page_asked = parseInt(ev.target.value, 10);
            this.page_number = (page_asked > 0 && page_asked <= this.page_count) ? page_asked : this.page_count;
            if (!this.rendering) {
                this.render_page();
            }
        }

    });

    //Export fullscreen Browser Compatible API to website namespace
    var fullScreenApi = {
            supportsFullScreen: false,
            isFullScreen: function () {
                return false;
            },
            requestFullScreen: function () {},
            cancelFullScreen: function () {},
            fullScreenEventName: '',
            prefix: ''
        },
        browserPrefixes = 'webkit moz o ms khtml'.split(' ');

    // check for native support
    if (typeof document.cancelFullScreen != 'undefined') {
        fullScreenApi.supportsFullScreen = true;
    } else {
        // check for fullscreen support by vendor prefix
        for (var i = 0, il = browserPrefixes.length; i < il; i++) {
            fullScreenApi.prefix = browserPrefixes[i];

            if (typeof document[fullScreenApi.prefix + 'CancelFullScreen'] != 'undefined') {
                fullScreenApi.supportsFullScreen = true;
                break;
            }
        }
    }

    if (fullScreenApi.supportsFullScreen) {
        fullScreenApi.fullScreenEventName = fullScreenApi.prefix + 'fullscreenchange';

        fullScreenApi.isFullScreen = function () {
            switch (this.prefix) {
            case '':
                return document.fullScreen;
            case 'webkit':
                return document.webkitIsFullScreen;
            default:
                return document[this.prefix + 'FullScreen'];
            }
        };
        fullScreenApi.requestFullScreen = function (el) {
            return (this.prefix === '') ? el.requestFullScreen() : el[this.prefix + 'RequestFullScreen']();
        };
        fullScreenApi.cancelFullScreen = function (el) {
            return (this.prefix === '') ? document.cancelFullScreen() : document[this.prefix + 'CancelFullScreen']();
        };
    }

    website.fullScreenAPI = fullScreenApi;

})();

$(document).ready(function () {
    var website = openerp.website;
    website.slide.PDFViewer_Launcher($('#PDFViewer'));
    $("timeago.timeago").timeago();

    $('.slide-container').on('click', function (ev) {
        window.location = $(this).find("a").attr("href");
    });
    $('.slide-tabs').on('click', function (ev) {
        ev.preventDefault();
        window.location = $(this).attr('href');
    });

    $('.slide-like, .slide-unlike').on('click', function (ev) {
        ev.preventDefault();
        var link_id = $(this).attr('id');
        var attachment_id = $(this).attr('attachment-id');
        var user_id = $(this).attr('user-id');
        var $link = $(ev.currentTarget);
        if (localStorage[link_id + '_' + attachment_id] != user_id) {
            openerp.jsonRpc($link.data('href'), 'call', {}).then(function (data) {
                $($link.data('count-el')).text(data);
            });
            localStorage[link_id + '_' + attachment_id] = user_id;
        } else {
            var $warning = $('<div class="alert alert-danger alert-dismissable oe_forum_alert" id="vote_alert">' +
                '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>' +
                'you have already voted for this slide' +
                '</div>');
            if ($link.parent().find('#vote_alert').length == 0) {
                $link.parent().append($warning);
            }
        }
    });
    $('.upload').on('click', function (ev) {
        var channel_id = $(this).attr('channel_id');
        var category_id = $(this).attr('category_id');
        new website.slide.Dialog(this, channel_id, category_id).appendTo(document.body);
    });

    $(document).keydown(function (ev) {
        if (ev.keyCode == 37) {
            website.slide.PDFViewer_inst.previous(ev);
        }
        if (ev.keyCode == 39) {
            website.slide.PDFViewer_inst.next(ev);
        }
    });

    website.slide.modifyembedcode = function (currentVal) {
        var $embed_input = $('.slide_embed_code');
        var slide_embed_code = $embed_input.val();
        var tmp_embed_code = slide_embed_code.replace(/(page=).*?([^\d]+)/, '$1' + currentVal + '$2');
        $embed_input.val(tmp_embed_code);
    };

    $('.embed-page-counter').on('change', function (e) {
        e.preventDefault();
        var currentVal = parseInt($(this).val());
        var maxval = parseInt($('#page_count').text());
        if (currentVal > 0 && currentVal <= maxval) {
            website.slide.modifyembedcode(currentVal);
        } else {
            $(this).val(1);
            website.slide.modifyembedcode(1);
        }
    });
    $(".js_follow_btn").on('follow', function (ev, $el, click_ev) {
        if (click_ev) {
            $el.find(".js_unfollow_btn, .js_follow_email").hide();
            $el.find(".alert-success").removeClass("hidden");
        }
    });
    $('.share-toggle-option').on('click', function (ev) {
        ev.preventDefault();
        var toggleDiv = $(this).data('slide-share');
        $(toggleDiv).slideToggle();
    });


    if ($('div#statistic').length) {
        var socialgatter = function (app_url, url, callback) {
            $.ajax({
                url: app_url + url,
                dataType: 'jsonp',
                success: callback
            });
        };
        var current_url = window.location.origin + window.location.pathname;
        socialgatter('http://www.linkedin.com/countserv/count/share?url=', current_url, function (data) {
            $('#linkedin-badge').text(data.count || 0);
            $('#total-share').text(parseInt($('#total-share').text()) + parseInt($('#linkedin-badge').text()));
        });
        socialgatter('http://cdn.api.twitter.com/1/urls/count.json?url=', current_url, function (data) {
            $('#twitter-badge').text(data.count || 0);
            $('#total-share').text(parseInt($('#total-share').text()) + parseInt($('#twitter-badge').text()));
        });
        socialgatter('http://graph.facebook.com/?id=', current_url, function (data) {
            $('#facebook-badge').text(data.shares || 0);
            $('#total-share').text(parseInt($('#total-share').text()) + parseInt($('#facebook-badge').text()));
        });

        $.ajax({
            url: 'https://clients6.google.com/rpc',
            type: "POST",
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify([{
                "method": "pos.plusones.get",
                "id": "p",
                "params": {
                    "nolog": true,
                    "id": current_url,
                    "source": "widget",
                    "userId": "@viewer",
                    "groupId": "@self"
                },
                "jsonrpc": "2.0",
                "key": "AIzaSyCFi7q20yMDmAZ9Qxmiu-zHPnxvIX0u2zM",
                "apiVersion": "v1"
            }]),
            success: function (data) {
                $('#google-badge').text(data[0].result.metadata.globalCounts.count || 0);
                $('#total-share').text(parseInt($('#total-share').text()) + parseInt($('#google-badge').text()));
            }
        });
    }

    $('.sendbymail').on('click', function (ev) {
        var $input = $(this).parent().prev(':input');
        if (!$input.val() || !$input[0].checkValidity()) {
            $input.closest('.form-group').addClass('has-error');
            $input.focus();
            return;
        }
        $input.closest('.form-group').removeClass('has-error');
        openerp.jsonRpc('/slides/sendbymail/' + $(this).attr('slide-id'), 'call', {
            email: $input.val()
        }).then(function (data) {
            $input.closest('.form-group').html($('<div class="alert alert-info" role="alert"><strong>Thank you!</strong> Mail has been sent.</div>'));
        });
    });
});
