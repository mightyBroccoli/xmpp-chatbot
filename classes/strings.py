# -*- coding: utf-8 -*-
from random import randint


class StaticAnswers:
	def __init__(self, nick=""):
		self.nickname = nick
		self.helpfile = {'help'   : '!help -- display this text',
						'version': '!version domain.tld  -- receive XMPP server version',
						'uptime' : '!uptime domain.tld -- receive XMPP server uptime',
						'contact': '!contact domain.tld -- receive XMPP server contact address info'}
		self.possible_answers = {'1': 'I heard that, %s.',
								'2': 'I am sorry for that %s.',
								'3': '%s did you try turning it off and on again?'}

	def gen_help(self):
		helpdoc = "\n".join(['%s' % value for (_, value) in self.helpfile.items()])
		return helpdoc

	def gen_answer(self):
		possible_answers = self.possible_answers
		return possible_answers[str(randint(1, possible_answers.__len__()))] % self.nickname
