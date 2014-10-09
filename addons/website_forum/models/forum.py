# -*- coding: utf-8 -*-

from datetime import datetime

import openerp
from openerp import SUPERUSER_ID, models, fields, api, _, tools
from openerp.tools import html2plaintext
from openerp.addons.website.models.website import slug
from openerp.exceptions import except_orm


class KarmaError(ValueError):
    """ Karma-related error, used for forum and posts. """
    pass


class Forum(models.Model):
    _name = 'forum.forum'
    _description = 'Forum'
    _inherit = ['mail.thread', 'website.seo.metadata']

    @api.model
    def _get_default_faq(self):
        fname = openerp.modules.get_module_resource('website_forum', 'data', 'forum_default_faq.html')
        with open(fname, 'r') as f:
            return f.read()
        return False

    name = fields.Char(string='Forum Name', required=True, translate=True)
    faq = fields.Html(string='Guidelines', default=_get_default_faq, translate=True)
    description = fields.Html(
        'Description',
        default='<p> This community is for professionals and enthusiasts of our products and services.'
                'Share and discuss the best content and new marketing ideas,'
                'build your professional profile and become a better marketer together.</p>')
    # introduction_message = fields.Html('Introduction Message',
    #     default="""<h1 class="mt0">Welcome!</h1>
    #         <p> This community is for professionals and enthusiasts of our products and services.
    #             Share and discuss the best content and new marketing ideas,
    #             build your professional profile and become a better marketer together.
    #         </p>""")
    relevancy_option_first = fields.Float('First Relevancy Parameter', default=0.8)
    relevancy_option_second = fields.Float('Second Relevancy Parameter', default=1.8)
    default_order = fields.Selection([
        ('create_date desc', 'Newest'),
        ('write_date desc', 'Last Updated'),
        ('vote_count desc', 'Most Voted'),
        ('relevancy desc', 'Relevancy'),
        ('child_count desc', 'Answered')],
        string='Default Order', required=True, default='write_date desc')
    default_allow = fields.Selection([
        ('ask_question', 'Question'),
        ('post_discussion', 'Discussion'),
        ('post_link', 'Link')],
        string='Default Post', required=True, default='ask_question')
    allow_link = fields.Boolean('Links', help="When clicking on the post, it redirects to an external link", default=False)
    allow_question = fields.Boolean('Questions', help="Users can answer only once per question. Contributors can edit answers and mark the right ones.", default=True)
    allow_discussion = fields.Boolean('Discussions', default=False)
    # karma generation
    karma_gen_question_new = fields.Integer(string='Post a Questions', default=2)
    karma_gen_question_upvote = fields.Integer(string='Upvote a Question', default=5)
    karma_gen_question_downvote = fields.Integer(string='Downvote a Question', default=-2)
    karma_gen_answer_upvote = fields.Integer(string='Upvote an Answer', default=10)
    karma_gen_answer_downvote = fields.Integer(string='Downvote an answer', default=-2)
    karma_gen_answer_accept = fields.Integer(string='Accept an Answer', default=2)
    karma_gen_answer_accepted = fields.Integer(string='Have Your Answer Accepted', default=15)
    karma_gen_answer_flagged = fields.Integer(string='Have Your Answer Flagged', default=-100)
    # karma-based actions
    karma_ask = fields.Integer(string='Ask a new question', default=0)
    karma_answer = fields.Integer(string='Answer a question', default=0)
    karma_edit_own = fields.Integer(string='Edit its own posts', default=1)
    karma_edit_all = fields.Integer(string='Edit all posts', default=300)
    karma_close_own = fields.Integer(string='Close its own posts', default=100)
    karma_close_all = fields.Integer(string='Close all posts', default=500)
    karma_unlink_own = fields.Integer(string='Delete its own posts', default=500)
    karma_unlink_all = fields.Integer(string='Delete all posts', default=1000)
    karma_upvote = fields.Integer(string='Upvote', default=5)
    karma_downvote = fields.Integer(string='Downvote', default=50)
    karma_answer_accept_own = fields.Integer(string='Accept an answer on its own questions', default=20)
    karma_answer_accept_all = fields.Integer(string='Accept an answers to all questions', default=500)
    karma_editor_link_files = fields.Integer(string='Linking files (Editor)', default=20)
    karma_editor_clickable_link = fields.Integer(string='Add clickable links (Editor)', default=20)
    karma_comment_own = fields.Integer(string='Comment its own posts', default=1)
    karma_comment_all = fields.Integer(string='Comment all posts', default=1)
    karma_comment_convert_own = fields.Integer(string='Convert its own answers to comments and vice versa', default=50)
    karma_comment_convert_all = fields.Integer(string='Convert all answers to answers and vice versa', default=500)
    karma_comment_unlink_own = fields.Integer(string='Unlink its own comments', default=50)
    karma_comment_unlink_all = fields.Integer(string='Unlinnk all comments', default=500)
    karma_retag = fields.Integer(string='Change question tags', default=75)
    karma_flag = fields.Integer(string='Flag a post as offensive', default=500)

    @api.model
    def create(self, values):
        return super(Forum, self.with_context(mail_create_nolog=True)).create(values)


