"""Authored M3 advancement skills and shared tier rules."""

import keyword
import re
from dataclasses import dataclass
from enum import StrEnum

from app.readonly_mapping import readonly_mapping


class AdvancementSkillKind(StrEnum):
    PASSIVE = "passive"
    NORMAL_MOVE = "normal_move"
    MANA_MOVE = "mana_move"
    SUPER = "super"


ADVANCEMENT_DRIFTER_IDS = ("branoc", "azhvielle", "zhaivra", "joruun")
_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _build_slot_rules():
    rules = {}
    for index in range(1, 6):
        rules[f"p{index:02d}"] = (1, 1, AdvancementSkillKind.PASSIVE, 2)
    rules["a01"] = (1, 1, AdvancementSkillKind.NORMAL_MOVE, 3)
    for index in range(6, 10):
        rules[f"p{index:02d}"] = (2, 25, AdvancementSkillKind.PASSIVE, 2)
    rules["a02"] = (2, 25, AdvancementSkillKind.MANA_MOVE, 3)
    for index in range(10, 14):
        rules[f"p{index:02d}"] = (3, 50, AdvancementSkillKind.PASSIVE, 2)
    rules["a03"] = (3, 50, AdvancementSkillKind.MANA_MOVE, 3)
    rules["a04"] = (3, 50, AdvancementSkillKind.SUPER, 3)
    for index in range(14, 18):
        rules[f"p{index:02d}"] = (4, 75, AdvancementSkillKind.PASSIVE, 2)
    rules["a05"] = (4, 75, AdvancementSkillKind.MANA_MOVE, 3)
    rules["p18"] = (5, 100, AdvancementSkillKind.PASSIVE, 2)
    rules["a06"] = (5, 100, AdvancementSkillKind.MANA_MOVE, 3)
    return readonly_mapping(rules)


ADVANCEMENT_SLOT_RULES = _build_slot_rules()


@dataclass(frozen=True)
class AdvancementSkillSpec:
    drifter_id: str
    slot_id: str
    name: str
    purpose: str

    def __post_init__(self):
        for field in ("drifter_id", "slot_id"):
            value = getattr(self, field)
            if not isinstance(value, str):
                raise TypeError(f"{field} must be a string")
            if _ID_PATTERN.fullmatch(value) is None or keyword.iskeyword(value):
                raise ValueError(f"{field} must be a lowercase snake-case ID")
        if self.drifter_id not in ADVANCEMENT_DRIFTER_IDS:
            raise ValueError(f"unknown advancement Drifter: {self.drifter_id!r}")
        if self.slot_id not in ADVANCEMENT_SLOT_RULES:
            raise ValueError(f"unknown advancement slot: {self.slot_id!r}")
        for field in ("name", "purpose"):
            value = getattr(self, field)
            if not isinstance(value, str):
                raise TypeError(f"{field} must be a string")
            if not value.strip():
                raise ValueError(f"{field} must not be empty")

    @property
    def skill_id(self):
        return f"{self.drifter_id}_{self.slot_id}"

    @property
    def tier(self):
        return ADVANCEMENT_SLOT_RULES[self.slot_id][0]

    @property
    def minimum_level(self):
        return ADVANCEMENT_SLOT_RULES[self.slot_id][1]

    @property
    def kind(self):
        return ADVANCEMENT_SLOT_RULES[self.slot_id][2]

    @property
    def gp_cost(self):
        return ADVANCEMENT_SLOT_RULES[self.slot_id][3]


