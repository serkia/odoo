from openerp.addons.website_blog.tests.common import TestWebsiteBlogCommon

class TestWebsiteBlogFlow(TestWebsiteBlogCommon):
    def test_website_blog(self):
        test_blog = self.Blog.create({
            'name': 'New Blog',
            'description': 'Presentation of new Odoo features'
        })
        test_blog_post = self.Blog_Post.create({
            'name': 'New Blog Post',
            'blog_id': test_blog.id,
            'website_published': True
        })
        test_blog.message_subscribe(self.user_bloguser.partner_id.ids)
        self.assertIn(self.user_bloguser.partner_id.id, test_blog.message_follower_ids.ids, 'User not Suscribed Blog Successfully')
        message_id = test_blog_post.blog_id.message_post(body=(('Post <b>%s</b> Published Of <b>%s</b> Blog') % (test_blog_post.name,test_blog_post.blog_id.name)), subtype='website_blog.mt_blog_blog_published_post')
        notif_ids = self.env["mail.notification"].search([('message_id', '=', message_id)])
        assert notif_ids, 'Blog Post Published notification not send Successfully'
        test_blog_post.sudo().message_post(
            body='Armande BlogUser Commented',
            type='comment',
            author_id=self.user_bloguser.partner_id.id,
            subtype='mt_comment',
        )
        self.assertIn(self.user_bloguser.partner_id.id, test_blog_post.message_follower_ids.ids, 'User not Follower in Blog Post Successfully')
