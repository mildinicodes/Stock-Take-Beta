import tempfile
import unittest
from pathlib import Path

from src.stock_take_beta.services.progress_store import ProgressStore


class ProgressStoreTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "progress.json"
            store = ProgressStore(path)
            state = store.load()
            state["audit"]["JOR001"] = {"physical": True}
            store.save(state)
            loaded = store.load()
            self.assertTrue(loaded["audit"]["JOR001"]["physical"])
            self.assertIsNotNone(loaded["updated_at"])


if __name__ == "__main__":
    unittest.main()