_AUTHORED_SKILL_ROWS = (
    ("branoc", "p01", "Crestcleaver Form", "Strength-led heavy and blade offense; reinforces Sunder-Spire's physical role."),
    ("branoc", "p02", "Deep-Iron Frame", "Constitution-led durability and survival, without turning Constitution into damage."),
    ("branoc", "p03", "Rhom-Ghalian Lung", "Improves sustained use of Branoc's existing resource-consuming techniques."),
    ("branoc", "p04", "Brace of the Exile", "Deepens Brace as his defining defensive setup."),
    ("branoc", "p05", "Hold the Breach", "Frontline protection that rewards staying engaged rather than avoiding attacks."),
    ("branoc", "a01", "Anvil-Line Thrust", "A non-mana, deliberate physical strike that offers a more accurate, lower-commitment alternative to a heavy attack."),
    ("branoc", "p06", "Mountain's Weight", "Stronger Strength-led pressure, distinct from the foundational P1 role."),
    ("branoc", "p07", "Sentinel's Constitution", "Converts Branoc's Constitution investment into a more dependable defensive benefit."),
    ("branoc", "p08", "Breath Between Blows", "Eases resource pressure on an authored Branoc technique; does not create indefinite sustain."),
    ("branoc", "p09", "Brace to Break", "Makes the existing Brace-to-heavy-follow-up sequence more rewarding."),
    ("branoc", "a02", "Gate-Splitting Arc", "A mana technique centered on a crushing Sunder-Spire strike and guard disruption; guard effects require Gate 2 support."),
    ("branoc", "p10", "Crest and Iron", "Links Strength offense with Constitution-based staying power without requiring a split-damage formula."),
    ("branoc", "p11", "Deliberate Tempo", "Rewards a measured heavy-attack sequence or Brace follow-up rather than raw speed."),
    ("branoc", "p12", "Unbroken Guard", "Improves Branoc's ability to absorb physical pressure while preserving the distinction between Brace and Defend."),
    ("branoc", "p13", "Rhom-Ghal's Answer", "A major improvement to the Brace/heavy follow-up identity."),
    ("branoc", "a03", "Sentinel's Reprisal", "A mana technique whose payoff is tied to Branoc's defensive setup and heavy follow-up."),
    ("branoc", "a04", "The Last Crest", "A second Super with a protective frontline purpose, distinct from Third Gate Obsequy; exact party targeting must use supported M3 targeting rules."),
    ("branoc", "p14", "Sunder-Spire Mastery", "High-level mastery of Strength-led heavy and blade techniques."),
    ("branoc", "p15", "Mountain-Born Endurance", "High-level Constitution mastery focused on remaining effective through prolonged pressure."),
    ("branoc", "p16", "Answer the Impact", "Conditional benefit after Branoc successfully absorbs or braces through an enemy action."),
    ("branoc", "p17", "The Sentinel's Measure", "Branoc's strongest ordinary enhancement to the Brace/heavy sequence."),
    ("branoc", "p18", "Unbroken Crest", "Capstone joining Strength, Constitution, and the Heavy Vanguard loop into a transformative defensive-offensive identity."),
    ("branoc", "a05", "Ironwake Reversal", "A control/defense-oriented mana technique that turns a deliberate setup into a response; no new status family is implied."),
    ("branoc", "a06", "Rhom-Ghal's Final Word", "Branoc's endgame mana technique: a decisive Sunder-Spire attack that expresses heavy pressure and earned endurance."),
    ("azhvielle", "p01", "Ninth-Court Formula", "Intelligence-led magical output and disciplined spellcraft."),
    ("azhvielle", "p02", "Deepwell Reservoir", "Spirit-led mana capacity and sustained casting."),
    ("azhvielle", "p03", "Measured Invocation", "Improves the efficiency of Azhvielle's existing mana techniques."),
    ("azhvielle", "p04", "Black-Ice Geometry", "Strengthens the relationship between her frost charges, Frozen, and Frostbite mechanics."),
    ("azhvielle", "p05", "Weight of the Archive", "Improves control or defensive utility around her existing gravity/Arcane mechanics."),
    ("azhvielle", "a01", "Witchlight Bolt", "A non-mana magical attack that gives the caster an Intelligence-led option without spending Mana."),
    ("azhvielle", "p06", "Gravitic Thesis", "Advances Intelligence-led gravity spell output, distinct from P1's general foundation."),
    ("azhvielle", "p07", "Spirit's Continuum", "Makes Spirit investment more useful to her sustained-casting identity."),
    ("azhvielle", "p08", "Economical Hex", "Reduces resource pressure under an authored spell-use condition; it must not create free repeated casting."),
    ("azhvielle", "p09", "Frost and Ruin", "Rewards using frost control before or alongside a gravity/Arcane spell."),
    ("azhvielle", "a02", "Mournglass Lance", "A mana technique built around deliberate frost application and the existing frost-charge loop."),
    ("azhvielle", "p10", "The Ninth-Court Balance", "Rewards combined Intelligence and Spirit investment through spell strength supported by Mana."),
    ("azhvielle", "p11", "Causality's Opening", "Improves tempo when Azhvielle successfully establishes an Arcane or frost setup."),
    ("azhvielle", "p12", "Glass-Mantle Ward", "Caster survival through existing defensive/Arcane interactions, not a universal tank conversion."),
    ("azhvielle", "p13", "Archive of Ruin", "A major upgrade to the frost/gravity spell interaction."),
    ("azhvielle", "a03", "Sepulcher Convergence", "A mana technique combining Intelligence-led gravity with Spirit-supported casting; damage remains one action unless Gate 2 explicitly defines components."),
    ("azhvielle", "a04", "Court Without Dawn", "A second Super focused on decisive frost/Arcane control, distinct from Causality Nullwake's direct erasure fantasy."),
    ("azhvielle", "p14", "Axiom of the Ninth Court", "High-level Intelligence mastery for magical techniques."),
    ("azhvielle", "p15", "Unfathomed Reserve", "High-level Spirit mastery for sustained spell access."),
    ("azhvielle", "p16", "Instability Exploited", "Conditional benefit when Azhvielle capitalizes on her own existing Arcane instability/overcharge interaction."),
    ("azhvielle", "p17", "Gravitic Dominion", "Her strongest ordinary passive improvement to controlled gravity and frost interactions."),
    ("azhvielle", "p18", "The Unconfessed Truth", "Capstone joining deep Mana investment, spell control, and the Ninth-Court identity into a transformative arcane state."),
    ("azhvielle", "a05", "Stillness Beneath the Weight", "A control-oriented mana technique using existing frost or gravity states to deny an enemy's next opportunity; exact status timing is Gate 2."),
    ("azhvielle", "a06", "Ninth-Court Cataclysm", "Azhvielle's final mana technique: a decisive, Intelligence-led spell sustained by Spirit."),
    ("zhaivra", "p01", "Ashvein Sightline", "Dexterity-led bow accuracy and physical output."),
    ("zhaivra", "p02", "Calculated Reaction", "Intuition-led specialized potency, critical interaction, or Super generation."),
    ("zhaivra", "p03", "Six-Reservoir Discipline", "Makes better use of Zhaivra's existing prepared-payload capacity and resource limits."),
    ("zhaivra", "p04", "Compound Timing", "Deepens the existing Infused Barb fire/poison payload loop."),
    ("zhaivra", "p05", "Vanishing Angle", "An avoidance or accuracy utility that supports survival without making Zhaivra a tank."),
    ("zhaivra", "a01", "Needle Through", "A non-mana precision shot with a different accuracy/commitment profile from a basic arrow."),
    ("zhaivra", "p06", "Hollowstring Precision", "Advances Dexterity-led archery and precision pressure beyond P1."),
    ("zhaivra", "p07", "Reagent Intuition", "Strengthens Intuition's specialized effect role in Zhaivra's compound attacks."),
    ("zhaivra", "p08", "Prepared Twice", "Improves resource efficiency around a prepared payload, without duplicating or refunding a consumed payload."),
    ("zhaivra", "p09", "Barb and Bloom", "Rewards applying or exploiting the existing Burn/Poison effects from Infused Barb."),
    ("zhaivra", "a02", "Caustic Thread", "A mana technique centered on a prepared alchemical shot and the existing payload interaction."),
    ("zhaivra", "p10", "Sight and Instinct", "Rewards combined Dexterity precision and Intuition-powered specialized effects."),
    ("zhaivra", "p11", "Second-Window Aim", "Improves tempo after a critical, status application, or successful prepared shot."),
    ("zhaivra", "p12", "Reagent's Evasion", "A defensive benefit tied to precision or avoidance rather than direct damage reduction."),
    ("zhaivra", "p13", "The Compound Sequence", "A major improvement to deliberate setup and payload payoff."),
    ("zhaivra", "a03", "Ashvein Chain Reaction", "A mana technique that exploits an existing Burn/Poison state and prepared-shot timing."),
    ("zhaivra", "a04", "Sixfold Reagent", "A second Super built around a decisive prepared-compound payoff, distinct from Starless Meridian Obsequy."),
    ("zhaivra", "p14", "Sathren's True Line", "High-level Dexterity mastery for bow techniques."),
    ("zhaivra", "p15", "Uncontrolled Reagent", "High-level Intuition mastery for critical and specialized compound effects."),
    ("zhaivra", "p16", "Volatile Opening", "Conditional benefit when attacking a target already carrying one of Zhaivra's authored statuses."),
    ("zhaivra", "p17", "Colossus-Reader", "Her strongest ordinary passive enhancement to precision-plus-payload sequencing."),
    ("zhaivra", "p18", "The Perfect Reaction", "Capstone combining Dexterity, Intuition, and a prepared compound sequence into a defining marksman payoff."),
    ("zhaivra", "a05", "Deadfall Compound", "A control-oriented mana technique that uses the existing Burn/Poison vocabulary to create a tactical opening."),
    ("zhaivra", "a06", "Hollow Colossus Verdict", "Zhaivra's final mana technique: a high-precision, compound-aware finishing shot."),
    ("joruun", "p01", "Single-Current Channel", "Intelligence-led elemental and magical output."),
    ("joruun", "p02", "Staff-Wind Footwork", "Dexterity-led physical staff technique, accuracy, or avoidance."),
    ("joruun", "p03", "Breath Between Forms", "Improves sustainable use of Joruun's existing Mana techniques without removing their physical cost."),
    ("joruun", "p04", "Conductive Sequence", "Deepens the existing Conductive/Turbulence-to-Lightning interaction."),
    ("joruun", "p05", "Unfixed Stance", "Improves Joruun's agile defensive utility while preserving his skirmisher identity."),
    ("joruun", "a01", "Reed-Cut Staff", "A non-mana physical staff technique with a distinct precision/commitment profile."),
    ("joruun", "p06", "Storm-Caller", "Advances Intelligence-led elemental technique output beyond P1."),
    ("joruun", "p07", "Balanced Step", "Makes Dexterity investment useful to physical staff attacks and agile defense."),
    ("joruun", "p08", "Thrifty Current", "Reduces resource pressure under a supported elemental/setup condition; no infinite sustain."),
    ("joruun", "p09", "Rain Before Thunder", "Rewards sequencing Hydro Whip or Tempest Surge into Lightning Palm."),
    ("joruun", "a02", "Gale-Split Current", "A mana technique expressing Intelligence-led storm force through Joruun's elemental form."),
    ("joruun", "p10", "Mind and Motion", "Rewards combined Intelligence spell force and Dexterity physical technique."),
    ("joruun", "p11", "Turn of the Current", "Improves tempo when Joruun changes the tactical state through an existing elemental setup."),
    ("joruun", "p12", "Water-Bound Balance", "A defensive/sustain option tied to the existing water-control identity."),
    ("joruun", "p13", "Law of One Current", "A major upgrade to Joruun's Conductive/Turbulence setup and lightning payoff."),
    ("joruun", "a03", "Thunder Through the Staff", "A mana technique linking physical staff form to Intelligence-led elemental power."),
    ("joruun", "a04", "Three Currents, One Sky", "A second Super with an elemental-form payoff distinct from Coagulated Torrent's finishing surge."),
    ("joruun", "p14", "Sky-Needle Mastery", "High-level Intelligence mastery for elemental and magical techniques."),
    ("joruun", "p15", "Unerring Step", "High-level Dexterity mastery for physical staff technique and agile positioning."),
    ("joruun", "p16", "Storm's Invitation", "Conditional benefit after Joruun establishes Conductive or Turbulence."),
    ("joruun", "p17", "The Hollow Gale Form", "His strongest ordinary passive improvement to elemental setup and physical/magical transition."),
    ("joruun", "p18", "Bloody Storm", "Capstone joining Intelligence, Dexterity, and the Law of the Single Current into a transformative storm sequence."),
    ("joruun", "a05", "Floodgate Turn", "A control/utility mana technique built around Hydro Whip's existing Conductive setup."),
    ("joruun", "a06", "Horizon-Breaking Torrent", "Joruun's final mana technique: a decisive elemental strike that pays off established storm setup."),
)


