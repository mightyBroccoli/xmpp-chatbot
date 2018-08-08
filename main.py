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
from slixmpp.exceptions import XMPPError

from classes.strings import StaticAnswers


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

	def start(self):
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
		keywords = {"keywords": ["!help", "!uptime", "!version", "!contact"],
					"no_arg_keywords": ["!help"]}
		valid_domain, valid_keyword = False, False

		try:
			# check for valid keyword in position 0
			if line[0] in keywords["keywords"]:
				valid_keyword = True
			else:
				return False

			# catch no arg keywords
			if line[0] in keywords["no_arg_keywords"]:
				valid_domain = True
			# check if domain is valid
			elif validators.domain(line[1]):
				valid_domain = True
			else:
				return False
		except IndexError:
			pass

		return valid_keyword and valid_domain

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
			self.send_message(mto=msg['from'].bare, mbody=StaticAnswers(msg['mucnick']).gen_answer(), mtype=msg['type'])

		reply = []

		for line in msg['body'].splitlines():
			""" split multiline messages into lines to check every line for keywords """
			# remove double whitespaces and  then split
			line = " ".join(line.split()).split(sep=" ")

			if self.precheck(line):
				""" true if keyword and domain are valid """
				# Display help
				if line[0] == '!help':
					""" display help when keyword !help is recieved """
					reply.append(StaticAnswers().gen_help())

				# XEP-0072: Server Version
				if line[0] == '!version':
					from classes.functions import Version
					""" query the server software version of the specified domain, defined by XEP-0092 """
					try:
						version = yield from self['xep_0092'].get_version(line[1])
						reply.append(Version(version, msg, line[1]).reply())
					except (NameError, XMPPError) as error:
						logger.exception(error)
						pass

				# XEP-0012: Last Activity
				if line[0] == '!uptime':
					from classes.functions import LastActivity
					""" query the server uptime of the specified domain, defined by XEP-0012 """
					try:
						last_activity = yield from self['xep_0012'].get_last_activity(line[1])
						reply.append(LastActivity(last_activity, msg, line[1]).reply())
					except (NameError, XMPPError) as error:
						logger.exception(error)
						pass

				# XEP-0157: Contact Addresses for XMPP Services
				if line[0] == "!contact":
					from classes.functions import ContactInfo
					""" query the XEP-0030: Service Discovery and extract contact information """
					try:
						contact = yield from self['xep_0030'].get_info(jid=line[1], cached=False)
						reply.append(ContactInfo(contact, msg, line[1]).reply())
					except (NameError, XMPPError) as error:
						logger.exception(error)
						pass
			else:
				pass

		# remove None type from list
		if list(filter(None.__ne__, reply)):
			self.send_message(mto=msg['from'].bare, mbody="\n".join(reply), mtype=msg['type'])


class Modules:
	def __init__(self, session):
		self.session = session


if __name__ == '__main__':
	# command line arguments.
	parser = ArgumentParser()
	parser.add_argument('-q', '--quiet', help='set logging to ERROR', action='store_const', dest='loglevel',
						const=logging.ERROR, default=logging.INFO)
	parser.add_argument('-d', '--debug', help='set logging to DEBUG', action='store_const', dest='loglevel',
						const=logging.DEBUG, default=logging.INFO)
	parser.add_argument('-D', '--dev', help='set logging to console', action='store_const', dest='logfile', const="",
						default='bot.log')
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
	xmpp.register_plugin('xep_0128')  # Service Discovery Extensions
	xmpp.register_plugin('xep_0199')  # XMPP Ping
	session = Modules(xmpp)

	# connect and start receiving stanzas
	xmpp.connect()
	xmpp.process()
