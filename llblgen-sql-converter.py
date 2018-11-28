# -*- coding: utf-8 -*-
""" Plugin for Sublime Text 3
	Converts output SQL from LLBLGen to valid t-SQL
"""


import sublime
import sublime_plugin
import re

class Param:
	""" Holds parameters for SQL statements
	ex: param = @1, param_type = varchar, value = 'random text'
	"""
	def __init__(self, param, param_type, value):
		self.param = param
		self.param_type = param_type
		self.value = value

class sql_set_paramsCommand(sublime_plugin.TextCommand):
	""" Parse selected text, and replace with SQL
	"""
	def run(self, edit):
		self.queries = []
		selection = self.view.sel()
		for region in selection:
			self.lines = self.view.substr(region).split("\n")

			i = 0
			while i < len(self.lines):
				if self.lines[i].startswith("\tQuery:"):
					query = self.lines[i].replace("\tQuery: ", "")
					params = []
					i = i+1
					while "Method Exit:" not in self.lines[i]:
						if self.lines[i].startswith("\tParameter:"):
							params.append(self.get_parameter(self.lines[i]))
							i = i+1
					self.queries.append(self.build_query(query, params))
				else:
					i = i+1

		self.view.replace(edit, region, "\n\n".join(self.queries))


	def get_parameter(self, line):
		""" Gets parameter with type, name and value
		"""
		parts = line.split()
		param = parts[1]
		param_type = self.get_type(parts[3].replace(".", ""))
		value = parts[-1].replace(".", "")

		if parts[3] == "Boolean.":
			value = value.replace("False", "0").replace("True", "1")

		if param_type == "varchar":
			value = value.replace("\"", "'")

		return Param(param, param_type, value)


	def build_query(self, query, params):
		""" Combine query with declare statements
		"""
		final_query = ""
		for n in params:
			final_query = final_query + "declare " + n.param + " " + n.param_type + " = " + n.value + "\n"

		final_query = final_query + "\n" + self.formatted_query(query)

		return final_query


	def formatted_query(self, query):
		""" Used to add line breaks for readability
		"""
		rep = {
			"WHERE": "\nWHERE",
			"FROM": "\nFROM",
			"AND": "\nAND",
			"INNER JOIN",: "\nINNER JOIN"
		}
		return self.format_string(query, rep)


	def get_type(self, param_type):
		# Int16, Int32, Int64, Boolean, DateTime, AnsiString, String, Double
		rep = {
			"Int16": "int",
			"Int32": "int",
			"Int64": "int",
			"AnsiString": "varchar",
			"String": "varchar",
			"Double": "float",
			"Boolean": "int"
		}
		return self.format_string(param_type, rep)


	def format_string(self, input, words):
		""" Repalce key word with value word in input
		"""
		words = dict((re.escape(k), v) for k, v in words.items())
		pattern = re.compile("|".join(words.keys()))
		input = pattern.sub(lambda m: words[re.escape(m.group(0))], input)
		return input