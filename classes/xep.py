#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import xml.etree.ElementTree as ET


class XEPRequest:
	def __init__(self, msg, xepnumber):
		"""
		class which requests the header of the referenced xep
		:param xepnumber: number int or str to request the xep for
		"""
		self.message_type = msg['type']
		self.muc_nick = msg['mucnick']

		self.reqxep = str(xepnumber)
		self.xeplist = None
		self.acceptedxeps = list()

	def req_xeplist(self):
		"""
		query and save the current xep list to reduce network bandwidth
		"""
		try:
			with open(".etag") as file:
				local_etag = file.read()
		except FileExistsError:
			local_etag = ""
			pass

		with requests.Session() as s:
			s.headers.update({'Accept': 'application/xml'})
			head = s.head("https://xmpp.org/extensions/xeplist.xml")
			etag = head.headers['etag']

			if local_etag == etag:
				with open("xeplist.xml", "r") as file:
					self.xeplist = ET.fromstring(file.read())
			else:
				r = s.get("https://xmpp.org/extensions/xeplist.xml")
				r.encoding = 'utf-8'
				local_etag = head.headers['etag']

				with open("xeplist.xml", "w") as file:
					file.write(r.content.decode())
					self.xeplist = ET.fromstring(r.content.decode())

				with open('.etag', 'w') as string:
					string.write(local_etag)

		# populate xep comparison list
		for xep in self.xeplist.findall(".//*[@accepted='true']/number"):
			self.acceptedxeps.append(xep.text)

	def get(self):
		"""
		function to query the xep entry if xepnumber is present in xeplist
		:return: nicely formatted xep header information
		"""
		# check if xeplist is accurate
		self.req_xeplist()

		result = list()
		# if requested number is inside acceptedxeps continou
		if self.reqxep in self.acceptedxeps:
			searchstring = ".//*[@accepted='true']/[number='%s']" % self.reqxep

			for item in self.xeplist.findall(searchstring):
				for x in range(1,5):
					result.append(item[x].tag + " : " + item[x].text)

		else:
			if self.message_type == "groupchat":
				result.append(self.muc_nick + " : " + "XEP-" + str(self.reqxep) + " : is not available.")
			else:
				result.append("XEP-" + str(self.reqxep) + " : is not available.")

		return result

	def format(self):
		reply = self.get()
		if self.message_type == "groupchat":
			text = "%s: " % self.muc_nick
			reply[0] = text + reply[0]

		text = '\n'.join(reply)

		return text
