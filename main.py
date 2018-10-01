#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
	Slixmpp: The Slick XMPP Library
	Copyright (C) 2010  Nathanael C. Fritz
	This file is part of Slixmpp.

	See the file LICENSE for copying permission.
"""
import configparser
import logging
from argparse import ArgumentParser
from classes.Querybot import QueryBot
from classes.functions import Modules

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
