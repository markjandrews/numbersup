import csv
import json
import os
import math
import statistics
from itertools import combinations, chain
from typing import Sequence
from scipy.stats import norm

from datetime import datetime, timedelta, date

import pyreadline as readline

from util import is_number_sequence, odd_even_ratio, high_low_ratio, draw_sum, hot_ratio, prompt


class Draw(object):
    @staticmethod
    def Parse(data: Sequence[str]):
        raise NotImplementedError

    def __init__(self):
        self.number = None
        self.date = None
        self.winning_numbers = set()
        self.comb_sets = {}

    def powerset(self):
        s = list(self.winning_numbers)
        return chain.from_iterable(combinations(s, r + 1) for r in range(len(s)))

    def comb_set(self, r):

        if len(self.winning_numbers) < r:
            return {}

        if not os.path.exists('OZ/Draw%s.json' % self.number):
            ps = self.powerset()
            json_data = list(ps)
            with open('OZ/Draw%s.json' % self.number, 'w') as outf:
                json.dump(json_data, outf, sort_keys=True, separators=(',', ': '))

        combs_r = self.comb_sets.get(r)
        if combs_r is None:
            with open('OZ/Draw%s.json' % self.number, 'r') as inf:
                json_data = json.load(inf)

            for ball_list in json_data:
                ball_set = self.comb_sets.setdefault(len(ball_list), set())
                ball_set.add(tuple(ball_list))

        return self.comb_sets[r]


class OZDraw(Draw):
    MAX_BALL = 45
    NUM_BALLS = 7

    WINNING_COMBS = [(1, 7, 0),
                     (2, 6, 1),
                     (3, 6, 0),
                     (4, 5, 1),
                     (5, 5, 0),
                     (6, 4, 0),
                     (7, 3, 1)]

    @staticmethod
    def Parse(data: Sequence[str]):
        result = OZDraw()
        result.number = int(data[0])
        result.date = data[1]
        result.winning_numbers.add(int(data[2]))
        result.winning_numbers.add(int(data[3]))
        result.winning_numbers.add(int(data[4]))
        result.winning_numbers.add(int(data[5]))
        result.winning_numbers.add(int(data[6]))
        result.winning_numbers.add(int(data[7]))
        result.winning_numbers.add(int(data[8]))

        result.supplementaries.append(int(data[9]))
        result.supplementaries.append(int(data[10]))

        return result

    def __init__(self, winning_numbers=None, supplementaries=None):
        super().__init__()

        if winning_numbers is not None:
            self.winning_numbers = winning_numbers

        if supplementaries is not None:
            self.supplementaries = supplementaries
        else:
            self.supplementaries = []

    def __str__(self):
        return '%s (%s): %s %s' % (self.number, self.date, str(self.winning_numbers), str(self.supplementaries))

    def __repr__(self):
        return self.__str__()


class BallStat(object):
    first_draw = '20051018'
    most_recent_draw = (date.today() - timedelta(days=((datetime.today().weekday() - 3) % 7))).strftime("%Y%m%d")

    @classmethod
    def diff_date(cls, last_draw_date, prev_draw_date):

        if prev_draw_date is None:
            prev_draw_date = cls.first_draw

        if last_draw_date is None:
            last_draw_date = cls.most_recent_draw

        last_time = datetime.strptime(last_draw_date, "%Y%m%d")
        prev_time = datetime.strptime(prev_draw_date, "%Y%m%d")

        return (last_time - prev_time).days // 7

    def __init__(self, ball_comb):
        self._ball_comb = sorted(ball_comb)
        self.draws = []
        self.draw_avg = 0
        self.total_draws = 0

    def __str__(self):
        return '%s: %s (%s) - %s (%s)' % (self._ball_comb, self.draws[-1].date, self.total_draws, int(self.draw_avg),
                                          self.weeks_since_drawn)

    def __repr__(self):
        return self.__str__()

    @property
    def ball_comb(self):
        return self._ball_comb

    @property
    def weeks_since_drawn(self):
        return self.diff_date(None, self.draws[-1].date)

    def new_draw(self, draw_date, draw):
        if len(self.draws) == 0:
            prev_draw = draw.date
        else:
            prev_draw = self.draws[-1].date

        self.draws.append(draw)

        weeks_diff = self.diff_date(draw_date, prev_draw)
        total_weeks = self.draw_avg * self.total_draws + weeks_diff
        self.total_draws += 1
        self.draw_avg = total_weeks / self.total_draws


