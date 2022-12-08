from types import SimpleNamespace
import requests
import json
import pprint
import pickle
import write_to_json

API_KEY = "8dd49bb13fb27f18e7f0f504e51cf5a3"


class Game:

    def __init__(self, game_dict):
        self.game_dict = game_dict

        self.game_id = self.game_dict.get('id')
        self.sport_title = self.game_dict.get('sport_title')
        self.commence_time = self.game_dict.get('commence_time')
        self.home_team = game_dict.get('home_team')
        self.away_team = game_dict.get('away_team')

        # List of dictionaries in form {'title': 'mybookieag', 'last_update': 'x', 'outcomes': [{'name': 'Cincinnati Bengals', 'price': 170}, {'name': 'Tennessee Titans', 'price': -192}]}
        self.h2h_markets = []
        self.spreads_markets = []
        self.totals_markets = []

        self.list_of_arbs = []
        self.list_of_h2h_arbs = []
        self.list_of_spread_arbs = []
        self.list_of_total_arbs = []
        self.list_of_ArbGroups = []
        self.list_of_ArbGroups_h2h = []
        self.list_of_ArbGroups_spreads = []
        self.list_of_ArbGroups_totals = []

        self.organize_markets()

        # print(f"Markets for {game_dict.get('home_team')} vs {game_dict.get('away_team')}:")
        # print(f"H2H markets: {self.h2h_markets}")
        # print(f"Spread markets: {self.spreads_markets}")
        # print(f"Totals markets: {self.totals_markets}")
        # print("\n")

        self.scan_for_arbs_h2h()
        self.merge_arbs_h2h()

        self.scan_for_arbs_spreads()
        self.merge_arbs_spreads()

        self.scan_for_arbs_totals()
        self.merge_arbs_totals()

        self.combine_arbgroup_lists_into_one()

    def combine_arbgroup_lists_into_one(self):
        for arb_group in self.list_of_ArbGroups_h2h:
            self.list_of_ArbGroups.append(arb_group)

        for arb_group in self.list_of_ArbGroups_spreads:
            self.list_of_ArbGroups.append(arb_group)

        for arb_group in self.list_of_ArbGroups_totals:
            self.list_of_ArbGroups.append(arb_group)

    def calculate_arbs_edge_h2h(self):
        for arb in self.list_of_h2h_arbs:
            arb.calculate_edge()

    def calculate_arbs_edge_spreads(self):
        for arb in self.list_of_spread_arbs:
            arb.calculate_edge()

    def organize_markets(self):
        for i in range(len(self.game_dict.get("bookmakers"))):
            title = self.game_dict.get("bookmakers")[i].get("title")
            last_update = self.game_dict.get("bookmakers")[i].get("last_update")

            h2h_market = None
            spread_market = None
            totals_market = None

            for j in range(len(self.game_dict.get("bookmakers")[i].get("markets"))):
                bet_type = self.game_dict.get("bookmakers")[i].get("markets")[j].get("key")
                if bet_type == "h2h":
                    h2h_market = self.game_dict.get("bookmakers")[i].get("markets")[j].get("outcomes")
                elif bet_type == "spreads":
                    spread_market = self.game_dict.get("bookmakers")[i].get("markets")[j].get("outcomes")
                elif bet_type == "totals":
                    totals_market = self.game_dict.get("bookmakers")[i].get("markets")[j].get("outcomes")

            if h2h_market is not None:
                h2h_dict = {'title': title, 'last_update': last_update, 'outcomes': h2h_market, 'game_id': self.game_id}
                self.h2h_markets.append(h2h_dict)
            if spread_market is not None:
                spread_dict = {'title': title, 'last_update': last_update, 'outcomes': spread_market,
                               'game_id': self.game_id}
                self.spreads_markets.append(spread_dict)
            if totals_market is not None:
                totals_dict = {'title': title, 'last_update': last_update, 'outcomes': totals_market,
                               'game_id': self.game_id}
                self.totals_markets.append(totals_dict)

    @staticmethod
    def get_implied_probability(odds):
        if odds <= 0:
            return -odds / (-odds + 100) * 100
        else:
            return 100 / (odds + 100) * 100

    def check_if_arb_h2h(self, home_odds, away_odds):

        home_implied_probability = self.get_implied_probability(home_odds)
        away_implied_probability = self.get_implied_probability(away_odds)
        if home_implied_probability + away_implied_probability < 100:
            edge = round(100 - (home_implied_probability + away_implied_probability), 2)
            return True, edge
        return False, 0

    def check_if_arb_with_point(self, home_odds, away_odds, home_point, away_point):

        if home_point == -1 * away_point:
            home_implied_probability = self.get_implied_probability(home_odds)
            away_implied_probability = self.get_implied_probability(away_odds)
            if home_implied_probability + away_implied_probability < 100:
                edge = round(100 - (home_implied_probability + away_implied_probability), 2)
                return True, edge
            return False, 0
        return False, 0

    def merge_arbs_spreads(self):

        for arb in self.list_of_spread_arbs:
            if self.is_arb_in_arb_group_spreads(arb):
                pass
            else:
                self.find_spot_for_arb_in_ArbGroups_spreads(arb)

    def merge_arbs_h2h(self):
        for arb in self.list_of_h2h_arbs:
            if self.is_arb_in_arb_group_h2h(arb):
                pass
            else:
                self.find_spot_for_arb_in_ArbGroups_h2h(arb)

    def merge_arbs_totals(self):
        for arb in self.list_of_total_arbs:
            if self.is_arb_in_arb_group_totals(arb):
                pass
            else:
                self.find_spot_for_arb_in_ArbGroups_totals(arb)

    def is_arb_in_arb_group_totals(self, arb):
        for arb_group in self.list_of_ArbGroups_totals:
            if arb.home_team_lines[0] in arb_group.home_team_lines and arb.away_team_lines[0]\
                    in arb_group.away_team_lines:
                return True
        return False

    def is_arb_in_arb_group_spreads(self, arb):
        for arb_group in self.list_of_ArbGroups_spreads:
            if arb.home_team_lines[0] in arb_group.home_team_lines and arb.away_team_lines[0]\
                    in arb_group.away_team_lines:
                return True
        return False

    def is_arb_in_arb_group_h2h(self, arb):
        for arb_group in self.list_of_ArbGroups_h2h:
            if arb.home_team_lines[0] in arb_group.home_team_lines and arb.away_team_lines[0]\
                    in arb_group.away_team_lines:
                return True
        return False

    def find_spot_for_arb_in_ArbGroups_totals(self, arb):

        arb_home_team_price = arb.home_team_lines[0].get('price')
        arb_home_team_point = arb.home_team_lines[0].get('point')
        arb_away_team_price = arb.away_team_lines[0].get('price')
        arb_away_team_point = arb.away_team_lines[0].get('point')

        for arb_group in self.list_of_ArbGroups_totals:
            if arb_home_team_price == arb_group.home_team_lines[0].get('price') and arb_home_team_point == \
                    arb_group.home_team_lines[0].get('point') and arb_away_team_price ==\
                    arb_group.away_team_lines[0].get('price') and arb_away_team_point ==\
                    arb_group.away_team_lines[0].get('point'):
                arb_group.add_arb(arb)
                return

        new_arb_group = ArbGroup(arb)
        self.list_of_ArbGroups_spreads.append(new_arb_group)

    def find_spot_for_arb_in_ArbGroups_spreads(self, arb):

        arb_home_team_price = arb.home_team_lines[0].get('price')
        arb_home_team_point = arb.home_team_lines[0].get('point')
        arb_away_team_price = arb.away_team_lines[0].get('price')
        arb_away_team_point = arb.away_team_lines[0].get('point')

        for arb_group in self.list_of_ArbGroups_spreads:
            if arb_home_team_price == arb_group.home_team_lines[0].get('price') and arb_home_team_point == \
                    arb_group.home_team_lines[0].get('point') and arb_away_team_price ==\
                    arb_group.away_team_lines[0].get('price') and arb_away_team_point ==\
                    arb_group.away_team_lines[0].get('point'):
                arb_group.add_arb(arb)
                return

        new_arb_group = ArbGroup(arb)
        self.list_of_ArbGroups_spreads.append(new_arb_group)

    def find_spot_for_arb_in_ArbGroups_h2h(self, arb):

        arb_home_team_price = arb.home_team_lines[0].get('price')
        arb_away_team_price = arb.away_team_lines[0].get('price')

        for arb_group in self.list_of_ArbGroups_h2h:
            # print(arb_group)
            if arb_home_team_price == arb_group.home_team_lines[0].get('price') and arb_away_team_price == \
                    arb_group.away_team_lines[0].get('price'):
                arb_group.add_arb(arb)
                return

        new_arb_group = ArbGroup(arb)
        self.list_of_ArbGroups_h2h.append(new_arb_group)

    def remove_duplicate_lines_h2h(self):
        for arb in self.list_of_h2h_arbs:
            if len(arb.home_team_lines) > 1:
                for i, home_line in enumerate(arb.home_team_lines):
                    for j, home_line2 in enumerate(arb.home_team_lines):
                        if i != j:
                            if home_line == home_line2:
                                arb.home_team_lines.remove(home_line2)

        for arb in self.list_of_h2h_arbs:
            if len(arb.away_team_lines) > 1:
                for i, away_line in enumerate(arb.away_team_lines):
                    for j, away_line2 in enumerate(arb.away_team_lines):
                        if i != j:
                            if away_line == away_line2:
                                arb.away_team_lines.remove(away_line2)

        for arb in self.list_of_h2h_arbs:
            for arb2 in self.list_of_h2h_arbs:
                if arb == arb2:
                    self.list_of_h2h_arbs.remove(arb2)

    def remove_duplicate_lines_spreads(self):
        for arb in self.list_of_spread_arbs:
            if len(arb.home_team_lines) > 1:
                for i, home_line in enumerate(arb.home_team_lines):
                    for j, home_line2 in enumerate(arb.home_team_lines):
                        if i != j:
                            if home_line == home_line2:
                                arb.home_team_lines.remove(home_line2)

        for arb in self.list_of_spread_arbs:
            if len(arb.away_team_lines) > 1:
                for i, away_line in enumerate(arb.away_team_lines):
                    for j, away_line2 in enumerate(arb.away_team_lines):
                        # print("fff")
                        # print(away_line)
                        # print(away_line2)
                        if i != j:
                            if away_line == away_line2:
                                arb.away_team_lines.remove(away_line2)

    def scan_for_arbs_h2h(self):

        # Comparing home team odds with away, running through all combinations
        for entry in self.h2h_markets:
            for home_team_odds in entry.get("outcomes"):
                if home_team_odds.get('name') == self.home_team:

                    last_update_home = entry.get("last_update")
                    home_team_price = home_team_odds.get('price')
                    bookie = entry.get('title')
                    # print(f"{bookie}'s price for {self.home_team}: {home_team_price}")

                    # for each home team price, look at all away prices and find arbs
                    for entry2 in self.h2h_markets:
                        for away_team_odds in entry2.get("outcomes"):
                            if away_team_odds.get('name') == self.away_team:
                                last_update_away = entry2.get("last_update")
                                away_team_price = away_team_odds.get('price')
                                bookie2 = entry2.get('title')
                                # print(f"\t{bookie2}'s price for {self.away_team}: {away_team_price}")

                                is_arb, edge = self.check_if_arb_h2h(home_team_price, away_team_price)
                                if is_arb:
                                    # print(f"\t\t!!!! Arb bet found. {self.home_team} {home_team_price} from {
                                    # bookie} and {self.away_team} {away_team_price} from {bookie2} with an edge of {
                                    # edge}%")
                                    arb = H2hArb(game_id=self.game_id, sport_title=self.sport_title,
                                                 commence_time=self.commence_time, home_team=self.home_team,
                                                 away_team=self.away_team)
                                    home_team_line = {'team': self.home_team, 'last_update': last_update_home,
                                                      'price': home_team_price, 'bookie': bookie}
                                    arb.home_team_lines.append(home_team_line)
                                    away_team_line = {'team': self.away_team, 'last_update': last_update_away,
                                                      'price': away_team_price, 'bookie': bookie2}
                                    arb.away_team_lines.append(away_team_line)
                                    self.list_of_h2h_arbs.append(arb)

    def scan_for_arbs_spreads(self):

        # Comparing home team odds with away

        for entry in self.spreads_markets:
            for home_team_odds in entry.get("outcomes"):
                if home_team_odds.get('name') == self.home_team:
                    # for each home team price, look at all away prices and find arbs so long as the point spread is the same
                    last_update_home = entry.get("last_update")
                    home_team_price = home_team_odds.get('price')
                    bookie = entry.get('title')
                    home_team_spread = home_team_odds.get('point')
                    # print(f"{bookie}'s price for {self.home_team}: {home_team_price} at {home_team_spread}")

                    for entry2 in self.spreads_markets:
                        for away_team_odds in entry2.get("outcomes"):
                            if away_team_odds.get('name') == self.away_team:
                                last_update_away = entry2.get("last_update")
                                away_team_price = away_team_odds.get('price')
                                bookie2 = entry2.get('title')
                                away_team_spread = away_team_odds.get('point')

                                if away_team_spread is not None and home_team_spread is not None:
                                    # print(f"\t{bookie2}'s price for {self.away_team}: {away_team_price} at {away_team_spread")
                                    is_arb, edge = self.check_if_arb_with_point(home_team_price, away_team_price,
                                                                                home_team_spread, away_team_spread)
                                    if is_arb:
                                        # print(f"\t\t!!!! Arb bet found. {self.home_team} {home_team_price} at {home_team_spread} from {bookie} and {self.away_team} {away_team_price} at {away_team_spread} from {bookie2} with an edge of {edge}%")
                                        arb = SpreadArb(game_id=self.game_id, sport_title=self.sport_title,
                                                        commence_time=self.commence_time, home_team=self.home_team,
                                                        away_team=self.away_team)
                                        home_team_line = {'team': self.home_team, 'last_update': last_update_home,
                                                          'price': home_team_price, 'bookie': bookie,
                                                          'point': home_team_spread}
                                        arb.home_team_lines.append(home_team_line)
                                        away_team_line = {'team': self.away_team, 'last_update': last_update_away,
                                                          'price': away_team_price, 'bookie': bookie2,
                                                          'point': away_team_spread}
                                        arb.away_team_lines.append(away_team_line)
                                        self.list_of_spread_arbs.append(arb)

    def scan_for_arbs_totals(self):
        # Comparing home team odds with away

        for entry in self.totals_markets:
            for home_team_odds in entry.get("outcomes"):
                if home_team_odds.get('name') == self.home_team:
                    # for each home team price, look at all away prices and find arbs so long as the point total is the same
                    last_update_home = entry.get("last_update")
                    home_team_price = home_team_odds.get('price')
                    bookie = entry.get('title')
                    home_team_total = home_team_odds.get('point')
                    # print(f"{bookie}'s price for {self.home_team}: {home_team_price} at {home_team_total}")

                    for entry2 in self.totals_markets:
                        for away_team_odds in entry2.get("outcomes"):
                            if away_team_odds.get('name') == self.away_team:
                                last_update_away = entry2.get("last_update")
                                away_team_price = away_team_odds.get('price')
                                bookie2 = entry2.get('title')
                                away_team_total = away_team_odds.get('point')

                                if away_team_total is not None and home_team_total is not None:
                                    # print(f"\t{bookie2}'s price for {self.away_team}: {away_team_price} at {away_team_total")
                                    is_arb, edge = self.check_if_arb_with_point(home_team_price, away_team_price,
                                                                                home_team_total, away_team_total)
                                    if is_arb:
                                        arb = TotalArb(game_id=self.game_id, sport_title=self.sport_title,
                                                       commence_time=self.commence_time, home_team=self.home_team,
                                                       away_team=self.away_team)
                                        home_team_line = {'team': self.home_team, 'last_update': last_update_home,
                                                          'price': home_team_price, 'bookie': bookie,
                                                          'point': home_team_total}
                                        arb.home_team_lines.append(home_team_line)
                                        away_team_line = {'team': self.away_team, 'last_update': last_update_away,
                                                          'price': away_team_price, 'bookie': bookie2,
                                                          'point': away_team_total}
                                        arb.away_team_lines.append(away_team_line)
                                        self.list_of_total_arbs.append(arb)


