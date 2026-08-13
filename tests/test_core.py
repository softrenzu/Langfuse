import os
import tempfile
import unittest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["AIOPS_DB"] = _tmp.name

from aiops.costops import budget_status, set_budget
from aiops.ops import incidents, overview
from aiops.promptops import get_prompt, put_prompt
from aiops.recording import record_span


class CoreTest(unittest.TestCase):
    def test_core_flow(self):
        record_span(name="answer", input="user@example.com", latency_ms=100, cost_usd=0.01, metadata={"prompt_version": "v1"})
        self.assertEqual(overview(60)["traces"], 1)
        self.assertEqual(incidents(60), [])
        self.assertEqual(put_prompt("answer", "hello", ["production"]), 1)
        self.assertEqual(get_prompt("answer", "production")["content"], "hello")
        set_budget("monthly", 10)
        self.assertFalse(budget_status()[0]["breached"])


if __name__ == "__main__":
    unittest.main()
