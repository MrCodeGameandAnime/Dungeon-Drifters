"""Authored optional story scenes for the M8 campaign."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StoryChoiceSpec:
    choice_id: str
    label: str
    response: str

    def __post_init__(self):
        for name in ("choice_id", "label", "response"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonempty")


@dataclass(frozen=True)
class StorySceneSpec:
    scene_id: str
    title: str
    dialogue: tuple[str, ...]
    choices: tuple[StoryChoiceSpec, ...] = ()
    completion_response: str = ""

    def __post_init__(self):
        for name in ("scene_id", "title"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonempty")
        if not isinstance(self.dialogue, tuple) or not self.dialogue:
            raise ValueError("dialogue must be a nonempty tuple")
        if any(not isinstance(line, str) or not line.strip() for line in self.dialogue):
            raise ValueError("dialogue lines must be nonempty")
        if not isinstance(self.choices, tuple):
            raise TypeError("choices must be a tuple")
        if len(self.choices) > 2 or any(
            not isinstance(choice, StoryChoiceSpec) for choice in self.choices
        ):
            raise ValueError("a scene may have at most two authored choices")
        if len({choice.choice_id for choice in self.choices}) != len(self.choices):
            raise ValueError("scene choice IDs must be unique")
        if not isinstance(self.completion_response, str):
            raise TypeError("completion_response must be a string")
        if not self.choices and not self.completion_response.strip():
            raise ValueError("scenes without choices require a completion response")


M8_PAIR_SCENE_BY_PAIR = {
    ("azhvielle", "branoc"): "m8_pair_scene_branoc_azhvielle",
    ("branoc", "joruun"): "m8_pair_scene_branoc_joruun",
    ("branoc", "zhaivra"): "m8_pair_scene_branoc_zhaivra",
    ("azhvielle", "joruun"): "m8_pair_scene_azhvielle_joruun",
    ("azhvielle", "zhaivra"): "m8_pair_scene_azhvielle_zhaivra",
    ("joruun", "zhaivra"): "m8_pair_scene_joruun_zhaivra",
}


M8_STORY_SCENES = (
    StorySceneSpec(
        "m8_pair_scene_branoc_azhvielle",
        "The Cost Of A Warning",
        (
            "Branoc: A warning can save a company. It can also send one into a trap.",
            "Azhvielle: Knowledge is not dangerous by itself. Certainty borrowed from it often is.",
            "Branoc: Then tell me what you know, and what you do not.",
            "Azhvielle: That distinction is the responsibility. The rest is only temptation.",
        ),
        (
            StoryChoiceSpec(
                "share_warning",
                "Share the warning, with its limits",
                "Branoc: Then we tell them what the warning can bear, not what we wish it said.\nAzhvielle: Good. No one should mistake a warning for an order.",
            ),
            StoryChoiceSpec(
                "leave_closed",
                "Leave the record closed for now",
                "Branoc: Not until we know who would pay for acting on it.\nAzhvielle: Delay can be mercy. It can also become a debt. We will have to answer for either choice.",
            ),
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_branoc_joruun",
        "A Promise Freely Kept",
        (
            "Branoc: You call every refusal a test of faith.",
            "Joruun: No. Only the entertaining refusals. The others are tests of patience.",
            "Branoc: Duty is not entertainment.",
            "Joruun: No, duty is usually a table full of unpaid drinks.",
            "Branoc: I took an oath because people needed someone to stay.",
            "Joruun: And I left because people kept deciding my oath for me. A promise chosen freely is harder to break.",
        ),
        (
            StoryChoiceSpec(
                "walk_together",
                "Ask him to walk the watch with you",
                "Branoc: Walk with me, then. No oath. Just this watch.\nJoruun: Gladly. If I find a tavern on patrol, I reserve the right to call it a strategic post.",
            ),
            StoryChoiceSpec(
                "leave_choice",
                "Let him choose whether to stay",
                "Branoc: I will not bind you to a promise you did not make.\nJoruun: That is the first invitation tonight I can accept without checking for a hidden chain.",
            ),
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_branoc_zhaivra",
        "A Stopping Point",
        (
            "Zhaivra: The trace is worth testing. Small sample, one cut, then we stop and compare.",
            "Branoc: Who decides the test has gone far enough?",
            "Zhaivra: I do, if the work risks a person. The evidence decides whether it taught us anything.",
            "Branoc: You hold the tool and judge the cut. That is a lot of trust to place in one hand.",
            "Zhaivra: I know. So I mark the stopping point before I begin.",
        ),
        completion_response=(
            "Branoc: Mark it where everyone can see.\n"
            "Zhaivra: Agreed. An experiment without a stopping point is only damage with better notes."
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_azhvielle_joruun",
        "Prayer And Power",
        (
            "Azhvielle: I can pray. What the covenant prevents is invoking holy magic.",
            "Joruun: People confuse the two whenever it makes their argument easier.",
            "Azhvielle: A prayer is not a spell, and a spell is not proof of devotion.",
            "Joruun: I have met loud believers who were afraid of silence, and quiet ones who never needed an audience.",
        ),
        (
            StoryChoiceSpec(
                "ask_about_faith",
                "Ask what faith means to him",
                "Azhvielle: And what does faith mean when no miracle follows?\nJoruun: The same thing it meant before. Otherwise it was only a wager.",
            ),
            StoryChoiceSpec(
                "leave_prayer_private",
                "Leave the question private",
                "Joruun: Fair. Some prayers are not conversations for an audience.\nAzhvielle: On that, we agree without needing to make a doctrine of it.",
            ),
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_azhvielle_zhaivra",
        "The Boundary Of A Question",
        (
            "Zhaivra: Nhal Voryss still lives within the Hollow Colossus. I am following the traces beneath it because they may explain the First Turning.",
            "Azhvielle: Then you know what it is to have a question large enough to consume every smaller duty.",
            "Zhaivra: I know what it is to want an answer and still measure the cost of reaching it.",
            "Azhvielle: The surviving Vharosynian record bears my name. That makes it personal. It does not make every locked page ours to open.",
        ),
        (
            StoryChoiceSpec(
                "respect_boundary",
                "Respect the boundary around her record",
                "Zhaivra: I will not mistake your name for permission.\nAzhvielle: Thank you. Ambition is not smaller for knowing where to stop.",
            ),
            StoryChoiceSpec(
                "share_question",
                "Share the question, not the page",
                "Zhaivra: I will tell you what the traces say about the First Turning. You may tell me only what you choose about the record.\nAzhvielle: That is a fair exchange. No one has to surrender the key to be useful.",
            ),
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_joruun_zhaivra",
        "One More Step",
        (
            "Zhaivra: One sample. No widening the passage, no second cut, and no touching the pale seam.",
            "Joruun: You have mistaken me for someone who ignores instructions.",
            "Zhaivra: You tried to wager away a map yesterday.",
            "Joruun: I wagered the map would remain a map. I was right; the map is still here.",
            "Zhaivra: Your definition of success is unusually survivable.",
            "Joruun: It is a discipline. Curiosity gets us to the door. Recklessness decides whether we need a new one.",
        ),
        completion_response=(
            "Zhaivra: One sample. I keep the tools.\n"
            "Joruun: And I keep my hands where you can see them. A historic first."
        ),
    ),
    StorySceneSpec(
        "m8_azh_archive_memory",
        "A Name In The Index",
        (
            "Azhvielle: I have spent centuries keeping other people's histories in order. This surviving record bears my name, and I still cannot tell what the writers meant by it.",
            "Azhvielle: Seeing it here makes the past feel less like a shelf and more like a room I never finished leaving.",
            "Azhvielle: The same pages name the Ashen Regent as a threat ahead, not a danger safely buried. We must prepare for it.",
            "Azhvielle: I will not pretend the record tells me everything. I only know that this time, the warning concerns all of us.",
        ),
        completion_response=(
            "Azhvielle: I do not have to settle what the record says about me tonight. I do have to make sure we are ready for the Ashen Regent."
        ),
    ),
    StorySceneSpec(
        "m8_reliquary_echo_scene",
        "An Account From The Reliquary",
        (
            "The report from the two expedition members says that, after both had stopped walking, one more footstep sounded in the flooded passage.",
            "Branoc: If the account is true, we treat the passage as occupied until we know otherwise.",
            "Azhvielle: Or the stone returned a sound. I will not call an echo a ghost because it arrived at a dramatic moment.",
            "Zhaivra: The useful question is whether the sound followed the same interval both times. I want the account, not a third person's theory of it.",
            "Joruun: I would prefer a ghost. It might finally be someone else willing to take watch.",
            "Branoc: You would ask it to take the first watch.",
            "Joruun: Naturally. Curiosity is no excuse to ignore a sensible rota.",
        ),
        completion_response=(
            "No one agrees what the report means. For now, the four of them agree not to mistake a good story for a safe passage."
        ),
    ),
)


_STORY_SCENE_BY_ID = {scene.scene_id: scene for scene in M8_STORY_SCENES}
if len(_STORY_SCENE_BY_ID) != len(M8_STORY_SCENES):
    raise ValueError("M8 story scene IDs must be unique")


def get_story_scene(scene_id):
    if not isinstance(scene_id, str):
        raise TypeError("scene_id must be a string")
    try:
        return _STORY_SCENE_BY_ID[scene_id]
    except KeyError as error:
        raise ValueError(f"unknown story scene ID: {scene_id}") from error


def format_story_scene(scene, *, response=None):
    if not isinstance(scene, StorySceneSpec):
        raise TypeError("scene must be a StorySceneSpec")
    lines = [scene.title, ""]
    lines.extend(scene.dialogue)
    if response is not None:
        if not isinstance(response, str) or not response.strip():
            raise ValueError("response must be nonempty")
        lines.extend(("", response))
    return "\n".join(lines)


__all__ = (
    "M8_PAIR_SCENE_BY_PAIR",
    "M8_STORY_SCENES",
    "StoryChoiceSpec",
    "StorySceneSpec",
    "format_story_scene",
    "get_story_scene",
)
