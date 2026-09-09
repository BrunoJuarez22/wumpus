import random
import re
from collections import deque

def imprimir_mecanicas():
    print("""
======================================================================
                 NOVEDADES VS. WUMPUS CLASICO (1972)
======================================================================
1. Modo Cacería del Wumpus:
   * Original: El Wumpus era estático y solo se movía al fallar flechas.
   * Nuevo: ¡Al coger el Oro, el Wumpus despierta e inicia cacería!
     Te persigue activamente por el mapa cada 2 turnos para devorarte.
     Debes huir a tiempo de regreso hasta la Cueva 1 para escapar.

2. Lanzamiento de Piedras (3 en bolsa):
   * Original: Solo contabas con una flecha para disparar a ciegas.
   * Nuevo: Arroja piedras a cuevas contiguas ('lanzar X' o 'p X') para tantear riesgos:
       - Eco de chapoteo (Splash): Pozo mortal sin fondo.
       - Rugido furioso: Golpeas al Wumpus, huye y retrasa la cacería.
       - Chillidos y aleteo: Nido de murciélagos gigantes.
       - Crujido de piedra: Techo inestable a punto de desplomarse.

3. Partida Siempre Ganable:
   * Original: Los pozos al azar podían bloquear la cueva inicial.
   * Nuevo: El mapa siempre se genera con un camino seguro
     para encontrar el oro y regresar a la salida.
======================================================================
""")

