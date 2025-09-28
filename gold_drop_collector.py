import cv2
import numpy as np
import pyautogui
import time
import random
import os
import keyboard
import global_vars

cancel_scan_flag = False

def on_f12_press():
    global cancel_scan_flag
    cancel_scan_flag = True
    global_vars.stop_all_services = True # Signal to stop all services
    print("F12 pressionado. Cancelando varredura...")

keyboard.add_hotkey('f12', on_f12_press)

def load_template(path):
    """Carrega uma imagem de template do caminho especificado."""
    template = cv2.imread(path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template não encontrado: {path}")
    return template

def find_template(frame, template, threshold=0.75):
    """Encontra ocorrências de um único template em um quadro de imagem."""
    h, w = template.shape[:2]
    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)
    points = []
    for pt in zip(*loc[::-1]):
        center = (pt[0] + w // 2, pt[1] + h // 2)
        points.append(center)
    
    # Supressão de não-máximos simplificada para evitar detecções sobrepostas do mesmo template
    filtered = []
    for c in points:
        if all(np.linalg.norm(np.array(c) - np.array(f)) > min(w, h)//2 for f in filtered):
            filtered.append(c)
    return filtered

def find_templates(frame, templates, threshold=0.7):
    """Encontra múltiplos templates em um quadro e filtra resultados sobrepostos."""
    all_points = []
    for template in templates:
        # find_template já realiza supressão para um único template
        points = find_template(frame, template, threshold)
        all_points.extend(points)
    
    # Passagem final de supressão de não-máximos nos pontos combinados de todos os templates
    final_filtered = []
    if not all_points:
        return []

    all_points.sort(key=lambda p: (p[0], p[1]))

    for p in all_points:
        # Usa uma distância fixa (20px) para filtrar entre diferentes templates
        if all(np.linalg.norm(np.array(p) - np.array(f)) > 20 for f in final_filtered):
            final_filtered.append(p)
            
    return final_filtered

# Define o nome do arquivo de backup
CALIBRATION_BACKUP_FILE = 'gold_drop_calibration_backup.txt'

def save_calibration_backup(search_region):
    """Salva as coordenadas da zona de busca em um arquivo de backup."""
    try:
        with open(CALIBRATION_BACKUP_FILE, 'w') as f:
            f.write(f"search_region = {search_region}\n")
        print(f"Backup da calibração salvo em '{CALIBRATION_BACKUP_FILE}'")
    except Exception as e:
        print(f"Erro ao salvar backup da calibração: {e}")

def load_calibration_backup():
    """Carrega as coordenadas da zona de busca de um arquivo de backup."""
    if os.path.exists(CALIBRATION_BACKUP_FILE):
        try:
            with open(CALIBRATION_BACKUP_FILE, 'r') as f:
                content = f.read()
            
            # Extrai a região usando parsing de string simples
            region_str = content.split("search_region = ")[1].strip()
            
            # Usa eval para converter a representação de string da tupla de volta para o objeto real
            # AVISO: eval pode ser perigoso se o conteúdo não for confiável.
            # No entanto, este arquivo é gerado pelo próprio bot, então deve ser seguro.
            loaded_region = eval(region_str)
            print(f"Calibração carregada de '{CALIBRATION_BACKUP_FILE}' com sucesso.")
            return loaded_region
        except Exception as e:
            print(f"Erro ao carregar calibração de '{CALIBRATION_BACKUP_FILE}': {e}")
            return None
    else:
        print(f"Arquivo de backup de calibração '{CALIBRATION_BACKUP_FILE}' não encontrado. Usando configurações padrão.")
        return None

def calibrate_search_region(initial_region):
    """Sistema interativo de calibração da zona de busca, baseado no GameBot."""
    print("🎯 SISTEMA DE CALIBRAÇÃO DA ZONA DE BUSCA")
    print("=" * 50)
    print("INSTRUÇÕES:")
    print("- 🖱️  CLIQUE E ARRASTE para mover ou desenhar a região de busca.")
    print("- [WASD] - Mover a região selecionada (5 pixels)")
    print("- [+/-] - Aumentar/diminuir largura (5 pixels)")
    print("- [[]/] - Aumentar/diminuir altura (5 pixels)")
    print("- [R] - Resetar a região para o padrão (tela cheia)")
    print("- [SPACE] - Salvar as coordenadas e sair")
    print("- [Q/ESC] - Sair sem salvar")
    print()

    screen_width, screen_height = pyautogui.size()
    search_region = list(initial_region) # Use a list for mutability

    drawing = False
    drag_start = None
    drag_offset = None
    scale = 0.7 # Scale for display, actual coordinates are full size

    # Default for reset
    default_full_screen_region = [0, 0, screen_width, screen_height]

    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, drag_start, drag_offset, search_region

        # Convert scaled display coordinates to real screen coordinates
        real_x = int(x / scale)
        real_y = int(y / scale)

        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if clicking inside the search_region
            rx, ry, rw, rh = search_region
            if rx <= real_x <= rx + rw and ry <= real_y <= ry + rh:
                drawing = True
                drag_start = (real_x, real_y)
                drag_offset = (real_x - rx, real_y - ry)
            else: # If clicking outside, start a new drag to define a new region
                drawing = True
                drag_start = (real_x, real_y)
                search_region[0] = real_x
                search_region[1] = real_y
                search_region[2] = 1 # Minimum width
                search_region[3] = 1 # Minimum height


        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            if drag_offset: # Moving an existing region
                new_x = real_x - drag_offset[0]
                new_y = real_y - drag_offset[1]
                search_region[0] = new_x
                search_region[1] = new_y
            else: # Drawing a new region
                x1, y1 = drag_start
                x2, y2 = real_x, real_y
                search_region[0] = min(x1, x2)
                search_region[1] = min(y1, y2)
                search_region[2] = abs(x1 - x2)
                search_region[3] = abs(y1 - y2)
                # Ensure minimum size
                if search_region[2] < 10: search_region[2] = 10
                if search_region[3] < 10: search_region[3] = 10


        elif event == cv2.EVENT_LBUTTONUP:
            if drawing:
                drawing = False
                drag_start = None
                drag_offset = None
                print(f"Região definida: x={search_region[0]}, y={search_region[1]}, w={search_region[2]}, h={search_region[3]}")

    window_name = 'Calibracao da Zona de Busca - Clique e Arraste'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)

    while True:
        frame = pyautogui.screenshot()
        frame_np = np.array(frame)
        display_frame = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)

        # Draw the current search_region
        x, y, w, h = search_region
        color = (0, 255, 0) # Green
        thickness = 2
        cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, thickness)
        cv2.putText(display_frame, f"Regiao de Busca: x={x}, y={y}, w={w}, h={h}", (x, y - 10),
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
            save_calibration_backup(tuple(search_region)) # Call save function
            break
        elif key == ord('r'): # Reset to full screen
            search_region = list(default_full_screen_region)
            print("Região resetada para tela cheia.")

        # Movement (WASD) and Resize
        if key == ord('w'): # Up
            search_region[1] -= 5
        elif key == ord('s'): # Down
            search_region[1] += 5
        elif key == ord('a'): # Left
            search_region[0] -= 5
        elif key == ord('d'): # Right
            search_region[0] += 5
        elif key == ord('+') or key == ord('='):  # Aumentar largura
            search_region[2] += 5
        elif key == ord('-'):  # Diminuir largura
            search_region[2] = max(10, search_region[2] - 5)
        elif key == ord('['): # Aumentar altura
            search_region[3] += 5
        elif key == ord(']'): # Diminuir altura
            search_region[3] = max(10, search_region[3] - 5)

        time.sleep(0.01) # Small delay for smoother display

    cv2.destroyAllWindows()
    return tuple(search_region) # Return the final region as a tuple

import subprocess

def is_game_running(process_name="Game.exe"):
    """
    Verifica se um processo específico está em execução no Windows.
    Retorna True se o processo for encontrado, False caso contrário.
    """
    try:
        # Executa o comando tasklist para listar os processos
        # /FI "IMAGENAME eq Game.exe" filtra pelo nome da imagem
        result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], 
                                capture_output=True, text=True, check=False)
        
        # tasklist retorna "INFO: No tasks are running which match the specified criteria."
        # se o processo não for encontrado. Caso contrário, retorna uma tabela.
        return process_name.lower() in result.stdout.lower()
    except Exception as e:
        print(f"Erro ao verificar processo {process_name}: {e}") # Using print as logging is not configured here
        return False

