from app.combat.move import Move


def create_legacy_moves():
    return {1: 'fireball', 2: 'heal', 3: 'thunderbolt'}


def create_combat_moves():
    return [
        Move(
            name='fireball',
            kind='magic_damage',
            mana_cost=8,
            power=14,
            scales_with='intelligence',
            accuracy=88,
            target='enemy',
            mechanic='burn',
            description='A direct fire spell with a chance to leave burning damage later.'),
        Move(
            name='heal',
            kind='healing',
            mana_cost=10,
            power=12,
            scales_with='intelligence',
            accuracy=100,
            target='self',
            mechanic='arcane_recovery',
            description='Restores health instead of damaging the enemy.'),
        Move(
            name='thunderbolt',
            kind='magic_damage',
            mana_cost=14,
            power=20,
            scales_with='intelligence',
            accuracy=78,
            target='enemy',
            mechanic='shock',
            description='A volatile lightning spell with high damage and lower accuracy.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Arcane Focus',
        'resource': 'mana',
        'description': 'Spells spend mana and scale primarily from intelligence.',
    }  # ice shield
