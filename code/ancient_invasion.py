"""
This file contains source code of the game "Ancient Invasion".
Author: DtjiSoftwareDeveloper
"""


# Game version: 1


# Importing necessary libraries

import sys
import uuid
import pickle
import copy
import random
from datetime import datetime
import os
from mpmath import *

mp.pretty = True


# Creating static functions to be used throughout the game.


def is_number(string: str) -> bool:
    try:
        mpf(string)
        return True
    except ValueError:
        return False


def triangular(n: int) -> int:
    return int(n * (n - 1) / 2)


def mpf_sum_of_list(a_list: list) -> mpf:
    return mpf(str(sum(mpf(str(elem)) for elem in a_list if is_number(str(elem)))))


def load_game_data(file_name):
    # type: (str) -> Game
    return pickle.load(open(file_name, "rb"))


def save_game_data(game_data, file_name):
    # type: (Game, str) -> None
    pickle.dump(game_data, open(file_name, "wb"))


def clear():
    # type: () -> None
    if sys.platform.startswith('win'):
        os.system('cls')  # For Windows System
    else:
        os.system('clear')  # For Linux System


# Creating necessary classes.


class Action:
    """
    This class contains attributes of an action which can be carried out during battles.
    """

    POSSIBLE_NAMES: list = ["NORMAL ATTACK", "NORMAL HEAL", "USE SKILL"]

    def __init__(self, name):
        # type: (str) -> None
        self.name: str = name if name in self.POSSIBLE_NAMES else self.POSSIBLE_NAMES[0]

    def clone(self):
        # type: () -> Action
        return copy.deepcopy(self)


class Arena:
    """
    This class contains attributes of the battle arena where the player can face AI controlled trainers as opponents.
    """


class Battle:
    """
    This class contains attributes of a battle in this game.
    """

    def __init__(self, team1, team2):
        # type: (Team, Team) -> None
        self.team1: Team = team1
        self.team2: Team = team2
        self.winner: Team or None = None
        self.whose_turn: Hero or None = None

    def clone(self):
        # type: () -> Battle
        return copy.deepcopy(self)


class BattleArea:
    """
    This class contains attributes of areas where battles take place.
    """

    def __init__(self, name, levels, clear_reward):
        # type: (str, list, Reward) -> None
        self.name: str = name
        self.__levels: list = levels
        self.clear_reward: Reward = clear_reward
        self.is_cleared: bool = False

    def get_levels(self):
        # type: () -> list
        return self.__levels

    def clone(self):
        # type: () -> BattleArea
        return copy.deepcopy(self)


class Dungeon(BattleArea):
    """
    This class contains attributes of dungeons in this game.
    """

    POSSIBLE_DUNGEON_TYPES: list = ["ITEM", "ELEMENTAL"]

    def __init__(self, name, levels, clear_reward, dungeon_type):
        # type: (str, list, Reward, str) -> None
        BattleArea.__init__(self, name, levels, clear_reward)
        self.dungeon_type: str = dungeon_type if dungeon_type in self.POSSIBLE_DUNGEON_TYPES else \
            self.POSSIBLE_DUNGEON_TYPES[0]


class MapArea(BattleArea):
    """
    This class contains attributes of map areas for battles.
    """

    def __init__(self, name, levels, clear_reward):
        # type: (str, list, Reward) -> None
        BattleArea.__init__(self, name, levels, clear_reward)


class Level:
    """
    This class contains attributes of levels in battle areas.
    """

    def __init__(self, name, stages):
        # type: (str, list) -> None
        self.name: str = name
        self.__stages: list = stages
        self.is_cleared: bool = False

    def get_stages(self):
        # type: () -> list
        return self.__stages

    def clone(self):
        # type: () -> Level
        return copy.deepcopy(self)


class LevelStage:
    """
    This class contains attributes of a stage inside a level.
    """

    def __init__(self, enemies_list):
        # type: (list) -> None
        self.__enemies_list: list = enemies_list
        self.is_cleared: bool = False

    def clone(self):
        # type: () -> LevelStage
        return copy.deepcopy(self)


