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

import common.misc as misc
from common.strings import StaticAnswers
from classes.functions import Version, LastActivity, ContactInfo, HandleError
from classes.xep import XEPRequest


class QueryBot(slixmpp.ClientXMPP):
	def __init__(self, jid, password, room, nick):
		slixmpp.ClientXMPP.__init__(self, jid, password)
		self.ssl_version = ssl.PROTOCOL_TLSv1_2
		self.room = room
		self.nick = nick

		self.data = {
			'words': list(),
			'reply': list(),
			'queue': list()
		}

		# session start event, starting point for the presence and roster requests
		self.add_event_handler('session_start', self.start)

		# register recieve handler for both groupchat and normal message events
		self.add_event_handler('message', self.message)

	def start(self, event):
		"""
		:param event -- An empty dictionary. The session_start event does not provide any additional data.
		"""
		self.send_presence()
		self.get_roster()

		# If a room password is needed, use: password=the_room_password
		for rooms in self.room.split(sep=","):
			self.plugin['xep_0045'].join_muc(rooms, self.nick, wait=True)

	def validate(self, wordlist, index):
		"""
		validation method to reduce malformed querys and unnecessary connection attempts
		:param wordlist: words separated by " " from the message
		:param index: keyword index inside the message
		:return: true if valid
		"""
		# keyword inside the message
		argument = wordlist[index]

		# check if argument is in the argument list
		if argument in StaticAnswers().keys(arg='list'):
			# if argument uses a domain check for occurence in list and check domain
			if argument in StaticAnswers().keys(arg='list', keyword='domain_keywords'):
				try:
					target = wordlist[index + 1]
					if validators.domain(target):
						return True
				except IndexError:
					# except an IndexError if a keywords is the last word in the message
					return False

			# check if number keyword is used if true check if target is assignable
			elif argument in StaticAnswers().keys(arg='list', keyword='number_keywords'):
				try:
					if wordlist[index + 1]:
						return True
				except IndexError:
					# except an IndexError if target is not assignable
					return False
			# check if argument is inside no_arg list
			elif argument in StaticAnswers().keys(arg='list', keyword="no_arg_keywords"):
				return True
			else:
				return False
		else:
			return False

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

	async def message(self, msg):
		"""
		:param msg: received message stanza
		"""
		data = self.data

		# catch self messages to prevent self flooding
		if msg['mucnick'] == self.nick:
			return

		elif self.nick in msg['body']:
			# add pre predefined text to reply list
			data['reply'].append(StaticAnswers(msg['mucnick']).gen_answer())

		# building the queue
		# double splitting to exclude whitespaces
		data['words'] = " ".join(msg['body'].split()).split(sep=" ")

		# check all words in side the message for possible hits
		for x in enumerate(data['words']):
			# check word for match in keywords list
			for y in StaticAnswers().keys(arg='list'):
				# if so queue the keyword and the position in the string
				if x[1] == y:
					# only add job to queue if domain is valid
					if misc.validate(data['words'], x[0]):
						data['queue'].append({str(y): x[0]})

		# queue
		for job in data['queue']:
			for keyword in job:
				index = job[keyword]

				if keyword == '!help':
					data['reply'].append(StaticAnswers().gen_help())
					continue

				target = data['words'][index + 1]
				try:
					if keyword == '!uptime':
						last_activity = await self['xep_0012'].get_last_activity(jid=target)
						self.data['reply'].append(LastActivity(last_activity, msg, target).format_values())

					elif keyword == "!version":
						version = await self['xep_0092'].get_version(jid=target)
						self.data['reply'].append(Version(version, msg, target).format_version())


					elif keyword == "!contact":
						last_activity = await self['xep_0012'].get_last_activity(jid=target)
						self.data['reply'].append(LastActivity(last_activity, msg, target).format_values())


					elif keyword == "!xep":
						data['reply'].append(XEPRequest(msg, target).format())

				except XMPPError as error:
					data['reply'].append(HandleError(error, msg, keyword, target).build_report())

		# remove None type from list and send all elements
		if list(filter(None.__ne__, data['reply'])) and data['reply']:
			reply = misc.deduplicate(data['reply'])
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
