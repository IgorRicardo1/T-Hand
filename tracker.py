import math
from pathlib import Path
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
        posicao_x=None,
    ):
        self.punhos_fechados = punhos_fechados
        self.pinca_esquerda = pinca_esquerda
        self.pinca_direita = pinca_direita
        self.posicao_x = posicao_x


class HandTracker:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        self.timestamp = 0

        opcoes = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(CAMINHO_MODELO)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
        )
        self.detector = vision.HandLandmarker.create_from_options(opcoes)

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

    def ler_frame(self):
        sucesso, frame = self.cap.read()
        if not sucesso:
            return None, ResultadoGesto()

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imagem_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        self.timestamp += 33
        resultado_mp = self.detector.detect_for_video(imagem_mp, self.timestamp)

        gesto = ResultadoGesto()
        centros_punhos_x = []

        for mao, classificacao in zip(
            resultado_mp.hand_landmarks, resultado_mp.handedness
        ):
            vision.drawing_utils.draw_landmarks(
                frame, mao, vision.HandLandmarksConnections.HAND_CONNECTIONS
            )

            eh_direita = classificacao[0].category_name == "Left"

            if self._eh_punho(mao):
                centros_punhos_x.append(mao[9].x)
            elif self._eh_pinca(mao):
                if eh_direita:
                    gesto.pinca_direita = True
                else:
                    gesto.pinca_esquerda = True

        if len(centros_punhos_x) == 2:
            gesto.punhos_fechados = True
            gesto.posicao_x = sum(centros_punhos_x) / 2

        return frame, gesto

    def fechar(self):
        self.cap.release()
        self.detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    tracker = HandTracker()

    while True:
        frame, gesto = tracker.ler_frame()
        if frame is None:
            break

        status = []
        if gesto.punhos_fechados:
            status.append(f"PUNHOS (x={gesto.posicao_x:.2f})")
        if gesto.pinca_esquerda:
            status.append("PINCA ESQ")
        if gesto.pinca_direita:
            status.append("PINCA DIR")

        cv2.putText(
            frame,
            " | ".join(status) or "Nenhum gesto",
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

        cv2.imshow("T-Hand", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    tracker.fechar()
