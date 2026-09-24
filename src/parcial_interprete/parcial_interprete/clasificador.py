import unicodedata


def normalizar(texto):
    """
    Convierte a minusculas y elimina tildes.
    Ejemplo:
    'RÁPIDO' -> 'rapido'
    """

    texto = texto.lower().strip()

    texto = unicodedata.normalize(
        'NFD',
        texto
    )

    texto = ''.join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != 'Mn'
    )

    return texto


def detectar_accion(frase):

    texto = normalizar(frase)

    palabras_recoger = [
        'recoge',
        'recoger',
        'agarra',
        'agarrar',
        'toma',
        'tomar',
        'coge',
    ]

    palabras_depositar = [
        'deposita',
        'depositar',
        'coloca',
        'colocar',
        'pon',
        'poner',
        'lleva',
    ]

    palabras_detener = [
        'deten',
        'detener',
        'para',
        'parar',
        'alto',
        'stop',
    ]

    for palabra in palabras_recoger:
        if palabra in texto:
            return 'recoger'

    for palabra in palabras_depositar:
        if palabra in texto:
            return 'depositar'

    for palabra in palabras_detener:
        if palabra in texto:
            return 'detener'

    return 'desconocida'


def detectar_color(frase):

    texto = normalizar(frase)

    colores = {
        'rojo': [
            'rojo',
            'roja',
        ],

        'verde': [
            'verde',
        ],

        'azul': [
            'azul',
        ],

        'amarillo': [
            'amarillo',
            'amarilla',
        ],
    }

    for color_canonico, variantes in colores.items():

        for variante in variantes:

            if variante in texto:
                return color_canonico

    return 'desconocido'

def detectar_prioridad(frase):

    texto = normalizar(frase)

    palabras_urgentes = [
        'urgente',
        'inmediatamente',
        'ahora mismo',
        'emergencia',
    ]

    palabras_altas = [
        'rapido',
        'rapidamente',
        'prioridad alta',
        'importante',
    ]

    palabras_bajas = [
        'cuando puedas',
        'sin apuro',
        'despacio',
        'prioridad baja',
    ]

    for palabra in palabras_urgentes:
        if palabra in texto:
            return 3

    for palabra in palabras_altas:
        if palabra in texto:
            return 2

    for palabra in palabras_bajas:
        if palabra in texto:
            return 0

    return 1


def detectar_permitido(frase):

    texto = normalizar(frase)

    palabras_prohibidas = [
        'golpea',
        'golpear',
        'lastima',
        'lastimar',
        'ataca',
        'atacar',
    ]

    for palabra in palabras_prohibidas:
        if palabra in texto:
            return False

    return True


def detectar_objeto(frase):

    texto = normalizar(frase)

    # TEMPORAL:
    # cuando conozcamos los 4 objetos reales,
    # cambiaremos esta lista.
    objetos = [
        'cubo',
        'bloque',
        'botella',
        'pelota',
    ]

    for objeto in objetos:
        if objeto in texto:
            return objeto

    return 'desconocido'


def clasificar_local(frase):

    return {
        'accion': detectar_accion(frase),
        'objeto': detectar_objeto(frase),
        'color': detectar_color(frase),
        'prioridad': detectar_prioridad(frase),
        'permitido': detectar_permitido(frase),
    }
