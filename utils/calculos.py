import math

def calcular_pacotes(quantidade_telas, tipo_pao):
    if tipo_pao == 'G3':
        return math.ceil((quantidade_telas * 30) / 180)
    elif tipo_pao == 'G4':
        return math.ceil((quantidade_telas * 30) / 166)
    elif tipo_pao == 'F3':
        return math.ceil((quantidade_telas * 40) / 180)
    elif tipo_pao == 'F4' or tipo_pao == 'F4':
        return math.ceil((quantidade_telas * 40) / 166)
    return 0