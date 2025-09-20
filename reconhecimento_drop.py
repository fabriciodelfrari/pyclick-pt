import time
import re
import numpy as np
import cv2
import mss
import pytesseract
from PIL import Image
import logging
import pyautogui
import os
import random  # Corrige erro: random não está definido

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define o nome do arquivo de backup da calibração
CALIBRATION_BACKUP_FILE = 'reconhecimento_drop_calibration_backup.txt'

def save_calibration_backup(monitor_region):
    """Salva as coordenadas da região do monitor em um arquivo de backup."""
    try:
        with open(CALIBRATION_BACKUP_FILE, 'w') as f:
            f.write(f"monitor_region = {monitor_region}\n")
        logging.info(f"Backup da calibração salvo em '{CALIBRATION_BACKUP_FILE}'")
    except Exception as e:
        logging.error(f"Erro ao salvar backup da calibração: {e}")

def load_calibration_backup():
    """Carrega as coordenadas da região do monitor de um arquivo de backup."""
    if os.path.exists(CALIBRATION_BACKUP_FILE):
        try:
            with open(CALIBRATION_BACKUP_FILE, 'r') as f:
                content = f.read()
            
            # Extrai a região usando parsing de string simples
            region_str = content.split("monitor_region = ")[1].strip()
            
            # Usa eval para converter a representação de string da tupla de volta para o objeto real
            loaded_region = eval(region_str)
            logging.info(f"Calibração carregada de '{CALIBRATION_BACKUP_FILE}' com sucesso.")
            return loaded_region
        except Exception as e:
            logging.error(f"Erro ao carregar calibração de '{CALIBRATION_BACKUP_FILE}': {e}")
            return None
    else:
        logging.info(f"Arquivo de backup de calibração '{CALIBRATION_BACKUP_FILE}' não encontrado. Usando configurações padrão.")
        return None