class Post(models.Model):
    _name = 'forum.post'
    _description = 'Forum Post'
    _inherit = ['mail.thread', 'website.seo.metadata']
    _order = "is_correct DESC, vote_count DESC, write_date DESC"

    @api.multi
    @api.depends('vote_ids', 'vote_ids.vote')
    def _compute_relevancy(self):
        for post in self:
            if post.create_date:
                days = (datetime.today() - datetime.strptime(post.create_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)).days
            else:
                days = 0
            relavency = abs(post.vote_count - 1) ** post.forum_id.relevancy_option_first / ( days + 2) ** post.forum_id.relevancy_option_second
            post.relevancy = relavency if (post.vote_count - 1) >= 0 else -relavency

    @api.multi
    def _get_user_vote(self):
        votes = self.env['forum.post.vote'].search_read([('post_id', 'in', self._ids), ('user_id', '=', self._uid)], ['vote', 'post_id'])
        mapped_vote = dict([(v['post_id'][0], v['vote']) for v in votes]) 
        for vote in self:
            vote.user_vote = mapped_vote.get(vote.id, 0)

    @api.multi
    @api.depends('vote_ids', 'vote_ids.vote')
    def _get_vote_count(self):
        for post in self:
            post.vote_count = sum([int(vote.vote) for vote in post.vote_ids])

    @api.one
    def _get_user_favourite(self):
        self.user_favourite = self._uid in self.favourite_ids.ids

    @api.one
    @api.depends('favourite_ids')
    def _get_favorite_count(self):
        self.favourite_count = len(self.favourite_ids)

    @api.multi
    @api.depends('child_ids')
    def _get_child_count(self): 
        for post in self:
            post.child_count = len(post.child_ids)

    @api.multi
    def _get_uid_answered(self):
        for post in self:
            post.uid_has_answered = any(answer.create_uid.id == self._uid for answer in post.child_ids)

    @api.multi
    @api.depends('child_ids', 'is_correct')
    def _get_has_validated_answer(self):
        for post in self:
            post.has_validated_answer = False
            if post.parent_id:
                post.parent_id.has_validated_answer = post.is_correct #TODO:this thing is not working may be due to bug

    @api.multi
    @api.depends('create_uid', 'parent_id')
    def _is_self_reply(self):
        for post in self:
            post.self_reply = post.parent_id and post.parent_id.create_uid == post.parent_id or False

    @api.one
    def _get_post_karma_rights(self):
        user = self.env.user
        self.can_ask = user.karma >= self.forum_id.karma_ask
        self.can_answer = user.karma >= self.forum_id.karma_answer
        self.can_accept = user.karma >= (self.parent_id and self.parent_id.create_uid.id == self._uid and self.forum_id.karma_answer_accept_own or self.forum_id.karma_answer_accept_all)
        self.can_edit = user.karma >= (self.create_uid.id == self._uid and self.forum_id.karma_edit_own or self.forum_id.karma_edit_all)
        self.can_close = user.karma >= (self.create_uid.id == self._uid and self.forum_id.karma_close_own or self.forum_id.karma_close_all)
        self.can_unlink = user.karma >= (self.create_uid.id == self._uid and self.forum_id.karma_unlink_own or self.forum_id.karma_unlink_all)
        self.can_upvote = user.karma >= self.forum_id.karma_upvote
        self.can_downvote = user.karma >= self.forum_id.karma_downvote
        self.can_comment = user.karma >= (self.create_uid.id == self._uid and self.forum_id.karma_comment_own or self.forum_id.karma_comment_all)
        self.can_comment_convert = user.karma >= (self.create_uid.id == self._uid and self.forum_id.karma_comment_convert_own or self.forum_id.karma_comment_convert_all)

    name = fields.Char(string='Title')
    forum_id = fields.Many2one('forum.forum', string='Forum', required=True)
    content = fields.Html(string='Content')
    content_link = fields.Char(string='URL', help="URL of Link Articles")
    tag_ids = fields.Many2many('forum.tag', 'forum_tag_rel', 'forum_id', 'forum_tag_id', string='Tags')
    state = fields.Selection([('active', 'Active'), ('close', 'Close'), ('offensive', 'Offensive')], string='Status', default='active')
    views = fields.Integer(string='Number of Views', default=0)
    active = fields.Boolean(string='Active', default=True)
    type = fields.Selection([('question', 'Question'), ('link', 'Article'), ('discussion', 'Discussion')], string='Type', default='question')
    is_correct = fields.Boolean(string='Valid Answer', help='Correct Answer or Answer on this question accepted.')
    relevancy = fields.Float('Relevancy', compute="_compute_relevancy", store=True)
    website_message_ids = fields.One2many(
        'mail.message', 'res_id',
        domain=lambda self: ['&', ('model', '=', self._name), ('type', 'in', ['email', 'comment'])],
        string='Post Messages', help="Comments on forum post",
    )
    # history
    create_date = fields.Datetime(string='Asked on', select=True, readonly=True)
    create_uid = fields.Many2one('res.users', string='Created by', select=True, readonly=True)
    write_date = fields.Datetime(string='Update on', select=True, readonly=True)
    write_uid = fields.Many2one('res.users', string='Updated by', select=True, readonly=True)
    # vote fields
    vote_ids = fields.One2many('forum.post.vote', 'post_id', string='Votes', default=list())
    user_vote = fields.Integer(string='My Vote', compute='_get_user_vote')
    vote_count = fields.Integer(string="Votes", compute='_get_vote_count', store=True)
    # favorite fields
    favourite_ids = fields.Many2many('res.users', string='Favourite', default=list())
    user_favourite = fields.Boolean(compute='_get_user_favourite', string="My Favourite")
    favourite_count = fields.Integer(compute='_get_favorite_count', string='Favorite Count', store=True)
    # hierarchy
    parent_id = fields.Many2one('forum.post', string='Question', ondelete='cascade')
    self_reply = fields.Boolean(string='Reply to own question', compute='_is_self_reply', store=True)
    child_ids = fields.One2many('forum.post', 'parent_id', string='Answers')
    child_count = fields.Integer(string="Answers", compute='_get_child_count', store=True)
    uid_has_answered = fields.Boolean(string='Has Answered', compute='_get_uid_answered')
    has_validated_answer = fields.Boolean(string='Has a Validated Answered', compute='_get_has_validated_answer', store=True)
    # closing
    closed_reason_id = fields.Many2one('forum.post.reason', string='Reason')
    closed_uid = fields.Many2one('res.users', string='Closed by', select=1)
    closed_date = fields.Datetime(string='Closed on', readonly=True)
    # access rights
    can_ask = fields.Boolean(string='Can Ask', compute='_get_post_karma_rights')
    can_answer = fields.Boolean(string='Can Answer', compute='_get_post_karma_rights')
    can_accept = fields.Boolean(string='Can Accept', compute='_get_post_karma_rights')
    can_edit = fields.Boolean(string='Can Edit', compute='_get_post_karma_rights')
    can_close = fields.Boolean(string='Can Close', compute='_get_post_karma_rights')
    can_unlink = fields.Boolean(string='Can Unlink', compute='_get_post_karma_rights')
    can_upvote = fields.Boolean(string='Can Upvote', compute='_get_post_karma_rights')
    can_downvote = fields.Boolean(string='Can Downvote', compute='_get_post_karma_rights')
    can_comment = fields.Boolean(string='Can Comment', compute='_get_post_karma_rights', store=True)
    can_comment_convert = fields.Boolean(string='Can Convert to Comment', compute='_get_post_karma_rights')

    @api.model
    def create(self, vals):
        self = self.with_context(mail_create_nolog=True)
        post = super(Post, self).create(vals)
        # deleted or closed questions
        if post.parent_id and (post.parent_id.state == 'close' or post.parent_id.active == False):
            raise except_orm(_('Error !'), _('Posting answer on [Deleted] or [Closed] question is prohibited'))
        # karma-based access
        if post.parent_id and not post.can_ask:
            raise KarmaError('Not enough karma to create a new question')
        elif not post.parent_id and not post.can_answer:
            raise KarmaError('Not enough karma to answer to a question')
        # messaging and chatter
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if post.parent_id:
            body = _(
                '<p>A new answer for <i>%s</i> has been posted. <a href="%s/forum/%s/question/%s">Click here to access the post.</a></p>' % 
                (post.parent_id.name, base_url, slug(post.parent_id.forum_id), slug(post.parent_id))
            )
            post.parent_id.message_post(subject=_('Re: %s') % post.parent_id.name, body=body, subtype='website_forum.mt_answer_new')
        else:
            body = _(
                '<p>A new question <i>%s</i> has been asked on %s. <a href="%s/forum/%s/question/%s">Click here to access the question.</a></p>' % 
                (post.name, post.forum_id.name, base_url, slug(post.forum_id), slug(post))
            )
            post.message_post(subject=post.name, body=body, subtype='website_forum.mt_question_new')
            self.sudo().env['res.users'].search([('id', '=', self._uid)]).add_karma(post.forum_id.karma_gen_question_new)
        return post

    @api.multi
    def write(self, vals):
        if 'state' in vals:
            if vals['state'] in ['active', 'close'] and any(not post.can_close for post in self):
                raise KarmaError('Not enough karma to close or reopen a post.')
        if 'active' in vals:
            if any(not post.can_unlink for post in self):
                raise KarmaError('Not enough karma to delete or reactivate a post')
        if 'is_correct' in vals:
            if any(not post.can_accept for post in self):
                raise KarmaError('Not enough karma to accept or refuse an answer')
            # update karma except for self-acceptance
            mult = 1 if vals['is_correct'] else -1
            for post in self:
                if vals['is_correct'] != post.is_correct and post.create_uid.id != self._uid:
                    super_self = self.sudo()
                    super_self.env['res.users'].search([('id', '=', post.create_uid.id)]).add_karma(post.forum_id.karma_gen_answer_accepted * mult)
                    super_self.env['res.users'].search([('id', '=', self._uid)]).add_karma(post.forum_id.karma_gen_answer_accept * mult)
        if any(key not in ['state', 'active', 'is_correct', 'closed_uid', 'closed_date', 'closed_reason_id'] for key in vals.keys()) and any(not post.can_edit for post in self):
            raise KarmaError('Not enough karma to edit a post.')

        res = super(Post, self).write(vals)
        # if post content modify, notify followers
        if 'content' in vals or 'name' in vals:
            for post in self:
                if post.parent_id:
                    body, subtype = _('Answer Edited'), 'website_forum.mt_answer_edit'
                    obj_id = post.parent_id
                else:
                    body, subtype = _('Question Edited'), 'website_forum.mt_question_edit'
                    obj_id = post
                obj_id.message_post(body=body, subtype=subtype)
        return res


    def close(self, reason_id):
        if any(post.parent_id for post in self):
            return False
        self.write({
            'state': 'close',
            'closed_uid': self._uid,
            'closed_date': datetime.today().strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
            'closed_reason_id': reason_id,
        })
        return True

    @api.multi
    def unlink(self):
        if any(not post.can_unlink for post in self):
            raise KarmaError('Not enough karma to unlink a post')
        # if unlinking an answer with accepted answer: remove provided karma
        for post in self:
            if post.is_correct:
                super_self = self.sudo()
                super_self.env['res.users'].search([('id', '=', post.create_uid.id)]).add_karma(post.forum_id.karma_gen_answer_accepted * -1)
                super_self.env['res.users'].search([('id', '=', self._uid)]).add_karma(post.forum_id.karma_gen_answer_accepted * -1)
        return super(Post, self).unlink()

    def vote(self, upvote=True):
        if upvote and any(not post.can_upvote for post in self):
            raise KarmaError('Not enough karma to upvote.')
        elif not upvote and any(not post.can_downvote for post in self):
            raise KarmaError('Not enough karma to downvote.')

        Vote = self.env['forum.post.vote']
        vote_ids = Vote.search([('post_id', 'in', self._ids), ('user_id', '=', self._uid)])
        new_vote = '1' if upvote else '-1'
        voted_forum_ids = set()
        if vote_ids:
            for vote in vote_ids:
                if upvote:
                    new_vote = '0' if vote.vote == '-1' else '1'
                else:
                    new_vote = '0' if vote.vote == '1' else '-1'
                vote.vote = new_vote
                voted_forum_ids.add(vote.post_id.id)
        for post_id in set(self._ids) - voted_forum_ids:
            for post_id in self._ids:
                Vote.create({'post_id': post_id, 'vote': new_vote})
        return {'vote_count': self.vote_count, 'user_vote': new_vote}

    def convert_answer_to_comment(self, post):
        """ Tools to convert an answer (forum.post) to a comment (mail.message).
        The original post is unlinked and a new comment is posted on the question
        using the post create_uid as the comment's author. """
        if not post.parent_id:
            return False

        # karma-based action check: use the post field that computed own/all value
        if not post.can_comment_convert:
            raise KarmaError('Not enough karma to convert an answer to a comment')

        # post the message
        question = post.parent_id
        values = {
            'author_id': post.create_uid.partner_id.id,
            'body': html2plaintext(post.content),
            'type': 'comment',
            'subtype': 'mail.mt_comment',
            'date': post.create_date,
        }
        message_id = self.search([('id', '=', question.id)]).with_context(mail_create_nosubcribe=True).message_post(**values)

        # unlink the original answer, using SUPERUSER_ID to avoid karma issues
        post.sudo().unlink()

        return message_id

    def convert_comment_to_answer(self, message_id):
        """ Tool to convert a comment (mail.message) into an answer (forum.post).
        The original comment is unlinked and a new answer from the comment's author
        is created. Nothing is done if the comment's author already answered the
        question. """
        comment = self.sudo().env['mail.message'].search([('id', '=', message_id)])
        post = self.env['forum.post'].search([('id', '=', comment.res_id)])
        user = self.env.user
        if not comment.author_id or not comment.author_id.user_ids:  # only comment posted by users can be converted
            return False

        # karma-based action check: must check the message's author to know if own / all
        karma_convert = comment.author_id.id == user.partner_id.id and post.forum_id.karma_comment_convert_own or post.forum_id.karma_comment_convert_all
        can_convert = user.id == SUPERUSER_ID or user.karma >= karma_convert
        if not can_convert:
            raise KarmaError('Not enough karma to convert a comment to an answer')

        # check the message's author has not already an answer
        question = post.parent_id if post.parent_id else post
        post_create_uid = comment.author_id.user_ids[0]
        if any(answer.create_uid.id == post_create_uid.id for answer in question.child_ids):
            return False

        # create the new post
        post_values = {
            'forum_id': question.forum_id.id,
            'content': comment.body,
            'parent_id': question.id,
        }
        # done with the author user to have create_uid correctly set
        new_post_id = self.sudo(post_create_uid.id).env['forum.post'].create(post_values)

        # delete comment
        self.sudo().env['mail.message'].search([('id', '=', comment.id)]).unlink()

        return new_post_id
    
    def unlink_comment(self, post, comment):
        user = self.env.user
        if not comment.model == 'forum.post' or not comment.res_id == post.id:
            return False
        # karma-based action check: must check the message's author to know if own or all
        karma_unlink = comment.author_id.id == user.partner_id.id and post.forum_id.karma_comment_unlink_own or post.forum_id.karma_comment_unlink_all
        can_unlink = user.id == SUPERUSER_ID or user.karma >= karma_unlink
        if not can_unlink:
            raise KarmaError('Not enough karma to unlink a comment')
        return comment.sudo().unlink()
    @api.multi
    def set_viewed(self):
        self._cr.execute("""UPDATE forum_post SET views = views+1 WHERE id IN %s""", (self._ids,))
        return True


