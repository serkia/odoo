(function () {
    'use strict';

    var website = openerp.website;
    var _t = openerp._t;
    if ('function' !== typeof Array.prototype.reduce) {
        /**
         * Array.prototype.reduce fallback
         *
         * https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/Reduce
         */
        Array.prototype.reduce = function (callback, optInitialValue) {
          var idx, value, length = this.length >>> 0, isValueSet = false;
          if (1 < arguments.length) {
            value = optInitialValue;
            isValueSet = true;
          }
          for (idx = 0; length > idx; ++idx) {
            if (this.hasOwnProperty(idx)) {
              if (isValueSet) {
                value = callback(value, this[idx], idx, this);
              } else {
                value = this[idx];
                isValueSet = true;
              }
            }
          }
          if (!isValueSet) {
            throw new TypeError('Reduce of empty array with no initial value');
          }
          return value;
        };
    }
    /**
    * Object which check platform and agent
    */
    var agent = {
        bMac: navigator.appVersion.indexOf('Mac') > -1,
        bMSIE: navigator.userAgent.indexOf('MSIE') > -1 || navigator.userAgent.indexOf('Trident') > -1,
        bFF: navigator.userAgent.indexOf('Firefox') > -1,
        jqueryVersion: parseFloat($.fn.jquery),
    };
    /**
    * func utils (for high-order func's arg)
    */
    var func = (function () {
        var eq = function (elA) {
            return function (elB) {
                return elA === elB;
            };
        };

        var eq2 = function (elA, elB) {
            return elA === elB;
        };

        var ok = function () {
            return true;
        };

        var fail = function () {
            return false;
        };

        var not = function (f) {
            return function () {
                return !f.apply(f, arguments);
            };
        };

        var self = function (a) {
            return a;
        };

        var idCounter = 0;

        /**
        * generate a globally-unique id
        *
        * @param {String} [prefix]
        */
        var uniqueId = function (prefix) {
            var id = ++idCounter + '';
            return prefix ? prefix + id : id;
        };

        /**
         * returns bnd (bounds) from rect
         *
         * - IE Compatability Issue: http://goo.gl/sRLOAo
         * - Scroll Issue: http://goo.gl/sNjUc
         *
         * @param {Rect} rect
         * @return {Object} bounds
         * @return {Number} bounds.top
         * @return {Number} bounds.left
         * @return {Number} bounds.width
         * @return {Number} bounds.height
         */
        var rect2bnd = function (rect) {
            var $document = $(document);
            return {
                top: rect.top + $document.scrollTop(),
                left: rect.left + $document.scrollLeft(),
                width: rect.right - rect.left,
                height: rect.bottom - rect.top
            };
        };

        /**
        * returns a copy of the object where the keys have become the values and the values the keys.
        * @param {Object} obj
        * @return {Object}
        */
        var invertObject = function (obj) {
            var inverted = {};
            for (var key in obj) {
                if (obj.hasOwnProperty(key)) {
                inverted[obj[key]] = key;
                }
            }
            return inverted;
        };

        return {
            eq: eq,
            eq2: eq2,
            ok: ok,
            fail: fail,
            not: not,
            self: self,
            uniqueId: uniqueId,
            rect2bnd: rect2bnd,
            invertObject: invertObject
        };
    })();

    /**
    * list utils
    */
    var list = (function () {
        /**
        * returns the first element of an array.
        * @param {Array} array
        */
        var head = function (array) {
            return array[0];
        };

        /**
        * returns the last element of an array.
        * @param {Array} array
        */
        var last = function (array) {
            return array[array.length - 1];
        };

        /**
        * returns everything but the last entry of the array.
        * @param {Array} array
        */
        var initial = function (array) {
            return array.slice(0, array.length - 1);
        };

        /**
        * returns the rest of the elements in an array.
        * @param {Array} array
        */
        var tail = function (array) {
            return array.slice(1);
        };

        /**
        * returns next item.
        * @param {Array} array
        */
        var next = function (array, item) {
            var idx = array.indexOf(item);
            if (idx === -1) { return null; }
            return array[idx + 1];
        };

        /**
        * returns prev item.
        * @param {Array} array
        */
        var prev = function (array, item) {
            var idx = array.indexOf(item);
            if (idx === -1) { return null; }
            return array[idx - 1];
        };
  
        /**
        * get sum from a list
        * @param {Array} array - array
        * @param {Function} fn - iterator
        */
        var sum = function (array, fn) {
            fn = fn || func.self;
            return array.reduce(function (memo, v) {
                return memo + fn(v);
            }, 0);
        };
  
        /**
        * returns a copy of the collection with array type.
        * @param {Collection} collection - collection eg) node.childNodes, ...
        */
        var from = function (collection) {
            var result = [], idx = -1, length = collection.length;
            while (++idx < length) {
                result[idx] = collection[idx];
            }
            return result;
        };

        /**
        * cluster elements by predicate function.
        * @param {Array} array - array
        * @param {Function} fn - predicate function for cluster rule
        * @param {Array[]}
        */
        var clusterBy = function (array, fn) {
            if (array.length === 0) { return []; }
            var aTail = tail(array);
            return aTail.reduce(function (memo, v) {
                var aLast = last(memo);
                if (fn(last(aLast), v)) {
                  aLast[aLast.length] = v;
                } else {
                  memo[memo.length] = [v];
                }
                return memo;
            }, [[head(array)]]);
        };
  
        /**
        * returns a copy of the array with all falsy values removed
        * @param {Array} array - array
        * @param {Function} fn - predicate function for cluster rule
        */
        var compact = function (array) {
            var aResult = [];
            for (var idx = 0, sz = array.length; idx < sz; idx ++) {
                if (array[idx]) { aResult.push(array[idx]); }
            }
            return aResult;
        };
  
        return { head: head, last: last, initial: initial, tail: tail,
                 prev: prev, next: next, sum: sum, from: from,
                 compact: compact, clusterBy: clusterBy };
    })();
    /**
    * Dom functions
    */
    var dom = (function () {
        /**
         * returns whether node is `note-editable` or not.
         *
         * @param {Element} node
         * @return {Boolean}
         */
        var isEditable = function (node) {
            return node && $(node).hasClass('note-editable');
        };

        var isControlSizing = function (node) {
            return node && $(node).hasClass('note-control-sizing');
        };

        /**
        * build layoutInfo from $editor(.note-editor)
        *
        * @param {jQuery} $editor
        * @return {Object}
        */
        var buildLayoutInfo = function ($editor) {
            var makeFinder;

            // air mode
            if ($editor.hasClass('note-air-editor')) {
                var id = list.last($editor.attr('id').split('-'));
                makeFinder = function (sIdPrefix) {
                    return function () { return $(sIdPrefix + id); };
                };

            return {
            editor: function () { return $editor; },
            editable: function () { return $editor; },
            popover: makeFinder('#note-popover-'),
            handle: makeFinder('#note-handle-'),
            dialog: makeFinder('#note-dialog-')
            };

            // frame mode
            } else {
                makeFinder = function (sClassName) {
                    return function () { return $editor.find(sClassName); };
                    };
                return {
                    editor: function () { return $editor; },
                    dropzone: makeFinder('.note-dropzone'),
                    toolbar: makeFinder('.note-toolbar'),
                    editable: makeFinder('.note-editable'),
                    codable: makeFinder('.note-codable'),
                    statusbar: makeFinder('.note-statusbar'),
                    popover: makeFinder('.note-popover'),
                    handle: makeFinder('.note-handle'),
                    dialog: makeFinder('.note-dialog')
                };
            }
        };

        /**
        * returns predicate which judge whether nodeName is same
        * @param {String} sNodeName
        */
        var makePredByNodeName = function (sNodeName) {
        // nodeName is always uppercase.
            return function (node) {
                return node && node.nodeName === sNodeName;
            };
        };

        var isPara = function (node) {
            // Chrome(v31.0), FF(v25.0.1) use DIV for paragraph
            return node && /^DIV|^P|^LI|^H[1-7]/.test(node.nodeName);
        };

        var isList = function (node) {
            return node && /^UL|^OL/.test(node.nodeName);
        };

        var isCell = function (node) {
            return node && /^TD|^TH/.test(node.nodeName);
        };

        /**
        * find nearest ancestor predicate hit
        *
        * @param {Element} node
        * @param {Function} pred - predicate function
        */
        var ancestor = function (node, pred) {
            while (node) {
                if (pred(node)) { return node; }
                if (isEditable(node)) { break; }

                node = node.parentNode;
            }
            return null;
        };

        /**
        * returns new array of ancestor nodes (until predicate hit).
        *
        * @param {Element} node
        * @param {Function} [optional] pred - predicate function
        */
        var listAncestor = function (node, pred) {
            pred = pred || func.fail;
            var aAncestor = [];
            ancestor(node, function (el) {
                aAncestor.push(el);
                return pred(el);
            });
            return aAncestor;
        };

        /**
        * returns common ancestor node between two nodes.
        *
        * @param {Element} nodeA
        * @param {Element} nodeB
        */
        var commonAncestor = function (nodeA, nodeB) {
            var aAncestor = listAncestor(nodeA);
            for (var n = nodeB; n; n = n.parentNode) {
                if ($.inArray(n, aAncestor) > -1) { return n; }
            }
            return null; // difference document area
        };

        /**
        * listing all Nodes between two nodes.
        * FIXME: nodeA and nodeB must be sorted, use comparePoints later.
        *
        * @param {Element} nodeA
        * @param {Element} nodeB
        */
        var listBetween = function (nodeA, nodeB) {
            var aNode = [];

            var bStart = false, bEnd = false;

            // DFS(depth first search) with commonAcestor.
            (function fnWalk(node) {
                if (!node) { return; } // traverse fisnish
                if (node === nodeA) { bStart = true; } // start point
                if (bStart && !bEnd) { aNode.push(node); } // between
                if (node === nodeB) { bEnd = true; return; } // end point

                for (var idx = 0, sz = node.childNodes.length; idx < sz; idx++) {
                  fnWalk(node.childNodes[idx]);
                }
            })(commonAncestor(nodeA, nodeB));
            return aNode;
        };

        /**
        * listing all previous siblings (until predicate hit).
        * @param {Element} node
        * @param {Function} [optional] pred - predicate function
        */
        var listPrev = function (node, pred) {
            pred = pred || func.fail;

            var aNext = [];
            while (node) {
                aNext.push(node);
                if (pred(node)) { break; }
                node = node.previousSibling;
            }
            return aNext;
        };

        /**
        * listing next siblings (until predicate hit).
        *
        * @param {Element} node
        * @param {Function} [pred] - predicate function
        */
        var listNext = function (node, pred) {
            pred = pred || func.fail;

            var aNext = [];
            while (node) {
                aNext.push(node);
                if (pred(node)) { break; }
                    node = node.nextSibling;
                }
            return aNext;
        };

        /**
        * listing descendant nodes
        *
        * @param {Element} node
        * @param {Function} [pred] - predicate function
        */
        var listDescendant = function (node, pred) {
            var aDescendant = [];
            pred = pred || func.ok;

            // start DFS(depth first search) with node
            (function fnWalk(current) {
                if (node !== current && pred(current)) {
                    aDescendant.push(current);
                }
                for (var idx = 0, sz = current.childNodes.length; idx < sz; idx++) {
                    fnWalk(current.childNodes[idx]);
                }
            })(node);
            return aDescendant;
        };

        /**
        * insert node after preceding
        *
        * @param {Element} node
        * @param {Element} preceding - predicate function
        */
        var insertAfter = function (node, preceding) {
            var next = preceding.nextSibling, parent = preceding.parentNode;
            if (next) {
                parent.insertBefore(node, next);
            } else {
                parent.appendChild(node);
            }
            return node;
        };

        /**
        * append elements.
        *
        * @param {Element} node
        * @param {Collection} aChild
        */
        var appends = function (node, aChild) {
            $.each(aChild, function (idx, child) {
                node.appendChild(child);
            });
            return node;
        };

        var isText = makePredByNodeName('#text');

        /**
        * returns #text's text size or element's childNodes size
        *
        * @param {Element} node
        */
        var length = function (node) {
            if (isText(node)) { return node.nodeValue.length; }
            return node.childNodes.length;
        };

        /**
        * returns offset from parent.
        *
        * @param {Element} node
        */
        var position = function (node) {
            var offset = 0;
            while ((node = node.previousSibling)) { offset += 1; }
            return offset;
        };

        /**
        * return offsetPath(array of offset) from ancestor
        *
        * @param {Element} ancestor - ancestor node
        * @param {Element} node
        */
        var makeOffsetPath = function (ancestor, node) {
            var aAncestor = list.initial(listAncestor(node, func.eq(ancestor)));
            return $.map(aAncestor, position).reverse();
        };

        /**
        * return element from offsetPath(array of offset)
        *
        * @param {Element} ancestor - ancestor node
        * @param {array} aOffset - offsetPath
        */
        var fromOffsetPath = function (ancestor, aOffset) {
            var current = ancestor;
            for (var i = 0, sz = aOffset.length; i < sz; i++) {
                current = current.childNodes[aOffset[i]];
            }
            return current;
        };

        /**
        * split element or #text
        *
        * @param {Element} node
        * @param {Number} offset
        */
        var splitData = function (node, offset) {
            if (offset === 0) { return node; }
            if (offset >= length(node)) { return node.nextSibling; }

            // splitText
            if (isText(node)) { return node.splitText(offset); }

            // splitElement
            var child = node.childNodes[offset];
            node = insertAfter(node.cloneNode(false), node);
            return appends(node, listNext(child));
        };

        /**
        * split dom tree by boundaryPoint(pivot and offset)
        *
        * @param {Element} root
        * @param {Element} pivot - this will be boundaryPoint's node
        * @param {Number} offset - this will be boundaryPoint's offset
        */
        var split = function (root, pivot, offset) {
            var aAncestor = listAncestor(pivot, func.eq(root));
            if (aAncestor.length === 1) { return splitData(pivot, offset); }
            return aAncestor.reduce(function (node, parent) {
                var clone = parent.cloneNode(false);
                insertAfter(clone, parent);
                if (node === pivot) {
                    node = splitData(node, offset);
                }
                appends(clone, listNext(node));
                return clone;
            });
        };

        /**
        * remove node, (bRemoveChild: remove child or not)
        * @param {Element} node
        * @param {Boolean} bRemoveChild
        */
        var remove = function (node, bRemoveChild) {
            if (!node || !node.parentNode) { return; }
            if (node.removeNode) { return node.removeNode(bRemoveChild); }

            var elParent = node.parentNode;
            if (!bRemoveChild) {
                var aNode = [];
                var i, sz;
                for (i = 0, sz = node.childNodes.length; i < sz; i++) {
                    aNode.push(node.childNodes[i]);
                }
                for (i = 0, sz = aNode.length; i < sz; i++) {
                    elParent.insertBefore(aNode[i], node);
                }
            }
            elParent.removeChild(node);
        };

        var html = function ($node) {
            return dom.isTextarea($node[0]) ? $node.val() : $node.html();
        };

        return {
            blank: agent.bMSIE ? '&nbsp;' : '<br/>',
            emptyPara: '<p><br/></p>',
            isEditable: isEditable,
            isControlSizing: isControlSizing,
            buildLayoutInfo: buildLayoutInfo,
            isText: isText,
            isPara: isPara,
            isList: isList,
            isTable: makePredByNodeName('TABLE'),
            isCell: isCell,
            isAnchor: makePredByNodeName('A'),
            isDiv: makePredByNodeName('DIV'),
            isLi: makePredByNodeName('LI'),
            isSpan: makePredByNodeName('SPAN'),
            isB: makePredByNodeName('B'),
            isU: makePredByNodeName('U'),
            isS: makePredByNodeName('S'),
            isI: makePredByNodeName('I'),
            isImg: makePredByNodeName('IMG'),
            isTextarea: makePredByNodeName('TEXTAREA'),
            ancestor: ancestor,
            listAncestor: listAncestor,
            listNext: listNext,
            listPrev: listPrev,
            listDescendant: listDescendant,
            commonAncestor: commonAncestor,
            listBetween: listBetween,
            insertAfter: insertAfter,
            position: position,
            makeOffsetPath: makeOffsetPath,
            fromOffsetPath: fromOffsetPath,
            split: split,
            remove: remove,
            html: html
        };
    })();
    var tplButtonInfo = {
        picture: function (lang) {
            return {
                sLabel : '<i class="fa fa-picture-o icon-picture"></i>',
                event: 'showImageDialog',
                title: lang.image.image
            };
        },
        link: function (lang) {
            return {
                sLabel : '<i class="fa fa-link icon-link"></i>',
                event: 'showLinkDialog',
                title: lang.link.link
            };
        },
        video: function (lang) {
            return {
                sLabel : '<i class="fa fa-youtube-play icon-play"></i>',
                event: 'showVideoDialog',
                title: lang.video.video
            };
        },
        table: function (lang) {
            var dropdown = openerp.qweb.render('website.editor.table', {});
            return {
                sLabel : '<i class="fa fa-table icon-table"></i>',
                title: lang.table.table,
                dropdown: dropdown
            };
        },
        style: function (lang, options) {
            var items = options.styleTags.reduce(function (memo, v) {
                var label = lang.style[v === 'p' ? 'normal' : v];
                return memo + '<li><a data-event="formatBlock" data-value="' + v + '">' +
                   (
                     (v === 'p' || v === 'pre') ? label :
                     '<' + v + '>' + label + '</' + v + '>'
                   ) +
                 '</a></li>';
            }, '');

            return {
                sLabel : '<i class="fa fa-magic icon-magic"></i>',
                title: lang.style.style,
                dropdown: '<ul class="dropdown-menu">' + items + '</ul>'
            };
        },
        fontname: function (lang, options) {
            var items = options.fontNames.reduce(function (memo, v) {
                return memo + '<li><a data-event="fontName" data-value="' + v + '">' +
                          '<i class="fa fa-check icon-ok"></i> ' + v +
                        '</a></li>';
            }, '');
            return {
                sLabel : '<span class="note-current-fontname">' + options.defaultFontName + '</span>',
                title: lang.font.name,
                dropdown: '<ul class="dropdown-menu">' + items + '</ul>'
            };
        },
        fontsize: function (lang, options) {
            var items = options.fontSizes.reduce(function (memo, v) {
                return memo + '<li><a data-event="fontSize" data-value="' + v + '">' +
                          '<i class="fa fa-check icon-ok"></i> ' + v +
                        '</a></li>';
            }, '');
            return {
                sLabel : '<span class="note-current-fontsize">11</span>',
                title: lang.font.size,
                dropdown: '<ul class="dropdown-menu">' + items + '</ul>'
            };
        },
        color: function (lang) {
            var dropdown = openerp.qweb.render('website.editor.color', {lang : lang});
            var colorButton = {
                sLabel : '<i class="fa fa-font icon-font" style="color:black;background-color:yellow;"></i>',
                className: 'note-recent-color',
                title: lang.color.recent,
                event: 'color',
                value: '{"backColor":"yellow"}',
                dropdown: dropdown
            };
            return colorButton;
        },
        bold: function (lang) {
            return {
                sLabel : '<i class="fa fa-bold icon-bold"></i>',
                event: 'bold',
                title: lang.font.bold
            };
        },
        italic: function (lang) {
            return {
                sLabel : '<i class="fa fa-italic icon-italic"></i>',
                event: 'italic',
                title: lang.font.italic
            };
        },
        underline: function (lang) {
            return {
                sLabel : '<i class="fa fa-underline icon-underline"></i>',
                event: 'underline',
                title: lang.font.underline
            };
        },
        strikethrough: function (lang) {
            return {
                sLabel : '<i class="fa fa-strikethrough icon-strikethrough"></i>',
                event: 'strikethrough',
                title: lang.font.strikethrough
            };
        },
        superscript: function (lang) {
            return {
                sLabel : '<i class="fa fa-superscript icon-superscript"></i>',
                event: 'superscript',
                title: lang.font.superscript
            };
        },
        subscript: function (lang) {
            return {
                sLabel : '<i class="fa fa-subscript icon-subscript"></i>',
                event: 'subscript',
                title: lang.font.subscript
            };
        },
        clear: function (lang) {
        return {
                sLabel : '<i class="fa fa-eraser icon-eraser"></i>',
                event: 'removeFormat',
                title: lang.font.clear
            };
        },
        ul: function (lang) {
            return {
                sLabel : '<i class="fa fa-list-ul icon-list-ul"></i>',
                event: 'insertUnorderedList',
                title: lang.lists.unordered
            };
        },
        ol: function (lang) {
            return {
                sLabel : '<i class="fa fa-list-ol icon-list-ol"></i>',
                event: 'insertOrderedList',
                title: lang.lists.ordered
            };
        },
        paragraph: function (lang) {
            var leftButton = {
                sLabel : '<i class="fa fa-align-left icon-align-left"></i>',
                title: lang.paragraph.left,
                event: 'justifyLeft'
            };
            var centerButton = {
                sLabel : '<i class="fa fa-align-center icon-align-center"></i>',
                title: lang.paragraph.center,
                event: 'justifyCenter'
            };
            var rightButton = {
                sLabel : '<i class="fa fa-align-right icon-align-right"></i>',
                title: lang.paragraph.right,
                event: 'justifyRight'
            };
            var justifyButton = {
                sLabel : '<i class="fa fa-align-justify icon-align-justify"></i>',
                title: lang.paragraph.justify,
                event: 'justifyFull'
            };
            var outdentButton = {
                sLabel : '<i class="fa fa-outdent icon-indent-left"></i>',
                title: lang.paragraph.outdent,
                event: 'outdent'
            };
            var indentButton = {
                sLabel : '<i class="fa fa-indent icon-indent-right"></i>',
                title: lang.paragraph.indent,
                event: 'indent'
            };

            var dropdown = openerp.qweb.render('website.editor.paragraph', {leftButton : leftButton, centerButton : centerButton, rightButton : rightButton, justifyButton : justifyButton, indentButton : indentButton, outdentButton : outdentButton});

            return {
                sLabel : '<i class="fa fa-align-left icon-align-left"></i>',
                title: lang.paragraph.paragraph,
                dropdown: dropdown
            };
        },
        height: function (lang, options) {
            var items = options.lineHeights.reduce(function (memo, v) {
                return memo + '<li><a data-event="lineHeight" data-value="' + parseFloat(v) + '">' +
                          '<i class="fa fa-check icon-ok"></i> ' + v +
                        '</a></li>';
            }, '');
            return {
                sLabel : '<i class="fa fa-text-height icon-text-height"></i>',
                title: lang.font.height,
                dropdown: '<ul class="dropdown-menu">' + items + '</ul>'
            };
        },
        help: function (lang) {
            return {
                sLabel : '<i class="fa fa-question icon-questiont"></i>',
                event: 'showHelpDialog',
                title: lang.options.help
            };
        },
        fullscreen: function (lang) {
            return {
                sLabel : '<i class="fa fa-arrows-alt icon-fullscreen"></i>',
                event: 'fullscreen',
                title: lang.options.fullscreen
            };
        },
        codeview: function (lang) {
            return {
                sLabel : '<i class="fa fa-code icon-code"></i>',
                event: 'codeview',
                title: lang.options.codeview
            };
        },
        undo: function (lang) {
            return {
                sLabel : '<i class="fa fa-undo icon-undo"></i>',
                event: 'undo',
                title: lang.history.undo
            };
        },
        redo: function (lang) {
            return {
                sLabel : '<i class="fa fa-repeat icon-repeat"></i>',
                event: 'redo',
                title: lang.history.redo
            };
        },
        hr: function (lang) {
            return {
                sLabel : '<i class="fa fa-minus icon-hr"></i>',
                event: 'insertHorizontalRule',
                title: lang.hr.insert
            };
        }
    };
    var defaults = {
        /**
        * options
        */
        options: {
            width: null,                  // set editor width
            height: null,                 // set editor height, ex) 300

            minHeight: null,              // set minimum height of editor
            maxHeight: null,              // set maximum height of editor

            focus: false,                 // set focus after initilize summernote

            tabsize: 4,                   // size of tab ex) 2 or 4
            styleWithSpan: true,          // style with span (Chrome and FF only)

            disableLinkTarget: false,     // hide link Target Checkbox
            disableDragAndDrop: false,    // disable drag and drop event
            disableResizeEditor: false,   // disable resizing editor

            incons : [], // list of icons
            inlinemedia : [] , //insert inline media eg. image , video etc 
            codemirror: {                 // codemirror options
                mode: 'text/html',
                lineNumbers: true
            },
            // language
            lang: 'en-US',                // language 'en-US', 'ko-KR', ...
            direction: null,              // text direction, ex) 'rtl'

            // toolbar
            toolbar: [
            ['style', ['style']],
            ['font', ['bold', 'italic', 'underline', 'superscript', 'subscript', 'strikethrough', 'clear']],
            ['fontname', ['fontname']],
            // ['fontsize', ['fontsize']], // Still buggy
            ['color', ['color']],
            ['para', ['ul', 'ol', 'paragraph']],
            ['height', ['height']],
            ['table', ['table']],
            ['insert', ['link', 'picture', 'video', 'hr']],
            ['view', ['fullscreen', 'codeview']],
            ['help', ['help']]
            ],

            // air mode: inline editor
            airMode: false,
            // airPopover: [
            //   ['style', ['style']],
            //   ['font', ['bold', 'italic', 'underline', 'clear']],
            //   ['fontname', ['fontname']],
            //   ['fontsize', ['fontsize']], // Still buggy
            //   ['color', ['color']],
            //   ['para', ['ul', 'ol', 'paragraph']],
            //   ['height', ['height']],
            //   ['table', ['table']],
            //   ['insert', ['link', 'picture', 'video']],
            //   ['help', ['help']]
            // ],
            airPopover: [
            ['color', ['color']],
            ['font', ['bold', 'underline', 'clear']],
            ['para', ['ul', 'paragraph']],
            ['table', ['table']],
            ['insert', ['link', 'picture']]
            ],

            // style tag
            styleTags: ['p', 'blockquote', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],

            // default fontName
            defaultFontName: 'Arial',

            // fontName
            fontNames: [
            'Serif', 'Sans', 'Arial', 'Arial Black', 'Courier',
            'Courier New', 'Comic Sans MS', 'Helvetica', 'Impact', 'Lucida Grande',
            'Lucida Sans', 'Tahoma', 'Times', 'Times New Roman', 'Verdana'
            ],

            // pallete colors(n x n)
            colors: [
            ['#000000', '#424242', '#636363', '#9C9C94', '#CEC6CE', '#EFEFEF', '#F7F7F7', '#FFFFFF'],
            ['#FF0000', '#FF9C00', '#FFFF00', '#00FF00', '#00FFFF', '#0000FF', '#9C00FF', '#FF00FF'],
            ['#F7C6CE', '#FFE7CE', '#FFEFC6', '#D6EFD6', '#CEDEE7', '#CEE7F7', '#D6D6E7', '#E7D6DE'],
            ['#E79C9C', '#FFC69C', '#FFE79C', '#B5D6A5', '#A5C6CE', '#9CC6EF', '#B5A5D6', '#D6A5BD'],
            ['#E76363', '#F7AD6B', '#FFD663', '#94BD7B', '#73A5AD', '#6BADDE', '#8C7BC6', '#C67BA5'],
            ['#CE0000', '#E79439', '#EFC631', '#6BA54A', '#4A7B8C', '#3984C6', '#634AA5', '#A54A7B'],
            ['#9C0000', '#B56308', '#BD9400', '#397B21', '#104A5A', '#085294', '#311873', '#731842'],
            ['#630000', '#7B3900', '#846300', '#295218', '#083139', '#003163', '#21104A', '#4A1031']
            ],

            // fontSize
            fontSizes: ['8', '9', '10', '11', '12', '14', '18', '24', '36'],

            // lineHeight
            lineHeights: ['1.0', '1.2', '1.4', '1.5', '1.6', '1.8', '2.0', '3.0'],

            // callbacks
            oninit: null,             // initialize
            onfocus: null,            // editable has focus
            onblur: null,             // editable out of focus
            onenter: null,            // enter key pressed
            onkeyup: null,            // keyup
            onkeydown: null,          // keydown
            onImageUpload: null,      // imageUploadHandler
            onImageUploadError: null, // imageUploadErrorHandler
            onToolbarClick: null,

            keyMap: {
                pc: {
                    'CTRL+Z': 'undo',
                    'CTRL+Y': 'redo',
                    'TAB': 'tab',
                    'SHIFT+TAB': 'untab',
                    'CTRL+B': 'bold',
                    'CTRL+I': 'italic',
                    'CTRL+U': 'underline',
                    'CTRL+SHIFT+S': 'strikethrough',
                    'CTRL+BACKSLASH': 'removeFormat',
                    'CTRL+SHIFT+L': 'justifyLeft',
                    'CTRL+SHIFT+E': 'justifyCenter',
                    'CTRL+SHIFT+R': 'justifyRight',
                    'CTRL+SHIFT+J': 'justifyFull',
                    'CTRL+SHIFT+NUM7': 'insertUnorderedList',
                    'CTRL+SHIFT+NUM8': 'insertOrderedList',
                    'CTRL+LEFTBRACKET': 'outdent',
                    'CTRL+RIGHTBRACKET': 'indent',
                    'CTRL+NUM0': 'formatPara',
                    'CTRL+NUM1': 'formatH1',
                    'CTRL+NUM2': 'formatH2',
                    'CTRL+NUM3': 'formatH3',
                    'CTRL+NUM4': 'formatH4',
                    'CTRL+NUM5': 'formatH5',
                    'CTRL+NUM6': 'formatH6',
                    'CTRL+ENTER': 'insertHorizontalRule'
                },
                mac: {
                    'CMD+Z': 'undo',
                    'CMD+SHIFT+Z': 'redo',
                    'TAB': 'tab',
                    'SHIFT+TAB': 'untab',
                    'CMD+B': 'bold',
                    'CMD+I': 'italic',
                    'CMD+U': 'underline',
                    'CMD+SHIFT+S': 'strikethrough',
                    'CMD+BACKSLASH': 'removeFormat',
                    'CMD+SHIFT+L': 'justifyLeft',
                    'CMD+SHIFT+E': 'justifyCenter',
                    'CMD+SHIFT+R': 'justifyRight',
                    'CMD+SHIFT+J': 'justifyFull',
                    'CMD+SHIFT+NUM7': 'insertUnorderedList',
                    'CMD+SHIFT+NUM8': 'insertOrderedList',
                    'CMD+LEFTBRACKET': 'outdent',
                    'CMD+RIGHTBRACKET': 'indent',
                    'CMD+NUM0': 'formatPara',
                    'CMD+NUM1': 'formatH1',
                    'CMD+NUM2': 'formatH2',
                    'CMD+NUM3': 'formatH3',
                    'CMD+NUM4': 'formatH4',
                    'CMD+NUM5': 'formatH5',
                    'CMD+NUM6': 'formatH6',
                    'CMD+ENTER': 'insertHorizontalRule'
                }
            }
        },

        // default language: en-US
        lang: {
            'en-US': {
                font: {
                    bold: 'Bold',
                    italic: 'Italic',
                    underline: 'Underline',
                    strikethrough: 'Strikethrough',
                    clear: 'Remove Font Style',
                    height: 'Line Height',
                    name: 'Font Family',
                    size: 'Font Size'
                },
                image: {
                    image: 'Picture',
                    insert: 'Insert Image',
                    resizeFull: 'Resize Full',
                    resizeHalf: 'Resize Half',
                    resizeQuarter: 'Resize Quarter',
                    floatLeft: 'Float Left',
                    floatRight: 'Float Right',
                    floatNone: 'Float None',
                    dragImageHere: 'Drag an image here',
                    selectFromFiles: 'Select from files',
                    url: 'Image URL',
                    remove: 'Remove Image'
                },
                link: {
                    link: 'Link',
                    insert: 'Insert Link',
                    unlink: 'Unlink',
                    edit: 'Edit',
                    textToDisplay: 'Text to display',
                    url: 'To what URL should this link go?',
                    openInNewWindow: 'Open in new window'
                },
                video: {
                    video: 'Video',
                    videoLink: 'Video Link',
                    insert: 'Insert Video',
                    url: 'Video URL?',
                    providers: '(YouTube, Vimeo, Vine, Instagram, or DailyMotion)'
                },
                table: {
                    table: 'Table'
                },
                hr: {
                    insert: 'Insert Horizontal Rule'
                },
                style: {
                    style: 'Style',
                    normal: 'Normal',
                    blockquote: 'Quote',
                    pre: 'Code',
                    h1: 'Header 1',
                    h2: 'Header 2',
                    h3: 'Header 3',
                    h4: 'Header 4',
                    h5: 'Header 5',
                    h6: 'Header 6'
                },
                lists: {
                    unordered: 'Unordered list',
                    ordered: 'Ordered list'
                },
                options: {
                    help: 'Help',
                    fullscreen: 'Full Screen',
                    codeview: 'Code View'
                },
                paragraph: {
                    paragraph: 'Paragraph',
                    outdent: 'Outdent',
                    indent: 'Indent',
                    left: 'Align left',
                    center: 'Align center',
                    right: 'Align right',
                    justify: 'Justify full'
                },
                color: {
                    recent: 'Recent Color',
                    more: 'More Color',
                    background: 'BackColor',
                    foreground: 'FontColor',
                    transparent: 'Transparent',
                    setTransparent: 'Set transparent',
                    reset: 'Reset',
                    resetToDefault: 'Reset to default'
                },
                shortcut: {
                    shortcuts: 'Keyboard shortcuts',
                    close: 'Close',
                    textFormatting: 'Text formatting',
                    action: 'Action',
                    paragraphFormatting: 'Paragraph formatting',
                    documentStyle: 'Document Style'
                },
                history: {
                    undo: 'Undo',
                    redo: 'Redo'
                }
            }
        }
    };
    /**
    * Async functions which returns `Promise`
    */
    var async = (function () {
        /**
        * read contents of file as representing URL
        *
        * @param {File} file
        * @return {Promise} - then: sDataUrl
        */
        var readFileAsDataURL = function (file) {
            return $.Deferred(function (deferred) {
                $.extend(new FileReader(), {
                    onload: function (e) {
                        var sDataURL = e.target.result;
                        deferred.resolve(sDataURL);
                    },
                    onerror: function () {
                        deferred.reject(this);
                    }
                }).readAsDataURL(file);
            }).promise();
        };

        /**
        * create `<image>` from url string
        *
        * @param {String} sUrl
        * @return {Promise} - then: $image
        */
        var createImage = function (sUrl) {
            return $.Deferred(function (deferred) {
                $('<img>').one('load', function () {
                    deferred.resolve($(this));
                }).one('error abort', function () {
                    deferred.reject($(this));
                }).css({
                    display: 'none'
                }).appendTo(document.body).attr('src', sUrl);
            }).promise();
        };

        return {
            readFileAsDataURL: readFileAsDataURL,
            createImage: createImage
        };
    })();
    /**
    * Object for keycodes.
    */
    var key = {
        isEdit: function (keyCode) {
            return [8, 9, 13, 32].indexOf(keyCode) !== -1;
        },
        nameFromCode: {
            '8': 'BACKSPACE',
            '9': 'TAB',
            '13': 'ENTER',
            '32': 'SPACE',

            // Number: 0-9
            '48': 'NUM0',
            '49': 'NUM1',
            '50': 'NUM2',
            '51': 'NUM3',
            '52': 'NUM4',
            '53': 'NUM5',
            '54': 'NUM6',
            '55': 'NUM7',
            '56': 'NUM8',

            // Alphabet: a-z
            '66': 'B',
            '69': 'E',
            '73': 'I',
            '74': 'J',
            '75': 'K',
            '76': 'L',
            '82': 'R',
            '83': 'S',
            '85': 'U',
            '89': 'Y',
            '90': 'Z',

            '191': 'SLASH',
            '219': 'LEFTBRACKET',
            '220': 'BACKSLASH',
            '221': 'RIGHTBRACKET'
        }
    };

    /**
    * Style
    * @class
    */
    var Style = function () {
        /**
        * passing an array of style properties to .css()
        * will result in an object of property-value pairs.
        * (compability with version < 1.9)
        *
        * @param  {jQuery} $obj
        * @param  {Array} propertyNames - An array of one or more CSS properties.
        * @returns {Object}
        */
        var jQueryCSS = function ($obj, propertyNames) {
            if (agent.jqueryVersion < 1.9) {
                var result = {};
                $.each(propertyNames, function (idx, propertyName) {
                  result[propertyName] = $obj.css(propertyName);
                });
                return result;
            }
            return $obj.css.call($obj, propertyNames);
        };

        /**
        * paragraph level style
        *
        * @param {WrappedRange} rng
        * @param {Object} oStyle
        */
        this.stylePara = function (rng, oStyle) {
            $.each(rng.nodes(dom.isPara), function (idx, elPara) {
                $(elPara).css(oStyle);
            });
        };

        /**
        * get current style on cursor
        *
        * @param {WrappedRange} rng
        * @param {Element} elTarget - target element on event
        * @return {Object} - object contains style properties.
        */
        this.current = function (rng, elTarget) {
            var $cont = $(dom.isText(rng.sc) ? rng.sc.parentNode : rng.sc);
            var properties = ['font-family', 'font-size', 'text-align', 'list-style-type', 'line-height'];
            var oStyle = jQueryCSS($cont, properties) || {};
            oStyle['font-size'] = parseInt(oStyle['font-size'], 10);
            // document.queryCommandState for toggle state
            oStyle['font-bold'] = document.queryCommandState('bold') ? 'bold' : 'normal';
            oStyle['font-italic'] = document.queryCommandState('italic') ? 'italic' : 'normal';
            oStyle['font-underline'] = document.queryCommandState('underline') ? 'underline' : 'normal';
            oStyle['font-strikethrough'] = document.queryCommandState('strikeThrough') ? 'strikethrough' : 'normal';
            oStyle['font-superscript'] = document.queryCommandState('superscript') ? 'superscript' : 'normal';
            oStyle['font-subscript'] = document.queryCommandState('subscript') ? 'subscript' : 'normal';
            // list-style-type to list-style(unordered, ordered)
            if (!rng.isOnList()) {
                oStyle['list-style'] = 'none';
            } else {
                var aOrderedType = ['circle', 'disc', 'disc-leading-zero', 'square'];
                var bUnordered = $.inArray(oStyle['list-style-type'], aOrderedType) > -1;
                oStyle['list-style'] = bUnordered ? 'unordered' : 'ordered';
            }

            var elPara = dom.ancestor(rng.sc, dom.isPara);
            if (elPara && elPara.style['line-height']) {
                oStyle['line-height'] = elPara.style.lineHeight;
            } else {
                var lineHeight = parseInt(oStyle['line-height'], 10) / parseInt(oStyle['font-size'], 10);
                oStyle['line-height'] = lineHeight.toFixed(1);
            }

            oStyle.image = dom.isImg(elTarget) && elTarget;
            oStyle.anchor = rng.isOnAnchor() && dom.ancestor(rng.sc, dom.isAnchor);
            oStyle.aAncestor = dom.listAncestor(rng.sc, dom.isEditable);
            oStyle.range = rng;

            return oStyle;
        };
    };

    /**
    * range module
    */
    var range = (function () {
        var bW3CRangeSupport = !!document.createRange;
        /**
        * return boundaryPoint from TextRange, inspired by Andy Na's HuskyRange.js
        * @param {TextRange} textRange
        * @param {Boolean} bStart
        * @return {BoundaryPoint}
        */
        var textRange2bp = function (textRange, bStart) {
            var elCont = textRange.parentElement(), nOffset;
            var tester = document.body.createTextRange(), elPrevCont;
            var aChild = list.from(elCont.childNodes);
            for (nOffset = 0; nOffset < aChild.length; nOffset++) {
                if (dom.isText(aChild[nOffset])) { continue; }
                tester.moveToElementText(aChild[nOffset]);
                if (tester.compareEndPoints('StartToStart', textRange) >= 0) { break; }
                elPrevCont = aChild[nOffset];
        }

        if (nOffset !== 0 && dom.isText(aChild[nOffset - 1])) {
            var textRangeStart = document.body.createTextRange(), elCurText = null;
            textRangeStart.moveToElementText(elPrevCont || elCont);
            textRangeStart.collapse(!elPrevCont);
            elCurText = elPrevCont ? elPrevCont.nextSibling : elCont.firstChild;

            var pointTester = textRange.duplicate();
            pointTester.setEndPoint('StartToStart', textRangeStart);
            var nTextCount = pointTester.text.replace(/[\r\n]/g, '').length;

            while (nTextCount > elCurText.nodeValue.length && elCurText.nextSibling) {
                nTextCount -= elCurText.nodeValue.length;
                elCurText = elCurText.nextSibling;
            }

            /* jshint ignore:start */
            var sDummy = elCurText.nodeValue; //enforce IE to re-reference elCurText, hack
            /* jshint ignore:end */
            if (bStart && elCurText.nextSibling && dom.isText(elCurText.nextSibling) &&
                nTextCount === elCurText.nodeValue.length) {
                nTextCount -= elCurText.nodeValue.length;
                elCurText = elCurText.nextSibling;
            }
            elCont = elCurText;
            nOffset = nTextCount;
        }
        return {cont: elCont, offset: nOffset};
    };

    /**
    * return TextRange from boundary point (inspired by google closure-library)
    * @param {BoundaryPoint} bp
    * @return {TextRange}
    */
    var bp2textRange = function (bp) {
        var textRangeInfo = function (elCont, nOffset) {
            var elNode, bCollapseToStart;
            if (dom.isText(elCont)) {
                var aPrevText = dom.listPrev(elCont, func.not(dom.isText));
                var elPrevCont = list.last(aPrevText).previousSibling;
                elNode =  elPrevCont || elCont.parentNode;
                nOffset += list.sum(list.tail(aPrevText), dom.length);
                bCollapseToStart = !elPrevCont;
            } else {
                elNode = elCont.childNodes[nOffset] || elCont;
                if (dom.isText(elNode)) {
                    return textRangeInfo(elNode, nOffset);
                }
                nOffset = 0;
                bCollapseToStart = false;
            }
            return {cont: elNode, collapseToStart: bCollapseToStart, offset: nOffset};
        };

        var textRange = document.body.createTextRange();
        var info = textRangeInfo(bp.cont, bp.offset);

        textRange.moveToElementText(info.cont);
        textRange.collapse(info.collapseToStart);
        textRange.moveStart('character', info.offset);
        return textRange;
    };

    /**
    * Wrapped Range
    *
    * @param {Element} sc - start container
    * @param {Number} so - start offset
    * @param {Element} ec - end container
    * @param {Number} eo - end offset
    */
    var WrappedRange = function (sc, so, ec, eo) {
        this.sc = sc;
        this.so = so;
        this.ec = ec;
        this.eo = eo;

        // nativeRange: get nativeRange from sc, so, ec, eo
        var nativeRange = function () {
            if (bW3CRangeSupport) {
                var w3cRange = document.createRange();
                w3cRange.setStart(sc, so);
                w3cRange.setEnd(ec, eo);
                return w3cRange;
            } else {
                var textRange = bp2textRange({cont: sc, offset: so});
                textRange.setEndPoint('EndToEnd', bp2textRange({cont: ec, offset: eo}));
                return textRange;
            }
        };

        /**
        * select update visible range
        */
        this.select = function () {
            var nativeRng = nativeRange();
            if (bW3CRangeSupport) {
                var selection = document.getSelection();
                if (selection.rangeCount > 0) { selection.removeAllRanges(); }
                selection.addRange(nativeRng);
            } else {
                nativeRng.select();
            }
        };

        /**
        * returns matched nodes on range
        *
        * @param {Function} pred - predicate function
        * @return {Element[]}
        */
        this.nodes = function (pred) {
            var aNode = dom.listBetween(sc, ec);
            var aMatched = list.compact($.map(aNode, function (node) {
                return dom.ancestor(node, pred);
            }));
            return $.map(list.clusterBy(aMatched, func.eq2), list.head);
        };

        /**
        * returns commonAncestor of range
        * @return {Element} - commonAncestor
        */
        this.commonAncestor = function () {
            return dom.commonAncestor(sc, ec);
        };

        /**
        * makeIsOn: return isOn(pred) function
        */
        var makeIsOn = function (pred) {
            return function () {
                var elAncestor = dom.ancestor(sc, pred);
                return !!elAncestor && (elAncestor === dom.ancestor(ec, pred));
            };
        };

        // isOnEditable: judge whether range is on editable or not
        this.isOnEditable = makeIsOn(dom.isEditable);
        // isOnList: judge whether range is on list node or not
        this.isOnList = makeIsOn(dom.isList);
        // isOnAnchor: judge whether range is on anchor node or not
        this.isOnAnchor = makeIsOn(dom.isAnchor);
        // isOnAnchor: judge whether range is on cell node or not
        this.isOnCell = makeIsOn(dom.isCell);
        // isCollapsed: judge whether range was collapsed
        this.isCollapsed = function () { return sc === ec && so === eo; };

        /**
        * insert node at current cursor
        * @param {Element} node
        */
        this.insertNode = function (node) {
            var nativeRng = nativeRange();
            if (bW3CRangeSupport) {
                nativeRng.insertNode(node);
            } else {
                nativeRng.pasteHTML(node.outerHTML); // NOTE: missing node reference.
            }
        };

        this.toString = function () {
            var nativeRng = nativeRange();
            return bW3CRangeSupport ? nativeRng.toString() : nativeRng.text;
        };

        /**
        * create offsetPath bookmark
        * @param {Element} elEditable
        */
        this.bookmark = function (elEditable) {
            return {
                s: { path: dom.makeOffsetPath(elEditable, sc), offset: so },
                e: { path: dom.makeOffsetPath(elEditable, ec), offset: eo }
            };
        };

        /**
        * getClientRects
        * @return {Rect[]}
        */
        this.getClientRects = function () {
            var nativeRng = nativeRange();
                return nativeRng.getClientRects();
            };
        };

        return {
            /**
            * create Range Object From arguments or Browser Selection
            *
            * @param {Element} sc - start container
            * @param {Number} so - start offset
            * @param {Element} ec - end container
            * @param {Number} eo - end offset
            */
            create : function (sc, so, ec, eo) {
                if (arguments.length === 0) { // from Browser Selection
                    if (bW3CRangeSupport) { // webkit, firefox
                        var selection = document.getSelection();
                        if (selection.rangeCount === 0) { return null; }

                        var nativeRng = selection.getRangeAt(0);
                        sc = nativeRng.startContainer;
                        so = nativeRng.startOffset;
                        ec = nativeRng.endContainer;
                        eo = nativeRng.endOffset;
                    } else { // IE8: TextRange
                        var textRange = document.selection.createRange();
                        var textRangeEnd = textRange.duplicate();
                        textRangeEnd.collapse(false);
                        var textRangeStart = textRange;
                        textRangeStart.collapse(true);

                        var bpStart = textRange2bp(textRangeStart, true),
                        bpEnd = textRange2bp(textRangeEnd, false);

                        sc = bpStart.cont;
                        so = bpStart.offset;
                        ec = bpEnd.cont;
                        eo = bpEnd.offset;
                    }
                } else if (arguments.length === 2) { //collapsed
                    ec = sc;
                    eo = so;
                }
                return new WrappedRange(sc, so, ec, eo);
            },

            /**
            * create WrappedRange from node
            *
            * @param {Element} node
            * @return {WrappedRange}
            */
            createFromNode: function (node) {
                return this.create(node, 0, node, 1);
            },

            /**
            * create WrappedRange from Bookmark
            *
            * @param {Element} elEditable
            * @param {Obkect} bookmark
            * @return {WrappedRange}
            */
            createFromBookmark : function (elEditable, bookmark) {
                var sc = dom.fromOffsetPath(elEditable, bookmark.s.path);
                var so = bookmark.s.offset;
                var ec = dom.fromOffsetPath(elEditable, bookmark.e.path);
                var eo = bookmark.e.offset;
                return new WrappedRange(sc, so, ec, eo);
            }
        };
    })();

    /**
    * Table
    * @class
    */
    var Table = function () {
        /**
        * handle tab key
        *
        * @param {WrappedRange} rng
        * @param {Boolean} bShift
        */
        this.tab = function (rng, bShift) {
            var elCell = dom.ancestor(rng.commonAncestor(), dom.isCell);
            var elTable = dom.ancestor(elCell, dom.isTable);
            var aCell = dom.listDescendant(elTable, dom.isCell);

            var elNext = list[bShift ? 'prev' : 'next'](aCell, elCell);
            if (elNext) {
                range.create(elNext, 0).select();
            }
        };

        /**
        * create empty table element
        *
        * @param {Number} nRow
        * @param {Number} nCol
        */
        this.createTable = function (nCol, nRow) {
            var aTD = [], sTD;
            for (var idxCol = 0; idxCol < nCol; idxCol++) {
                aTD.push('<td>' + dom.blank + '</td>');
            }
            sTD = aTD.join('');

            var aTR = [], sTR;
            for (var idxRow = 0; idxRow < nRow; idxRow++) {
                aTR.push('<tr>' + sTD + '</tr>');
            }
            sTR = aTR.join('');
            var sTable = '<table class="table table-bordered">' + sTR + '</table>';

            return $(sTable)[0];
        };
    };

    /**
    * Editor
    * @class
    */
    var Editor = function () {

        var style = new Style();
        var table = new Table();

        /**
        * save current range
        *
        * @param {jQuery} $editable
        */
        this.saveRange = function ($editable) {
            $editable.data('range', range.create());
        };

        /**
         * restore lately range
         *
         * @param {jQuery} $editable
         */
        this.restoreRange = function ($editable) {
            var rng = $editable.data('range');
            if (rng) { rng.select(); }
        };

        /**
        * current style
        * @param {Element} elTarget
        */
        this.currentStyle = function (elTarget) {
            var rng = range.create();
            var $el =$(elTarget).parent();
            if($el.hasClass('inline-media-link')) {
                $el.prev().append('<p class="insert-media"/>')
            }
            return rng.isOnEditable() && style.current(rng, elTarget);
        };

        /**
         * undo
         * @param {jQuery} $editable
         */
        this.undo = function ($editable) {
            $editable.data('NoteHistory').undo($editable);
        };

        /**
        * redo
        * @param {jQuery} $editable
        */
        this.redo = function ($editable) {
            $editable.data('NoteHistory').redo($editable);
        };

        /**
        * record Undo
        * @param {jQuery} $editable
        */
        var recordUndo = this.recordUndo = function ($editable) {
            $editable.data('NoteHistory').recordUndo($editable);
        };

        /* jshint ignore:start */
        // native commands(with execCommand), generate function for execCommand
        var aCmd = ['bold', 'italic', 'underline', 'strikethrough', 'superscript', 'subscript',
            'justifyLeft', 'justifyCenter', 'justifyRight', 'justifyFull',
            'insertOrderedList', 'insertUnorderedList',
            'indent', 'outdent', 'formatBlock', 'removeFormat',
            'backColor', 'foreColor', 'insertHorizontalRule', 'fontName'];

        for (var idx = 0, len = aCmd.length; idx < len; idx ++) {
            this[aCmd[idx]] = (function (sCmd) {
                return function ($editable, sValue) {
                    recordUndo($editable);
                    document.execCommand(sCmd, false, sValue);
                };
            })(aCmd[idx]);
        }
        /* jshint ignore:end */

        /**
        * @param {jQuery} $editable 
        * @param {WrappedRange} rng
        * @param {Number} nTabsize
        */
        var insertTab = function ($editable, rng, nTabsize) {
            recordUndo($editable);
            var sNbsp = new Array(nTabsize + 1).join('&nbsp;');
            rng.insertNode($('<span id="noteTab">' + sNbsp + '</span>')[0]);
            var $tab = $('#noteTab').removeAttr('id');
            rng = range.create($tab[0], 1);
            rng.select();
            dom.remove($tab[0]);
        };

        /**
        * handle tab key
        * @param {jQuery} $editable 
        * @param {Number} nTabsize
        * @param {Boolean} bShift
        */
        this.tab = function ($editable, options) {
            var rng = range.create();
            if (rng.isCollapsed() && rng.isOnCell()) {
                table.tab(rng);
            } else {
                insertTab($editable, rng, options.tabsize);
            }
        };

        /**
        * handle shift+tab key
        */
        this.untab = function () {
            var rng = range.create();
                if (rng.isCollapsed() && rng.isOnCell()) {
                table.tab(rng, true);
            }
        };

        /**
        * formatBlock
        *
        * @param {jQuery} $editable
        * @param {String} sTagName
        */
        this.formatBlock = function ($editable, sTagName) {
            recordUndo($editable);
            sTagName = agent.bMSIE ? '<' + sTagName + '>' : sTagName;
            document.execCommand('FormatBlock', false, sTagName);
        };

        this.formatPara = function ($editable) {
            this.formatBlock($editable, 'P');
        };

        /* jshint ignore:start */
        for (var idx = 1; idx <= 6; idx ++) {
            this['formatH' + idx] = function (idx) {
                return function ($editable) {
                    this.formatBlock($editable, 'H' + idx);
                };
            }(idx);
        };
        /* jshint ignore:end */

        /**
        * fontsize
        * FIXME: Still buggy
        *
        * @param {jQuery} $editable
        * @param {String} sValue - px
        */
        this.fontSize = function ($editable, sValue) {
            recordUndo($editable);
            document.execCommand('fontSize', false, 3);
            if (agent.bFF) {
                // firefox: <font size="3"> to <span style='font-size={sValue}px;'>, buggy
                $editable.find('font[size=3]').removeAttr('size').css('font-size', sValue + 'px');
            } else {
                // chrome: <span style="font-size: medium"> to <span style='font-size={sValue}px;'>
                $editable.find('span').filter(function () {
                    return this.style.fontSize === 'medium';
                }).css('font-size', sValue + 'px');
            }
        };

        /**
        * lineHeight
        * @param {jQuery} $editable
        * @param {String} sValue
        */
        this.lineHeight = function ($editable, sValue) {
            recordUndo($editable);
            style.stylePara(range.create(), {lineHeight: sValue});
        };

        /**
        * unlink
        * @param {jQuery} $editable
        */
        this.unlink = function ($editable) {
            var rng = range.create();
            if (rng.isOnAnchor()) {
                recordUndo($editable);
                var elAnchor = dom.ancestor(rng.sc, dom.isAnchor);
                rng = range.createFromNode(elAnchor);
                rng.select();
                document.execCommand('unlink');
            }
        };

        this.color = function ($editable, sObjColor) {
            var oColor = JSON.parse(sObjColor);
            var foreColor = oColor.foreColor, backColor = oColor.backColor;
            recordUndo($editable);
            if (foreColor) { document.execCommand('foreColor', false, foreColor); }
            if (backColor) { document.execCommand('backColor', false, backColor); }
        };

        this.insertTable = function ($editable, sDim) {
            recordUndo($editable);
            var aDim = sDim.split('x');
            range.create().insertNode(table.createTable(aDim[0], aDim[1]));
        };

        /**
        * @param {jQuery} $editable
        * @param {String} sValue
        * @param {jQuery} $target
        */
        this.floatMe = function ($editable, sValue, $target) {
            recordUndo($editable);
            $target.css('float', sValue);
        };

        /**
        * resize overlay element
        * @param {jQuery} $editable
        * @param {String} sValue
        * @param {jQuery} $target - target element
        */
        this.resize = function ($editable, sValue, $target) {
            recordUndo($editable);
            $target.css({
                width: $editable.width() * sValue + 'px',
                height: ''
            });
        };

        /**
        * @param {Position} pos
        * @param {jQuery} $target - target element
        * @param {Boolean} [bKeepRatio] - keep ratio
        */
        this.resizeTo = function (pos, $target, bKeepRatio) {
            var szImage;
            if (bKeepRatio) {
                var newRatio = pos.y / pos.x;
                var ratio = $target.data('ratio');
                szImage = {
                    width: ratio > newRatio ? pos.x : pos.y / ratio,
                    height: ratio > newRatio ? pos.x * ratio : pos.y
                };
            } else {
                szImage = {
                    width: pos.x,
                    height: pos.y
                };
            }
            $target.css(szImage);
        };

        /**
        * remove media object
        *
        * @param {jQuery} $editable
        * @param {String} sValue - dummy argument (for keep interface)
        * @param {jQuery} $target - target element
        */
        this.removeMedia = function ($editable, sValue, $target) {
            recordUndo($editable);
            $target.detach();
        };
    };

    /**
    * History
    * @class
    */
    var History = function () {
        var aUndo = [], aRedo = [];
        var makeSnap = function ($editable) {
            var elEditable = $editable[0], rng = range.create();
            return {
                contents: $editable.html(),
                bookmark: rng.bookmark(elEditable),
                scrollTop: $editable.scrollTop()
            };
        };

        var applySnap = function ($editable, oSnap) {
            $editable.html(oSnap.contents).scrollTop(oSnap.scrollTop);
            range.createFromBookmark($editable[0], oSnap.bookmark).select();
        };

        this.undo = function ($editable) {
            var oSnap = makeSnap($editable);
            if (aUndo.length === 0) { return; }
            applySnap($editable, aUndo.pop());
            aRedo.push(oSnap);
        };

        this.redo = function ($editable) {
            var oSnap = makeSnap($editable);
            if (aRedo.length === 0) { return; }
            applySnap($editable, aRedo.pop());
            aUndo.push(oSnap);
        };

        this.recordUndo = function ($editable) {
            aRedo = [];
            aUndo.push(makeSnap($editable));
        };
    };
    /**
    * Button
    */
    var Button = function () {
        /**
        * update button status
        *
        * @param {jQuery} $container
        * @param {Object} oStyle
        */
        this.update = function ($container, oStyle) {
            /**
            * handle dropdown's check mark (for fontname, fontsize, lineHeight).
            * @param {jQuery} $btn
            * @param {Number} nValue
            */
            var checkDropdownMenu = function ($btn, nValue) {
                $btn.find('.dropdown-menu li a').each(function () {
                    // always compare string to avoid creating another func.
                    var bChecked = ($(this).data('value') + '') === (nValue + '');
                    this.className = bChecked ? 'checked' : '';
                });
            };

            /**
            * update button state(active or not).
            *
            * @param {String} sSelector
            * @param {Function} pred
            */
            var btnState = function (sSelector, pred) {
                var $btn = $container.find(sSelector);
                $btn.toggleClass('active', pred());
            };

            // fontname
            var $fontname = $container.find('.note-fontname');
            if ($fontname.length > 0) {
                var selectedFont = oStyle['font-family'];
                if (!!selectedFont) {
                    selectedFont = list.head(selectedFont.split(','));
                    selectedFont = selectedFont.replace(/\'/g, '');
                    $fontname.find('.note-current-fontname').text(selectedFont);
                    checkDropdownMenu($fontname, selectedFont);
                }
            }
            // fontsize
            var $fontsize = $container.find('.note-fontsize');
            $fontsize.find('.note-current-fontsize').text(oStyle['font-size']);
            checkDropdownMenu($fontsize, parseFloat(oStyle['font-size']));
            // lineheight
            var $lineHeight = $container.find('.note-height');
            checkDropdownMenu($lineHeight, parseFloat(oStyle['line-height']));
            btnState('button[data-event="bold"]', function () {
                return oStyle['font-bold'] === 'bold';
            });
            btnState('button[data-event="italic"]', function () {
                return oStyle['font-italic'] === 'italic';
            });
            btnState('button[data-event="underline"]', function () {
                return oStyle['font-underline'] === 'underline';
            });
            btnState('button[data-event="strikethrough"]', function () {
                return oStyle['font-strikethrough'] === 'strikethrough';
            });
            btnState('button[data-event="superscript"]', function () {
                return oStyle['font-superscript'] === 'superscript';
            });
            btnState('button[data-event="subscript"]', function () {
                return oStyle['font-subscript'] === 'subscript';
            });
            btnState('button[data-event="justifyLeft"]', function () {
                return oStyle['text-align'] === 'left' || oStyle['text-align'] === 'start';
            });
            btnState('button[data-event="justifyCenter"]', function () {
                return oStyle['text-align'] === 'center';
            });
            btnState('button[data-event="justifyRight"]', function () {
                return oStyle['text-align'] === 'right';
            });
            btnState('button[data-event="justifyFull"]', function () {
                return oStyle['text-align'] === 'justify';
            });
            btnState('button[data-event="insertUnorderedList"]', function () {
                return oStyle['list-style'] === 'unordered';
            });
            btnState('button[data-event="insertOrderedList"]', function () {
                return oStyle['list-style'] === 'ordered';
            });
        };

        /**
        * update recent color
        *
        * @param {Element} elBtn
        * @param {String} sEvent
        * @param {sValue} sValue
        */
        this.updateRecentColor = function (elBtn, sEvent, sValue) {
            var $color = $(elBtn).closest('.note-color');
            var $recentColor = $color.find('.note-recent-color');
            var oColor = JSON.parse($recentColor.attr('data-value'));
            oColor[sEvent] = sValue;
            $recentColor.attr('data-value', JSON.stringify(oColor));
            var sKey = sEvent === 'backColor' ? 'background-color' : 'color';
            $recentColor.find('i').css(sKey, sValue);
        };
    };

    /**
    * Toolbar
    */
    var Toolbar = function () {
        var button = new Button();

        this.update = function ($toolbar, oStyle) {
            button.update($toolbar, oStyle);
        };

        this.updateRecentColor = function (elBtn, sEvent, sValue) {
            button.updateRecentColor(elBtn, sEvent, sValue);
        };

        /**
        * activate buttons exclude codeview
        * @param {jQuery} $toolbar
        */
        this.activate = function ($toolbar) {
            $toolbar.find('button').not('button[data-event="codeview"]').removeClass('disabled');
        };

        /**
        * deactivate buttons exclude codeview
        * @param {jQuery} $toolbar
        */
        this.deactivate = function ($toolbar) {
            $toolbar.find('button').not('button[data-event="codeview"]').addClass('disabled');
        };

        this.updateFullscreen = function ($container, bFullscreen) {
            var $btn = $container.find('button[data-event="fullscreen"]');
            $btn.toggleClass('active', bFullscreen);
        };

        this.updateCodeview = function ($container, bCodeview) {
            var $btn = $container.find('button[data-event="codeview"]');
            $btn.toggleClass('active', bCodeview);
        };
    };

    /**
    * Popover (http://getbootstrap.com/javascript/#popovers)
    */
    var Popover = function () {
        var button = new Button();

        /**
        * show popover
        * @param {jQuery} popover
        * @param {Element} elPlaceholder - placeholder for popover
        */
        var showPopover = function ($popover, elPlaceholder) {
            var $placeholder = $(elPlaceholder);
            var pos = $placeholder.offset();
            // include margin
            var height = $placeholder.outerHeight(true);
            // display popover below placeholder.
            $popover.css({
                display: 'block',
                left: pos.left,
                top: pos.top + height
            });
        };

        var PX_POPOVER_ARROW_OFFSET_X = 20;

        /**
        * update current state
        * @param {jQuery} $popover - popover container
        * @param {Object} oStyle - style object
        * @param {Boolean} isAirMode
        */
        this.update = function ($popover, oStyle, isAirMode) {
            button.update($popover, oStyle);

            var $linkPopover = $popover.find('.note-link-image-popover');
            if($(oStyle.anchor).hasClass('editor-insert-media')) {
                var $anchor = $linkPopover.find('a');
                $anchor.attr('href', oStyle.anchor.href).html(oStyle.anchor.href);
                showPopover($linkPopover, oStyle.anchor);
            }
            else if (oStyle.anchor) {
                $linkPopover = $popover.find('.note-link-popover');
                var $anchor = $linkPopover.find('a');
                $anchor.attr('href', oStyle.anchor.href).html(oStyle.anchor.href);
                showPopover($linkPopover, oStyle.anchor);
            } else {
                $linkPopover.hide();
            }

            var $imagePopover = $popover.find('.note-image-popover');
            if (oStyle.image) {
                showPopover($imagePopover, oStyle.image);
            } else {
                $imagePopover.hide();
            }

            if (isAirMode) {
                var $airPopover = $popover.find('.note-air-popover');
                if (!oStyle.range.isCollapsed()) {
                    var bnd = func.rect2bnd(list.last(oStyle.range.getClientRects()));
                    $airPopover.css({
                        display: 'block',
                        left: Math.max(bnd.left + bnd.width / 2 - PX_POPOVER_ARROW_OFFSET_X, 0),
                        top: bnd.top + bnd.height
                    });
                } else {
                    $airPopover.hide();
                }
            }
        };

        this.updateRecentColor = function (elBtn, sEvent, sValue) {
            button.updateRecentColor(elBtn, sEvent, sValue);
        };

        /**
        * hide all popovers
        * @param {jQuery} $popover - popover contaienr
        */
        this.hide = function ($popover) {
            $popover.children().hide();
        };
    };

    /**
    * Handle
    */
    var Handle = function () {
        /**
        * update handle
        * @param {jQuery} $handle
        * @param {Object} oStyle
        */
        this.update = function ($handle, oStyle) {
            var $selection = $handle.find('.note-control-selection');
            if (oStyle.image) {
                var $image = $(oStyle.image);
                var pos = $image.position();
                // include margin
                var szImage = {
                    w: $image.outerWidth(true),
                    h: $image.outerHeight(true)
                };
                $selection.css({
                    display: 'block',
                    left: pos.left,
                    top: pos.top,
                    width: szImage.w,
                    height: szImage.h
                }).data('target', oStyle.image); // save current image element.
                var sSizing = szImage.w + 'x' + szImage.h;
                $selection.find('.note-control-selection-info').text(sSizing);
            } else {
                $selection.hide();
            }
        };

        this.hide = function ($handle) {
            $handle.children().hide();
        };
    };
    website.no_editor = !!$(document.documentElement).data('editable-no-editor');

    website.add_template_file('/website/static/src/xml/website.editor.xml');
    website.dom_ready.done(function () {
        var is_smartphone = $(document.body)[0].clientWidth < 767;

        if (!is_smartphone) {
            website.ready().then(website.init_editor);
        } else {
            var resize_smartphone = function () {
                is_smartphone = $(document.body)[0].clientWidth < 767;
                if (!is_smartphone) {
                    $(window).off("resize", resize_smartphone);
                    website.init_editor();
                }
            };
            $(window).on("resize", resize_smartphone);
        }

        $(document).on('click', 'a.js_link2post', function (ev) {
            ev.preventDefault();
            website.form(this.pathname, 'POST');
        });

        $(document).on('click', '.note-editable', function (ev) {
            ev.preventDefault();
        });

        $(document).on('submit', '.note-editable form', function (ev) {
            // Disable form submition in editable mode
            ev.preventDefault();
        });

        $(document).on('hide.bs.dropdown', '.dropdown', function (ev) {
            // Prevent dropdown closing when a contenteditable children is focused
            if (ev.originalEvent
                    && $(ev.target).has(ev.originalEvent.target).length
                    && $(ev.originalEvent.target).is('[contenteditable]')) {
                ev.preventDefault();
            }
        });
    });

    /**
     * An editing host is an HTML element with @contenteditable=true, or the
     * child of a document in designMode=on (but that one's not supported)
     *
     * https://dvcs.w3.org/hg/editing/raw-file/tip/editing.html#editing-host
     */
    function is_editing_host(element) {
        return element.attr('contentEditable') === 'false';
    }
    /**
     * Checks that both the element's content *and the element itself* are
     * editable: an editing host is considered non-editable because its content
     * is editable but its attributes should not be considered editable
     */
    function is_editable_node(element) {
        return !(element.data('oe-model') === 'ir.ui.view'
              || element.data('cke-realelement')
              || (is_editing_host(element) && element.getAttribute('attributeEditable') !== 'true'));
    }

    function link_dialog(event) {
        return new website.editor.LinkDialog(false, event, true).appendTo(document.body);
    }

    function image_dialog(editor, image) {
        return new website.editor.MediaDialog(editor, image).appendTo(document.body);
    }

    website.init_editor = function () {
        var editor = new website.EditorBar();
        var $body = $(document.body);
        editor.prependTo($body).then(function () {
            if (location.search.indexOf("enable_editor") >= 0) {
                editor.edit();
            }
        });
        website.editor_bar = editor;
    };

    /* ----- TOP EDITOR BAR FOR ADMIN ---- */
    website.EditorBar = openerp.Widget.extend({
        template: 'website.editorbar',
        events: {
            'click button[data-action=save]': 'save',
            'click a[data-action=cancel]': 'cancel',
        },
        start: function() {
            var self = this;
            this.saving_mutex = new openerp.Mutex();

            this.$buttons = {
                edit: this.$el.parents().find('button[data-action=edit]'),
                save: this.$('button[data-action=save]'),
                cancel: this.$('button[data-action=cancel]'),
            };

            this.$('#website-top-edit').hide();
            this.$('#website-top-view').show();
            this.$buttons.edit.show();

            var $edit_button = this.$buttons.edit
                    .prop('disabled', website.no_editor);
            if (website.no_editor) {
                var help_text = $(document.documentElement).data('editable-no-editor');
                $edit_button.parent()
                    // help must be set on form above button because it does
                    // not appear on disabled button
                    .attr('title', help_text);
            }

            $('.dropdown-toggle').dropdown();

            this.$buttons.edit.click(function(ev) {
                self.edit();
            });

            this.rte = new website.RTE(this);
            this.rte.on('change', this, this.proxy('rte_changed'));
            this.rte.on('rte:ready', this, function () {
                self.setup_hover_buttons();
                self.trigger('rte:ready');
            });

            this.rte.appendTo(this.$('#website-top-edit .nav.js_editor_placeholder'));
            return this._super.apply(this, arguments);
            
        },
        edit: function () {
            this.$buttons.edit.prop('disabled', true);
            this.$('#website-top-view').hide();
            this.$el.show();
            this.$('#website-top-edit').show();
            $('.css_non_editable_mode_hidden').removeClass("css_non_editable_mode_hidden");

            this.rte.start_edition();
            this.trigger('rte:called');
        },
        rte_changed: function () {
            this.$buttons.save.prop('disabled', false);
        },
        save: function () {
            var self = this;

            observer.disconnect();
            var editor = $('.note-air-editor');
            var defs = this.rte.fetch_editables(editor)
                .filter('.oe_dirty')
                .removeAttr('contentEditable')
                .removeClass('oe_dirty oe_editable cke_focus oe_carlos_danger')
                .map(function () {
                    var $el = $(this);
                    // TODO: Add a queue with concurrency limit in webclient
                    // https://github.com/medikoo/deferred/blob/master/lib/ext/function/gate.js
                    return self.saving_mutex.exec(function () {
                        return self.saveElement($el)
                            .then(undefined, function (thing, response) {
                                // because ckeditor regenerates all the dom,
                                // we can't just setup the popover here as
                                // everything will be destroyed by the DOM
                                // regeneration. Add markings instead, and
                                // returns a new rejection with all relevant
                                // info
                                var id = _.uniqueId('carlos_danger_');
                                $el.addClass('oe_dirty oe_carlos_danger');
                                $el.addClass(id);
                                return $.Deferred().reject({
                                    id: id,
                                    error: response.data,
                                });
                            });
                    });
                }).get();
            return $.when.apply(null, defs).then(function () {
                website.reload();
            }, function (failed) {
                // If there were errors, re-enable edition
                self.rte.start_edition(true).then(function () {
                    // jquery's deferred being a pain in the ass
                    if (!_.isArray(failed)) { failed = [failed]; }

                    _(failed).each(function (failure) {
                        var html = failure.error.exception_type === "except_osv";
                        if (html) {
                            var msg = $("<div/>").text(failure.error.message).html();
                            var data = msg.substring(3,msg.length-2).split(/', u'/);
                            failure.error.message = '<b>' + data[0] + '</b><br/>' + data[1];
                        }
                        $(root).find('.' + failure.id)
                            .removeClass(failure.id)
                            .popover({
                                html: html,
                                trigger: 'hover',
                                content: failure.error.message,
                                placement: 'auto top',
                            })
                            // Force-show popovers so users will notice them.
                            .popover('show');
                    });
                });
            });
        },
        /**
         * Saves an RTE content, which always corresponds to a view section (?).
         */
        saveElement: function ($el) {
            var markup = $el.prop('outerHTML');
            return openerp.jsonRpc('/web/dataset/call', 'call', {
                model: 'ir.ui.view',
                method: 'save',
                args: [$el.data('oe-id'), markup,
                       $el.data('oe-xpath') || null,
                       website.get_context()],
            });
        },
        cancel: function () {
            new $.Deferred(function (d) {
                var $dialog = $(openerp.qweb.render('website.editor.discard')).appendTo(document.body);
                $dialog.on('click', '.btn-danger', function () {
                    d.resolve();
                }).on('hidden.bs.modal', function () {
                    d.reject();
                });
                d.always(function () {
                    $dialog.remove();
                });
                $dialog.modal('show');
            }).then(function () {
                website.reload();
            })
        },

        /**
         * Creates a "hover" button for link edition
         *
         * @param {Function} editfn edition function, called when clicking the button
         * @returns {jQuery}
         */
        make_hover_button_link: function (editfn) {
            return $(openerp.qweb.render('website.editor.hoverbutton.link', {}))
                .hide()
                .click(function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    editfn.call(this, e);
                })
                .appendTo(document.body);
        },

        /**
         * Creates a "hover" button for image
         *
         * @param {Function} editfn edition function, called when clicking the button
         * @param {Function} stylefn edition style function, called when clicking the button
         * @returns {jQuery}
         */
        make_hover_button_image: function (editfn, stylefn) {
            var $div = $(openerp.qweb.render('website.editor.hoverbutton.media', {}))
                .hide()
                .appendTo(document.body);

            $div.find('[data-toggle="dropdown"]').dropdown();
            $div.find(".hover-edition-button").click(function (e) {
                e.preventDefault();
                e.stopPropagation();
                editfn.call(this, e);
            });
            if (stylefn) {
                $div.find(".hover-style-button").click(function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    stylefn.call(this, e);
                });
            }
            return $div;
        },
        /**
         * For UI clarity, during RTE edition when the user hovers links and
         * images a small button should appear to make the capability clear,
         * as not all users think of double-clicking the image or link.
         */
        setup_hover_buttons: function () {
            var editor = $('.note-air-editor');
            var $link_button = this.make_hover_button_link(function () {
                link_dialog(previous);
                previous = null;
            });

            // previous is the state of the button-trigger: it's the
            // currently-ish hovered element which can trigger a button showing.
            // -ish, because when moving to the button itself ``previous`` is
            // still set to the element having triggered showing the button.
            var previous;
            $(editor).on('mouseover', 'a', function () {
                // Back from edit button -> ignore
                var element = $(this).closest('[data-oe-field]');
                if (previous && previous === this) { return; }
                if (is_editable_node(element)) { return; }
                previous = this;
                var $selected = $(this);
                var position = $selected.offset();
                $link_button.show().offset({
                    top: $selected.outerHeight()
                            + position.top,
                    left: $selected.outerWidth() / 2
                            + position.left
                            - $link_button.outerWidth() / 2
                })
            }).on('mouseleave', 'a, img, .fa', function (e) {
                var current = document.elementFromPoint(e.clientX, e.clientY);
                if (current === $link_button[0] || $(current).parent()[0] === $link_button[0]) {
                    return;
                }
                $link_button.hide();
                previous = null;
            });
        },
    });
    
    website.EditorBarCustomize = openerp.Widget.extend({
        events: {
            'mousedown a.dropdown-toggle': 'load_menu',
            'click ul a[data-action!=ace]': 'do_customize',
        },
        start: function() {
            var self = this;
            this.$menu = self.$el.find('ul');
            this.view_name = $(document.documentElement).data('view-xmlid');
            if (!this.view_name) {
                this.$el.hide();
            }
            this.loaded = false;
        },
        load_menu: function () {
            var self = this;
            if(this.loaded) {
                return;
            }
            openerp.jsonRpc('/website/customize_template_get', 'call', { 'xml_id': this.view_name }).then(
                function(result) {
                    _.each(result, function (item) {
                        if (item.xml_id === "website.debugger" && !window.location.search.match(/[&?]debug(&|$)/)) return;
                        if (item.header) {
                            self.$menu.append('<li class="dropdown-header">' + item.name + '</li>');
                        } else {
                            self.$menu.append(_.str.sprintf('<li role="presentation"><a href="#" data-view-id="%s" role="menuitem"><strong class="fa fa%s-square-o"></strong> %s</a></li>',
                                item.id, item.active ? '-check' : '', item.name));
                        }
                    });
                    self.loaded = true;
                }
            );
        },
        do_customize: function (event) {
            var view_id = $(event.currentTarget).data('view-id');
            return openerp.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'ir.ui.view',
                method: 'toggle',
                args: [],
                kwargs: {
                    ids: [parseInt(view_id, 10)],
                    context: website.get_context()
                }
            }).then( function() {
                window.location.reload();
            });
        },
    });

    $(document).ready(function() {
        var editorBarCustomize = new website.EditorBarCustomize();
        editorBarCustomize.setElement($('li[id=customize-menu]'));
        editorBarCustomize.start();
    });

    /* ----- RICH TEXT EDITOR ---- */
    website.RTE = openerp.Widget.extend({
        init: function (EditorBar) {
            this.EditorBar = EditorBar;
            $('.inline-media-link').remove();
            this._super.apply(this, arguments);
        },
        tableNavigation: function (root) {
            var self = this;
            $(root).on('keydown', function (e) {
                // ignore non-TAB
                if (e.which !== 9) { return; }

                if (self.handleTab(e)) {
                    e.preventDefault();
                }
            });
        },
        /**
         * Performs whatever operation is necessary on a [TAB] hit, returns
         * ``true`` if the event's default should be cancelled (if the TAB was
         * handled by the function)
         */
        handleTab: function (event) {
            var forward = !event.shiftKey;

            var root = window.getSelection().getRangeAt(0).commonAncestorContainer;
            var $cell = $(root).closest('td,th');

            if (!$cell.length) { return false; }

            var cell = $cell[0];

            // find cell in same row
            var row = cell.parentNode;
            var sibling = row.cells[cell.cellIndex + (forward ? 1 : -1)];
            if (sibling) {
                document.getSelection().selectAllChildren(sibling);
                return true;
            }

            // find cell in previous/next row
            var table = row.parentNode;
            var sibling_row = table.rows[row.rowIndex + (forward ? 1 : -1)];
            if (sibling_row) {
                var new_cell = sibling_row.cells[forward ? 0 : sibling_row.cells.length - 1];
                document.getSelection().selectAllChildren(new_cell);
                return true;
            }

            // at edge cells, copy word/openoffice behavior: if going backwards
            // from first cell do nothing, if going forwards from last cell add
            // a row
            if (forward) {
                var row_size = row.cells.length;
                var new_row = document.createElement('tr');
                while(row_size--) {
                    var newcell = document.createElement('td');
                    // zero-width space
                    newcell.textContent = '\u200B';
                    new_row.appendChild(newcell);
                }
                table.appendChild(new_row);
                document.getSelection().selectAllChildren(new_row.cells[0]);
            }

            return true;
        },
        /**
         * Makes the page editable
         *
         * @param {Boolean} [restart=false] in case the edition was already set
         *                                  up once and is being re-enabled.
         * @returns {$.Deferred} deferred indicating when the RTE is ready
         */
        start_edition: function (restart) {
            var self = this;
            // create a single editor for the whole page
            var root = document.getElementById('wrapwrap');
            if (!restart) {
                $(root).on('dragstart', 'img', function (e) {
                    e.preventDefault();
                });
                this.tableNavigation(root);
            }
            var def = $.Deferred();
            this.editor = new openerp.website.summernote(self._config(root, def));
            return def;
        },
        setup_editables: function (root) {
            // selection of editable sub-items was previously in
            // EditorBar#edit, but for some unknown reason the elements were
            // apparently removed and recreated (?) at editor initalization,
            // and observer setup was lost.
            var self = this;
            // setup dirty-marking for each editable element
            this.fetch_editables(root)
                .addClass('oe_editable')
                .each(function () {
                    var node = this;
                    var $node = $(node);
                    // only explicitly set contenteditable on view sections,
                    // cke widgets system will do the widgets themselves
                    if ($node.data('oe-model') === 'ir.ui.view') {
                        node.contentEditable = true;
                    }
                    observer.observe(node, OBSERVER_CONFIG);
                    $node.one('content_changed', function () {
                        $node.addClass('oe_dirty');
                        self.trigger('change');
                    });
                });
        },
        fetch_editables: function (root) {
            return $(root).find('[data-oe-model]')
                .not('link, script')
                .not('.oe_snippet_editor')
                .filter(function () {
                    var $this = $(this);
                    // keep view sections and fields which are *not* in
                    // view sections for top-level editables
                    return $this.data('oe-model') === 'ir.ui.view'
                       || !$this.closest('[data-oe-model = "ir.ui.view"]').length;
                });
        },
        _config: function (root, def) {
            var self = this;
             return {
                content : $('#wrapwrap'),
                airMode : true,
                airPopover: [
                    ['style', ['style']],
                    ['font', ['bold', 'italic', 'underline', 'clear']],
                    ['fontsize', ['fontsize']],
                    ['color', ['color']],
                    ['para', ['ul', 'ol', 'paragraph']],
                    ['table', ['table']],
                    ['insert', ['link', 'picture']],
                ],
                oninit: function() {
                  self.setup_editables(root);
                  self.trigger('rte:ready');
                  def.resolve();
                },
                styleWithSpan: false,
                inlinemedia : ['p'],
                onpaste: function(e) {
                    e.preventDefault();
                    var text = (e.originalEvent || e).clipboardData.getData('text/plain') || prompt('Paste something..');
                    document.execCommand('insertText', false, text);
                },
             }
        }
    });

    website.summernote = openerp.Widget.extend({
        init: function(options) {
            var self = this ;
            self.settings = $.extend({}, defaults.options, options);
            self.renderer = new website.summernote.Renderer(self.settings);
            self.do_render(self);
        },
        do_render: function() {
            var self = this;
            self.settings.content.each(function (idx, elHolder) {
                var $holder = $(elHolder);
                // createLayout with options
                self.renderer.createLayout($holder);

                var info = self.renderer.layoutInfoFromHolder($holder);
                var eventHandler = new website.summernote.eventHandler(self.settings);
                eventHandler.attach(info, self.settings);

                // Textarea: auto filling the code before form submit.
                if (dom.isTextarea($holder[0])) {
                    $holder.closest('form').submit(function () {
                        $holder.html($holder.code());
                    });
                }
            });

            $.each(self.settings.inlinemedia , function (index,value) {
                $(value).each(function(i, v){
                    if (!$(this).next().hasClass('inline-media-link')) {
                        $(this).after(openerp.qweb.render('website.editor.insert.inline.media', {}));
                        $(this).next('.inline-media-link').attr('id', 'inline-media-link-'+ i);
                    }
                });
            });
            // callback on init
            if (self.settings.content.length > 0 && self.settings.oninit) {
                self.settings.oninit();
            }
        },
    });
    website.summernote.eventHandler = openerp.Widget.extend({
        init: function(settings) {
            this.editor = new Editor(); //new website.summernote.editor();
            this.toolbar = new Toolbar(); //new website.summernote.toolbar();
            this.popover = new Popover(); //new website.summernote.popover();
            this.handle = new Handle(); //new website.summernote.handle();
        },
        insertImages : function ($editable, files) {
            var self = this ;
            self.editor.restoreRange($editable);
            var callbacks = $editable.data('callbacks');

            // If onImageUpload options setted
            if (callbacks.onImageUpload) {
                callbacks.onImageUpload(files, editor, $editable);
            // else insert Image as dataURL
            } else {
                $.each(files, function (idx, file) {
                    async.readFileAsDataURL(file).then(function (sDataURL) {
                        self.editor.insertImage($editable, sDataURL);
                    }).fail(function () {
                        if (callbacks.onImageUploadError) {
                          callbacks.onImageUploadError();
                        }
                    });
                });
            }
        },
        hMousedown : function (event) {
            //preventDefault Selection for FF, IE8+
            if (dom.isImg(event.target)) {
                event.preventDefault();
            }
        },
        hMouseover : function (event) {
            var self = this;
            var element = $(event.target).closest('[data-oe-field]')
            if(is_editable_node(element)) { element.addClass('note-wrapper-editable'); return;}
        },
        hToolbarAndPopoverUpdate : function (event) {
            var self = this;
            var element = $(event.target).closest('[data-oe-field]')
            if(is_editable_node(element) && !$(event.target).hasClass('editor-insert-media')) { return; }
            // delay for range after mouseup
            setTimeout(function () {
                var oLayoutInfo = self.makeLayoutInfo(event.currentTarget || event.target);
                var oStyle = self.editor.currentStyle(event.target);
                if (!oStyle) { return; }

                var isAirMode = oLayoutInfo.editor().data('options').airMode;
                if (!isAirMode) {
                    self.toolbar.update(oLayoutInfo.toolbar(), oStyle);
                }
                self.popover.update(oLayoutInfo.popover(), oStyle, isAirMode);
                self.handle.update(oLayoutInfo.handle(), oStyle);
            }, 0);
        },
        hScroll : function (event) {
            var self = this;
            var oLayoutInfo = self.makeLayoutInfo(event.currentTarget || event.target);
            //hide popover and handle when scrolled
            self.popover.hide(oLayoutInfo.popover());
            self.handle.hide(oLayoutInfo.handle());
        },
        hPasteClipboardImage : function (event) {
            var self = this;
            var originalEvent = event.originalEvent;
            if (!originalEvent.clipboardData ||
                !originalEvent.clipboardData.items ||
                !originalEvent.clipboardData.items.length) {return;}

            var oLayoutInfo = self.makeLayoutInfo(event.currentTarget || event.target);
            var item = list.head(originalEvent.clipboardData.items);
            var bClipboardImage = item.kind === 'file' && item.type.indexOf('image/') !== -1;

            if (bClipboardImage) {
                self.insertImages(oLayoutInfo.editable(), [item.getAsFile()]);
            }
        },
        hHandleMousedown : function (event) {
            var self = this;
            if (dom.isControlSizing(event.target)) {
                event.preventDefault();
                event.stopPropagation();

                var oLayoutInfo = self.makeLayoutInfo(event.target),
                    $handle = oLayoutInfo.handle(), $popover = oLayoutInfo.popover(),
                    $editable = oLayoutInfo.editable();

                var elTarget = $handle.find('.note-control-selection').data('target'),
                    $target = $(elTarget), posStart = $target.offset(),
                    scrollTop = $document.scrollTop();

                $document.on('mousemove', function (event) {
                  self.editor.resizeTo({
                    x: event.clientX - posStart.left,
                    y: event.clientY - (posStart.top - scrollTop)
                  }, $target, !event.shiftKey);

                  self.handle.update($handle, {image: elTarget});
                  self.popover.update($popover, {image: elTarget});
                }).one('mouseup', function () {
                  $document.off('mousemove');
                });

                if (!$target.data('ratio')) { // original ratio.
                  $target.data('ratio', $target.height() / $target.width());
                }

                self.editor.recordUndo($editable);
            }
        },
        hToolbarAndPopoverMousedown : function (event) {
            // prevent default event when insertTable (FF, Webkit)
            var $btn = $(event.target).closest('[data-event]');
            if ($btn.length > 0) {
                event.preventDefault();
            }
        },
        hToolbarAndPopoverClick : function (event) {
            var self = this;
            var $btn = $(event.target).closest('[data-event]');
            if ($btn.length > 0) {
                var sEvent = $btn.attr('data-event'), sValue = $btn.attr('data-value');
                var oLayoutInfo = self.makeLayoutInfo(event.target);
                var $dialog = oLayoutInfo.dialog(),
                $editable = oLayoutInfo.editable();

                // before command: detect control selection element($target)
                var $target;
                if ($.inArray(sEvent, ['resize', 'floatMe', 'removeMedia']) !== -1) {
                    var $selection = oLayoutInfo.handle().find('.note-control-selection');
                    $target = $($selection.data('target'));
                }
                if (self.editor[sEvent]) { // on command
                    $editable.trigger('focus');
                    self.editor[sEvent]($editable, sValue, $target);
                }
                // after command
                if ($.inArray(sEvent, ['backColor', 'foreColor']) !== -1) {
                    var options = oLayoutInfo.editor().data('options', options);
                    var module = options.airMode ? attachDragAndDropEventpopover : toolbar;
                    module.updateRecentColor(list.head($btn), sEvent, sValue);
                } else if (sEvent === 'showLinkDialog') { // popover to dialog
                    $editable.focus();
                    self.editor.saveRange($editable);
                    return new  website.editor.LinkDialog(self.editor, $editable).appendTo(document.body);
                } else if (sEvent === 'showImageDialog') {
                    $editable.focus();
                    new website.editor.MediaDialog(self.editor, '').appendTo(document.body);
                    self.editor.restoreRange($editable);
                }
                self.hToolbarAndPopoverUpdate(event);
            }
        },
        hStatusbarMousedown : function (event) {
            var self = this;
            var EDITABLE_PADDING = 24;
            event.preventDefault();
            event.stopPropagation();

            var $editable = self.makeLayoutInfo(event.target).editable();
            var nEditableTop = $editable.offset().top - $document.scrollTop();

            var oLayoutInfo = self.makeLayoutInfo(event.currentTarget || event.target);
            var options = oLayoutInfo.editor().data('options');

            $document.on('mousemove', function (event) {
                var nHeight = event.clientY - (nEditableTop + EDITABLE_PADDING);

                nHeight = (options.minHeight > 0) ? Math.max(nHeight, options.minHeight) : nHeight;
                nHeight = (options.maxHeight > 0) ? Math.min(nHeight, options.maxHeight) : nHeight;

                $editable.height(nHeight);
            }).one('mouseup', function () {
                $document.off('mousemove');
            });
        },
        hDimensionPickerMove : function (event) {
            var self = this;
            var PX_PER_EM = 18;
            var $picker = $(event.target.parentNode); // target is mousecatcher
            var $dimensionDisplay = $picker.next();
            var $catcher = $picker.find('.note-dimension-picker-mousecatcher');
            var $highlighted = $picker.find('.note-dimension-picker-highlighted');
            var $unhighlighted = $picker.find('.note-dimension-picker-unhighlighted');

            var posOffset;
            // HTML5 with jQuery - e.offsetX is undefined in Firefox
            if (event.offsetX === undefined) {
                var posCatcher = $(event.target).offset();
                posOffset = {
                    x: event.pageX - posCatcher.left,
                    y: event.pageY - posCatcher.top
                };
            } else {
                posOffset = {
                    x: event.offsetX,
                    y: event.offsetY
                };
            }

            var dim = {
                c: Math.ceil(posOffset.x / PX_PER_EM) || 1,
                r: Math.ceil(posOffset.y / PX_PER_EM) || 1
            };

            $highlighted.css({ width: dim.c + 'em', height: dim.r + 'em' });
            $catcher.attr('data-value', dim.c + 'x' + dim.r);

            if (3 < dim.c && dim.c < 10) { // 5~10
                $unhighlighted.css({ width: dim.c + 1 + 'em'});
            }

            if (3 < dim.r && dim.r < 10) { // 5~10
                $unhighlighted.css({ height: dim.r + 1 + 'em'});
            }

            $dimensionDisplay.html(dim.c + ' x ' + dim.r);
        },
        attachDragAndDropEvent : function (oLayoutInfo) {
            var self = this;
            var collection = $(), $dropzone = oLayoutInfo.dropzone,
            $dropzoneMessage = oLayoutInfo.dropzone.find('.note-dropzone-message');

            // show dropzone on dragenter when dragging a object to document.
            $document.on('dragenter', function (e) {
                var bCodeview = oLayoutInfo.editor.hasClass('codeview');
                if (!bCodeview && collection.length === 0) {
                    oLayoutInfo.editor.addClass('dragover');
                    $dropzone.width(oLayoutInfo.editor.width());
                    $dropzone.height(oLayoutInfo.editor.height());
                    $dropzoneMessage.text('Drag Image Here');
                }
                collection = collection.add(e.target);
            }).on('dragleave', function (e) {
                collection = collection.not(e.target);
                if (collection.length === 0) {
                    oLayoutInfo.editor.removeClass('dragover');
                }
            }).on('drop', function () {
                collection = $();
                oLayoutInfo.editor.removeClass('dragover');
            });
            // change dropzone's message on hover.
            $dropzone.on('dragenter', function () {
                $dropzone.addClass('hover');
                $dropzoneMessage.text('Drop Image');
            }).on('dragleave', function () {
                $dropzone.removeClass('hover');
                $dropzoneMessage.text('Drag Image Here');
            });
            // attach dropImage
            $dropzone.on('drop', function (event) {
                event.preventDefault();
                var dataTransfer = event.originalEvent.dataTransfer;
                if (dataTransfer && dataTransfer.files) {
                    var oLayoutInfo = self.makeLayoutInfo(event.currentTarget || event.target);
                    oLayoutInfo.editable().focus();
                    self.insertImages(oLayoutInfo.editable(), dataTransfer.files);
                }
            }).on('dragover', false); // prevent default dragover event
        },
        bindKeyMap : function (oLayoutInfo, keyMap) {
            var self = this;
            var $editor = oLayoutInfo.editor;
            var $editable = oLayoutInfo.editable;
            $editable.on('keydown', function (event) {
                var aKey = [];
                // modifier
                if (event.metaKey) { aKey.push('CMD'); }
                if (event.ctrlKey) { aKey.push('CTRL'); }
                if (event.shiftKey) { aKey.push('SHIFT'); }
                // keycode
                var keyName = key.nameFromCode[event.keyCode];
                if (keyName) { aKey.push(keyName); }
                var handler = keyMap[aKey.join('+')];
                if (handler) {
                  event.preventDefault();
                  self.editor[handler]($editable, $editor.data('options'));
                } 
            });
        },
        attach : function (oLayoutInfo, options) {
            // handlers for editable
            var self = this;
            this.bindKeyMap(oLayoutInfo, options.keyMap[agent.bMac ? 'mac' : 'pc']);
            oLayoutInfo.editable.on('mousedown', self.hMousedown.bind(self));
            oLayoutInfo.editable.on('keyup mouseup', self.hToolbarAndPopoverUpdate.bind(self));
            oLayoutInfo.editable.on('scroll', self.hScroll.bind(self));
            oLayoutInfo.editable.on('paste', self.hPasteClipboardImage.bind(self));
            // handler for handle and popover
            oLayoutInfo.handle.on('mousedown', self.hHandleMousedown.bind(self));
            oLayoutInfo.popover.on('click', self.hToolbarAndPopoverClick.bind(self));
            oLayoutInfo.popover.on('mousedown', self.hToolbarAndPopoverMousedown.bind(self));
            oLayoutInfo.editable.on('mouseover' , self.hMouseover.bind(self));
            // handlers for frame mode (toolbar, statusbar)
            if (!options.airMode) {
                // handler for drag and drop
                if (!options.disableDragAndDrop) {
                    self.attachDragAndDropEvent(oLayoutInfo);
                }
                // handler for toolbar
                oLayoutInfo.toolbar.on('click', self.hToolbarAndPopoverClick.bind(self));
                oLayoutInfo.toolbar.on('mousedown', self.hToolbarAndPopoverMousedown.bind(self));
                // handler for statusbar
                if (!options.disableResizeEditor) {
                    oLayoutInfo.statusbar.on('mousedown', self.hStatusbarMousedown.bind(self));
                }
            }
            // handler for table dimension
            var $catcherContainer = options.airMode ? oLayoutInfo.popover :
                                                    oLayoutInfo.toolbar;
            var $catcher = $catcherContainer.find('.note-dimension-picker-mousecatcher');
            $catcher.on('mousemove', self.hDimensionPickerMove);
            // save selection when focusout
            oLayoutInfo.editable.on('blur', function () {
                self.editor.saveRange(oLayoutInfo.editable);
            });
            // save options on editor
            oLayoutInfo.editor.data('options', options);
            // ret styleWithCSS for backColor / foreColor clearing with 'inherit'.
            if (options.styleWithSpan && !agent.bMSIE) {
                // protect FF Error: NS_ERROR_FAILURE: Failure
                setTimeout(function () {
                    document.execCommand('styleWithCSS', 0, true);
                }, 0);
            }
            // History
            oLayoutInfo.editable.data('NoteHistory', new History());
            // basic event callbacks (lowercase)
            // enter, focus, blur, keyup, keydown
            if (options.onenter) {
                oLayoutInfo.editable.keypress(function (event) {
                    if (event.keyCode === key.ENTER) { options.onenter(event); }
                });
            }
            if (options.onfocus) { oLayoutInfo.editable.focus(options.onfocus); }
            if (options.onblur) { oLayoutInfo.editable.blur(options.onblur); }
            if (options.onkeyup) { oLayoutInfo.editable.keyup(options.onkeyup); }
            if (options.onkeydown) { oLayoutInfo.editable.keydown(options.onkeydown); }
            if (options.onpaste) { oLayoutInfo.editable.on('paste', options.onpaste); }
            // callbacks for advanced features (camel)
            if (options.onToolbarClick) { oLayoutInfo.toolbar.click(options.onToolbarClick); }
            if (options.onChange) {
                var hChange = function () {
                    options.onChange(oLayoutInfo.editable, oLayoutInfo.editable.html());
                };
                if (agent.bMSIE) {
                    var sDomEvents = 'DOMCharacterDataModified, DOMSubtreeModified, DOMNodeInserted';
                    oLayoutInfo.editable.on(sDomEvents, hChange);
                } else {
                    oLayoutInfo.editable.on('input', hChange);
                }
            }
            // All editor status will be saved on editable with jquery's data
            // for support multiple editor with singleton object.
            oLayoutInfo.editable.data('callbacks', {
                onAutoSave: options.onAutoSave,
                onImageUpload: options.onImageUpload,
                onImageUploadError: options.onImageUploadError,
                onFileUpload: options.onFileUpload,
                onFileUploadError: options.onFileUpload
            });
        },
        dettach : function (oLayoutInfo) {
            oLayoutInfo.editable.off();
            oLayoutInfo.popover.off();
            oLayoutInfo.handle.off();
            oLayoutInfo.dialog.off();
            if (oLayoutInfo.editor.data('options').airMode) {
                oLayoutInfo.dropzone.off();
                oLayoutInfo.toolbar.off();
                oLayoutInfo.statusbar.off();
            }
        },
        makeLayoutInfo : function (descendant) {
            var $target = $(descendant).closest('.note-editor, .note-air-editor, .note-air-layout');
            if ($target.length === 0) { return null; }
            var $editor;
            if ($target.is('.note-editor, .note-air-editor')) {
                $editor = $target;
            } else {
                $editor = $('#note-editor-' + list.last($target.attr('id').split('-')));
            }
            return dom.buildLayoutInfo($editor);
        }
    });
    website.summernote.Renderer = openerp.Widget.extend({
        init: function(settings) {
            var self = this ;
            self.settings = settings;
        },
        createLayout : function($holder) {
            var self = this;
            if (this.noteEditorFromHolder($holder).length > 0) { return; }
            if (self.settings.airMode) { self.createLayoutByAirMode($holder); }
        },
        createLayoutByAirMode : function ($holder) {
            var self = this;
            var keyMap = self.settings.keyMap[agent.bMac ? 'mac' : 'pc'];
            var langInfo = defaults.lang[self.settings.lang];
            var id = _.uniqueId();
            $holder.addClass('note-air-editor note-editable');
            $holder.attr({
                'id': 'note-editor-' + id,
                'contentEditable': true
            });
            var body = document.body;
            // create Popover
            var $popover = $(openerp.qweb.render('website.editor.tplPopovers',{options : self.settings , buttonInfo : tplButtonInfo , lang : langInfo}));
            $popover.addClass('note-air-layout');
            $popover.attr('id', 'note-popover-' + id);
            $popover.appendTo(body);
            self.createTooltip($popover, keyMap);
            self.createPalette($popover, self.settings);
            // create Handle
            var $handle = $(openerp.qweb.render('website.editor.tplHandles', {}));
            $handle.addClass('note-air-layout');
            $handle.attr('id', 'note-handle-' + id);
            $handle.appendTo(body);
        },
        createTooltip : function ($container, keyMap, sPlacement) {
            var self = this;
            var invertedKeyMap = func.invertObject(keyMap);
            var $buttons = $container.find('button');

            $buttons.each(function (i, elBtn) {
                var $btn = $(elBtn);
                var sShortcut = invertedKeyMap[$btn.data('event')];
                if (sShortcut) {
                    $btn.attr('title', function (i, v) {
                        return v + ' (' + self.representShortcut(sShortcut) + ')';
                    });
                }
            // bootstrap tooltip on btn-group bug
            // https://github.com/twitter/bootstrap/issues/5687
            }).tooltip({
                container: 'body',
                trigger: 'hover',
                placement: sPlacement || 'top'
            }).on('click', function () {
                $(this).tooltip('hide');
            });
        },
        createPalette : function ($container, options) {
            var aaColor = options.colors;
            $container.find('.note-color-palette').each(function () {
                var $palette = $(this), sEvent = $palette.attr('data-target-event');
                var aPaletteContents = [];
                for (var row = 0, szRow = aaColor.length; row < szRow; row++) {
                    var aColor = aaColor[row];
                    var aButton = [];
                    for (var col = 0, szCol = aColor.length; col < szCol; col++) {
                    var sColor = aColor[col];
                    aButton.push(['<button type="button" class="note-color-btn" style="background-color:', sColor,
                        ';" data-event="', sEvent,
                        '" data-value="', sColor,
                        '" title="', sColor,
                        '" data-toggle="button" tabindex="-1"></button>'].join(''));
                    }
                    aPaletteContents.push('<div>' + aButton.join('') + '</div>');
                }
                $palette.html(aPaletteContents.join(''));
            });
        },
        representShortcut : function (str) {
            if (agent.bMac) {
                str = str.replace('CMD', '⌘').replace('SHIFT', '⇧');
            }
            return str.replace('BACKSLASH', '\\')
                .replace('SLASH', '/')
                .replace('LEFTBRACKET', '[')
                .replace('RIGHTBRACKET', ']');
        },
        layoutInfoFromHolder : function ($holder) {
            var $editor = this.noteEditorFromHolder($holder);
            if (!$editor.length) { return; }

            var layoutInfo = dom.buildLayoutInfo($editor);
            // cache all properties.
            for (var key in layoutInfo) {
                if (layoutInfo.hasOwnProperty(key)) {
                    layoutInfo[key] = layoutInfo[key].call();
                }
            }
            return layoutInfo;
        },
        noteEditorFromHolder : function($holder) {
            if ($holder.hasClass('note-air-editor')) {
                return $holder;
            } else if ($holder.next().hasClass('note-editor')) {
                return $holder.next();
            } else {
                return $();
            }
        },
        removeLayout : function ($holder) {
            var info = this.layoutInfoFromHolder($holder);
            if (!info) { return; }
            $holder.html(info.editable.html());
            info.editor.remove();
            $holder.show();
        },
    });

    website.editor = { };
    website.editor.Dialog = openerp.Widget.extend({
        events: {
            'hidden.bs.modal': 'destroy',
            'click button.save': 'save',
            'click button[data-dismiss="modal"]': 'cancel',
        },
        init: function (editor, editable) {
            this._super();
            this.editor = editor;
            this.editable = editable;
        },
        start: function () {
            var sup = this._super();
            this.$el.modal({backdrop: 'static'});
            this.$('input:first').focus();
            return sup;
        },
        save: function () {
            this.close();
            this.trigger("saved");
        },
        cancel: function () {
            this.trigger("cancel");
        },
        close: function () {
            this.$el.modal('hide');
        },
    });

    website.editor.LinkDialog = website.editor.Dialog.extend({
        template: 'website.editor.dialog.link',
        events: _.extend({}, website.editor.Dialog.prototype.events, {
            'change :input.url-source': function (e) { this.changed($(e.target)); },
            'mousedown': function (e) {
                var $target = $(e.target).closest('.list-group-item');
                if (!$target.length || $target.hasClass('active')) {
                    // clicked outside groups, or clicked in active groups
                    return;
                }
                this.changed($target.find('.url-source').filter(':input'));
            },
            'click button.remove': 'remove_link',
            'change input#link-text': function (e) {
                this.text = $(e.target).val()
            },
        }),
        init: function (editor, editable , is_custome) {
            this._super(editor, editable);
            this.text = null;
            // Store last-performed request to be able to cancel/abort it.
            this.page_exists_req = null;
            this.search_pages_req = null;
            if(!is_custome){
                this.editable.focus();
                this.editor.saveRange(this.editable);
            }
            this.is_custome = is_custome;
        },
        start: function () {
            var self = this;
            this.linkInfo = self.get_linkinfo();
            var last;
            this.$('#link-page').select2({
                minimumInputLength: 1,
                placeholder: _t("New or existing page"),
                query: function (q) {
                    if (q.term == last) return;
                    last = q.term;
                    $.when(
                        self.page_exists(q.term),
                        self.fetch_pages(q.term)
                    ).then(function (exists, results) {
                        var rs = _.map(results, function (r) {
                            return { id: r.url, text: r.name, };
                        });
                        if (!exists) {
                            rs.push({
                                create: true,
                                id: q.term,
                                text: _.str.sprintf(_t("Create page '%s'"), q.term),
                            });
                        }
                        q.callback({
                            more: false,
                            results: rs
                        });
                    }, function () {
                        q.callback({more: false, results: []});
                    });
                },
            });
            return this._super().then(this.proxy('bind_data'));
        },
        save: function () {
            var self = this, _super = this._super.bind(this);
            var $e = this.$('.list-group-item.active .url-source').filter(':input');
            var val = $e.val();
            if (!val || !$e[0].checkValidity()) {
                // FIXME: error message
                $e.closest('.form-group').addClass('has-error');
                $e.focus();
                return;
            }

            var done = $.when();
            if ($e.hasClass('email-address')) {
                this.make_link(val, false, this.text || this.linkInfo.text);
            } else if ($e.hasClass('page')) {
                var data = $e.select2('data');
                if (!data.create) {
                    self.make_link(data.id, false, data.text);
                } else {
                    // Create the page, get the URL back
                    done = $.get(_.str.sprintf(
                            '/website/add/%s?noredirect=1', encodeURI(data.id)))
                        .then(function (response) {
                            self.make_link(response, false, data.id);
                        });
                }
            } else {
                this.make_link(val, this.$('input.window-new').prop('checked') , this.text || this.linkInfo.text);
            }
            done.then(_super);
        },
        make_link : function(url , new_window , label){
            var self =  this;
            var href = url;
            if (url.indexOf('@') !== -1 && url.indexOf(':') === -1) {
                href =  'mailto:' + url;
            } else if (url.indexOf('://') === -1) {
                href = 'http://' + url;
            }
            if(this.is_custome) {
                self.update_link(this.editable, href , new_window , label)
            } else {
                var rng = range.create();
                this.editor.restoreRange(this.editable);
                this.editor.recordUndo(this.editable); 

                // createLink when range collapsed (IE, Firefox).
                if ((agent.bMSIE || agent.bFF) && rng.isCollapsed()) {
                    rng.insertNode($('<A id="linkAnchor">' + label + '</A>')[0]);
                    var $anchor = $('#linkAnchor').attr('href', href).removeAttr('id');
                    rng = range.createFromNode($anchor[0]);
                    rng.select();
                } else {
                    document.execCommand('createlink', false, href);
                }
                // update link text
                $.each(rng.nodes(dom.isAnchor), function (idx, elAnchor) {
                    self.update_link(elAnchor, href , new_window , label)
                });
            }
        },
        update_link : function(target , href , new_window , label) {
            $(target).html(label);
            $(target).attr('href', href)
            if (new_window) {
                $(target).attr('target', '_blank');
            } else {
                $(target).removeAttr('target');
            }
        },
        bind_data: function (text, href, new_window) {
            href = this.linkInfo.url;
            if (new_window === undefined) {
                new_window = this.linkInfo.new_window;
            }
            if (text === undefined) {
                text = this.linkInfo.text;
            }
            this.$('input#link-text').val(text);
            this.$('input.window-new').prop('checked', new_window);

            if (!href) { return; }
            var match, $control;
            if ((match = /mailto:(.+)/.exec(href))) {
                $control = this.$('input.email-address').val(match[1]);
            }
            if (!$control) {
                $control = this.$('input.url').val(href);
            }

            this.changed($control);
        },
        get_linkinfo : function() {
            var rng = range.create();
            var new_window = true;
            var url = '';
            if(this.is_custome){
                rng = document.createRange();
                rng.selectNodeContents(this.editable)
                url = $(this.editable).attr('href')
                new_window = $(this.editable).attr('target')
            }
            else if (rng.isOnAnchor()) {
                var elAnchor = dom.ancestor(rng.sc, dom.isAnchor);
                rng = range.createFromNode(elAnchor);
                new_window = $(elAnchor).attr('target') === '_blank';
                url = elAnchor.href;
            }
            return {
                text: rng.toString(),
                url: url,
                new_window: new_window
            };
        },
        changed: function ($e) {
            this.$('.url-source').filter(':input').not($e).val('')
                    .filter(function () { return !!$(this).data('select2'); })
                    .select2('data', null);
            $e.closest('.list-group-item')
                .addClass('active')
                .siblings().removeClass('active')
                .addBack().removeClass('has-error');
        },
        call: function (method, args, kwargs) {
            var self = this;
            var req = method + '_req';
            if (this[req]) { this[req].abort(); }
            return this[req] = openerp.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'website',
                method: method,
                args: args,
                kwargs: kwargs,
            }).always(function () {
                self[req] = null;
            });
        },
        page_exists: function (term) {
            return this.call('page_exists', [null, term], {
                context: website.get_context(),
            });
        },
        fetch_pages: function (term) {
            return this.call('search_pages', [null, term], {
                limit: 9,
                context: website.get_context(),
            });
        },
    });

    website.editor.Media = openerp.Widget.extend({
        init: function (parent, editor, media) {
            this._super();
            this.parent = parent;
            this.editor = editor;
            this.media = media;
        },
        start: function () {
            this.$preview = this.$('.preview-container').detach();
            return this._super();
        },
        search: function (needle) {
        },
        save: function () {
        },
        clear: function () {
        },
        cancel: function () {
        },
        close: function () {
        },
    });
    website.editor.MediaDialog = website.editor.Dialog.extend({
        template: 'website.editor.dialog.media',
        events : _.extend({}, website.editor.Dialog.prototype.events, {
            'input input#icon-search': 'search',
        }),
        init: function (editor, media) {
            this._super(editor);
            this.editor = editor;
            this.page = 0;
            this.media = media;
        },
        start: function () {
            var self = this;

            this.imageDialog = new website.editor.RTEImageDialog(this, this.editor, this.media);
            this.imageDialog.appendTo(this.$("#editor-media-image"));
            this.iconDialog = new website.editor.FontIconsDialog(this, this.editor, this.media);
            this.iconDialog.appendTo(this.$("#editor-media-icon"));
            this.videoDialog = new website.editor.VideoDialog(this, this.editor, this.media);
            this.videoDialog.appendTo(this.$("#editor-media-video"));

            this.active = this.imageDialog;

            $('a[data-toggle="tab"]').on('shown.bs.tab', function (event) {
                if ($(event.target).is('[href="#editor-media-image"]')) {
                    self.active = self.imageDialog;
                    self.$('li.search, li.previous, li.next').removeClass("hidden");
                } else if ($(event.target).is('[href="#editor-media-icon"]')) {
                    self.active = self.iconDialog;
                    self.$('li.search, li.previous, li.next').removeClass("hidden");
                    self.$('.nav-tabs li.previous, .nav-tabs li.next').addClass("hidden");
                } else if ($(event.target).is('[href="#editor-media-video"]')) {
                    self.active = self.videoDialog;
                    self.$('.nav-tabs li.search').addClass("hidden");
                }
            });

            if (this.media) {
                if (this.media.$.nodeName === "IMG") {
                    this.$('[href="#editor-media-image"]').tab('show');
                } else if (this.media.$.className.match(/(^|\s)media_iframe_video($|\s)/)) {
                    this.$('[href="#editor-media-video"]').tab('show');
                } else if (this.media.$.className.match(/(^|\s)fa($|\s)/)) {
                    this.$('[href="#editor-media-icon"]').tab('show');
                }

                if ($(this.media.$).parent().data("oe-field") === "image") {
                    this.$('[href="#editor-media-video"], [href="#editor-media-icon"]').addClass('hidden');
                }
            }
            return this._super();
        },
        save: function () {
            var self = this;
            if (self.media) {
                this.media.$.innerHTML = "";
                if (this.active !== this.imageDialog) {
                    this.imageDialog.clear();
                }
                if (this.active !== this.iconDialog) {
                    this.iconDialog.clear();
                }
                if (this.active !== this.videoDialog) {
                    this.videoDialog.clear();
                }
            } else {
                var rng = range.create();
                if($('.insert-media')){
                    rng = document.createRange();
                    rng.selectNodeContents(document.getElementsByClassName('insert-media')[0])
                }
                this.media = document.createElement("img")
                rng.insertNode(this.media);
                this.active.media = this.media;
            }
            var $el = $(self.active.media.$);
            this.active.save();
            //this.media.$.className = this.media.$.className.replace(/\s+/g, ' ');
            setTimeout(function () {
                $el.trigger("saved", self.active.media.$);
                $(document.body).trigger("media-saved", [$el[0], self.active.media.$]);
            },0);
            this._super();
        },
        searchTimer: null,
        search: function () {
            var self = this;
            var needle = this.$("input#icon-search").val();
            clearTimeout(this.searchTimer);
            this.searchTimer = setTimeout(function () {
                self.active.search(needle || "");
            },250);
        }
    });

    /**
     * ImageDialog widget. Lets users change an image, including uploading a
     * new image in OpenERP or selecting the image style (if supported by
     * the caller).
     *
     * Initialized as usual, but the caller can hook into two events:
     *
     * @event start({url, style}) called during dialog initialization and
     *                            opening, the handler can *set* the ``url``
     *                            and ``style`` properties on its parameter
     *                            to provide these as default values to the
     *                            dialog
     * @event save({url, style}) called during dialog finalization, the handler
     *                           is provided with the image url and style
     *                           selected by the users (or possibly the ones
     *                           originally passed in)
     */
    var IMAGES_PER_ROW = 6;
    var IMAGES_ROWS = 2;
    website.editor.ImageDialog = website.editor.Media.extend({
        template: 'website.editor.dialog.image',
        events: _.extend({}, website.editor.Dialog.prototype.events, {
            'change .url-source': function (e) {
                this.changed($(e.target));
            },
            'click button.filepicker': function () {
                this.$('input[type=file]').click();
            },
            'change input[type=file]': 'file_selection',
            'submit form': 'form_submit',
            'change input.url': "change_input",
            'keyup input.url': "change_input",
            //'change select.image-style': 'preview_image',
            'click .existing-attachments img': 'select_existing',
            'click .existing-attachment-remove': 'try_remove',
        }),
        init: function (parent, editor, media) {
            this.page = 0;
            this._super(parent, editor, media);
        },
        start: function () {
            var self = this;
            var res = this._super();
            var o = { url: null };
            // avoid typos, prevent addition of new properties to the object
            Object.preventExtensions(o);
            this.trigger('start', o);
            this.parent.$(".pager > li").click(function (e) {
                e.preventDefault();
                var $target = $(e.currentTarget);
                if ($target.hasClass('disabled')) {
                    return;
                }
                self.page += $target.hasClass('previous') ? -1 : 1;
                self.display_attachments();
            });
            this.set_image(o.url);
            return res;
        },
        save: function () {
            if (!this.link) {
                this.link = this.$(".existing-attachments img:first").attr('src');
            }
            this.trigger('save', {
                url: this.link
            });
            //this.media.renameNode("img");
            $(this.media).attr('src', this.link);
            return this._super();
        },
        clear: function () {
            this.media.$.className = this.media.$.className.replace(/(^|\s)(img(\s|$)|img-[^\s]*)/g, ' ');
        },
        cancel: function () {
            this.trigger('cancel');
        },
        change_input: function (e) {
            var $input = $(e.target);
            var $button = $input.parent().find("button");
            if ($input.val() === "") {
                $button.addClass("btn-default").removeClass("btn-primary");
            } else {
                $button.removeClass("btn-default").addClass("btn-primary");
            }
        },
        search: function (needle) {
            var self = this;
            this.fetch_existing(needle).then(function () {
                self.selected_existing(self.$('input.url').val());
            });
        },
        set_image: function (url, error) {
            var self = this;
            if (url) this.link = url;
            this.$('input.url').val('');
            this.fetch_existing().then(function () {
                self.selected_existing(url);
            });
        },
        form_submit: function (event) {
            var self = this;
            var $form = this.$('form[action="/website/attach"]');
            if (!$form.find('input[name="upload"]').val().length) {
                var url = $form.find('input[name="url"]').val();
                if (this.selected_existing(url).size()) {
                    event.preventDefault();
                    return false;
                }
            }
            var callback = _.uniqueId('func_');
            this.$('input[name=func]').val(callback);
            window[callback] = function (url, error) {
                delete window[callback];
                self.file_selected(url, error);
            };
        },
        file_selection: function () {
            this.$el.addClass('nosave');
            this.$('form').removeClass('has-error').find('.help-block').empty();
            this.$('button.filepicker').removeClass('btn-danger btn-success');
            this.$('form').submit();
        },
        file_selected: function(url, error) {
            var $button = this.$('button.filepicker');
            if (!error) {
                $button.addClass('btn-success');
            } else {
                url = null;
                this.$('form').addClass('has-error')
                    .find('.help-block').text(error);
                $button.addClass('btn-danger');
            }
            this.set_image(url, error);
            // auto save and close popup
            this.parent.save();
        },
        fetch_existing: function (needle) {
            var domain = [['res_model', '=', 'ir.ui.view'], '|',
                        ['mimetype', '=', false], ['mimetype', '=like', 'image/%']];
            if (needle && needle.length) {
                domain.push('|', ['datas_fname', 'ilike', needle], ['name', 'ilike', needle]);
            }
            return openerp.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'ir.attachment',
                method: 'search_read',
                args: [],
                kwargs: {
                    fields: ['name', 'website_url'],
                    domain: domain,
                    order: 'id desc',
                    context: website.get_context(),
                }
            }).then(this.proxy('fetched_existing'));
        },
        fetched_existing: function (records) {
            this.records = records;
            this.display_attachments();
        },
        display_attachments: function () {
            this.$('.help-block').empty();
            var per_screen = IMAGES_PER_ROW * IMAGES_ROWS;

            var from = this.page * per_screen;
            var records = this.records;

            // Create rows of 3 records
            var rows = _(records).chain()
                .slice(from, from + per_screen)
                .groupBy(function (_, index) { return Math.floor(index / IMAGES_PER_ROW); })
                .values()
                .value();
            this.$('.existing-attachments').replaceWith(
                openerp.qweb.render(
                    'website.editor.dialog.image.existing.content', {rows: rows}));
            this.parent.$('.pager')
                .find('li.previous').toggleClass('disabled', (from === 0)).end()
                .find('li.next').toggleClass('disabled', (from + per_screen >= records.length));
        },
        select_existing: function (e) {
            var link = $(e.currentTarget).attr('src');
            this.link = link;
            this.selected_existing(link);
        },
        selected_existing: function (link) {
            this.$('.existing-attachment-cell.media_selected').removeClass("media_selected");
            var $select = this.$('.existing-attachment-cell img').filter(function () {
                return $(this).attr("src") == link;
            }).first();
            $select.parent().addClass("media_selected");
            return $select;
        },
        try_remove: function (e) {
            var $help_block = this.$('.help-block').empty();
            var self = this;
            var $a = $(e.target);
            var id = parseInt($a.data('id'), 10);
            var attachment = _.findWhere(this.records, {id: id});
            var $both = $a.parent().children();

            $both.css({borderWidth: "5px", borderColor: "#f00"});

            return openerp.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'ir.attachment',
                method: 'try_remove',
                args: [],
                kwargs: {
                    ids: [id],
                    context: website.get_context()
                }
            }).then(function (prevented) {
                if (_.isEmpty(prevented)) {
                    self.records = _.without(self.records, attachment);
                    self.display_attachments();
                    return;
                }
                $both.css({borderWidth: "", borderColor: ""});
                $help_block.replaceWith(openerp.qweb.render(
                    'website.editor.dialog.image.existing.error', {
                        views: prevented[id]
                    }
                ));
            });
        },
    });

    website.editor.RTEImageDialog = website.editor.ImageDialog.extend({
        init: function (parent, editor, media) {
            this._super(parent, editor, media);
            this.on('start', this, this.proxy('started'));
            this.on('save', this, this.proxy('saved'));
        },
        started: function (holder) {
            if (!this.media) { this.media = document.getElementsByClassName('insert-media')[0] }
            var el = this.media;
            if (!el) { return; }
            holder.url = el.getAttribute('src');
        },
        saved: function (data) {
            var element = document.getElementsByClassName('insert-media')[0]
            $('p').removeClass('insert-media');
            if (!(element = this.media)) {
                element = document.createElement('img');
                element.addClass('img');
                element.addClass('img-responsive');
                setTimeout(function () {
                    editor.insertElement(element);
                }, 0);
            }
            var style = data.style;
            element.setAttribute('src', data.url);
            if (style) { element.addClass(style); }
        },
    });

    website.editor.FontIconsDialog = website.editor.Media.extend({
        template: 'website.editor.dialog.font-icons',
        events : _.extend({}, website.editor.Dialog.prototype.events, {
            change: 'update_preview',
            'click .font-icons-icon': function (e) {
                e.preventDefault();
                e.stopPropagation();

                this.$('#fa-icon').val(e.target.getAttribute('data-id'));
                this.update_preview();
            },
            'click #fa-preview span': function (e) {
                e.preventDefault();
                e.stopPropagation();

                this.$('#fa-size').val(e.target.getAttribute('data-size'));
                this.update_preview();
            },
        }),
        // List of FontAwesome icons in 4.0.3, extracted from the cheatsheet.
        // Each icon provides the unicode codepoint as ``text`` and the class
        // name as ``id`` so the whole thing can be fed directly to select2
        // without post-processing and do the right thing (except for the part
        // where we still need to implement ``initSelection``)
        // TODO: add id/name to the text in order to allow FAYT selection of icons?
        icons: [{"text": "\uf000", "id": "fa-glass"}, {"text": "\uf001", "id": "fa-music"}, {"text": "\uf002", "id": "fa-search"}, {"text": "\uf003", "id": "fa-envelope-o"}, {"text": "\uf004", "id": "fa-heart"}, {"text": "\uf005", "id": "fa-star"}, {"text": "\uf006", "id": "fa-star-o"}, {"text": "\uf007", "id": "fa-user"}, {"text": "\uf008", "id": "fa-film"}, {"text": "\uf009", "id": "fa-th-large"}, {"text": "\uf00a", "id": "fa-th"}, {"text": "\uf00b", "id": "fa-th-list"}, {"text": "\uf00c", "id": "fa-check"}, {"text": "\uf00d", "id": "fa-times"}, {"text": "\uf00e", "id": "fa-search-plus"}, {"text": "\uf010", "id": "fa-search-minus"}, {"text": "\uf011", "id": "fa-power-off"}, {"text": "\uf012", "id": "fa-signal"}, {"text": "\uf013", "id": "fa-cog"}, {"text": "\uf014", "id": "fa-trash-o"}, {"text": "\uf015", "id": "fa-home"}, {"text": "\uf016", "id": "fa-file-o"}, {"text": "\uf017", "id": "fa-clock-o"}, {"text": "\uf018", "id": "fa-road"}, {"text": "\uf019", "id": "fa-download"}, {"text": "\uf01a", "id": "fa-arrow-circle-o-down"}, {"text": "\uf01b", "id": "fa-arrow-circle-o-up"}, {"text": "\uf01c", "id": "fa-inbox"}, {"text": "\uf01d", "id": "fa-play-circle-o"}, {"text": "\uf01e", "id": "fa-repeat"}, {"text": "\uf021", "id": "fa-refresh"}, {"text": "\uf022", "id": "fa-list-alt"}, {"text": "\uf023", "id": "fa-lock"}, {"text": "\uf024", "id": "fa-flag"}, {"text": "\uf025", "id": "fa-headphones"}, {"text": "\uf026", "id": "fa-volume-off"}, {"text": "\uf027", "id": "fa-volume-down"}, {"text": "\uf028", "id": "fa-volume-up"}, {"text": "\uf029", "id": "fa-qrcode"}, {"text": "\uf02a", "id": "fa-barcode"}, {"text": "\uf02b", "id": "fa-tag"}, {"text": "\uf02c", "id": "fa-tags"}, {"text": "\uf02d", "id": "fa-book"}, {"text": "\uf02e", "id": "fa-bookmark"}, {"text": "\uf02f", "id": "fa-print"}, {"text": "\uf030", "id": "fa-camera"}, {"text": "\uf031", "id": "fa-font"}, {"text": "\uf032", "id": "fa-bold"}, {"text": "\uf033", "id": "fa-italic"}, {"text": "\uf034", "id": "fa-text-height"}, {"text": "\uf035", "id": "fa-text-width"}, {"text": "\uf036", "id": "fa-align-left"}, {"text": "\uf037", "id": "fa-align-center"}, {"text": "\uf038", "id": "fa-align-right"}, {"text": "\uf039", "id": "fa-align-justify"}, {"text": "\uf03a", "id": "fa-list"}, {"text": "\uf03b", "id": "fa-outdent"}, {"text": "\uf03c", "id": "fa-indent"}, {"text": "\uf03d", "id": "fa-video-camera"}, {"text": "\uf03e", "id": "fa-picture-o"}, {"text": "\uf040", "id": "fa-pencil"}, {"text": "\uf041", "id": "fa-map-marker"}, {"text": "\uf042", "id": "fa-adjust"}, {"text": "\uf043", "id": "fa-tint"}, {"text": "\uf044", "id": "fa-pencil-square-o"}, {"text": "\uf045", "id": "fa-share-square-o"}, {"text": "\uf046", "id": "fa-check-square-o"}, {"text": "\uf047", "id": "fa-arrows"}, {"text": "\uf048", "id": "fa-step-backward"}, {"text": "\uf049", "id": "fa-fast-backward"}, {"text": "\uf04a", "id": "fa-backward"}, {"text": "\uf04b", "id": "fa-play"}, {"text": "\uf04c", "id": "fa-pause"}, {"text": "\uf04d", "id": "fa-stop"}, {"text": "\uf04e", "id": "fa-forward"}, {"text": "\uf050", "id": "fa-fast-forward"}, {"text": "\uf051", "id": "fa-step-forward"}, {"text": "\uf052", "id": "fa-eject"}, {"text": "\uf053", "id": "fa-chevron-left"}, {"text": "\uf054", "id": "fa-chevron-right"}, {"text": "\uf055", "id": "fa-plus-circle"}, {"text": "\uf056", "id": "fa-minus-circle"}, {"text": "\uf057", "id": "fa-times-circle"}, {"text": "\uf058", "id": "fa-check-circle"}, {"text": "\uf059", "id": "fa-question-circle"}, {"text": "\uf05a", "id": "fa-info-circle"}, {"text": "\uf05b", "id": "fa-crosshairs"}, {"text": "\uf05c", "id": "fa-times-circle-o"}, {"text": "\uf05d", "id": "fa-check-circle-o"}, {"text": "\uf05e", "id": "fa-ban"}, {"text": "\uf060", "id": "fa-arrow-left"}, {"text": "\uf061", "id": "fa-arrow-right"}, {"text": "\uf062", "id": "fa-arrow-up"}, {"text": "\uf063", "id": "fa-arrow-down"}, {"text": "\uf064", "id": "fa-share"}, {"text": "\uf065", "id": "fa-expand"}, {"text": "\uf066", "id": "fa-compress"}, {"text": "\uf067", "id": "fa-plus"}, {"text": "\uf068", "id": "fa-minus"}, {"text": "\uf069", "id": "fa-asterisk"}, {"text": "\uf06a", "id": "fa-exclamation-circle"}, {"text": "\uf06b", "id": "fa-gift"}, {"text": "\uf06c", "id": "fa-leaf"}, {"text": "\uf06d", "id": "fa-fire"}, {"text": "\uf06e", "id": "fa-eye"}, {"text": "\uf070", "id": "fa-eye-slash"}, {"text": "\uf071", "id": "fa-exclamation-triangle"}, {"text": "\uf072", "id": "fa-plane"}, {"text": "\uf073", "id": "fa-calendar"}, {"text": "\uf074", "id": "fa-random"}, {"text": "\uf075", "id": "fa-comment"}, {"text": "\uf076", "id": "fa-magnet"}, {"text": "\uf077", "id": "fa-chevron-up"}, {"text": "\uf078", "id": "fa-chevron-down"}, {"text": "\uf079", "id": "fa-retweet"}, {"text": "\uf07a", "id": "fa-shopping-cart"}, {"text": "\uf07b", "id": "fa-folder"}, {"text": "\uf07c", "id": "fa-folder-open"}, {"text": "\uf07d", "id": "fa-arrows-v"}, {"text": "\uf07e", "id": "fa-arrows-h"}, {"text": "\uf080", "id": "fa-bar-chart-o"}, {"text": "\uf081", "id": "fa-twitter-square"}, {"text": "\uf082", "id": "fa-facebook-square"}, {"text": "\uf083", "id": "fa-camera-retro"}, {"text": "\uf084", "id": "fa-key"}, {"text": "\uf085", "id": "fa-cogs"}, {"text": "\uf086", "id": "fa-comments"}, {"text": "\uf087", "id": "fa-thumbs-o-up"}, {"text": "\uf088", "id": "fa-thumbs-o-down"}, {"text": "\uf089", "id": "fa-star-half"}, {"text": "\uf08a", "id": "fa-heart-o"}, {"text": "\uf08b", "id": "fa-sign-out"}, {"text": "\uf08c", "id": "fa-linkedin-square"}, {"text": "\uf08d", "id": "fa-thumb-tack"}, {"text": "\uf08e", "id": "fa-external-link"}, {"text": "\uf090", "id": "fa-sign-in"}, {"text": "\uf091", "id": "fa-trophy"}, {"text": "\uf092", "id": "fa-github-square"}, {"text": "\uf093", "id": "fa-upload"}, {"text": "\uf094", "id": "fa-lemon-o"}, {"text": "\uf095", "id": "fa-phone"}, {"text": "\uf096", "id": "fa-square-o"}, {"text": "\uf097", "id": "fa-bookmark-o"}, {"text": "\uf098", "id": "fa-phone-square"}, {"text": "\uf099", "id": "fa-twitter"}, {"text": "\uf09a", "id": "fa-facebook"}, {"text": "\uf09b", "id": "fa-github"}, {"text": "\uf09c", "id": "fa-unlock"}, {"text": "\uf09d", "id": "fa-credit-card"}, {"text": "\uf09e", "id": "fa-rss"}, {"text": "\uf0a0", "id": "fa-hdd-o"}, {"text": "\uf0a1", "id": "fa-bullhorn"}, {"text": "\uf0f3", "id": "fa-bell"}, {"text": "\uf0a3", "id": "fa-certificate"}, {"text": "\uf0a4", "id": "fa-hand-o-right"}, {"text": "\uf0a5", "id": "fa-hand-o-left"}, {"text": "\uf0a6", "id": "fa-hand-o-up"}, {"text": "\uf0a7", "id": "fa-hand-o-down"}, {"text": "\uf0a8", "id": "fa-arrow-circle-left"}, {"text": "\uf0a9", "id": "fa-arrow-circle-right"}, {"text": "\uf0aa", "id": "fa-arrow-circle-up"}, {"text": "\uf0ab", "id": "fa-arrow-circle-down"}, {"text": "\uf0ac", "id": "fa-globe"}, {"text": "\uf0ad", "id": "fa-wrench"}, {"text": "\uf0ae", "id": "fa-tasks"}, {"text": "\uf0b0", "id": "fa-filter"}, {"text": "\uf0b1", "id": "fa-briefcase"}, {"text": "\uf0b2", "id": "fa-arrows-alt"}, {"text": "\uf0c0", "id": "fa-users"}, {"text": "\uf0c1", "id": "fa-link"}, {"text": "\uf0c2", "id": "fa-cloud"}, {"text": "\uf0c3", "id": "fa-flask"}, {"text": "\uf0c4", "id": "fa-scissors"}, {"text": "\uf0c5", "id": "fa-files-o"}, {"text": "\uf0c6", "id": "fa-paperclip"}, {"text": "\uf0c7", "id": "fa-floppy-o"}, {"text": "\uf0c8", "id": "fa-square"}, {"text": "\uf0c9", "id": "fa-bars"}, {"text": "\uf0ca", "id": "fa-list-ul"}, {"text": "\uf0cb", "id": "fa-list-ol"}, {"text": "\uf0cc", "id": "fa-strikethrough"}, {"text": "\uf0cd", "id": "fa-underline"}, {"text": "\uf0ce", "id": "fa-table"}, {"text": "\uf0d0", "id": "fa-magic"}, {"text": "\uf0d1", "id": "fa-truck"}, {"text": "\uf0d2", "id": "fa-pinterest"}, {"text": "\uf0d3", "id": "fa-pinterest-square"}, {"text": "\uf0d4", "id": "fa-google-plus-square"}, {"text": "\uf0d5", "id": "fa-google-plus"}, {"text": "\uf0d6", "id": "fa-money"}, {"text": "\uf0d7", "id": "fa-caret-down"}, {"text": "\uf0d8", "id": "fa-caret-up"}, {"text": "\uf0d9", "id": "fa-caret-left"}, {"text": "\uf0da", "id": "fa-caret-right"}, {"text": "\uf0db", "id": "fa-columns"}, {"text": "\uf0dc", "id": "fa-sort"}, {"text": "\uf0dd", "id": "fa-sort-asc"}, {"text": "\uf0de", "id": "fa-sort-desc"}, {"text": "\uf0e0", "id": "fa-envelope"}, {"text": "\uf0e1", "id": "fa-linkedin"}, {"text": "\uf0e2", "id": "fa-undo"}, {"text": "\uf0e3", "id": "fa-gavel"}, {"text": "\uf0e4", "id": "fa-tachometer"}, {"text": "\uf0e5", "id": "fa-comment-o"}, {"text": "\uf0e6", "id": "fa-comments-o"}, {"text": "\uf0e7", "id": "fa-bolt"}, {"text": "\uf0e8", "id": "fa-sitemap"}, {"text": "\uf0e9", "id": "fa-umbrella"}, {"text": "\uf0ea", "id": "fa-clipboard"}, {"text": "\uf0eb", "id": "fa-lightbulb-o"}, {"text": "\uf0ec", "id": "fa-exchange"}, {"text": "\uf0ed", "id": "fa-cloud-download"}, {"text": "\uf0ee", "id": "fa-cloud-upload"}, {"text": "\uf0f0", "id": "fa-user-md"}, {"text": "\uf0f1", "id": "fa-stethoscope"}, {"text": "\uf0f2", "id": "fa-suitcase"}, {"text": "\uf0a2", "id": "fa-bell-o"}, {"text": "\uf0f4", "id": "fa-coffee"}, {"text": "\uf0f5", "id": "fa-cutlery"}, {"text": "\uf0f6", "id": "fa-file-text-o"}, {"text": "\uf0f7", "id": "fa-building-o"}, {"text": "\uf0f8", "id": "fa-hospital-o"}, {"text": "\uf0f9", "id": "fa-ambulance"}, {"text": "\uf0fa", "id": "fa-medkit"}, {"text": "\uf0fb", "id": "fa-fighter-jet"}, {"text": "\uf0fc", "id": "fa-beer"}, {"text": "\uf0fd", "id": "fa-h-square"}, {"text": "\uf0fe", "id": "fa-plus-square"}, {"text": "\uf100", "id": "fa-angle-double-left"}, {"text": "\uf101", "id": "fa-angle-double-right"}, {"text": "\uf102", "id": "fa-angle-double-up"}, {"text": "\uf103", "id": "fa-angle-double-down"}, {"text": "\uf104", "id": "fa-angle-left"}, {"text": "\uf105", "id": "fa-angle-right"}, {"text": "\uf106", "id": "fa-angle-up"}, {"text": "\uf107", "id": "fa-angle-down"}, {"text": "\uf108", "id": "fa-desktop"}, {"text": "\uf109", "id": "fa-laptop"}, {"text": "\uf10a", "id": "fa-tablet"}, {"text": "\uf10b", "id": "fa-mobile"}, {"text": "\uf10c", "id": "fa-circle-o"}, {"text": "\uf10d", "id": "fa-quote-left"}, {"text": "\uf10e", "id": "fa-quote-right"}, {"text": "\uf110", "id": "fa-spinner"}, {"text": "\uf111", "id": "fa-circle"}, {"text": "\uf112", "id": "fa-reply"}, {"text": "\uf113", "id": "fa-github-alt"}, {"text": "\uf114", "id": "fa-folder-o"}, {"text": "\uf115", "id": "fa-folder-open-o"}, {"text": "\uf118", "id": "fa-smile-o"}, {"text": "\uf119", "id": "fa-frown-o"}, {"text": "\uf11a", "id": "fa-meh-o"}, {"text": "\uf11b", "id": "fa-gamepad"}, {"text": "\uf11c", "id": "fa-keyboard-o"}, {"text": "\uf11d", "id": "fa-flag-o"}, {"text": "\uf11e", "id": "fa-flag-checkered"}, {"text": "\uf120", "id": "fa-terminal"}, {"text": "\uf121", "id": "fa-code"}, {"text": "\uf122", "id": "fa-reply-all"}, {"text": "\uf122", "id": "fa-mail-reply-all"}, {"text": "\uf123", "id": "fa-star-half-o"}, {"text": "\uf124", "id": "fa-location-arrow"}, {"text": "\uf125", "id": "fa-crop"}, {"text": "\uf126", "id": "fa-code-fork"}, {"text": "\uf127", "id": "fa-chain-broken"}, {"text": "\uf128", "id": "fa-question"}, {"text": "\uf129", "id": "fa-info"}, {"text": "\uf12a", "id": "fa-exclamation"}, {"text": "\uf12b", "id": "fa-superscript"}, {"text": "\uf12c", "id": "fa-subscript"}, {"text": "\uf12d", "id": "fa-eraser"}, {"text": "\uf12e", "id": "fa-puzzle-piece"}, {"text": "\uf130", "id": "fa-microphone"}, {"text": "\uf131", "id": "fa-microphone-slash"}, {"text": "\uf132", "id": "fa-shield"}, {"text": "\uf133", "id": "fa-calendar-o"}, {"text": "\uf134", "id": "fa-fire-extinguisher"}, {"text": "\uf135", "id": "fa-rocket"}, {"text": "\uf136", "id": "fa-maxcdn"}, {"text": "\uf137", "id": "fa-chevron-circle-left"}, {"text": "\uf138", "id": "fa-chevron-circle-right"}, {"text": "\uf139", "id": "fa-chevron-circle-up"}, {"text": "\uf13a", "id": "fa-chevron-circle-down"}, {"text": "\uf13b", "id": "fa-html5"}, {"text": "\uf13c", "id": "fa-css3"}, {"text": "\uf13d", "id": "fa-anchor"}, {"text": "\uf13e", "id": "fa-unlock-alt"}, {"text": "\uf140", "id": "fa-bullseye"}, {"text": "\uf141", "id": "fa-ellipsis-h"}, {"text": "\uf142", "id": "fa-ellipsis-v"}, {"text": "\uf143", "id": "fa-rss-square"}, {"text": "\uf144", "id": "fa-play-circle"}, {"text": "\uf145", "id": "fa-ticket"}, {"text": "\uf146", "id": "fa-minus-square"}, {"text": "\uf147", "id": "fa-minus-square-o"}, {"text": "\uf148", "id": "fa-level-up"}, {"text": "\uf149", "id": "fa-level-down"}, {"text": "\uf14a", "id": "fa-check-square"}, {"text": "\uf14b", "id": "fa-pencil-square"}, {"text": "\uf14c", "id": "fa-external-link-square"}, {"text": "\uf14d", "id": "fa-share-square"}, {"text": "\uf14e", "id": "fa-compass"}, {"text": "\uf150", "id": "fa-caret-square-o-down"}, {"text": "\uf151", "id": "fa-caret-square-o-up"}, {"text": "\uf152", "id": "fa-caret-square-o-right"}, {"text": "\uf153", "id": "fa-eur"}, {"text": "\uf154", "id": "fa-gbp"}, {"text": "\uf155", "id": "fa-usd"}, {"text": "\uf156", "id": "fa-inr"}, {"text": "\uf157", "id": "fa-jpy"}, {"text": "\uf158", "id": "fa-rub"}, {"text": "\uf159", "id": "fa-krw"}, {"text": "\uf15a", "id": "fa-btc"}, {"text": "\uf15b", "id": "fa-file"}, {"text": "\uf15c", "id": "fa-file-text"}, {"text": "\uf15d", "id": "fa-sort-alpha-asc"}, {"text": "\uf15e", "id": "fa-sort-alpha-desc"}, {"text": "\uf160", "id": "fa-sort-amount-asc"}, {"text": "\uf161", "id": "fa-sort-amount-desc"}, {"text": "\uf162", "id": "fa-sort-numeric-asc"}, {"text": "\uf163", "id": "fa-sort-numeric-desc"}, {"text": "\uf164", "id": "fa-thumbs-up"}, {"text": "\uf165", "id": "fa-thumbs-down"}, {"text": "\uf166", "id": "fa-youtube-square"}, {"text": "\uf167", "id": "fa-youtube"}, {"text": "\uf168", "id": "fa-xing"}, {"text": "\uf169", "id": "fa-xing-square"}, {"text": "\uf16a", "id": "fa-youtube-play"}, {"text": "\uf16b", "id": "fa-dropbox"}, {"text": "\uf16c", "id": "fa-stack-overflow"}, {"text": "\uf16d", "id": "fa-instagram"}, {"text": "\uf16e", "id": "fa-flickr"}, {"text": "\uf170", "id": "fa-adn"}, {"text": "\uf171", "id": "fa-bitbucket"}, {"text": "\uf172", "id": "fa-bitbucket-square"}, {"text": "\uf173", "id": "fa-tumblr"}, {"text": "\uf174", "id": "fa-tumblr-square"}, {"text": "\uf175", "id": "fa-long-arrow-down"}, {"text": "\uf176", "id": "fa-long-arrow-up"}, {"text": "\uf177", "id": "fa-long-arrow-left"}, {"text": "\uf178", "id": "fa-long-arrow-right"}, {"text": "\uf179", "id": "fa-apple"}, {"text": "\uf17a", "id": "fa-windows"}, {"text": "\uf17b", "id": "fa-android"}, {"text": "\uf17c", "id": "fa-linux"}, {"text": "\uf17d", "id": "fa-dribbble"}, {"text": "\uf17e", "id": "fa-skype"}, {"text": "\uf180", "id": "fa-foursquare"}, {"text": "\uf181", "id": "fa-trello"}, {"text": "\uf182", "id": "fa-female"}, {"text": "\uf183", "id": "fa-male"}, {"text": "\uf184", "id": "fa-gittip"}, {"text": "\uf185", "id": "fa-sun-o"}, {"text": "\uf186", "id": "fa-moon-o"}, {"text": "\uf187", "id": "fa-archive"}, {"text": "\uf188", "id": "fa-bug"}, {"text": "\uf189", "id": "fa-vk"}, {"text": "\uf18a", "id": "fa-weibo"}, {"text": "\uf18b", "id": "fa-renren"}, {"text": "\uf18c", "id": "fa-pagelines"}, {"text": "\uf18d", "id": "fa-stack-exchange"}, {"text": "\uf18e", "id": "fa-arrow-circle-o-right"}, {"text": "\uf190", "id": "fa-arrow-circle-o-left"}, {"text": "\uf191", "id": "fa-caret-square-o-left"}, {"text": "\uf192", "id": "fa-dot-circle-o"}, {"text": "\uf193", "id": "fa-wheelchair"}, {"text": "\uf194", "id": "fa-vimeo-square"}, {"text": "\uf195", "id": "fa-try"}, {"text": "\uf196", "id": "fa-plus-square-o"}],
        /*
         * Initializes select2: in Chrome and Safari, <select> font apparently
         * isn't customizable (?) and the fontawesome glyphs fail to appear.
         */
        start: function () {
            return this._super().then(this.proxy('load_data'));
        },
        search: function (needle) {
            var icons = this.icons;
            if (needle) {
                icons = _(icons).filter(function (icon) {
                    return icon.id.substring(3).indexOf(needle) !== -1;
                });
            }
            this.$('div.font-icons-icons').html(
                openerp.qweb.render(
                    'website.editor.dialog.font-icons.icons',
                    {icons: icons}));
        },
        /**
         * Removes existing FontAwesome classes on the bound element, and sets
         * all the new ones if necessary.
         */
        save: function () {
            if (! this.media.$){
                var $image = this.$el.find('.font-icons-selected')
                var rng = range.create()
                if($('.insert-media')){
                    rng = document.createRange();
                    rng.selectNodeContents(document.getElementsByClassName('insert-media')[0])
                    $('p').removeClass('insert-media');
                }
                rng.insertNode($image[0]);
                $('.popover').hide();
            } else {
                var style = this.media.$.attributes.style ? this.media.$.attributes.style.textContent : '';
                var classes = (this.media.$.className||"").split(/\s+/);
                var non_fa_classes = _.reject(classes, function (cls) {
                    return cls === 'fa' || /^fa-/.test(cls);
                });
                var final_classes = non_fa_classes.concat(this.get_fa_classes());
                this.media.$.className = final_classes.join(' ');
                this.media.renameNode("span");
                this.media.$.attributes.style.textContent = style;
            }
            this._super();
        },
        /**
         * Looks up the various FontAwesome classes on the bound element and
         * sets the corresponding template/form elements to the right state.
         * If multiple classes of the same category are present on an element
         * (e.g. fa-lg and fa-3x) the last one occurring will be selected,
         * which may not match the visual look of the element.
         */
        load_data: function () {
            var classes = (this.media&&this.media.$.className||"").split(/\s+/);
            for (var i = 0; i < classes.length; i++) {
                var cls = classes[i];
                switch(cls) {
                case 'fa-2x':case 'fa-3x':case 'fa-4x':case 'fa-5x':
                    // size classes
                    this.$('#fa-size').val(cls);
                    continue;
                case 'fa-spin':
                case 'fa-rotate-90':case 'fa-rotate-180':case 'fa-rotate-270':
                case 'fa-flip-horizontal':case 'fa-rotate-vertical':
                    this.$('#fa-rotation').val(cls);
                    continue;
                case 'fa-fw':
                    continue;
                case 'fa-border':
                    this.$('#fa-border').prop('checked', true);
                    continue;
                default:
                    if (!/^fa-/.test(cls)) { continue; }
                    this.$('#fa-icon').val(cls);
                }
            }
            this.update_preview();
        },
        /**
         * Serializes the dialog to an array of FontAwesome classes. Includes
         * the base ``fa``.
         */
        get_fa_classes: function () {
            return [
                'fa',
                this.$('#fa-icon').val(),
                this.$('#fa-size').val(),
                this.$('#fa-rotation').val(),
                this.$('#fa-border').prop('checked') ? 'fa-border' : ''
            ];
        },
        update_preview: function () {
            this.$preview.empty();
            var $preview = this.$('#fa-preview').empty();

            var sizes = ['', 'fa-2x', 'fa-3x', 'fa-4x', 'fa-5x'];
            var classes = this.get_fa_classes();
            var no_sizes = _.difference(classes, sizes).join(' ');
            var selected = false;
            for (var i = sizes.length - 1; i >= 0; i--) {
                var size = sizes[i];

                var $p = $('<span>')
                        .attr('data-size', size)
                        .addClass(size)
                        .addClass(no_sizes);
                if ((size && _.contains(classes, size)) || (classes[2] === "" && !selected)) {
                    this.$preview.append($p.clone());
                    this.$('#fa-size').val(size);
                    $p.addClass('font-icons-selected');
                    selected = true;
                }
                $preview.prepend($p);
            }
        },
        clear: function () {
            this.media.$.className = this.media.$.className.replace(/(^|\s)(fa(\s|$)|fa-[^\s]*)/g, ' ');
        },
    });

    website.editor.VideoDialog = website.editor.Media.extend({
        template: 'website.editor.dialog.video',
        events : _.extend({}, website.editor.Dialog.prototype.events, {
            'click input#urlvideo ~ button': 'get_video',
            'click input#embedvideo ~ button': 'get_embed_video',
            'change input#urlvideo': 'change_input',
            'keyup input#urlvideo': 'change_input',
            'change input#embedvideo': 'change_input',
            'keyup input#embedvideo': 'change_input'
        }),
        start: function () {
            this.$iframe = this.$("iframe");
            var $media = $(this.media && this.media.$);
            if ($media.hasClass("media_iframe_video")) {
                var src = $media.data('src');
                this.$("input#urlvideo").val(src);
                this.$("#autoplay").attr("checked", src.indexOf('autoplay=1') != -1);
                this.get_video();
            }
            return this._super();
        },
        change_input: function (e) {
            var $input = $(e.target);
            var $button = $input.parent().find("button");
            if ($input.val() === "") {
                $button.addClass("btn-default").removeClass("btn-primary");
            } else {
                $button.removeClass("btn-default").addClass("btn-primary");
            }
        },
        get_url: function () {
            var video_id = this.$("#video_id").val();
            var video_type = this.$("#video_type").val();
            switch (video_type) {
                case "youtube":
                    return "//www.youtube.com/embed/" + video_id + "?autoplay=" + (this.$("#autoplay").is(":checked") ? 1 : 0);
                case "vimeo":
                    return "//player.vimeo.com/video/" + video_id + "?autoplay=" + (this.$("#autoplay").is(":checked") ? 1 : 0);
                case "dailymotion":
                    return "//www.dailymotion.com/embed/video/" + video_id + "?autoplay=" + (this.$("#autoplay").is(":checked") ? 1 : 0);
                default:
                    return video_id;
            }
        },
        get_embed_video: function (event) {
            event.preventDefault();
            var embedvideo = this.$("input#embedvideo").val().match(/src=["']?([^"']+)["' ]?/);
            if (embedvideo) {
                this.$("input#urlvideo").val(embedvideo[1]);
                this.get_video(event);
            }
            return false;
        },
        get_video: function (event) {
            if (event) event.preventDefault();
            var needle = this.$("input#urlvideo").val();
            var video_id;
            var video_type;

            if (needle.indexOf(".youtube.") != -1) {
                video_type = "youtube";
                video_id = needle.match(/\.youtube\.[a-z]+\/(embed\/|watch\?v=)?([^\/?&]+)/i)[2];
            } else if (needle.indexOf("//youtu.") != -1) {
                video_type = "youtube";
                video_id = needle.match(/youtube\.[a-z]+\/([^\/?&]+)/i)[1];
            } else if (needle.indexOf("player.vimeo.") != -1 || needle.indexOf("//vimeo.") != -1) {
                video_type = "vimeo";
                video_id = needle.match(/vimeo\.[a-z]+\/(video\/)?([^?&]+)/i)[2];
            } else if (needle.indexOf(".dailymotion.") != -1) {
                video_type = "dailymotion";
                video_id = needle.match(/dailymotion\.[a-z]+\/(embed\/)?(video\/)?([^\/?&]+)/i)[3];
            } else {
                video_type = "";
                video_id = needle;
            }

            this.$("#video_id").val(video_id);
            this.$("#video_type").val(video_type);

            this.$iframe.attr("src", this.get_url());
            return false;
        },
        save: function () {
            var video_id = this.$("#video_id").val();
            if (!video_id) {
                this.$("button.btn-primary").click();
                video_id = this.$("#video_id").val();
            }
            var video_type = this.$("#video_type").val();
            var $iframe = $(
                '<div class="media_iframe_video" data-src="'+this.get_url()+'">'+
                    '<div class="css_editable_mode_display">&nbsp;</div>'+
                    '<iframe src="'+this.get_url()+'" frameborder="0" allowfullscreen="allowfullscreen"></iframe>'+
                '</div>');
            $('.insert-media').replaceWith($iframe);
            this.media.$ = $iframe[0];
            this._super();
        },
        clear: function () {
            delete this.media.$.dataset.src;
            this.media.$.className = this.media.$.className.replace(/(^|\s)media_iframe_video(\s|$)/g, ' ');
        },
    });

    website.Observer = window.MutationObserver || window.WebkitMutationObserver || window.JsMutationObserver;
    var OBSERVER_CONFIG = {
        childList: true,
        attributes: true,
        characterData: true,
        subtree: true,
        attributeOldValue: true,
    };
    var observer = new website.Observer(function (mutations) {
        // NOTE: Webkit does not fire DOMAttrModified => webkit browsers
        //       relying on JsMutationObserver shim (Chrome < 18, Safari < 6)
        //       will not mark dirty on attribute changes (@class, img/@src,
        //       a/@href, ...)
        _(mutations).chain()
            .filter(function (m) {
                // ignore any SVG target, these blokes are like weird mon
                if (m.target && m.target instanceof SVGElement) {
                    return false;
                }

                // ignore any change related to mundane image-edit-button
                if (m.target && m.target.className
                        && m.target.className.indexOf('image-edit-button') !== -1) {
                    return false;
                }
                switch(m.type) {
                case 'attributes': // ignore .cke_focus being added or removed
                    // ignore id modification
                    if (m.attributeName === 'id') { return false; }
                    // if attribute is not a class, can't be .cke_focus change
                    if (m.attributeName !== 'class') { return true; }

                    // find out what classes were added or removed
                    var oldClasses = (m.oldValue || '').split(/\s+/);
                    var newClasses = m.target.className.split(/\s+/);
                    var change = _.union(_.difference(oldClasses, newClasses),
                                         _.difference(newClasses, oldClasses));
                    // ignore mutation if the *only* change is .cke_focus
                    return change.length !== 1 || change[0] === 'cke_focus';
                case 'childList':
                    setTimeout(function () {
                        fixup_browser_crap(m.addedNodes);
                    }, 0);
                    // Remove ignorable nodes from addedNodes or removedNodes,
                    // if either set remains non-empty it's considered to be an
                    // impactful change. Otherwise it's ignored.
                    return !!remove_mundane_nodes(m.addedNodes).length ||
                           !!remove_mundane_nodes(m.removedNodes).length;
                default:
                    return true;
                }
            })
            .map(function (m) {
                var node = m.target;
                while (node && !$(node).hasClass('oe_editable')) {
                    node = node.parentNode;
                }
                return node;
            })
            .compact()
            .uniq()
            .each(function (node) { $(node).trigger('content_changed'); })
    });
    function remove_mundane_nodes(nodes) {
        if (!nodes || !nodes.length) { return []; }

        var output = [];
        for(var i=0; i<nodes.length; ++i) {
            var node = nodes[i];
            if (node.nodeType === document.ELEMENT_NODE) {
                if (node.nodeName === 'BR' && node.getAttribute('type') === '_moz') {
                    // <br type="_moz"> appears when focusing RTE in FF, ignore
                    continue;
                } else if (node.nodeName === 'DIV' && $(node).hasClass('oe_drop_zone')) {
                    // ignore dropzone inserted by snippets
                    continue
                }
            }

            output.push(node);
        }
        return output;
    }

    var programmatic_styles = {
        float: 1,
        display: 1,
        position: 1,
        top: 1,
        left: 1,
        right: 1,
        bottom: 1,
    };
    function fixup_browser_crap(nodes) {
        if (!nodes || !nodes.length) { return; }
        /**
         * Checks that the node only has a @style, not e.g. @class or whatever
         */
        function has_only_style(node) {
            for (var i = 0; i < node.attributes.length; i++) {
                var attr = node.attributes[i];
                if (attr.attributeName !== 'style') {
                    return false;
                }
            }
            return true;
        }
        function has_programmatic_style(node) {
            for (var i = 0; i < node.style.length; i++) {
              var style = node.style[i];
              if (programmatic_styles[style]) {
                  return true;
              }
            }
            return false;
        }

        for (var i=0; i<nodes.length; ++i) {
            var node = nodes[i];
            if (node.nodeType !== document.ELEMENT_NODE) { continue; }

            if (node.nodeName === 'SPAN'
                    && has_only_style(node)
                    && !has_programmatic_style(node)) {
                // On backspace, webkit browsers create a <span> with a bunch of
                // inline styles "remembering" where they come from. Refs:
                //    http://www.neotericdesign.com/blog/2013/3/working-around-chrome-s-contenteditable-span-bug
                //    https://code.google.com/p/chromium/issues/detail?id=226941
                //    https://bugs.webkit.org/show_bug.cgi?id=114791
                //    http://dev.ckeditor.com/ticket/9998
                var child, parent = node.parentNode;
                while (child = node.firstChild) {
                    parent.insertBefore(child, node);
                }
            }
        }
    }
})();
