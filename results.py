from typing import Sequence


class Draw(object):

    @staticmethod
    def Parse(data: Sequence[str]):
        raise NotImplementedError


class PBDraw(Draw):

    @staticmethod
    def Parse(data: Sequence[str]):
        result = PBDraw()
        result.number = int(data[0])
        result.date = data[1]
        result.winning_numbers.add(int(data[2]))
        result.winning_numbers.add(int(data[3]))
        result.winning_numbers.add(int(data[4]))
        result.winning_numbers.add(int(data[5]))
        result.winning_numbers.add(int(data[6]))

        if data[8] == '-':
            result.powerball = int(data[7])
        else:
            result.powerball = int(data[8])
            if data[7] != '-':
                result.winning_numbers.add(int(data[7]))

        return result

    def __init__(self):
        self.number = None
        self.date = None
        self.winning_numbers = set()
        self.powerball = None

    def __str__(self):
        return '%s (%s): %s (%s)' % (self.number, self.date, str(self.winning_numbers), self.powerball)