# Markets are "h2h", "totals", "spreads"
class Arb:
    def __init__(self, game_id: str, sport_title: str, commence_time: str, home_team: str, away_team: str, market: str):
        self.game_id = game_id
        self.sports_title = sport_title
        self.commence_time = commence_time
        self.home_team = home_team
        self.away_team = away_team
        self.market = market
        self.edge = None

        # Form: [{'team': 'bruins', 'last_update': 'last_update' 'price': '-130', 'bookie': 'mybookie'}, ... {}, ...]
        self.home_team_lines: list[dict] = []
        # Form: [{'team': 'flyers', 'last_update': 'last_update' 'price': '140', 'bookie': 'mybookie'}, ... {}, ...]
        #   has key 'point': 'point' if there is a point spread/total
        self.away_team_lines: list[dict] = []

    def calculate_edge(self):
        home_implied_probability = self.get_implied_probability(self.home_team_lines[0].get('price'))
        away_implied_probability = self.get_implied_probability(self.away_team_lines[0].get('price'))
        self.edge = round(100 - (home_implied_probability + away_implied_probability), 2)

    @staticmethod
    def get_implied_probability(odds):
        if odds <= 0:
            return -odds / (-odds + 100) * 100
        else:
            return 100 / (odds + 100) * 100

    def __str__(self):

        string = f"Arb:\n" \
                 f"Game: {self.game_id}\n" \
                 f"Sport: {self.sports_title}\n" \
                 f"{self.home_team}: {self.home_team_lines}\n" \
                 f"{self.away_team}: {self.away_team_lines}\n" \
                 f"Profit: {self.edge}\n"
        return string


