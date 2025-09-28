# Documentação do Game Bot de Automação

## Visão Geral

Este projeto consiste em um conjunto de scripts modulares para automatizar tarefas em jogos online. Ele utiliza visão computacional (OpenCV), reconhecimento óptico de caracteres (OCR com Tesseract) e automação de interface de usuário (PyAutoGUI) para simular interações humanas.

O sistema é dividido em três componentes principais que podem ser executados de forma independente ou coordenada:
1.  **`game_automation.py`**: O núcleo do bot, responsável pelo monitoramento de status do personagem e automação de combate/suporte.
2.  **`gold_drop_collector.py`**: Um coletor de drops especializado que usa template matching e varredura de área.
3.  **`reconhecimento_drop.py`**: Um sistema avançado de reconhecimento de drops que utiliza OCR para ler nomes de itens.

---

## Módulos e Funcionalidades

### 1. `game_automation.py` - Automação Principal
Este é o orquestrador central que gerencia as ações de sobrevivência e combate do personagem.

- **Monitoramento de Barras (HP, Mana, Energy):**
- **Como funciona:**
  - O bot captura regiões específicas da tela onde ficam as barras de HP, Mana e Energy.
  - Analisa o nível de cada barra usando múltiplos métodos de visão computacional (intensidade de cor, gradiente, preenchimento vertical, etc).
  - Se o nível estiver baixo, executa ações automáticas para restaurar a barra (ex: usar poção).
- **Comandos simulados:**
  - Pressiona teclas específicas (ex: `1` para HP, `2` para Energy, `3` para Mana) usando `pyautogui.press()`.
  - Em situações críticas, pode pressionar a tecla duas vezes rapidamente.
- **Monitoramento e Reposição de Poções:**
- **Como funciona:**
  - Monitora slots de poções na tela para detectar quando estão vazios.
  - Usa análise de cor, intensidade e bordas para identificar slots vazios.
  - Quando detecta um slot vazio, tenta repor automaticamente a poção a partir do inventário.
- **Comandos simulados:**
  - Abre o inventário (`V`), localiza a poção pelo reconhecimento de cor, move o mouse até ela e executa combinações como `Shift+1`, `Shift+2`, `Shift+3` para recarregar os slots.
  - Usa `pyautogui.hotkey()` para combinações e `pyautogui.moveTo()`/`pyautogui.click()` para simular o uso do mouse.
- **Sequência de Skills Especiais:**
- **Como funciona:**
  - Executa uma sequência de teclas e cliques (ex: F2 + clique direito, F3 + clique direito, F1) em intervalos configuráveis para ativar habilidades especiais do personagem.
- **Comandos simulados:**
  - `pyautogui.press('f2')`, `pyautogui.rightClick()`, etc.
- **Serviços em Background:**
- **Como funciona:**
  - Executa ações periódicas em segundo plano, como cliques automáticos com o botão direito do mouse para evitar desconexão do jogo.
- **Comandos simulados:**
  - `pyautogui.rightClick()` em intervalos regulares.

### 2. `gold_drop_collector.py` - Coletor de Drops por Imagem
Este módulo é focado na coleta de itens no chão e pode ser executado a partir de seu próprio menu.
- **Como funciona:**
  - **Modo 1: Detecção Visual:** Utiliza template matching (OpenCV `matchTemplate`) para encontrar imagens de itens (ex: `GOLD_drop.bmp`) na tela. É rápido e preciso para itens com aparência consistente.
  - **Modo 2: Varredura Cega:** Clica sistematicamente em uma grade de pontos dentro da área de busca definida. É um método de força bruta para garantir que nenhum item seja perdido, mesmo que não seja reconhecido visualmente.
  - **Integração:** Usa o `global_vars.py` para pausar a coleta quando o `game_automation.py` está repondo poções, evitando conflitos de ação.
- **Comandos simulados:**
  - `pyautogui.moveTo(x, y)` para mover o mouse até o item.
  - `pyautogui.click()` para clicar e coletar.

### 3. `reconhecimento_drop.py` - Coletor de Drops por OCR
Um módulo autônomo e mais avançado para identificar drops.
- **Como funciona:**
  - **Reconhecimento de Texto (OCR):** Usa a biblioteca Tesseract para "ler" o nome dos itens que aparecem na tela. Isso permite identificar uma variedade maior de drops sem precisar de uma imagem de template para cada um.
  - **Detecção de Formas:** Identifica as "barras brancas" de texto sobre os itens no chão, permitindo clicar em drops mesmo que o OCR falhe em ler o texto.
  - **Pré-processamento de Imagem:** Aplica filtros (tons de cinza, binarização, dilatação) para melhorar a precisão do Tesseract.

