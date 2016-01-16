import json
import os
import shutil
import sys

import remote
from results import PBDraw, BallStat, is_numberset_valid, games_out, calibrate, check_results
from util import random_combination


def main(argv):
    ballstats_dict = {}
    last_draw = None
    # last_draw = PBDraw.Parse(
    #         ["1026", "20160114", "4", "8", "11", "20", "32", "39", "15", "$0.00", "$0.00", "$11,526.05", "$192.90",
    #          "$63.70", "$37.95", "$27.75", "$13.35"])
    # last_draw = PBDraw(winning_numbers=[11, 13, 20, 21, 28, 37], powerball=20)
    candidate_list = set()

    if '-d' in argv:
        if os.path.exists('PB'):
            shutil.rmtree('PB')

        if os.path.exists('results.csv'):
            os.unlink('results.csv')

    if not os.path.exists('PB'):
        os.makedirs('PB')

    # url = 'https://tatts.com/DownloadFile.ashx?product=Powerball'
    url = argv[0]
    draw_results = []
    print('==============================\nGenerating Draw Statistics\n==============================\n')
    for result in remote.pull_results(url):
        if result is None or len(result) == 0:
            continue

        draw = PBDraw.Parse(result)
        draw_results.append(draw)
        for draw_comb_set in [draw.comb_set(x + 1) for x in range(len(draw.winning_numbers))]:
            for draw_comb in draw_comb_set:
                ballstat = ballstats_dict.setdefault(tuple(sorted(draw_comb)), BallStat(draw_comb))
                ballstat.new_draw(draw.date, draw)

    # Calibrate draw settings
    if '-c' in argv or not os.path.exists('settings.json'):
        calibrate(ballstats_dict)

    # Check if number set is valid
    # result = is_numberset_valid([24, 30, 18, 3, 11, 8], ballstats_dict)

    games_out_dict = games_out(draw_results, ballstats_dict)

    if os.path.exists('pbcandidate.json'):
        print('==============================\nChecking Existing Candidates for Invalid Entries\n'
              '==============================')
        with open('pbcandidate.json', 'r') as inf:
            data = json.load(inf)
            for item in sorted(data):
                if is_numberset_valid(item, ballstats_dict, games_out_dict) is True:
                    # print('%s - Valid' % str(item))
                    candidate_list.add(tuple(sorted(item)))
                else:
                    print('%s - Invalid' % str(item))

        print()

    if len(candidate_list) < 100:
        print('==============================\nAdding new candidates to candidate list\n==============================')
    while len(candidate_list) < 100:
        candidate = random_combination(PBDraw.MAX_BALL, PBDraw.NUM_BALLS)
        if is_numberset_valid(candidate, ballstats_dict, games_out_dict) is True:
            print('Adding %s' % str(candidate))
            candidate_list.add(tuple(sorted(candidate)))
        else:
            print('Skipping %s' % str(candidate))

    print('==============================\nSaving Candiate List to File(s)\n==============================')
    with open('pbcandidate.json', 'w') as outf:
        json.dump(list(candidate_list), outf)

    num_entries_per_ticket = 50
    num_files = len(candidate_list) // num_entries_per_ticket
    if (num_files * num_entries_per_ticket) < len(candidate_list):
        num_files += 1

    for i in range(num_files):
        with open('pbcandidate_%s.txt' % str(i + 1), 'w') as outf:
            print('pbcandidate_%s.txt' % str(i + 1))
            for candidate in sorted(candidate_list)[
                             i * num_entries_per_ticket:i * num_entries_per_ticket + num_entries_per_ticket]:
                outf.write('%s\n' % ', '.join([str(i) for i in candidate]))

    if last_draw is None:
        last_draw = draw_results[-1]

    # Check if last draw "could have" one
    print('\n==============================\nChecking Validity of Last Draw\n==============================')
    print('Last Draw: %s' % last_draw)
    print('Could have won: %s' % is_numberset_valid(last_draw.winning_numbers, ballstats_dict, games_out_dict))

    # Look for winning combinations from candidates
    print('\n==============================\nChecking Candidates Against Last Draw\n==============================')
    print('Last Draw: %s' % last_draw)
    check_results(last_draw, candidate_list)


if __name__ == '__main__':
    main(sys.argv[1:])
