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

    def execute(self, user, target, skill_to_use=None):
        # type: (Hero, Hero, Skill or None) -> bool
        if self.name == "NORMAL ATTACK":
            if user == target:
                return False

            user_actual_crit_rate: mpf = user.crit_rate + user.battle_crit_rate_up
            if user_actual_crit_rate > user.MAX_CRIT_RATE:
                user_actual_crit_rate = user.MAX_CRIT_RATE

            is_crit: bool = random.random() <= user_actual_crit_rate
            user_actual_attack_power: mpf = user.attack_power * (1 + user.battle_attack_power_percentage_up / 100 -
                                                                 user.battle_attack_power_percentage_down / 100)
            target_actual_defense: mpf = target.defense * (1 + target.battle_defense_percentage_up / 100 -
                                                           target.battle_defense_percentage_down / 100)
            raw_damage: mpf = user_actual_attack_power
            if is_crit:
                raw_damage *= user.crit_damage

            raw_damage -= target_actual_defense
            damage: mpf = raw_damage if raw_damage > 0 else 0
            target.curr_hp -= damage
            return True

        elif self.name == "NORMAL HEAL":
            if user != target:
                return False

            heal_amount: mpf = 0.05 * user.max_hp
            user.curr_hp += heal_amount
            return True

        elif self.name == "USE SKILL":
            if isinstance(skill_to_use, Skill):
                # TODO: fix this elif branch by checking whether the skill attacks or heals and the team the user and the target are in
                # Attack the enemy if the skill is an active skill or a special power
                if isinstance(skill_to_use, ActiveSkill):
                    user_actual_crit_rate: mpf = user.crit_rate + user.battle_crit_rate_up
                    if user_actual_crit_rate > user.MAX_CRIT_RATE:
                        user_actual_crit_rate = user.MAX_CRIT_RATE

                    target_team: Team = target.curr_team
                    if not skill_to_use.is_aoe:
                        if user not in target_team.get_heroes_list():
                            raw_damage: mpf = skill_to_use.damage_multiplier.\
                                calculate_normal_raw_damage_without_enemy_defense(user, target)
                            is_crit: bool = random.random() <= user_actual_crit_rate
                            if is_crit:
                                raw_damage *= user.crit_damage

                            if not skill_to_use.does_ignore_enemies_defense:
                                raw_damage -= target.defense

                            damage: mpf = raw_damage if raw_damage > 0 else 0
                            target_is_invincible: bool = False
                            for buff in target.get_buffs():
                                if buff.name == "INVINCIBLE":
                                    target_is_invincible = True

                            if target_is_invincible:
                                damage = 0

                            target.curr_hp -= damage
                        else:
                            user.curr_hp += skill_to_use.heal_amount_to_self
                            if user.curr_hp > user.max_hp:
                                user.curr_hp = user.max_hp

                            target.curr_hp += skill_to_use.heal_amount_to_allies
                            if target.curr_hp > target.max_hp:
                                target.curr_hp = target.max_hp
                    else:
                        for enemy_target in target_team.get_heroes_list():
                            raw_damage: mpf = skill_to_use.damage_multiplier. \
                                calculate_normal_raw_damage_without_enemy_defense(user, enemy_target)
                            is_crit: bool = random.random() <= user_actual_crit_rate
                            if is_crit:
                                raw_damage *= user.crit_damage

                            if not skill_to_use.does_ignore_enemies_defense:
                                raw_damage -= enemy_target.defense

                            damage: mpf = raw_damage if raw_damage > 0 else 0
                            enemy_target_is_invincible: bool = False
                            for buff in enemy_target.get_buffs():
                                if buff.name == "INVINCIBLE":
                                    enemy_target_is_invincible = True

                            if enemy_target_is_invincible:
                                damage = 0

                            enemy_target.curr_hp -= damage

            elif isinstance(skill_to_use, SpecialPower):
                if skill_to_use.cooltime == 0:
                    user_actual_crit_rate: mpf = user.crit_rate + user.battle_crit_rate_up
                    if user_actual_crit_rate > user.MAX_CRIT_RATE:
                        user_actual_crit_rate = user.MAX_CRIT_RATE

                    raw_damage: mpf = skill_to_use.damage_multiplier. \
                        calculate_normal_raw_damage_without_enemy_defense(user, target)
                    is_crit: bool = random.random() <= user_actual_crit_rate
                    if is_crit:
                        raw_damage *= user.crit_damage

                    if not skill_to_use.does_ignore_enemies_defense:
                        raw_damage -= target.defense

                    damage: mpf = raw_damage if raw_damage > 0 else 0
                    target_is_invincible: bool = False
                    for buff in target.get_buffs():
                        if buff.name == "INVINCIBLE":
                            target_is_invincible = True

                    if target_is_invincible:
                        damage = 0

                    target.curr_hp -= damage

    def clone(self):
        # type: () -> Action
        return copy.deepcopy(self)


