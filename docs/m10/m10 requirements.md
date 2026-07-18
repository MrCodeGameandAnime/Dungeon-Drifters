**1. Enemy definitions**

For Goblin Warrior, Goblin Shaman, Goblin Elite, and Goblin Lord:

- HP and Mana
- Stats
- Exact moves
- Capabilities
- Tier/rank
- Enemy action policy
- Whether the boss uses the shared three-enemy composition exactly as documented

**2. Multi-enemy turn rules**

Confirm:

```text
Player acts
→ living enemies act in authored order
→ repeat
```

Also:

- Who gets initiative?
- Is one remaining enemy auto-targeted?
- How are duplicate enemies labeled?
- Are defeated enemies still visible?

**3. Progression rewards**

Per encounter:

- EXP
- Gold
- Level-up timing
- Whether permanent attribute growth occurs
- Whether HP/Mana maximum growth immediately affects current values
- Whether secured-EXP scaling is active

**4. Rest rules**

For each of the three rest nodes:

- Full or partial HP/Mana recovery
- Gold or other cost
- Super behavior
- Prepared Infusion behavior
- Whether each rest can be used once
- Whether skipping is allowed

My recommended initial contract is full HP/Mana recovery, no cost, Super and inventory preserved, and each rest node usable once.

**5. Equipment**

- Which item is available during the route
- Slot and stat bonuses
- Who can equip it
- Whether existing signature weapons remain untouched
- Whether defensive equipment affects defense or only stats

**6. Save/load**

- One fixed save path
- Safe save boundaries
- Whether save is manual only
- Opening-menu Load behavior
- Invalid-save behavior
- Whether schema 7 must load or M10 moves directly to schema 8

The route map itself now gives us the authored node order and three rest locations. Once the six areas above are locked, M10 can proceed milestone by milestone without inventing campaign values.