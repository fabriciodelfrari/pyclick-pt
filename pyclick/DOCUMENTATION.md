# Documentação do Game Bot de Automação

## Visão Geral

Este bot foi desenvolvido para automatizar tarefas em jogos online, monitorando barras de status (HP, Mana, Energy), slots de poções, coletando drops automaticamente e simulando interações humanas (teclado e mouse). Ele utiliza visão computacional (OpenCV), OCR (Tesseract) e automação de interface (PyAutoGUI).

---

## Funcionalidades Principais

### 1. Monitoramento de Barras (HP, Mana, Energy)
- **Como funciona:**
  - O bot captura regiões específicas da tela onde ficam as barras de HP, Mana e Energy.
  - Analisa o nível de cada barra usando múltiplos métodos de visão computacional (intensidade de cor, gradiente, preenchimento vertical, etc).
  - Se o nível estiver baixo, executa ações automáticas para restaurar a barra (ex: usar poção).
- **Comandos simulados:**
  - Pressiona teclas específicas (ex: `1` para HP, `2` para Energy, `3` para Mana) usando `pyautogui.press()`.
  - Em situações críticas, pode pressionar a tecla duas vezes rapidamente.

### 2. Monitoramento e Reposição de Poções
- **Como funciona:**
  - Monitora slots de poções na tela para detectar quando estão vazios.
  - Usa análise de cor, intensidade e bordas para identificar slots vazios.
  - Quando detecta um slot vazio, tenta repor automaticamente a poção a partir do inventário.
- **Comandos simulados:**
  - Abre o inventário (`V`), localiza a poção pelo reconhecimento de cor, move o mouse até ela e executa combinações como `Shift+1`, `Shift+2`, `Shift+3` para recarregar os slots.
  - Usa `pyautogui.hotkey()` para combinações e `pyautogui.moveTo()`/`pyautogui.click()` para simular o uso do mouse.

### 3. Coleta Automática de Drops
- **Como funciona:**
  - Utiliza o módulo `drop_detector` para identificar itens no chão usando template matching (comparação de imagens) e, opcionalmente, OCR para ler nomes de itens.
  - Detecta moedas de ouro, poções e outros itens configurados.
  - Move o mouse até o item detectado e executa cliques para coletar.
  - Possui modos de coleta dinâmica (redetecção contínua) e varredura circular/quadrante para garantir a coleta mesmo com movimentação do personagem.
- **Comandos simulados:**
  - `pyautogui.moveTo(x, y)` para mover o mouse até o item.
  - `pyautogui.click()` para clicar e coletar.
  - Padrões de clique humano (espiral, circular, duplo clique, clique segurado) para simular comportamento real.

### 4. Sequência de Skills Especiais
- **Como funciona:**
  - Executa uma sequência de teclas e cliques (ex: F2 + clique direito, F3 + clique direito, F1) em intervalos configuráveis para ativar habilidades especiais do personagem.
- **Comandos simulados:**
  - `pyautogui.press('f2')`, `pyautogui.rightClick()`, etc.

### 5. Calibração Interativa de Regiões
- **Como funciona:**
  - Permite ao usuário ajustar manualmente as regiões de interesse (barras, poções, inventário, drops) com o mouse e teclado.
  - Salva e carrega configurações de calibração.
- **Comandos simulados:**
  - Interface gráfica com OpenCV para arrastar/redimensionar regiões.
  - Uso de teclas para selecionar/mover/redimensionar regiões.

### 6. Serviços em Background
- **Como funciona:**
  - Executa ações periódicas em segundo plano, como cliques automáticos com o botão direito do mouse para evitar desconexão do jogo.
- **Comandos simulados:**
  - `pyautogui.rightClick()` em intervalos regulares.

### 7. Configuração e Testes
- **Como funciona:**
  - Menus interativos para configurar parâmetros do bot (intervalos, thresholds, logs, etc).
  - Modos de teste para simular teclas, testar detecção de slots vazios, drops, diagnósticos de clique, etc.
- **Comandos simulados:**
  - Todos os comandos acima podem ser testados individualmente via menu.

---

## Módulo drop_detector.py

### Função: `load_templates()`
- Carrega imagens de referência (templates) dos itens a serem detectados (ouro, poções, etc) da pasta `drop_images`.

### Função: `find_drops(screenshot_frame, threshold=0.8)`
- Recebe um frame da tela e retorna as coordenadas dos itens detectados usando template matching.
- Utiliza OpenCV para comparar cada template com a tela e retorna os pontos centrais para clique.

---

## Simulação de Interação Humana

O bot utiliza diversas técnicas para simular o comportamento humano:
- Movimentação do mouse com pequenas variações e delays aleatórios.
- Cliques em padrões (espiral, circular, duplo clique, clique segurado).
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

## Observações Finais
- O bot é altamente configurável e modular.
- Possui logs detalhados e modos de debug para facilitar ajustes.
- A calibração das regiões é fundamental para o funcionamento correto.
- O uso de delays e padrões de clique ajuda a evitar detecção por sistemas anti-bot.

---

**Desenvolvido por Fabricio Costa — 2025**
