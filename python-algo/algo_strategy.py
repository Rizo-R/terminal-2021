import gamelib
import random
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.left_columns = [0, 1, 2, 3, 4]
        self.right_columns = [27, 26, 25, 24, 23]
        self.enemy_side = list(range(14, 28))
        self.attack_direction = 0
        self.last_attacked = 0
        self.main_attack_locations = [[24, 10], [3, 10]]

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        self.game_state = game_state
        if game_state.turn_number < 2:
            self.top_left = game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT)
            self.top_right = game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.
        if self.turret_count_right(game_state) < self.turret_count_left(game_state):
            self.attack_direction = 1
        elif self.turret_count_left(game_state) < self.turret_count_right(game_state):
            self.attack_direction = 0
        elif self.wall_count_left(game_state)[1] < self.wall_count_right(game_state)[1]:
            self.attack_direction = 0
        elif self.wall_count_right(game_state)[1] < self.wall_count_left(game_state)[1]:
            self.attack_direction = 1
        elif self.least_damage_spawn_location(game_state, self.main_attack_locations) == [[3, 10]]:
            self.attack_direction = 0
        else:
            self.attack_direction = 1
        self.starter_strategy(game_state)
        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def min_wall_health_left(self, game_state):
        min_health = 0
        walls = [[1, 14], [2, 15], [3, 15], [2, 14], [3,14], [3,16]]
        for location in walls:
            for unit in game_state.game_map[location[0], location[1]]:
                min_health = min(min_health, unit.health)
        return min_health

    def min_wall_health_right(self, game_state):
        min_health = 0
        walls = [[26, 14], [26, 15], [25,14], [24,14], [25, 16], [25, 15]]
        for location in walls:
            for unit in game_state.game_map[location[0], location[1]]:
                min_health = min(min_health, unit.health)
        return min_health


    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        # Now build reactive defenses based on where the enemy scored
        # self.build_reactive_defense(game_state)
        defensive_bias = 0
        left_walls = [[3, 12], [4, 11]]
        right_walls = [[23, 11], [24, 12]]
        left_health = 0
        left_maxhealth = 0
        right_health = 0
        right_maxhealth = 0
        for x in left_walls:
            left_health += self.check_health(game_state, x)[0]
            left_maxhealth += self.check_health(game_state, x)[1]
        for x in right_walls:
            right_health += self.check_health(game_state, x)[0]
            right_maxhealth += self.check_health(game_state, x)[1]
        unit_type = SCOUT
        wait = 0
        if game_state.turn_number < 4:
            timing = 1
            support_exists = 1
            lane_clear = 1
        elif game_state.turn_number < 20:
            timing = 0
            wait = 6
        elif game_state.turn_number < 35:
            wait = 6
            timing = game_state.turn_number - self.last_attacked >= wait
        else:
            wait = 5
            timing = game_state.turn_number - self.last_attacked >= wait
        if game_state.turn_number < 5:
            unit_type = INTERCEPTOR
        if self.attack_direction == 0 and self.turret_count_left(game_state) == 0 and self.wall_count_left(
                game_state)[0] > 2:
            unit_type = DEMOLISHER
        elif self.attack_direction == 1 and self.turret_count_right(game_state) == 0 and self.wall_count_right(
                game_state)[0] > 2:
            unit_type = DEMOLISHER
        if unit_type == DEMOLISHER:
            if self.attack_direction == 0:
                min_health = self.min_wall_health_left(game_state)
                quantity = int(round(min_health/60, 0))
                wait = quantity + wait
                timing = game_state.turn_number - self.last_attacked >= wait
            else:
                min_health = self.min_wall_health_right(game_state)
                quantity = int(round(min_health/60, 0))
                wait = quantity + wait
                timing = game_state.turn_number - self.last_attacked >= wait
        if game_state.turn_number > 3:
            lane_clear = ((self.attack_direction == 0 and not game_state.contains_stationary_unit([2, 11])) or
                          self.attack_direction == 1 and not game_state.contains_stationary_unit([25, 11]))
            left_supports = [[5, 10], [6, 9]]
            right_supports = [[22, 10], [21, 9]]
            support_exists = ((self.attack_direction == 0 and self.check_position_upgrades(left_supports, game_state)) or
                              (self.attack_direction == 1 and self.check_position_upgrades(right_supports, game_state)))
        attack_conditions = timing and lane_clear and support_exists
        if game_state.contains_stationary_unit([2, 11]):
            lane_blocked = 0
        elif game_state.contains_stationary_unit([25, 11]):
            lane_blocked = 1
        else:
            lane_blocked = -1
        self.build_defences(game_state, lane_blocked)
        if attack_conditions:
            self.last_attacked = game_state.turn_number
            if self.attack_direction == 0:
                best_location = [24, 10]
                double_up_location = [23, 9]
            else:
                best_location = [3, 10]
                double_up_location = [4, 9]
            if unit_type == DEMOLISHER:
                if best_location == [3, 10]:
                    double_up_location = [16, 2]
                else:
                    double_up_location = [11, 2]
                game_state.attempt_spawn(unit_type, double_up_location, quantity)
                game_state.attempt_spawn(SCOUT, best_location, 10000)
            else:
                game_state.attempt_spawn(SCOUT, best_location, 10000)

    def check_position_upgrades(self, positions: list, game_state: gamelib.GameState):
        for location in positions:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location[0], location[1]]:
                    if unit.stationary:
                        existing_unit = unit
                    else:
                        return False
                    if not existing_unit.upgraded:
                        return False
            else:
                return False
        return True


    def build_support(self, game_state):
        support_locations1 = [[13, 3], [14, 3]]
        support_locations2 = [[12, 4], [15, 4]]
        support_locations3 = [[11, 4], [16, 4]]
        support_locations4 = [[10, 5], [17, 5]]
        support_locations5 = [[9, 6], [18, 6]]
        support_locations6 = [[8, 7], [19, 7]]
        support_locations7 = [[7, 8], [20, 8]]
        support_locations8 = [[6, 9], [21, 9]]
        support_locations9 = [[5, 10], [22, 10]]
        game_state.attempt_spawn(WALL, support_locations1)
        game_state.attempt_spawn(WALL, support_locations2)
        game_state.attempt_spawn(WALL, support_locations3)
        game_state.attempt_spawn(WALL, support_locations4)
        self.check_health(game_state, support_locations5)
        game_state.attempt_spawn(SUPPORT, support_locations5)
        self.check_health(game_state, support_locations6)
        game_state.attempt_spawn(SUPPORT, support_locations6)
        self.check_health(game_state, support_locations7)
        game_state.attempt_spawn(SUPPORT, support_locations7)
        self.check_health(game_state, support_locations8)
        game_state.attempt_spawn(SUPPORT, support_locations8)
        self.check_health(game_state, support_locations9)
        game_state.attempt_spawn(SUPPORT, support_locations9)

    def upgrade_support(self, game_state, turrets, lane_blocked):
        support_locations5 = [[9, 6], [18, 6]]
        support_locations6 = [[8, 7], [19, 7]]
        support_locations7 = [[7, 8], [20, 8]]
        support_locations8 = [[6, 9], [21, 9]]
        support_locations9 = [[5, 10], [22, 10]]
        if lane_blocked == 0:
            dirx = 1
        elif lane_blocked == 1:
            dirx = 0
        else:
            dirx = -1
        if self.check_position_upgrades(turrets, game_state):
            game_state.attempt_upgrade(support_locations9[dirx])
        if self.check_position_upgrades([support_locations9[dirx]], game_state):
            game_state.attempt_upgrade(support_locations8[dirx])
        if self.check_position_upgrades([support_locations8[dirx]], game_state):
            game_state.attempt_upgrade(support_locations7[dirx])
        if self.check_position_upgrades([support_locations7[dirx]], game_state):
            game_state.attempt_upgrade(support_locations6[dirx])
        if self.check_position_upgrades([support_locations6[dirx]], game_state):
            game_state.attempt_upgrade(support_locations5[dirx])
        if self.check_position_upgrades(turrets, game_state):
            game_state.attempt_upgrade(support_locations9)
        if self.check_position_upgrades(support_locations9, game_state):
            game_state.attempt_upgrade(support_locations8)
        if self.check_position_upgrades(support_locations8, game_state):
            game_state.attempt_upgrade(support_locations7)
        if self.check_position_upgrades(support_locations7, game_state):
            game_state.attempt_upgrade(support_locations6)
        if self.check_position_upgrades(support_locations6, game_state):
            game_state.attempt_upgrade(support_locations5)

    def turret_count_left(self, game_state):
        turret_count = 0
        for x in self.left_columns:
            for y in [14, 15, 16, 17]:
                if game_state.contains_stationary_unit([x, y]):
                    for unit in game_state.game_map[x, y]:
                        if unit.player_index == 1 and unit.unit_type == TURRET:
                            turret_count += 1
        return turret_count

    def wall_count_left(self, game_state):
        turret_count = 0
        upgraded_count = 0
        for x in self.left_columns:
            for y in [14, 15, 16, 17]:
                if game_state.contains_stationary_unit([x, y]):
                    for unit in game_state.game_map[x, y]:
                        if unit.player_index == 1 and unit.unit_type == WALL:
                            turret_count += 1
                            if unit.upgraded:
                                upgraded_count += 1
        return turret_count, upgraded_count

    def turret_count_right(self, game_state):
        turret_count = 0
        for x in self.right_columns:
            for y in [14, 15, 16, 17]:
                if game_state.contains_stationary_unit([x, y]):
                    for unit in game_state.game_map[x, y]:
                        if unit.player_index == 1 and unit.unit_type == TURRET:
                            turret_count += 1
        return turret_count

    def wall_count_right(self, game_state):
        turret_count = 0
        upgraded_count = 0
        for x in self.right_columns:
            for y in [14, 15, 16, 17]:
                if game_state.contains_stationary_unit([x, y]):
                    for unit in game_state.game_map[x, y]:
                        if unit.player_index == 1 and unit.unit_type == WALL:
                            turret_count += 1
                            if unit.upgraded:
                                upgraded_count += 1
        return turret_count, upgraded_count

    def check_health(self, game_state, locations):
        if isinstance(locations[0], list):
            for loc in locations:
                if game_state.contains_stationary_unit(loc):
                    for unit in game_state.game_map[loc]:
                        if self.check_position_upgrades([loc], game_state):
                            if unit.health / unit.max_health <= 1/3:
                                game_state.attempt_remove(loc)
        else:
            loc = locations
            if game_state.contains_stationary_unit(loc):
                for unit in game_state.game_map[loc]:
                    if unit.health / unit.max_health <= 1 / 2:
                        game_state.attempt_remove(loc)
                    return unit.health, unit.max_health
        return 0, 1

    def reinforcement_turrets(self, game_state, lane_blocked):
        turret_locations = [[4, 11], [23, 11]]
        turret_locations4 = [[1, 12], [26, 12]]
        turret_locations2 = [[3, 12], [24, 12]]
        all_turrets = turret_locations + turret_locations2 + turret_locations4
        if self.check_position_upgrades(all_turrets, game_state):
            if lane_blocked == -1:
                self.check_health(game_state, [5, 11])
                game_state.attempt_spawn(TURRET, [5, 11])
                game_state.attempt_upgrade([5, 11])
                all_turrets = all_turrets + [[5, 11]]
                if self.check_position_upgrades(all_turrets, game_state):
                    self.check_health(game_state, [22, 11])
                    game_state.attempt_spawn(TURRET, [22, 11])
                    game_state.attempt_upgrade([22, 11])
                all_turrets = all_turrets + [[22, 11]]
                if self.check_position_upgrades(all_turrets, game_state):
                    self.check_health(game_state, [22, 12])
                    game_state.attempt_spawn(TURRET, [22, 12])
                    game_state.attempt_upgrade([22, 12])
                all_turrets = all_turrets + [[22, 12]]
                if self.check_position_upgrades(all_turrets, game_state):
                    self.check_health(game_state, [5, 12])
                    game_state.attempt_spawn(TURRET, [5, 12])
                    game_state.attempt_upgrade([5, 12])
            elif lane_blocked == 0:
                    self.check_health(game_state, [22, 11])
                    game_state.attempt_spawn(TURRET, [22, 11])
                    game_state.attempt_upgrade([22, 11])
                    all_turrets = all_turrets + [[22, 11]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [23, 12])
                        game_state.attempt_spawn(TURRET, [23, 12])
                        game_state.attempt_upgrade([23, 12])
                    all_turrets = all_turrets + [[23, 12]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [22, 12])
                        game_state.attempt_spawn(TURRET, [22, 12])
                        game_state.attempt_upgrade([22, 12])
                    all_turrets = all_turrets + [[22, 12]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [26, 13])
                        game_state.attempt_spawn(TURRET, [26, 13])
                        game_state.attempt_upgrade([26, 13])
                    all_turrets = all_turrets + [[26, 13]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [5, 11])
                        game_state.attempt_spawn(TURRET, [5, 11])
                        game_state.attempt_upgrade([5, 11])
                    all_turrets = all_turrets + [[5, 11]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [4, 12])
                        game_state.attempt_spawn(TURRET, [4, 12])
                        game_state.attempt_upgrade([4, 12])
                    all_turrets = all_turrets + [[4, 12]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [5, 12])
                        game_state.attempt_spawn(TURRET, [5, 12])
                        game_state.attempt_upgrade([5, 12])
            elif lane_blocked == 1:
                    self.check_health(game_state, [5, 11])
                    game_state.attempt_spawn(TURRET, [5, 11])
                    game_state.attempt_upgrade([5, 11])
                    all_turrets = all_turrets + [[5, 11]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [4, 12])
                        game_state.attempt_spawn(TURRET, [4, 12])
                        game_state.attempt_upgrade([4, 12])
                    all_turrets = all_turrets + [[4, 12]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [5, 12])
                        game_state.attempt_spawn(TURRET, [5, 12])
                        game_state.attempt_upgrade([5, 12])
                    all_turrets = all_turrets + [[5, 12]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [2, 13])
                        game_state.attempt_spawn(TURRET, [2, 13])
                        game_state.attempt_upgrade([2, 13])
                    all_turrets = all_turrets + [[2, 13]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [22, 11])
                        game_state.attempt_spawn(TURRET, [22, 11])
                        game_state.attempt_upgrade([22, 11])
                    all_turrets = all_turrets + [[22, 11]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [23, 12])
                        game_state.attempt_spawn(TURRET, [23, 12])
                        game_state.attempt_upgrade([23, 12])
                    all_turrets = all_turrets + [[23, 12]]
                    if self.check_position_upgrades(all_turrets, game_state):
                        self.check_health(game_state, [22, 12])
                        game_state.attempt_spawn(TURRET, [22, 12])
                        game_state.attempt_upgrade([22, 12])


    def build_defences(self, game_state, lane_blocked):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[4, 11], [23, 11]]

        turret_locations2 = [[0, 13], [27, 13]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        self.check_health(game_state, turret_locations)
        self.check_health(game_state, turret_locations2)
        game_state.attempt_spawn(TURRET, turret_locations)
        game_state.attempt_upgrade(turret_locations)
        if not lane_blocked == 0 and not lane_blocked == 1:
            turret_locations4 = [[1, 12], [26, 12]]
            turret_locations3 = [[3, 12], [24, 12]]
        elif lane_blocked == 0:
            turret_locations4 = [[24, 12], [26, 12]]
            turret_locations3 = [[3, 12], [1, 12]]
        elif lane_blocked == 1:
            turret_locations3 = [[24, 12], [26, 12]]
            turret_locations4 = [[3, 12], [1, 12]]
        if self.check_position_upgrades(turret_locations, game_state):
            self.check_health(game_state, turret_locations2)
            game_state.attempt_spawn(TURRET, turret_locations2)
            game_state.attempt_upgrade(turret_locations2)

            if self.check_position_upgrades(turret_locations + turret_locations2, game_state):
                self.check_health(game_state, turret_locations3)
                game_state.attempt_spawn(TURRET, turret_locations3)
                game_state.attempt_upgrade(turret_locations3)
            if self.check_position_upgrades(turret_locations + turret_locations2 + turret_locations3, game_state):
                self.check_health(game_state, turret_locations4)
                game_state.attempt_spawn(TURRET, turret_locations4)
                game_state.attempt_upgrade(turret_locations4)
            if self.attack_direction == 0:
                game_state.attempt_remove([2, 11])
                if not game_state.contains_stationary_unit([2, 11]):
                    game_state.attempt_spawn(WALL, [25, 11])
            else:
                game_state.attempt_remove([25, 11])
                if not game_state.contains_stationary_unit([25, 11]):
                    game_state.attempt_spawn(WALL, [2, 11])
            turrets = turret_locations + turret_locations2 + turret_locations3 + turret_locations4
            self.build_support(game_state)
            if game_state.turn_number < 20:
                self.upgrade_support(game_state, turrets, lane_blocked)
                self.reinforcement_turrets(game_state, lane_blocked)
            else:
                self.reinforcement_turrets(game_state, lane_blocked)
                self.upgrade_support(game_state, turrets, lane_blocked)




    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        paths = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i

            if path[-1] not in self.top_left + self.top_right:
                damage *= 2
            damages.append(damage)
            paths.append(len(path))
        if damages[0] == damages[1]:
            return location_options[paths.index(min(paths))]
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
