#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# XEP-0072: Server Version
class Version:
	def __init__(self, version, msg, target):
		self.version = version['software_version']['version']
		self.os = version['software_version']['os']
		self.name = version['software_version']['name']
		self.nick = msg['mucnick']
		self.message_type = msg['type']
		self.target = target

	def format_version(self):
		if self.message_type == "groupchat":
			text = "%s: %s is running %s version %s on %s" % (self.nick, self.target, self.name, self.version, self.os)
		else:
			text = "%s is running %s version %s on %s" % (self.target, self.name, self.version, self.os)

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
		uptime = []
		intervals = (
			('years', 31536000),  # 60 * 60 * 24 * 365
			('weeks', 604800),  # 60 * 60 * 24 * 7
			('days', 86400),  # 60 * 60 * 24
			('hours', 3600),  # 60 * 60
			('minutes', 60),
			('seconds', 1)
		)
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


# XEP-0157: Contact Addresses for XMPP Services
class ContactInfo:
	def __init__(self, contact, msg, target):
		self.contact = contact
		self.message = msg
		self.target = target

	def format_contact(self):
		server_info = []
		sep = ' , '
		possible_vars = ['abuse-addresses',
						 'admin-addresses',
						 'feedback-addresses',
						 'sales-addresses',
						 'security-addresses',
						 'support-addresses']

		for field in self.contact['disco_info']['form']:
			var = field['var']
			if var in possible_vars:
				field_value = field.get_value(convert=False)
				value = sep.join(field_value) if isinstance(field_value, list) else field_value
				server_info.append(' - %s: %s' % (var, value))

		if server_info:
			text = "contact addresses for %s are" % self.target
			for count in range(server_info.__len__()):
				text += "\n" + server_info[count]
		else:
			text = "%s has no contact addresses configured." % self.target

		return text


# class handeling XMPPError exeptions
class HandleError:
	def __init__(self, error, msg, key, target="target missing"):
		self.error = error
		self.message = msg
		self.key = key
		self.target = target

	def build_report(self):
		condition = self.error.condition
		keyword = self.key[1:]

		text = "There was an error requesting " + self.target + '\'s ' + keyword + " : " + condition

		return text
