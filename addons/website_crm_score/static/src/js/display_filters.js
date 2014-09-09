openerp.website_crm_score = function(instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.website_crm_score = {};

    instance.website_crm_score.filters = instance.web_kanban.AbstractField.extend({
        /**
            bnf grammar of a filter:  // is it correct ?
                <filter>    ::= <expr>
                <expr>      ::= <tuple> | '!' <expr> | <bin_op> <expr> <expr>
                <bin_op>    ::= '&' | '|'
                <tuple>     ::= '(' <field_name> ',' <operator> ',' <field_value> ')'
                <operator>  ::= '=' | '!=' | '<=' | '<' | '>' | '>=' | '=?' | 
                                '=like' | '=ilike' | 'like' | 'not like' | 
                                'ilike' | 'not ilike' | 'in' | 'not in' | 'child_of'
            some operators are negative
        */
        NEG_OP: ['!=', 'not like', 'not ilike', 'not in'],
        MAX_LEN: 10,
        start: function() {
            var val = this.field.raw_value;
            var self = this;
            if (val) {
                val = eval(val);
                // console.log('len');
                // console.log(val.length);
                // console.log(this.MAX_LEN);
                if (val.length <= this.MAX_LEN) {
                    var i = 0;
                    while (i < val.length) {
                        var res = this.interpret(val, i);
                        i = res[0];
                        var $span = res[1];
                        // var $span = '<h2>' + res[1] + '</h2>';
                        self.$el.append($span);
                    }
                }                
            }
        },

        interpret: function(val, i) {
            var a = val[i];
            if(typeof a !== 'string'){
                // a is a tuple (field, op, value)
                // console.log(a);
                var tag = a[0]; // field name
                var tip = a[2]; // field value
                if (this.NEG_OP.indexOf(a[1]) !== -1){
                    // op in NEG_OP
                    tip = 'not ' + tip;
                } 
                var span = '<span class="oe_tag" title="' + tip + '">'+ tag +'</span>';
                return [i+1, span];
            }
            else if (a === '!'){
                var res = this.interpret(val, i+1);
                var span = '<span class="label label-danger">' + res[1] + '</span>';
                return [res[0], span];
            }
            else {
                // binary operator
                var res = this.binary_operator(val, i);
                return res;
            }
            return [i+1, ''];
        },

        binary_operator: function(val, i) {
            // console.log('bin');
            // console.log(val[i]);
            var resA = this.interpret(val, i+1);
            var resB = this.interpret(val, resA[0]);
            // console.log(resA);
            // console.log(resB);
            var label = '';
            var op = '';
            if (val[i] === '|') {
                label = 'label-success';
                op = ' or '
            }
            else if (val[i] === '&') {
                label = 'label-primary';
                op = ' and ';
            }
            // newline is needed...
            var span = '<span class="label ' + label + '">' + resA[1] + ' ' + resB[1] + '</span>';
            // var span = '<span>[ ' + resA[1] + op + resB[1] + ' ]</span>';
            // var span = '<span class="well well-sm">' + resA[1] + ' ' + resB[1] + '</span>';
            return [resB[0], span];
        }
    });

    instance.web_kanban.fields_registry.add('filters', 'instance.website_crm_score.filters');
}