class H2hArb(Arb):
    def __init__(self, game_id: str, sport_title: str, commence_time: str, home_team: str, away_team: str):
        super(H2hArb, self).__init__(game_id=game_id, sport_title=sport_title, commence_time=commence_time,
                                     home_team=home_team, away_team=away_team, market="h2h")


class SpreadArb(Arb):
    def __init__(self, game_id: str, sport_title: str, commence_time: str, home_team: str, away_team: str):
        super(SpreadArb, self).__init__(game_id=game_id, sport_title=sport_title, commence_time=commence_time,
                                        home_team=home_team, away_team=away_team, market="spreads")

    def __str__(self):
        string = f"Arb:\n" \
                 f"Game: {self.game_id}\n" \
                 f"Sport: {self.sports_title}\n" \
                 f"{self.home_team}: {self.home_team_lines}\n" \
                 f"{self.away_team}: {self.away_team_lines}\n" \
                 f"Profit: {self.edge}\n"
        return string


class TotalArb(Arb):
    def __init__(self, game_id: str, sport_title: str, commence_time: str, home_team: str, away_team: str):
        super().__init__(game_id=game_id, sport_title=sport_title, commence_time=commence_time,
                         home_team=home_team, away_team=away_team, market="spreads")

    def __str__(self):
        string = f"Arb:\n" \
                 f"Game: {self.game_id}\n" \
                 f"Sport: {self.sports_title}\n" \
                 f"{self.home_team}: {self.home_team_lines}\n" \
                 f"{self.away_team}: {self.away_team_lines}\n" \
                 f"Profit: {self.edge}\n"
        return string


