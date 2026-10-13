"""Deterministic remote profile API double for client sync acceptance tests."""

from uuid import UUID
from datetime import datetime, timezone

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.envelope import payload_sha256
from app.persistence.remote_client import (
    RemoteConflict,
    RemoteProfileCreationConflict,
    RemoteProfileHead,
    RemoteProfileNotFound,
    RemoteProfileSummary,
    RemoteRequestRejected,
    RemoteUnavailable,
)
from app.persistence.save_document import build_save_document
from app.player.player_state import PlayerState


PROFILE_ID = UUID("00000000-0000-4000-8000-000000000001")
ACCOUNT_ID = UUID("00000000-0000-4000-8000-000000000004")
DEVICE_A = UUID("00000000-0000-4000-8000-000000000003")
DEVICE_B = UUID("00000000-0000-4000-8000-000000000006")
SAVE_A = UUID("00000000-0000-4000-8000-000000000002")
SAVE_B = UUID("00000000-0000-4000-8000-000000000009")
SAVE_C = UUID("00000000-0000-4000-8000-00000000000a")


def make_payload(gold=0):
    character = get_drifter_spec_by_choice("1").create_character()
    return build_save_document(GameState(PlayerState(character, gold=gold)))


class MemoryRemoteProfileServer:
    def __init__(self):
        self.available = True
        self.profiles = {}
        self.drop_next_create_after_commit = False
        self.drop_next_push_after_commit = False

    def get_profile(self, account_id, profile_id):
        self._require_available()
        record = self.profiles.get(profile_id)
        if record is None or record["account_id"] != account_id:
            raise RemoteProfileNotFound("profile is unavailable to this account")
        return self._head(profile_id, record)

    def create_profile(self, account_id, device_id, profile_id, save_id, payload):
        self._require_available()
        digest = payload_sha256(payload)
        record = self.profiles.get(profile_id)
        if record is None:
            record = {
                "account_id": account_id,
                "head": None,
                "revisions": [],
                "accepted": {},
                "claim": (save_id, digest),
            }
            record["head"] = self._make_head(
                profile_id, account_id, 1, None, save_id, payload, created=1
            )
            record["revisions"].append(record["head"])
            record["accepted"][save_id] = (digest, 1)
            self.profiles[profile_id] = record
            if self.drop_next_create_after_commit:
                self.drop_next_create_after_commit = False
                raise RemoteUnavailable("test response was lost after claim commit")
            return record["head"]
        if record["account_id"] != account_id:
            raise RemoteProfileNotFound("profile is unavailable to this account")
        if record["claim"] != (save_id, digest):
            raise RemoteProfileCreationConflict("profile_creation_conflict")
        return self._head(profile_id, record, created=1)

    def push_progression(
        self,
        account_id,
        device_id,
        profile_id,
        base_revision,
        save_id,
        payload,
    ):
        self._require_available()
        record = self.profiles.get(profile_id)
        if record is None or record["account_id"] != account_id:
            raise RemoteProfileNotFound("profile is unavailable to this account")
        digest = payload_sha256(payload)
        accepted = record["accepted"].get(save_id)
        if accepted is not None:
            accepted_digest, accepted_revision = accepted
            if accepted_digest != digest:
                raise RemoteRequestRejected("idempotency_key_reuse")
            return self._head(
                profile_id, record, accepted=accepted_revision
            )
        current = record["head"]
        if current.current_revision != base_revision:
            return RemoteConflict(
                profile_id=profile_id,
                base_revision=base_revision,
                current_revision=current.current_revision,
                client_save_id=current.client_save_id,
                payload_sha256=current.payload_sha256,
            )
        revision = current.current_revision + 1
        head = self._make_head(
            profile_id,
            account_id,
            revision,
            current.current_revision,
            save_id,
            payload,
            accepted=revision,
        )
        record["head"] = head
        record["revisions"].append(head)
        record["accepted"][save_id] = (digest, revision)
        if self.drop_next_push_after_commit:
            self.drop_next_push_after_commit = False
            raise RemoteUnavailable("test response was lost after progression commit")
        return head

    def advance(self, account_id, device_id, profile_id, base_revision, save_id, payload):
        result = self.push_progression(
            account_id, device_id, profile_id, base_revision, save_id, payload
        )
        if isinstance(result, RemoteConflict):
            raise AssertionError("test server advance used a stale base")
        return result

    def revision_count(self, profile_id):
        return len(self.profiles[profile_id]["revisions"])

    def list_profiles(self, account_id):
        created_at = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
        return tuple(
            RemoteProfileSummary(
                profile_id=profile_id,
                current_revision=record["head"].current_revision,
                created_at=created_at,
                updated_at=created_at,
            )
            for profile_id, record in sorted(self.profiles.items(), key=lambda item: str(item[0]))
            if record["account_id"] == account_id
        )

    def _head(self, profile_id, record, *, created=None, accepted=None):
        head = record["head"]
        return RemoteProfileHead(
            profile_id=profile_id,
            account_id=record["account_id"],
            current_revision=head.current_revision,
            client_save_id=head.client_save_id,
            payload_sha256=head.payload_sha256,
            payload=head.payload,
            base_revision=head.base_revision,
            created_revision=created,
            accepted_revision=accepted,
        )

    @staticmethod
    def _make_head(
        profile_id,
        account_id,
        revision,
        base_revision,
        save_id,
        payload,
        *,
        created=None,
        accepted=None,
    ):
        return RemoteProfileHead(
            profile_id=profile_id,
            account_id=account_id,
            current_revision=revision,
            client_save_id=save_id,
            payload_sha256=payload_sha256(payload),
            payload=payload,
            base_revision=base_revision,
            created_revision=created,
            accepted_revision=accepted,
        )

    def _require_available(self):
        if not self.available:
            raise RemoteUnavailable("test network is offline")


class BoundMemoryRemoteClient:
    def __init__(self, server, account_id, device_id):
        self.server = server
        self.account_id = account_id
        self.device_id = device_id
        self.advance_before_next_push = None

    def list_profiles(self):
        return self.server.list_profiles(self.account_id)

    def get_profile(self, profile_id):
        return self.server.get_profile(self.account_id, profile_id)

    def create_profile(self, profile_id, client_save_id, payload):
        return self.server.create_profile(
            self.account_id,
            self.device_id,
            profile_id,
            client_save_id,
            payload,
        )

    def push_progression(self, profile_id, base_revision, client_save_id, payload):
        if self.advance_before_next_push is not None:
            save_id, remote_payload = self.advance_before_next_push
            self.advance_before_next_push = None
            self.server.advance(
                self.account_id,
                self.device_id,
                profile_id,
                base_revision,
                save_id,
                remote_payload,
            )
        return self.server.push_progression(
            self.account_id,
            self.device_id,
            profile_id,
            base_revision,
            client_save_id,
            payload,
        )
