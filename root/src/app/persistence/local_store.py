"""Atomic filesystem storage for versioned local profiles and conflicts."""

import os
import tempfile
from pathlib import Path
from uuid import UUID

from app.persistence.envelope import (
    ConflictSnapshot,
    ProfileEnvelope,
    parse_conflict_snapshot,
    parse_profile_envelope,
    serialize_conflict_snapshot,
    serialize_profile_envelope,
)
from app.persistence.ports import (
    ConflictStoreResult,
    ConflictStoreStatus,
    ProfileStoreError,
    ProfileStoreResult,
    ProfileStoreStatus,
)


class LocalProfileStore:
    def __init__(self, root):
        self._root = Path(root)

    @property
    def root(self):
        return self._root

    def inspect(self, profile_id):
        result = self.load(profile_id)
        if result.status is ProfileStoreStatus.VALID:
            return ProfileStoreResult(status=ProfileStoreStatus.VALID)
        return result

    def load(self, profile_id):
        path = self._profile_path(profile_id)
        if not path.exists():
            return ProfileStoreResult(status=ProfileStoreStatus.MISSING)
        try:
            envelope = parse_profile_envelope(path.read_bytes())
        except (OSError, TypeError, ValueError):
            return ProfileStoreResult(
                status=ProfileStoreStatus.INVALID,
                error="The local profile is invalid and was not loaded.",
            )
        if envelope.profile_id != profile_id:
            return ProfileStoreResult(
                status=ProfileStoreStatus.INVALID,
                error="The local profile identity does not match its file name.",
            )
        return ProfileStoreResult(
            status=ProfileStoreStatus.VALID,
            envelope=envelope,
        )

    def save(self, envelope):
        try:
            encoded = serialize_profile_envelope(envelope)
            canonical = parse_profile_envelope(encoded)
            path = self._profile_path(canonical.profile_id)
            current = self.load(canonical.profile_id)
            if current.status is ProfileStoreStatus.INVALID:
                raise ProfileStoreError(
                    "existing local profile is invalid; refusing to replace it"
                )
            if current.status is ProfileStoreStatus.VALID:
                self._validate_sequence_advance(current.envelope, canonical)
            self._atomic_write(path, encoded)
        except ProfileStoreError:
            raise
        except (OSError, TypeError, ValueError) as error:
            raise ProfileStoreError("local profile could not be saved safely") from error

    def list_profiles(self):
        if not self._profiles_directory.is_dir():
            return ()
        profile_ids = []
        for path in self._profiles_directory.glob("*.json"):
            try:
                profile_id = UUID(path.stem)
            except (TypeError, ValueError):
                continue
            if str(profile_id) == path.stem:
                profile_ids.append(profile_id)
        return tuple(sorted(profile_ids, key=str))

    def load_conflict(self, profile_id):
        path = self._conflict_path(profile_id)
        if not path.exists():
            return ConflictStoreResult(status=ConflictStoreStatus.MISSING)
        try:
            snapshot = parse_conflict_snapshot(path.read_bytes())
        except (OSError, TypeError, ValueError):
            return ConflictStoreResult(
                status=ConflictStoreStatus.INVALID,
                error="The local conflict record is invalid and was not loaded.",
            )
        if snapshot.profile_id != profile_id:
            return ConflictStoreResult(
                status=ConflictStoreStatus.INVALID,
                error="The conflict identity does not match its file name.",
            )
        return ConflictStoreResult(
            status=ConflictStoreStatus.VALID,
            snapshot=snapshot,
        )

    def save_conflict(self, snapshot):
        try:
            encoded = serialize_conflict_snapshot(snapshot)
            canonical = parse_conflict_snapshot(encoded)
            path = self._conflict_path(canonical.profile_id)
            current = self.load_conflict(canonical.profile_id)
            if current.status is ConflictStoreStatus.INVALID:
                raise ProfileStoreError(
                    "existing conflict record is invalid; refusing to replace it"
                )
            if current.status is ConflictStoreStatus.VALID:
                if current.snapshot == canonical:
                    return
                raise ProfileStoreError(
                    "existing conflict evidence is immutable until explicitly cleared"
                )
            self._atomic_write(path, encoded)
        except ProfileStoreError:
            raise
        except (OSError, TypeError, ValueError) as error:
            raise ProfileStoreError("local conflict could not be saved safely") from error

    def replace_conflict(self, expected, replacement):
        if not isinstance(expected, ConflictSnapshot):
            raise TypeError("expected must be a ConflictSnapshot")
        if not isinstance(replacement, ConflictSnapshot):
            raise TypeError("replacement must be a ConflictSnapshot")
        if expected.profile_id != replacement.profile_id:
            raise ProfileStoreError("replacement conflict must use the same profile")
        try:
            encoded = serialize_conflict_snapshot(replacement)
            canonical = parse_conflict_snapshot(encoded)
            current = self.load_conflict(canonical.profile_id)
            if (
                current.status is not ConflictStoreStatus.VALID
                or current.snapshot != expected
            ):
                raise ProfileStoreError(
                    "conflict evidence changed before replacement"
                )
            self._atomic_write(self._conflict_path(canonical.profile_id), encoded)
        except ProfileStoreError:
            raise
        except (OSError, TypeError, ValueError) as error:
            raise ProfileStoreError(
                "local conflict could not be replaced safely"
            ) from error

    def clear_conflict(self, profile_id):
        path = self._conflict_path(profile_id)
        try:
            path.unlink(missing_ok=True)
        except OSError as error:
            raise ProfileStoreError("local conflict could not be cleared") from error

    def archive_recovery(self, envelope, snapshot=None):
        if not isinstance(envelope, ProfileEnvelope):
            raise TypeError("envelope must be a ProfileEnvelope")
        try:
            encoded_profile = serialize_profile_envelope(envelope)
            canonical_profile = parse_profile_envelope(encoded_profile)
            profile_path = self._recovery_profile_path(
                canonical_profile.profile_id, canonical_profile.client_save_id
            )
            encoded_conflict = None
            conflict_path = None
            if snapshot is not None:
                if not isinstance(snapshot, ConflictSnapshot):
                    raise TypeError("snapshot must be a ConflictSnapshot")
                if snapshot.profile_id != canonical_profile.profile_id:
                    raise ProfileStoreError(
                        "recovery records must belong to the same profile"
                    )
                encoded_conflict = serialize_conflict_snapshot(snapshot)
                canonical_conflict = parse_conflict_snapshot(encoded_conflict)
                conflict_path = self._recovery_conflict_path(
                    canonical_conflict.profile_id,
                    canonical_conflict.local_client_save_id,
                    canonical_conflict.remote_current_revision,
                )
            self._write_immutable_profile_archive(
                profile_path, encoded_profile, canonical_profile
            )
            if conflict_path is not None:
                self._write_immutable_archive(conflict_path, encoded_conflict)
        except ProfileStoreError:
            raise
        except (OSError, TypeError, ValueError) as error:
            raise ProfileStoreError("recovery data could not be archived safely") from error

    def load_recovery_profile(self, profile_id, client_save_id):
        path = self._recovery_profile_path(profile_id, client_save_id)
        return self._load_recovery_record(
            path,
            parse_profile_envelope,
            ProfileStoreStatus,
            ProfileStoreResult,
            lambda record: record.profile_id == profile_id
            and record.client_save_id == client_save_id,
            "The recovery profile is invalid and was not loaded.",
        )

    def load_recovery_conflict(self, profile_id, client_save_id, remote_revision):
        path = self._recovery_conflict_path(
            profile_id, client_save_id, remote_revision
        )
        return self._load_recovery_record(
            path,
            parse_conflict_snapshot,
            ConflictStoreStatus,
            ConflictStoreResult,
            lambda record: record.profile_id == profile_id
            and record.local_client_save_id == client_save_id
            and record.remote_current_revision == remote_revision,
            "The recovery conflict is invalid and was not loaded.",
        )

    @property
    def _profiles_directory(self):
        return self._root / "profiles"

    @property
    def _conflicts_directory(self):
        return self._root / "conflicts"

    def _profile_path(self, profile_id):
        if not isinstance(profile_id, UUID):
            raise TypeError("profile_id must be a UUID")
        return self._profiles_directory / f"{profile_id}.json"

    def _conflict_path(self, profile_id):
        if not isinstance(profile_id, UUID):
            raise TypeError("profile_id must be a UUID")
        return self._conflicts_directory / f"{profile_id}.json"

    def _recovery_profile_path(self, profile_id, client_save_id):
        self._require_archive_ids(profile_id, client_save_id)
        return (
            self._recovery_profiles_directory
            / str(profile_id)
            / f"{client_save_id}.json"
        )

    def _recovery_conflict_path(self, profile_id, client_save_id, remote_revision):
        self._require_archive_ids(profile_id, client_save_id)
        if type(remote_revision) is not int or remote_revision < 1:
            raise TypeError("remote_revision must be a positive integer")
        return (
            self._recovery_conflicts_directory
            / str(profile_id)
            / f"{client_save_id}-{remote_revision}.json"
        )

    @property
    def _recovery_profiles_directory(self):
        return self._root / "recovery" / "profiles"

    @property
    def _recovery_conflicts_directory(self):
        return self._root / "recovery" / "conflicts"

    def _require_archive_ids(self, profile_id, client_save_id):
        if not isinstance(profile_id, UUID) or not isinstance(client_save_id, UUID):
            raise TypeError("recovery IDs must be UUIDs")

    def _write_immutable_archive(self, path, encoded):
        if path.exists():
            try:
                existing = path.read_bytes()
            except OSError as error:
                raise ProfileStoreError("existing recovery data could not be read") from error
            if existing == encoded:
                return
            raise ProfileStoreError("recovery data is immutable")
        self._atomic_write(path, encoded)

    def _write_immutable_profile_archive(self, path, encoded, candidate):
        if path.exists():
            try:
                existing = parse_profile_envelope(path.read_bytes())
            except (OSError, TypeError, ValueError) as error:
                raise ProfileStoreError(
                    "existing recovery profile is invalid"
                ) from error
            if (
                existing.profile_id == candidate.profile_id
                and existing.client_save_id == candidate.client_save_id
                and existing.payload_sha256 == candidate.payload_sha256
                and existing.payload == candidate.payload
            ):
                return
            raise ProfileStoreError("recovery profile branch is immutable")
        self._atomic_write(path, encoded)

    def _load_recovery_record(
        self, path, parser, status_type, result_type, identity_matches, error_message
    ):
        if not path.exists():
            return result_type(status=status_type.MISSING)
        try:
            record = parser(path.read_bytes())
        except (OSError, TypeError, ValueError):
            return result_type(status=status_type.INVALID, error=error_message)
        if not identity_matches(record):
            return result_type(status=status_type.INVALID, error=error_message)
        if isinstance(record, ProfileEnvelope):
            return result_type(status=status_type.VALID, envelope=record)
        return result_type(status=status_type.VALID, snapshot=record)

    def _validate_sequence_advance(self, current, candidate):
        if candidate.local_sequence < current.local_sequence:
            raise ProfileStoreError("local profile sequence cannot go backwards")
        if candidate.local_sequence == current.local_sequence and (
            candidate.client_save_id != current.client_save_id
            or candidate.payload_sha256 != current.payload_sha256
        ):
            raise ProfileStoreError(
                "a changed local payload requires a new sequence and save ID"
            )
        if (
            candidate.local_sequence > current.local_sequence
            and candidate.client_save_id == current.client_save_id
        ):
            raise ProfileStoreError("a new local sequence requires a new save ID")

    def _atomic_write(self, path, encoded):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            temporary = tempfile.NamedTemporaryFile(
                mode="wb",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            )
            temporary_path = Path(temporary.name)
            with temporary:
                temporary.write(encoded)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, path)
            temporary_path = None
        except OSError as error:
            raise ProfileStoreError("atomic local profile write failed") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass


__all__ = ["LocalProfileStore", "ProfileStoreError"]
