import math
from pathlib import Path
import threading
import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

CAMINHO_MODELO = Path(__file__).with_name("hand_landmarker.task")
DEDOS = ((8, 6), (12, 10), (16, 14), (20, 18))


class ResultadoGesto:
    def __init__(
        self,
        punhos_fechados=False,
        pinca_esquerda=False,
        pinca_direita=False,
        pinca_dupla=False,
        posicao_x=None,
        posicao_y=None,
    ):
        self.punhos_fechados = punhos_fechados
        self.pinca_esquerda = pinca_esquerda
        self.pinca_direita = pinca_direita
        self.pinca_dupla = pinca_dupla
        self.posicao_x = posicao_x
        self.posicao_y = posicao_y


class HandTracker:
    """Captura webcam + MediaPipe em thread dedicada para manter o motor 3D cravado em 60+ FPS."""

    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        self.timestamp = 0
        self.pinca_anterior = {"Esquerda": False, "Direita": False, "Dupla": False}

        opcoes = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(CAMINHO_MODELO)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
        )
        self.detector = vision.HandLandmarker.create_from_options(opcoes)

        self._lock = threading.Lock()
        self._rodando = False
        self._thread = None
        self._frame_pronto = None
        self._gesto_acumulado = ResultadoGesto()
        self._tem_novo = False

    def _distancia(self, p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def _eh_punho(self, mao):
        pulso = mao[0]
        return all(
            self._distancia(mao[ponta], pulso) < self._distancia(mao[dobra], pulso)
            for ponta, dobra in DEDOS
        )

    def _eh_pinca(self, mao):
        palma = self._distancia(mao[0], mao[9])
        if palma == 0 or self._eh_punho(mao):
            return False
        return (self._distancia(mao[4], mao[8]) / palma) < 0.35

    def _desenhar_hud_ar(self, frame, mao, cor_linha, cor_ponto):
        altura, largura = frame.shape[:2]
        overlay = frame.copy()
        pts = [(int(p.x * largura), int(p.y * altura)) for p in mao]

        # Halo luminoso translúcido no esqueleto
        for con in vision.HandLandmarksConnections.HAND_CONNECTIONS:
            cv2.line(overlay, pts[con.start], pts[con.end], cor_linha, 6, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

        for con in vision.HandLandmarksConnections.HAND_CONNECTIONS:
            cv2.line(frame, pts[con.start], pts[con.end], (255, 255, 255), 2, cv2.LINE_AA)

        for idx, pt in enumerate(pts):
            raio = 6 if idx in (4, 8, 12, 16, 20) else 3
            cv2.circle(frame, pt, raio, cor_ponto, -1, cv2.LINE_AA)

    def ler_frame(self):
        sucesso, frame = self.cap.read()
        if not sucesso:
            return None, ResultadoGesto()

        frame = cv2.flip(frame, 1)
        altura, largura = frame.shape[:2]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imagem_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        self.timestamp += 33
        resultado_mp = self.detector.detect_for_video(imagem_mp, self.timestamp)

        gesto = ResultadoGesto()
        centros_punhos_x = []
        centros_punhos_y = []
        pontos_punhos_px = []
        pinca_atual = {"Esquerda": False, "Direita": False}

        for mao, classificacao in zip(
            resultado_mp.hand_landmarks, resultado_mp.handedness
        ):
            lado = "Direita" if classificacao[0].category_name == "Left" else "Esquerda"
            punho = self._eh_punho(mao)
            pinca = not punho and self._eh_pinca(mao)

            if punho:
                cor_l, cor_p = (80, 255, 140), (0, 255, 100)
            elif pinca:
                cor_l, cor_p = (255, 220, 40), (0, 220, 255)
            else:
                cor_l, cor_p = (220, 90, 255), (255, 255, 255)

            self._desenhar_hud_ar(frame, mao, cor_l, cor_p)

            if punho:
                centros_punhos_x.append(mao[9].x)
                centros_punhos_y.append(mao[9].y)
                px, py = int(mao[9].x * largura), int(mao[9].y * altura)
                pontos_punhos_px.append((px, py))
                cv2.circle(frame, (px, py), 22, (0, 255, 120), 2, cv2.LINE_AA)
            elif pinca:
                pinca_atual[lado] = True
                px = int(((mao[4].x + mao[8].x) / 2) * largura)
                py = int(((mao[4].y + mao[8].y) / 2) * altura)
                cv2.circle(frame, (px, py), 24, (0, 230, 255), 3, cv2.LINE_AA)
                cv2.circle(frame, (px, py), 6, (255, 255, 255), -1, cv2.LINE_AA)

        dupla_agora = pinca_atual["Esquerda"] and pinca_atual["Direita"]

        if len(centros_punhos_x) == 2:
            gesto.punhos_fechados = True
            gesto.posicao_x = sum(centros_punhos_x) / 2
            gesto.posicao_y = sum(centros_punhos_y) / 2

            p1, p2 = pontos_punhos_px
            mx, my = int(gesto.posicao_x * largura), int(gesto.posicao_y * altura)
            cv2.line(frame, p1, p2, (0, 255, 140), 3, cv2.LINE_AA)
            # Mira sci-fi no centro de controle
            cv2.circle(frame, (mx, my), 20, (0, 255, 140), 2, cv2.LINE_AA)
            cv2.line(frame, (mx - 26, my), (mx + 26, my), (255, 255, 255), 1, cv2.LINE_AA)
            cv2.line(frame, (mx, my - 26), (mx, my + 26), (255, 255, 255), 1, cv2.LINE_AA)
            cv2.circle(frame, (mx, my), 5, (255, 255, 255), -1, cv2.LINE_AA)
        elif dupla_agora:
            if not self.pinca_anterior["Dupla"]:
                gesto.pinca_dupla = True
        else:
            gesto.pinca_esquerda = (
                pinca_atual["Esquerda"] and not self.pinca_anterior["Esquerda"]
            )
            gesto.pinca_direita = (
                pinca_atual["Direita"] and not self.pinca_anterior["Direita"]
            )

        self.pinca_anterior = {
            "Esquerda": pinca_atual["Esquerda"],
            "Direita": pinca_atual["Direita"],
            "Dupla": dupla_agora,
        }
        return frame, gesto

    def _loop_thread(self):
        while self._rodando:
            frame, gesto = self.ler_frame()
            if frame is None:
                continue
            with self._lock:
                # Preserva pulsos instantâneos de pinça caso o Ursina ainda não tenha lido
                if self._tem_novo:
                    gesto.pinca_esquerda = (
                        gesto.pinca_esquerda or self._gesto_acumulado.pinca_esquerda
                    )
                    gesto.pinca_direita = (
                        gesto.pinca_direita or self._gesto_acumulado.pinca_direita
                    )
                    gesto.pinca_dupla = (
                        gesto.pinca_dupla or self._gesto_acumulado.pinca_dupla
                    )
                self._frame_pronto = frame
                self._gesto_acumulado = gesto
                self._tem_novo = True

    def iniciar_thread(self):
        if self._rodando:
            return
        self._rodando = True
        self._thread = threading.Thread(target=self._loop_thread, daemon=True)
        self._thread.start()

    def obter_dados(self):
        with self._lock:
            if not self._tem_novo or self._frame_pronto is None:
                return None, None
            self._tem_novo = False
            return self._frame_pronto, self._gesto_acumulado

    def fechar(self):
        self._rodando = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self.cap.release()
        self.detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    tracker = HandTracker()

    while True:
        frame, gesto = tracker.ler_frame()
        if frame is None:
            break

        cv2.imshow("T-Hand AR Tracker", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    tracker.fechar()
