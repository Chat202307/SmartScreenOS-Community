"""Resident-authored lists; no device actions or inferred platform semantics.

One server owns a file. A process-wide lock protects HTTP worker threads;
revision tokens reject edits from stale screens. Do not share a file between
multiple server processes or edit it externally while this server is writing.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

_LOCK = threading.RLock()
MAX_ITEMS = 1000
MAX_BYTES = 2_000_000


class TodoError(ValueError):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


def title_value(value):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
        raise TodoError(400, "invalid_title")
    return value.strip()


class TodoStore:
    def __init__(self, path):
        self.path = Path(path) if path is not None else None

    def _load(self):
        try:
            missing = self.path is None
            if self.path is None:
                raw = b""
            else:
                try:
                    with self.path.open("rb") as stream:
                        raw = stream.read(MAX_BYTES + 1)
                except FileNotFoundError:
                    missing = True
                    raw = b""
            if len(raw) > MAX_BYTES:
                raise ValueError("too large")
            data = {"todos": []} if missing else json.loads(raw)
            if not isinstance(data, dict) or data.get("schema_version", 1) != 1:
                raise ValueError("schema")
            items = data.get("todos")
            if not isinstance(items, list) or len(items) > MAX_ITEMS:
                raise ValueError("items")
            normalized, seen = [], set()
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    raise ValueError("item")
                title = title_value(item.get("title"))
                completed = item.get("completed", False)
                if not isinstance(completed, bool):
                    raise ValueError("completed")
                identifier = item.get("id")
                if identifier is None:
                    identifier = "legacy-" + hashlib.sha256(
                        (str(index) + ":" + title).encode()
                    ).hexdigest()[:24]
                if not isinstance(identifier, str) or not identifier or identifier in seen:
                    raise ValueError("id")
                seen.add(identifier)
                normalized.append(dict(item, id=identifier, title=title, completed=completed))
            return raw, {"schema_version": 1, "revision": hashlib.sha256(raw).hexdigest(), "todos": normalized}
        except (OSError, ValueError, UnicodeError, TypeError) as exc:
            print(
                "TODO LOAD FAILURE:",
                type(exc).__name__,
                repr(exc),
                "path=",
                self.path,
                flush=True,
            )
            raise TodoError(503, "todo_storage_unavailable") from None

    def read(self):
        with _LOCK:
            return self._load()[1]

    def mutate(self, payload):
        if self.path is None:
            raise TodoError(503, "todo_storage_unconfigured")
        if not isinstance(payload, dict):
            raise TodoError(400, "invalid_payload")
        with _LOCK:
            raw, data = self._load()
            if payload.get("revision") != data["revision"]:
                raise TodoError(409, "todo_conflict")
            op = payload.get("op")
            now = datetime.now(timezone.utc).isoformat()
            if op == "create":
                if len(data["todos"]) >= MAX_ITEMS:
                    raise TodoError(400, "todo_limit")
                data["todos"].append({"id": uuid4().hex, "title": title_value(payload.get("title")),
                    "completed": False, "created_at": now, "updated_at": now})
            elif op in ("update", "delete"):
                item = next((x for x in data["todos"] if x["id"] == payload.get("id")), None)
                if item is None:
                    raise TodoError(404, "todo_not_found")
                if op == "delete":
                    data["todos"].remove(item)
                else:
                    if not any(k in payload for k in ("title", "completed")):
                        raise TodoError(400, "invalid_payload")
                    if "title" in payload:
                        item["title"] = title_value(payload["title"])
                    if "completed" in payload:
                        if not isinstance(payload["completed"], bool):
                            raise TodoError(400, "invalid_completed")
                        item["completed"] = payload["completed"]
                    item["updated_at"] = now
            else:
                raise TodoError(400, "invalid_operation")
            data.pop("revision")
            serialized = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            if len(serialized) > MAX_BYTES:
                raise TodoError(400, "todo_limit")
            temporary = None
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                # Preserve the original pre-management file once, before any replacement.
                if raw:
                    backup = self.path.with_name(self.path.name + ".before-management")
                    try:
                        with backup.open("xb") as stream:
                            stream.write(raw)
                            stream.flush()
                            os.fsync(stream.fileno())
                    except FileExistsError:
                        pass
                with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix=".todos-", delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(serialized)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            except OSError:
                raise TodoError(503, "todo_save_failed") from None
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            data["revision"] = hashlib.sha256(serialized).hexdigest()
            return data