# To be used in web page
class ArbGroup:
    def __init__(self, arb: Arb):
        self.game_id = None
        self.sports_title = None
        self.commence_time = None
        self.home_team = None
        self.away_team = None
        self.market = None
        self.edge = None
        self.parse_arb_info(arb)

        # Form: [{'team': 'bruins', 'last_update': 'last_update' 'price': '-130', 'bookie': 'mybookie'}, ... {}, ...]
        self.home_team_lines: list[dict] = []
        # Form: [{'team': 'flyers', 'last_update': 'last_update' 'price': '140', 'bookie': 'mybookie'}, ... {}, ...]
        #   has key 'point': 'point' if there is a point spread/total
        self.away_team_lines: list[dict] = []

        self.add_arb(arb)
        self.calculate_edge()

    def calculate_edge(self):
        home_implied_probability = self.get_implied_probability(self.home_team_lines[0].get('price'))
        away_implied_probability = self.get_implied_probability(self.away_team_lines[0].get('price'))
        self.edge = round(100 - (home_implied_probability + away_implied_probability), 2)

    @staticmethod
    def get_implied_probability(odds):
        if odds <= 0:
            return -odds / (-odds + 100) * 100
        else:
            return 100 / (odds + 100) * 100

    def parse_arb_info(self, arb_data):
        self.game_id = arb_data.game_id
        self.sports_title = arb_data.sports_title
        self.commence_time = arb_data.commence_time
        self.home_team = arb_data.home_team
        self.away_team = arb_data.away_team
        self.market = arb_data.market
        self.edge = arb_data.edge

    def add_arb(self, arb: Arb):
        # Add home team line
        if arb.home_team_lines[0] not in self.home_team_lines:
            self.home_team_lines.append(arb.home_team_lines[0])

        # Add away team line
        if arb.away_team_lines[0] not in self.away_team_lines:
            self.away_team_lines.append(arb.away_team_lines[0])

    def __str__(self):

        string = f"\tArbGroup:\n" \
                 f"\t\tGame: {self.game_id}\n" \
                 f"\t\tSport: {self.sports_title}\n" \
                 f"\t\t{self.home_team}: {self.home_team_lines}\n" \
                 f"\t\t{self.away_team}: {self.away_team_lines}\n" \
                 f"\t\tMarket: {self.market}\n" \
                 f"\t\tProfit: {self.edge}\n"

        return string


