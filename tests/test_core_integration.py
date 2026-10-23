"""Docs integration with the distributed core configuration and RAG capabilities."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from yamcps import ConfigStore, RagConfig, RagContext
from yamcps.cli import main
from yamcps.server import create_server

from yamcps_docs import DocsConnector, configured_index


class CoreIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "rag"
        self.root.mkdir()
        self.store = ConfigStore(self.root / "config.json")
        environment = patch.dict("os.environ", {"YAMCPS_RAG_DIR": str(self.root)})
        environment.start()
        self.addCleanup(environment.stop)

    def test_cli_set_list_delete_and_docs_share_the_store(self):
        arguments = ["--config-file", str(self.store.path)]
        with patch(
            "sys.argv",
            [
                "yamcps",
                "configs",
                "set",
                "--connector",
                "docs",
                "--name",
                "index",
                "--value",
                str(self.root / "docs.sqlite3"),
                *arguments,
            ],
        ):
            main()
        self.assertEqual(configured_index(self.store.path).path, self.root / "docs.sqlite3")
        docs = DocsConnector()
        with patch("yamcps.server.load", return_value=[docs]):
            create_server(config_store=self.store)
        self.assertEqual(docs.index.path, configured_index(self.store.path).path)
        with (
            patch("sys.argv", ["yamcps", "configs", "list", *arguments]),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            main()
        self.assertIn("YAMCPS_DOCS_INDEX=", output.getvalue())
        with patch(
            "sys.argv",
            ["yamcps", "configs", "delete", "--connector", "docs", "--name", "index", *arguments],
        ):
            main()
        self.assertEqual(self.store.values(), {})
        with (
            patch(
                "sys.argv",
                [
                    "yamcps",
                    "configs",
                    "set",
                    "--connector",
                    "docs",
                    "--value",
                    "invalid",
                    *arguments,
                ],
            ),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            with self.assertRaises(SystemExit):
                main()

    def test_docs_ingestion_and_server_use_same_defaults_and_overrides(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.home", return_value=Path(self.temp.name)):
                default = RagContext("docs", RagConfig()).path
                self.assertTrue(str(default).endswith("/yamcps/rag/docs.sqlite3"))
        with patch.dict("os.environ", {"YAMCPS_RAG_DIR": str(self.root)}, clear=True):
            docs = DocsConnector()
            with self.assertRaisesRegex(ValueError, "not configured"):
                _ = docs.index
            with patch("yamcps.server.load", return_value=[docs]):
                create_server()
            self.assertEqual(docs.index.path, configured_index().path)
            self.assertEqual(docs.index.path, self.root / "docs.sqlite3")
        explicit = self.root / "legacy.sqlite3"
        with patch.dict("os.environ", {"YAMCPS_DOCS_INDEX": str(explicit)}, clear=True):
            self.assertEqual(configured_index().path, explicit)