class MundoWumpus:
    def __init__(self, tamano=4):
        self.tamano = tamano
        self.total_cuevas = tamano * tamano
        self.grafo = {}
        self.construir_grafo()
        
        self.pos_jugador = 1
        self.pos_wumpus = None
        self.pos_oro = None
        self.pos_pozos = []
        self.pos_murcielagos = []
        self.pos_derrumbe = None
        self.derrumbe_ocurrido = False
        self.bloqueos = set()
        
        self.vivo = True
        self.tiene_oro = False
        self.wumpus_vivo = True
        self.modo_caceria = False
        self.turnos_caceria = 0
        self.flechas = 1
        self.piedras = 3
        self.habitaciones_visitadas = {self.pos_jugador}
        
        self.inicializar_elementos()

    def _cueva_a_xy(self, c):
        return (c - 1) % self.tamano, (c - 1) // self.tamano

    def _xy_a_cueva(self, x, y):
        return y * self.tamano + x + 1

    def construir_grafo(self):
        self.grafo.clear()
        for c in range(1, self.total_cuevas + 1):
            x, y = self._cueva_a_xy(c)
            vecinos = []
            if x > 0: vecinos.append(self._xy_a_cueva(x - 1, y))
            if x < self.tamano - 1: vecinos.append(self._xy_a_cueva(x + 1, y))
            if y > 0: vecinos.append(self._xy_a_cueva(x, y - 1))
            if y < self.tamano - 1: vecinos.append(self._xy_a_cueva(x, y + 1))
            self.grafo[c] = sorted(vecinos)

    def _existe_camino_seguro(self, inicio, destino):
        cola = deque([inicio])
        visitados = {inicio}
        while cola:
            actual = cola.popleft()
            if actual == destino:
                return True
            for vecino in self.grafo.get(actual, []):
                if vecino not in self.pos_pozos and vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)
        return False

    def _obtener_camino_wumpus(self):
        cola = deque([[self.pos_wumpus]])
        visitados = {self.pos_wumpus}
        while cola:
            camino = cola.popleft()
            actual = camino[-1]
            if actual == self.pos_jugador:
                return camino
            for vecino in self.grafo.get(actual, []):
                if vecino not in self.pos_pozos and vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(camino + [vecino])
        return None

    def _distancia_al_jugador(self):
        camino = self._obtener_camino_wumpus()
        if camino:
            return len(camino) - 1
        x1, y1 = self._cueva_a_xy(self.pos_wumpus)
        x2, y2 = self._cueva_a_xy(self.pos_jugador)
        return abs(x1 - x2) + abs(y1 - y2)

    def inicializar_elementos(self):
        while True:
            cuevas = list(range(2, self.total_cuevas + 1))
            
            self.pos_wumpus = random.choice(cuevas)
            cuevas.remove(self.pos_wumpus)
            
            self.pos_oro = random.choice(cuevas)
            cuevas.remove(self.pos_oro)
            
            pos_bat = random.choice(cuevas)
            self.pos_murcielagos = [pos_bat]
            cuevas.remove(pos_bat)
            
            self.pos_derrumbe = random.choice(cuevas)
            cuevas.remove(self.pos_derrumbe)
            
            self.pos_pozos = [c for c in cuevas if random.random() < 0.2]
            
            if self._existe_camino_seguro(1, self.pos_oro):
                break

    def percibir(self):
        percepciones = []
        vecinos = self.grafo.get(self.pos_jugador, [])
        
        if any(v == self.pos_wumpus for v in vecinos) and self.wumpus_vivo:
            percepciones.append("Hedor")
        if any(v in self.pos_pozos for v in vecinos):
            percepciones.append("Brisa")
        if any(v in self.pos_murcielagos for v in vecinos):
            percepciones.append("Aleteo")
        if any(v == self.pos_derrumbe for v in vecinos) and not self.derrumbe_ocurrido:
            percepciones.append("Crujido")
        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            percepciones.append("Brillo")
            
        return percepciones

    def mover_wumpus_aleatorio(self):
        vecinos = [c for c in self.grafo.get(self.pos_wumpus, []) if c not in self.pos_pozos]
        if vecinos:
            self.pos_wumpus = random.choice(vecinos)
            if self.pos_wumpus == self.pos_jugador:
                print("\n¡¡EL WUMPUS IRRUMPE EN TU CUEVA EN SU HUIDA!!")
                self.verificar_estado()

    def cazar_jugador(self):
        camino = self._obtener_camino_wumpus()
        if camino and len(camino) > 1:
            siguiente_cueva = camino[1]
            self.pos_wumpus = siguiente_cueva
            distancia = len(camino) - 2
            
            if self.pos_wumpus == self.pos_jugador:
                print("\n¡¡EL WUMPUS IRRUMPE VELOZMENTE EN TU CUEVA CON LAS FAUCES ABIERTAS!!")
                self.verificar_estado()
            else:
                sufijo = "s" if distancia > 1 else ""
                print(f"\n¡¡PASOS PESADOS Y RASPADO DE GARRAS!! El Wumpus avanza hacia ti (está a {distancia} cueva{sufijo} de distancia).")
        else:
            print("\n¡Escuchas un rugido frustrado a lo lejos! El Wumpus intenta buscar una ruta hacia ti.")
            self.mover_wumpus_aleatorio()

    def activar_derrumbe(self):
        if self.derrumbe_ocurrido:
            return
            
        self.derrumbe_ocurrido = True
        print("\n¡¡CRRAAAACK... BOOOM!! ¡Se produce un violento desprendimiento de rocas del techo!")
        
        pos = self.pos_jugador
        vecinos = list(self.grafo.get(pos, []))
        random.shuffle(vecinos)
        
        tunel_bloqueado = False
        for v in vecinos:
            self.grafo[pos].remove(v)
            self.grafo[v].remove(pos)
            
            camino_inicio = self._existe_camino_seguro(self.pos_jugador, 1)
            camino_oro = True if self.tiene_oro else self._existe_camino_seguro(self.pos_jugador, self.pos_oro)
            
            if camino_inicio and camino_oro:
                tunel_bloqueado = True
                self.bloqueos.add((min(pos, v), max(pos, v)))
                print(f"¡Rocas gigantes han sellado el paso entre Cueva {pos} y Cueva {v}! Ese túnel ya no existe.")
                break
            else:
                self.grafo[pos].append(v)
                self.grafo[v].append(pos)
                
        if not tunel_bloqueado:
            print("¡Grandes rocas se desploman sobre el suelo rozándote! Logras esquivarlas a tiempo.")

    def mover(self, nueva_pos):
        if nueva_pos in self.grafo.get(self.pos_jugador, []):
            self.pos_jugador = nueva_pos
            self.habitaciones_visitadas.add(nueva_pos)
            print(f"\nTe has movido a la Cueva {self.pos_jugador}.")
            
            if self.pos_jugador == self.pos_derrumbe and not self.derrumbe_ocurrido:
                self.activar_derrumbe()
                
            self.verificar_estado()
            
            if self.vivo:
                self.verificar_murcielagos()
                
            if self.vivo and self.modo_caceria and self.wumpus_vivo:
                self.turnos_caceria += 1
                if self.turnos_caceria % 2 == 0:
                    self.cazar_jugador()
                else:
                    dist = self._distancia_al_jugador()
                    sufijo = "s" if dist > 1 else ""
                    print(f"\n¡Sientes un bufido cavernoso y el suelo vibrar! El Wumpus te acecha a {dist} cueva{sufijo}...")
        else:
            vecinos = self.grafo.get(self.pos_jugador, [])
            print(f"\n¡No hay túnel directo hacia la Cueva {nueva_pos}! Cuevas conectadas: {vecinos}")

    def verificar_murcielagos(self):
        if self.pos_jugador in self.pos_murcielagos:
            print("\n¡¡SWOOOOSH!! ¡Una bandada de murciélagos gigantes te atrapa con sus garras y te alza en vuelo!")
            posibles = [c for c in range(1, self.total_cuevas + 1) if c != self.pos_jugador]
            destino = random.choice(posibles)
            print(f"¡Te dejan caer en la Cueva {destino} y huyen hacia la oscuridad!")
            self.pos_jugador = destino
            self.habitaciones_visitadas.add(destino)
            
            libres = [c for c in posibles if c != destino and c != 1]
            self.pos_murcielagos = [random.choice(libres)]
            
            self.verificar_estado()

    def verificar_estado(self):
        if self.pos_jugador in self.pos_pozos:
            print("\n¡AAAAAAHHHH! Caíste en un pozo infinito. Fin del juego.")
            self.vivo = False
        elif self.pos_jugador == self.pos_wumpus and self.wumpus_vivo:
            print("\n¡CRUNCH! El Wumpus te ha devorado. Fin del juego.")
            self.vivo = False

    def lanzar_piedra(self, objetivo):
        if self.piedras <= 0:
            print("\nYa no te quedan piedras en la bolsa.")
            return

        if objetivo not in self.grafo.get(self.pos_jugador, []):
            print(f"\nSolo puedes lanzar piedras a cuevas directamente conectadas: {self.grafo.get(self.pos_jugador, [])}")
            return

        self.piedras -= 1
        print(f"\n¡Lanzas una piedra hacia la Cueva {objetivo}! Escuchas atentamente...")

        if objetivo in self.pos_pozos:
            print("  > ... ¡SPLASH! Escuchas el eco lejano de la piedra cayendo al abismo de un pozo.")
        elif objetivo == self.pos_wumpus and self.wumpus_vivo:
            print("  > ... ¡¡ROAAAR!! La piedra golpeó al Wumpus y ruge enfurecido.")
            self.mover_wumpus_aleatorio()
        elif objetivo in self.pos_murcielagos:
            print("  > ... ¡¡CHIIIRP!! Escuchas un chillido agudo y un frenético aleteo. ¡Hay murciélagos gigantes!")
        elif objetivo == self.pos_derrumbe and not self.derrumbe_ocurrido:
            print("  > ... ¡CRAC! La piedra impacta el techo y cae polvo y guijarros. ¡El techo es inestable!")
        else:
            print("  > ... ¡Clac-clac! La piedra rueda por el suelo de roca sin novedad. Parece seguro.")

    def agarrar(self):
        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            self.tiene_oro = True
            print("\n¡¡HAS COGIDO EL COFRE DE ORO!! ¡¡FANTÁSTICO!!")
            print("¡Ahora debes regresar a salvo hasta la Cueva 1 para escapar!")
            
            if self.wumpus_vivo:
                self.modo_caceria = True
                print("\n¡¡ROOOAAAR!! ¡¡EL WUMPUS HA OLIDO EL ORO Y SE HA DESPERTADO!!")
                print("¡MODO CACERÍA ACTIVADO! El Wumpus avanzará hacia ti cada 2 turnos. ¡¡CORRE!!")
        elif self.tiene_oro:
            print("\nYa tienes el oro en tu mochila.")
        else:
            print("\nNo hay nada de valor que agarrar en esta cueva.")

    def disparar(self, objetivo):
        if self.flechas <= 0:
            print("\nYa no te quedan flechas.")
            return

        vecinos = self.grafo.get(self.pos_jugador, [])
        if objetivo not in vecinos:
            print(f"\nSolo puedes disparar a través de un túnel conectado: {vecinos}")
            return

        x_orig, y_orig = self._cueva_a_xy(self.pos_jugador)
        x_dest, y_dest = self._cueva_a_xy(objetivo)

        dx = x_dest - x_orig
        dy = y_dest - y_orig

        paso_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        paso_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

        self.flechas -= 1
        print(f"\n¡Disparas la flecha hacia la Cueva {objetivo}! La flecha silba velozmente en la oscuridad...")

        cur_x, cur_y = x_orig + paso_x, y_orig + paso_y
        impacto = False

        while 0 <= cur_x < self.tamano and 0 <= cur_y < self.tamano:
            cur_cueva = self._xy_a_cueva(cur_x, cur_y)
            if cur_cueva == self.pos_wumpus and self.wumpus_vivo:
                self.wumpus_vivo = False
                impacto = True
                print(f"¡¡¡GRITO ESCALOFRIANTE en la Cueva {cur_cueva}!!! Has matado al Wumpus.")
                if self.modo_caceria:
                    self.modo_caceria = False
                    print("¡La cueva queda en silencio sepulcral! La cacería ha terminado, estás a salvo.")
                break
            cur_x += paso_x
            cur_y += paso_y

        if not impacto:
            print("¡Clac! La flecha se estrelló contra una pared lejana. No acertaste.")
            if self.wumpus_vivo and not self.modo_caceria:
                self.mover_wumpus_aleatorio()

    def mostrar_mapa(self, revelar_todo=False):
        titulo = "--- MAPA DE CUEVAS (REVELADO) ---" if revelar_todo else "--- MAPA DE CUEVAS EXPLORADAS ---"
        print(f"\n{titulo}")
        
        for y in range(self.tamano - 1, -1, -1):
            fila_nodos = "  "
            for x in range(self.tamano):
                c = self._xy_a_cueva(x, y)
                if c == self.pos_jugador:
                    tag = "JO" if self.tiene_oro else "J"
                elif revelar_todo:
                    if c == self.pos_wumpus:
                        tag = "W" if self.wumpus_vivo else "MW"
                    elif c == self.pos_oro:
                        tag = "O"
                    elif c in self.pos_pozos:
                        tag = "P"
                    elif c in self.pos_murcielagos:
                        tag = "M"
                    elif c == self.pos_derrumbe:
                        tag = "R"
                    elif c in self.habitaciones_visitadas:
                        tag = "."
                    else:
                        tag = "."
                else:
                    if c in self.habitaciones_visitadas:
                        tag = "."
                    else:
                        tag = "?"
                
                fila_nodos += f"[{c:>2}:{tag:<2}]"
                
                if x < self.tamano - 1:
                    vecino_este = self._xy_a_cueva(x + 1, y)
                    arista = (min(c, vecino_este), max(c, vecino_este))
                    if vecino_este in self.grafo.get(c, []):
                        fila_nodos += " --- "
                    elif arista in self.bloqueos:
                        fila_nodos += " -x- "
                    else:
                        fila_nodos += "     "
            print(fila_nodos)
            
            if y > 0:
                fila_vert = "  "
                for x in range(self.tamano):
                    c = self._xy_a_cueva(x, y)
                    vecino_sur = self._xy_a_cueva(x, y - 1)
                    arista = (min(c, vecino_sur), max(c, vecino_sur))
                    if vecino_sur in self.grafo.get(c, []):
                        fila_vert += "  |   "
                    elif arista in self.bloqueos:
                        fila_vert += "  x   "
                    else:
                        fila_vert += "      "
                    
                    if x < self.tamano - 1:
                        fila_vert += "     "
                print(fila_vert)
                
        print("\nLeyenda:")
        if not revelar_todo:
            print("  Cuevas: [N:?] = Desconocida, [N:J ] = Tu posición actual, [N:.] = Visitada y vacía")
            print("  Túneles: (--- / |) = Túnel abierto, (-x- / x) = Túnel bloqueado por derrumbe\n")
        else:
            print("  Cuevas: [N:J] = Jugador, [N:W] = Wumpus, [N:MW] = Wumpus Muerto, [N:O] = Oro")
            print("          [N:P] = Pozo, [N:M] = Murciélagos, [N:R] = Roca inestable, [N:.] = Vacía")
            print("  Túneles: (--- / |) = Túnel abierto, (-x- / x) = Túnel bloqueado por derrumbe\n")

    def describir_cueva(self):
        print("\n" + "=" * 56)
        print(f"  ESTÁS EN LA CUEVA {self.pos_jugador}")
        print("=" * 56)
        
        percepciones = self.percibir()
        if percepciones:
            print("[Percepciones sensoriales en esta cueva]:")
            for p in percepciones:
                if p == "Hedor":
                    print("  * ¡Hedor nauseabundo! Un olor fétido y penetrante impregna el aire (el Wumpus está cerca).")
                elif p == "Brisa":
                    print("  * ¡Brisa helada! Sientes una corriente de aire frío ascender de las profundidades (hay un pozo mortal cerca).")
                elif p == "Aleteo":
                    print("  * ¡Aleteo inquietante! Escuchas chasquidos y murmullo de alas en la penumbra (murciélagos gigantes).")
                elif p == "Crujido":
                    print("  * ¡Crujido de roca! Pequeños guijarros caen y el techo vibra con tensión (zona inestable).")
                elif p == "Brillo":
                    print("  * ¡¡BRILLO DORADO!! ¡Un cofre repleto de oro resplandece en el suelo de esta cueva! (Usa 'agarrar').")
        else:
            print("[Percepciones]:")
            print("  * Silencio absoluto. No percibes peligros contiguos.")

        vecinos = self.grafo.get(self.pos_jugador, [])
        lista_vecinos = ", ".join(f"Cueva {v}" for v in vecinos)
        print(f"\n[Túneles disponibles]: Puedes moverte a: {lista_vecinos}")

        estado_caceria = "\n  [¡¡ALERTA MÁXIMA!! ¡El Wumpus está despierto y te está cazando!]" if self.modo_caceria and self.wumpus_vivo else ""
        print(f"[Inventario]: Flechas: {self.flechas} | Piedras: {self.piedras} | Oro: {'Sí' if self.tiene_oro else 'No'}{estado_caceria}")
        print("=" * 56)


