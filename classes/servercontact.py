# -*- coding: utf-8 -*-
import defusedxml.ElementTree as Et


# XEP-0157: Contact Addresses for XMPP Services
class ServerContact:
	"""
	plugin to process the server contact addresses from a disco query
	"""
	def __init__(self):
		# init all necessary variables
		self.possible_vars = ['abuse-addresses',
							'admin-addresses',
							'feedback-addresses',
							'sales-addresses',
							'security-addresses',
							'support-addresses']

		self.contact = None
		self.target, self.opt_arg = None, None

	def opt_arg_abbreviation(self):
		"""
		optional argument abbreviation function
		if the provided string > 2 characters the most likely key will be chosen
		:return: completes the opt_arg to the most likely one
		"""
		# if opt_argument is smaller then 2 pass to prohibit multiple answers
		if len(self.opt_arg) < 2:
			pass

		abbr = str(self.opt_arg)
		possible_abbr = ["abuse-addresses", "admin-addresses", "feedback-addresses", "sales-addresses",
			"security-addresses", "support-addresses"]

		# searches the best match in the list of possible_abbr and completes the opt_arg to that
		self.opt_arg = [s for s in possible_abbr if s.startswith(abbr)][0]

	def process(self):
		# get etree from base xml
		iq = Et.fromstring(str(self.contact))

		# check if query is a valid result query
		if iq.find('{http://jabber.org/protocol/disco#info}query'):
			# only init result dict if result query is present
			result = dict()

			# extract query from iq
			query = iq.find('{http://jabber.org/protocol/disco#info}query')

			# extract jabber:x:data from query
			xdata = query.findall('{jabber:x:data}x')

			# iterate over all nodes with the xdata tag
			for node in xdata:

				# iterate over all child elements in node
				for child in node:

					# if one opt_arg is defined return just that one
					if self.opt_arg in self.possible_vars:
						# check for possible abbreviations to the optional argument
						self.opt_arg_abbreviation()

						if child.attrib['var'] == self.opt_arg:
							# add section to result dict and append info
							result[child.attrib['var']] = list()
							for value in child:
								result[child.attrib['var']].append(value.text)

					# if node has a var attribute that matches our list process
					elif child.attrib['var'] in self.possible_vars:
						# add section to result dict and append info
						result[child.attrib['var']] = list()
						for value in child:
							result[child.attrib['var']].append(value.text)

			return result

	def format(self, query, target, opt_arg):
		self.contact = query

		self.target = target
		self.opt_arg = opt_arg

		result = self.process()

		# if result is present continue
		if result:
			text = "contact addresses for %s are\n" % self.target

			# if opt_arg is present and member of possible_vars change text line
			if self.opt_arg in self.possible_vars:
				text = "%s for %s are\n" % (self.opt_arg, self.target)

			for key in result.keys():
				addr = ' , '.join(result[key])
				text += "- %s : %s\n" % (key, addr)
		else:
			text = "%s has no contact addresses configured." % self.target

			# if opt_arg is present and member of possible_vars but the key is empty change text line
			if self.opt_arg in self.possible_vars:
				text = "%s for %s are not defined." % (self.opt_arg, self.target)

		return text
