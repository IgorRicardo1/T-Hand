from ursina import Ursina, application, time
from graficos_3d import VisualGrid
from logica_jogo import Jogo
from tracker import HandTracker

PASSO_MOVIMENTO_X = 0.05


if __name__ == "__main__":
    app = Ursina()

    jogo = Jogo()
    arena = VisualGrid(jogo.grid.largura, jogo.grid.altura)
    tracker = HandTracker()

    ancora_x = None
    peca_ancorada = None

    def input(key):
        global jogo, ancora_x
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
            ancora_x = None
        elif key == "escape":
            tracker.fechar()
            application.quit()

    def update():
        global ancora_x, peca_ancorada

        frame, gesto = tracker.ler_frame()
        if frame is not None:
            arena.atualizar_camera(frame)

            if gesto.pinca_direita:
                jogo.tentar_rotacionar(horario=True)
            elif gesto.pinca_esquerda:
                jogo.tentar_rotacionar(horario=False)

            if gesto.punhos_fechados:
                if ancora_x is None or peca_ancorada is not jogo.peca_atual:
                    ancora_x = gesto.posicao_x
                    peca_ancorada = jogo.peca_atual
                else:
                    delta = gesto.posicao_x - ancora_x
                    while abs(delta) >= PASSO_MOVIMENTO_X:
                        direcao = 1 if delta > 0 else -1
                        jogo.tentar_mover(direcao, 0)
                        ancora_x += direcao * PASSO_MOVIMENTO_X
                        delta = gesto.posicao_x - ancora_x
            else:
                ancora_x = None

        jogo.atualizar(time.dt)
        arena.atualizar(jogo)

    app.run()
    tracker.fechar()
