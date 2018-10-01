# -*- coding: utf-8 -*-
import logging

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

		# call the reply function
		self.reply()

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

	def format_values(self, granularity=4):
		seconds = self.last_activity['last_activity']['seconds']
		intervals = (
			('years', 31536000),  # 60 * 60 * 24 * 365
			('weeks', 604800),  # 60 * 60 * 24 * 7
			('days', 86400),  # 60 * 60 * 24
			('hours', 3600),  # 60 * 60
			('minutes', 60),
			('seconds', 1)
		)
		uptime = []

		for name, count in intervals:
			value = seconds // count
			if value:
				seconds -= value * count
				if value == 1:
					name = name.rstrip('s')
				uptime.append("{} {}".format(value, name))
		result = ' '.join(uptime[:granularity])

		if self.message_type == "groupchat":
			text = "%s: %s is running since %s" % (self.nick, self.target, result)
		else:
			text = "%s is running since %s" % (self.target, result)

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


class Modules:
	"""
	modules class to handle the execution of various features
	:param session: valid xmpp session
	:param keyword: valid keyword
	:param index: index of the valid keyword
	"""
	def __init__(self, session, msg, words, keyword, index):
		self.logger = logging.getLogger(__name__)
		self.session = session
		self.message = msg
		self.words = words
		self.keyword = keyword
		self.index = index

	def start(self):
		if self.keyword == '!help':
			return StaticAnswers.gen_help()

		elif self.keyword == '!uptime':
			try:
				target = self.words[self.index + 1]
				last_activity = yield from self['xep_0012'].get_last_activity(target)

				return LastActivity(last_activity, self.message, target).format_values()
			except (NameError, XMPPError):
				pass

		elif self.keyword == "!version":
			try:
				target = self.words[self.index + 1]
				version = yield from self['xep_0092'].get_version(target)

				return Version(version, self.message, target)
			except (NameError, XMPPError):
				pass
		else:
			print("unknown keyword")
			pass

