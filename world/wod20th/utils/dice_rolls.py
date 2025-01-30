from random import randint
from typing import List, Tuple

def roll_dice(dice_pool: int, difficulty: int) -> Tuple[List[int], int, int]:
    """
    Roll dice for World of Darkness 20th Anniversary Edition.

    Args:
    dice_pool (int): The number of dice to roll.
    difficulty (int): The difficulty of the roll.

    Returns:
    Tuple[List[int], int, int]: A tuple containing:
        - List of individual die results
        - Number of successes
        - Number of ones (potential botches)
    """
    rolls = [randint(1, 10) for _ in range(max(0, dice_pool))]
    successes = sum(1 for roll in rolls if roll >= difficulty)
    ones = sum(1 for roll in rolls if roll == 1)
    successes = successes - ones
    
    return rolls, successes, ones

def interpret_roll_results(successes, ones, rolls=None, diff=6, nightmare_dice=0):
    """
    Interpret the results of a dice roll.
    Colors used:
    - Regular successes: |g Green
    - Regular failures: |w White
    - Nightmare successes: |r Red
    - Nightmare failures: |y Yellow
    - Ones: |r Red
    """
    # Format success count with color
    if successes == 0:
        success_string = f"|w{successes}|n"
    elif successes > 0:
        success_string = f"|g{successes}|n"  # Green for successes
    else:
        success_string = f"|r{successes}|n"

    msg = f"|w(|n{success_string}|w)|n"
    
    # Add Success/Successes text
    if successes == -1 and ones > 0:
        msg += f"|r Botch!|n"
    else:
        msg += " Success" if successes == 1 else " Successes"
    
    # Format dice results with color
    if rolls:
        msg += " |w(|n"
        colored_rolls = []
        
        # Keep track of which dice are nightmare dice (the last N dice)
        nightmare_start = len(rolls) - nightmare_dice
        
        # Sort the rolls but keep track of their original positions
        roll_info = [(i, roll) for i, roll in enumerate(rolls)]
        roll_info.sort(key=lambda x: (-x[1], x[0]))  # Sort by value (descending) then position
        
        for i, (orig_pos, roll) in enumerate(roll_info):
            is_nightmare = orig_pos >= nightmare_start
            
            if roll == 1:
                # Ones are always red
                colored_rolls.append(f"|r1|n")
            elif roll >= diff:
                if is_nightmare:
                    # Nightmare successes are magenta
                    colored_rolls.append(f"|m{roll}|n")
                else:
                    # Regular successes are green
                    colored_rolls.append(f"|g{roll}|n")
            else:
                if is_nightmare:
                    # Non-success nightmare dice are blue
                    colored_rolls.append(f"|b{roll}|n")
                else:
                    # Regular non-successes are white
                    colored_rolls.append(f"|w{roll}|n")
        
        msg += " ".join(colored_rolls)
        msg += "|w)|n"
    
    return msg