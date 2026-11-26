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
            "Azhvielle studies a worn line on the stone. Branoc watches the passage.",
            "Azhvielle: This inscription is a warning about the record below it.",
            "Branoc: Can you read the record?",
            "Azhvielle: Yes. That doesn’t mean I should.",
            "Branoc: If it could endanger us, say so.",
            "Azhvielle: It could endanger anyone who mistakes knowledge for permission. The trouble is that people usually ask for the knowledge first and consider responsibility later.",
            "Branoc: That is why I ask what it costs before I give an order.",
            "Azhvielle: And if the cost is paid by people who never heard the order?",
            "Branoc: Then I have failed them.",
            "Azhvielle: You make responsibility sound simple.",
            "Branoc: No. I make it mine.",
        ),
        (
            StoryChoiceSpec(
                "share_warning",
                "Read only the warning",
                "Azhvielle: The warning says the reader answers for what follows.\nBranoc: Then we decide what to do with it before we ask for more.\nAzhvielle: That is more care than most people bring to a book.",
            ),
            StoryChoiceSpec(
                "leave_closed",
                "Leave the record closed",
                "Branoc: We have no cause to use what we don’t understand.\nAzhvielle: You don’t have to defend not knowing.\nBranoc: I do if someone else would pay for my curiosity.\nAzhvielle: Then at least we agree on whose burden it is.",
            ),
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_branoc_joruun",
        "A Promise Freely Kept",
        (
            "Branoc has taken the seat facing the passage. Joruun dries his spectacles.",
            "Joruun: You still take the entrance-facing seat.",
            "Branoc: It’s the useful seat.",
            "Joruun: Of course. No one ever calls it guilt when it comes with excellent posture.",
            "Branoc: You’ve mistaken a habit for a confession.",
            "Joruun: I’ve made a career of mistakes people reward.",
            "Branoc: I surrendered my rank so my soldiers could return to their lives.",
            "Joruun: And if they had chosen to follow you anyway?",
            "Branoc: Then I should have let them choose.",
            "Joruun: You say that as if freedom were a safer road.",
            "Branoc: No. Only theirs.",
            "Joruun: I’ve made a living leaving before anyone can order me home. It’s less noble than your version.",
            "Branoc: Is it freedom if you never stay long enough to be asked?",
            "Joruun: That is an irritating question for a man who chose exile.",
            "Branoc: I know.",
        ),
        (
            StoryChoiceSpec(
                "joruun_returning",
                "Hear Joruun speak about returning",
                "Joruun: If I ever go back, it will be because I want to—not because a village, a temple, or a pretty face tells me I owe it.\nBranoc: And if you wanted to stay?\nJoruun: Then I’d have to learn what to do the morning after.",
            ),
            StoryChoiceSpec(
                "branoc_choice",
                "Hear Branoc speak about his choice",
                "Branoc: I don’t know whether I would make the same choice again. Knowing the cost would not make it simple.\nJoruun: Good. I was beginning to worry you’d turned regret into another duty.\nBranoc: I haven’t.",
            ),
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_branoc_zhaivra",
        "A Stopping Point",
        (
            "Zhaivra has found a way to test how the current moves around the ledge. Branoc notices that she intends to get closer to the water.",
            "Branoc: Don’t put your hand in.",
            "Zhaivra: I wasn’t going to. I was going to learn something.",
            "Branoc: By putting yourself where the current can take you.",
            "Zhaivra: A small test can prevent a larger mistake.",
            "Branoc: And a small test can become somebody else’s rescue.",
            "Zhaivra: You think control is the same as safety.",
            "Branoc: No. I think asking others to pay for my risk is a failure of control.",
            "Zhaivra: This is not a whim.",
            "Branoc: I know. That is why I’m asking you to wait until we can do it safely.",
            "Zhaivra: You’re asking, then.",
            "Branoc: I’m trying to learn the difference.",
        ),
        completion_response=(
            "Zhaivra puts the test aside for now.\n"
            "Zhaivra: When I do it, you can stand where you can keep me from being swept away. Not where you can stop me from learning.\n"
            "Branoc: I’ll try to tell the difference.\n"
            "Zhaivra: That will do."
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_azhvielle_joruun",
        "Prayer And Power",
        (
            "Joruun: You say sorcery always takes a price. What does faith take?",
            "Azhvielle: Sometimes it takes the cost and hands it to someone who cannot object.",
            "Joruun: And sorcery?",
            "Azhvielle: Gives you the bill before you choose. Then may send another bill somewhere you cannot see.",
            "Joruun: I’ve seen things I cannot explain happen after my prayers. I don’t know whether the prayer caused them. I know I prayed because someone was afraid.",
            "Azhvielle: That is not a claim of divine power.",
            "Joruun: No. It is a reason I still pray.",
            "Azhvielle: I cannot invoke holy magic. The covenant in my soul rejects it.",
            "Joruun: I didn’t ask you to cast anything.",
            "Azhvielle: Don’t make an invitation out of a wound.",
            "Joruun: Fair. I’ll ask a different question.",
        ),
        (
            StoryChoiceSpec(
                "ask_about_faith",
                "Hear Joruun answer whether he would pray without a miracle",
                "Joruun: Yes, if it helped a frightened person feel less alone. For myself? I’m still working that out.\nAzhvielle: That is a more honest answer than most priests give.\nJoruun: I charge less, too.",
            ),
            StoryChoiceSpec(
                "leave_prayer_private",
                "Hear Azhvielle answer whether sorcery comforts her more than faith",
                "Azhvielle: No. Sorcery only lets me pretend I can account for the cost. That is not comfort. It is the burden I know how to carry.\nJoruun: I thought you might say that.\nAzhvielle: Then why ask?\nJoruun: Because being right about someone is not the same as understanding them.",
            ),
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_azhvielle_zhaivra",
        "The Boundary Of A Question",
        (
            "Zhaivra: If this trace really resembles the Hollow Colossus, it could change everything I know about Nhal Voryss.",
            "Azhvielle: Is that what you want?",
            "Zhaivra: I want the truth.",
            "Azhvielle: People often say that when they mean they want the answer that will let them act.",
            "Zhaivra: And people call knowledge forbidden when they’re afraid of what someone else might do with it.",
            "Azhvielle: Both can be true.",
            "Zhaivra: Then I want the right to choose after I know.",
            "Azhvielle: I understand. I once believed that learning a thing made me responsible enough to use it. It did not.",
            "Zhaivra: Did you stop looking?",
            "Azhvielle: No. I learned to ask who else would pay for the answer.",
            "Zhaivra: That isn’t a reason to stop.",
            "Azhvielle: No. It is a reason to be certain the question is yours to ask.",
        ),
        (
            StoryChoiceSpec(
                "respect_boundary",
                "Hear Zhaivra speak about what she hopes to learn",
                "Zhaivra: Whether the First Turning can be undone—or whether my people have misunderstood what the Colossus is. Either answer could change what Nhal Voryss must do next. I still need to know.\nAzhvielle: I won’t call that foolish.\nZhaivra: Good. I would have ignored you.",
            ),
            StoryChoiceSpec(
                "share_question",
                "Hear Azhvielle speak about her own ambition",
                "Azhvielle: I have watched my name appear in histories that cannot all be true. Once, I thought correcting them would settle the matter. It only gave people a new version to argue over.\nZhaivra: And now?\nAzhvielle: Now I try to notice when my need to know has become a need to be right.",
            ),
        ),
    ),
    StorySceneSpec(
        "m8_pair_scene_joruun_zhaivra",
        "One More Step",
        (
            "Zhaivra watches dust drift along the ledge. Joruun leans just far enough to feel the air change.",
            "Zhaivra: You’re testing the current.",
            "Joruun: I’m letting it introduce itself.",
            "Zhaivra: It’s a draft.",
            "Joruun: You say that as though drafts have never ruined a good plan.",
            "Zhaivra: I have six arrow reservoirs and no plan that requires you to put your face in the water.",
            "Joruun: I was testing the air.",
            "Zhaivra: You were about to test the water with your face.",
            "Joruun: That was a later stage.",
            "Zhaivra: There is no later stage.",
            "Joruun: Your caution is very bad for discovery.",
            "Zhaivra: Your curiosity is very bad for staying dry.",
            "Joruun: Yet you did notice the current changed.",
            "Zhaivra: Because you leaned in.",
            "Joruun: So we both contributed.",
            "Zhaivra: Don’t make this sound like teamwork.",
        ),
        completion_response=(
            "Joruun: Too late. I’m already proud of us."
        ),
    ),
    StorySceneSpec(
        "m8_azh_archive_memory",
        "A Name In The Index",
        (
            "Azhvielle recognizes a catalog mark. She says nothing for a moment.",
            "Azhvielle: I remember writing that mark.",
            "Azhvielle: I was an archivist. A name appeared in a record. Later, it was absent from the copy others could read. I was told that was to protect the living. I have never learned whether I made that choice, or whether I only learned to live with it.",
            "She reads the adjacent entry.",
            "Azhvielle: Ashen Regent. This is recorded as a current office, not a dead ruler’s title. Someone still holds authority in the Ashen Vault.",
            "Azhvielle: That is the part I can tell you with certainty. The rest is what I have carried as a question.",
        ),
        (
            StoryChoiceSpec(
                "ask_about_missing_name",
                "Ask what she remembers about the name",
                "Azhvielle: The court feared what people might do with that name. Someone must have believed silence would contain the danger. I cannot tell you whether I was part of that choice or only taught to accept it. Either way, someone else was left to live with the cost.",
            ),
            StoryChoiceSpec(
                "ask_party_plan",
                "Ask what the party should do now",
                "Azhvielle: Carry the warning, not a verdict about me. The Regent is a present threat. We should bring all four of us when we face it, and not pretend I know its methods.",
            ),
        ),
    ),
    StorySceneSpec(
        "m8_reliquary_echo_scene",
        "An Account From The Reliquary",
        (
            "The report from the two expedition members says that, after both had stopped walking, one more footstep sounded in the flooded passage.",
            "The report does not identify which pair heard the footstep. At the Hub, all four Drifters discuss what the account could mean.",
            "Branoc: My answer to the report is to face the passage. Not because I know someone was there. Because no one gets left behind.",
            "Zhaivra: The temptation would be to go back and test the wall. But no measurement is worth leaving a partner alone in that chamber.",
            "Joruun: I could have called it a fifth traveler. It would have made a fine sermon.",
            "Azhvielle: And what would have stopped you?",
            "Joruun: The report says they were frightened. I wouldn’t sell them a ghost.",
            "Azhvielle: Good.",
            "Joruun: Don’t sound so surprised.",
            "Azhvielle: I’m not. I’m relieved.",
            "There is a pause.",
            "Branoc: We can leave the account unexplained without leaving one another there.",
            "Zhaivra: I still want to know what caused it.",
            "Joruun: I still want to know whether the fifth traveler tips.",
            "Azhvielle: And I still don’t know who I would have blamed if the report had described a voice.",
            "Branoc: Then we have our answer for tonight.",
        ),
        completion_response=(
            "Azhvielle: No. We have each other’s answers."
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
