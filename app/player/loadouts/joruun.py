from app.combat.move import Move


def create_legacy_moves():
    return {
        1: 'Bring The Horse To Water',
        2: 'Sweep The Leaves',
        3: '5-foot punch',
        4: 'Waki Gamae Kamae Kata',
        5: 'Carry Water',
    }


def create_combat_moves():
    return [
        Move(
            name='Bring The Horse To Water',
            kind='physical_damage_control',
            mana_cost=3,
            power=10,
            scales_with='strength',
            accuracy=90,
            target='enemy',
            mechanic='brace',
            description='Braces the staff and pulls the target into the strike.'),
        Move(
            name='Sweep The Leaves',
            kind='physical_damage_control',
            mana_cost=4,
            power=11,
            scales_with='dexterity',
            accuracy=88,
            target='enemy',
            mechanic='trip',
            description='A low strike that can knock the enemy off balance.'),
        Move(
            name='5-foot punch',
            kind='ki_damage',
            mana_cost=5,
            power=13,
            scales_with='strength',
            accuracy=86,
            target='enemy',
            mechanic='ki_burst',
            description='A focused staff thrust that channels Ki through impact.'),
        Move(
            name='Waki Gamae Kamae Kata',
            kind='charged_damage',
            mana_cost=8,
            power=20,
            scales_with='constitution',
            accuracy=76,
            target='enemy',
            mechanic='charged_counter',
            description='A committed overhead form best used after bracing or defending.'),
        Move(
            name='Carry Water',
            kind='finisher_damage',
            mana_cost=10,
            power=24,
            scales_with='strength',
            accuracy=72,
            target='enemy',
            mechanic='prone_finisher',
            description='A heavy finishing maneuver against a vulnerable or prone foe.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Ki Forms',
        'resource': 'ki',
        'description': 'Monk techniques combine positioning, balance, and Ki setup effects.',
    }


# Bring The Horse To Water:
# brace the quarterstaff (think: set spear vs charge) and pull the target's head into it.
#
# Sweep The Leaves:
# low strike to the shin or foot, could also be a shove (trip) attack.
#
# 5-foot punch:
# straight thrust into the stomach, playing on the name of the 5-inch punch from Jeet Kune Do
#
# Waki Gamae Kamae Kata (Wah-Kee Gah-May Ka-May Ka-Ta):
# a strike from holding the quarterstaff overhead with both hands at the bottom.
# Best when done at the end of a charge or after defending for a turn (to charge up!)
#
# Carry Water:
# execute a fireman's carry maneuver on the quarterstaff against a prone enemy,
# using both rotational force and adding your own weight to maximize the blow.
