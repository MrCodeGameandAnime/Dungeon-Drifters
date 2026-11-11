"""Authored combat projections for purchased M3 advancement skills."""

from app.combat.frost import FROST_ATTACK_MECHANIC
from app.combat.infused_barb import INFUSED_BARB_MECHANIC
from app.combat.move import (
    DamageComponent,
    DamageComponentIdentity,
    DamageDefenseClass,
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.combat.move_presentation import MovePresentation, MoveRole
from app.combat.passive_effect import (
    PassiveCombatEffect,
    PassiveEffectCondition as Condition,
    PassiveEffectKind as Kind,
)
from app.combat.storm import (
    HYDRO_WHIP_MECHANIC,
    LIGHTNING_PALM_MECHANIC,
    TEMPEST_SURGE_MECHANIC,
)
from app.content.advancement_spec import (
    ADVANCEMENT_SKILLS,
    AdvancementSkillKind,
    get_advancement_skill,
)
from app.readonly_mapping import readonly_mapping


def _component(identity, defense, power, scaling, subtype=None):
    return DamageComponent(
        identity=identity,
        defense_class=defense,
        power=power,
        scales_with=scaling,
        subtype=subtype,
    )


def _skill_move(
    name,
    *,
    power,
    scaling,
    accuracy,
    resource=ResourceType.NONE,
    cost=0,
    damage=DamageType.PHYSICAL,
    mechanic=None,
    components=(),
    is_spell=False,
    frost_backlash=False,
    role=MoveRole.NORMAL,
    target=TargetType.ENEMY,
    description,
):
    return Move(
        name=name,
        kind=MoveKind.UTILITY if role is MoveRole.UTILITY else MoveKind.DAMAGE,
        resource_type=resource,
        resource_cost=cost,
        power=power,
        scales_with=scaling,
        accuracy=accuracy,
        target=target,
        damage_type=DamageType.NONE if components else damage,
        mechanic=mechanic,
        description=description,
        presentation=MovePresentation(role=role),
        is_spell=is_spell,
        frost_backlash=frost_backlash,
        damage_components=components,
    )


_ACTIVE_MOVES = {
    "branoc_a01": _skill_move(
        "Anvil-Line Thrust", power=10, scaling=(ScalingAttribute.STRENGTH,),
        accuracy=96, description="A measured Sunder-Spire thrust with a sure line."
    ),
    "branoc_a02": _skill_move(
        "Gate-Splitting Arc", power=24, scaling=(ScalingAttribute.STRENGTH,),
        accuracy=88, resource=ResourceType.MANA, cost=6,
        mechanic="heavy_attack", role=MoveRole.HEAVY,
        description="A crushing Sunder-Spire arc driven through the target."
    ),
    "branoc_a03": _skill_move(
        "Sentinel's Reprisal", power=22, scaling=(ScalingAttribute.STRENGTH,),
        accuracy=90, resource=ResourceType.MANA, cost=7,
        mechanic="heavy_attack", role=MoveRole.HEAVY,
        description="A deliberate heavy answer, especially potent after Brace."
    ),
    "branoc_a04": _skill_move(
        "The Last Crest", power=0, scaling=(ScalingAttribute.NONE,),
        accuracy=100, resource=ResourceType.SUPER, cost=100,
        damage=DamageType.NONE, mechanic="brace", role=MoveRole.UTILITY,
        target=TargetType.SELF,
        description="Spend the Super to brace behind Sunder-Spire for the next attack."
    ),
    "branoc_a05": _skill_move(
        "Ironwake Reversal", power=25, scaling=(ScalingAttribute.STRENGTH,),
        accuracy=90, resource=ResourceType.MANA, cost=8,
        mechanic="heavy_attack", role=MoveRole.HEAVY,
        description="Turn a prepared defense into a forceful Ironwake strike."
    ),
    "branoc_a06": _skill_move(
        "Rhom-Ghal's Final Word", power=34,
        scaling=(ScalingAttribute.STRENGTH,), accuracy=86,
        resource=ResourceType.MANA, cost=10, mechanic="heavy_attack",
        role=MoveRole.HEAVY,
        description="A decisive, full-weight Sunder-Spire blow."
    ),
    "azhvielle_a01": _skill_move(
        "Witchlight Bolt", power=12, scaling=(ScalingAttribute.INTELLIGENCE,),
        accuracy=96, damage=DamageType.NONE, is_spell=True,
        components=(_component(
            DamageComponentIdentity.ELEMENTAL, DamageDefenseClass.MAGICAL,
            12, (ScalingAttribute.INTELLIGENCE,), "fire",
        ),),
        description="A precise bolt of witchlight shaped by focused spellcraft."
    ),
    "azhvielle_a02": _skill_move(
        "Mournglass Lance", power=22, scaling=(ScalingAttribute.INTELLIGENCE,),
        accuracy=90, resource=ResourceType.MANA, cost=6,
        damage=DamageType.NONE, mechanic=FROST_ATTACK_MECHANIC,
        is_spell=True,
        components=(_component(
            DamageComponentIdentity.ELEMENTAL, DamageDefenseClass.MAGICAL,
            22, (ScalingAttribute.INTELLIGENCE,), "cold",
        ),),
        description="A narrow lance of black frost that advances the frost-charge loop."
    ),
    "azhvielle_a03": _skill_move(
        "Sepulcher Convergence", power=26,
        scaling=(ScalingAttribute.INTELLIGENCE,), accuracy=84,
        resource=ResourceType.MANA, cost=9, damage=DamageType.NONE,
        mechanic="gravemantle_rupture", is_spell=True,
        components=(_component(
            DamageComponentIdentity.MAGICAL, DamageDefenseClass.MAGICAL,
            26, (ScalingAttribute.INTELLIGENCE,),
        ),),
        description="A gravity spell that opens Azhvielle's existing Gravemantle state."
    ),
    "azhvielle_a04": _skill_move(
        "Court Without Dawn", power=32,
        scaling=(ScalingAttribute.INTELLIGENCE,), accuracy=100,
        resource=ResourceType.SUPER, cost=100, damage=DamageType.NONE,
        mechanic=FROST_ATTACK_MECHANIC, is_spell=True, role=MoveRole.SUPER,
        components=(_component(
            DamageComponentIdentity.ELEMENTAL, DamageDefenseClass.MAGICAL,
            32, (ScalingAttribute.INTELLIGENCE,), "cold",
        ),),
        description="A Super of black frost that drives the target toward Frozen."
    ),
    "azhvielle_a05": _skill_move(
        "Stillness Beneath the Weight", power=23,
        scaling=(ScalingAttribute.INTELLIGENCE,), accuracy=94,
        resource=ResourceType.MANA, cost=8, damage=DamageType.NONE,
        mechanic=FROST_ATTACK_MECHANIC, is_spell=True,
        components=(_component(
            DamageComponentIdentity.ELEMENTAL, DamageDefenseClass.MAGICAL,
            23, (ScalingAttribute.INTELLIGENCE,), "cold",
        ),),
        description="A controlled frost spell that builds toward denying an enemy action."
    ),
    "azhvielle_a06": _skill_move(
        "Ninth-Court Cataclysm", power=37,
        scaling=(ScalingAttribute.INTELLIGENCE,), accuracy=88,
        resource=ResourceType.MANA, cost=12, damage=DamageType.NONE,
        is_spell=True,
        components=(_component(
            DamageComponentIdentity.MAGICAL, DamageDefenseClass.MAGICAL,
            37, (ScalingAttribute.INTELLIGENCE,),
        ),),
        description="A decisive Ninth-Court spell sustained by Azhvielle's reserve."
    ),
    "zhaivra_a01": _skill_move(
        "Needle Through", power=12, scaling=(ScalingAttribute.DEXTERITY,),
        accuracy=100, damage=DamageType.PHYSICAL,
        description="A single, exact Sathren shot with little wasted motion."
    ),
    "zhaivra_a02": _skill_move(
        "Caustic Thread", power=22,
        scaling=(ScalingAttribute.DEXTERITY,), accuracy=90,
        resource=ResourceType.MANA, cost=5, damage=DamageType.NONE,
        mechanic=INFUSED_BARB_MECHANIC,
        components=(
            _component(
                DamageComponentIdentity.PHYSICAL, DamageDefenseClass.PHYSICAL,
                16, (ScalingAttribute.DEXTERITY,),
            ),
            _component(
                DamageComponentIdentity.ALCHEMICAL, DamageDefenseClass.MAGICAL,
                6, (ScalingAttribute.NONE,), "prepared_payload",
            ),
        ),
        description="A precise arrow carrying Zhaivra's prepared fire or poison payload."
    ),
    "zhaivra_a03": _skill_move(
        "Ashvein Chain Reaction", power=25,
        scaling=(ScalingAttribute.DEXTERITY,), accuracy=88,
        resource=ResourceType.MANA, cost=7, damage=DamageType.NONE,
        mechanic=INFUSED_BARB_MECHANIC,
        components=(
            _component(
                DamageComponentIdentity.PHYSICAL, DamageDefenseClass.PHYSICAL,
                18, (ScalingAttribute.DEXTERITY,),
            ),
            _component(
                DamageComponentIdentity.ALCHEMICAL, DamageDefenseClass.MAGICAL,
                7, (ScalingAttribute.NONE,), "prepared_payload",
            ),
        ),
        description="A compound shot that reapplies a prepared payload on a living target."
    ),
    "zhaivra_a04": _skill_move(
        "Sixfold Reagent", power=34,
        scaling=(ScalingAttribute.DEXTERITY,), accuracy=100,
        resource=ResourceType.SUPER, cost=100, damage=DamageType.NONE,
        mechanic=INFUSED_BARB_MECHANIC, role=MoveRole.SUPER,
        components=(
            _component(
                DamageComponentIdentity.PHYSICAL, DamageDefenseClass.PHYSICAL,
                25, (ScalingAttribute.DEXTERITY,),
            ),
            _component(
                DamageComponentIdentity.ALCHEMICAL, DamageDefenseClass.MAGICAL,
                9, (ScalingAttribute.NONE,), "prepared_payload",
            ),
        ),
        description="A prepared compound Super delivered through one perfect arrow."
    ),
    "zhaivra_a05": _skill_move(
        "Deadfall Compound", power=27,
        scaling=(ScalingAttribute.DEXTERITY,), accuracy=94,
        resource=ResourceType.MANA, cost=8, damage=DamageType.NONE,
        mechanic=INFUSED_BARB_MECHANIC,
        components=(
            _component(
                DamageComponentIdentity.PHYSICAL, DamageDefenseClass.PHYSICAL,
                20, (ScalingAttribute.DEXTERITY,),
            ),
            _component(
                DamageComponentIdentity.ALCHEMICAL, DamageDefenseClass.MAGICAL,
                7, (ScalingAttribute.NONE,), "prepared_payload",
            ),
        ),
        description="A controlled compound shot that commits a prepared payload."
    ),
    "zhaivra_a06": _skill_move(
        "Hollow Colossus Verdict", power=37,
        scaling=(ScalingAttribute.DEXTERITY,), accuracy=96,
        resource=ResourceType.MANA, cost=12, damage=DamageType.NONE,
        mechanic=INFUSED_BARB_MECHANIC,
        components=(
            _component(
                DamageComponentIdentity.PHYSICAL, DamageDefenseClass.PHYSICAL,
                28, (ScalingAttribute.DEXTERITY,),
            ),
            _component(
                DamageComponentIdentity.ALCHEMICAL, DamageDefenseClass.MAGICAL,
                9, (ScalingAttribute.NONE,), "prepared_payload",
            ),
        ),
        description="A high-precision finishing arrow with a prepared compound payload."
    ),
    "joruun_a01": _skill_move(
        "Reed-Cut Staff", power=13, scaling=(ScalingAttribute.DEXTERITY,),
        accuracy=96, damage=DamageType.PHYSICAL,
        description="A clean Sky-Needle staff strike delivered on a precise line."
    ),
    "joruun_a02": _skill_move(
        "Gale-Split Current", power=24,
        scaling=(ScalingAttribute.INTELLIGENCE,), accuracy=90,
        resource=ResourceType.MANA, cost=5, damage=DamageType.NONE,
        mechanic=TEMPEST_SURGE_MECHANIC,
        components=(_component(
            DamageComponentIdentity.ELEMENTAL, DamageDefenseClass.MAGICAL,
            24, (ScalingAttribute.INTELLIGENCE,), "wind",
        ),),
        description="An elemental gale that establishes Joruun's existing Turbulence."
    ),
    "joruun_a03": _skill_move(
        "Thunder Through the Staff", power=28,
        scaling=(ScalingAttribute.DEXTERITY, ScalingAttribute.INTELLIGENCE),
        accuracy=84, resource=ResourceType.MANA, cost=7, damage=DamageType.NONE,
        mechanic=LIGHTNING_PALM_MECHANIC,
        components=(
            _component(
                DamageComponentIdentity.PHYSICAL, DamageDefenseClass.PHYSICAL,
                14, (ScalingAttribute.DEXTERITY,),
            ),
            _component(
                DamageComponentIdentity.ELEMENTAL, DamageDefenseClass.MAGICAL,
                14, (ScalingAttribute.INTELLIGENCE,), "lightning",
            ),
        ),
        description="A staff-and-lightning strike that consumes Joruun's storm setup."
    ),
    "joruun_a04": _skill_move(
        "Three Currents, One Sky", power=38,
        scaling=(ScalingAttribute.DEXTERITY, ScalingAttribute.INTELLIGENCE),
        accuracy=100, resource=ResourceType.SUPER, cost=100,
        damage=DamageType.NONE, mechanic=LIGHTNING_PALM_MECHANIC,
        role=MoveRole.SUPER,
        components=(
            _component(
                DamageComponentIdentity.PHYSICAL, DamageDefenseClass.PHYSICAL,
                19, (ScalingAttribute.DEXTERITY,),
            ),
            _component(
                DamageComponentIdentity.ELEMENTAL, DamageDefenseClass.MAGICAL,
                19, (ScalingAttribute.INTELLIGENCE,), "lightning",
            ),
        ),
        description="A Super joining staff, lightning, and the existing storm payoff."
    ),
    "joruun_a05": _skill_move(
        "Floodgate Turn", power=24,
        scaling=(ScalingAttribute.INTELLIGENCE,), accuracy=92,
        resource=ResourceType.MANA, cost=6, damage=DamageType.NONE,
        mechanic=HYDRO_WHIP_MECHANIC,
        components=(_component(
            DamageComponentIdentity.ELEMENTAL, DamageDefenseClass.MAGICAL,
            24, (ScalingAttribute.INTELLIGENCE,), "water",
        ),),
        description="A water-form technique that establishes Conductive."
    ),
    "joruun_a06": _skill_move(
        "Horizon-Breaking Torrent", power=38,
        scaling=(ScalingAttribute.INTELLIGENCE,), accuracy=90,
        resource=ResourceType.MANA, cost=11, damage=DamageType.NONE,
        mechanic=TEMPEST_SURGE_MECHANIC,
        components=(_component(
            DamageComponentIdentity.ELEMENTAL, DamageDefenseClass.MAGICAL,
            38, (ScalingAttribute.INTELLIGENCE,), "lightning",
        ),),
        description="A final storm technique that leaves the target in Turbulence."
    ),
}


def _effect(kind, value, *, damage_class=None, mechanic=None,
            condition=Condition.ALWAYS, statuses=(), uses_intuition=False):
    return PassiveCombatEffect(
        kind=kind,
        value=value,
        damage_class=damage_class,
        mechanic=mechanic,
        condition=condition,
        target_statuses=statuses,
        uses_intuition=uses_intuition,
    )


P = Kind.DAMAGE_OUTPUT
M = Kind.MITIGATION
A = Kind.ACCURACY
D = Kind.DODGE
C = Kind.CRITICAL
MC = Kind.MANA_COST
SG = Kind.SUPER_GAIN
SP = Kind.STATUS_POTENCY
BI = Kind.BRACE_INCOMING
BF = Kind.BRACE_FOLLOW_UP
PHYS = DamageDefenseClass.PHYSICAL
MAG = DamageDefenseClass.MAGICAL

_PASSIVE_EFFECTS = {
    "branoc_p01": (_effect(P, 5, damage_class=PHYS),),
    "branoc_p02": (_effect(M, 1, damage_class=PHYS),),
    "branoc_p03": (_effect(MC, 1),),
    "branoc_p04": (_effect(BI, 8),),
    "branoc_p05": (_effect(M, 1, damage_class=PHYS),),
    "branoc_p06": (_effect(P, 4, damage_class=PHYS),),
    "branoc_p07": (_effect(M, 2, damage_class=PHYS),),
    "branoc_p08": (_effect(MC, 1, mechanic="brace"),),
    "branoc_p09": (_effect(BF, 10),),
    "branoc_p10": (_effect(P, 3, damage_class=PHYS, condition=Condition.HIGH_HEALTH),),
    "branoc_p11": (_effect(SG, 10, mechanic="heavy_attack"),),
    "branoc_p12": (_effect(M, 2, damage_class=PHYS),),
    "branoc_p13": (_effect(BF, 15),),
    "branoc_p14": (_effect(P, 5, damage_class=PHYS),),
    "branoc_p15": (_effect(M, 3, damage_class=PHYS),),
    "branoc_p16": (_effect(BF, 10, condition=Condition.BRACE_READY),),
    "branoc_p17": (_effect(BF, 20),),
    "branoc_p18": (
        _effect(P, 7, damage_class=PHYS, condition=Condition.LOW_HEALTH),
        _effect(BF, 10),
    ),
    "azhvielle_p01": (_effect(P, 5, damage_class=MAG),),
    "azhvielle_p02": (_effect(MC, 1),),
    "azhvielle_p03": (_effect(MC, 1, mechanic="gravemantle_rupture"),),
    "azhvielle_p04": (_effect(P, 4, damage_class=MAG, mechanic=FROST_ATTACK_MECHANIC),),
    "azhvielle_p05": (_effect(M, 1, damage_class=MAG),),
    "azhvielle_p06": (_effect(P, 4, damage_class=MAG),),
    "azhvielle_p07": (_effect(MC, 1, condition=Condition.LOW_MANA),),
    "azhvielle_p08": (_effect(MC, 1, condition=Condition.ARCANE_OVERCHARGE),),
    "azhvielle_p09": (_effect(P, 3, damage_class=MAG, condition=Condition.OWN_FROST),),
    "azhvielle_p10": (_effect(P, 3, damage_class=MAG, condition=Condition.HIGH_MANA),),
    "azhvielle_p11": (_effect(SG, 10, condition=Condition.ARCANE_OVERCHARGE),),
    "azhvielle_p12": (_effect(M, 2, damage_class=MAG),),
    "azhvielle_p13": (_effect(P, 5, damage_class=MAG, condition=Condition.OWN_FROST),),
    "azhvielle_p14": (_effect(P, 5, damage_class=MAG),),
    "azhvielle_p15": (_effect(MC, 1, mechanic="frost_attack"),),
    "azhvielle_p16": (_effect(P, 4, damage_class=MAG, condition=Condition.ARCANE_OVERCHARGE),),
    "azhvielle_p17": (_effect(P, 6, damage_class=MAG, condition=Condition.OWN_FROST),),
    "azhvielle_p18": (_effect(P, 8, damage_class=MAG, condition=Condition.ARCANE_OVERCHARGE),),
    "zhaivra_p01": (
        _effect(P, 3, damage_class=PHYS),
        _effect(A, 2),
    ),
    "zhaivra_p02": (
        _effect(C, 2),
        _effect(SP, 0, mechanic=INFUSED_BARB_MECHANIC, uses_intuition=True),
    ),
    "zhaivra_p03": (_effect(MC, 1, mechanic=INFUSED_BARB_MECHANIC),),
    "zhaivra_p04": (_effect(SP, 5, mechanic=INFUSED_BARB_MECHANIC),),
    "zhaivra_p05": (_effect(D, 2),),
    "zhaivra_p06": (_effect(P, 4, damage_class=PHYS),),
    "zhaivra_p07": (_effect(SP, 3, mechanic=INFUSED_BARB_MECHANIC, uses_intuition=True),),
    "zhaivra_p08": (_effect(MC, 1, mechanic=INFUSED_BARB_MECHANIC),),
    "zhaivra_p09": (_effect(P, 5, damage_class=PHYS, condition=Condition.TARGET_HAS_OWN_STATUS, statuses=("burn", "poison")),),
    "zhaivra_p10": (_effect(P, 3, damage_class=PHYS, condition=Condition.TARGET_HAS_OWN_STATUS, statuses=("burn", "poison")),),
    "zhaivra_p11": (_effect(C, 3, condition=Condition.TARGET_HAS_OWN_STATUS, statuses=("burn", "poison")),),
    "zhaivra_p12": (_effect(D, 3),),
    "zhaivra_p13": (_effect(P, 6, damage_class=PHYS, mechanic=INFUSED_BARB_MECHANIC),),
    "zhaivra_p14": (_effect(P, 5, damage_class=PHYS),),
    "zhaivra_p15": (_effect(SP, 5, mechanic=INFUSED_BARB_MECHANIC, uses_intuition=True),),
    "zhaivra_p16": (_effect(P, 5, damage_class=PHYS, condition=Condition.TARGET_HAS_OWN_STATUS, statuses=("burn", "poison")),),
    "zhaivra_p17": (_effect(P, 7, damage_class=PHYS, mechanic=INFUSED_BARB_MECHANIC, condition=Condition.TARGET_HAS_OWN_STATUS, statuses=("burn", "poison")),),
    "zhaivra_p18": (
        _effect(P, 8, damage_class=PHYS, condition=Condition.TARGET_HAS_OWN_STATUS, statuses=("burn", "poison")),
        _effect(SP, 8, mechanic=INFUSED_BARB_MECHANIC, uses_intuition=True),
    ),
    "joruun_p01": (_effect(P, 5, damage_class=MAG),),
    "joruun_p02": (_effect(A, 3),),
    "joruun_p03": (_effect(MC, 1),),
    "joruun_p04": (_effect(P, 4, damage_class=MAG, mechanic=LIGHTNING_PALM_MECHANIC, condition=Condition.OWN_CONDUCTIVE_OR_TURBULENCE),),
    "joruun_p05": (_effect(D, 2),),
    "joruun_p06": (_effect(P, 4, damage_class=MAG),),
    "joruun_p07": (
        _effect(P, 2, damage_class=PHYS),
        _effect(A, 2),
    ),
    "joruun_p08": (
        _effect(MC, 1, mechanic=HYDRO_WHIP_MECHANIC),
        _effect(MC, 1, mechanic=TEMPEST_SURGE_MECHANIC),
        _effect(MC, 1, mechanic=LIGHTNING_PALM_MECHANIC),
    ),
    "joruun_p09": (_effect(P, 5, damage_class=MAG, mechanic=LIGHTNING_PALM_MECHANIC, condition=Condition.LIGHTNING_STORM),),
    "joruun_p10": (
        _effect(P, 2, damage_class=PHYS),
        _effect(P, 2, damage_class=MAG),
    ),
    "joruun_p11": (
        _effect(SG, 10, mechanic=HYDRO_WHIP_MECHANIC),
        _effect(SG, 10, mechanic=TEMPEST_SURGE_MECHANIC),
        _effect(SG, 10, mechanic=LIGHTNING_PALM_MECHANIC),
    ),
    "joruun_p12": (_effect(M, 1, damage_class=MAG),),
    "joruun_p13": (_effect(P, 5, damage_class=MAG, mechanic=LIGHTNING_PALM_MECHANIC, condition=Condition.OWN_CONDUCTIVE_OR_TURBULENCE),),
    "joruun_p14": (_effect(P, 5, damage_class=MAG),),
    "joruun_p15": (
        _effect(P, 3, damage_class=PHYS),
        _effect(D, 2),
    ),
    "joruun_p16": (_effect(P, 5, damage_class=MAG, condition=Condition.OWN_CONDUCTIVE_OR_TURBULENCE),),
    "joruun_p17": (_effect(P, 8, damage_class=MAG, mechanic=LIGHTNING_PALM_MECHANIC, condition=Condition.LIGHTNING_STORM),),
    "joruun_p18": (
        _effect(P, 8, damage_class=MAG, mechanic=LIGHTNING_PALM_MECHANIC, condition=Condition.LIGHTNING_STORM),
        _effect(SG, 10, mechanic=LIGHTNING_PALM_MECHANIC),
    ),
}


def _validate_catalog():
    active_ids = {
        skill.skill_id
        for skill in ADVANCEMENT_SKILLS
        if skill.kind is not AdvancementSkillKind.PASSIVE
    }
    passive_ids = {
        skill.skill_id
        for skill in ADVANCEMENT_SKILLS
        if skill.kind is AdvancementSkillKind.PASSIVE
    }
    if set(_ACTIVE_MOVES) != active_ids:
        raise ValueError("advancement combat moves must cover every active skill exactly once")
    if set(_PASSIVE_EFFECTS) != passive_ids:
        raise ValueError("advancement passive effects must cover every passive exactly once")
    for skill_id, move in _ACTIVE_MOVES.items():
        skill = get_advancement_skill(skill_id)
        expected_resource = (
            ResourceType.SUPER
            if skill.kind is AdvancementSkillKind.SUPER
            else ResourceType.NONE
            if skill.kind is AdvancementSkillKind.NORMAL_MOVE
            else ResourceType.MANA
        )
        if move.resource_type is not expected_resource:
            raise ValueError(f"advancement move {skill_id} has the wrong resource type")
        if (move.target is TargetType.SELF) != (skill.kind is AdvancementSkillKind.SUPER and move.kind is MoveKind.UTILITY):
            raise ValueError(f"advancement move {skill_id} has an invalid target")


_validate_catalog()
_ACTIVE_MOVES = readonly_mapping(_ACTIVE_MOVES)
_PASSIVE_EFFECTS = readonly_mapping(_PASSIVE_EFFECTS)


def get_advancement_move(skill_id):
    try:
        return _ACTIVE_MOVES[skill_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"advancement skill has no authored move: {skill_id}") from error


def get_advancement_passive_effects(skill_ids):
    effects = []
    for skill_id in skill_ids:
        try:
            effects.extend(_PASSIVE_EFFECTS[skill_id])
        except (KeyError, TypeError) as error:
            raise ValueError(f"advancement skill has no authored passive effect: {skill_id}") from error
    return tuple(effects)


__all__ = ["get_advancement_move", "get_advancement_passive_effects"]
