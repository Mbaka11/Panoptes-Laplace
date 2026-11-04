"""Synthetic semantics for SYN-07 through SYN-10: unknown vs zero, scheduled context,
workspace isolation, and source-deletion propagation.

In-memory, synthetic-only, no I/O, no persistence, no cryptography. This is NOT a
production schema, storage design, or security boundary. See workspace-semantics.md.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

UNKNOWN = "unknown"  # Used wherever a value was not measured; never substitute 0.

DERIVED_KINDS = ("feature", "finding", "cache", "export")
POLICY_ACTIONS = ("remove", "invalidate")


# --- SYN-07: empty Health query with a write-permission status -------------------

def health_query_observation(rows: list[dict[str, Any]], write_status: str | None) -> dict[str, Any]:
    """Describe a Health query without inferring read denial or a zero measurement.

    write_status is a write-authorization value kept as a separate fact. It says
    nothing about read access, and an empty result cannot distinguish denial,
    no data, or no producer.
    """
    observation: dict[str, Any] = {
        "rows_returned": len(rows),
        "write_status": write_status if write_status is not None else UNKNOWN,
        "read_authorization": UNKNOWN,  # not observable from results or write status
        "measurements": [],
    }
    if not rows:
        observation["measured_value"] = UNKNOWN
        observation["interpretation"] = "no_rows_returned_cause_unknown"
        return observation
    observation["measurements"] = [copy.deepcopy(r) for r in rows]
    observation["measured_value"] = UNKNOWN  # aggregation is not this spike's job
    observation["interpretation"] = "rows_returned"
    return observation


# --- SYN-08: planned calendar event vs observed activity -------------------------

def classify_calendar_events(
    events: list[dict[str, Any]], observations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Planned events are scheduled context unless an observation explicitly confirms them.

    Time overlap alone is only a possible overlap, never a confirmation. Scheduled
    duration is never reported as observed duration.
    """
    results = []
    for event in events:
        confirming = [o["id"] for o in observations if o.get("confirms_event_id") == event["id"]]
        start, end = event.get("start"), event.get("end")
        overlapping = [
            o["id"] for o in observations
            if o["id"] not in confirming and start is not None and end is not None
            and o.get("start") is not None and o.get("end") is not None
            and o["start"] < end and start < o["end"]
        ]
        if confirming:
            role = "observed_activity"
        else:
            role = "scheduled_context"
        results.append({
            "event_id": event["id"],
            "role": role,
            "confirmed_by": confirming,
            "possible_overlap_with": overlapping,
            "observed_duration": UNKNOWN,
        })
    return results


# --- SYN-09 / SYN-10: workspace isolation and deletion ---------------------------

@dataclass
class Node:
    kind: str  # source, feature, finding, cache, export
    content: Any
    parents: tuple[str, ...] = ()
    status: str = "active"  # active, removed, invalidated
    delivered: bool = False  # exports only: a copy may exist outside this store


@dataclass
class Workspace:
    nodes: dict[str, Node] = field(default_factory=dict)
    corrections: dict[str, list[str]] = field(default_factory=dict)  # target id -> notes


class WorkspaceStore:
    """Every operation names its workspace; identifiers are only unique within one."""

    def __init__(self) -> None:
        self._workspaces: dict[str, Workspace] = {}

    def _ws(self, workspace: str) -> Workspace:
        if workspace not in self._workspaces:
            self._workspaces[workspace] = Workspace()
        return self._workspaces[workspace]

    def add_source(self, workspace: str, source_id: str, records: list[Any]) -> None:
        self._ws(workspace).nodes[source_id] = Node("source", copy.deepcopy(records))

    def derive(self, workspace: str, kind: str, derived_id: str, parents: list[str], content: Any,
               delivered: bool = False) -> None:
        if kind not in DERIVED_KINDS:
            raise ValueError("unknown derived kind")
        ws = self._ws(workspace)
        for parent in parents:  # links can only point inside the same workspace
            if parent not in ws.nodes:
                raise KeyError(f"parent not in workspace: {parent}")
        ws.nodes[derived_id] = Node(kind, copy.deepcopy(content), tuple(parents), delivered=delivered)

    def read(self, workspace: str, node_id: str) -> Any:
        node = self._ws(workspace).nodes.get(node_id)
        if node is None:
            raise KeyError(node_id)
        if node.status != "active":
            return {"status": node.status}  # no content after removal/invalidation
        return copy.deepcopy(node.content)

    def correct(self, workspace: str, target_id: str, note: str) -> None:
        ws = self._ws(workspace)
        if target_id not in ws.nodes:
            raise KeyError(target_id)
        ws.corrections.setdefault(target_id, []).append(note)

    def corrections(self, workspace: str, target_id: str) -> list[str]:
        return list(self._ws(workspace).corrections.get(target_id, []))

    def export(self, workspace: str) -> dict[str, Any]:
        """Export active nodes of ONE workspace, with provenance links and corrections."""
        ws = self._ws(workspace)
        return {
            "workspace": workspace,
            "nodes": {
                nid: {"kind": n.kind, "parents": list(n.parents), "content": copy.deepcopy(n.content),
                      "corrections": list(ws.corrections.get(nid, []))}
                for nid, n in ws.nodes.items() if n.status == "active"
            },
        }

    def snapshot(self, workspace: str) -> dict[str, Any]:
        """Deep copy of full internal state, for before/after isolation checks."""
        ws = self._ws(workspace)
        return copy.deepcopy({"nodes": ws.nodes, "corrections": ws.corrections})

    def delete_source(self, workspace: str, source_id: str, policy: dict[str, str]) -> dict[str, Any]:
        """Delete a source and apply a declared per-kind policy to all dependents.

        policy maps every derived kind to "remove" (drop content and node) or
        "invalidate" (drop content, keep a tombstone so the loss is visible). A
        policy missing a kind is rejected rather than defaulted. Only the named
        workspace is touched. Delivered exports cannot be recalled by this store,
        so they are reported as unverified copies.
        """
        if set(policy) != set(DERIVED_KINDS) or any(a not in POLICY_ACTIONS for a in policy.values()):
            raise ValueError("policy must declare remove|invalidate for every derived kind")
        ws = self._ws(workspace)
        if source_id not in ws.nodes or ws.nodes[source_id].kind != "source":
            raise KeyError(source_id)

        affected = {source_id}
        changed = True
        while changed:  # transitive closure over parent links, same workspace only
            changed = False
            for nid, node in ws.nodes.items():
                if nid not in affected and any(p in affected for p in node.parents):
                    affected.add(nid)
                    changed = True

        actions: dict[str, str] = {source_id: "remove"}
        unverified: list[str] = []
        for nid in sorted(affected - {source_id}):
            node = ws.nodes[nid]
            actions[nid] = policy[node.kind]
            if node.kind == "export" and node.delivered:
                unverified.append(nid)
        orphaned_corrections = sorted(t for t in ws.corrections if t in affected)
        for nid, action in actions.items():
            if action == "remove":
                del ws.nodes[nid]
            else:
                ws.nodes[nid].content = None
                ws.nodes[nid].status = "invalidated"
        # Corrections on removed targets are dropped; on tombstones they are kept, flagged.
        for target in orphaned_corrections:
            if target not in ws.nodes:
                del ws.corrections[target]
        return {
            "workspace": workspace,
            "deleted_source": source_id,
            "actions": actions,
            "unverified_copies": unverified,  # delivery/removal of these copies is NOT verified
            "orphaned_corrections": orphaned_corrections,
        }