def is_numberset_valid(number_set, ball_stats_dict, games_out_dict):
    with open('settings.json', 'r') as inf:
        settings = json.load(inf)

    valid = True
    number_set = sorted(number_set)

    comb_pool = chain.from_iterable(combinations(number_set, r) for r in range(len(number_set) + 1))

    for comb in comb_pool:
        if len(comb) < 2:
            continue

        num_balls_per_draw = settings['num_balls_per_draw']
        if len(comb) == num_balls_per_draw:

            games_out_list = [x for x, y in games_out_dict.items() if y == 0]
            if len(games_out_list) > 0:
                raise NotImplementedError('Games Out not yet implemented')

            odd, even = odd_even_ratio(comb)

            if odd not in settings['allowed_odd_ratios']:
                print('Comb %s has unlikely odd/even ratio (%s/%s)' % (str(comb), odd, even))
                valid = False
                break

            high, low = high_low_ratio(comb)
            if high not in settings['allowed_high_ratios']:
                print('Comb %s has unlikely high/low ratio (%s/%s)' % (str(comb), high, low))
                valid = False
                break

            draw_sum_value = draw_sum(comb)
            if draw_sum_value < settings['min_sum'] or draw_sum_value > settings['max_sum']:
                print('Comb %s has unlikely sum (%s)' % (str(comb), draw_sum_value))
                valid = False
                break

            hr = hot_ratio(comb, ball_stats_dict)
            if hr not in settings['allowed_hot_ratios']:
                print('Comb %s does not contain enough "hot" numbers (%s) min 4' % (str(comb), hr))
                valid = False
                break

        diff = is_number_sequence(comb)
        if diff is not None:
            allowed_sequences = settings['allowed_sequences'].get(str(len(comb)), None)
            if allowed_sequences is not None and diff not in allowed_sequences:
                print('Comb %s has unlikely sequence' % str(comb))
                valid = False
                break

        allowed_total_draws = settings['allowed_total_draws'].get(str(len(comb)), None)
        if allowed_total_draws is not None:
            if comb in ball_stats_dict:
                total_draws = ball_stats_dict[comb].total_draws
            else:
                total_draws = 0

            if total_draws < allowed_total_draws[0] or total_draws >= allowed_total_draws[1]:
                print('Comb %s unlikely to be drawn again (%s) "< %s || >= %s"' % (
                    str(comb), total_draws, allowed_total_draws[0], allowed_total_draws[1]))
                valid = False
                break

    return valid


def games_out(draws, ball_stats):
    results = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for draw in draws[-5:]:
        for ball in draw.winning_numbers:
            ball = tuple([ball])
            ball_stat = ball_stats[ball]
            games_skipped = BallStat.diff_date(ball_stat.draws[-1].date, ball_stat.draws[-2].date)

            if 1 <= games_skipped <= 5:
                results[games_skipped] += 1

    return results


