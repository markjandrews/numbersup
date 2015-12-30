import sys

import remote
from results import PBDraw


def main(argv):

    # url = 'https://tatts.com/DownloadFile.ashx?product=Powerball'
    url = argv[0]
    for result in remote.pull_results(url):
        draw = PBDraw.Parse(result)
        print(draw)

if __name__ == '__main__':
    main(sys.argv[1:])