def calibrate_monitor_region(initial_region):
    """Sistema interativo de calibração da região do monitor."""
    logging.info("🎯 SISTEMA DE CALIBRAÇÃO DA REGIÃO DO MONITOR")
    logging.info("=" * 50)
    logging.info("INSTRUÇÕES:")
    logging.info("- 🖱️  CLIQUE E ARRASTE para mover ou desenhar a região.")
    logging.info("- [WASD] - Mover a região selecionada (5 pixels)")
    logging.info("- [+/-] - Aumentar/diminuir largura (5 pixels)")
    logging.info("- [[]/] - Aumentar/diminuir altura (5 pixels)")
    logging.info("- [R] - Resetar a região para o padrão (tela cheia)")
    logging.info("- [SPACE] - Salvar as coordenadas e sair")
    logging.info("- [Q/ESC] - Sair sem salvar")
    logging.info("")

    screen_width, screen_height = pyautogui.size()
    # Convert initial_region dict to a mutable list [left, top, width, height]
    monitor_region_list = [
        initial_region["left"],
        initial_region["top"],
        initial_region["width"],
        initial_region["height"]
    ]

    drawing = False
    drag_start = None
    drag_offset = None
    scale = 0.7 # Scale for display, actual coordinates are full size

    # Default for reset (full screen)
    default_full_screen_region_list = [0, 0, screen_width, screen_height]

    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, drag_start, drag_offset, monitor_region_list

        # Convert scaled display coordinates to real screen coordinates
        real_x = int(x / scale)
        real_y = int(y / scale)

        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if clicking inside the monitor_region
            rx, ry, rw, rh = monitor_region_list
            if rx <= real_x <= rx + rw and ry <= real_y <= ry + rh:
                drawing = True
                drag_start = (real_x, real_y)
                drag_offset = (real_x - rx, real_y - ry)
            else: # If clicking outside, start a new drag to define a new region
                drawing = True
                drag_start = (real_x, real_y)
                monitor_region_list[0] = real_x
                monitor_region_list[1] = real_y
                monitor_region_list[2] = 1 # Minimum width
                monitor_region_list[3] = 1 # Minimum height


        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            if drag_offset: # Moving an existing region
                new_x = real_x - drag_offset[0]
                new_y = real_y - drag_offset[1]
                monitor_region_list[0] = new_x
                monitor_region_list[1] = new_y
            else: # Drawing a new region
                x1, y1 = drag_start
                x2, y2 = real_x, real_y
                monitor_region_list[0] = min(x1, x2)
                monitor_region_list[1] = min(y1, y2)
                monitor_region_list[2] = abs(x1 - x2)
                monitor_region_list[3] = abs(y1 - y2)
                # Ensure minimum size
                if monitor_region_list[2] < 10: monitor_region_list[2] = 10
                if monitor_region_list[3] < 10: monitor_region_list[3] = 10


        elif event == cv2.EVENT_LBUTTONUP:
            if drawing:
                drawing = False
                drag_start = None
                drag_offset = None
                logging.info(f"Região definida: left={monitor_region_list[0]}, top={monitor_region_list[1]}, width={monitor_region_list[2]}, height={monitor_region_list[3]}")

    window_name = 'Calibracao da Regiao do Monitor - Clique e Arraste'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)

    while True:
        frame = pyautogui.screenshot()
        frame_np = np.array(frame)
        display_frame = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)

        # Draw the current monitor_region
        x, y, w, h = monitor_region_list
        color = (0, 255, 0) # Green
        thickness = 2
        cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, thickness)
        cv2.putText(display_frame, f"Regiao do Monitor: left={x}, top={y}, width={w}, height={h}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Resize for display
        height, width = display_frame.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)
        display_frame = cv2.resize(display_frame, (new_width, new_height))

        # Add instructions on screen
        instructions = [
            "CLIQUE E ARRASTE para mover ou desenhar a regiao",
            "WASD: Mover | +/-: Largura | [ ]: Altura",
            "R: Resetar | SPACE: Salvar | Q/ESC: Sair"
        ]

        for i, instruction in enumerate(instructions):
            y_pos = display_frame.shape[0] - 80 + (i * 25)
            cv2.putText(display_frame, instruction, (10, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow(window_name, display_frame)

        key = cv2.waitKey(1) & 0xFF

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break

        if key == ord('q') or key == 27: # Q or ESC
            break
        elif key == ord(' '): # SPACE to save
            # Convert list back to dictionary format for saving
            calibrated_region_dict = {
                "left": monitor_region_list[0],
                "top": monitor_region_list[1],
                "width": monitor_region_list[2],
                "height": monitor_region_list[3]
            }
            save_calibration_backup(calibrated_region_dict)
            break
        elif key == ord('r'): # Reset to full screen
            monitor_region_list = list(default_full_screen_region_list)
            logging.info("Região resetada para tela cheia.")

        # Movement (WASD) and Resize
        if key == ord('w'): # Up
            monitor_region_list[1] -= 5
        elif key == ord('s'): # Down
            monitor_region_list[1] += 5
        elif key == ord('a'): # Left
            monitor_region_list[0] -= 5
        elif key == ord('d'): # Right
            monitor_region_list[0] += 5
        elif key == ord('+') or key == ord('='):  # Aumentar largura
            monitor_region_list[2] += 5
        elif key == ord('-'):  # Diminuir largura
            monitor_region_list[2] = max(10, monitor_region_list[2] - 5)
        elif key == ord('['): # Aumentar altura
            monitor_region_list[3] += 5
        elif key == ord(']'): # Diminuir altura
            monitor_region_list[3] = max(10, monitor_region_list[3] - 5)

        time.sleep(0.01) # Small delay for smoother display

    cv2.destroyAllWindows()
    # Return the final region as a dictionary
    return {
        "left": monitor_region_list[0],
        "top": monitor_region_list[1],
        "width": monitor_region_list[2],
        "height": monitor_region_list[3]
    }

# --------------------------
# CONFIGURAÇÕES ESSENCIAIS
# --------------------------

# 1. Ajuste o caminho para o executável do Tesseract.
# Se você adicionou ao PATH (recomendado), pode ser apenas 'tesseract'.
# Se não, coloque o caminho completo: Ex: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# 2. Defina a Região de Interesse (ROI) para a captura.
# Otimize ao máximo para cobrir apenas os drops.
# Exemplo (ajuste esses valores para o seu monitor e jogo!):
MONITOR_REGION = {
    "top": 350,      # Coordenada Y (vertical) do topo
    "left": 550,     # Coordenada X (horizontal) da esquerda
    "width": 300,    # Largura da área a ser capturada
    "height": 250    # Altura da área a ser capturada
}

# 3. Configurações para o Tesseract para melhorar o OCR em jogos.
# --psm 6: Assumir um bloco uniforme de texto.
# Whitelist: Restringe os caracteres que o OCR procura (números, letras, ':').
# Isso aumenta a velocidade e a precisão, ignorando lixo.
TESSERACT_CONFIG = '--psm 6 -c tessedit_char_whitelist="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ: "'

# 4. Intervalo entre as capturas (em segundos).
# 0.1s = 10 capturas por segundo. Ajuste para balancear performance e tempo real.
SCAN_INTERVAL = 0.2  # 5 capturas por segundo

# --------------------------
# FUNÇÕES DE PROCESSAMENTO
# --------------------------

def preprocess_image(img_np):
    """Aplica o pré-processamento à imagem capturada."""
    
    # 1. Converte para tons de cinza
    gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

    # 2. Binarização Adaptativa (melhor para texto claro em fundo escuro com iluminação variável)
    # cv2.ADAPTIVE_THRESH_GAUSSIAN_C: o valor do limiar é uma soma ponderada dos valores da vizinhança.
    # cv2.THRESH_BINARY_INV: Inverte o limiar para tornar o texto preto no branco (preferido pelo Tesseract).
    processed_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    # Tamanho do bloco 11: tamanho da vizinhança de pixels usada para calcular o valor do limiar.
    # C = 2: constante subtraída da média ou média ponderada.

    # 3. Dilatação para engrossar o texto (pode ajudar com fontes finas)
    kernel = np.ones((2,2), np.uint8) # Kernel ligeiramente maior
    processed_img = cv2.dilate(processed_img, kernel, iterations=1)
    
    return processed_img

def run_ocr(image):
    """Executa o Tesseract OCR e retorna o texto detectado."""
    try:
        # A imagem já está pré-processada em formato OpenCV/NumPy
        text = pytesseract.image_to_string(image, config=TESSERACT_CONFIG)
        return text
    except pytesseract.TesseractNotFoundError:
        print("\n[ERRO FATAL] Tesseract não encontrado. Verifique se o caminho no código está correto.")
        exit()
    except Exception as e:
        # Erro de OCR ocasional, pode ser ignorado na maioria das vezes.
        # print(f"Erro de OCR: {e}")
        return ""

def parse_drops(raw_text):
    """Limpa e formata a saída do OCR."""
    
    # Remove espaços extras e linhas vazias
    items = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    # Lista para armazenar os drops identificados
    parsed_drops = []

    for item in items:
        # Regex para identificar "Gold" (opcional, mas útil para limpar)
        if re.search(r'\bGold\b', item, re.IGNORECASE):
            # Limpa o texto de Gold, mantendo apenas a quantidade e o nome
            match = re.search(r'(\d+)\s*Gold', item, re.IGNORECASE)
            if match:
                parsed_drops.append(f"{match.group(1)} Gold")
        
        # Regex para identificar itens com Potion/Stamina
        elif re.search(r'\bPotion\b|\bStamina\b|\bLife\b', item, re.IGNORECASE):
            # Tenta pegar o nome completo e a quantidade (se houver xN)
            # Remove caracteres que o OCR pode confundir (ex: | ou !)
            clean_item = re.sub(r'[|!]', '', item)
            parsed_drops.append(clean_item)
            
        else:
            # Se for outro tipo de texto que passou pelo whitelist, mas não é um item conhecido.
            # Opcional: você pode adicionar mais regras de filtragem aqui.
            pass

    return parsed_drops

def find_white_bars(processed_img, min_area=50, max_area=5000, aspect_ratio_min=0.1, aspect_ratio_max=10.0):
    """
    Identifica as "barras brancas" no chão da imagem processada.
    Retorna uma lista de tuplas (center_x, center_y) das barras detectadas.
    """
    detected_bars_coords = []

    contours, _ = cv2.findContours(processed_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(contour)
            
            if h > 0:
                aspect_ratio = float(w) / h
            else:
                aspect_ratio = 0

            if aspect_ratio_min < aspect_ratio < aspect_ratio_max:
                center_x = x + w // 2
                center_y = y + h // 2
                detected_bars_coords.append((center_x, center_y))

    return detected_bars_coords

# --------------------------
# LOOP PRINCIPAL
# --------------------------

def main():
    logging.info("--- Sistema de Reconhecimento de Drops Ativo ---")
    
    # Load calibration from backup or use default
    loaded_region = load_calibration_backup()
    if loaded_region:
        current_monitor_region = loaded_region
    else:
        # Default MONITOR_REGION (from original file)
        current_monitor_region = {
            "top": 350,      # Coordenada Y (vertical) do topo
            "left": 550,     # Coordenada X (horizontal) da esquerda
            "width": 300,    # Largura da área a ser capturada
            "height": 250    # Altura da área a ser capturada
        }

    while True:
        logging.info("\nOpções:")
        logging.info("1. Iniciar Reconhecimento de Drops")
        logging.info("2. Calibrar Região do Monitor")
        logging.info("3. Sair")

        choice = input("\nEscolha uma opção (1-3): ").strip()

        if choice == '1':
            # Debug folder setup
            DEBUG_FOLDER = "rec_debug"
            DEBUG_SAVE_INTERVAL = 20 # seconds
            last_debug_save_time = time.time()
            debug_image_count = 0

            if not os.path.exists(DEBUG_FOLDER):
                os.makedirs(DEBUG_FOLDER)
                logging.info(f"Pasta de debug '{DEBUG_FOLDER}' criada.")

            logging.info("\nIniciando Reconhecimento de Drops...")
            logging.info(f"Intervalo de Scan: {SCAN_INTERVAL} segundos")
            logging.info(f"Região de Captura: {current_monitor_region}")
            logging.info("Pressione CTRL+C para sair.")

            last_drops = set()

            with mss.mss() as sct:
                try:
                    while True:
                        start_time = time.time()
                        # 1. Captura de Tela
                        sct_img = sct.grab(current_monitor_region) # Use current_monitor_region
                        img_np = np.array(sct_img)
                        # 2. Pré-processamento
                        processed_img = preprocess_image(img_np)
                        # Save processed image for debug
                        current_time_debug = time.time()
                        if current_time_debug - last_debug_save_time >= DEBUG_SAVE_INTERVAL:
                            debug_image_filename = os.path.join(DEBUG_FOLDER, f"processed_img_{debug_image_count}.png")
                            cv2.imwrite(debug_image_filename, processed_img)
                            logging.info(f"Imagem de debug salva: {debug_image_filename}")
                            last_debug_save_time = current_time_debug
                            debug_image_count += 1
                        # 3. Execução do OCR
                        raw_text = run_ocr(processed_img)
                        # 4. Processamento dos Drops (OCR-based)
                        ocr_drops = set(parse_drops(raw_text))
                        # 5. Detecção de Barras Brancas (Shape-based)
                        white_bar_drops_coords = find_white_bars(processed_img) # Call the new function
                        # Combine all detected drops
                        # all_detected_drops will now contain a mix of OCR text strings and (x, y) tuples
                        all_detected_drops = ocr_drops.union(set(white_bar_drops_coords)) # white_bar_drops_coords are now tuples
                        # 6. Lógica de Identificação de Novos Drops
                        # Drops que estão na tela agora, mas não estavam na última leitura.
                        new_drops = all_detected_drops - last_drops
                        if new_drops:
                            for drop_item in sorted(list(new_drops), key=str): # Sort by string representation for consistency
                                if isinstance(drop_item, tuple) and len(drop_item) == 2: # It's a white bar coordinate
                                    # Convert relative coordinates to absolute screen coordinates
                                    abs_x = current_monitor_region["left"] + drop_item[0]
                                    abs_y = current_monitor_region["top"] + drop_item[1]
                                    logging.info(f"[NOVA BARRA BRANCA] -> Clicando em ({abs_x}, {abs_y})")
                                    pyautogui.keyDown('a') # Press 'a' down
                                    pyautogui.moveTo(abs_x, abs_y, duration=random.uniform(0.1, 0.3)) # Human-like move
                                    time.sleep(random.uniform(0.05, 0.15)) # Small pause before click
                                    pyautogui.click(abs_x, abs_y)
                                    time.sleep(random.uniform(0.1, 0.3)) # Small pause after click
                                    pyautogui.keyUp('a') # Release 'a'
                                else: # It's an OCR text drop
                                    logging.info(f"[NOVO DROP] -> {drop_item}")
                        last_drops = all_detected_drops # Update last_drops with all detected items
                        # Cálculo do tempo de execução para manter o intervalo
                        elapsed_time = time.time() - start_time
                        sleep_time = max(0, SCAN_INTERVAL - elapsed_time)
                        time.sleep(sleep_time)
                except KeyboardInterrupt:
                    logging.info("\n\nSistema de Reconhecimento de Drops Encerrado.")
                except Exception as e:
                    logging.error(f"Erro no loop principal de reconhecimento: {e}")
        elif choice == '2':
            logging.info("\nIniciando calibração da região do monitor...")
            calibrated_region = calibrate_monitor_region(current_monitor_region)
            if calibrated_region:
                current_monitor_region = calibrated_region # Update the region
                logging.info(f"Região do monitor atualizada para: {current_monitor_region}")
        elif choice == '3':
            logging.info("\nFinalizando aplicação...")
            break
        else:
            logging.warning("\nOpção inválida! Tente novamente.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("\n\nSistema de Reconhecimento de Drops Encerrado.")