def parse_comando(entrada):
    texto = entrada.strip().lower()
    if not texto:
        return None, None

    partes = texto.split()
    cmd = partes[0]

    if cmd in ["salir", "exit", "quit", "q"]:
        return "salir", None
    if cmd in ["ayuda", "help", "?", "h"]:
        return "ayuda", None
    if cmd in ["mapa", "ver", "m"]:
        return "mapa", None
    if cmd in ["mecanicas", "mecanica", "novedades", "reglas"]:
        return "mecanicas", None
    if cmd in ["agarrar", "coger", "tomar", "grab", "oro", "g", "a"]:
        return "agarrar", None

    if texto.isdigit():
        return "mover", int(texto)

    numeros = re.findall(r'\d+', texto)
    num = int(numeros[0]) if numeros else None

    if cmd in ["mover", "ir", "mov"]:
        if num is not None:
            return "mover", num
        return "mover_invalido", None

    if cmd in ["disparar", "flecha", "disp", "shoot", "f", "d"]:
        if num is not None:
            return "disparar", num
        return "disparar_invalido", None

    if cmd in ["lanzar", "piedra", "tirar", "rock", "p", "l"]:
        if num is not None:
            return "lanzar", num
        return "lanzar_invalido", None

    return "desconocido", texto


def imprimir_ayuda():
    print("\n--- COMANDOS DISPONIBLES ---")
    print("  mover N     (o solo 'N')     : Desplazarte a la Cueva N conectada (ej: 'mover 2' o '2').")
    print("  disparar N  (o 'f N', 'd N') : Disparar una flecha en línea recta hacia la Cueva N.")
    print("  lanzar N    (o 'p N', 'l N') : Lanzar una piedra a la Cueva N para tantear peligros.")
    print("  agarrar     (o 'g', 'oro')   : Coger el cofre de oro (¡despierta la cacería del Wumpus!).")
    print("  mapa        (o 'm')          : Mostrar el mapa con la numeración de cuevas y niebla.")
    print("  mecanicas   (o 'novedades')  : Ver las nuevas mecánicas respecto al Wumpus de 1972.")
    print("  ayuda       (o '?')          : Mostrar esta lista de comandos.")
    print("  salir       (o 'q')          : Abandonar la partida.")
    print("----------------------------\n")


