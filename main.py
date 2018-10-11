#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
	James the MagicXMPP Bot
	build with Slick XMPP Library
	Copyright (C) 2018 Nico Wellpott

	See the file LICENSE for copying permission.
"""
import slixmpp
import ssl
import configparser
import logging

from argparse import ArgumentParser
from slixmpp.exceptions import XMPPError

import common.misc as misc
from common.strings import StaticAnswers
from classes.functions import Version, ContactInfo, HandleError
from classes.servercontact import ServerContact
from classes.uptime import LastActivity
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

		# register receive handler for both groupchat and normal message events
		self.add_event_handler('message', self.message)

	def start(self, event):
		"""
		:param event -- An empty dictionary. The session_start event does not provide any additional data.
		"""
		self.send_presence()
		self.get_roster()

		# If a room password is needed, use: password=the_room_password
		if self.room:
			for rooms in self.room.split(sep=","):
				self.plugin['xep_0045'].join_muc(rooms, self.nick, wait=True)

	async def message(self, msg):
		"""
		:param msg: received message stanza
		"""
		data = {
			'words': list(),
			'reply': list(),
			'queue': list()
		}

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
						data['reply'].append(LastActivity(self, msg, target).format_values())

						#last_activity = await self['xep_0012'].get_last_activity(jid=target)
						#data['reply'].append(LastActivity(last_activity, msg, target).format_values())

					elif keyword == "!version":
						version = await self['xep_0092'].get_version(jid=target)
						data['reply'].append(Version(version, msg, target).format_version())

					elif keyword == "!contact":
						contact = await self['xep_0030'].get_info(jid=target, cached=False)
						data['reply'].append(ServerContact(contact, msg, target).format_contact())

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
