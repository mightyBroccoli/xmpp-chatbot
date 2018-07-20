#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
	Slixmpp: The Slick XMPP Library
	Copyright (C) 2010  Nathanael C. Fritz
	This file is part of Slixmpp.

	See the file LICENSE for copying permission.
"""
import asyncio
import configparser
import logging
import slixmpp
import ssl
import validators
from argparse import ArgumentParser
from datetime import datetime, timedelta
from random import randint
from slixmpp.exceptions import XMPPError


class QueryBot(slixmpp.ClientXMPP):
	""" A simple Slixmpp bot with some features """
	def __init__(self, jid, password, room, nick):
		slixmpp.ClientXMPP.__init__(self, jid, password)

		self.room = room
		self.nick = nick

		# session start event, starting point for the presence and roster requests
		self.add_event_handler('session_start', self.start)

		# register handler to recieve both groupchat and normal message events
		self.add_event_handler('message', self.message)

	def start(self, event):
		"""
		Arguments:
			event -- An empty dictionary. The session_start event does not provide any additional data.
		"""
		self.send_presence()
		self.get_roster()

		# If a room password is needed, use: password=the_room_password
		for rooms in self.room.split(sep=","):
			self.plugin['xep_0045'].join_muc(rooms, self.nick, wait=True)


	@staticmethod
	def precheck(line):
		"""
		pre check function
		- check that keywords are used properly
		- check that following a keyword a proper jid is following
		:param line: line from message body
		:return: true if correct
		"""
		keywords = ["!help", "!uptime", "!version", "!contact"]
		proper_domain, proper_key = False, False

		try:
			# check for valid keyword in position 0
			if line[0] in keywords:
				proper_key = True
			else:
				return

			# help command is used
			if line[0] == "!help":
				proper_domain = True
			# check if domain is valid
			elif validators.domain(line[1]):
				proper_domain = True
			else:
				return
		except IndexError:
			pass

		return proper_key and proper_domain

	@asyncio.coroutine
	def message(self, msg):
		"""
		Arguments:
			msg -- The received message stanza. See the documentation for stanza objects and the Message stanza to see
					how it may be used.
		"""

		# catch self messages to prevent self flooding
		if msg['mucnick'] == self.nick:
			return

		if self.nick in msg['body']:
			# answer with predefined text when mucnick is used
			self.send_message(mto=msg['from'].bare, mbody=notice_answer(msg['mucnick']), mtype=msg['type'])

		for line in msg['body'].splitlines():
			""" split multiline messages into lines to check every line for keywords """
			line = line.split(sep= " ")

			if self.precheck(line):
				""" true if keyword and domain are valid """
				# Display help
				if line[0] == '!help':
					""" display help when keyword !help is recieved """
					self.send_message(mto=msg['from'].bare, mbody=help_doc(), mtype=msg['type'])

				# XEP-0072: Server Version
				if line[0] == '!version':
					""" query the server software version of the specified domain, defined by XEP-0092 """
					try:
						version = yield from self['xep_0092'].get_version(line[1])

						if msg['type'] == "groupchat":
							text = "%s: %s is running %s version %s on %s" % (msg['mucnick'], line[1], version[
							'software_version']['name'], version['software_version']['version'], version[
							'software_version']['os'])
						else:
							text = "%s is running %s version %s on %s" % (line[1], version['software_version'][
								'name'], version['software_version']['version'], version['software_version']['os'])

						self.send_message(mto=msg['from'].bare, mbody=text, mtype=msg['type'])
					except NameError:
						pass
					except XMPPError:
						pass

				# XEP-0012: Last Activity
				if line[0] == '!uptime':
					""" query the server uptime of the specified domain, defined by XEP-0012 """
					try:
						# try if domain[0] is set if not just pass
						last_activity = yield from self['xep_0012'].get_last_activity(line[1])
						uptime = datetime(1, 1, 1) + timedelta(seconds=last_activity['last_activity']['seconds'])

						if msg['type'] == "groupchat":
							text = "%s: %s is running since %d days %d hours %d minutes" % (msg['mucnick'], line[1],
																						uptime.day - 1, uptime.hour,
																						uptime.minute)
						else:
							text = "%s is running since %d days %d hours %d minutes" % (line[1], uptime.day - 1,
																						uptime.hour, uptime.minute)
						self.send_message(mto=msg['from'].bare, mbody=text, mtype=msg['type'])
					except NameError:
						pass
					except XMPPError:
						pass

				# XEP-0157: Contact Addresses for XMPP Services
				if line[0] == "!contact":
					""" query the XEP-0030: Service Discovery and extract contact information """
					try:
						result = yield from self['xep_0030'].get_info(jid=line[1], cached=False)
						server_info = []
						for field in result['disco_info']['form']:
							var = field['var']
							if field['type'] == 'hidden' and var == 'FORM_TYPE':
								title = field['value'][0]
								continue
							sep = '\n  ' + len(var) * ' '
							field_value = field.get_value(convert=False)
							value = sep.join(field_value) if isinstance(field_value, list) else field_value
							server_info.append('%s: %s' % (var, value))

							self.send_message(mto=msg['from'].bare, mbody=server_info, mtype=msg['type'])
					except NameError:
						pass
					except XMPPError:
						pass

				# TODO
				# append all results to single message send just once
			else:
				pass


def help_doc():
	helpfile = {'help': '!help -- display this text',
				'version': '!version domain.tld  -- receive XMPP server version',
				'uptime':'!uptime domain.tld -- receive XMPP server uptime',
				'contact': '!contact domain.tld -- receive XMPP server contact address info'}
	return "".join(['%s\n' % (value) for (_, value) in helpfile.items()])


def notice_answer(nickname):
	possible_answers = {'1': 'I heard that, %s.',
						'2': 'I am sorry for that %s.',
						'3': '%s did you try turning it off and on again?'}
	return  possible_answers[str(randint(1, len(possible_answers)))] % nickname

if __name__ == '__main__':
	# command line arguments.
	parser = ArgumentParser()
	parser.add_argument('-q', '--quiet', help='set logging to ERROR', action='store_const', dest='loglevel',
						const=logging.ERROR, default=logging.INFO)
	parser.add_argument('-d', '--debug', help='set logging to DEBUG', action='store_const', dest='loglevel',
						const=logging.DEBUG, default=logging.INFO)
	parser.add_argument('-D', '--dev', help='set logging to console', action='store_const', dest='logfile',
						const="", default='bot.log')
	args = parser.parse_args()

	# logging
	logging.basicConfig(filename=args.logfile, level=args.loglevel, format='%(levelname)-8s %(message)s')
	logger = logging.getLogger(__name__)

	# configfile
	config = configparser.RawConfigParser()
	config.read('./bot.cfg')
	args.jid = config.get('Account', 'jid')
	args.password = config.get('Account', 'password')
	args.room = config.get('MUC', 'rooms')
	args.nick = config.get('MUC', 'nick')
	args.admins = config.get('ADMIN', 'admins')

	# init the bot and register used slixmpp plugins
	xmpp = QueryBot(args.jid, args.password, args.room, args.nick)
	xmpp.ssl_version = ssl.PROTOCOL_TLSv1_2
	xmpp.register_plugin('xep_0012')  # Last Activity
	xmpp.register_plugin('xep_0030')  # Service Discovery
	xmpp.register_plugin('xep_0045')  # Multi-User Chat
	xmpp.register_plugin('xep_0060')  # PubSub
	xmpp.register_plugin('xep_0085')  # Chat State Notifications
	xmpp.register_plugin('xep_0092')  # Software Version
	xmpp.register_plugin('xep_0199')  # XMPP Ping

	# connect and start receiving stanzas
	xmpp.connect()
	xmpp.process()
