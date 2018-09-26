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
from classes.functions import Modules


class QueryBot(slixmpp.ClientXMPP):
	""" A simple Slixmpp bot with some features """
	def __init__(self, jid, password, room, nick):
		slixmpp.ClientXMPP.__init__(self, jid, password)
		self.ssl_version = ssl.PROTOCOL_TLSv1_2

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

	def validate_domain(self, wordlist, index):
		"""
		validation method to reduce nonsense connection attemps to unvalid domains
		:param wordlist: words seperated by " " from the message
		:param index: keyword index inside the message
		:return: true if valid
		"""
		# keyword inside the message
		argument = wordlist[index]

		# if the argument is not inside the no_arg_keywords target is index + 1
		if argument not in StaticAnswers().keys(arg='list', keyword="no_arg_keywords"):
			try:
				target = wordlist[index + 1]
				if validators.domain(target):
					return True
			except IndexError:
				# except an IndexError if a keywords is the last word in the message
				return False
		elif argument in StaticAnswers().keys(arg='list', keyword="no_arg_keywords"):
			return True
		else:
			return

	@asyncio.coroutine
	def message(self, msg):
		"""
		Arguments:
			msg -- The received message stanza. See the documentation for stanza objects and the Message stanza to see
					how it may be used.
		"""
		# init empty reply list
		reply = list()

		# catch self messages to prevent self flooding
		if msg['mucnick'] == self.nick:
			return
		elif self.nick in msg['body']:
			# add pre predefined text to reply list
			reply.append(StaticAnswers(msg['mucnick']).gen_answer())

		# building the queue
		# double splitting to exclude whitespaces
		words = " ".join(msg['body'].split()).split(sep=" ")
		queue = list()

		# check all words in side the message for possible hits
		for x in enumerate(words):
			# check word for match in keywords list
			for y in StaticAnswers().keys(arg='list'):
				# if so queue the keyword and the postion in the string
				if x[1] == y:
					# only add job to queue if domain is valid
					if self.validate_domain(words, x[0]):
						queue.append({str(y): x[0]})

		# queue
		for job in queue:
			for key in job:
				keyword = key
				index = job[key]

				# hand over the xmpp object, keyword and index to Modules
				gen = Modules(self, words, keyword, index)
				reply.append(next(gen))

		# remove None type from list and send all elements
		if list(filter(None.__ne__, reply)) and reply:
			self.send_message(mto=msg['from'].bare, mbody="\n".join(reply), mtype=msg['type'])

		#### PRECAUTION TO EXIT GRACEFULLY ####
		exit(0)

		for line in msg['body'].splitlines():
			""" split multiline messages into lines to check every line for keywords
			remove double whitespaces and then split """
			line = " ".join(line.split()).split(sep=" ")

			if self.precheck(line):
				keyword = line[0]
				""" true if keyword and domain are valid """


				# XEP-0072: Server Version
				if keyword == '!version':
					from classes.functions import Version
					""" query the server software version of the specified domain, defined by XEP-0092 """
					try:
						version = yield from self['xep_0092'].get_version(target)
						reply.append(Version(version, msg, target).reply())
					except (NameError, XMPPError) as error:
						logger.exception(error)
						pass

				# XEP-0012: Last Activity
				if keyword == '!uptime':
					from classes.functions import LastActivity
					""" query the server uptime of the specified domain, defined by XEP-0012 """
					try:
						last_activity = yield from self['xep_0012'].get_last_activity(target)
						reply.append(LastActivity(last_activity, msg, target).reply())
					except (NameError, XMPPError) as error:
						logger.exception(error)
						pass

				# XEP-0157: Contact Addresses for XMPP Services
				if keyword == "!contact":
					contact = Modules(self, target)
					print(contact.contact())

					"""
					from classes.functions import ContactInfo
					"" query the XEP-0030: Service Discovery and extract contact information ""
					contact = yield from self['xep_0030'].get_info(jid=line[1], cached=False)
					for items in contact:
						reply.append(ContactInfo(items, msg, target).reply())
					"""
			else:
				pass


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
	xmpp.register_plugin('xep_0012')  # Last Activity
	xmpp.register_plugin('xep_0030')  # Service Discovery
	xmpp.register_plugin('xep_0045')  # Multi-User Chat
	xmpp.register_plugin('xep_0060')  # PubSub
	xmpp.register_plugin('xep_0085')  # Chat State Notifications
	xmpp.register_plugin('xep_0092')  # Software Version
	xmpp.register_plugin('xep_0128')  # Service Discovery Extensions
	xmpp.register_plugin('xep_0199')  # XMPP Ping

	# connect and start receiving stanzas
	xmpp.connect()
	xmpp.process()
