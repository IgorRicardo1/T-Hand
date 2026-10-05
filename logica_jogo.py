import random


class CuboUnico:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"CuboUnico({self.x}, {self.y})"


class PecasPossiveis:
    FORMATOS = {
        "I": ((-1, 0), (0, 0), (1, 0), (2, 0)),
        "T": ((-1, 0), (0, 0), (1, 0), (0, -1)),
        "L": ((1, -1), (-1, 0), (0, 0), (1, 0)),
        "J": ((-1, -1), (-1, 0), (0, 0), (1, 0)),
        "S": ((-1, 0), (0, 0), (0, -1), (1, -1)),
        "Z": ((-1, -1), (0, -1), (0, 0), (1, 0)),
        "O": ((0, 0), (0, 1), (1, 0), (1, 1)),
    }

    @classmethod
    def sortear(cls):
        return random.choice(list(cls.FORMATOS.items()))


class Peca:
    def __init__(self):
        pass


class Grid:
    def __init__(self):
        pass


class Jogo:
    def __init__(self):
        pass


if __name__ == "__main__":
    """testes"""
    for c in range(5):
        print(c, PecasPossiveis.sortear())
