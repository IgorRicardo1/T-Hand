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

 Duas mãos fechadas: move a peca 
 Pinca com a mao direita: rotaciona a peca horizontal
 Pinca com a mao esquerda: rotaciona a peca vertical

Estrutura

    tracker.py

HandTracker - Inicializa a webcam e o MediaPipe. Processa cada frame e identifica os gestos das maos.
Resultado_gesto - Armazena o resultado dos gestos detectados em um frame (punhos fechados, pinca esquerda, pinca direita).

    logica_jogo.py

Cubo_unico - Representa um unico cubo dentro de uma peca. Guarda sua posicao relativa (x, y, z).
Grid - Matriz tridimensional do campo de jogo. Controla colisoes, empilhamento e limpeza de camadas completas.
Pecas_possiveis - Define os formatos disponiveis das pecas 3D e suas rotacoes.

    graficos_3d.py

Visual_do_bloco - Representacao grafica de um cubo na tela usando Ursina (cor, posicao, textura).
Visual_do_Grid - Desenha a arena 3D (paredes, chao, iluminacao) e sincroniza a visualizacao com a logica do jogo.

main.py

Ponto de entrada. Instancia todas as classes, conecta os gestos da webcam a logica do jogo e roda o loop principal do Ursina.