class Arena:
    """
    This class contains attributes of the battle arena where the player can face AI controlled trainers as opponents.
    """

    def __init__(self, available_opponent_trainers):
        # type: (list) -> None
        self.__available_opponent_trainers: list = available_opponent_trainers

    def add_opponent_trainer(self, opponent_trainer):
        # type: (Trainer) -> None
        self.__available_opponent_trainers.append(opponent_trainer)

    def remove_opponent_trainer(self, opponent_trainer):
        # type: (Trainer) -> bool
        if opponent_trainer in self.__available_opponent_trainers:
            self.__available_opponent_trainers.remove(opponent_trainer)
            return True
        return False

    def get_available_opponent_trainers(self):
        # type: () -> list
        return self.__available_opponent_trainers

    def clone(self):
        # type: () -> Arena
        return copy.deepcopy(self)


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
        self.times_beaten: int = 0  # initial value

    def get_beaten(self):
        # type: () -> None
        """
        Make enemies stronger once this stage is beaten.
        :return: None
        """

        for stage in self.__stages:
            for enemy in stage.get_enemies_list():
                for i in range(2 ** self.times_beaten):
                    enemy.exp = enemy.required_exp
                    enemy.level_up()

        self.times_beaten += 1

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

    def get_enemies_list(self):
        # type: () -> list
        return self.__enemies_list

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
    MIN_EXTRA_TURN_CHANCE: mpf = mpf("0")
    MAX_EXTRA_TURN_CHANCE: mpf = mpf("0.75")
    MIN_COUNTERATTACK_CHANCE: mpf = mpf("0")
    MAX_COUNTERATTACK_CHANCE: mpf = mpf("1")
    MIN_STUN_RATE: mpf = mpf("0")
    MAX_STUN_RATE: mpf = mpf("0")
    MIN_ATTACK_GAUGE: mpf = mpf("0")
    FULL_ATTACK_GAUGE: mpf = mpf("1")
    MIN_BUFFS: int = 0
    MAX_BUFFS: int = 10
    MIN_DEBUFFS: int = 0
    MAX_DEBUFFS: int = 10

    def __init__(self, hero_id, name, element, type_, rating,
                 max_hp, max_magic_points, attack_power, defense, attack_speed, skills, secondary_awaken_exp_required,
                 awaken_bonus, secondary_awaken_bonus, immunities=None):
        # type: (str, str, str, str, int, mpf, mpf, mpf, mpf, mpf, list, mpf, AwakenBonus, SecondaryAwakenBonus, list) -> None
        if immunities is None:
            immunities = []
        self.__immunities: list = immunities
        self.hero_id: str = hero_id
        self.name: str = name
        self.element: str = element if element in self.POSSIBLE_ELEMENTS else self.POSSIBLE_ELEMENTS[0]
        self.type: str = type_ if type_ in self.POSSIBLE_HERO_TYPES else self.POSSIBLE_HERO_TYPES[0]
        self.rating: int = rating if self.MIN_RATING <= rating <= self.MAX_RATING else self.MIN_RATING
        self.level: int = self.MIN_LEVEL
        self.max_level: int = triangular(self.rating) * 10
        self.limit_break_applied: bool = False
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
        self.extra_turn_chance: mpf = self.MIN_EXTRA_TURN_CHANCE
        self.counterattack_chance: mpf = self.MIN_COUNTERATTACK_CHANCE
        self.stun_rate: mpf = self.MIN_STUN_RATE
        self.__buffs: list = []
        self.__debuffs: list = []
        self.__skills: list = skills  # initial value
        self.attack_gauge_up_per_hp_percentage_down: mpf = mpf("0")
        self.attack_gauge: mpf = self.MIN_ATTACK_GAUGE
        self.starting_turns_with_immunity: int = 0
        self.secondary_awaken_exp: mpf = mpf("0")
        self.secondary_awaken_exp_required: mpf = secondary_awaken_exp_required
        self.can_reduce_enemies_max_hp: bool = False  # initial value as no destroy runes are equipped
        self.turns_gained: int = 0  # Initial number of turns gained before battles start. This will reset after
        # finishing a battle.
        self.awaken_bonus: AwakenBonus = awaken_bonus
        self.secondary_awaken_bonus: SecondaryAwakenBonus = secondary_awaken_bonus
        self.has_awakened: bool = False
        self.is_locked: bool = False  # initial value. This variable determines whether this hero is locked from
        # being used as power up material or not
        self.has_secondary_awakened: bool = False
        self.curr_team: Team or None = None  # initial value

        # Initialising variables for stat bonus and penalties for battles from both self and ally runes which increase
        # allies' stats, passive skills, leader skills, buffs, and debuffs.
        self.battle_attack_power_percentage_up: mpf = mpf("0")
        self.battle_defense_percentage_up: mpf = mpf("0")
        self.battle_attack_speed_percentage_up: mpf = mpf("0")
        self.battle_max_hp_percentage_up: mpf = mpf("0")
        self.battle_crit_rate_up: mpf = mpf("0")
        self.battle_crit_damage_up: mpf = mpf("0")
        self.battle_accuracy_up: mpf = mpf("0")
        self.battle_resistance_up: mpf = mpf("0")
        self.battle_max_magic_points_percentage_up: mpf = mpf("0")
        self.battle_additional_damage_percentage_received: mpf = mpf("0")  # percentage of additional damage received. This
        # has something to do with branding effects.
        self.battle_damage_percentage_reduced: mpf = mpf("0")
        self.battle_damage_per_turn: mpf = mpf("0")
        self.battle_max_hp_percentage_down: mpf = mpf("0")
        self.battle_attack_power_percentage_down: mpf = mpf("0")
        self.battle_defense_percentage_down: mpf = mpf("0")
        self.battle_attack_speed_percentage_down: mpf = mpf("0")
        self.battle_counterattack_chance_up: mpf = mpf("0")
        self.battle_reflected_damage_percentage_up: mpf = mpf("0")
        self.battle_shield_amount_percentage: mpf = mpf("0")
        self.battle_recovery_percentage_per_turn: mpf = mpf("0")
        self.battle_dodge_attack_chance: mpf = mpf("0")
        self.__battle_immunities: list = []  # initial value

    def get_battle_immunities(self):
        # type: () -> list
        return self.__battle_immunities

    def get_immunities(self):
        # type: () -> list
        return self.__immunities

    def get_skills(self):
        # type: () -> list
        return self.__skills

    def add_skill(self, skill):
        # type: (Skill) -> None
        self.__skills.append(skill)

    def remove_skill(self, skill):
        # type: (Skill) -> bool
        if skill in self.__skills:
            self.__skills.remove(skill)
            return True
        return False

    def apply_limit_break(self):
        # type: () -> bool
        if not self.limit_break_applied and self.level == self.max_level and self.rating == self.MAX_RATING:
            self.limit_break_applied = True
            self.max_level = float('inf')
            return True
        return False

    def recover_magic_points(self):
        # type: () -> None
        self.curr_magic_points += self.max_magic_points / 12
        if self.curr_magic_points >= self.max_magic_points:
            self.curr_magic_points = self.max_magic_points

    def restore(self):
        # type: () -> None
        self.curr_hp = self.max_hp
        self.curr_magic_points = self.max_magic_points

    def level_up(self):
        # type: () -> None
        while self.exp >= self.required_exp:
            if self.level == self.max_level:
                break

            self.level += 1
            self.required_exp *= mpf("10") ** self.level
            self.attack_power *= triangular(self.level)
            self.max_hp *= triangular(self.level)
            self.max_magic_points *= triangular(self.level)
            self.defense *= triangular(self.level)
            self.restore()

    def normal_attack(self, other):
        # type: (Hero) -> None
        action: Action = Action("NORMAL ATTACK")
        action.execute(self, other)

    def normal_heal(self, other):
        # type: (Hero) -> None
        action: Action = Action("NORMAL HEAL")
        action.execute(self, other)

    def use_skill(self, other, skill):
        # type: (Hero, Skill) -> bool
        if skill not in self.__skills:
            return False

        if self.curr_magic_points < skill.magic_points_cost:
            return False

        action: Action = Action("USE SKILL")
        action.execute(self, other, skill)
        self.curr_magic_points -= skill.magic_points_cost
        return True

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

    def __init__(self, max_hp_percentage_up, max_magic_points_percentage_up, attack_power_percentage_up,
                 defense_percentage_up, attack_speed_up, crit_rate_up, crit_damage_up, resistance_up, accuracy_up,
                 new_skill_gained):
        # type: (mpf, mpf, mpf, mpf,mpf, mpf, mpf, mpf, mpf, Skill) -> None
        self.max_hp_percentage_up: mpf = max_hp_percentage_up
        self.max_magic_points_percentage_up: mpf = max_magic_points_percentage_up
        self.attack_power_percentage_up: mpf = attack_power_percentage_up
        self.defense_percentage_up: mpf = defense_percentage_up
        self.attack_speed_up: mpf = attack_speed_up
        self.crit_rate_up: mpf = crit_rate_up
        self.crit_damage_up: mpf = crit_damage_up
        self.resistance_up: mpf = resistance_up
        self.accuracy_up: mpf = accuracy_up
        self.new_skill_gained: Skill = new_skill_gained

    def clone(self):
        # type: () -> AwakenBonus
        return copy.deepcopy(self)