def build_advancement_catalog(records, *, drifter_ids=ADVANCEMENT_DRIFTER_IDS):
    by_id = {}
    drifter_ids = tuple(drifter_ids)
    if len(drifter_ids) != len(set(drifter_ids)):
        raise ValueError("advancement Drifter IDs must be unique")
    by_drifter = {drifter_id: {} for drifter_id in drifter_ids}
    for spec in records:
        if not isinstance(spec, AdvancementSkillSpec):
            raise TypeError("advancement catalog records must be AdvancementSkillSpec values")
        if spec.drifter_id not in by_drifter:
            raise ValueError(f"advancement references unknown Drifter: {spec.drifter_id!r}")
        if spec.skill_id in by_id:
            raise ValueError(f"duplicate advancement skill ID: {spec.skill_id}")
        by_id[spec.skill_id] = spec
        by_drifter[spec.drifter_id][spec.slot_id] = spec

    expected_slots = set(ADVANCEMENT_SLOT_RULES)
    for drifter_id, skills in by_drifter.items():
        if set(skills) != expected_slots:
            raise ValueError(
                f"Drifter {drifter_id!r} must define each advancement slot exactly once"
            )
    ordered = tuple(by_id.values())
    return ordered, readonly_mapping(by_id), readonly_mapping(
        {drifter_id: readonly_mapping(skills) for drifter_id, skills in by_drifter.items()}
    )


ADVANCEMENT_SKILLS, _SKILLS_BY_ID, _SKILLS_BY_DRIFTER = build_advancement_catalog(
    tuple(AdvancementSkillSpec(*row) for row in _AUTHORED_SKILL_ROWS)
)


def get_advancement_skill(skill_id):
    try:
        return _SKILLS_BY_ID[skill_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"unknown advancement skill: {skill_id}") from error


def get_drifter_advancement_skills(drifter_id):
    try:
        skills = _SKILLS_BY_DRIFTER[drifter_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"unknown advancement Drifter: {drifter_id}") from error
    return tuple(skills[slot_id] for slot_id in ADVANCEMENT_SLOT_RULES)


__all__ = [
    "ADVANCEMENT_DRIFTER_IDS",
    "ADVANCEMENT_SKILLS",
    "ADVANCEMENT_SLOT_RULES",
    "AdvancementSkillKind",
    "AdvancementSkillSpec",
    "build_advancement_catalog",
    "get_advancement_skill",
    "get_drifter_advancement_skills",
]