class Hero:
    """
    This class contains attributes of a hero in this game.
    """

    POSSIBLE_HERO_CLASSES: list = ["NORMAL", "MINIBOSS", "BOSS"]
    POSSIBLE_HERO_TYPES: list = ["ATTACK", "DEFENSE", "HP", "SUPPORT"]
    POSSIBLE_ELEMENTS: list = ["FIRE", "WATER", "WIND", "LIGHT", "DARK", "NEUTRAL"]
    MIN_LEVEL: int = 1
    MIN_RATING: int = 1
    MAX_RATING: int = 6
    MIN_CRIT_RATE: mpf = mpf("0.15")
    MAX_CRIT_RATE: mpf = mpf("1")
    MIN_CRIT_DAMAGE: mpf = mpf("0.5")
    MIN_RESISTANCE: mpf = mpf("0.15")
    MAX_RESISTANCE: mpf = mpf("1")
    MIN_ACCURACY: mpf = mpf("0")
    MAX_ACCURACY: mpf = mpf("1")
    MIN_REFLECTED_DAMAGE_PERCENTAGE: mpf = mpf("0")
    MIN_CRIT_RESIST: mpf = mpf("0")
    MIN_GLANCING_HIT_CHANCE: mpf = mpf("0")
    MIN_LIFE_DRAIN_PERCENTAGE: mpf = mpf("0")
    MIN_BUFFS: int = 0
    MAX_BUFFS: int = 10
    MIN_DEBUFFS: int = 0
    MAX_DEBUFFS: int = 10

    def __init__(self, hero_id, name, element, type_, max_hp, max_magic_points, attack_power, defense, attack_speed):
        # type: (str, str, str, str, mpf, mpf, mpf, mpf, mpf) -> None
        self.hero_id: str = hero_id
        self.name: str = name
        self.element: str = element if element in self.POSSIBLE_ELEMENTS else self.POSSIBLE_ELEMENTS[0]
        self.type: str = type_ if type_ in self.POSSIBLE_HERO_TYPES else self.POSSIBLE_HERO_TYPES[0]
        self.level: int = self.MIN_LEVEL
        self.exp: mpf = mpf("0")
        self.required_exp: mpf = mpf("1e6")
        self.curr_hp: mpf = max_hp
        self.max_hp: mpf = max_hp
        self.curr_magic_points: mpf = max_magic_points
        self.max_magic_points: mpf = max_magic_points
        self.attack_power: mpf = attack_power
        self.defense: mpf = defense
        self.attack_speed: mpf = attack_speed
        self.crit_rate: mpf = self.MIN_CRIT_RATE
        self.crit_damage: mpf = self.MIN_CRIT_DAMAGE
        self.resistance: mpf = self.MIN_RESISTANCE
        self.accuracy: mpf = self.MIN_ACCURACY
        self.reflected_damage_percentage: mpf = self.MIN_REFLECTED_DAMAGE_PERCENTAGE
        self.crit_resist: mpf = self.MIN_CRIT_RESIST
        self.glancing_hit_chance: mpf = self.MIN_GLANCING_HIT_CHANCE
        self.life_drain_percentage: mpf = self.MIN_LIFE_DRAIN_PERCENTAGE
        self.shield_amount: mpf = mpf("0")
        self.__buffs: list = []
        self.__debuffs: list = []

    def get_is_alive(self):
        # type: () -> bool
        return self.curr_hp > 0

    def get_buffs(self):
        # type: () -> list
        return self.__buffs

    def add_buff(self, buff):
        # type: (Buff) -> bool
        if len(self.__buffs) < self.MAX_BUFFS:
            self.__buffs.append(buff)
            return True
        return False

    def remove_buff(self, buff):
        # type: (Buff) -> bool
        if buff in self.__buffs:
            self.__buffs.remove(buff)
            return True
        return False

    def get_debuffs(self):
        # type: () -> list
        return self.__debuffs

    def add_debuff(self, debuff):
        # type: (Debuff) -> bool
        if len(self.__debuffs) < self.MAX_DEBUFFS:
            self.__debuffs.append(debuff)
            return True
        return False

    def remove_debuff(self, debuff):
        # type: (Debuff) -> bool
        if debuff in self.__debuffs:
            self.__debuffs.remove(debuff)
            return True
        return False

    def clone(self):
        # type: () -> Hero
        return copy.deepcopy(self)


class AwakenBonus:
    """
    This class contains attributes of the awaken bonus gained for awakening a hero.
    """


class SecondaryAwakenBonus:
    """
    This class contains attributes of the secondary awaken bonus for secondary awakening a hero.
    """