class SecondaryAwakenBonus:
    """
    This class contains attributes of the secondary awaken bonus for secondary awakening a hero.
    """

    def __init__(self, max_hp_percentage_up, max_magic_points_percentage_up, attack_power_percentage_up,
                 defense_percentage_up, new_upgraded_skills_list):
        # type: (mpf, mpf, mpf, mpf, list) -> None
        self.max_hp_percentage_up: mpf = max_hp_percentage_up
        self.max_magic_points_percentage_up: mpf = max_magic_points_percentage_up
        self.attack_power_percentage_up: mpf = attack_power_percentage_up
        self.defense_percentage_up: mpf = defense_percentage_up
        self.__new_upgraded_skills_list: list = new_upgraded_skills_list  # a list of new skills the hero will have
        # which will be the upgraded versions of the initial skills the hero has.

    def get_new_upgraded_skills_list(self):
        # type: () -> list
        return self.__new_upgraded_skills_list

    def clone(self):
        # type: () -> SecondaryAwakenBonus
        return copy.deepcopy(self)


class Skill:
    """
    This class contains attributes of a skill heroes have.
    """

    def __init__(self, name, description, magic_points_cost):
        # type: (str, str, mpf) -> None
        self.name: str = name
        self.description: str = description
        self.magic_points_cost: mpf = magic_points_cost

    def clone(self):
        # type: () -> Skill
        return copy.deepcopy(self)


class ActiveSkill(Skill):
    """
    This class contains attributes of active skills heroes have.
    """

    def __init__(self, name, description, magic_points_cost, damage_multiplier, does_ignore_enemies_defense,
                 buffs_to_self, buffs_to_allies, debuffs_to_enemies, does_remove_self_debuffs, does_remove_allies_debuffs,
                 does_remove_enemies_buffs, self_attack_gauge_increase, enemies_attack_gauge_down, heal_amount_to_self,
                 heal_amount_to_allies, does_balance_allies_hp_bar, is_aoe):
        # type: (str, str, mpf, DamageMultiplier, bool, list, list, list, bool, bool, bool, mpf, mpf, mpf, mpf, bool, bool) -> None
        Skill.__init__(self, name, description, magic_points_cost)
        self.damage_multiplier: DamageMultiplier = damage_multiplier
        self.does_ignore_enemies_defense: bool = does_ignore_enemies_defense
        self.__buffs_to_self: list = buffs_to_self
        self.__buffs_to_allies: list = buffs_to_allies
        self.__debuffs_to_enemies: list = debuffs_to_enemies
        self.does_remove_self_debuffs: bool = does_remove_self_debuffs
        self.does_remove_allies_debuffs: bool = does_remove_allies_debuffs
        self.does_remove_enemies_buffs: bool = does_remove_enemies_buffs
        self.self_attack_gauge_increase: mpf = self_attack_gauge_increase
        self.enemies_attack_gauge_down: mpf = enemies_attack_gauge_down
        self.heal_amount_to_self: mpf = heal_amount_to_self
        self.heal_amount_to_allies: mpf = heal_amount_to_allies
        self.does_balance_allies_hp_bar: bool = does_balance_allies_hp_bar
        self.is_aoe: bool = is_aoe

    def get_buffs_to_self(self):
        # type: () -> list
        return self.__buffs_to_self

    def get_buffs_to_allies(self):
        # type: () -> list
        return self.__buffs_to_allies

    def get_debuffs_to_enemies(self):
        # type: () -> list
        return self.__debuffs_to_enemies


class PassiveSkill(Skill):
    """
    This class contains attributes of passive skills heroes have.
    """

    def __init__(self, name, description, passive_effect):
        # type: (str, str, PassiveEffect) -> None
        Skill.__init__(self, name, description, mpf("0"))
        self.passive_effect: PassiveEffect = passive_effect


class PassiveEffect:
    """
    This class contains attributes of passive skill effects.
    """

    def __init__(self, self_max_hp_percentage_up, self_max_magic_points_percentage_up, self_attack_power_percentage_up,
                 self_defense_percentage_up, self_attack_speed_percentage_up, self_crit_rate_up, self_crit_damage_up,
                 self_resistance_up, self_accuracy_up, self_damage_percentage_reduced, allies_max_hp_percentage_up,
                 allies_max_magic_points_percentage_up, allies_attack_power_percentage_up, allies_defense_percentage_up,
                 allies_attack_speed_percentage_up, allies_crit_rate_up, allies_crit_damage_up, allies_resistance_up,
                 allies_accuracy_up, allies_damage_percentage_reduced, immunities, self_attack_gauge_increase,
                 enemies_attack_gauge_down, dodge_attack_chance):
        # type: (mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, list, mpf, mpf, mpf) -> None
        self.self_max_hp_percentage_up: mpf = self_max_hp_percentage_up
        self.self_max_magic_points_percentage_up: mpf = self_max_magic_points_percentage_up
        self.self_attack_power_percentage_up: mpf = self_attack_power_percentage_up
        self.self_defense_percentage_up: mpf = self_defense_percentage_up
        self.self_attack_speed_percentage_up: mpf = self_attack_speed_percentage_up
        self.self_crit_rate_up: mpf = self_crit_rate_up
        self.self_crit_damage_up: mpf = self_crit_damage_up
        self.self_resistance_up: mpf = self_resistance_up
        self.self_accuracy_up: mpf = self_accuracy_up
        self.self_damage_percentage_reduced: mpf = self_damage_percentage_reduced
        self.allies_max_hp_percentage_up: mpf = allies_max_hp_percentage_up
        self.allies_max_magic_points_percentage_up: mpf = allies_max_magic_points_percentage_up
        self.allies_attack_power_percentage_up: mpf = allies_attack_power_percentage_up
        self.allies_defense_percentage_up: mpf = allies_defense_percentage_up
        self.allies_attack_speed_percentage_up: mpf = allies_attack_speed_percentage_up
        self.allies_crit_rate_up: mpf = allies_crit_rate_up
        self.allies_crit_damage_up: mpf = allies_crit_damage_up
        self.allies_resistance_up: mpf = allies_resistance_up
        self.allies_accuracy_up: mpf = allies_accuracy_up
        self.allies_damage_percentage_reduced: mpf = allies_damage_percentage_reduced
        self.__immunities: list = immunities
        self.self_attack_gauge_increase: mpf = self_attack_gauge_increase
        self.enemies_attack_gauge_down: mpf = enemies_attack_gauge_down
        self.dodge_attack_chance: mpf = dodge_attack_chance

    def get_immunities(self):
        # type: () -> list
        return self.__immunities

    def clone(self):
        # type: () -> PassiveEffect
        return copy.deepcopy(self)