def calibrate(ball_stats):
    print('Calibrating Analysis')
    if os.path.exists('settings.json'):
        with open('settings.json', 'r') as inf:
            settings = json.load(inf)
    else:
        settings = {}

    settings['num_balls_per_draw'] = num_balls_per_draw = settings.get('num_balls_per_draw',
                                                                       max([len(x) for x in ball_stats]))

    draw_balls_list = [x for x in ball_stats if len(x) == num_balls_per_draw]

    print('Analysis based on %s draws' % len(draw_balls_list))
    print('\nOdd Ratios')
    odd_ratios = {}
    for draw_balls_item in draw_balls_list:
        odd, even = odd_even_ratio(draw_balls_item)

        ratio = odd_ratios.get(odd, 0) + 1
        odd_ratios[odd] = ratio

    print(odd_ratios)
    default = ','.join([str(x) for x in settings.get('allowed_odd_ratios', [])])
    prompt('Allowed Odd Ratios', default)

    value_str = input()
    if len(value_str) == 0:
        value_str = default

    values = [int(x) for x in value_str.split(',')]
    settings['allowed_odd_ratios'] = values

    print('\nHigh Ratios')
    high_ratios = {}
    for draw_balls_item in draw_balls_list:
        high, low = high_low_ratio(draw_balls_item)
        high_ratios[high] = high_ratios.get(high, 0) + 1

    print(high_ratios)
    default = ','.join([str(x) for x in settings.get('allowed_high_ratios', [])])
    prompt('Allowed High Ratios', default)

    value_str = input()
    if len(value_str) == 0:
        value_str = default

    values = [int(x) for x in value_str.split(',')]
    settings['allowed_high_ratios'] = values

    print('\nAllowed Draw Sums')
    default = settings.get('sum_percentile', None)
    prompt('Allowed Percentile', default)

    value_str = input()
    if len(value_str) == 0:
        value_str = default

    settings['sum_percentile'] = value_str
    value = float(int(value_str) / 100)

    draw_sums = []
    for draw_balls_item in draw_balls_list:
        draw_sums.append(draw_sum(draw_balls_item))

    mean = statistics.mean(draw_sums)
    standard_dev = statistics.stdev(draw_sums)
    low_z = norm.ppf(0.5 - (value / 2))
    high_z = norm.ppf(0.5 + (value / 2))
    min_value = low_z * standard_dev + mean
    max_value = high_z * standard_dev + mean

    settings['max_sum'] = math.ceil(max_value)
    settings['min_sum'] = math.floor(min_value)
    print('Max Sum: %s Min Sum: %s' % (settings['max_sum'], settings['min_sum']))
    print('\nHot Ratios')
    hot_ratios = {}
    for draw_balls_item in draw_balls_list:
        ratio = hot_ratio(draw_balls_item, ball_stats)
        hot_ratios[ratio] = hot_ratios.get(ratio, 0) + 1

    print(hot_ratios)
    default = ','.join([str(x) for x in settings.get('allowed_hot_ratios', [])])
    prompt('Allowed Hot Ratios', default)

    value_str = input()
    if len(value_str) == 0:
        value_str = default

    values = [int(x) for x in value_str.split(',')]
    settings['allowed_hot_ratios'] = values

    sequences_dict = {}
    for ball_item in ball_stats:
        diff = is_number_sequence(ball_item)
        if diff is not None:
            sequence_count = sequences_dict.setdefault(len(ball_item), {})
            sequence_count[diff] = sequence_count.get(diff, 0) + 1

    print('\nNumber Sequences')
    settings.setdefault('allowed_sequences', {})
    for sequence_value, sequence_item in sequences_dict.items():
        print(sequence_value, str(sequence_item))
        default = ','.join([str(x) for x in settings['allowed_sequences'].get(str(sequence_value), [])])
        prompt('Allowed Sequences for Set Len (%d)' % sequence_value, default)

        value_str = input()
        if len(value_str) == 0:
            value_str = default

        settings['allowed_sequences'][str(sequence_value)] = [int(x) for x in value_str.split(',')]

    total_draws_dict = {}
    for stat_key, stat_value in ball_stats.items():
        if len(stat_key) == 1:
            continue

        total_draws = stat_value.total_draws
        total_draw_count = total_draws_dict.setdefault(len(stat_key), {})
        total_draw_count[total_draws] = total_draw_count.get(total_draws, 0) + 1

    print('\nTotal Draws')
    settings.setdefault('allowed_total_draws', {})
    for total_draws_key, total_draws_value in total_draws_dict.items():
        print(total_draws_key, str(total_draws_value))
        default = ','.join([str(x) for x in settings['allowed_total_draws'].get(str(total_draws_key), [])])
        prompt('Total Draws (min,max) for Set Len (%d)' % total_draws_key, default)

        value_str = input()
        if len(value_str) == 0:
            value_str = default

        settings['allowed_total_draws'][str(total_draws_key)] = [int(x) for x in value_str.split(',')]

    with open('settings.json', 'w') as outf:
        json.dump(settings, outf)


def check_results(draw, candidates):
    winning_numbers = set(draw.winning_numbers)
    supplementaries = set(draw.supplementaries)

    for candidate in candidates:
        candidate = set(candidate)
        drawn_numbers = candidate & winning_numbers
        drawn_supps = candidate & supplementaries

        if len(drawn_numbers) == 0:
            continue

        matched_winning_combs = [x for x in draw.WINNING_COMBS if
                                 x[1] == len(drawn_numbers) and x[2] <= len(drawn_supps)]

        if len(matched_winning_combs) == 0:
            continue

        print('Candidate: %s:' % candidate)
        for div in matched_winning_combs:
            print('  Div (%s): %s %s' % (div[0], str(drawn_numbers), str(drawn_supps)))
