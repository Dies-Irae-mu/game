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

def interpret_roll_results(successes, ones, diff=6, rolls=None):
    """
    Interpret the results of a dice roll.

    Args:
    successes (int): The number of successes rolled.
    ones (int): The number of ones rolled.

    Returns:
    str: A string describing the result of the roll.
    """
    success_string = ""
    if successes == 0:
        success_string = f"|y{successes}|n"
    elif successes > 0:
        success_string = f"|g{successes}|n"
    else:
        success_string = f"|r{successes}|n"
        

    msg =  f"|w(|n{success_string}|w)|n"
    if successes == -1 and ones > 0:
        msg += f"|r Botch!|n"
    else:
        msg += "|y Successes|n" if successes != 1 else "|y Success|n"
    

   # colorize the succesess to green, botches to red and everything else to yellow
    msg += " |w(|n"
    if rolls:
        rolls.sort( reverse=True )
        for roll in rolls:
            if roll == 1:
                msg += f"|r{roll}|n"
            elif roll >= diff:
                msg += f"|g{roll}|n"
            else:
                msg += f"|y{roll}|n"
            
            if roll != rolls[-1]:
                msg += " "


    msg += "|w)|n"
    return msg