#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
	Slixmpp: The Slick XMPP Library
	Copyright (C) 2010  Nathanael C. Fritz
	This file is part of Slixmpp.

	See the file LICENSE for copying permission.
"""
import asyncio
import slixmpp
import ssl
import validators
import configparser
import logging

from argparse import ArgumentParser
from slixmpp.exceptions import XMPPError

from classes.strings import StaticAnswers
from classes.functions import Version, LastActivity, ContactInfo, HandleError


class QueryBot(slixmpp.ClientXMPP):
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
		:param str event -- An empty dictionary. The session_start event does not provide any additional data.
		"""
		self.send_presence()
		self.get_roster()

		# If a room password is needed, use: password=the_room_password
		for rooms in self.room.split(sep=","):
			self.plugin['xep_0045'].join_muc(rooms, self.nick, wait=True)

	def validate_domain(self, wordlist, index):
		"""
		validation method to reduce connection attemps to unvalid domains
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

	def deduplicate(self, reply):
		"""
		deduplication method for the result list
		:param list reply: list containing strings
		:return: list containing unique strings
		"""
		reply_dedup = list()
		for item in reply:
			if item not in reply_dedup:
				reply_dedup.append(item)

		return reply_dedup

	@asyncio.coroutine
	def message(self, msg):
		"""
		:param msg: received message stanza
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

				if keyword == '!help':
					reply.append(StaticAnswers().gen_help())

				try:
					target = words[index + 1]
					if keyword == '!uptime':
						last_activity = yield from self['xep_0012'].get_last_activity(target)
						reply.append(LastActivity(last_activity, msg, target).format_values())

					elif keyword == "!version":
						version = yield from self['xep_0092'].get_version(target)
						reply.append(Version(version, msg, target).format_version())

					elif keyword == "!contact":
						contact = yield from self['xep_0030'].get_info(jid=target, cached=False)
						reply.append(ContactInfo(contact, msg, target).format_contact())

				except XMPPError as error:
					reply.append(HandleError(error, msg, key, target).build_report())

		# remove None type from list and send all elements
		if list(filter(None.__ne__, reply)) and reply:
			reply = self.deduplicate(reply)
			self.send_message(mto=msg['from'].bare, mbody="\n".join(reply), mtype=msg['type'])


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
