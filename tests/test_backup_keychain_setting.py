"""``storage.backupKeychain``: with it off, account backups never touch the Keychain.

Every ``security`` call is replaced by one that fails the test, so a single
stray Keychain read, write or delete on the backup path shows up as a failure.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from claude_swap import macos_keychain
from claude_swap.credentials import CredentialStore
from claude_swap.models import Platform
from claude_swap.settings import (
    StorageSettings,
    effective_settings,
    load_storage_settings,
    set_setting,
)

CREDS = json.dumps({"claudeAiOauth": {"accessToken": "sk-a", "refreshToken": "rt-a"}})
NEWER = json.dumps({"claudeAiOauth": {"accessToken": "sk-b", "refreshToken": "rt-b"}})


class _Host:
    def __init__(self, credentials_dir: Path):
        self.platform = Platform.MACOS
        self.credentials_dir = credentials_dir
        self._logger = logging.getLogger("test")


def _no_keychain(*args, **kwargs):
    raise AssertionError(f"Keychain touched: {args}")


@pytest.fixture
def backup_root(tmp_path: Path) -> Path:
    root = tmp_path / "backup"
    (root / "credentials").mkdir(parents=True)
    return root


@pytest.fixture
def store_without_keychain(backup_root: Path, monkeypatch) -> CredentialStore:
    set_setting(backup_root, "storage.backupKeychain", "false")
    for fn in ("get_password", "set_password", "delete_password"):
        monkeypatch.setattr(macos_keychain, fn, _no_keychain)
    return CredentialStore(_Host(backup_root / "credentials"))


class TestSetting:
    def test_defaults_to_keychain(self, backup_root: Path):
        assert load_storage_settings(backup_root) == StorageSettings(backup_keychain=True)

    def test_config_set_turns_it_off(self, backup_root: Path):
        set_setting(backup_root, "storage.backupKeychain", "false")
        assert load_storage_settings(backup_root).backup_keychain is False
        rows = {spec.dotted: value for spec, value, _ in effective_settings(backup_root)}
        assert rows["storage.backupKeychain"] is False

    def test_non_bool_value_falls_back_to_default(self, backup_root: Path):
        (backup_root / "settings.json").write_text(
            json.dumps({"storage": {"backupKeychain": "no"}})
        )
        assert load_storage_settings(backup_root).backup_keychain is True


class TestBackupsStayInFiles:
    def test_write_then_read_round_trips_through_the_enc_file(
        self, store_without_keychain: CredentialStore
    ):
        store = store_without_keychain
        store._write_account_credentials("3", "a@example.com", CREDS)
        assert store._backup_enc_path("3", "a@example.com").is_file()
        assert store._read_account_credentials("3", "a@example.com") == CREDS
        assert store._read_account_credentials_ex("3", "a@example.com") == (CREDS, False)

    def test_overwrite_keeps_the_previous_generation_as_a_file(
        self, store_without_keychain: CredentialStore
    ):
        store = store_without_keychain
        store._write_account_credentials("3", "a@example.com", CREDS)
        store._write_account_credentials("3", "a@example.com", NEWER)
        assert store._read_account_credentials("3", "a@example.com") == NEWER
        assert store._prev_backup_path("3", "a@example.com").is_file()
        assert store._read_previous_backup("3", "a@example.com") == CREDS

    def test_missing_backup_reads_as_absent_not_unreadable(
        self, store_without_keychain: CredentialStore
    ):
        assert store_without_keychain._read_account_credentials_ex("9", "x@example.com") == ("", False)

    def test_delete_removes_the_files(self, store_without_keychain: CredentialStore):
        store = store_without_keychain
        store._write_account_credentials("3", "a@example.com", CREDS)
        store._write_account_credentials("3", "a@example.com", NEWER)
        store._delete_account_credentials("3", "a@example.com")
        store.delete_previous_backup("3", "a@example.com")
        assert not store._backup_enc_path("3", "a@example.com").exists()
        assert not store._prev_backup_path("3", "a@example.com").exists()

    def test_reports_the_file_backend(self, store_without_keychain: CredentialStore):
        assert store_without_keychain._uses_file_backup_backend() is True
