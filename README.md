T-Hand

Um jogo de empilhar blocos baseado em física (estilo Tricky Towers), controlado através do rastreamento da mão do jogador via webcam. O objetivo é empilhar peças geométricas o mais alto possível sem deixar a torre perder o equilíbrio e desmoronar.

Principais Mecânicas:

- Rastreamento da Mão: O jogo desenha e espelha os movimentos da mão do jogador em tempo real na tela.
- Agarrar (Pinça): O jogador junta o polegar e o indicador para segurar e mover uma peça.
- Rotação: A peça rotaciona acompanhando a inclinação real do pulso do jogador.
- Física Híbrida (2D/3D): As peças são modelos 3D que caem com gravidade e sofrem colisões realistas, mas a física é travada nos eixos X e Y para evitar frustrações com a falta de percepção de profundidade da webcam.

Tecnologias

- Python: Linguagem de programação base.
- MediaPipe: Rastreamento contínuo dos 21 pontos (landmarks) da mão.
- OpenCV: Captura e processamento inicial dos frames da webcam.
- Ursina Engine: Motor gráfico para renderização do ambiente e iluminação 3D.
- Panda3D Bullet: Motor de física que controla a gravidade, colisões, atrito e corpos rígidos.

Controles

- Pinça (polegar + indicador): Agarra a peça mais próxima da mão virtual.
- Mover a mão com pinça ativa: Arrasta a peça pela tela.
- Girar o pulso com pinça ativa: Rotaciona a peça.
- Abrir a mão (soltar a pinça): Solta a peça e a gravidade volta a agir.
- Espaço (teclado): Spawna uma nova peça no topo da tela.

Estrutura

   constantes.py

Parâmetros de configuração do jogo (gravidade, massa, atrito, thresholds de pinça, posição da câmera, cores das peças, etc).

    peca.py

Classe Peca. Encapsula o corpo rígido (Bullet), o visual (Ursina) e a lógica de agarrar, soltar, mover e rotacionar.

    tracker.py

Captura da webcam via OpenCV e processamento dos frames com MediaPipe. Detecta os 21 landmarks da mão e calcula os gestos (pinça ativa, ângulo do pulso, posição da palma).

    fisica.py

Inicialização do BulletWorld e criação dos corpos rígidos estáticos (chão, paredes). Define gravidade e substeps da simulação.

    graficos.py

Configuração da câmera, iluminação e HUD. Sincroniza os visuais com os nós físicos do Bullet via reparent_to.

    jogo.py

Lógica central do jogo. Conecta o tracker às peças: converte coordenadas dos landmarks em posições do mundo, gerencia o estado de agarrar/soltar com histerese e spawna novas peças.
    
    main.py

Ponto de entrada. Instancia os módulos, inicia a Ursina e roda o loop principal.
