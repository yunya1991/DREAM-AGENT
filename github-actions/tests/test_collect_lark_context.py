import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

MODULE_PATH = MODULE_DIR / "collect_lark_context.py"
SPEC = importlib.util.spec_from_file_location("collect_lark_context", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CollectLarkContextTests(unittest.TestCase):
    @mock.patch.object(MODULE, "ensure_lark_auth")
    @mock.patch.object(MODULE, "run_lark_json")
    def test_collect_context_reads_base_record_and_okr_entities(
        self,
        mock_run,
        mock_auth,
    ):
        mock_run.side_effect = [
            {
                "data": {
                    "records": [
                        {
                            "record_id": "rec789",
                            "fields": {
                                "Title": "Pilot item",
                                "Objective ID": "obj1",
                                "KR ID": "kr1",
                            },
                        }
                    ]
                }
            },
            {
                "data": {
                    "objective": {
                        "id": "obj1",
                        "content": {
                            "blocks": [{"text": "Stabilize acceptance orchestration"}]
                        },
                    }
                }
            },
            {
                "data": {
                    "key_result": {
                        "id": "kr1",
                        "content": {
                            "blocks": [{"text": "Run one cycle from work item"}]
                        },
                    }
                }
            },
        ]

        snapshot = MODULE.collect_context_snapshot(
            {
                "work_item_id": "WI-123",
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                },
            }
        )

        mock_auth.assert_called_once_with(identity="user")
        self.assertEqual(snapshot["work_item"]["record_id"], "rec789")
        self.assertEqual(snapshot["objective"]["id"], "obj1")
        self.assertEqual(snapshot["key_result"]["id"], "kr1")
        self.assertEqual(snapshot["context_summary"], "Pilot item")

    @mock.patch.dict(os.environ, {"LARK_IDENTITY": "bot"}, clear=False)
    @mock.patch.object(MODULE, "ensure_lark_auth")
    @mock.patch.object(MODULE, "run_lark_json")
    def test_collect_context_uses_env_selected_identity_for_all_lark_calls(
        self,
        mock_run,
        mock_auth,
    ):
        mock_run.side_effect = [
            {
                "data": {
                    "records": [
                        {
                            "record_id": "rec789",
                            "fields": {
                                "Title": "Pilot item",
                                "Objective ID": "obj1",
                                "KR ID": "kr1",
                            },
                        }
                    ]
                }
            },
            {"data": {"objective": {"id": "obj1"}}},
            {"data": {"key_result": {"id": "kr1"}}},
        ]

        snapshot = MODULE.collect_context_snapshot(
            {
                "work_item_id": "WI-123",
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                },
            }
        )

        mock_auth.assert_called_once_with(identity="bot")
        self.assertEqual(mock_run.call_count, 3)
        for call in mock_run.call_args_list:
            self.assertEqual(call.kwargs["identity"], "bot")
        self.assertEqual(snapshot["objective"]["id"], "obj1")
        self.assertEqual(snapshot["key_result"]["id"], "kr1")

    @mock.patch.object(MODULE, "run_lark_json")
    def test_get_base_record_reads_real_lark_cli_record_shape(
        self,
        mock_run,
    ):
        mock_run.return_value = {
            "data": {
                "data": [
                    ["Pilot item", "obj1", "kr1"],
                ],
                "fields": ["Title", "Objective ID", "KR ID"],
                "record_id_list": ["rec789"],
            }
        }

        record = MODULE.get_base_record("app123", "tbl456", "rec789")

        self.assertEqual(record["record_id"], "rec789")
        self.assertEqual(
            record["fields"],
            {
                "Title": "Pilot item",
                "Objective ID": "obj1",
                "KR ID": "kr1",
            },
        )

    @mock.patch.object(MODULE, "ensure_lark_auth")
    @mock.patch.object(MODULE, "run_lark_json")
    def test_collect_context_reads_real_lark_cli_record_shape(
        self,
        mock_run,
        mock_auth,
    ):
        mock_run.side_effect = [
            {
                "data": {
                    "data": [
                        ["Pilot item", "obj1", "kr1"],
                    ],
                    "fields": ["Title", "Objective ID", "KR ID"],
                    "record_id_list": ["rec789"],
                },
            },
            {
                "data": {
                    "objective": {
                        "id": "obj1",
                        "content": {
                            "blocks": [{"text": "Stabilize acceptance orchestration"}]
                        },
                    }
                }
            },
            {
                "data": {
                    "key_result": {
                        "id": "kr1",
                        "content": {
                            "blocks": [{"text": "Run one cycle from work item"}]
                        },
                    }
                }
            },
        ]

        snapshot = MODULE.collect_context_snapshot(
            {
                "work_item_id": "WI-123",
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                },
            }
        )

        mock_auth.assert_called_once_with(identity="user")
        self.assertEqual(snapshot["work_item"]["record_id"], "rec789")
        self.assertEqual(snapshot["work_item"]["fields"]["Title"], "Pilot item")
        self.assertEqual(snapshot["objective"]["id"], "obj1")
        self.assertEqual(snapshot["key_result"]["id"], "kr1")
        self.assertEqual(snapshot["context_summary"], "Pilot item")

    @mock.patch.object(MODULE, "ensure_lark_auth")
    @mock.patch.object(MODULE, "run_lark_json")
    def test_collect_context_uses_task_field_as_summary_when_title_is_absent(
        self,
        mock_run,
        mock_auth,
    ):
        mock_run.side_effect = [
            {
                "data": {
                    "data": [
                        ["收集、整合用户反馈", "obj1", "kr1"],
                    ],
                    "fields": ["任务", "Objective ID", "KR ID"],
                    "record_id_list": ["rec789"],
                },
            },
            {"data": {"objective": {"id": "obj1"}}},
            {"data": {"key_result": {"id": "kr1"}}},
        ]

        snapshot = MODULE.collect_context_snapshot(
            {
                "work_item_id": "WI-123",
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                },
            }
        )

        mock_auth.assert_called_once_with(identity="user")
        self.assertEqual(snapshot["work_item"]["fields"]["任务"], "收集、整合用户反馈")
        self.assertEqual(snapshot["context_summary"], "收集、整合用户反馈")

    @mock.patch.object(MODULE, "collect_context_snapshot")
    def test_main_reads_cycle_file_and_prints_context_json(self, mock_collect):
        mock_collect.return_value = {
            "work_item": {"record_id": "rec789", "fields": {"Title": "Pilot item"}},
            "objective": {},
            "key_result": {},
            "context_summary": "Pilot item",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cycle_path = Path(tmpdir) / "acceptance_cycle.json"
            cycle_path.write_text(
                json.dumps(
                    {
                        "acceptance_cycle_id": "ac-20260607-001",
                        "lark_context_locator": {
                            "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                            "table_id": "tbl456",
                            "record_id": "rec789",
                        },
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with mock.patch.object(sys, "argv", ["collect_lark_context.py", str(cycle_path)]):
                with mock.patch.dict(os.environ, {}, clear=False):
                    with mock.patch("sys.stdout", new=stdout):
                        MODULE.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["work_item"]["record_id"], "rec789")
        self.assertEqual(payload["context_summary"], "Pilot item")


if __name__ == "__main__":
    unittest.main()
