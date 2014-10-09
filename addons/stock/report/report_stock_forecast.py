from openerp import fields, models
from openerp import tools

class report_stock_forecast(models.Model):
    _name = 'report.stock.forecast'
    _auto = False

    date = fields.Date(string='Date')
    location_id = fields.Many2one('stock.location', string='Location', required=True)
    company_id = fields.Many2one('res.company', 'Company')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_categ_id = fields.Many2one('product.category', string='Product Category', required=True)
    cumulative_quantity = fields.Float(string='Cumulative Quantity')
    quantity = fields.Integer(string='Quantity')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_stock_forecast')
        cr.execute("""CREATE or REPLACE VIEW report_stock_forecast AS (SELECT
                        max(id) AS id,
                        location_id,
                        product_id,
                        product_categ_id, company_id,
                        date,
                        sum(qty) as quantity,
                        sum(sum(qty)) OVER(PARTITION BY product_id ORDER BY date) AS cumulative_quantity
                        FROM (
                            SELECT
                                max(sm.id) AS id,
                                dest_location.id AS location_id,
                                dest_location.company_id AS company_id,
                                sm.product_id,
                                product_template.categ_id AS product_categ_id,
                                to_date(to_char(date, 'YYYY/MM/DD'), 'YYYY/MM/DD') AS date,
                                sum(sm.product_uom_qty / u.factor * u2.factor) AS qty
                            FROM
                               stock_move as sm
                                LEFT JOIN
                                   stock_location dest_location ON sm.location_dest_id = dest_location.id
                                LEFT JOIN
                                   stock_location source_location ON sm.location_id = source_location.id
                                LEFT JOIN
                                   product_product ON product_product.id = sm.product_id
                                LEFT JOIN
                                   product_template ON product_template.id = product_product.product_tmpl_id
                                LEFT JOIN
                                   product_uom u on (sm.product_uom=u.id)
                                LEFT JOIN
                               product_uom u2 on (u2.id=product_template.uom_id)
                            WHERE
                                sm.state NOT IN ('draft','cancel') and
                                   dest_location.usage in ('internal', 'transit') and
                                ((source_location.company_id is null and dest_location.company_id is not null) or
                                    (source_location.company_id is not null and dest_location.company_id is null) or source_location.company_id != dest_location.company_id)
                            GROUP BY
                                to_date(to_char(sm.date, 'YYYY/MM/DD'), 'YYYY/MM/DD'),
                                sm.product_id,dest_location.id,product_template.categ_id,
                                dest_location.company_id
                            UNION ALL
                            SELECT
                                max(sm.id) AS id,
                                source_location.id AS location_id,
                                source_location.company_id AS company_id,
                                sm.product_id,
                                product_template.categ_id AS product_categ_id,
                                to_date(to_char(date, 'YYYY/MM/DD'), 'YYYY/MM/DD') AS date,
                                -sum(sm.product_uom_qty / u.factor * u2.factor) AS qty
                            FROM
                               stock_move as sm
                                LEFT JOIN
                                   stock_location source_location ON sm.location_id = source_location.id
                                LEFT JOIN
                                   stock_location dest_location ON sm.location_dest_id = dest_location.id
                                LEFT JOIN
                                   product_product ON product_product.id = sm.product_id
                                LEFT JOIN
                                   product_template ON product_template.id = product_product.product_tmpl_id
                                LEFT JOIN
                                   product_uom u on (sm.product_uom=u.id)
                                LEFT JOIN
                                   product_uom u2 on (u2.id=product_template.uom_id)
                            WHERE
                                sm.state NOT IN ('draft','cancel') and
                                   source_location.usage in ('internal', 'transit') and
                                ((source_location.company_id is null and dest_location.company_id is not null) or
                                    (source_location.company_id is not null and dest_location.company_id is null) or source_location.company_id != dest_location.company_id)
                            GROUP BY
                                to_date(to_char(sm.date, 'YYYY/MM/DD'), 'YYYY/MM/DD'),
                                sm.product_id,source_location.id,product_template.categ_id,
                                source_location.company_id
                            ) as report
                        GROUP BY date,product_id,location_id,product_categ_id,company_id)""")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: