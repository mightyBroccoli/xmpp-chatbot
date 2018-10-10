# -*- coding: utf-8 -*-
import defusedxml.ElementTree as Et


class ServerContact:
	def __init__(self, contact, msg, target):
		self.contact = contact
		self.message = msg
		self.target = target

		self.possible_vars = ['abuse-addresses',
							'admin-addresses',
							'feedback-addresses',
							'sales-addresses',
							'security-addresses',
							'support-addresses']

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

			# check for multiple x nodes
			for x in range(len(xdata)):

				# iterate over all x nodes
				for child in xdata[x]:

					# if node has a var attribute that matches our list process
					if child.attrib['var'] in self.possible_vars:
						# add section to result dict and append info
						result[child.attrib['var']] = list()
						for value in child:
							result[child.attrib['var']].append(value.text)

			return result

	def format_contact(self):
		result = self.process()

		if result:
			text = "contact addresses for %s are\n" % self.target

			for key in result.keys():
				if result[key]:
					addr = ' , '.join(result[key])
					text += "- %s : %s\n" % (key, addr)
		else:
			text = "%s has no contact addresses configured." % self.target

		return text
