import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import logging

try:
    from game_automation import GameBot, on_f12_press
    import global_vars
except ImportError:
    print("[ERRO FATAL] O arquivo 'game_automation.py' não foi encontrado. A GUI não pode ser iniciada.")
    input("Pressione Enter para sair.")
    exit()
import keyboard

class QueueHandler(logging.Handler):
    """
    Classe para redirecionar logs para uma fila (queue) que a GUI pode ler.
    """
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

class BotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Automation Bot")
        self.root.geometry("600x750")

        # Inicializa o bot
        self.bot = GameBot()
        self.bot_thread = None

        # Configura o hotkey F12
        keyboard.on_press_key("f12", self.handle_f12_press)

        # --- Layout da GUI ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Seção de Controle Principal ---
        control_frame = ttk.LabelFrame(main_frame, text="Controle Principal", padding="10")
        control_frame.pack(fill=tk.X, pady=5)

        self.start_stop_button = ttk.Button(control_frame, text="Iniciar Bot", command=self.toggle_bot)
        self.start_stop_button.pack(fill=tk.X, ipady=5)

        self.status_label = ttk.Label(control_frame, text="Status: Parado", foreground="red", font=("Helvetica", 10, "bold"))
        self.status_label.pack(pady=5)

        # --- Seção de Calibração ---
        calib_frame = ttk.LabelFrame(main_frame, text="Calibração", padding="10")
        calib_frame.pack(fill=tk.X, pady=5)

        ttk.Button(calib_frame, text="Calibrar Regiões Principais (Barras, Poções)", command=self.bot.calibrate_regions).pack(fill=tk.X, pady=2)
        ttk.Button(calib_frame, text="Calibrar Área de Coleta (Varredura)", command=self.bot.calibrate_search_region).pack(fill=tk.X, pady=2)

        # --- Seção de Testes e Diagnósticos ---
        test_frame = ttk.LabelFrame(main_frame, text="Testes & Diagnósticos", padding="10")
        test_frame.pack(fill=tk.X, pady=5)

        ttk.Button(test_frame, text="Testar Simulação de Teclas", command=self.bot.test_key_simulation).pack(fill=tk.X, pady=2)
        ttk.Button(test_frame, text="Diagnóstico de Barras", command=self.bot.run_diagnostics).pack(fill=tk.X, pady=2)
        ttk.Button(test_frame, text="Diagnóstico de Poções", command=self.bot.run_potion_diagnostics).pack(fill=tk.X, pady=2)
        ttk.Button(test_frame, text="Testar Fluxo Periódico (F2->F3...)", command=self.bot.test_periodic_flow).pack(fill=tk.X, pady=2)
        ttk.Button(test_frame, text="Testar Fluxo Secundário (F5->F1)", command=self.bot.test_secondary_flow).pack(fill=tk.X, pady=2)
        ttk.Button(test_frame, text="Testar Detecção de Slot Vazio", command=self.bot.test_empty_slot).pack(fill=tk.X, pady=2)

        # --- Seção de Configurações ---
        settings_frame = ttk.LabelFrame(main_frame, text="Configurações", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)

        # Checkbox para varredura de coleta
        self.scan_enabled_var = tk.BooleanVar(value=self.bot.scan_enabled)
        self.scan_enabled_var.trace_add("write", self.update_bot_settings)
        ttk.Checkbutton(settings_frame, text="Ativar Coleta Automática (Varredura)", variable=self.scan_enabled_var).pack(anchor=tk.W)

        # Checkboxes para logs
        self.log_vars = {
            "Debug Mode": tk.BooleanVar(value=self.bot.debug_mode),
            "Logs Verbosos": tk.BooleanVar(value=self.bot.verbose_logs),
            "Logs de Barras": tk.BooleanVar(value=self.bot.show_bar_logs),
            "Logs de Poções": tk.BooleanVar(value=self.bot.show_potion_logs),
            "Logs de Ações": tk.BooleanVar(value=self.bot.show_action_logs),
        }

        for name, var in self.log_vars.items():
            var.trace_add("write", self.update_bot_settings)
            ttk.Checkbutton(settings_frame, text=name, variable=var).pack(anchor=tk.W)

        # --- Seção de Logs ---
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', height=10, bg="black", fg="white")
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # Configura o logging para a GUI
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        
        # Formato customizado para o handler da GUI
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.queue_handler.setFormatter(formatter)
        
        # Adiciona o handler ao logger raiz
        logging.getLogger().addHandler(self.queue_handler)
        
        # Inicia o processo de leitura da fila de logs
        self.root.after(100, self.poll_log_queue)

        # Garante que o bot pare ao fechar a janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def handle_f12_press(self, e=None):
        """Callback para o hotkey F12, atualiza a GUI."""
        on_f12_press(e) # Chama a função original
        if global_vars.stop_all_services:
            self.status_label.config(text="Status: Pausado (F12)", foreground="orange")
        else:
            if self.bot.running:
                self.status_label.config(text="Status: Rodando", foreground="green")
            else:
                self.status_label.config(text="Status: Parado", foreground="red")

    def toggle_bot(self):
        """Inicia ou para o bot."""
        if self.bot.running:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        """Inicia o bot em uma nova thread."""
        self.bot.running = True
        global_vars.stop_all_services = False # Garante que não comece pausado
        
        self.bot_thread = threading.Thread(target=self.bot.start, daemon=True)
        self.bot_thread.start()
        
        self.start_stop_button.config(text="Parar Bot")
        self.status_label.config(text="Status: Rodando", foreground="green")
        logging.info("Interface iniciou o bot.")

    def stop_bot(self):
        """Para o bot."""
        if self.bot.running:
            self.bot.running = False
            global_vars.stop_all_services = True # Sinaliza para todas as threads pararem
            
            self.start_stop_button.config(text="Iniciar Bot")
            self.status_label.config(text="Status: Parado", foreground="red")
            logging.info("Interface solicitou a parada do bot.")

    def update_bot_settings(self, *args):
        """Atualiza as configurações do bot com base nos checkboxes."""
        self.bot.scan_enabled = self.scan_enabled_var.get()
        self.bot.debug_mode = self.log_vars["Debug Mode"].get()
        self.bot.verbose_logs = self.log_vars["Logs Verbosos"].get()
        self.bot.show_bar_logs = self.log_vars["Logs de Barras"].get()
        self.bot.show_potion_logs = self.log_vars["Logs de Poções"].get()
        self.bot.show_action_logs = self.log_vars["Logs de Ações"].get()
        logging.info("Configurações de log atualizadas pela GUI.")

    def poll_log_queue(self):
        """Verifica a fila de logs e atualiza a área de texto."""
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display_log_record(record)
        self.root.after(100, self.poll_log_queue)

    def display_log_record(self, record):
        """Adiciona uma entrada de log à área de texto."""
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, record + '\n')
        self.log_area.configure(state='disabled')
        self.log_area.yview(tk.END) # Auto-scroll

        # Colore a linha de log
        if "WARNING" in record or "CRITICO" in record:
            self.colorize_log("orange")
        elif "ERROR" in record or "FALHA" in record:
            self.colorize_log("red")

    def colorize_log(self, color):
        """Aplica cor à última linha inserida no log."""
        # 'end-2c' (end minus 2 chars) para pegar o início da última linha
        # 'end-1c' (end minus 1 char) para pegar o final da última linha
        self.log_area.tag_add(color, "end-2c linestart", "end-1c")
        self.log_area.tag_config(color, foreground=color)

    def on_closing(self):
        """Ação a ser executada ao fechar a janela."""
        self.stop_bot()
        self.root.destroy()

def main_gui():
    """Função principal para iniciar a GUI."""
    root = tk.Tk()
    app = BotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    # Adiciona um handler de console para ver logs antes da GUI iniciar
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(console_handler)
    
    main_gui()