# -*- coding: utf-8 -*-
import logging
import asyncio

from classes.strings import StaticAnswers
from datetime import datetime, timedelta
from slixmpp.exceptions import XMPPError, IqError


# XEP-0072: Server Version
class Version:
	def __init__(self, version, msg, target):
		self.version = version['software_version']['version']
		self.OS = version['software_version']['os']
		self.name = version['software_version']['name']
		self.nick = msg['mucnick']
		self.message_type = msg['type']
		self.target = target

	def reply(self):
		if self.message_type == "groupchat":
			text = "%s: %s is running %s version %s on %s" % (self.nick, self.target, self.name, self.version, self.OS)
		else:
			text = "%s is running %s version %s on %s" % (self.target, self.name, self.version, self.OS)

		return text


# XEP-0012: Last Activity
class LastActivity:
	""" query the server uptime of the specified domain, defined by XEP-0012 """
	def __init__(self, last_activity, msg, target):
		self.last_activity = last_activity
		self.nick = msg['mucnick']
		self.message_type = msg['type']
		self.target = target
		self.uptime = datetime(1, 1, 1) + timedelta(seconds=self.last_activity['last_activity']['seconds'])

		print(last_activity['last_activity']['seconds'])

	def reply(self):
		uptime = self.uptime
		if self.message_type == "groupchat":
			text = "%s: %s is running since %d days %d hours %d minutes" % (self.nick, self.target, uptime.day - 1,
																			uptime.hour, uptime.minute)
		else:
			text = "%s is running since %d days %d hours %d minutes" % (self.target, uptime.day - 1, uptime.hour,
																		uptime.minute)
		return text


class ContactInfo:
	def __init__(self, contact, message, target):
		self.contact = contact
		self.message = message
		self.target = target

	def reply(self):
		server_info = []
		for field in self.contact['disco_info']['form']:
			var = field['var']
			if field['type'] == 'hidden' and var == 'FORM_TYPE':
				title = field['value'][0]
				continue
			sep = ', '
			field_value = field.get_value(convert=False)
			value = sep.join(field_value) if isinstance(field_value, list) else field_value
			server_info.append('%s: %s' % (var, value))

		if server_info.__len__() > 0:
			text = "contact addresses for %s are" % (self.target)
			for count in range(server_info.__len__()):
				text += "\n" + server_info[count]
			return text


@asyncio.coroutine
class Modules:
	"""
	modules class to handle the execution of varios features
	:param session: valid xmpp session
	:param keyword: valid keyword
	:param index: index of the valid keyword
	"""
	def __init__(self, session, words, keyword, index ):
		self.logger = logging.getLogger(__name__)
		self.session = session
		self.words = words
		self.keyword = keyword
		self.index = index

		if keyword == "!help":
			self.gen_help()

	def gen_help(self):
		text = StaticAnswers().gen_help()
		return text

	def contact(self):
		try:
			yield from self.session['xep_0030'].get_info(jid=self.target, cached=False)
		except XMPPError as error:
			self.logger.exception(error)
			pass

		print("blub")
		#for items in contact:
		#	self.contact_format(items)

		#return self.reply


	def contact_format(self, query):
		# misc
		target = self.target
		server_info = []
		sep = ' , '

		# format reply
		for field in query['disco_info']['form']:
			var = field['var']
			if field['type'] == 'hidden' and var == 'FORM_TYPE':
				title = field['value'][0]
				continue
			field_value = field.get_value(convert=False)
			value = sep.join(field_value) if isinstance(field_value, list) else field_value
			server_info.append('%s: %s' % (var, value))

		if server_info.__len__() > 0:
			text = "contact addresses for %s are" % (target)
			for count in range(server_info.__len__()):
				text += "\n" + server_info[count]
			self.reply =+ text