class Skill:
    """
    This class contains attributes of a skill heroes have.
    """


class ActiveSkill(Skill):
    """
    This class contains attributes of active skills heroes have.
    """


class PassiveSkill(Skill):
    """
    This class contains attributes of passive skills heroes have.
    """


class SpecialPower(Skill):
    """
    This class contains attributes of special powers heroes have.
    """


class Team:
    """
    This class contains attributes of a team brought to battles.
    """

    MIN_HEROES: int = 0
    MAX_HEROES: int = 5

    def __init__(self, heroes_list=None):
        # type: (list) -> None
        if heroes_list is None:
            heroes_list = []

        self.__heroes_list: list = heroes_list if self.MIN_HEROES <= len(heroes_list) <= self.MAX_HEROES else []

    def get_heroes_list(self):
        # type: () -> list
        return self.__heroes_list

    def clone(self):
        # type: () -> Team
        return copy.deepcopy(self)


class Item:
    """
    This class contains attributes of an item in this game.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        self.name: str = name
        self.description: str = description
        self.coin_cost: mpf = coin_cost

    def clone(self):
        # type: () -> Item
        return copy.deepcopy(self)


class Gear(Item):
    """
    This class contains attributes of a gear used to power up heroes in this game.
    """

    MIN_RATING: int = 1
    MAX_RATING: int = 6
    MIN_SLOT_NUMBER: int = 1
    MAX_SLOT_NUMBER: int = 8
    POSSIBLE_GEAR_TYPES: list = ["WEAPON", "GLOVES", "SHIRT", "HELMET", "PANTS", "SHOES", "NECKLACE", "RING"]
    POSSIBLE_SET_NAMES: list = ["LIFE", "BEAST", "BLADE", "HAVOC", "IRON", "ERUPTION", "SKILL", "RESISTANCE",
                                "VAMPIRE", "VIOLENT", "SHIELD"]

    def __init__(self, name, description, coin_cost, rating, slot_number, set_name):
        # type: (str, str, mpf, int, int, str) -> None
        Item.__init__(self, name, description, coin_cost)
        self.rating: int = rating if self.MIN_RATING <= rating <= self.MAX_RATING else self.MIN_RATING
        self.slot_number: int = slot_number if self.MIN_SLOT_NUMBER <= slot_number <= self.MAX_SLOT_NUMBER \
            else self.MIN_SLOT_NUMBER
        self.set_name: str = set_name if set_name in self.POSSIBLE_SET_NAMES else self.POSSIBLE_SET_NAMES[0]


class SetEffect:
    """
    This class contains attributes of gear set effect.
    """


class StatIncrease:
    """
    This class contains attributes of increase of stats of a gear.
    """


class Scroll(Item):
    """
    This class contains attributes of a scroll used to summon heroes.
    """


class AwakenShard(Item):
    """
    This class contains attributes of an awaken shard used to awaken a hero in this game.
    """


class EXPShard(Item):
    """
    This class contains attributes of an EXP shard used to increase the EXP of a hero in this game.
    """


class LevelUpShard(Item):
    """
    This class contains attributes of a level up shard used to level up a hero in this game.
    """


class Player:
    """
    This class contains attributes of a player in this game.
    """

    def __init__(self, name):
        # type: (str) -> None
        self.player_id: str = str(uuid.uuid1())  # Generating random player ID
        self.name: str = name
        self.level: int = 1
        self.exp: mpf = mpf("0")
        self.required_exp: mpf = mpf("1e6")
        self.coins: mpf = mpf("0")
        self.arena_wins: int = 0
        self.arena_draws: int = 0
        self.arena_losses: int = 0
        self.arena_points: int = 1000  # initial value
        self.rank: Rank = Rank("BEGINNER")
        self.battle_team: Team = Team()
        self.item_inventory: Inventory = Inventory()

    def update_rank(self):
        # type: () -> None
        """
        Updates the rank of the player based on arena points.
        :return: None
        """

        # TODO: Add code to update player's rank based on arena points

    def clone(self):
        # type: () -> Player
        return copy.deepcopy(self)


class Rank:
    """
    This class contains attributes of the player's rank in the arena.
    """

    POSSIBLE_VALUES: list = ["BEGINNER", "CHALLENGER", "FIGHTER", "CONQUEROR", "GUARDIAN", "LEGEND"]

    def __init__(self, value):
        # type: (str) -> None
        self.value: str = value if value in self.POSSIBLE_VALUES else self.POSSIBLE_VALUES[0]

    def clone(self):
        # type: () -> Rank
        return copy.deepcopy(self)


class PlayerBase:
    """
    This class contains attributes of the base for the player.
    """

    def __init__(self):
        # type: () -> None
        self.__islands: list = []  # initial value

    def get_islands(self):
        # type: () -> list
        return self.__islands

    def add_island(self, island):
        # type: (Island) -> None
        self.__islands.append(island)

    def clone(self):
        # type: () -> PlayerBase
        return copy.deepcopy(self)


class Island:
    """
    This class contains attributes of an island in the player's base.
    """

    ISLAND_HEIGHT: int = 8
    ISLAND_WIDTH: int = 8

    def __init__(self):
        # type: () -> None
        self.__tiles: list = []  # initial value
        for row in range(self.ISLAND_HEIGHT):
            new: list = []  # initial value
            for col in range(self.ISLAND_WIDTH):
                new.append(Tile())

            self.__tiles.append(new)

    def get_tiles(self):
        # type: () -> list
        return self.__tiles

    def clone(self):
        # type: () -> Island
        return copy.deepcopy(self)


class Tile:
    """
    This class contains attributes of a tile on a player island.
    """

    def __init__(self, building=None):
        # type: (Building or None) -> None
        self.building: Building or None = building

    def clone(self):
        # type: () -> Tile
        return copy.deepcopy(self)


class Building:
    """
    This class contains attributes of a building in this game.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        self.name: str = name
        self.description: str = description
        self.coin_cost: mpf = coin_cost

    def clone(self):
        # type: () -> Building
        return copy.deepcopy(self)


