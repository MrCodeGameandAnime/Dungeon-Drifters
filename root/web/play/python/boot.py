"""Pyodide entry points for the playable browser shell."""

import json

import dd_bridge


def _json(value):
    return json.dumps(value, separators=(",", ":"))


def start_game_json(drifter_id="branoc"):
    return _json(dd_bridge.start_game(drifter_id))


def current_view_json():
    return _json(dd_bridge.current_view())


def submit_json(command_json):
    return _json(dd_bridge.submit(json.loads(command_json)))


def restart_game_json():
    return _json(dd_bridge.restart_game())


def drifter_roster_json():
    return _json(dd_bridge.drifter_roster())


def boot():
    return drifter_roster_json()
