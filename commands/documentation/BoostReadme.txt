# Stat Boost System Documentation

## Overview
The stat boost system allows characters to temporarily enhance their attributes, abilities, and pools based on their supernatural type (splat). The system handles both temporary and indefinite boosts, tracks active boosts with IDs, and manages boost stacking.

## Key Components

### 1. Boost Types
- **Vampire Boosts**: Physical attributes only, lasts 1 hour, costs blood
- **Shifter Boosts**: Any stat if they have a Totem background, indefinite duration
- **Changeling/Mage/Mortal+ Boosts**: Any attribute, indefinite duration
- **Fomori/Kami Boosts**: Through blessings, indefinite duration

### 2. Boost Storage
Boosts are stored in three key character attributes:
- `attribute_boosts`: Dictionary tracking active boosts
- `next_boost_id`: Counter for assigning unique boost IDs
- `recycled_boost_ids`: List of previously used IDs available for reuse

### 3. Stat Categories
The system handles different stat types:
- Attributes (physical, social, mental)
- Abilities (talents, skills, knowledges)
- Pools (rage, gnosis, willpower)
- Secondary abilities

## Core Functionality

### Boost Application
1. **Direct Dictionary Access for Attributes**
   ```python
   # For attributes, directly modify the stats dictionary
   stats_dict[category][stat_type][stat_name]['temp'] = new_value
   ```

2. **Boost Stacking**
   - If a stat is already boosted, adds to existing boost
   - Tracks total boost amount in `attribute_boosts`
   - Maintains cap limits (10 for most stats, 20 for rage/gnosis)

3. **Boost Storage Format**
   ```python
   attribute_boosts[stat_name] = {
       'id': boost_id,
       'amount': boost_amount,
       'source': source_name
   }
   ```

### Boost Management

1. **Adding Boosts**
   - Validates character can boost the stat
   - Checks against stat caps
   - Assigns unique boost ID
   - Stores boost information
   - Updates temporary stat value

2. **Ending Boosts**
   - Individual boost removal (`+boost/end <id>`)
   - Mass boost removal (`+boost/endall`)
   - Returns stats to permanent values
   - Recycles boost IDs

3. **Boost Duration**
   - Vampire boosts: 1 hour automatic expiration
   - Other splats: Indefinite until manually ended

## Special Cases

1. **Pool Stats**
   - Rage, Gnosis, Willpower have special handling
   - Higher caps (20 instead of 10)
   - Modifies both permanent and temporary values

2. **Vampire Blood Expenditure**
   ```python
   # Checks and deducts blood points
   if current_blood < amount:
       return "Not enough blood"
   new_blood = current_blood - amount
   ```

3. **Shifter Totem Source**
   - Tracks totem name in boost source
   - Requires Totem background to boost

## Commands

1. **Boost Application**
   ```
   +boost <stat>=<amount>
   ```

2. **Boost Management**
   ```
   +boost/end <id>     # End specific boost
   +boost/endall       # End all boosts
   +boosts            # List active boosts
   ```

## Error Handling
- Validates stat existence
- Checks boost permissions
- Ensures proper boost amounts
- Maintains stat caps
- Preserves minimum values for pools

## Best Practices
1. Always use direct dictionary access for attributes
2. Maintain boost tracking in `attribute_boosts`
3. Use proper case for stat names
4. Handle pool stats separately
5. Preserve boost stacking functionality