class Bank(Building):
    """
    This class contains attributes of a bank producing coins.
    """


class PowerUpCircle(Building):
    """
    This class contains attributes of a power-up circle used to power up heroes in this game.
    """


class ItemShop(Building):
    """
    This class contains attributes of shops selling items to players.
    """


class Summonhenge(Building):
    """
    This class contains attributes of a summonhenge used to summon heroes.
    """


class TempleOfWishes(Building):
    """
    This class contains attributes of temple of wishes for lucky draws.
    """


class TrainingCenter(Building):
    """
    This class contains attributes of a training center to increase heroes' EXP.
    """


class Trainer(Player):
    """
    This class contains attributes of trainers to play against the player in the arena.
    """


class HeroStorage:
    """
    This class contains attributes of a storage to store heroes.
    """

    def __init__(self):
        # type: () -> None
        self.__heroes: list = []  # initial value

    def get_heroes(self):
        # type: () -> list
        return self.__heroes

    def add_hero(self, hero):
        # type: (Hero) -> None
        self.__heroes.append(hero)

    def remove_hero(self, hero):
        # type: (Hero) -> bool
        if hero in self.__heroes:
            self.__heroes.remove(hero)
            return True
        return False

    def clone(self):
        # type: () -> HeroStorage
        return copy.deepcopy(self)


class Inventory:
    """
    This class contains attributes of an inventory to store items.
    """

    def __init__(self):
        # type: () -> None
        self.__items: list = []  # initial value

    def get_items(self):
        # type: () -> list
        return self.__items

    def add_item(self, item):
        # type: (Item) -> None
        self.__items.append(item)

    def remove_item(self, item):
        # type: (Item) -> bool
        if item in self.__items:
            self.__items.remove(item)
            return True
        return False

    def clone(self):
        # type: () -> Inventory
        return copy.deepcopy(self)


class Buff:
    """
    This class contains attributes of beneficial effects in this game.
    """


class Debuff:
    """
    This class contains attributes of harmful effects in this game.
    """


class Reward:
    """
    This class contains attributes of rewards gained for doing something in the game.
    """


class DamageMultiplier:
    """
    This class contains attributes of damage multiplier.
    """


class Game:
    """
    This class contains attributes of saved game data.
    """


# Creating main function to run the game.


def main():
    """
    This function is used to run the game.
    :return: None
    """

    print("Welcome to 'Ancient Invasion' by 'DtjiSoftwareDeveloper'.")
    print("This game is a turn based strategy RPG where you use a team of heroes to battle ")
    print("against another team of heroes.")


if __name__ == '__main__':
    main()
