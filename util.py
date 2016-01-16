import random
from functools import reduce
import operator as op


def nCr(n, r):
    r = min(r, n - r)
    if r == 0: return 1
    numer = reduce(op.mul, range(n, n - r, -1))
    denom = reduce(op.mul, range(1, r + 1))
    return numer // denom


def is_number_sequence(s):
    if len(s) <= 2:
        return None  # tuple of <= 2 elements can't be in sequence

    sorted_s = sorted(s)
    diff = sorted_s[1] - sorted_s[0]

    for i, item in enumerate(sorted_s[2:]):
        if (sorted_s[i + 2] - sorted_s[i + 1]) != diff:
            return None

    return diff


def odd_even_ratio(s):

    even = 0
    odd = 0

    for item in s:
        if item % 2 == 0:
            even += 1
        else:
            odd += 1

    return odd, even


def high_low_ratio(s):

    high = 0
    low = 0

    for item in s:
        if item <= 20:
            low += 1
        else:
            high += 1

    return high, low


def draw_sum(s):
    return sum(s)


def hot_ratio(s, ball_stats):

    hot_count = 0

    for item in s:
        ball_stat = ball_stats[tuple([item])]
        if ball_stat.weeks_since_drawn <= 10:
            hot_count += 1

    return hot_count


def prompt(desc, default=None):
    print(desc, end='')

    if default is not None:
        print(' (%s)' % default, end='')

    print(':> ', end='')


def random_combination(n, r):
    pool = tuple(range(1, n + 1))
    indicies = sorted(random.sample(range(n), r))
    return tuple(pool[i] for i in indicies)
