from app.combat.move import Move


def create_legacy_moves():
    return {1: 'deadshot', 2: 'triple shot', 3: 'rain of arrows', 4: 'flaming arrow'}


def create_combat_moves():
    return [
        Move(
            name='deadshot',
            kind='precision_damage',
            mana_cost=4,
            power=12,
            scales_with='dexterity',
            accuracy=95,
            target='enemy',
            mechanic='crit_bonus',
            description='A precise shot with increased critical potential.'),
        Move(
            name='triple shot',
            kind='multi_hit_damage',
            mana_cost=6,
            power=6,
            scales_with='dexterity',
            accuracy=86,
            target='enemy',
            mechanic='multi_hit',
            description='Fires three lighter shots that can each contribute damage.'),
        Move(
            name='rain of arrows',
            kind='area_damage',
            mana_cost=8,
            power=10,
            scales_with='dexterity',
            accuracy=80,
            target='enemy',
            mechanic='volley',
            description='A broad volley designed for future multi-enemy encounters.'),
        Move(
            name='flaming arrow',
            kind='hybrid_damage',
            mana_cost=7,
            power=13,
            scales_with='dexterity',
            accuracy=84,
            target='enemy',
            mechanic='burn',
            description='A dexterous shot with a fire effect hook for later status damage.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Precision',
        'resource': 'focus',
        'description': 'High dexterity supports accuracy, critical hits, and multi-hit attacks.',
    }
