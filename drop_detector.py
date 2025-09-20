import cv2
import numpy as np
import os

# Caminho do template GOLD_drop.bmp
TEMPLATE_PATH = os.path.join(
    'images', 'drops', 'drops', 'GOLD_drop.bmp'
)

def load_gold_template():
    """Carrega o template de gold drop."""
    template = cv2.imread(TEMPLATE_PATH, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template não encontrado: {TEMPLATE_PATH}")
    return template

def find_gold_drops(frame, threshold=0.82):
    """
    Detecta drops de gold na imagem da tela usando template matching.
    Retorna uma lista de coordenadas centrais dos matches.
    """
    template = load_gold_template()
    h, w = template.shape[:2]
    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)
    points = []
    for pt in zip(*loc[::-1]):
        center = (pt[0] + w // 2, pt[1] + h // 2)
        points.append(center)
    # Remover sobreposições próximas (non-maximum suppression simplificado)
    filtered = []
    for c in points:
        if all(np.linalg.norm(np.array(c) - np.array(f)) > min(w, h)//2 for f in filtered):
            filtered.append(c)
    return filtered