class PostReason(models.Model):
    _name = "forum.post.reason"
    _description = "Post Closing Reason"
    _order = 'name'

    name = fields.Char(string='Closing Reason', required=True, translate=True)


class Vote(models.Model):
    _name = 'forum.post.vote'
    _description = 'Vote'

    post_id = fields.Many2one('forum.post', string='Post', ondelete='cascade', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self._uid)
    vote = fields.Selection([('1', '1'), ('-1', '-1'), ('0', '0')], string='Vote', required=True, default='1')
    create_date = fields.Datetime('Create Date', select=True, readonly=True)
    forum_id = fields.Many2one('forum.forum', string='Forum', related="post_id.forum_id", store=True)
    recipient_id = fields.Many2one('res.users', string='To', related="post_id.create_uid", store=True)

    def _get_karma_value(self, old_vote, new_vote, up_karma, down_karma):
        _karma_upd = {
            '-1': {'-1': 0, '0': -1 * down_karma, '1': -1 * down_karma + up_karma},
            '0': {'-1': 1 * down_karma, '0': 0, '1': up_karma},
            '1': {'-1': -1 * up_karma + down_karma, '0': -1 * up_karma, '1': 0}
        }
        return _karma_upd[old_vote][new_vote]

    @api.model
    def create(self, vals):
        vote = super(Vote, self).create(vals)
        if vote.post_id.parent_id:
            karma_value = self._get_karma_value('0', vote.vote, vote.forum_id.karma_gen_answer_upvote, vote.forum_id.karma_gen_answer_downvote)
        else:
            karma_value = self._get_karma_value('0', vote.vote, vote.forum_id.karma_gen_question_upvote, vote.forum_id.karma_gen_question_downvote)
        self.sudo().recipient_id.add_karma(karma_value)
        return vote

    @api.multi
    def write(self, values):
        if 'vote' in values:
            for vote in self:
                if vote.post_id.parent_id:
                    karma_value = self._get_karma_value(vote.vote, values['vote'], vote.forum_id.karma_gen_answer_upvote, vote.forum_id.karma_gen_answer_downvote)
                else:
                    karma_value = self._get_karma_value(vote.vote, values['vote'], vote.forum_id.karma_gen_question_upvote, vote.forum_id.karma_gen_question_downvote)
                vote.sudo().recipient_id.add_karma(karma_value)
        res = super(Vote, self).write(values)
        return res


class Tags(models.Model):
    _name = "forum.tag"
    _description = "Forum Tag"
    _inherit = ['website.seo.metadata']

    @api.multi
    @api.depends("post_ids.tag_ids")
    def _get_posts_count(self):
        for tag in self:
            tag.posts_count = len(tag.post_ids)

    name = fields.Char('Name', required=True)
    forum_id = fields.Many2one('forum.forum', string='Forum', required=True)
    post_ids = fields.Many2many('forum.post', 'forum_tag_rel', 'forum_tag_id', 'forum_id', string='Posts')
    posts_count = fields.Integer('Number of Posts', compute='_get_posts_count', store=True)
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
