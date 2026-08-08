"""Brawler authored Drifter content."""

from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.combat.move_presentation import MovePresentation, MoveRole
from app.content.drifter_spec import (
    ClassMechanicSpec,
    DrifterSpec,
    DrifterStatSpec,
)


_STATS = DrifterStatSpec(14, 6, 5, 15, 10, 10)


_COMBAT_MOVES = (
        Move(
            name='Crestgrave Reaping',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=9,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=92,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='basic_attack',
            # Deferred mechanic: guard and armor cleave
            description='Sunder-Spire tears through the target, cleaving guard and armor.',
            presentation=MovePresentation(role=MoveRole.NORMAL)),
        Move(
            name='Cinderlung Vesper',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=3,
            power=8,
            scales_with=(ScalingAttribute.SPIRIT,),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=None,
            # Deferred mechanic: line or multi-target war-breath
            description='A black war-breath erupts forward, searing everything in its path.',
            presentation=MovePresentation(
                role=MoveRole.NORMAL,
                affinity_label='Fire',
            )),
        Move(
            name='Brace',
            kind=MoveKind.UTILITY,
            resource_type=ResourceType.MANA,
            resource_cost=5,
            power=0,
            scales_with=(ScalingAttribute.NONE,),
            accuracy=100,
            target=TargetType.SELF,
            damage_type=DamageType.NONE,
            mechanic='brace',
            description='Branoc plants Sunder-Spire and braces behind the Deep-Iron crest.',
            presentation=MovePresentation(role=MoveRole.UTILITY)),
        Move(
            name='Ironwake Dismemberment',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=14,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=82,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='heavy_attack',
            # Deferred mechanic: battlefield-splitting impact
            description='Branoc drives Sunder-Spire downward with battlefield-splitting force.',
            presentation=MovePresentation(
                role=MoveRole.HEAVY,
                static_summary='A crushing Sunder-Spire strike.',
            )),
        Move(
            name='Third Gate Obsequy',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.SUPER,
            resource_cost=100,
            power=24,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.SPIRIT),
            accuracy=100,
            target=TargetType.ENEMY,
            damage_type=DamageType.HYBRID,
            mechanic=None,
            # Deferred mechanic: Third Gate manifestation
            description='A forbidden gate manifests behind Branoc, pouring ruin through Sunder-Spire.',
            presentation=MovePresentation(role=MoveRole.SUPER)),
)


DRIFTER = DrifterSpec(
    drifter_id="branoc",
    archetype_name='Brawler',
    stats=_STATS,
    combat_moves=_COMBAT_MOVES,
    class_mechanic=ClassMechanicSpec(
        name='Heavy Vanguard',
        description='A durable frontline identity built around heavy physical pressure.',
    ),
    starting_weapon_id="sunder_spire",
    starting_run_inventory=(),
    starting_prepared_payloads=(),
    choice="1",
    short_name="Ser Branoc",
    display_name="Ser Branoc, the Unbroken Crest",
    ascii_art=r"""
        /\_/\                  .-^^^^^^^^^-.                /\_/\
   ____/ / \ \____          .-'  RHOM-GHAL  '-.        ____/ / \ \____
  /___  /___\  ___\________/___________________\______/___  /___\  ___\
      | |   | |      _.-'   /\    /\    /\    /\ '-._      | |   | |
   ___|_|___|_|___.-'      /  \__/  \__/  \__/  \    '-.___|_|___|_|___
  /  /\   /\   /\ \       / /\  /\  /\  /\  /\ \        / /\   /\   /\ \
 /__/  \_/  \_/  \_\     /_/  \/  \/  \/  \/  \_\      /_/  \_/  \_/  \_\
 |                  \ |      .---------------.      | /                 |
 |   THE UNBROKEN    \|    .'  /\   /\   /\   '.    |/    THIRD GATE    |
 |      CREST         |   /   /  \_/  \_/  \    \   |      SENTINEL     |
 |                    |  |   / /\   /\   /\  \   |  |                   |
 |      /\    /\      |  |  /_/  \_/  \_/  \__\  |  |      /\    /\     |
 |_____/  \__/  \_____|  |       __________      |  |_____/  \__/  \____|
 \                   /   |      /  ______  \     |   \                  /
  \_________________/    |     /__/|    |\__\    |    \________________/
        \                |     |  || /\ ||  |    |                /
         '---------------|     |__||_||_||__|    |---------------'
                         '--------\_||_/--------'
              .============ HONOR  DUTY  ENDURE ============.
               '============================================'
""",
    origin_title="Exiled Sentinel of Rhom-Ghal",
    biography="""From the Iron-Spires of Rhom-Ghal comes a knight without a crest. Once Lord-Commander of the mountain
vanguard, Branoc surrendered his name, rank, and homeland to spare the soldiers under his command. Now he wanders the
outer kingdoms in scarred Deep-Iron plate, accepting no gold for his sword, only provisions and information. Behind the
narrow grilles of his helm is no revenant or cursed immortal. Branoc is flesh and blood, sustained by the Rhom-Ghalian
Lung, a punishing discipline that allows the mountain knights to fight through thin air, smoke, exhaustion, and pain.
He carries Sunder-Spire, a massive Great-Flamberge forged from broken Deep-Iron. Its rippled edge tears through guards
and chainmail, while Branoc’s weight and momentum turn every swing into a crushing advance.""",
    dungeon_motive="""He has entered the dungeon in search of a lost mark of the Third Gate, believing it may lead him
    to the scattered remnants of his fallen order. He does not know what waits beneath the stone.""",
    combat_role="Heavy Vanguard",
    combat_summary="""Branoc is slow, durable, and difficult to interrupt. He controls space through sweeping attacks,
    heavy stagger, and relentless forward pressure.""",
    strengths="Defense, endurance, guard breaking, crowd control",
    weaknesses="Speed, recovery time, limited mobility",
    weapon="Sunder-Spire",
    discipline="Rhom-Ghalian Lung",
    quote="“Endurance is merely suffering with direction.”",
    selection_summary="durable, relentless, slow",
)


__all__ = ["DRIFTER"]