class LeaderSkill(Skill):
    """
    This class contains attributes of leader skills heroes have.
    """

    def __init__(self, name, description, leader_effect):
        # type: (str, str, LeaderEffect) -> None
        Skill.__init__(self, name, description, mpf("0"))
        self.leader_effect: LeaderEffect = leader_effect


class LeaderEffect:
    """
    This class contains attributes of leader skill effects.
    """

    def __init__(self, allies_max_hp_percentage_up, allies_max_magic_points_percentage_up,
                 allies_attack_power_percentage_up, allies_defense_percentage_up, allies_attack_speed_percentage_up,
                 allies_crit_rate_up, allies_crit_damage_up, allies_resistance_up, allies_accuracy_up):
        # type: (mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf) -> None
        self.allies_max_hp_percentage_up: mpf = allies_max_hp_percentage_up
        self.allies_max_magic_points_percentage_up: mpf = allies_max_magic_points_percentage_up
        self.allies_attack_power_percentage_up: mpf = allies_attack_power_percentage_up
        self.allies_defense_percentage_up: mpf = allies_defense_percentage_up
        self.allies_attack_speed_percentage_up: mpf = allies_attack_speed_percentage_up
        self.allies_crit_rate_up: mpf = allies_crit_rate_up
        self.allies_crit_damage_up: mpf = allies_crit_damage_up
        self.allies_resistance_up: mpf = allies_resistance_up
        self.allies_accuracy_up: mpf = allies_accuracy_up

    def clone(self):
        # type: () -> LeaderEffect
        return copy.deepcopy(self)


class SpecialPower(Skill):
    """
    This class contains attributes of special powers heroes have.
    """

    def __init__(self, name, description, damage_multiplier, max_cooltime, does_ignore_enemies_defense):
        # type: (str, str, DamageMultiplier, int, bool) -> None
        Skill.__init__(self, name, description, mpf("0"))
        self.damage_multiplier: DamageMultiplier = damage_multiplier
        self.cooltime: int = max_cooltime
        self.max_cooltime: int = max_cooltime
        self.does_ignore_enemies_defense: bool = does_ignore_enemies_defense


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
        self.leader: Hero or None = self.__heroes_list[0]
        self.team_effects_applied: bool = False  # initial value

    def set_leader(self, hero):
        # type: (Hero) -> bool
        if hero in self.__heroes_list:
            self.leader = hero
            return True
        return False

    def add_hero(self, hero):
        # type: (Hero) -> bool
        if len(self.__heroes_list) < self.MAX_HEROES:
            self.__heroes_list.append(hero)
            hero.curr_team = self
            return True
        return False

    def remove_hero(self, hero):
        # type: (Hero) -> bool
        if hero in self.__heroes_list:
            self.__heroes_list.remove(hero)
            if hero == self.leader:
                if len(self.__heroes_list) > 0:
                    self.leader = self.__heroes_list[0]
                else:
                    self.leader = None

            hero.curr_team = None

            return True
        return False

    def apply_team_effects(self):
        # type: () -> bool
        if not self.team_effects_applied:
            # TODO: apply stat increase effects to team members
            self.team_effects_applied = True
            return True
        return False

    def remove_team_effects(self):
        # type: () -> bool
        if self.team_effects_applied:
            for hero in self.__heroes_list:
                hero.battle_attack_power_percentage_up = mpf("0")
                hero.battle_max_hp_percentage_up = mpf("0")
                hero.battle_defense_percentage_up = mpf("0")
                hero.battle_max_magic_points_percentage_up = mpf("0")
                hero.battle_accuracy_up = mpf("0")
                hero.battle_resistance_up = mpf("0")

            self.team_effects_applied = False
            return True
        return False

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
    POSSIBLE_SET_NAMES: list = ["LIFE", "BEAST", "BLADE", "HAVOC", "IRON", "MAGIC", "ERUPTION", "FOCUS", "RESISTANCE",
                                "VAMPIRE", "VIOLENT", "SHIELD", "REVENGE", "DESPAIR", "NEMESIS", "WILL", "DESTROY",
                                "FIGHT", "DETERMINATION", "ENHANCE", "ACCURACY", "TOLERANCE", "SKILL", "REFLECT"]
    POSSIBLE_PRIMARY_ATTRIBUTES: list = ["ATTACK POWER", "ATTACK POWER PERCENTAGE", "MAX HP", "MAX HP PERCENTAGE",
                                         "DEFENSE", "DEFENSE PERCENTAGE", "MAX MAGIC POINTS",
                                         "MAX MAGIC POINTS PERCENTAGE"]

    def __init__(self, name, description, coin_cost, rating, slot_number, set_name, primary_attribute):
        # type: (str, str, mpf, int, int, str, str) -> None
        Item.__init__(self, name, description, coin_cost)
        self.rating: int = rating if self.MIN_RATING <= rating <= self.MAX_RATING else self.MIN_RATING
        self.slot_number: int = slot_number if self.MIN_SLOT_NUMBER <= slot_number <= self.MAX_SLOT_NUMBER \
            else self.MIN_SLOT_NUMBER
        self.set_name: str = set_name if set_name in self.POSSIBLE_SET_NAMES else self.POSSIBLE_SET_NAMES[0]
        self.gear_type: str = str(self.POSSIBLE_GEAR_TYPES[self.slot_number - 1])
        self.level: int = 0
        self.primary_attribute: str = primary_attribute
        self.set_effect: SetEffect = SetEffect(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, False, 0, 0, 0, 0, 0, 0)
        self.update_set_effect()
        self.set_effect_is_active: bool = False  # initial value
        self.level_up_coin_cost: mpf = coin_cost
        self.level_up_success_rate: mpf = mpf("1")
        self.set_size: int = 2 if self.set_name in ["LIFE", "BLADE", "IRON", "MAGIC", "FOCUS", "RESISTANCE",
                                                    "SHIELD", "REVENGE", "WILL", "DESTROY", "FIGHT",
                                                    "DETERMINATION", "ENHANCE", "ACCURACY", "TOLERANCE", "SKILL",
                                                    "REFLECT"] else 4

    def update_set_effect(self):
        # type: () -> None
        if self.set_name == "LIFE":
            self.set_effect.max_hp_percentage_up = mpf("17")
        elif self.set_name == "BEAST":
            self.set_effect.attack_power_percentage_up = mpf("35")
        elif self.set_name == "BLADE":
            self.set_effect.crit_rate_up = mpf("0.12")
        elif self.set_name == "HAVOC":
            self.set_effect.crit_damage_up = mpf("0.4")
        elif self.set_name == "IRON":
            self.set_effect.defense_percentage_up = mpf("17")
        elif self.set_name == "MAGIC":
            self.set_effect.max_magic_points_percentage_up = mpf("17")
        elif self.set_name == "ERUPTION":
            self.set_effect.attack_speed_percentage_up = mpf("25")
        elif self.set_name == "FOCUS":
            self.set_effect.accuracy_up = mpf("0.2")
        elif self.set_name == "RESISTANCE":
            self.set_effect.resistance_up = mpf("0.2")
        elif self.set_name == "VAMPIRE":
            self.set_effect.life_drain_percentage_up = mpf("35")
        elif self.set_name == "VIOLENT":
            self.set_effect.extra_turn_chance_up = mpf("0.22")
        elif self.set_name == "SHIELD":
            self.set_effect.ally_shield_amount_percentage_up = mpf("15")
        elif self.set_name == "REVENGE":
            self.set_effect.counterattack_chance_up = mpf("0.15")
        elif self.set_name == "DESPAIR":
            self.set_effect.stun_rate_up = mpf("0.25")
        elif self.set_name == "NEMESIS":
            self.set_effect.attack_gauge_up_per_hp_percentage_down = mpf("0.0175")
        elif self.set_name == "WILL":
            self.set_effect.starting_turns_with_immunity = 1
        elif self.set_name == "DESTROY":
            self.set_effect.does_reduce_enemies_max_hp = True
        elif self.set_name == "FIGHT":
            self.set_effect.allies_attack_power_percentage_up = mpf("8")
        elif self.set_name == "DETERMINATION":
            self.set_effect.allies_defense_percentage_up = mpf("8")
        elif self.set_name == "ENHANCE":
            self.set_effect.allies_max_hp_percentage_up = mpf("8")
        elif self.set_name == "ACCURACY":
            self.set_effect.allies_accuracy_up = mpf("0.1")
        elif self.set_name == "TOLERANCE":
            self.set_effect.allies_resistance_up = mpf("0.1")
        elif self.set_name == "SKILL":
            self.set_effect.allies_max_magic_points_percentage_up = mpf("8")
        elif self.set_name == "REFLECT":
            self.set_effect.reflected_damage_percentage_up = mpf("17")
        else:
            pass  # do nothing