def export_ncaab_games():
    for ncaab_game in list_of_ncaab_games:
        for arb_group in ncaab_game.list_of_ArbGroups:
            write_to_json.write_to_json(arb_group)


def export_nba_games():
    for nba_game in list_of_nba_games:
        for arb_group in nba_game.list_of_ArbGroups:
            write_to_json.write_to_json(arb_group)


def export_nfl_games():
    for nfl_game in list_of_nfl_games:
        for arb_group in nfl_game.list_of_ArbGroups:
            write_to_json.write_to_json(arb_group)


def export_nhl_games():
    for nhl_game in list_of_nhl_games:
        for arb_group in nhl_game.list_of_ArbGroups:
            write_to_json.write_to_json(arb_group)


def write_arbgroups_to_json():
    export_ncaab_games()
    export_nfl_games()
    export_nba_games()
    export_nhl_games()


def print_ArbGroups():
    print("**********NHL**********\n")
    for nhl_game in list_of_nhl_games:
        if len(nhl_game.list_of_ArbGroups_h2h) != 0:
            print(
                f"List of H2H ArbGroups in game {nhl_game.home_team} vs {nhl_game.away_team}: {nhl_game.list_of_ArbGroups_h2h}\n")
            for arb_group in nhl_game.list_of_ArbGroups_h2h:
                print(arb_group)

    for nhl_game in list_of_nhl_games:
        if len(nhl_game.list_of_ArbGroups_spreads) != 0:
            print(
                f"List of Spreads ArbGroups in game {nhl_game.home_team} vs {nhl_game.away_team}: {nhl_game.list_of_ArbGroups_spreads}\n")
            for arb_group in nhl_game.list_of_ArbGroups_spreads:
                print(arb_group)

    for nhl_game in list_of_nhl_games:
        if len(nhl_game.list_of_ArbGroups_totals) != 0:
            print(
                f"List of Totals ArbGroups in game {nhl_game.home_team} vs {nhl_game.away_team}: {nhl_game.list_of_ArbGroups_totals}\n")
            for arb_group in nhl_game.list_of_ArbGroups_totals:
                print(arb_group)

    print("\n\n\n")

    print("**********NFL**********\n")
    for nfl_game in list_of_nfl_games:
        if len(nfl_game.list_of_ArbGroups_h2h) != 0:
            print(
                f"List of H2H ArbGroups in game {nfl_game.home_team} vs {nfl_game.away_team}: {nfl_game.list_of_ArbGroups_h2h}\n")
            for arb_group in nfl_game.list_of_ArbGroups_h2h:
                print(arb_group)

    for nfl_game in list_of_nfl_games:
        if len(nfl_game.list_of_ArbGroups_spreads) != 0:
            print(
                f"List of Spreads ArbGroups in game {nfl_game.home_team} vs {nfl_game.away_team}: {nfl_game.list_of_ArbGroups_spreads}\n")
            for arb_group in nfl_game.list_of_ArbGroups_spreads:
                print(arb_group)

    for nfl_game in list_of_nhl_games:
        if len(nfl_game.list_of_ArbGroups_totals) != 0:
            print(
                f"List of Totals ArbGroups in game {nfl_game.home_team} vs {nfl_game.away_team}: {nfl_game.list_of_ArbGroups_totals}\n")
            for arb_group in nfl_game.list_of_ArbGroups_totals:
                print(arb_group)

    print("\n\n\n")

    print("**********NBA**********\n")
    for nba_game in list_of_nba_games:
        if len(nba_game.list_of_ArbGroups_h2h) != 0:
            print(
                f"List of H2H ArbGroups in game {nba_game.home_team} vs {nba_game.away_team}: {nba_game.list_of_ArbGroups_h2h}\n")
            for arb_group in nba_game.list_of_ArbGroups_h2h:
                print(arb_group)
                print(arb_group)

    for nba_game in list_of_nba_games:
        if len(nba_game.list_of_ArbGroups_spreads) != 0:
            print(
                f"List of Spreads ArbGroups in game {nba_game.home_team} vs {nba_game.away_team}: {nba_game.list_of_ArbGroups_spreads}\n")
            for arb_group in nba_game.list_of_ArbGroups_spreads:
                print(arb_group)

    for nba_game in list_of_nba_games:
        if len(nba_game.list_of_ArbGroups_totals) != 0:
            print(
                f"List of Totals ArbGroups in game {nba_game.home_team} vs {nba_game.away_team}: {nba_game.list_of_ArbGroups_totals}\n")
            for arb_group in nba_game.list_of_ArbGroups_totals:
                print(arb_group)

    print("\n\n\n")

    print("**********NCAAB**********\n")
    for ncaab_game in list_of_ncaab_games:
        if len(ncaab_game.list_of_ArbGroups_h2h) != 0:
            print(
                f"List of H2H ArbGroups in game {ncaab_game.home_team} vs {ncaab_game.away_team}: {ncaab_game.list_of_ArbGroups_h2h}\n")
            for arb_group in ncaab_game.list_of_ArbGroups_h2h:
                print(arb_group)

    for ncaab_game in list_of_ncaab_games:
        if len(ncaab_game.list_of_ArbGroups_spreads) != 0:
            print(
                f"List of Spreads ArbGroups in game {ncaab_game.home_team} vs {ncaab_game.away_team}: {ncaab_game.list_of_ArbGroups_spreads}\n")
            for arb_group in ncaab_game.list_of_ArbGroups_spreads:
                print(arb_group)

    for ncaab_game in list_of_ncaab_games:
        if len(ncaab_game.list_of_ArbGroups_totals) != 0:
            print(
                f"List of Totals ArbGroups in game {ncaab_game.home_team} vs {ncaab_game.away_team}: {ncaab_game.list_of_ArbGroups_totals}\n")
            for arb_group in ncaab_game.list_of_ArbGroups_totals:
                print(arb_group)


