from pathlib import Path
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

URL_MODELO = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
CAMINHO_MODELO = Path(__file__).with_name("hand_landmarker.task")


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
        if not CAMINHO_MODELO.exists():
            urllib.request.urlretrieve(URL_MODELO, CAMINHO_MODELO)

        self.cap = cv2.VideoCapture(camera_index)
        self.timestamp = 0

        opcoes = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(CAMINHO_MODELO)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
        )
        self.detector = vision.HandLandmarker.create_from_options(opcoes)

    def ler_frame(self):
        sucesso, frame = self.cap.read()
        if not sucesso:
            return None, ResultadoGesto()

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imagem_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        self.timestamp += 33
        resultado_mp = self.detector.detect_for_video(imagem_mp, self.timestamp)

        for mao in resultado_mp.hand_landmarks:
            vision.drawing_utils.draw_landmarks(
                frame, mao, vision.HandLandmarksConnections.HAND_CONNECTIONS
            )

        return frame, ResultadoGesto()

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

        cv2.imshow("T-Hand", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    tracker.fechar()
