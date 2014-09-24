import re
from openerp import models, fields, api

""" Class: ForumSEO

 	Purpose of this forum.seo model store keywords, SEO keywords with optional store URL. 
 	For improving the Forum description more descriptive with seo friendly. 
"""
class ForumSEO(models.Model):
    _name = 'forum.seo'
    _description = 'Forum SEO'
    _rec_name = 'keyword'
    
    keyword = fields.Char(string='Keyword', required="True", help="Keyword", index=True)
    replacement_word = fields.Char(string='New Keyword', help="Replace to a new keyword!")
    url = fields.Text(string='URL', help="Optional URL, The keyword will be replaced by a link to the URL\nURL start with any valid protocol http://, https://, ftp://, ftps://")
    case_sensitive = fields.Boolean(string='Case sensitive', help="Optional case sensitive, Case sensitive match (ignores case of [a-zA-Z]")

    @api.model
    def create(self, values):
        if 'url' in values:
            url = values['url']
            values['url'] = url if "://" in url else "http://" + url
        return super(ForumSEO, self).create(values)

    @api.multi
    def write(self, values):
        if 'url' in values:
            url = values['url']
            values['url'] = url if "://" in url else "http://" + url
        return super(ForumSEO, self).write(values)

    def update_seo_word(self, post_content):
        forum_words = self.search([])
        words = [(forum_word.keyword, forum_word.replacement_word, forum_word.url or None, forum_word.case_sensitive) for forum_word in forum_words]
        words.sort(key=lambda t: len(t[0]), reverse=True)

        protocals_name = ['http', 'https', 'ftp', 'ftps']
        protocals = '|'.join(protocals_name)
        prefix = "(?<!(?=((%s?)\:\/\/?)(www\.?)))" % (protocals)

        domain_extension_name = ['com', 'org', 'net', 'co\.in', 'be', 'fr']
        domain_extension = '|'.join(domain_extension_name)
        postfix = "(?!(?:(.(%s))))(?![^(<\s\-\"\.\'\,\]\)\}\?\!\:\;\\\|)]+)" % (domain_extension)

        tag_name = ['a','span']
        tags = '|'.join(tag_name)
        tag_filter = "(?=[^<>]*<)(?!(?:(?!</?(?:%s)[ >/])(?:.|\\n))*</(?:%s)>)" % (tags, tags)

        for keyword, replacement_word, url, case_sensitive in words:
            if keyword not in post_content: continue
            seo_word = replacement_word if replacement_word else keyword
            replace = "<a href='" + url + "'><span>" + seo_word + "</span></a>" if url else "<span>" +replacement_word + "</span>"
            pattern = r"%s%s%s%s" % (prefix, keyword, postfix, tag_filter)
            flag = re.M if case_sensitive else re.I|re.M
            post_content = re.sub(pattern, replace, post_content, flags=flag)

        return post_content