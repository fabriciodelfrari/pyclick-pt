# 🎮 Automação de Jogo - Monitor de Barras e Poções

Sistema completo de automação para jogos online que monitora barras de status (HP, Mana, Energy), gerencia poções automaticamente e executa serviços em background.

## 📋 Funcionalidades

### 🔋 Monitoramento de Barras
- **HP (Vermelho)**: Monitora barra de vida (limite: 40%)
- **Mana (Azul)**: Monitora barra de mana (limite: 30%)
- **Energy (Verde)**: Monitora barra de energia/stamina (limite: 30%)
- **Sistema de Prioridade**: HP tem prioridade máxima
- **Ações Urgentes**: HP crítico dispara ações especiais
- **Análise Avançada**: Combina 4 métodos de detecção

### 🧪 Sistema de Poções
- **Detecção Automática**: Identifica quando poções acabam
- **Reposição Inteligente**: Abre inventário e repõe automaticamente
- **Suporte a 3 Tipos**: Poções de HP, Mana e Energy
- **Fallback**: Comandos Shift+1/2/3 se reposição falhar

### 🤖 Serviços em Background
- **Cliques Aleatórios**: 2 cliques direitos a cada 30-45 segundos
- **Fluxo Periódico**: Sequência F2→cliques→F3→cliques→F1 a cada 10 minutos
- **Thread Separada**: Não interfere no monitoramento principal

### ⚙️ Calibração Manual
- **Interface Visual**: Calibração interativa com OpenCV
- **Controles Simples**: WASD para mover, +/- para redimensionar
- **Múltiplas Regiões**: Barras, poções e inventário
- **Backup Automático**: Salva coordenadas automaticamente

### 🔍 Diagnósticos
- **Análise Detalhada**: Diagnóstico completo de barras e poções
- **Imagens de Debug**: Salva capturas para análise
- **Teste Real**: Testa reposição com ações reais no jogo
- **Logs Configuráveis**: Sistema de logs opcional

## 🚀 Instalação

1. **Clone o repositório**:
```bash
git clone <repository_url>
cd pyclick
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Execute o programa**:
```bash
python game_automation.py
```

## 🎯 Como Usar

### 1. Primeira Execução
1. Execute `python game_automation.py`
2. Escolha opção **2** (Calibrar regiões)
3. Ajuste as posições das barras e poções
4. Pressione **SPACE** para salvar
5. Pressione **Q** para sair

### 2. Calibração Manual
**Controles da Calibração:**
- `1-3`: Selecionar barras (HP/Mana/Energy)
- `4-6`: Selecionar poções (Red/Green/Blue)
- `7`: Selecionar inventário
- `WASD`: Mover região selecionada
- `+/-`: Redimensionar largura
- `Shift +/-`: Redimensionar altura
- `R`: Resetar região
- `SPACE`: Salvar coordenadas
- `Q/ESC`: Sair

### 3. Configuração de Logs
- **Opção 8** no menu principal
- Configure quais logs exibir
- **Modo Silencioso**: Desativa maioria dos logs
- **Modo Completo**: Ativa todos os logs

### 4. Diagnósticos
- **Opção 5**: Diagnóstico de barras
- **Opção 6**: Diagnóstico de poções
- **Opção 7**: Teste real de slot vazio

## 🔧 Configuração

### Coordenadas Padrão
```python
# Barras (ajustar conforme sua resolução)
self.bar_regions = {
    'hp': (600, 920, 25, 120),      # x, y, width, height
    'mana': (870, 990, 25, 50),     
    'energy': (570, 997, 15, 45),   
}

# Poções
self.potion_regions = {
    'red_potion': (650, 1000, 30, 30),    # HP potion
    'green_potion': (690, 1000, 30, 30),  # Energy potion
    'blue_potion': (730, 1000, 30, 30),   # Mana potion
}

# Inventário
self.inventory_region = (768, 324, 672, 432)
```

### Teclas de Ação
- **Tecla 1**: Poção de HP (quando HP < 40%)
- **Tecla 2**: Poção de Energy (quando Energy < 30%)
- **Tecla 3**: Poção de Mana (quando Mana < 30%)
- **Shift+1**: Recarregar poção de HP do inventário
- **Shift+2**: Recarregar poção de Energy do inventário
- **Shift+3**: Recarregar poção de Mana do inventário

## 🛡️ Segurança

- **FAILSAFE**: PyAutoGUI com proteção de canto
- **Controle de Mouse**: Restaura posição original após ações
- **Cooldowns**: Evita spam de ações
- **Error Handling**: Tratamento de erros robusto

## 📊 Algoritmo de Detecção

### Barras de Status
Combina 4 métodos para máxima precisão:
1. **Análise BGR**: Intensidade de cor por canal
2. **Análise HSV**: Detecção de faixa de cor específica
3. **Análise de Gradiente**: Mudanças de intensidade
4. **Análise de Preenchimento**: Preenchimento vertical

### Detecção de Poções Vazias
Usa critério 2-de-3:
1. **Intensidade Baixa**: < 80/255
2. **Poucas Bordas**: < 15% densidade
3. **Pouca Cor Específica**: < 10% da cor esperada

## 🔍 Resolução de Problemas

### Barras Não Detectadas
1. Execute o **diagnóstico de barras** (opção 5)
2. Verifique as imagens salvas `debug_bar_*.png`
3. Recalibre as regiões manualmente
4. Ajuste as coordenadas no código

### Poções Não Funcionando
1. Execute o **diagnóstico de poções** (opção 6)
2. Teste com **slot vazio real** (opção 7)
3. Verifique se o inventário abre com 'V'
4. Calibre a região do inventário

### Performance
- Reduza logs para melhor performance
- Use "Modo Silencioso" em produção
- Ajuste `time.sleep()` no loop principal se necessário

## 📁 Arquivos Gerados

- `debug_bar_*.png`: Imagens das barras capturadas
- `debug_potion_*.png`: Imagens das poções capturadas
- `diagnostic_*.png`: Imagens de diagnóstico detalhado
- `calibration_backup.txt`: Backup das coordenadas
- `test_empty_*.png`: Imagens do teste de slot vazio

## ⚠️ Avisos Importantes

1. **Use apenas em jogos permitidos**: Verifique ToS do jogo
2. **Teste em ambiente controlado**: Sempre teste antes de usar
3. **Supervisione o funcionamento**: Não deixe totalmente sem supervisão
4. **Backup das configurações**: Salve suas calibrações

## 🤝 Contribuições

- Reportar bugs através de Issues
- Sugerir melhorias
- Contribuir com código via Pull Requests

## 📝 Licença

Este projeto é para fins educacionais. Use por sua conta e risco.

---

**Desenvolvido por**: Fabricio Costa  
**Data**: 18/09/2025  
**Versão**: 1.0.0
