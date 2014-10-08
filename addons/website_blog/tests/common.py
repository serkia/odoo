from openerp.tests import common

class TestWebsiteBlogCommon(common.TransactionCase):
    def setUp(self):
        super(TestWebsiteBlogCommon, self).setUp()

        # Usefull models
        self.Users = self.env['res.users']
        self.Blog = self.env['blog.blog']
        self.Blog_Post = self.env['blog.post']
        # Test users to use through the various tests
        self.user_blogmanager = self.Users.with_context({'no_reset_password': True}).create({
            'name': 'Bastien BlogManager',
            'login': 'bastien',
            'alias_name': 'bastien',
            'email': 'bastien.blogmanager@example.com'
        })
        self.user_bloguser = self.Users.with_context({'no_reset_password': True}).create({
            'name': 'Armande BlogUser',
            'login': 'Armande',
            'alias_name': 'armande',
            'email': 'armande.eventuser@example.com',
        })
