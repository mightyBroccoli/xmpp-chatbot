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
				try:
					target = words[index + 1]
					last_activity = yield from self['xep_0012'].get_last_activity(target)
					from classes.functions import LastActivity

					reply.append(LastActivity(last_activity, msg, target).format_values())
				except (NameError, XMPPError, IndexError):
					pass
				test = Modules(self, msg, words, keyword, index).start()
				for x in test:
					print(x)

		# remove None type from list and send all elements
		if list(filter(None.__ne__, reply)) and reply:
			self.send_message(mto=msg['from'].bare, mbody="\n".join(reply), mtype=msg['type'])
