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
				reply.append(Version(version, msg, target))
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
















	def gen_help(self):
		text = StaticAnswers().gen_help()
		return text

	def contact(self):
		try:
			yield from self.session['xep_0030'].get_info(jid=self.target, cached=False)
		except XMPPError as error:
			self.logger.exception(error)
			pass

		print("blub")
		#for items in contact:
		#	self.contact_format(items)

		#return self.reply


	def contact_format(self, query):
		# misc
		target = self.target
		server_info = []
		sep = ' , '

		# format reply
		for field in query['disco_info']['form']:
			var = field['var']
			if field['type'] == 'hidden' and var == 'FORM_TYPE':
				title = field['value'][0]
				continue
			field_value = field.get_value(convert=False)
			value = sep.join(field_value) if isinstance(field_value, list) else field_value
			server_info.append('%s: %s' % (var, value))

		if server_info.__len__() > 0:
			text = "contact addresses for %s are" % (target)
			for count in range(server_info.__len__()):
				text += "\n" + server_info[count]
			self.reply =+ text