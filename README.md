# T-Hand

Tetris 3D controlado por rastreamento de mãos via webcam. As peças descem em um fosso tridimensional e o jogador usa gestos para mover e rotacionar.

## Tecnologias

 - Python;
 - Ursina Engine (motor 3D);
 - MediaPipe (rastreamento de mãos).

## Controles

 - Duas mãos fechadas: move a peça;
 - Pinça com a mão direita: rotaciona a peça horizontal;
 - Pinça com a mão esquerda: rotaciona a peça vertical.

## Estrutura

➔```tracker.py```

- HandTracker - Inicializa a webcam e o MediaPipe. Processa cada frame e identifica os gestos das mãos;
- ResultadoGesto - Armazena o resultado dos gestos detectados em um frame (punhos fechados, pinça esquerda, pinça direita).

➔```logica_jogo.py```

- CuboUnico - Representa um único cubo dentro de uma peça. Guarda sua posiçao relativa (x, y, z);
- Grid - Matriz tridimensional do campo de jogo. Controla colisões, empilhamento e limpeza de camadas completas;
- PecasPossiveis - Define os formatos disponíveis das peças 3D e suas rotações.

➔```graficos_3d.py```

- VisualBloco - Representação gráfica de um cubo na tela usando Ursina (cor, posição, textura);
- VisualGrid - Desenha a arena 3D (paredes, chão, iluminação) e sincroniza a visualização com a lógica do jogo.

➔```main.py```

- Ponto de entrada. Instancia todas as classes, conecta os gestos da webcam a lógica do jogo e roda o loop principal do Ursina.
