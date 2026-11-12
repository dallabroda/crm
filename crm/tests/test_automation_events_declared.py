"""Every event crm.automation.events emits must be declared in hooks.automation_events, or the automation engine
refuses it at emit time (bug: crm.lead_converted made every lead conversion fail with automation on)."""

import ast
import os
import unittest

import crm
from crm import hooks

EVENTS_FILE = os.path.join(os.path.dirname(crm.__file__), "automation", "events.py")


def emitted_events() -> set:
	tree = ast.parse(open(EVENTS_FILE, encoding="utf-8").read())
	names = set()
	for node in ast.walk(tree):
		if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "emit" and node.args:
			first = node.args[0]
			if isinstance(first, ast.Constant) and isinstance(first.value, str):
				names.add(first.value)
	return names


class TestAutomationEventsDeclared(unittest.TestCase):
	def test_every_emitted_event_is_declared(self):
		declared = set()
		for group in hooks.automation_events:
			declared |= set(group)
		emitted = emitted_events()
		self.assertTrue(emitted, "no emit() calls found: the check would prove nothing")
		self.assertEqual(emitted - declared, set())
