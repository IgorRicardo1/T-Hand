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

    @classmethod
    def obter_por_letra(cls, letra):
        return (letra, cls.FORMATOS[letra])

    @classmethod
    def gerar_bolsa(cls):
        itens = list(cls.FORMATOS.items())
        random.shuffle(itens)
        return itens


class Peca:
    def __init__(self, letra_e_formato):
        letra, formato = letra_e_formato
        self.letra = letra
        self.cubos = [CuboUnico(c[0], c[1]) for c in formato]
        self.origem = [4, 0]

    def mover(self, mover_x, mover_y):
        self.origem[0] += mover_x
        self.origem[1] += mover_y

    def rodar(self, horario=True):
        if self.letra == "O":
            return
        for cubo in self.cubos:
            if horario:
                cubo.x, cubo.y = -cubo.y, cubo.x
            else:
                cubo.x, cubo.y = cubo.y, -cubo.x


class Grid:
    def __init__(self, largura=10, altura=20):
        self.largura = largura
        self.altura = altura
        self.celulas = [[None for _ in range(largura)] for _ in range(altura)]
        self.cubos_eliminados = []
        self.linhas_eliminadas_y = []

    def valida_posicao(self, peca):
        for cubo in peca.cubos:
            x_real = peca.origem[0] + cubo.x
            y_real = peca.origem[1] + cubo.y

            if x_real < 0 or x_real >= self.largura:
                return False
            if y_real >= self.altura:
                return False
            if y_real >= 0 and self.celulas[y_real][x_real] is not None:
                return False

        return True

    def fixar_peca(self, peca):
        for cubo in peca.cubos:
            x_real = peca.origem[0] + cubo.x
            y_real = peca.origem[1] + cubo.y
            if y_real >= 0:
                self.celulas[y_real][x_real] = peca.letra

    def limpar_linha(self):
        linhas_completadas = 0
        self.cubos_eliminados = []
        self.linhas_eliminadas_y = []

        for y in range(self.altura):
            if None not in self.celulas[y]:
                self.linhas_eliminadas_y.append(y)
                for x, letra in enumerate(self.celulas[y]):
                    self.cubos_eliminados.append((x, y, letra))
                self.celulas.pop(y)
                linhas_completadas += 1
                self.celulas.insert(0, [None for _ in range(self.largura)])
        return linhas_completadas

    def altura_pilha(self):
        for y in range(self.altura):
            if any(c is not None for c in self.celulas[y]):
                return self.altura - y
        return 0


