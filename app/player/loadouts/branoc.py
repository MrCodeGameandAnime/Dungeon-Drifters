from app.combat.move import Move


def create_legacy_moves():
    return {1: 'slash', 2: 'jumping slash', 3: 'suplex'}


def create_combat_moves():
    return [
        Move(
            name='slash',
            kind='physical_damage',
            mana_cost=0,
            power=9,
            scales_with='strength',
            accuracy=92,
            target='enemy',
            mechanic='combo_builder',
            description='A reliable close-range strike that builds momentum.'),
        Move(
            name='jumping slash',
            kind='physical_damage',
            mana_cost=3,
            power=14,
            scales_with='strength',
            accuracy=82,
            target='enemy',
            mechanic='combo_spender',
            description='A risky leaping attack that hits harder after momentum is built.'),
        Move(
            name='suplex',
            kind='physical_damage_control',
            mana_cost=5,
            power=18,
            scales_with='strength',
            accuracy=75,
            target='enemy',
            mechanic='stagger',
            description='A brutal throw that can stagger a weakened foe.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Momentum',
        'resource': 'momentum',
        'description': 'Basic hits build momentum; heavy techniques spend it for burst damage.',
    }