class SetEffect:
    """
    This class contains attributes of gear set effect.
    """

    def __init__(self, max_hp_percentage_up, max_magic_points_percentage_up, attack_power_percentage_up, defense_percentage_up,
                 attack_speed_percentage_up, crit_rate_up, crit_damage_up, resistance_up, accuracy_up,
                 life_drain_percentage_up, extra_turn_chance_up, counterattack_chance_up, stun_rate_up,
                 ally_shield_amount_percentage_up, attack_gauge_up_per_hp_percentage_down, starting_turns_with_immunity,
                 does_reduce_enemies_max_hp, allies_attack_power_percentage_up, allies_defense_percentage_up,
                 allies_max_hp_percentage_up, allies_accuracy_up, allies_resistance_up,
                 allies_max_magic_points_percentage_up, reflected_damage_percentage_up):
        # type: (mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, int, bool, mpf, mpf, mpf, mpf, mpf, mpf, mpf) -> None
        self.max_hp_percentage_up: mpf = max_hp_percentage_up
        self.max_magic_points_percentage_up: mpf = max_magic_points_percentage_up
        self.attack_power_percentage_up: mpf = attack_power_percentage_up
        self.defense_percentage_up: mpf = defense_percentage_up
        self.attack_speed_percentage_up: mpf = attack_speed_percentage_up
        self.crit_rate_up: mpf = crit_rate_up
        self.crit_damage_up: mpf = crit_damage_up
        self.resistance_up: mpf = resistance_up
        self.accuracy_up: mpf = accuracy_up
        self.life_drain_percentage_up: mpf = life_drain_percentage_up
        self.extra_turn_chance_up: mpf = extra_turn_chance_up
        self.counterattack_chance_up: mpf = counterattack_chance_up
        self.stun_rate_up: mpf = stun_rate_up
        self.ally_shield_amount_percentage_up: mpf = ally_shield_amount_percentage_up
        self.attack_gauge_up_per_hp_percentage_down: mpf = attack_gauge_up_per_hp_percentage_down
        self.starting_turns_with_immunity: int = starting_turns_with_immunity
        self.does_reduce_enemies_max_hp: bool = does_reduce_enemies_max_hp  # True if destroy rune is used.
        self.allies_attack_power_percentage_up: mpf = allies_attack_power_percentage_up
        self.allies_defense_percentage_up: mpf = allies_defense_percentage_up
        self.allies_max_hp_percentage_up: mpf = allies_max_hp_percentage_up
        self.allies_accuracy_up: mpf = allies_accuracy_up
        self.allies_resistance_up: mpf = allies_resistance_up
        self.allies_max_magic_points_percentage_up: mpf = allies_max_magic_points_percentage_up
        self.reflected_damage_percentage_up: mpf = reflected_damage_percentage_up

    def clone(self):
        # type: () -> SetEffect
        return copy.deepcopy(self)


class StatIncrease:
    """
    This class contains attributes of increase of stats of a gear.
    """

    def __init__(self, max_hp_up, max_hp_percentage_up, max_magic_points_up, max_magic_points_percentage_up,
                 attack_up, attack_percentage_up, defense_up, defense_percentage_up, attack_speed_up, crit_rate_up,
                 crit_damage_up, resistance_up, accuracy_up):
        # type: (mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf) -> None
        self.max_hp_up: mpf = max_hp_up
        self.max_hp_percentage_up: mpf = max_hp_percentage_up
        self.max_magic_points_up: mpf = max_magic_points_up
        self.max_magic_points_percentage_up: mpf = max_magic_points_percentage_up
        self.attack_up: mpf = attack_up
        self.attack_percentage_up: mpf = attack_percentage_up
        self.defense_up: mpf = defense_up
        self.defense_percentage_up: mpf = defense_percentage_up
        self.attack_speed_up: mpf = attack_speed_up
        self.crit_rate_up: mpf = crit_rate_up
        self.crit_damage_up: mpf = crit_damage_up
        self.resistance_up: mpf = resistance_up
        self.accuracy_up: mpf = accuracy_up

    def clone(self):
        # type: () -> StatIncrease
        return copy.deepcopy(self)