class Jogo:
    NUMERO_PONTOS = {1: 100, 2: 300, 3: 600, 4: 1000}
    RECORDE_SESSAO = 0

    def __init__(self):
        self.pontos = 0
        self.linhas = 0
        self.nivel = 1
        self.combo = 0
        self.ultimo_foi_tetris = False
        self.pausado = False
        self.grid = Grid()
        self.game_over = False

        self.cubos_explodindo = []
        self.linhas_flash = []
        self.impactos_pouso = []
        self.rastros_queda = []
        self.eventos_visuais = []
        self.sons_pendentes = []

        self._bolsa = []
        self.peca_reserva = None
        self.pode_reservar = True
        self.fila_proximas = [Peca(self._retirar_da_bolsa()) for _ in range(3)]
        self.nova_peca()

        self.gravidade = 1
        self.intervalo_queda = 1.0
        self.tempo_acumulado = 0.0

    def _retirar_da_bolsa(self):
        if not self._bolsa:
            self._bolsa = PecasPossiveis.gerar_bolsa()
        return self._bolsa.pop()

    @property
    def proxima_peca(self):
        return self.fila_proximas[0]

    def nova_peca(self):
        self.peca_atual = self.fila_proximas.pop(0)
        self.fila_proximas.append(Peca(self._retirar_da_bolsa()))
        self.pode_reservar = True
        if not self.grid.valida_posicao(self.peca_atual):
            self.game_over = True
            self.sons_pendentes.append(("gameover", 1))

    def reservar_peca(self):
        if self.game_over or self.pausado or not self.pode_reservar:
            return
        letra_atual = self.peca_atual.letra
        if self.peca_reserva is None:
            self.peca_reserva = Peca(PecasPossiveis.obter_por_letra(letra_atual))
            self.nova_peca()
        else:
            letra_reserva = self.peca_reserva.letra
            self.peca_reserva = Peca(PecasPossiveis.obter_por_letra(letra_atual))
            self.peca_atual = Peca(PecasPossiveis.obter_por_letra(letra_reserva))
        self.pode_reservar = False
        self.tempo_acumulado = 0.0
        self.sons_pendentes.append(("reserva", 1))
        self.eventos_visuais.append(("HOLD!", "CIANO"))

    def _processar_pouso(self, impacto_forte=False):
        for cubo in self.peca_atual.cubos:
            x_r = self.peca_atual.origem[0] + cubo.x
            y_r = self.peca_atual.origem[1] + cubo.y
            self.impactos_pouso.append((x_r, y_r, self.peca_atual.letra, impacto_forte))

        self.grid.fixar_peca(self.peca_atual)
        linhas_eliminadas = self.grid.limpar_linha()

        if linhas_eliminadas > 0:
            self.combo += 1
            self.cubos_explodindo.extend(self.grid.cubos_eliminados)
            self.linhas_flash.extend(self.grid.linhas_eliminadas_y)
            self.linhas += linhas_eliminadas
            self.nivel = 1 + (self.linhas // 2)
            self.intervalo_queda = max(0.14, 1.0 - (self.nivel - 1) * 0.085)

            ganho = self.NUMERO_PONTOS.get(linhas_eliminadas, 0) * self.nivel
            if linhas_eliminadas == 4 and self.ultimo_foi_tetris:
                ganho = int(ganho * 1.5)
            if self.combo > 1:
                ganho += 50 * self.combo * self.nivel

            # Bonus Perfect Clear (tabuleiro 100% limpo)
            limpou_tudo = self.grid.altura_pilha() == 0
            if limpou_tudo:
                ganho += 1500 * self.nivel

            self.pontos += ganho

            if limpou_tudo:
                self.eventos_visuais.append((f"PERFECT CLEAR!! +{ganho}", "OURO"))
                self.sons_pendentes.append(("tetris", self.combo))
            elif linhas_eliminadas == 4:
                prefixo = "B2B TETRIS!!" if self.ultimo_foi_tetris else "TETRIS!!"
                self.eventos_visuais.append((f"{prefixo} +{ganho}", "OURO"))
                self.sons_pendentes.append(("tetris", self.combo))
            elif self.combo > 1:
                self.eventos_visuais.append((f"COMBO x{self.combo}! +{ganho}", "CIANO"))
                self.sons_pendentes.append(("linha", self.combo))
            elif linhas_eliminadas >= 2:
                self.eventos_visuais.append(
                    (f"MULTI x{linhas_eliminadas}! +{ganho}", "LARANJA")
                )
                self.sons_pendentes.append(("linha", self.combo))
            else:
                self.eventos_visuais.append((f"+{ganho}", "VERDE"))
                self.sons_pendentes.append(("linha", self.combo))

            self.ultimo_foi_tetris = linhas_eliminadas == 4
        else:
            self.combo = 0
            self.sons_pendentes.append(("hard_drop" if impacto_forte else "pouso", 1))

        if self.pontos > Jogo.RECORDE_SESSAO:
            Jogo.RECORDE_SESSAO = self.pontos

        self.nova_peca()

    def queda_instantanea(self):
        if self.game_over or self.pausado:
            return
        y_inicio = self.peca_atual.origem[1]
        linhas_descidas = 0
        while self.tentar_mover(0, 1, tocar_som=False):
            linhas_descidas += 1
        y_fim = self.peca_atual.origem[1]

        if y_fim > y_inicio:
            for cubo in self.peca_atual.cubos:
                x_r = self.peca_atual.origem[0] + cubo.x
                self.rastros_queda.append(
                    (x_r, y_inicio + cubo.y, y_fim + cubo.y, self.peca_atual.letra)
                )

        self.pontos += linhas_descidas * 2
        if self.pontos > Jogo.RECORDE_SESSAO:
            Jogo.RECORDE_SESSAO = self.pontos
        self.tempo_acumulado = 0.0
        self._processar_pouso(impacto_forte=True)

    def atualizar(self, dt):
        if self.game_over or self.pausado:
            return
        self.tempo_acumulado += dt

        while self.tempo_acumulado >= self.intervalo_queda:
            self.tempo_acumulado -= self.intervalo_queda

            if not self.tentar_mover(0, self.gravidade, tocar_som=False):
                self._processar_pouso(impacto_forte=False)

    def tentar_rotacionar(self, horario=True):
        if self.game_over or self.pausado:
            return
        self.peca_atual.rodar(horario)

        if not self.grid.valida_posicao(self.peca_atual):
            for dx in (-1, 1, -2, 2):
                self.peca_atual.mover(dx, 0)
                if self.grid.valida_posicao(self.peca_atual):
                    self.sons_pendentes.append(("girar", 1))
                    return
                self.peca_atual.mover(-dx, 0)
            self.peca_atual.rodar(not horario)
            return

        self.sons_pendentes.append(("girar", 1))

    def tentar_mover(self, dx, dy, tocar_som=True):
        if self.game_over or self.pausado:
            return False
        self.peca_atual.mover(dx, dy)

        if not self.grid.valida_posicao(self.peca_atual):
            self.peca_atual.mover(-dx, -dy)
            return False

        if tocar_som and dx != 0:
            self.sons_pendentes.append(("mover", 1))
        return True

    def y_de_aterrissagem(self):
        peca = self.peca_atual
        y_original = peca.origem[1]
        while self.grid.valida_posicao(peca):
            peca.origem[1] += 1
        y_final = peca.origem[1] - 1
        peca.origem[1] = y_original
        return y_final


def renderizar_console(jogo):
    print("\n" * 10)
    tela = [["." for _ in range(jogo.grid.largura)] for _ in range(jogo.grid.altura)]

    for y in range(jogo.grid.altura):
        for x in range(jogo.grid.largura):
            if jogo.grid.celulas[y][x] is not None:
                tela[y][x] = "#"

    for cubo in jogo.peca_atual.cubos:
        x_real = jogo.peca_atual.origem[0] + cubo.x
        y_real = jogo.peca_atual.origem[1] + cubo.y
        if 0 <= y_real < jogo.grid.altura and 0 <= x_real < jogo.grid.largura:
            tela[y_real][x_real] = "@"

    print("=" * (jogo.grid.largura * 2 + 3))
    for linha in tela:
        print("| " + " ".join(linha) + " |")
    print("=" * (jogo.grid.largura * 2 + 3))


if __name__ == "__main__":
    jogo = Jogo()

    while True:
        renderizar_console(jogo)
        print(
            "Controles: [A] Esquerda | [D] Direita | [W] Girar | [Enter] Apenas Cair | [Q] Sair"
        )
        print(
            f"Pontos: {jogo.pontos} | Linhas: {jogo.linhas} | Próxima: {jogo.proxima_peca.letra}"
        )
        comando = input("Digite um comando:  ").strip().lower()

        if comando == "q":
            break
        elif comando == "a":
            jogo.tentar_mover(-1, 0)
        elif comando == "d":
            jogo.tentar_mover(1, 0)
        elif comando == "w":
            jogo.tentar_rotacionar(horario=True)

        jogo.atualizar(0.5)

        if jogo.game_over:
            renderizar_console(jogo)
            print("Game Over")
            break
