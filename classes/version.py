# -*- coding: utf-8 -*-


# XEP-0072: Server Version
class Version:
	"""
	process and format a version query
	"""
	def __init__(self):
		# init all necessary variables
		self.software_version = None
		self.target, self.opt_arg = None, None

	def format_result(self):
		# list of all possible opt_arg
		possible_opt_args = ["version", "os", "name"]

		name = self.software_version['name']
		version = self.software_version['version']
		os = self.software_version['os']

		# if opt_arg is given member of possible_opt_args list return that element
		if self.opt_arg in possible_opt_args:
			text = "%s: %s" % (self.opt_arg, self.software_version[self.opt_arg])

		# otherwise return full version string
		else:
			text = "%s is running %s version %s on %s" % (self.target, name, version, os)

		return text

	def format(self, query, target, opt_arg):
		self.software_version = query['software_version']

		self.target = target
		self.opt_arg = opt_arg

		reply = self.format_result()
		return reply