class Scroll(Item):
    """
    This class contains attributes of a scroll used to summon heroes.
    """

    def __init__(self, name, description, coin_cost, potential_heroes):
        # type: (str, str, mpf, list) -> None
        Item.__init__(self, name, description, coin_cost)
        self.__potential_heroes: list = potential_heroes

    def get_potential_heroes(self):
        # type: () -> list
        return self.__potential_heroes


class LimitBreakShard(Item):
    """
    This class contains attributes of a limit break shard to apply limit break to a hero in this game.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        Item.__init__(self, name, description, coin_cost)


class AwakenShard(Item):
    """
    This class contains attributes of an awaken shard used to awaken a hero in this game.
    """

    def __init__(self, name, description, coin_cost, id_of_hero_to_awaken):
        # type: (str, str, mpf, str) -> None
        Item.__init__(self, name, description, coin_cost)
        self.id_of_hero_to_awaken: str = id_of_hero_to_awaken


class SummoningPiece(Item):
    """
    This class contains attributes of a summoning piece to summon a hero in this game.
    """

    def __init__(self, name, description, coin_cost, id_of_hero_to_summon):
        # type: (str, str, mpf, str) -> None
        Item.__init__(self, name, description, coin_cost)
        self.id_of_hero_to_summon: str = id_of_hero_to_summon


class PowerUpStone(Item):
    """
    This class contains attributes of a power-up stone to increase chances of levelling up gears.
    """

    def __init__(self, name, description, coin_cost, level_up_success_rate_up):
        # type: (str, str, mpf, mpf) -> None
        Item.__init__(self, name, description, coin_cost)
        self.level_up_success_rate_up: mpf = level_up_success_rate_up


class EXPShard(Item):
    """
    This class contains attributes of an EXP shard used to increase the EXP of a hero in this game.
    """

    def __init__(self, name, description, coin_cost, exp_gain):
        # type: (str, str, mpf, mpf) -> None
        Item.__init__(self, name, description, coin_cost)
        self.level: int = 1
        self.exp_gain: mpf = exp_gain
        self.level_up_coin_cost: mpf = coin_cost


class LevelUpShard(Item):
    """
    This class contains attributes of a level up shard used to level up a hero in this game.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        Item.__init__(self, name, description, coin_cost)


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
        self.update_rank()
        self.battle_team: Team = Team()
        self.item_inventory: Inventory = Inventory()

    def update_rank(self):
        # type: () -> None
        """
        Updates the rank of the player based on arena points.
        :return: None
        """

        if self.arena_points < 1100:
            self.rank = Rank("BEGINNER")
        elif 1100 <= self.arena_points < 1200:
            self.rank = Rank("CHALLENGER")
        elif 1200 <= self.arena_points < 1400:
            self.rank = Rank("FIGHTER")
        elif 1400 <= self.arena_points < 1700:
            self.rank = Rank("CONQUEROR")
        elif 1700 <= self.arena_points < 2100:
            self.rank = Rank("GUARDIAN")
        else:
            self.rank = Rank("LEGEND")

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

    def get_tile_at(self, x, y):
        # type: (int, int) -> Tile or None
        if x < 0 or x >= self.ISLAND_WIDTH or y < 0 or y >= self.ISLAND_HEIGHT:
            return None
        return self.__tiles[y][x]

    def set_tile(self, x, y, tile):
        # type: (int, int, Tile) -> bool
        if isinstance(self.get_tile_at(x, y), Tile):
            curr_tile: Tile = self.get_tile_at(x, y)
            curr_tile = tile
            return True
        return False

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

    def __init__(self, name, description, coin_cost, coin_per_second):
        # type: (str, str, mpf, mpf) -> None
        Building.__init__(self, name, description, coin_cost)
        self.coin_per_second: mpf = coin_per_second