if __name__ == '__main__':

    # Make API requests
    the_odds_api_nfl = requests.get(
        f'https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regions=us&markets=h2h,spreads,totals'
        f'&oddsFormat=american&apiKey={API_KEY}')
    nfl_games_json = the_odds_api_nfl.json()

    the_odds_api_nhl = requests.get(
        f'https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds?regions=us&markets=h2h,spreads,totals'
        f'&oddsFormat=american&apiKey={API_KEY}')
    nhl_games_json = the_odds_api_nhl.json()

    the_odds_api_nba = requests.get(
        f'https://api.the-odds-api.com/v4/sports/basketball_nba/odds?regions=us&markets=h2h,spreads,totals'
        f'&oddsFormat=american&apiKey={API_KEY}')
    nba_games_json = the_odds_api_nba.json()

    the_odds_api_ncaab = requests.get(
        f'https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds?regions=us&markets=h2h,spreads,totals'
        f'&oddsFormat=american&apiKey={API_KEY}')
    ncaab_games_json = the_odds_api_ncaab.json()

    # Write API data to files
    with open("nfl_odds_json.json", "w") as file:
        file.write(json.dumps(nfl_games_json))

    with open("nhl_odds_json.json", "w") as file:
        file.write(json.dumps(nhl_games_json))

    with open("nba_odds_json.json", "w") as file:
        file.write(json.dumps(nba_games_json))

    with open("ncaab_odds_json.json", "w") as file:
        file.write(json.dumps(ncaab_games_json))

    # Read JSON data from files
    with open("nfl_odds_json.json", "r") as file:
        nfl_games_json = json.load(file)

    with open("nhl_odds_json.json", "r") as file:
        nhl_games_json = json.load(file)

    with open("nba_odds_json.json", "r") as file:
        nba_games_json = json.load(file)

    with open("ncaab_odds_json.json", "r") as file:
        ncaab_games_json = json.load(file)

    list_of_nfl_games = []
    list_of_nhl_games = []
    list_of_nba_games = []
    list_of_ncaab_games = []

    i = 0
    for game_dict in nfl_games_json:
        if i <= 1000:
            game = Game(game_dict)
            list_of_nfl_games.append(game)
            i += 1

    j = 0
    for game_dict in nhl_games_json:
        if j <= 1000:
            game = Game(game_dict)
            list_of_nhl_games.append(game)
        j += 1

    k = 0
    for game_dict in nba_games_json:
        if k <= 1000:
            game = Game(game_dict)
            list_of_nba_games.append(game)
        k += 1

    l = 0
    for game_dict in ncaab_games_json:
        if l <= 1000:
            game = Game(game_dict)
            list_of_ncaab_games.append(game)
        l += 1

    print_ArbGroups()
    write_to_json.clear_arbs_json()
    write_arbgroups_to_json()
