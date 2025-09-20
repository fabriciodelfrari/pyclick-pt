#!/usr/bin/env python3
"""
Automação de Jogo - Monitor de Barras e Poções
Desenvolvido por: Fabricio Costa
Data: 18/09/2025

Sistema completo de automação para jogos online que monitora:
- Barras de status (HP, Mana, Energy)
- Slots de poções automáticas
- Serviços em background
"""

import cv2
import numpy as np
import pyautogui
import time
import threading
import logging
import random
import os
from PIL import Image

# Configurar PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class GameBot:
    def __init__(self):
        """Inicializa o bot de automação do jogo"""
        
        # Coordenadas das barras VERTICAIS (ajustar conforme necessário)
        self.bar_regions = {
            'hp': (600, 920, 25, 120),      # x, y, width, height
            'mana': (870, 990, 25, 50),     # x, y, width, height  
            'energy': (570, 997, 15, 45),   # x, y, width, height
        }
        
        # Coordenadas das poções (ajustar conforme necessário)
        self.potion_regions = {
            'red_potion': (650, 1000, 30, 30),    # HP potion
            'green_potion': (690, 1000, 30, 30),  # Energy potion
            'blue_potion': (730, 1000, 30, 30),   # Mana potion
        }
        
        # Região do inventário (para reposição automática)
        self.inventory_region = (768, 324, 672, 432)
        
        # Estados das barras e poções
        self.bar_states = {
            'hp': False,
            'mana': False, 
            'energy': False
        }
        
        self.potion_states = {
            'red_potion': False,
            'green_potion': False,
            'blue_potion': False
        }
        
        # Prioridades e controle avançado das barras
        self.bar_priorities = {'hp': 1, 'mana': 2, 'energy': 3}
        self.last_action_time = {'hp': 0, 'mana': 0, 'energy': 0}
        self.action_cooldowns = {'hp': 1.0, 'mana': 0.5, 'energy': 0.5}
        self.consecutive_low_count = {'hp': 0, 'mana': 0, 'energy': 0}
        self.urgent_threshold = {'hp': 20, 'mana': 15, 'energy': 15}
        
        # Controle do serviço em background
        self.running = False
        self.last_background_click = 0
        self.background_interval = random.randint(30, 45)
        self.last_periodic_flow = 0
        self.periodic_flow_interval = 300  # 5 minutos
        
        # Configurações de logging opcionais
        self.debug_mode = False
        self.verbose_logs = True
        self.show_bar_logs = True
        self.show_potion_logs = True
        self.show_action_logs = True

        self.potion_templates = {} # Initialize potion templates dictionary
        self._load_potion_templates() # Load potion templates
        self._load_calibration_from_backup() # Load calibration from backup if available

        logging.info("GameBot inicializado com sucesso")
    
    def _load_potion_templates(self):
        """Loads potion template images for inventory matching."""
        # Use os.path.join to create a platform-independent path
        base_path = os.path.join(os.path.dirname(__file__), 'images', 'potions_inventario')
        potion_types = {'hp': 'hp', 'mana': 'mana', 'stamina': 'stamina'} # Map internal names to folder names

        for internal_type, folder_name in potion_types.items():
            self.potion_templates[internal_type] = []
            folder_path = os.path.join(base_path, folder_name)
            try:
                # Use glob to find all .bmp files in the specific folder
                # This is a more robust way to get the files
                # I will use the glob tool to get the list of files dynamically.
                # For now, I'll keep the hardcoded list, but construct the paths dynamically.

                files = []
                if internal_type == 'hp':
                    files = [
                        "itPL101.bmp", "itPL102.bmp", "itPL103.bmp", "itPL104.bmp", "itPL105.bmp",
                    ]
                elif internal_type == 'mana':
                    files = [
                        "itPM101.bmp", "itPM102.bmp", "itPM103.bmp", "itPM104.bmp", "itPM105.bmp",
                    ]
                elif internal_type == 'stamina':
                    files = [
                        "itPS101.bmp", "itPS102.bmp", "itPS103.bmp", "itPS104.bmp",
                    ]

                for file_name in files:
                    file_path = os.path.join(folder_path, file_name)
                    template = cv2.imread(file_path, cv2.IMREAD_COLOR)
                    if template is not None:
                        self.potion_templates[internal_type].append(template)
                        logging.info(f"Template carregado: {file_path}")
                    else:
                        logging.warning(f"Falha ao carregar template: {file_path}")
            except Exception as e:
                logging.error(f"Erro ao carregar templates de poção para {folder_name}: {e}")

        if not self.potion_templates['hp'] and not self.potion_templates['mana'] and not self.potion_templates['stamina']:
            logging.warning("Nenhum template de poção carregado. A detecção de poções no inventário pode falhar.")

    def _load_calibration_from_backup(self):
        """Loads calibration data from 'calibration_backup.txt' if available."""
        backup_file = 'calibration_backup.txt'
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r') as f:
                    content = f.read()

                # Extract regions using simple string parsing (assuming format from save_calibration)
                # This is a bit fragile, but matches the output format of save_calibration
                bar_regions_str = content.split("bar_regions = ")[1].split("\npotion_regions = ")[0].strip()
                potion_regions_str = content.split("potion_regions = ")[1].split("\ninventory_region = ")[0].strip()
                inventory_region_str = content.split("inventory_region = ")[1].split("\n")[0].strip()

                # Use eval to convert string representation of dict/tuple back to actual objects
                # WARNING: eval can be dangerous if content is not trusted.
                # However, this file is generated by the bot itself, so it should be safe.
                loaded_bar_regions = eval(bar_regions_str)
                loaded_potion_regions = eval(potion_regions_str)
                loaded_inventory_region = eval(inventory_region_str)

                # Update current regions
                self.bar_regions.update(loaded_bar_regions)
                self.potion_regions.update(loaded_potion_regions)
                self.inventory_region = loaded_inventory_region

                logging.info(f"Calibração carregada de '{backup_file}' com sucesso.")
            except Exception as e:
                logging.error(f"Erro ao carregar calibração de '{backup_file}': {e}")
        else:
            logging.info(f"Arquivo de backup de calibração '{backup_file}' não encontrado. Usando configurações padrão.")

    def capture_screen(self):
        try:
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            logging.error(f"Erro ao capturar tela: {e}")
            return None
    
    def extract_region(self, frame, region):
        """Extrai uma região específica da imagem"""
        try:
            x, y, w, h = region
            height, width = frame.shape[:2]
            
            # Verificar limites
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = max(1, min(w, width - x))
            h = max(1, min(h, height - y))
            
            return frame[y:y+h, x:x+w]
        except Exception as e:
            logging.error(f"Erro ao extrair região {region}: {e}")
            return None
    
    def analyze_bar_level_advanced(self, bar_image, bar_type):
        """
        Análise avançada do nível da barra vertical combinando múltiplos métodos
        """
        if bar_image is None or bar_image.size == 0:
            return 100, {}
        
        try:
            # Análise combinada usando 4 métodos diferentes
            bgr_score = self._analyze_bgr_intensity(bar_image, bar_type)
            hsv_score = self._analyze_hsv_color(bar_image, bar_type)
            gradient_score = self._analyze_color_gradient(bar_image, bar_type)
            fill_score = self._analyze_vertical_fill(bar_image, bar_type)
            
            # Pesos para cada método
            weights = {'bgr': 0.3, 'hsv': 0.3, 'gradient': 0.2, 'fill': 0.2}
            
            # Calcular score final ponderado
            final_score = (
                bgr_score * weights['bgr'] +
                hsv_score * weights['hsv'] +
                gradient_score * weights['gradient'] +
                fill_score * weights['fill']
            )
            
            # Informações detalhadas
            analysis_details = {
                'bgr_score': bgr_score,
                'hsv_score': hsv_score,
                'gradient_score': gradient_score,
                'fill_score': fill_score,
                'final_score': final_score,
                'bar_type': bar_type
            }
            
            # Determinar se ação deve ser tomada baseado no tipo de barra
            threshold = 40 if bar_type == 'hp' else 30  # HP = 40%, outros = 30%
            action_needed = final_score < threshold
            
            if self.debug_mode and self.show_bar_logs:
                logging.info(f"Análise {bar_type.upper()}: BGR={bgr_score:.1f}, HSV={hsv_score:.1f}, "
                           f"Gradient={gradient_score:.1f}, Fill={fill_score:.1f} -> Final={final_score:.1f}% "
                           f"(Limite: {threshold}%) {'AÇÃO!' if action_needed else 'OK'}")
            
            return final_score, analysis_details
            
        except Exception as e:
            logging.error(f"Erro na análise da barra {bar_type}: {e}")
            return 100, {}
    
    def _analyze_bgr_intensity(self, bar_image, bar_type):
        """Analisa intensidade BGR"""
        try:
            mean_bgr = np.mean(bar_image, axis=(0, 1))
            b, g, r = mean_bgr
            
            if bar_type == 'hp':
                return min(100, (r / max(b + g, 1)) * 30)
            elif bar_type == 'mana':
                return min(100, (b / max(r + g, 1)) * 30)
            elif bar_type == 'energy':
                return min(100, (g / max(r + b, 1)) * 30)
            
            return 50
        except:
            return 50
    
    def _analyze_hsv_color(self, bar_image, bar_type):
        """Analisa cor HSV"""
        try:
            hsv = cv2.cvtColor(bar_image, cv2.COLOR_BGR2HSV)
            
            # Faixas de cor para cada tipo de barra
            if bar_type == 'hp':
                mask = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([20, 255, 255]))
            elif bar_type == 'mana':
                mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([140, 255, 255]))
            elif bar_type == 'energy':
                mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
            else:
                return 50
            
            color_percentage = (np.sum(mask > 0) / mask.size) * 100
            return min(100, color_percentage * 2)
            
        except:
            return 50
    
    def _analyze_color_gradient(self, bar_image, bar_type):
        """Analisa gradiente de cor"""
        try:
            gray = cv2.cvtColor(bar_image, cv2.COLOR_BGR2GRAY)
            gradient = np.gradient(gray.astype(float), axis=0)
            gradient_intensity = np.mean(np.abs(gradient))
            return min(100, gradient_intensity * 3)
        except:
            return 50
    
    def _analyze_vertical_fill(self, bar_image, bar_type):
        """Analisa preenchimento vertical"""
        try:
            height, width = bar_image.shape[:2]
            gray = cv2.cvtColor(bar_image, cv2.COLOR_BGR2GRAY)
            
            # Analisar de baixo para cima
            filled_rows = 0
            for row in range(height - 1, -1, -1):
                row_mean = np.mean(gray[row, :])
                if row_mean > 80:  # Threshold para pixel "cheio"
                    filled_rows += 1
                else:
                    break
            
            fill_percentage = (filled_rows / height) * 100
            return fill_percentage
            
        except:
            return 50
    
    def monitor_bars(self, frame):
        """
        Monitora as barras com sistema de prioridade e agilidade
        """
        current_time = time.time()
        bar_analysis = {}
        
        # Analisar todas as barras primeiro
        for bar_type, region in self.bar_regions.items():
            try:
                bar_image = self.extract_region(frame, region)
                level, details = self.analyze_bar_level_advanced(bar_image, bar_type)
                
                # Salvar imagem de debug se necessário
                if self.debug_mode:
                    cv2.imwrite(f'debug_bar_{bar_type}.png', bar_image)
                
                # Determinar estado crítico
                threshold = 40 if bar_type == 'hp' else 30
                is_critical = level < threshold
                is_urgent = level < self.urgent_threshold[bar_type]
                
                bar_analysis[bar_type] = {
                    'level': level,
                    'details': details,
                    'is_critical': is_critical,
                    'is_urgent': is_urgent,
                    'region': region
                }
                
                # Atualizar contador consecutivo
                if is_critical:
                    self.consecutive_low_count[bar_type] += 1
                else:
                    self.consecutive_low_count[bar_type] = 0
                    
            except Exception as e:
                logging.error(f"Erro ao monitorar barra {bar_type}: {e}")
        
        # Executar ações baseadas na prioridade
        self._execute_priority_actions(bar_analysis, current_time)
    
    def _execute_priority_actions(self, bar_analysis, current_time):
        """Executa ações baseadas na prioridade das barras"""
        
        # Ordenar barras por prioridade (HP primeiro)
        sorted_bars = sorted(bar_analysis.items(), 
                           key=lambda x: self.bar_priorities.get(x[0], 999))
        
        for bar_type, analysis in sorted_bars:
            if not analysis['is_critical']:
                continue
                
            # Verificar cooldown
            time_since_last = current_time - self.last_action_time[bar_type]
            if time_since_last < self.action_cooldowns[bar_type]:
                continue
            
            # HP urgente tem prioridade máxima
            if bar_type == 'hp' and analysis['is_urgent']:
                self._execute_urgent_hp_action(analysis, current_time)
                break  # Parar tudo para HP urgente
            
            # Barras persistentemente baixas
            elif self.consecutive_low_count[bar_type] >= 3:
                self._execute_repeated_action(bar_type, current_time)
                break
            
            # Primeira detecção de barra baixa
            else:
                self._execute_normal_action(bar_type, current_time)
                break
    
    def _execute_urgent_hp_action(self, analysis, current_time):
        """Ação urgente para HP crítico"""
        if self.show_bar_logs:
            logging.warning(f"HP CRITICO! Nivel: {analysis['level']:.1f}% - Acao urgente!")
        
        # Pressionar '1' duas vezes rapidamente
        self.simulate_key_press('1')
        time.sleep(0.1)
        self.simulate_key_press('1')
        
        self.last_action_time['hp'] = current_time
        self.action_cooldowns['hp'] = 0.5  # Cooldown reduzido para emergência
    
    def _execute_repeated_action(self, bar_type, current_time):
        """Ação para barras persistentemente baixas"""
        key_map = {'hp': '1', 'mana': '3', 'energy': '2'}
        key = key_map.get(bar_type, '1')
        
        if self.show_bar_logs:
            logging.warning(f"Barra {bar_type.upper()} persistentemente baixa - Repeticao de acao")
        
        # Pressionar duas vezes com pequeno delay
        self.simulate_key_press(key)
        time.sleep(0.2)
        self.simulate_key_press(key)
        
        self.last_action_time[bar_type] = current_time
        
        # Cooldown menor para HP
        if bar_type == 'hp':
            self.action_cooldowns[bar_type] = 0.3
        else:
            self.action_cooldowns[bar_type] = 0.5
    
    def _execute_normal_action(self, bar_type, current_time):
        """Ação normal para primeira detecção"""
        key_map = {'hp': '1', 'mana': '3', 'energy': '2'}
        key = key_map.get(bar_type, '1')
        
        if self.show_bar_logs:
            logging.warning(f"Barra {bar_type.upper()} baixa - Usando pocao")
        
        self.simulate_key_press(key)
        self.last_action_time[bar_type] = current_time
    
    def analyze_potion_status(self, potion_image, potion_type):
        """
        Analisa se um slot de poção está vazio usando múltiplos critérios
        """
        if potion_image is None or potion_image.size == 0:
            return False
        
        try:
            # Critério 1: Intensidade média
            mean_intensity = np.mean(potion_image)
            low_intensity = mean_intensity < 80
            
            # Critério 2: Densidade de bordas
            gray = cv2.cvtColor(potion_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            low_edges = edge_density < 0.15
            
            # Critério 3: Porcentagem de cor específica
            hsv = cv2.cvtColor(potion_image, cv2.COLOR_BGR2HSV)
            
            if potion_type == 'red_potion':
                mask = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([20, 255, 255]))
            elif potion_type == 'green_potion':
                mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
            elif potion_type == 'blue_potion':
                mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([140, 255, 255]))
            else:
                mask = np.zeros_like(gray)
            
            color_percentage = (np.sum(mask > 0) / mask.size) * 100
            low_color = color_percentage < 10
            
            # Considerar vazio se pelo menos 2 dos 3 critérios forem atendidos
            criteria_met = sum([low_intensity, low_edges, low_color])
            is_empty = criteria_met >= 2
            
            if self.debug_mode and self.show_potion_logs:
                logging.info(f"POCAO {potion_type.upper()}: intensidade={mean_intensity:.1f}, "
                           f"bordas={edge_density:.3f}, cor={color_percentage:.1f}% - "
                           f"{'VAZIA' if is_empty else 'OK'}")
            
            return is_empty
            
        except Exception as e:
            logging.error(f"Erro ao analisar poção {potion_type}: {e}")
            return False
    
    def monitor_potions(self, frame):
        """
        Monitora o status das poções e repõe automaticamente quando necessário
        """
        for potion_type, region in self.potion_regions.items():
            try:
                potion_image = self.extract_region(frame, region)
                
                # Verificar se a região é válida
                if potion_image is None or potion_image.size == 0:
                    logging.warning(f"Região da poção {potion_type} inválida: {region}")
                    continue
                
                is_empty = self.analyze_potion_status(potion_image, potion_type)
                
                # Verificar mudança de estado para evitar spam
                if is_empty and not self.potion_states[potion_type]:
                    self.potion_states[potion_type] = True
                    
                    if self.show_potion_logs:
                        logging.warning(f"POCAO {potion_type.upper()} ACABOU! Iniciando reposicao automatica...")
                    
                    # Tentar repor a poção automaticamente
                    if self.refill_potion(potion_type):
                        if self.show_potion_logs:
                            logging.warning(f"Pocao {potion_type.upper()} reposta com sucesso!")
                        # Aguardar um pouco antes de verificar novamente
                        time.sleep(2)
                    else:
                        if self.show_potion_logs:
                            logging.error(f"Falha ao repor pocao {potion_type.upper()}")
                        # Se falhar, tentar método antigo como fallback
                        if potion_type == 'red_potion':
                            self.simulate_key_combination(['shift', '1'])
                        elif potion_type == 'green_potion':
                            self.simulate_key_combination(['shift', '2'])
                        elif potion_type == 'blue_potion':
                            self.simulate_key_combination(['shift', '3'])
                    
                elif not is_empty and self.potion_states[potion_type]:
                    # Poção foi reposta
                    self.potion_states[potion_type] = False
                    if self.debug_mode and self.verbose_logs:
                        logging.info(f"Poção {potion_type} foi reposta")
                        
            except Exception as e:
                logging.error(f"Erro ao monitorar poção {potion_type}: {e}")
    
    def open_inventory(self):
        """Abre o inventário pressionando V"""
        try:
            logging.info("Abrindo inventário...")
            pyautogui.press('v')
            time.sleep(1.5)  # Aguardar inventário abrir
            return True
        except Exception as e:
            logging.error(f"Erro ao abrir inventário: {e}")
            return False
    
    def close_inventory(self):
        """Fecha o inventário pressionando V novamente"""
        try:
            logging.info("Fechando inventário...")
            pyautogui.press('v')
            time.sleep(0.3)  # Aguardar inventário fechar (otimizado)
            return True
        except Exception as e:
            logging.error(f"Erro ao fechar inventário: {e}")
            return False
    
    def find_potion_in_inventory(self, potion_type):
        """
        Encontra uma poção específica no inventário usando template matching.
        """
        try:
            # Mapear o tipo de poção para a categoria de template
            template_category_map = {
                'red_potion': 'hp',
                'green_potion': 'stamina', # Assuming green potion is for energy/stamina
                'blue_potion': 'mana',
            }
            category = template_category_map.get(potion_type)

            if not category or not self.potion_templates.get(category):
                logging.warning(f"Nenhum template carregado para a categoria de poção: {category} ({potion_type})")
                return None

            # Capturar região do inventário
            frame = self.capture_screen()
            if frame is None:
                return None

            inv_region = self.extract_region(frame, self.inventory_region)
            if inv_region is None:
                return None

            best_match_loc = None
            max_corr = -1

            # Iterar sobre todos os templates para o tipo de poção
            for template in self.potion_templates[category]:
                # Certificar-se de que o template não é maior que a região de busca
                if template.shape[0] > inv_region.shape[0] or template.shape[1] > inv_region.shape[1]:
                    logging.warning(f"Template {category} é maior que a região do inventário. Pulando.")
                    continue

                # Realizar template matching
                # Usamos cv2.TM_CCOEFF_NORMED para obter um valor de correlação normalizado
                result = cv2.matchTemplate(inv_region, template, cv2.TM_CCOEFF_NORMED)
                min_val, current_max_corr, min_loc, max_loc = cv2.minMaxLoc(result)

                if current_max_corr > max_corr:
                    max_corr = current_max_corr
                    best_match_loc = max_loc

            # Definir um threshold de correlação para considerar um match válido
            # Este valor pode precisar de ajuste
            match_threshold = 0.70 # 70% de correlação

            if max_corr >= match_threshold and best_match_loc:
                # Obter as dimensões do template para calcular o centro
                template_h, template_w = self.potion_templates[category][0].shape[:2] # Usar o primeiro template para dimensoes

                # Coordenadas do canto superior esquerdo do match
                top_left_x, top_left_y = best_match_loc

                # Calcular o centro do match na região do inventário
                center_x_in_inv = top_left_x + template_w // 2
                center_y_in_inv = top_left_y + template_h // 2

                # Converter coordenadas para posição absoluta na tela
                abs_x = self.inventory_region[0] + center_x_in_inv
                abs_y = self.inventory_region[1] + center_y_in_inv

                if self.debug_mode:
                    logging.info(f"Poção {potion_type} encontrada com {max_corr:.2f}% de correlação em ({abs_x}, {abs_y})")
                    # Desenhar o retângulo do match para debug
                    debug_img = inv_region.copy()
                    bottom_right_x = top_left_x + template_w
                    bottom_right_y = top_left_y + template_h
                    cv2.rectangle(debug_img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (0, 255, 0), 2)
                    cv2.imwrite(f'debug_potion_match_{potion_type}.png', debug_img)

                return (abs_x, abs_y)
            else:
                logging.info(f"Poção {potion_type} não encontrada no inventário (melhor correlação: {max_corr:.2f} < {match_threshold})")
                return None

        except Exception as e:
            logging.error(f"Erro ao encontrar poção {potion_type} no inventário por template matching: {e}")
            return None
    
    def refill_potion(self, potion_type):
        """
        Repõe uma poção específica do inventário
        """
        try:
            logging.warning(f"INICIANDO REPOSICAO DE POCAO: {potion_type.upper()}")
            
            # 0. Salvar posição original do mouse
            original_x, original_y = pyautogui.position()
            logging.info(f"Posição original do mouse salva: ({original_x}, {original_y})")
            
            # 1. Abrir inventário
            if not self.open_inventory():
                # Restaurar posição original se falhar
                pyautogui.moveTo(original_x, original_y, duration=0.3)
                return False
            
            # 2. Aguardar abertura completa
            time.sleep(0.5)
            
            # 3. Encontrar poção no inventário
            potion_pos = self.find_potion_in_inventory(potion_type)
            if potion_pos is None:
                logging.error(f"Poção {potion_type} não encontrada no inventário")
                # Fechar inventário e restaurar posição
                pyautogui.press('v')
                time.sleep(0.3)
                pyautogui.moveTo(original_x, original_y, duration=0.3)
                return False
            
            x, y = potion_pos
            logging.info(f"Poção {potion_type} encontrada no inventário em ({x}, {y})")
            
            # 4. Mover mouse para a poção
            pyautogui.moveTo(x, y, duration=0.3)
            time.sleep(0.2)
            logging.info(f"Mouse posicionado sobre poção em ({x}, {y})")
            
            # 5. Aguardar posicionamento
            time.sleep(0.2)
            
            # 6. Executar comando Shift + tecla correspondente COM MOUSE SOBRE A POÇÃO
            if potion_type == 'red_potion':
                logging.warning("RECARREGANDO HP - Shift+1")
                # Garantir que mouse está na posição e executar comando
                pyautogui.moveTo(x, y, duration=0.1)  # Reconfirmar posição
                self.simulate_key_combination(['shift', '1'], preserve_mouse_position=True)
                time.sleep(0.3)  # Aguardar execução com mouse parado
            elif potion_type == 'green_potion':
                logging.warning("RECARREGANDO ENERGY - Shift+2")
                # Garantir que mouse está na posição e executar comando
                pyautogui.moveTo(x, y, duration=0.1)  # Reconfirmar posição
                self.simulate_key_combination(['shift', '2'], preserve_mouse_position=True)
                time.sleep(0.3)  # Aguardar execução com mouse parado
            elif potion_type == 'blue_potion':
                logging.warning("RECARREGANDO MANA - Shift+3")
                # Garantir que mouse está na posição e executar comando
                pyautogui.moveTo(x, y, duration=0.1)  # Reconfirmar posição
                self.simulate_key_combination(['shift', '3'], preserve_mouse_position=True)
                time.sleep(0.3)  # Aguardar execução com mouse parado
            
            # 7. Aguardar reposição
            time.sleep(0.5)
            
            # 8. Fechar inventário com tecla 'v'
            logging.info("Fechando inventário com tecla 'v'...")
            pyautogui.press('v')
            time.sleep(0.3)  # Aguardar fechamento
            
            # 9. Restaurar posição original do mouse
            logging.info(f"Restaurando posição original do mouse: ({original_x}, {original_y})")
            pyautogui.moveTo(original_x, original_y, duration=0.5)
            
            logging.warning(f"REPOSICAO DE {potion_type.upper()} CONCLUIDA!")
            return True
            
        except Exception as e:
            logging.error(f"Erro durante reposição de poção {potion_type}: {e}")
            
            # Fechar inventário e restaurar posição em caso de erro
            try:
                pyautogui.press('v')  # Fechar inventário
                time.sleep(0.3)
                pyautogui.moveTo(original_x, original_y, duration=0.3)  # Restaurar posição
            except:
                pass
            
            return False
    
    def simulate_key_press(self, key):
        """Simula o pressionamento de uma tecla"""
        try:
            pyautogui.press(key)
            time.sleep(0.1)  # Pequeno delay entre teclas
            if self.show_action_logs:
                logging.warning(f"TECLA PRESSIONADA: {key.upper()}")
        except Exception as e:
            logging.error(f"Erro ao pressionar tecla {key}: {e}")
    
    def simulate_key_combination(self, keys, preserve_mouse_position=False):
        """
        Simula combinação de teclas (ex: shift+1)
        Args:
            keys: lista de teclas para pressionar simultaneamente
            preserve_mouse_position: se True, salva e restaura posição do mouse
        """
        try:
            # Salvar posição atual do mouse se necessário
            if preserve_mouse_position:
                current_x, current_y = pyautogui.position()
            
            pyautogui.hotkey(*keys)
            
            # Restaurar posição do mouse se necessário
            if preserve_mouse_position:
                pyautogui.moveTo(current_x, current_y, duration=0.1)
            
            if self.show_action_logs:
                logging.warning(f"COMBINACAO DE TECLAS: {'+'.join(keys).upper()}")
        except Exception as e:
            logging.error(f"Erro ao pressionar combinação {'+'.join(keys)}: {e}")
    
    def simulate_right_click(self, count=1, delay=0.1):
        """Simula cliques do botão direito do mouse"""
        try:
            for i in range(count):
                pyautogui.rightClick()
                if i < count - 1:  # Não dar delay após o último clique
                    time.sleep(delay)
            
            if self.show_action_logs:
                logging.info(f"Executados {count} cliques direitos")
        except Exception as e:
            logging.error(f"Erro ao executar cliques direitos: {e}")
    
    def background_service(self):
        """
        Serviço em background que executa cliques aleatórios e fluxo periódico
        Roda em thread separada
        """
        while self.running:
            try:
                current_time = time.time()
                
                # Clique a cada 1 segundo
                if current_time - self.last_background_click >= self.background_interval:
                    time.sleep(random.uniform(0.3, 0.7))
                    self.simulate_right_click(count=1)
                    self.last_background_click = current_time
                    self.background_interval = 1

                    if self.show_action_logs:
                        logging.info(f"Clique em background executado. Próximo em {self.background_interval}s")
                
                                # Fluxo periódico a cada 5 minutos
                if current_time - self.last_periodic_flow >= self.periodic_flow_interval:
                    if self.show_action_logs:
                        logging.info("Iniciando novo fluxo periódico: F2 + Clique Direito -> F3 + Clique Direito -> F1...")

                    # Teclar F2 + Clique com botão direito
                    pyautogui.keyDown('f2')
                    time.sleep(0.05) # Pequeno delay para simular o pressionamento
                    pyautogui.keyUp('f2')
                    time.sleep(0.1) # Pequeno delay para garantir o registro da tecla
                    pyautogui.rightClick()
                    time.sleep(0.5) # Aguardar 0.5s (mais rápido)

                    # Clicar F3 + Clique com botão direito
                    pyautogui.keyDown('f3')
                    time.sleep(0.05) # Pequeno delay para simular o pressionamento
                    pyautogui.keyUp('f3')
                    time.sleep(0.1) # Pequeno delay para garantir o registro da tecla
                    pyautogui.rightClick()
                    time.sleep(0.5) # Aguardar 0.5s (mais rápido)

                    # Teclar F1
                    pyautogui.keyDown('f1')
                    time.sleep(0.05) # Pequeno delay para simular o pressionamento
                    pyautogui.keyUp('f1')

                    self.last_periodic_flow = current_time

                    if self.show_action_logs:
                        logging.info("Novo fluxo periódico concluído.")
                time.sleep(1)  # Evitar uso excessivo de CPU
                
            except Exception as e:
                logging.error(f"Erro no serviço background: {e}")
                time.sleep(5)
    
    def calibrate_regions(self):
        """
        Sistema interativo de calibração das regiões.
        Permite ajustar posições e tamanhos das áreas de monitoramento.
        
        Controles:
        - CLIQUE E ARRASTE: mover regiões diretamente com o mouse
        - W/A/S/D: mover região selecionada (5 pixels)
        - Setas: redimensionar região selecionada (5 pixels)
        - 1/2/3: selecionar barra (HP/Mana/Energy)
        - 4/5/6: selecionar poção (Red/Green/Blue)
        - 7: selecionar inventário
        - R: resetar região selecionada para padrão
        - SPACE: salvar calibração atual
        - Q/ESC: sair da calibração
        """
        print("🎯 SISTEMA DE CALIBRAÇÃO INTERATIVA")
        print("=" * 50)
        print("INSTRUÇÕES:")
        print("- 🖱️  CLIQUE E ARRASTE as regiões para movê-las")
        print("- [1-3] - Selecionar barra (1=HP, 2=Mana, 3=Energy)")
        print("- [4-6] - Selecionar poção (4=Red, 5=Green, 6=Blue)")
        print("- [7] - Selecionar região do inventário")
        print("- [WASD] - Mover região selecionada (5 pixels)")
        print("- [+/-] - Aumentar/diminuir largura")
        print("- [Setas Cima/Baixo] - Aumentar/diminuir altura")
        print("- [R] - Resetar posições")
        print("- [SPACE] - Salvar coordenadas")
        print("- [Q/ESC] - Sair")
        print()
        
        # Configurações da calibração
        selected_region = 'hp'  # Região atualmente selecionada
        dragging = False
        drag_start = None
        drag_offset = None
        scale = 0.7  # Escala de visualização
        
        # Valores padrão para reset
        default_regions = {
            'hp': (600, 920, 25, 120),
            'mana': (870, 990, 25, 50),
            'energy': (570, 997, 15, 45),
            'red_potion': (650, 1000, 30, 30),
            'green_potion': (690, 1000, 30, 30),
            'blue_potion': (730, 1000, 30, 30),
            'inventory': (768, 324, 672, 432)
        }
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal dragging, drag_start, drag_offset, selected_region
            
            # Converter coordenadas da tela escalada para coordenadas reais
            real_x = int(x / scale)
            real_y = int(y / scale)
            
            if event == cv2.EVENT_LBUTTONDOWN:
                # Verificar qual região foi clicada
                clicked_region = None
                regions_to_check = {
                    **self.bar_regions,
                    **self.potion_regions,
                    'inventory': self.inventory_region
                }
                
                for name, region in regions_to_check.items():
                    rx, ry, rw, rh = region
                    if rx <= real_x <= rx + rw and ry <= real_y <= ry + rh:
                        clicked_region = name
                        break
                
                if clicked_region:
                    selected_region = clicked_region
                    dragging = True
                    drag_start = (real_x, real_y)
                    
                    # Calcular offset dentro da região
                    current_region = None
                    if selected_region in self.bar_regions:
                        current_region = self.bar_regions[selected_region]
                    elif selected_region in self.potion_regions:
                        current_region = self.potion_regions[selected_region]
                    elif selected_region == 'inventory':
                        current_region = self.inventory_region
                    
                    if current_region:
                        rx, ry, rw, rh = current_region
                        drag_offset = (real_x - rx, real_y - ry)
                    
                    print(f"🎯 Região selecionada: {selected_region.upper()}")
            
            elif event == cv2.EVENT_MOUSEMOVE and dragging:
                # Mover região durante o arraste
                if drag_offset:
                    new_x = real_x - drag_offset[0]
                    new_y = real_y - drag_offset[1]
                    
                    # Atualizar posição da região
                    if selected_region in self.bar_regions:
                        _, _, w, h = self.bar_regions[selected_region]
                        self.bar_regions[selected_region] = (new_x, new_y, w, h)
                    elif selected_region in self.potion_regions:
                        _, _, w, h = self.potion_regions[selected_region]
                        self.potion_regions[selected_region] = (new_x, new_y, w, h)
                    elif selected_region == 'inventory':
                        _, _, w, h = self.inventory_region
                        self.inventory_region = (new_x, new_y, w, h)
            
            elif event == cv2.EVENT_LBUTTONUP:
                if dragging:
                    dragging = False
                    drag_start = None
                    drag_offset = None
                    print(f"✅ Região {selected_region.upper()} movida para nova posição")
        
        try:
            # Criar janela e configurar callback do mouse
            window_name = 'Calibração - Clique e arraste as regiões'
            cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
            cv2.setMouseCallback(window_name, mouse_callback)
            
            while True:
                # Capturar tela atual
                frame = self.capture_screen()
                if frame is None:
                    continue
                
                # Criar cópia para desenhar
                display_frame = frame.copy()
                
                # Desenhar todas as regiões
                regions_to_draw = {
                    **self.bar_regions,
                    **self.potion_regions,
                    'inventory': self.inventory_region
                }
                
                for name, region in regions_to_draw.items():
                    x, y, w, h = region
                    
                    # Cor baseada no tipo e se está selecionada
                    if name == selected_region:
                        if dragging:
                            color = (0, 255, 255)  # Amarelo para arrastando
                            thickness = 4
                        else:
                            color = (0, 255, 0)  # Verde para selecionada
                            thickness = 3
                    elif name in self.bar_regions:
                        color = (0, 0, 255)  # Vermelho para barras
                        thickness = 2
                    elif name in self.potion_regions:
                        color = (255, 0, 0)  # Azul para poções
                        thickness = 2
                    else:
                        color = (255, 255, 0)  # Ciano para inventário
                        thickness = 2
                    
                    # Desenhar retângulo
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, thickness)
                    
                    # Adicionar texto
                    label = name.upper()
                    if name == selected_region and dragging:
                        label += " (ARRASTANDO)"
                    cv2.putText(display_frame, label, (x, y - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    # Adicionar ponto central para facilitar o clique
                    center_x = x + w // 2
                    center_y = y + h // 2
                    cv2.circle(display_frame, (center_x, center_y), 3, color, -1)
                
                # Redimensionar para exibição
                height, width = display_frame.shape[:2]
                scale = 0.7
                new_width = int(width * scale)
                new_height = int(height * scale)
                display_frame = cv2.resize(display_frame, (new_width, new_height))
                
                # Mostrar informações da região selecionada
                current_region = None
                if selected_region in self.bar_regions:
                    current_region = self.bar_regions[selected_region]
                elif selected_region in self.potion_regions:
                    current_region = self.potion_regions[selected_region]
                elif selected_region == 'inventory':
                    current_region = self.inventory_region
                
                if current_region:
                    x, y, w, h = current_region
                    info_text = f"{selected_region.upper()}: x={x}, y={y}, w={w}, h={h}"
                    cv2.putText(display_frame, info_text, (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Adicionar instruções na tela
                instructions = [
                    "CLIQUE E ARRASTE para mover regioes",
                    "1-7: Selecionar | WASD: Mover | +/-: Largura | [ ]: Altura",
                    "SPACE: Salvar | Q: Sair"
                ]
                
                for i, instruction in enumerate(instructions):
                    y_pos = display_frame.shape[0] - 80 + (i * 25)
                    cv2.putText(display_frame, instruction, (10, y_pos), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Exibir frame
                cv2.imshow(window_name, display_frame)
                
                # Capturar tecla pressionada
                key = cv2.waitKey(1)
                
                # Verificar se a janela foi fechada
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
                
                # Processar comandos
                if key == ord('q') or key == 27:  # Q ou ESC
                    break
                elif key == ord('1'):
                    selected_region = 'hp'
                    print(f"Região selecionada: {selected_region.upper()}")
                elif key == ord('2'):
                    selected_region = 'mana'
                    print(f"Região selecionada: {selected_region.upper()}")
                elif key == ord('3'):
                    selected_region = 'energy'
                    print(f"Região selecionada: {selected_region.upper()}")
                elif key == ord('4'):
                    selected_region = 'red_potion'
                    print(f"Região selecionada: {selected_region.upper()}")
                elif key == ord('5'):
                    selected_region = 'green_potion'
                    print(f"Região selecionada: {selected_region.upper()}")
                elif key == ord('6'):
                    selected_region = 'blue_potion'
                    print(f"Região selecionada: {selected_region.upper()}")
                elif key == ord('7'):
                    selected_region = 'inventory'
                    print(f"Região selecionada: {selected_region.upper()}")
                elif key == ord(' '):  # SPACE
                    self.save_calibration()
                elif key == ord('r'):  # Reset
                    if selected_region in default_regions:
                        if selected_region in self.bar_regions:
                            self.bar_regions[selected_region] = default_regions[selected_region]
                        elif selected_region in self.potion_regions:
                            self.potion_regions[selected_region] = default_regions[selected_region]
                        elif selected_region == 'inventory':
                            self.inventory_region = default_regions[selected_region]
                        print(f"Região {selected_region.upper()} resetada")
                
                # Movimento (WASD)
                elif key == ord('w'):  # Cima
                    self._move_region(selected_region, 0, -5)
                elif key == ord('s'):  # Baixo
                    self._move_region(selected_region, 0, 5)
                elif key == ord('a'):  # Esquerda
                    self._move_region(selected_region, -5, 0)
                elif key == ord('d'):  # Direita
                    self._move_region(selected_region, 5, 0)
                
                # Redimensionamento
                elif key == ord('+') or key == ord('='):  # Aumentar largura
                    self._resize_region(selected_region, 5, 0)
                elif key == ord('-'):  # Diminuir largura
                    self._resize_region(selected_region, -5, 0)
                elif key == ord('['): # Aumentar altura
                    self._resize_region(selected_region, 0, 5)
                elif key == ord(']'): # Diminuir altura
                    self._resize_region(selected_region, 0, -5)
                
                time.sleep(0.05)  # Pequeno delay para suavizar
        
        except Exception as e:
            logging.error(f"Erro na calibração: {e}")
        finally:
            cv2.destroyAllWindows()
            print("Calibração finalizada!")
    
    def _move_region(self, region_name, dx, dy):
        """Move uma região por dx, dy pixels"""
        try:
            if region_name in self.bar_regions:
                x, y, w, h = self.bar_regions[region_name]
                self.bar_regions[region_name] = (x + dx, y + dy, w, h)
            elif region_name in self.potion_regions:
                x, y, w, h = self.potion_regions[region_name]
                self.potion_regions[region_name] = (x + dx, y + dy, w, h)
            elif region_name == 'inventory':
                x, y, w, h = self.inventory_region
                self.inventory_region = (x + dx, y + dy, w, h)
        except Exception as e:
            logging.error(f"Erro ao mover região {region_name}: {e}")
    
    def _resize_region(self, region_name, dw, dh):
        """Redimensiona uma região por dw, dh pixels"""
        try:
            if region_name in self.bar_regions:
                x, y, w, h = self.bar_regions[region_name]
                self.bar_regions[region_name] = (x, y, max(5, w + dw), max(5, h + dh))
            elif region_name in self.potion_regions:
                x, y, w, h = self.potion_regions[region_name]
                self.potion_regions[region_name] = (x, y, max(5, w + dw), max(5, h + dh))
            elif region_name == 'inventory':
                x, y, w, h = self.inventory_region
                self.inventory_region = (x, y, max(50, w + dw), max(50, h + dh))
        except Exception as e:
            logging.error(f"Erro ao redimensionar região {region_name}: {e}")
    
    def save_calibration(self):
        """Salva as coordenadas atuais"""
        print("\n=== COORDENADAS ATUAIS ===")
        print("Copie e cole no código para salvar:")
        print()
        print("# Coordenadas das barras VERTICAIS")
        print("self.bar_regions = {")
        for name, region in self.bar_regions.items():
            print(f"    '{name}': {region},")
        print("}")
        print()
        print("# Coordenadas das poções")
        print("self.potion_regions = {")
        for name, region in self.potion_regions.items():
            print(f"    '{name}': {region},")
        print("}")
        print()
        print(f"# Região do inventário")
        print(f"self.inventory_region = {self.inventory_region}")
        print()
        print("Coordenadas salvas! Atualize o código com esses valores.")
        
        # Salvar em arquivo também
        try:
            with open('calibration_backup.txt', 'w') as f:
                f.write("# Backup da calibração\n")
                f.write(f"bar_regions = {self.bar_regions}\n")
                f.write(f"potion_regions = {self.potion_regions}\n")
                f.write(f"inventory_region = {self.inventory_region}\n")
            print("Backup salvo em 'calibration_backup.txt'")
        except Exception as e:
            logging.error(f"Erro ao salvar backup: {e}")
    
    def test_key_simulation(self):
        """Testa a simulação de teclas"""
        print("\n=== TESTE DE SIMULAÇÃO DE TECLAS ===")
        print("Testando teclas individuais em 3 segundos...")
        time.sleep(3)
        
        print("Testando tecla 1 (HP)...")
        self.simulate_key_press('1')
        time.sleep(1)
        
        print("Testando tecla 2 (Energy)...")
        self.simulate_key_press('2')
        time.sleep(1)
        
        print("Testando tecla 3 (Mana)...")
        self.simulate_key_press('3')
        time.sleep(1)
        
        print("Testando Shift+1...")
        self.simulate_key_combination(['shift', '1'])
        time.sleep(1)
        
        print("Testando cliques direitos...")
        self.simulate_right_click(2, 0.2)
        
        print("Teste concluído!")
    
    def run_diagnostics(self):
        """Executa diagnóstico completo das barras"""
        print("\n🔍 DIAGNÓSTICO COMPLETO DAS BARRAS")
        print("=" * 50)
        print("Capturando e analisando barras em tempo real por 10 segundos...")
        
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 10:
            frame = self.capture_screen()
            if frame is None:
                continue
                
            frame_count += 1
            print(f"\n📊 FRAME {frame_count} - {time.time() - start_time:.1f}s")
            
            for bar_type, region in self.bar_regions.items():
                try:
                    bar_image = self.extract_region(frame, region)
                    if bar_image is None:
                        print(f"❌ {bar_type.upper()}: Região inválida")
                        continue
                    
                    # Salvar imagem para debug
                    cv2.imwrite(f'diagnostic_bar_{bar_type}_frame_{frame_count}.png', bar_image)
                    
                    # Análise detalhada
                    level, details = self.analyze_bar_level_advanced(bar_image, bar_type)
                    threshold = 40 if bar_type == 'hp' else 30
                    action_needed = level < threshold
                    
                    print(f"🔹 {bar_type.upper()}: {level:.1f}% "
                          f"(Limite: {threshold}%) "
                          f"{'🚨 AÇÃO NECESSÁRIA!' if action_needed else '✅ OK'}")
                    
                    if self.debug_mode:
                        print(f"   Detalhes: BGR={details.get('bgr_score', 0):.1f}, "
                              f"HSV={details.get('hsv_score', 0):.1f}, "
                              f"Gradient={details.get('gradient_score', 0):.1f}, "
                              f"Fill={details.get('fill_score', 0):.1f}")
                    
                except Exception as e:
                    print(f"❌ Erro ao analisar {bar_type}: {e}")
            
            time.sleep(1)  # 1 segundo entre análises
        
        print(f"\n✅ Diagnóstico concluído! {frame_count} frames analisados.")
        print("💾 Imagens salvas: diagnostic_bar_*_frame_*.png")
    
    def run_potion_diagnostics(self):
        """Executa diagnóstico completo das poções"""
        print("\n🧪 DIAGNÓSTICO COMPLETO DAS POÇÕES")
        print("=" * 50)
        print("Capturando e analisando poções em tempo real por 10 segundos...")
        
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 10:
            frame = self.capture_screen()
            if frame is None:
                continue
                
            frame_count += 1
            print(f"\n🧪 FRAME {frame_count} - {time.time() - start_time:.1f}s")
            
            for potion_type, region in self.potion_regions.items():
                try:
                    potion_image = self.extract_region(frame, region)
                    if potion_image is None:
                        print(f"❌ {potion_type.upper()}: Região inválida")
                        continue
                    
                    # Salvar imagem para debug
                    cv2.imwrite(f'diagnostic_potion_{potion_type}_frame_{frame_count}.png', potion_image)
                    
                    # Análise detalhada
                    is_empty = self.analyze_potion_status(potion_image, potion_type)
                    
                    # Calcular métricas individuais para debug
                    mean_intensity = np.mean(potion_image)
                    gray = cv2.cvtColor(potion_image, cv2.COLOR_BGR2GRAY)
                    edges = cv2.Canny(gray, 50, 150)
                    edge_density = np.sum(edges > 0) / edges.size
                    
                    # Análise de cor específica
                    hsv = cv2.cvtColor(potion_image, cv2.COLOR_BGR2HSV)
                    if potion_type == 'red_potion':
                        mask = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([20, 255, 255]))
                        color_name = "Vermelho"
                    elif potion_type == 'green_potion':
                        mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
                        color_name = "Verde"
                    elif potion_type == 'blue_potion':
                        mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([140, 255, 255]))
                        color_name = "Azul"
                    else:
                        mask = np.zeros_like(gray)
                        color_name = "Desconhecido"
                    
                    color_percentage = (np.sum(mask > 0) / mask.size) * 100
                    
                    print(f"🧪 TESTANDO POÇÃO {potion_type.upper()}:")
                    print(f"   Região: {region}")
                    print(f"   💾 Imagem salva: diagnostic_potion_{potion_type}_frame_{frame_count}.png")
                    print(f"   📐 Dimensões: {potion_image.shape[1]}x{potion_image.shape[0]} pixels")
                    
                    # Análise de cor média
                    mean_bgr = np.mean(potion_image, axis=(0, 1))
                    print(f"   🎨 Cor média (BGR): B={mean_bgr[0]:.1f}, G={mean_bgr[1]:.1f}, R={mean_bgr[2]:.1f}")
                    
                    print(f"   🔆 Intensidade média: {mean_intensity:.1f}/255 ({mean_intensity/255*100:.1f}%)")
                    print(f"   📏 Densidade de bordas: {edge_density:.3f} ({edge_density*100:.1f}%)")
                    print(f"   🔴 Cor {color_name}: {color_percentage:.1f}% da imagem")
                    
                    # Critérios de detecção
                    low_intensity = mean_intensity < 80
                    low_edges = edge_density < 0.15
                    low_color = color_percentage < 10
                    criteria_met = sum([low_intensity, low_edges, low_color])
                    
                    print(f"   📊 ANÁLISE COMPLETA:")
                    print(f"       Intensidade: {mean_intensity:.1f} (threshold: 80)")
                    print(f"       Bordas: {edge_density:.3f} (threshold: 0.15)")
                    print(f"       Cor específica: {color_percentage:.1f}% (threshold: 10%)")
                    print(f"   🎯 CRITÉRIOS:")
                    print(f"       {'✓' if low_intensity else '✗'} Intensidade baixa | "
                          f"{'✓' if low_edges else '✗'} Poucas bordas | "
                          f"{'✓' if low_color else '✗'} Pouca cor")
                    print(f"   🏆 RESULTADO FINAL: {'🚨 VAZIA' if is_empty else '✅ OK'}")
                    
                    # Simular teste de reposição
                    print(f"   🔄 TESTE DE REPOSIÇÃO:")
                    if is_empty:
                        print(f"   🚨 POÇÃO DETECTADA COMO VAZIA - Simulando reposição...")
                        print(f"   📝 Ação seria: Abrir inventário -> Encontrar {potion_type} -> Shift+{'1' if potion_type == 'red_potion' else '2' if potion_type == 'green_potion' else '3'}")
                    else:
                        print(f"   ✅ POÇÃO OK - Nenhuma ação necessária")
                    
                except Exception as e:
                    print(f"❌ Erro ao analisar {potion_type}: {e}")
            
            time.sleep(1)  # 1 segundo entre análises
        
        print(f"\n✅ Diagnóstico de poções concluído! {frame_count} frames analisados.")
        print("💾 Imagens salvas: diagnostic_potion_*_frame_*.png")
    
    def test_periodic_flow(self):
        """
        Testa a rotina de fluxo periódico F2->F3->F1.
        ATENÇÃO: Este teste executará AÇÕES REAIS no jogo!
        """
        print("\n🧪 TESTE DE FLUXO PERIÓDICO F2->F3->F1")
        print("=" * 50)
        print("⚠️  ATENÇÃO: Este teste executará AÇÕES REAIS no jogo!")
        print("🎮 Certifique-se de estar com foco na janela do jogo.")
        print()

        confirm = input("Deseja continuar? (s/N): ").strip().lower()
        if confirm != 's':
            print("Teste cancelado.")
            return

        print("\n⏰ Aguardando 5 segundos para você focar no jogo...")
        for i in range(5, 0, -1):
            print(f"   {i}...", end='\r')
            time.sleep(1)
        print("   🚀 INICIANDO TESTE!")

        try:
            if self.show_action_logs:
                logging.info("Iniciando fluxo periódico F2->F3->F1 (TESTE)...")

            # Pressionar F2
            pyautogui.keyDown('f2')
            time.sleep(0.05) # Pequeno delay para simular o pressionamento
            pyautogui.keyUp('f2')
            time.sleep(0.5) # Added small delay after press

            # 3 cliques direitos com intervalo de 0.5s cada para teste
            for i in range(3):
                pyautogui.rightClick()
                if i < 2:
                    time.sleep(0.5) # Reduced to 0.5s

            time.sleep(0.5) # Added small delay

            # Pressionar F3
            pyautogui.keyDown('f3')
            time.sleep(0.05) # Pequeno delay para simular o pressionamento
            pyautogui.keyUp('f3')
            time.sleep(0.5) # Added small delay after press

            # 3 cliques direitos com intervalo de 0.5s cada para teste
            for i in range(3):
                pyautogui.rightClick()
                if i < 2:
                    time.sleep(0.5) # Reduced to 0.5s

            time.sleep(0.5) # Added small delay

            # Pressionar F1 para finalizar
            pyautogui.keyDown('f1')
            time.sleep(0.05) # Pequeno delay para simular o pressionamento
            pyautogui.keyUp('f1')

            if self.show_action_logs:
                logging.info("Fluxo periódico F2->F3->F1 (TESTE) concluído com sucesso!")
            print("\n✅ Teste de fluxo periódico concluído!")

        except Exception as e:
            logging.error(f"Erro durante o teste de fluxo periódico: {e}")
            print("\n❌ Teste de fluxo periódico falhou!")

    def test_empty_slot(self):
        """Testa especificamente slots vazios com ações reais"""
        print("\n🔬 TESTE DE SLOT VAZIO (REAL)")
        print("=" * 50)
        print("⚠️  ATENÇÃO: Este teste executará AÇÕES REAIS no jogo!")
        print("🎮 Certifique-se de:")
        print("   1. Ter uma poção vazia no jogo")
        print("   2. Estar com foco na janela do jogo")
        print("   3. Ter poções no inventário para reposição")
        print()
        
        confirm = input("Deseja continuar? (s/N): ").strip().lower()
        if confirm != 's':
            print("Teste cancelado.")
            return
        
        print("\n⏰ Aguardando 10 segundos para você focar no jogo...")
        for i in range(10, 0, -1):
            print(f"   {i}...", end='\r')
            time.sleep(1)
        print("   🚀 INICIANDO TESTE!")
        
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < 30:  # Teste por 30 segundos
            frame = self.capture_screen()
            if frame is None:
                continue
                
            attempt += 1
            print(f"\n🔍 TENTATIVA {attempt} - {time.time() - start_time:.1f}s")
            
            for potion_type, region in self.potion_regions.items():
                try:
                    potion_image = self.extract_region(frame, region)
                    if potion_image is None:
                        continue
                    
                    # Salvar imagem de teste
                    cv2.imwrite(f'test_empty_{potion_type}_attempt_{attempt}.png', potion_image)
                    
                    # Analisar se está vazio
                    is_empty = self.analyze_potion_status(potion_image, potion_type)
                    
                    print(f"🧪 {potion_type.upper()}: {'🚨 VAZIO' if is_empty else '✅ OK'}")
                    
                    if is_empty:
                        print(f"🚨 DETECTADO SLOT VAZIO: {potion_type.upper()}")
                        print(f"🔄 Executando reposição real...")
                        
                        # Executar reposição real
                        success = self.refill_potion(potion_type)
                        
                        if success:
                            print(f"✅ SUCESSO! Poção {potion_type.upper()} foi reposta!")
                        else:
                            print(f"❌ FALHA na reposição de {potion_type.upper()}")
                        
                        print(f"🎯 TESTE COMPLETO! Slot vazio foi detectado e processado.")
                        print(f"✅ Teste concluído!")
                        print(f"📁 Imagens salvas: test_empty_*_attempt_*.png")
                        print(f"📊 RESULTADOS:")
                        print(f"   ✅ Detecção de slot vazio: FUNCIONANDO")
                        print(f"   {'✅' if success else '❌'} Sistema de reposição: {'FUNCIONANDO' if success else 'FALHA'}")
                        return
                
                except Exception as e:
                    print(f"❌ Erro no teste de {potion_type}: {e}")
            
            time.sleep(2)  # Aguardar 2 segundos entre tentativas
        
        print("\n⏰ Tempo de teste esgotado (30s)")
        print("💡 Nenhum slot vazio foi detectado durante o teste")
        print("📁 Imagens salvas: test_empty_*_attempt_*.png")
    
    def configure_logs(self):
        """Configuração de logs opcionais"""
        print("\n⚙️ CONFIGURAÇÃO DE LOGS")
        print("=" * 30)
        
        while True:
            print(f"\nEstado atual dos logs:")
            print(f"1. Debug Mode: {'🟢 ATIVO' if self.debug_mode else '🔴 INATIVO'}")
            print(f"2. Logs Verbosos: {'🟢 ATIVO' if self.verbose_logs else '🔴 INATIVO'}")
            print(f"3. Logs de Barras: {'🟢 ATIVO' if self.show_bar_logs else '🔴 INATIVO'}")
            print(f"4. Logs de Poções: {'🟢 ATIVO' if self.show_potion_logs else '🔴 INATIVO'}")
            print(f"5. Logs de Ações: {'🟢 ATIVO' if self.show_action_logs else '🔴 INATIVO'}")
            print(f"6. Modo Silencioso (desativa maioria)")
            print(f"7. Modo Completo (ativa todos)")
            print(f"8. Voltar ao menu principal")
            
            choice = input("\nEscolha uma opção (1-8): ").strip()
            
            if choice == '1':
                self.debug_mode = not self.debug_mode
                print(f"Debug Mode: {'ATIVADO' if self.debug_mode else 'DESATIVADO'}")
            elif choice == '2':
                self.verbose_logs = not self.verbose_logs
                print(f"Logs Verbosos: {'ATIVADO' if self.verbose_logs else 'DESATIVADO'}")
            elif choice == '3':
                self.show_bar_logs = not self.show_bar_logs
                print(f"Logs de Barras: {'ATIVADO' if self.show_bar_logs else 'DESATIVADO'}")
            elif choice == '4':
                self.show_potion_logs = not self.show_potion_logs
                print(f"Logs de Poções: {'ATIVADO' if self.show_potion_logs else 'DESATIVADO'}")
            elif choice == '5':
                self.show_action_logs = not self.show_action_logs
                print(f"Logs de Ações: {'ATIVADO' if self.show_action_logs else 'DESATIVADO'}")
            elif choice == '6':
                # Modo silencioso
                self.debug_mode = False
                self.verbose_logs = False
                self.show_bar_logs = False
                self.show_potion_logs = False
                self.show_action_logs = False
                print("✅ Modo Silencioso ativado!")
            elif choice == '7':
                # Modo completo
                self.debug_mode = True
                self.verbose_logs = True
                self.show_bar_logs = True
                self.show_potion_logs = True
                self.show_action_logs = True
                print("✅ Modo Completo ativado!")
            elif choice == '8':
                break
            else:
                print("❌ Opção inválida!")
    
    def start(self):
        """Inicia o monitoramento do jogo"""
        self.running = True
        logging.info("Iniciando GameBot...")

        logging.info("Aguardando 5 segundos antes de iniciar o monitoramento...")
        time.sleep(5)
        
        # Iniciar serviço em background em thread separada
        background_thread = threading.Thread(target=self.background_service, daemon=True)
        background_thread.start()
        
        # Loop principal de monitoramento
        try:
            while self.running:
                # Salvar posição original do mouse no início de cada iteração
                original_mouse_x, original_mouse_y = pyautogui.position()
                
                # Capturar tela
                frame = self.capture_screen()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Monitorar barras e poções
                self.monitor_bars(frame)
                self.monitor_potions(frame)
                
                # Restaurar posição original do mouse após monitoramento
                current_x, current_y = pyautogui.position()
                if (current_x != original_mouse_x or current_y != original_mouse_y):
                    pyautogui.moveTo(original_mouse_x, original_mouse_y, duration=0.2)
                
                # Pequena pausa para não sobrecarregar o sistema
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logging.info("Interrupção pelo usuário detectada")
        except Exception as e:
            logging.error(f"Erro no loop principal: {e}")
        finally:
            self.running = False
            logging.info("GameBot finalizado")

def main():
    """Função principal"""
    print("=== Automação de Jogo - Monitor de Barras e Poções ===")
    print("Desenvolvido por: Fabricio Costa")
    print("Data: 18/09/2025\n")
    
    bot = GameBot()
    
    while True:
        print("\nOpções:")
        print("1. Iniciar monitoramento")
        print("2. Calibrar regiões (manual)")
        print("3. Testar simulação de teclas")
        print("4. Modo debug (salvar imagens das barras)")
        print("5. DIAGNÓSTICO COMPLETO das barras")
        print("6. DIAGNÓSTICO COMPLETO das poções")
        print("7. TESTAR FLUXO PERIÓDICO F2->F3->F1")
        print("8. TESTE DE SLOT VAZIO (usar poção no jogo)")
        print("9. Configurar logs")
        print("10. Sair")
        
        choice = input("\nEscolha uma opção (1-10): ").strip()

        if choice == '1':
            print("\nIniciando monitoramento...")
            print("Pressione Ctrl+C para parar\n")
            bot.start()

        elif choice == '2':
            print("\nModo calibração manual ativo")
            print("Ajuste as coordenadas conforme necessário")
            print("Pressione 'q' na janela de calibração para sair\n")
            bot.calibrate_regions()

        elif choice == '3':
            bot.test_key_simulation()

        elif choice == '4':
            bot.debug_mode = True
            print("\nModo debug ativado!")
            print("As imagens das barras serão salvas como debug_bar_*.png")
            print("Execute o monitoramento para gerar as imagens de debug")

        elif choice == '5':
            bot.run_diagnostics()

        elif choice == '6':
            bot.run_potion_diagnostics()

        elif choice == '7': # New option
            bot.test_periodic_flow()

        elif choice == '8': # Shifted
            bot.test_empty_slot()

        elif choice == '9': # Shifted
            bot.configure_logs()

        elif choice == '10': # Shifted
            print("\nFinalizando aplicação...")
            break

        else:
            print("\nOpção inválida! Tente novamente.")
if __name__ == "__main__":
    main()
