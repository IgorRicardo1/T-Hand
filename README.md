# T-Hand

Tetris com visual 3D controlado por rastreamento de mãos via webcam. As peças descem por um campo e o jogador usa gestos para mover e rotacionar.

## Como executar

### 1. Instalar o Python (3.12 ou superior)

Verifique no terminal se o Python já está instalado:

```powershell
python --version
```

Caso não tenha o Python (ou a versão seja inferior à 3.12), instale de uma das formas abaixo:
- **Pelo instalador oficial**: baixe em https://www.python.org/downloads/ e, na primeira tela da instalação no Windows, **marque a opção `"Add python.exe to PATH"`** antes de clicar em *Install Now*.
- **Pelo terminal do Windows (winget)**: rode `winget install Python.Python.3.12`.

Depois de instalar, feche e abra o terminal novamente para o comando `python` ser reconhecido.

### 2. Configurar o ambiente virtual e dependências

Na raiz do projeto, crie um ambiente virtual com `python -m venv .venv`, ative-o (no Windows: `.\.venv\Scripts\Activate.ps1`) e instale as dependências com `pip install -r requirements.txt`. Se o PowerShell bloquear a ativação, rode antes `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

O MediaPipe já instala o OpenCV, então não precisa instalar o `opencv-python` separado (os dois dão conflito). O modelo `hand_landmarker.task` já acompanha o projeto para execução offline.

### 3. Executar e testar

Com o ambiente virtual ativado:
- **Jogo completo (3D + Webcam)**: `python main.py`
- Versão 3D com teclado: `python graficos_3d.py` (A/D ou setas movem, W/Q giram, S acelera a queda, R reinicia).
- Lógica pelo terminal: `python logica_jogo.py` (A e D movem, W gira, Enter deixa cair, Q sai).
- Rastreamento da webcam isolado: `python tracker.py` (ESC fecha a janela).

## Status

Feito:
 - Lógica do jogo: peças, próxima peça, rotação, colisão, limpeza de linhas, pontuação e game over;
 - Gráficos 3D (`graficos_3d.py`);
 - Rastreamento de mãos (`tracker.py`);
 - Integração no `main.py`.

## Tecnologias

 - Python;
 - Ursina Engine (motor 3D);
 - MediaPipe (rastreamento de mãos).

## Controles

 - Duas mãos fechadas: move a peça para a esquerda ou para a direita;
 - Pinça com a mão direita: rotaciona a peça no sentido horário;
 - Pinça com a mão esquerda: rotaciona a peça no sentido anti-horário.

## Estrutura

➔```tracker.py```

- HandTracker - Inicializa a webcam e o MediaPipe. Processa cada frame e identifica os gestos das mãos;
- ResultadoGesto - Armazena o resultado dos gestos detectados em um frame (punhos fechados, pinça esquerda, pinça direita).

➔```logica_jogo.py```

Não depende do Ursina, o que permite testar a lógica isoladamente.

- CuboUnico - Representa um único cubo dentro de uma peça. Guarda sua posição relativa (x, y);
- PecasPossiveis - Define os formatos disponíveis das peças (os 7 tetrominós clássicos: I, O, T, S, Z, J, L);
- Peca - Uma peça em jogo: formato, posição no campo e rotação (90° no plano). Sabe se mover e rotacionar;
- Grid - Matriz 2D do campo de jogo contendo apenas as células já fixadas. Controla colisões, fixação de peças e limpeza de linhas completas;
- Jogo - Orquestra a partida. Guarda o Grid e a peça atual, controla a queda, a pontuação e o fim de jogo.

Ao encostar no fundo ou em outra peça, a peça atual é gravada no Grid (seus cubos viram células da matriz e ela deixa de existir como objeto) e uma nova peça é sorteada em seu lugar. Assim, sempre existe exatamente uma peça em movimento.

➔```graficos_3d.py```

- VisualBloco - Representação gráfica de um cubo na tela usando Ursina (cor, posição, textura);
- VisualGrid - Desenha a arena 3D (paredes, chão, iluminação) e sincroniza a visualização com a lógica do jogo (células do Grid e peça atual).

➔```main.py```

- Ponto de entrada. Instancia todas as classes, conecta os gestos da webcam à lógica do jogo e roda o loop principal do Ursina.
