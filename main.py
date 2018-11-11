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
from classes.servercontact import ServerContact
from classes.version import Version
from classes.uptime import LastActivity
from classes.xep import XEPRequest


class QueryBot(slixmpp.ClientXMPP):
	def __init__(self, jid, password, room, nick):
		slixmpp.ClientXMPP.__init__(self, jid, password)
		self.ssl_version = ssl.PROTOCOL_TLSv1_2
		self.room = room
		self.nick = nick
		self.use_message_ids = True

		self.functions = {
			"!uptime": LastActivity(),
			"!contact": ServerContact(),
			"!version": Version(),
			"!xep": XEPRequest()
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
				logging.debug("joining: %s" % rooms)
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

		data = self.build_queue(data, msg)

		# queue
		for job in data['queue']:
			keys = list(job.keys())
			keyword = keys[0]

			target = job[keyword][0]
			opt_arg = job[keyword][1]
			query = None

			if keyword == '!help':
				data['reply'].append(StaticAnswers().gen_help())
				continue

			try:
				if keyword == "!uptime":
					query = await self['xep_0012'].get_last_activity(jid=target)

				elif keyword == "!version":
					query = await self['xep_0092'].get_version(jid=target)

				elif keyword == "!contact":
					query = await self['xep_0030'].get_info(jid=target, cached=False)

			except XMPPError as error:
				logging.info(misc.HandleError(error, keyword, target).report())
				data['reply'].append(misc.HandleError(error, keyword, target).report())
				continue

			data["reply"].append(self.functions[keyword].format(query=query, target=target, opt_arg=opt_arg))

		# remove None type from list and send all elements
		if list(filter(None.__ne__, data['reply'])) and data['reply']:

			# if msg type is groupchat prepend mucnick
			if msg["type"] == "groupchat":
				data["reply"][0] = "%s: " % msg["mucnick"] + data["reply"][0]

			# reply = misc.deduplicate(data['reply'])
			reply = data["reply"]
			self.send_message(mto=msg['from'].bare, mbody="\n".join(reply), mtype=msg['type'])

	def build_queue(self, data, msg):
		# building the queue
		# double splitting to exclude whitespaces
		data['words'] = " ".join(msg['body'].split()).split(sep=" ")
		wordcount = len(data["words"])

		# check all words in side the message for possible hits
		for x in enumerate(data['words']):
			# check for valid keywords
			index = x[0]
			keyword = x[1]

			# match all words starting with ! and member of no_arg_keywords
			if keyword.startswith("!") and keyword in StaticAnswers().keys("no_arg_keywords"):
				data['queue'].append({keyword: [None, None]})

			# matching all words starting with ! and member of keywords
			elif keyword.startswith("!") and keyword in StaticAnswers().keys("keywords"):
				# init variables to circumvent IndexErrors
				target, opt_arg = None, None

				# compare to wordcount if assignment is possible
				if index + 1 < wordcount:
					target = data["words"][index + 1]

				if index + 2 < wordcount:
					if not data["words"][index + 2].startswith("!"):
						opt_arg = data["words"][index + 2]

				# only add job to queue if domain is valid
				if misc.validate(keyword, target):
					logging.debug("Item added to queue %s" % {str(keyword): [target, opt_arg]})
					data['queue'].append({str(keyword): [target, opt_arg]})

		# deduplicate queue elements
		data["queue"] = misc.deduplicate(data["queue"])

		return data


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
	logging.basicConfig(filename=args.logfile, level=args.loglevel, format='%(levelname)s: %(asctime)s: %(message)s')
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
