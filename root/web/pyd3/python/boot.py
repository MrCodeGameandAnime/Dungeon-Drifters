import json

from dd_bridge import current_view, restart_game, start_game, submit


def boot():
    initial = start_game("branoc")
    if initial["screen"] != "main":
        raise AssertionError("bridge did not start MAIN view")
    if initial["contextual_route_option"]["action"] != "enter_encounter":
        raise AssertionError("bridge did not expose the authored route action")

    same_view = current_view()
    if same_view != initial:
        raise AssertionError("projection changed authoritative view state")

    after_entry = submit(
        {"kind": "overworld_action", "action": "enter_encounter"}
    )
    if "interaction_phase" not in after_entry:
        raise AssertionError("semantic entry command did not return BattleView")

    after_restart = restart_game()
    if after_restart["screen"] != "main":
        raise AssertionError("bridge restart did not rebuild the session")

    return json.dumps(
        {
            "initial": initial,
            "after_entry": after_entry,
            "after_restart": after_restart,
        }
    )