if __name__ == "__main__":
    juego = MundoWumpus()
    print("=========================================================")
    print("         BIENVENIDO AL MUNDO DEL WUMPUS (v3)             ")
    print("=========================================================")
    print("Objetivo: Explora las cuevas, encuentra el oro, cógelo y")
    print("regresa a salvo hasta la Cueva 1 para escapar con vida.")
    print("Escribe 'ayuda' para ver los comandos o 'mecanicas' para")
    print("ver las diferencias con el juego clásico original de 1972.")

    imprimir_mecanicas()
    juego.mostrar_mapa()

    while juego.vivo:
        if juego.pos_jugador == 1 and juego.tiene_oro:
            print("\n*********************************************************")
            print(" ¡¡¡FELICIDADES!!! Has escapado de la cueva con el oro. ")
            print("                  ¡¡¡HAS GANADO LA PARTIDA!!!            ")
            print("*********************************************************")
            juego.mostrar_mapa(revelar_todo=True)
            break

        juego.describir_cueva()

        entrada = input("\n¿Qué deseas hacer? (ej: 'mover 2' o simplemente '2'): ")
        accion, args = parse_comando(entrada)

        if accion is None:
            continue

        if accion == "mover":
            juego.mover(args)
            if juego.vivo:
                juego.mostrar_mapa()
        elif accion == "mover_invalido":
            print("\n[!] Especifica a qué cueva moverte. Ejemplos: 'mover 2' o simplemente '2'.")
        elif accion == "disparar":
            juego.disparar(args)
        elif accion == "disparar_invalido":
            print("\n[!] Especifica hacia qué cueva disparar. Ejemplo: 'disparar 2' o 'f 2'.")
        elif accion == "lanzar":
            juego.lanzar_piedra(args)
        elif accion == "lanzar_invalido":
            print("\n[!] Especifica a qué cueva lanzar la piedra. Ejemplo: 'lanzar 2' o 'p 2'.")
        elif accion == "agarrar":
            juego.agarrar()
        elif accion == "mapa":
            juego.mostrar_mapa()
        elif accion == "mecanicas":
            imprimir_mecanicas()
        elif accion == "ayuda":
            imprimir_ayuda()
        elif accion == "salir":
            print("\nHas abandonado la cueva cobardemente.")
            juego.mostrar_mapa(revelar_todo=True)
            break
        else:
            print(f"\n[!] Comando '{args}' no reconocido. Escribe el número de cueva, 'ayuda' o 'mecanicas'.")

    if not juego.vivo:
        print("\nHas muerto en la oscuridad de la cueva.")
        juego.mostrar_mapa(revelar_todo=True)