def main():
    global cancel_scan_flag
    global_vars.is_scan_active = True # Set scan active when main starts
    print("=== Coleta Automática de Gold Drop ===")
    print("Desenvolvido por: Fabricio Costa\n")

    last_game_check_time = time.time() # Initialize for periodic check
    GAME_CHECK_INTERVAL = 5 # Check every 5 seconds
    
    # Load calibration from backup
    loaded_region = load_calibration_backup()
    if loaded_region:
        search_region = loaded_region
        search_region_x, search_region_y, search_region_width, search_region_height = search_region
    else:
        # Default search region (full screen)
        screen_width, screen_height = pyautogui.size()
        search_region_x = 0
        search_region_y = 0
        search_region_width = screen_width
        search_region_height = screen_height
        search_region = (search_region_x, search_region_y, search_region_width, search_region_height)

    drops_path = os.path.join('images', 'drops')
    
    gold_template_paths = [
        os.path.join(drops_path, 'GOLD_drop.bmp'),
        os.path.join(drops_path, 'GOLD_drop1.png'),
        os.path.join(drops_path, 'GOLD_drop2.png'),
        os.path.join(drops_path, 'GOLD_drop3.png'),
    ]
    barra_template_paths = [
        os.path.join(drops_path, 'caixa_texto_info_drop.png'),
        os.path.join(drops_path, 'barra_texto.png'),
        os.path.join(drops_path, 'barra_texto1.png'),
    ]

    # --- Novo: Template para ignorar barras verdes ---
    green_bar_template_path = os.path.join('images', 'ignore', 'green_bar.png')
    green_bar_templates = []
    try:
        green_bar_templates.append(load_template(green_bar_template_path))
    except FileNotFoundError as e:
        print(e)
    # -------------------------------------------------

    gold_templates = []
    for path in gold_template_paths:
        try:
            gold_templates.append(load_template(path))
        except FileNotFoundError as e:
            print(e)

    barra_templates = []
    for path in barra_template_paths:
        try:
            barra_templates.append(load_template(path))
        except FileNotFoundError as e:
            print(e)

    if not gold_templates and not barra_templates:
        print("Nenhum template de drop foi carregado. Verifique os caminhos e os arquivos.")
        return

    cooldown = 1.0  # segundos
    last_collect = 0
    debug = True

    while True:
        if global_vars.stop_all_services: # Check if a global stop is requested
            print("\nSinal de parada global recebido. Finalizando aplicação.")
            break
        
        current_time = time.time() # Get current time for periodic checks
        if current_time - last_game_check_time >= GAME_CHECK_INTERVAL:
            if not is_game_running():
                print("Game.exe não encontrado. Enviando sinal de parada global.")
                global_vars.stop_all_services = True # Signal to stop all services
                break # Exit the main loop
            last_game_check_time = current_time # Reset check time

        print("\nOpções:")
        print("1. Iniciar coleta de drops (detecção visual)")
        print("2. Calibrar zona de busca")
        print("3. Iniciar coleta por varredura cega")
        print("4. Sair")

        choice = input("\nEscolha uma opção (1-4): ").strip()

        if choice == '1':
            print("\nIniciando coleta de drops (detecção visual)...")
            print("Pressione Ctrl+C para parar\n")
            pyautogui.keyDown('a') # Press 'a' down once when scan starts
            try:
                while True:
                    if cancel_scan_flag or global_vars.stop_all_services: # Added global_vars.stop_all_services check
                        break
                    # Pause scan if potion replenishment is active
                    while global_vars.pause_scan_for_potion:
                        time.sleep(0.1) # Wait for potion replenishment to finish
                    
                    start_search_time = time.time()
                    pyautogui.keyDown('a')
                    
                    while (time.time() - start_search_time) < 30:
                        if cancel_scan_flag:
                            break # Search for 30 seconds
                        screenshot = pyautogui.screenshot(region=search_region)
                        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                        
                        gold_points = find_templates(frame, gold_templates, threshold=0.7)
                        barra_points = find_templates(frame, barra_templates, threshold=0.7)
                        
                        # --- Novo: Filtrar barras de texto com barra verde abaixo ---
                        filtered_barra_points = []
                        if green_bar_templates: # Only filter if green bar template is loaded
                            for (bx, by) in barra_points:
                                # Define a region below the text bar to search for the green bar
                                # Assuming text bar height is around 20-30px, and green bar is below it.
                                # Search area for green bar:
                                # x: bx - 50 (to cover width)
                                # y: by + 10 (just below the text bar center)
                                # width: 100
                                # height: 40 (for the green bar itself)
                                
                                green_bar_roi_x = bx - 50
                                green_bar_roi_y = by + 10
                                green_bar_roi_width = 100
                                green_bar_roi_height = 40

                                # Clamp ROI to frame boundaries (frame is the screenshot of search_region)
                                frame_h, frame_w = frame.shape[:2]
                                
                                roi_x1 = max(0, green_bar_roi_x)
                                roi_y1 = max(0, green_bar_roi_y)
                                roi_x2 = min(frame_w, green_bar_roi_x + green_bar_roi_width)
                                roi_y2 = min(frame_h, green_bar_roi_y + green_bar_roi_height)
                                
                                # If the ROI is valid (has positive width and height)
                                if roi_x2 > roi_x1 and roi_y2 > roi_y1:
                                    green_bar_search_area = frame[roi_y1:roi_y2, roi_x1:roi_x2]
                                    
                                    # Search for the green bar template in this area
                                    green_bar_found = find_templates(green_bar_search_area, green_bar_templates, threshold=0.8) # Higher threshold for specific match
                                    
                                    if not green_bar_found: # If green bar is NOT found, keep the text bar
                                        filtered_barra_points.append((bx, by))
                                else:
                                    # If ROI is invalid, assume no green bar found and keep the text bar
                                    filtered_barra_points.append((bx, by))
                            barra_points = filtered_barra_points
                        # -----------------------------------------------------------\n                        
                        # Combine all detected points
                        all_detected_points = []
                        for (x, y) in gold_points:
                            all_detected_points.append((x + search_region_x, y + search_region_y))
                        for (x, y) in barra_points:
                            all_detected_points.append((x + search_region_x, y + search_region_y))

                        if all_detected_points:
                            print(f"Drops detectados: {len(all_detected_points)}")
                            for (x, y) in all_detected_points:
                                # Click on the detected drop
                                pyautogui.click(x, y)
                                time.sleep(random.uniform(0.3, 0.7)) # Increased random delay to prevent double clicks
                            last_collect = time.time()
                        else:
                            print("Nenhum drop detectado.")
                        
                        time.sleep(random.uniform(0.5, 1.5)) # Small delay between detection cycles within the 30s window

                    if cancel_scan_flag:
                        cancel_scan_flag = False
                        break
            except KeyboardInterrupt:
                print("\nColeta de drops interrompida pelo usuário.")
            finally:
                pyautogui.keyUp('a') # Release 'a' when scan stops 
        elif choice == '2':
            print("\nIniciando calibração da zona de busca...")
            calibrated_region = calibrate_search_region(search_region)
            if calibrated_region:
                search_region = calibrated_region # Update the search_region
                print(f"Zona de busca atualizada para: {search_region}")

        elif choice == '3': # New option for blind scan
            print("\nIniciando coleta por varredura cega (pixel a pixel)...")
            print("Pressione Ctrl+C para parar\n")
            time.sleep(30) # Delay before starting the 30s routine
            pyautogui.keyDown('a') # Press 'a' down once when scan starts
            try:
                while True:
                    if cancel_scan_flag or global_vars.stop_all_services: # Added global_vars.stop_all_services check
                        break
                    # Pause scan if potion replenishment is active
                    while global_vars.pause_scan_for_potion:
                        time.sleep(0.1) # Wait for potion replenishment to finish
                    
                    pyautogui.keyDown('a')
                    
                    # Iterate pixel by pixel within the search_region
                    for y_coord in range(search_region_y, search_region_y + search_region_height, 20): # Step by 20 pixels for less humanized, straight line scan
                        if cancel_scan_flag:
                            break
                        for x_coord in range(search_region_x, search_region_x + search_region_width, 20): # Step by 20 pixels for less humanized, straight line scan
                            if cancel_scan_flag:
                                break
                            # Click exactly on the calculated coordinate (less humanized)
                            click_x = x_coord
                            click_y = y_coord

                            # Ensure click is within the search region boundaries
                            click_x = max(search_region_x, min(click_x, search_region_x + search_region_width - 1))
                            click_y = max(search_region_y, min(click_y, search_region_y + search_region_height - 1))
                            
                            pyautogui.click(click_x, click_y)
                            time.sleep(random.uniform(0.5, 1)) # Faster, less varied click delay
                    
                    if cancel_scan_flag:
                        cancel_scan_flag = False
                        break
                    time.sleep(random.uniform(90, 180)) # Very long pause after one full scan of the region
            except KeyboardInterrupt:
                print("\nColeta por varredura cega (pixel a pixel) interrompida pelo usuário.")
            finally:
                pyautogui.keyUp('a') # Release 'a' when scan stops
        elif choice == '4': # Original choice '3' is now '4'
            print("\nFinalizando aplicação...")
            global_vars.is_scan_active = False # Set scan inactive when exiting
            break

        else:
            print("\nOpção inválida! Tente novamente.")

if __name__ == "__main__":
    main()