class PowerUpCircle(Building):
    """
    This class contains attributes of a power-up circle used to power up heroes in this game.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        Building.__init__(self, name, description, coin_cost)


class ItemShop(Building):
    """
    This class contains attributes of shops selling items to players.
    """

    def __init__(self, name, description, coin_cost, items_sold):
        # type: (str, str, mpf, list) -> None
        Building.__init__(self, name, description, coin_cost)
        self.__items_sold: list = items_sold

    def get_items_sold(self):
        # type: () -> list
        return self.__items_sold


class Summonhenge(Building):
    """
    This class contains attributes of a summonhenge used to summon heroes.
    """

    def __init__(self, name, description, coin_cost):
        # type: (str, str, mpf) -> None
        Building.__init__(self, name, description, coin_cost)


class TempleOfWishes(Building):
    """
    This class contains attributes of temple of wishes for lucky draws.
    """

    def __init__(self, name, description, coin_cost, potential_rewards):
        # type: (str, str, mpf, list) -> None
        Building.__init__(self, name, description, coin_cost)
        self.__potential_rewards: list = potential_rewards

    def get_potential_rewards(self):
        # type: () -> list
        return self.__potential_rewards


class TrainingCenter(Building):
    """
    This class contains attributes of a training center to increase heroes' EXP.
    """

    def __init__(self, name, description, coin_cost, hero_exp_per_second):
        # type: (str, str, mpf, mpf) -> None
        Building.__init__(self, name, description, coin_cost)
        self.hero_exp_per_second: mpf = hero_exp_per_second


class Trainer(Player):
    """
    This class contains attributes of trainers to play against the player in the arena.
    """

    def __init__(self, name):
        # type: (str) -> None
        Player.__init__(self, name)
        self.times_beaten: int = 0

    def get_beaten(self):
        # type: () -> None
        for i in range(2 ** self.times_beaten):
            for hero in self.battle_team.get_heroes_list():
                hero.exp = hero.required_exp
                hero.level_up()

        self.times_beaten += 1


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

    POSSIBLE_NAMES: list = ["INCREASE ATTACK", "INCREASE DEFENSE", "INCREASE CRIT RATE", "INCREASE CRIT RESIST",
                            "INCREASE ATTACK SPEED", "HEAL OVER TIME", "COUNTER", "IMMUNITY", "INVINCIBLE",
                            "REFLECT DAMAGE", "SHIELD", "ENDURE"]

    def __init__(self, name, number_of_turns):
        # type: (str, int) -> None
        self.name: str = name if name in self.POSSIBLE_NAMES else self.POSSIBLE_NAMES[0]
        self.number_of_turns: int = number_of_turns
        self.attack_percentage_up: mpf = mpf("50") if self.name == "INCREASE ATTACK" else 0
        self.defense_percentage_up: mpf = mpf("50") if self.name == "INCREASE DEFENSE" else 0
        self.crit_rate_up: mpf = mpf("0.3") if self.name == "INCREASE CRIT RATE" else 0
        self.crit_resist_up: mpf = mpf("0.5") if self.name == "INCREASE CRIT RESIST" else 0
        self.attack_speed_percentage_up: mpf = mpf("33") if self.name == "INCREASE ATTACK SPEED" else 0
        self.recovery_percentage_per_turn_up: mpf = mpf("15") if self.name == "HEAL OVER TIME" else 0
        self.counterattack_chance_up: mpf = mpf("0.75") if self.name == "COUNTER" else 0
        self.prevents_debuffs: bool = self.name == "IMMUNITY"
        self.prevents_damage: bool = self.name == "INVINCIBLE"
        self.reflected_damage_percentage_up: mpf = mpf("30") if self.name == "REFLECT DAMAGE" else 0
        self.shield_amount_percentage_up: mpf = mpf("15") if self.name == "SHIELD" else 0
        self.prevents_death: bool = self.name == "ENDURE"

    def clone(self):
        # type: () -> Buff
        return copy.deepcopy(self)


class Debuff:
    """
    This class contains attributes of harmful effects in this game.
    """

    POSSIBLE_NAMES: list = ["GLANCING HIT", "DECREASE ATTACK", "DECREASE DEFENSE", "DECREASE ATTACK SPEED",
                            "BENEFICIAL EFFECTS BLOCKED", "SLEEP", "DAMAGE OVER TIME", "FREEZE", "STUN",
                            "UNRECOVERABLE", "SILENCE", "BRAND", "OBLIVION"]

    def __init__(self, name, number_of_turns):
        # type: (str, int) -> None
        self.name: str = name if name in self.POSSIBLE_NAMES else self.POSSIBLE_NAMES[0]
        self.number_of_turns: int = number_of_turns
        self.glancing_hit_chance_up: mpf = mpf("0.5") if self.name == "GLANCING HIT" else 0
        self.attack_power_percentage_down: mpf = mpf("50") if self.name == "DECREASE ATTACK" else 0
        self.defense_percentage_down: mpf = mpf("50") if self.name == "DECREASE DEFENSE" else 0
        self.attack_speed_percentage_down: mpf = mpf("33") if self.name == "DECREASE ATTACK SPEED" else 0
        self.blocks_buffs: bool = self.name == "BENEFICIAL EFFECTS BLOCKED"
        self.prevents_turn: bool = self.name in ["SLEEP", "FREEZE", "STUN"]
        self.can_be_awake_when_attacked: bool = self.name == "SLEEP"
        self.prevents_cooltime_from_running: bool = self.name == "STUN"
        self.damage_over_time_percentage: mpf = mpf("15") if self.name == "DAMAGE OVER TIME" else 0
        self.blocks_heal: bool = self.name == "UNRECOVERABLE"
        self.prevents_active_skills: bool = self.name == "SILENCE"
        self.additional_damage_percentage_received_up: mpf = mpf("25") if self.name == "BRAND" else 0
        self.prevents_passive_skills: bool = self.name == "OBLIVION"

    def clone(self):
        # type: () -> Debuff
        return copy.deepcopy(self)


class Reward:
    """
    This class contains attributes of rewards gained for doing something in the game.
    """

    def __init__(self, player_coin_gain, player_exp_gain, hero_exp_gain, player_items_gain, player_heroes_gain):
        # type: (mpf, mpf, mpf, list, list) -> None
        self.player_coin_gain: mpf = player_coin_gain
        self.player_exp_gain: mpf = player_exp_gain
        self.hero_exp_gain: mpf = hero_exp_gain
        self.__player_items_gain: list = player_items_gain
        self.__player_heroes_gain: list = player_heroes_gain

    def get_player_items_gain(self):
        # type: () -> list
        return self.__player_items_gain

    def get_player_heroes_gain(self):
        # type: () -> list
        return self.__player_heroes_gain

    def clone(self):
        # type: () -> Reward
        return copy.deepcopy(self)


class DamageMultiplier:
    """
    This class contains attributes of damage multiplier.
    """

    def __init__(self, multiplier_to_self_max_hp, multiplier_to_enemy_max_hp, multiplier_to_self_attack_power,
                 multiplier_to_enemy_attack_power, multiplier_to_self_defense, multiplier_to_enemy_defense,
                 multiplier_to_self_max_magic_points, multiplier_to_enemy_max_magic_points,
                 multiplier_to_self_attack_speed, multiplier_to_enemy_attack_speed,
                 multiplier_to_current_self_hp_percentage, multiplier_to_self_hp_percentage_loss,
                 multiplier_to_current_enemies_hp_percentage, multiplier_to_enemies_hp_percentage_loss,
                 multiplier_to_number_of_dead_allies, multiplier_to_number_of_dead_enemies,
                 multiplier_to_number_of_turns_gained, multiplier_to_number_of_self_buffs,
                 multiplier_to_number_of_enemies_debuffs, damage_increase_percentage_to_enemies_without_buffs):
        # type: (mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf, mpf) -> None
        self.multiplier_to_self_max_hp: mpf = multiplier_to_self_max_hp
        self.multiplier_to_enemy_max_hp: mpf = multiplier_to_enemy_max_hp
        self.multiplier_to_self_attack_power: mpf = multiplier_to_self_attack_power
        self.multiplier_to_enemy_attack_power: mpf = multiplier_to_enemy_attack_power
        self.multiplier_to_self_defense: mpf = multiplier_to_self_defense
        self.multiplier_to_enemy_defense: mpf = multiplier_to_enemy_defense
        self.multiplier_to_self_max_magic_points: mpf = multiplier_to_self_max_magic_points
        self.multiplier_to_enemy_max_magic_points: mpf = multiplier_to_enemy_max_magic_points
        self.multiplier_to_self_attack_speed: mpf = multiplier_to_self_attack_speed
        self.multiplier_to_enemy_attack_speed: mpf = multiplier_to_enemy_attack_speed
        self.multiplier_to_current_self_hp_percentage: mpf = multiplier_to_current_self_hp_percentage
        self.multiplier_to_self_hp_percentage_loss: mpf = multiplier_to_self_hp_percentage_loss
        self.multiplier_to_current_enemies_hp_percentage: mpf = multiplier_to_current_enemies_hp_percentage
        self.multiplier_to_enemies_hp_percentage_loss: mpf = multiplier_to_enemies_hp_percentage_loss
        self.multiplier_to_number_of_dead_allies: mpf = multiplier_to_number_of_dead_allies
        self.multiplier_to_number_of_dead_enemies: mpf = multiplier_to_number_of_dead_enemies
        self.multiplier_to_number_of_turns_gained: mpf = multiplier_to_number_of_turns_gained
        self.multiplier_to_number_of_self_buffs: mpf = multiplier_to_number_of_self_buffs
        self.multiplier_to_number_of_enemies_debuffs: mpf = multiplier_to_number_of_enemies_debuffs
        self.damage_increase_percentage_to_enemies_without_buffs: mpf = damage_increase_percentage_to_enemies_without_buffs

    def calculate_normal_raw_damage_without_enemy_defense(self, user, target):
        # type: (Hero, Hero) -> mpf
        if isinstance(user.curr_team, Team) and isinstance(target.curr_team, Team):
            user_team: Team = user.curr_team
            target_team: Team = target.curr_team
            actual_user_max_hp: mpf = user.max_hp * (1 + user.battle_max_hp_percentage_up / 100 -
                                                     user.battle_max_hp_percentage_down / 100)
            actual_user_attack_power: mpf = user.attack_power * (1 + user.battle_attack_power_percentage_up / 100 -
                                                                 user.battle_attack_power_percentage_down / 100)
            actual_user_defense: mpf = user.defense * (1 + user.battle_defense_percentage_up / 100 -
                                                       user.battle_defense_percentage_down / 100)
            actual_user_attack_speed: mpf = user.attack_speed * (1 + user.battle_attack_speed_percentage_up / 100 -
                                                                 user.battle_attack_speed_percentage_down / 100)
            actual_target_max_hp: mpf = target.max_hp * (1 + target.battle_max_hp_percentage_up / 100 -
                                                     target.battle_max_hp_percentage_down / 100)
            actual_target_attack_power: mpf = target.attack_power * (1 + target.battle_attack_power_percentage_up / 100 -
                                                                 target.battle_attack_power_percentage_down / 100)
            actual_target_defense: mpf = target.defense * (1 + target.battle_defense_percentage_up / 100 -
                                                       target.battle_defense_percentage_down / 100)
            actual_target_attack_speed: mpf = target.attack_speed * (1 + target.battle_attack_speed_percentage_up / 100 -
                                                                 target.battle_attack_speed_percentage_down / 100)
            current_user_hp_percentage: mpf = (user.curr_hp / user.max_hp) * 100
            current_target_hp_percentage: mpf = (target.curr_hp / target.max_hp) * 100
            user_hp_percentage_loss: mpf = 100 - current_user_hp_percentage
            target_hp_percentage_loss: mpf = 100 - current_target_hp_percentage
            number_of_dead_allies: int = len([hero for hero in user_team.get_heroes_list() if hero != user and
                                              not hero.get_is_alive()])
            number_of_dead_enemies: int = len([hero for hero in target_team.get_heroes_list() if hero != target and
                                              not target.get_is_alive()])
            number_of_turns_gained: int = user.turns_gained
            number_of_user_buffs: int = len(user.get_buffs())
            number_of_target_debuffs: int = len(target.get_debuffs())
            target_without_buffs: int = 1 if len(target.get_buffs()) == 0 else 0
            target_additional_damage_percentage_received: mpf = target.battle_additional_damage_percentage_received
            return (actual_user_max_hp * self.multiplier_to_self_max_hp + actual_target_max_hp *
                    self.multiplier_to_enemy_max_hp + actual_user_attack_power * (self.multiplier_to_self_attack_power +
                    (actual_user_attack_speed * self.multiplier_to_self_attack_speed)) + actual_target_attack_power *
                    (self.multiplier_to_enemy_attack_power + (actual_target_attack_speed *
                    self.multiplier_to_enemy_attack_speed)) + actual_user_defense * self.multiplier_to_self_defense +
                    actual_target_defense * self.multiplier_to_enemy_defense + user.max_magic_points *
                    self.multiplier_to_self_max_magic_points + target.max_magic_points *
                    self.multiplier_to_enemy_max_magic_points) * (1 + current_user_hp_percentage *
                    self.multiplier_to_current_self_hp_percentage) * (1 + current_target_hp_percentage *
                    self.multiplier_to_current_enemies_hp_percentage) * (1 + user_hp_percentage_loss *
                    self.multiplier_to_self_hp_percentage_loss) * (1 + target_hp_percentage_loss *
                    self.multiplier_to_enemies_hp_percentage_loss) * (1 + number_of_dead_allies *
                    self.multiplier_to_number_of_dead_allies) * (1 + number_of_dead_enemies *
                    self.multiplier_to_number_of_dead_enemies) * (1 + number_of_turns_gained *
                    self.multiplier_to_number_of_turns_gained) * (1 + number_of_user_buffs *
                    self.multiplier_to_number_of_self_buffs) * (1 + number_of_target_debuffs *
                    self.multiplier_to_number_of_enemies_debuffs) * (1 + target_without_buffs *
                    self.damage_increase_percentage_to_enemies_without_buffs) * \
                    (1 + target_additional_damage_percentage_received / 100)
        return mpf("0")  # attack is unsuccessful

    def calculate_normal_raw_damage(self, user, target):
        # type: (Hero, Hero) -> mpf
        actual_target_defense: mpf = target.defense * (1 + target.battle_defense_percentage_up / 100 -
                                                       target.battle_defense_percentage_down / 100)
        return self.calculate_normal_raw_damage_without_enemy_defense(user, target) - actual_target_defense

    def calculate_critical_raw_damage_without_enemy_defense(self, user, target):
        # type: (Hero, Hero) -> mpf
        return self.calculate_normal_raw_damage_without_enemy_defense(user, target) * (1 + user.crit_damage)

    def calculate_critical_raw_damage(self, user, target):
        # type: (Hero, Hero) -> mpf
        actual_target_defense: mpf = target.defense * (1 + target.battle_defense_percentage_up / 100 -
                                                       target.battle_defense_percentage_down / 100)
        return self.calculate_critical_raw_damage_without_enemy_defense(user, target) - actual_target_defense

    def clone(self):
        # type: () -> DamageMultiplier
        return copy.deepcopy(self)


class Game:
    """
    This class contains attributes of saved game data.
    """

    def __init__(self, player, opponent_trainers, battle_areas, potential_heroes):
        # type: (Player, list, list, list) -> None
        self.player: Player = player
        self.__opponent_trainers: list = opponent_trainers
        self.__battle_areas: list = battle_areas
        self.__potential_heroes: list = potential_heroes

    def get_opponent_trainers(self):
        # type: () -> list
        return self.__opponent_trainers

    def get_battle_areas(self):
        # type: () -> list
        return self.__battle_areas

    def get_potential_heroes(self):
        # type: () -> list
        return self.__potential_heroes

    def clone(self):
        # type: () -> Game
        return copy.deepcopy(self)


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
