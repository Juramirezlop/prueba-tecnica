PAGE_SIZE = 15

def calcular_total_paginas(total_registros: int, page_size: int = PAGE_SIZE) -> int:
    if total_registros <= 0:
        return 1
    return (total_registros + page_size - 1) // page_size

def rango_paginas(pagina_actual: int, total_paginas: int, delta: int = 2) -> list:
    if total_paginas <= 1:
        return []

    paginas = {1, total_paginas}
    for p in range(pagina_actual - delta, pagina_actual + delta + 1):
        if 1 <= p <= total_paginas:
            paginas.add(p)

    ordenadas = sorted(paginas)
    resultado = []
    anterior = None
    for p in ordenadas:
        if anterior is not None and p - anterior > 1:
            resultado.append(None)
        resultado.append(p)
        anterior = p
    return resultado