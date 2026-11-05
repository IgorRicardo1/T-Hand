from ursina import Ursina, application, time

from graficos_3d import VisualGrid
from logica_jogo import Jogo
from tracker import HandTracker, LeituraGesto, TipoGesto

PASSO_ARRASTO_X = 0.05  # ~5% da largura da câmera equivale a 1 coluna do Grid


class ControladorGestos:
    def __init__(self):
        self._ancora_x: float | None = None
        self._peca_ancorada = None

    def resetar(self):
        self._ancora_x = None
        self._peca_ancorada = None

    def aplicar(self, leitura: LeituraGesto, jogo: Jogo):
        gesto, pos_x = leitura

        if gesto == TipoGesto.PINCA_DIREITA:
            self._ancora_x = None
            jogo.tentar_rotacionar(horario=True)
            return

        if gesto == TipoGesto.PINCA_ESQUERDA:
            self._ancora_x = None
            jogo.tentar_rotacionar(horario=False)
            return

        if gesto == TipoGesto.PUNHOS_FECHADOS and pos_x is not None:
            if self._ancora_x is None or jogo.peca_atual is not self._peca_ancorada:
                self._ancora_x = pos_x
                self._peca_ancorada = jogo.peca_atual
                return

            delta = pos_x - self._ancora_x
            while abs(delta) >= PASSO_ARRASTO_X:
                direcao = 1 if delta > 0 else -1
                jogo.tentar_mover(direcao, 0)
                self._ancora_x += direcao * PASSO_ARRASTO_X
                delta = pos_x - self._ancora_x

        else:
            self._ancora_x = None


if __name__ == "__main__":
    app = Ursina()

    jogo = Jogo()
    arena = VisualGrid(jogo.grid.largura, jogo.grid.altura)
    controlador = ControladorGestos()

    tracker = HandTracker()
    tracker.iniciar()

    def input(key):
        global jogo
        if key in ("a", "left arrow"):
            jogo.tentar_mover(-1, 0)
        elif key in ("d", "right arrow"):
            jogo.tentar_mover(1, 0)
        elif key in ("s", "down arrow"):
            jogo.tentar_mover(0, 1)
        elif key in ("w", "up arrow"):
            jogo.tentar_rotacionar(horario=True)
        elif key == "q":
            jogo.tentar_rotacionar(horario=False)
        elif key == "r":
            jogo = Jogo()
            controlador.resetar()
        elif key == "escape":
            tracker.fechar()
            application.quit()

    def update():
        dados = tracker.obter_dados()
        if dados is not None:
            frame, leitura = dados
            controlador.aplicar(leitura, jogo)
            arena.atualizar_fundo(frame)

        jogo.atualizar(time.dt)
        arena.atualizar(jogo)

    try:
        app.run()
    finally:
        tracker.fechar()