from ursina import Ursina, application, time
from graficos_3d import VisualGrid
from logica_jogo import Jogo
from tracker import HandTracker

PASSO_MOVIMENTO_X = 0.05
PASSO_MOVIMENTO_Y = 0.04
LIMIAR_PUXAO_HARD_DROP = 0.14


if __name__ == "__main__":
    app = Ursina()

    jogo = Jogo()
    arena = VisualGrid(jogo.grid.largura, jogo.grid.altura)
    tracker = HandTracker()
    tracker.iniciar_thread()

    ancora_x = None
    ancora_y = None
    ultimo_y_mao = None
    peca_ancorada = None

    def input(key):
        global jogo, ancora_x, ancora_y, ultimo_y_mao
        if key in ("a", "left arrow"):
            jogo.tentar_mover(-1, 0)
        elif key in ("d", "right arrow"):
            jogo.tentar_mover(1, 0)
        elif key in ("s", "down arrow"):
            jogo.tentar_mover(0, 1)
        elif key == "space":
            jogo.queda_instantanea()
        elif key in ("c", "left shift", "right shift"):
            jogo.reservar_peca()
        elif key in ("w", "up arrow"):
            jogo.tentar_rotacionar(horario=True)
        elif key == "q":
            jogo.tentar_rotacionar(horario=False)
        elif key == "t":
            arena.alternar_tema()
        elif key == "m":
            arena.audio.alternar_musica()
        elif key == "g":
            arena.mostrar_fantasma = not arena.mostrar_fantasma
        elif key == "p":
            jogo.pausado = not jogo.pausado
        elif key == "r":
            jogo = Jogo()
            ancora_x = None
            ancora_y = None
            ultimo_y_mao = None
        elif key == "escape":
            tracker.fechar()
            arena.fechar()
            application.quit()

    def update():
        global ancora_x, ancora_y, ultimo_y_mao, peca_ancorada

        frame, gesto = tracker.obter_dados()
        if frame is not None and gesto is not None:
            arena.atualizar_camera(frame, gesto)

            if gesto.pinca_dupla:
                jogo.reservar_peca()
                ancora_x = None
                ancora_y = None
                ultimo_y_mao = None
            elif gesto.pinca_direita:
                jogo.tentar_rotacionar(horario=True)
            elif gesto.pinca_esquerda:
                jogo.tentar_rotacionar(horario=False)

            if gesto.punhos_fechados:
                if ancora_x is None or peca_ancorada is not jogo.peca_atual:
                    ancora_x = gesto.posicao_x
                    ancora_y = gesto.posicao_y
                    ultimo_y_mao = gesto.posicao_y
                    peca_ancorada = jogo.peca_atual
                else:
                    delta_x = gesto.posicao_x - ancora_x
                    while abs(delta_x) >= PASSO_MOVIMENTO_X:
                        direcao = 1 if delta_x > 0 else -1
                        jogo.tentar_mover(direcao, 0)
                        ancora_x += direcao * PASSO_MOVIMENTO_X
                        delta_x = gesto.posicao_x - ancora_x

                    velocidade_y = (
                        (gesto.posicao_y - ultimo_y_mao)
                        if ultimo_y_mao is not None
                        else 0.0
                    )
                    ultimo_y_mao = gesto.posicao_y

                    if velocidade_y >= LIMIAR_PUXAO_HARD_DROP:
                        jogo.queda_instantanea()
                        ancora_x = None
                        ancora_y = None
                        ultimo_y_mao = None
                    elif gesto.posicao_y < ancora_y:
                        ancora_y = gesto.posicao_y
                    else:
                        while (gesto.posicao_y - ancora_y) >= PASSO_MOVIMENTO_Y:
                            jogo.tentar_mover(0, 1)
                            ancora_y += PASSO_MOVIMENTO_Y
            else:
                ancora_x = None
                ancora_y = None
                ultimo_y_mao = None

        jogo.atualizar(time.dt)
        arena.atualizar(jogo)

    try:
        app.run()
    finally:
        tracker.fechar()
        arena.fechar()