### 4. Funcionalidades Comuns
- **Calibração Interativa de Regiões:**
- **Como funciona:**
  - Todos os módulos principais (`game_automation`, `gold_drop_collector`, `reconhecimento_drop`) possuem uma interface gráfica (usando OpenCV) que permite ao usuário desenhar, mover e redimensionar as áreas de interesse (barras de status, área de coleta, etc.).
  - As configurações são salvas em arquivos de backup (`.txt`) para serem carregadas automaticamente nas próximas execuções.
- **Comandos simulados:**
  - Interface gráfica com OpenCV para arrastar/redimensionar regiões.
  - Uso de teclas para selecionar/mover/redimensionar regiões.
- **Parada de Emergência:**
- **Como funciona:**
  - A tecla **F12** funciona como um interruptor global para pausar/retomar todos os serviços de automação. Isso é gerenciado através do `global_vars.py`.
- **Menus e Testes:**
- **Como funciona:**
  - Cada script principal oferece um menu de linha de comando para iniciar a automação, calibrar regiões ou executar rotinas de diagnóstico e teste.
- **Comandos simulados:**
  - Os modos de teste permitem verificar a simulação de teclas, a detecção de barras/poções e outras funcionalidades de forma isolada.

---

## Simulação de Interação Humana

O bot utiliza diversas técnicas para simular o comportamento humano:
- Movimentação do mouse com pequenas variações e delays aleatórios.
- Pequenos delays entre ações para evitar detecção por sistemas anti-bot.
- Uso de combinações de teclas e mouse de forma natural.

**Principais comandos PyAutoGUI usados:**
- `pyautogui.press(tecla)` — Pressiona uma tecla.
- `pyautogui.hotkey(teclas...)` — Pressiona uma combinação de teclas.
- `pyautogui.moveTo(x, y, duration)` — Move o mouse até a posição (x, y) com duração opcional.
- `pyautogui.click()` — Clique simples.
- `pyautogui.rightClick()` — Clique com o botão direito.
- `pyautogui.mouseDown()` / `pyautogui.mouseUp()` — Pressiona/solta o botão do mouse.

---

## Como Usar
- O bot é altamente configurável e modular.
- A calibração das regiões é fundamental para o funcionamento correto.
- Execute `game_automation.py` para o monitoramento principal.
- Execute `gold_drop_collector.py` ou `reconhecimento_drop.py` para coleta de itens.
- Use os menus interativos para calibrar as regiões antes de iniciar a automação pela primeira vez.

---

## Gerando um Executável (Standalone)

Para distribuir o bot como um programa único que não requer a instalação do Python na máquina de destino, você pode gerar um arquivo executável (`.exe`) usando a ferramenta `PyInstaller`.

### 1. Instalação do PyInstaller

Primeiro, instale o PyInstaller através do pip no seu terminal:

```bash
pip install pyinstaller
```

### 2. Comando para Gerar o Executável

Como o projeto depende de arquivos externos (imagens, templates), você precisa instruir o `PyInstaller` a incluí-los. O ponto de entrada principal é o `game_automation.py`.

Use o seguinte comando no terminal, na pasta raiz do projeto:

```bash
pyinstaller --name "GameBot" --onefile --windowed --add-data "images;images" game_automation.py
```

**Análise do comando:**

*   `--name "GameBot"`: Define o nome do arquivo executável que será gerado (ex: `GameBot.exe`).
*   `--onefile`: Agrupa tudo em um único arquivo executável para facilitar a distribuição.
*   `--windowed`: Como o bot usa uma interface gráfica (`gui.py`), este comando evita que uma janela de console (terminal preto) seja aberta junto com a aplicação.
*   `--add-data "images;images"`: Este é o comando mais importante. Ele copia a pasta `images` (source) para dentro do pacote, mantendo o nome `images` (destination). O formato é `source;destination` no Windows.

Após executar o comando, o `PyInstaller` criará uma pasta chamada `dist`. Dentro dela, você encontrará o `GameBot.exe`, pronto para ser executado em qualquer computador Windows.

---

**Desenvolvido por Fabricio Costa**
