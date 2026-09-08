import random
import re
from collections import deque

class MundoWumpus:
    def __init__(self, tamano=4, callback_notificar=None):
        self.tamano = tamano
        self.callback_notificar = callback_notificar
        self.historial_mensajes = []
        
        self.grafo = {}
        self.construir_grafo()
        
        # Posiciones de los elementos
        self.pos_jugador = (0, 0)
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

    def notificar(self, mensaje):
        """Registra un mensaje y lo envía al callback de la GUI o a print() en terminal."""
        self.historial_mensajes.append(mensaje)
        if self.callback_notificar:
            self.callback_notificar(mensaje)
        else:
            print(mensaje)

    def construir_grafo(self):
        """Construye un grafo no dirigido representando una cuadrícula."""
        for x in range(self.tamano):
            for y in range(self.tamano):
                vecinos = []
                # Conectar con las habitaciones adyacentes (Aristas no dirigidas)
                if x > 0: vecinos.append((x - 1, y)) # Izquierda
                if x < self.tamano - 1: vecinos.append((x + 1, y)) # Derecha
                if y > 0: vecinos.append((x, y - 1)) # Abajo
                if y < self.tamano - 1: vecinos.append((x, y + 1)) # Arriba
                
                self.grafo[(x, y)] = vecinos

    def _existe_camino_seguro(self, inicio, destino):
        """Verifica mediante BFS si existe un camino desde inicio hasta destino sin pisar pozos."""
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
        """Calcula el camino más corto del Wumpus al jugador evitando pozos mediante BFS."""
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
        """Devuelve la distancia en pasos de grafo del Wumpus al jugador."""
        camino = self._obtener_camino_wumpus()
        if camino:
            return len(camino) - 1
        return abs(self.pos_wumpus[0] - self.pos_jugador[0]) + abs(self.pos_wumpus[1] - self.pos_jugador[1])

    def inicializar_elementos(self):
        """
        Coloca el Wumpus, el oro, los pozos, los murciélagos y la zona de derrumbe.
        Garantiza mediante BFS que el mapa sea siempre solucionable (existe camino sin pozos hacia el oro).
        """
        while True:
            habitaciones = list(self.grafo.keys())
            habitaciones.remove((0, 0)) # El inicio siempre es seguro
            
            self.pos_wumpus = random.choice(habitaciones)
            habitaciones.remove(self.pos_wumpus)
            
            self.pos_oro = random.choice(habitaciones)
            habitaciones.remove(self.pos_oro)
            
            # Murciélagos gigantes (1 habitación)
            pos_bat = random.choice(habitaciones)
            self.pos_murcielagos = [pos_bat]
            habitaciones.remove(pos_bat)
            
            # Zona inestable propensa a desprendimiento de rocas (1 habitación)
            self.pos_derrumbe = random.choice(habitaciones)
            habitaciones.remove(self.pos_derrumbe)
            
            # Colocar pozos con 20% de probabilidad en habitaciones restantes
            self.pos_pozos = [hab for hab in habitaciones if random.random() < 0.2]
            
            # Validar que exista al menos un camino seguro hasta el oro
            if self._existe_camino_seguro((0, 0), self.pos_oro):
                break

    def percibir(self):
        """Devuelve las percepciones en el nodo actual del jugador."""
        percepciones = []
        vecinos = self.grafo.get(self.pos_jugador, [])
        
        # Percibir hedor
        if self.wumpus_vivo and (self.pos_wumpus in vecinos or self.pos_jugador == self.pos_wumpus):
            percepciones.append("Hedor")
            
        # Percibir brisa
        if any(pozo in vecinos for pozo in self.pos_pozos):
            percepciones.append("Brisa")
            
        # Percibir aleteo (murciélagos gigantes)
        if any(bat in vecinos for bat in self.pos_murcielagos):
            percepciones.append("Aleteo")
            
        # Percibir crujido (zona inestable / rocas sueltas)
        if self.pos_derrumbe in vecinos and not self.derrumbe_ocurrido:
            percepciones.append("Crujido")
            
        # Percibir brillo
        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            percepciones.append("Brillo")
            
        return percepciones

    def mover_wumpus_aleatorio(self):
        """Desplaza al Wumpus a una habitación adyacente libre de pozos."""
        if not self.wumpus_vivo:
            return
            
        candidatos = [n for n in self.grafo.get(self.pos_wumpus, []) if n not in self.pos_pozos]
        if candidatos:
            self.pos_wumpus = random.choice(candidatos)
            self.notificar("\n¡Escuchas pasos pesados y un bufido feroz en la penumbra! El Wumpus ha cambiado de habitación.")
            if self.pos_wumpus == self.pos_jugador:
                self.notificar("¡¡EL WUMPUS HA ENTRADO EN TU HABITACIÓN!!")
                self.verificar_estado()

    def cazar_jugador(self):
        """
        En modo cacería, el Wumpus calcula la ruta más corta hacia el jugador y avanza un paso.
        """
        if not self.wumpus_vivo or not self.modo_caceria:
            return

        camino = self._obtener_camino_wumpus()
        if camino and len(camino) >= 2:
            siguiente_paso = camino[1]
            self.pos_wumpus = siguiente_paso
            distancia_restante = len(camino) - 2
            
            if self.pos_wumpus == self.pos_jugador:
                self.notificar("\n¡¡EL WUMPUS IRRUMPE VELOZMENTE EN TU HABITACIÓN CON LAS FAUCES ABIERTAS!!")
                self.verificar_estado()
            else:
                sufijo = "es" if distancia_restante > 1 else ""
                self.notificar(f"\n¡¡PASOS PESADOS Y RASPADO DE GARRAS!! El Wumpus avanza hacia ti (está a {distancia_restante} habitación{sufijo} de distancia).")
        else:
            self.notificar("\n¡Escuchas un rugido frustrado a lo lejos! El Wumpus intenta buscar una ruta hacia ti.")
            self.mover_wumpus_aleatorio()

    def activar_derrumbe(self):
        """
        Provoca un desprendimiento de rocas en la habitación inestable.
        Bloquea un túnel adyacente eliminando la arista del grafo sin romper la solubilidad.
        """
        if self.derrumbe_ocurrido:
            return
            
        self.derrumbe_ocurrido = True
        self.notificar("\n¡¡CRRAAAACK... BOOOM!! ¡Se produce un violento desprendimiento de rocas del techo!")
        
        pos = self.pos_jugador
        vecinos = list(self.grafo.get(pos, []))
        random.shuffle(vecinos)
        
        tunel_bloqueado = False
        for v in vecinos:
            self.grafo[pos].remove(v)
            self.grafo[v].remove(pos)
            
            camino_inicio = self._existe_camino_seguro(self.pos_jugador, (0, 0))
            camino_oro = True if self.tiene_oro else self._existe_camino_seguro(self.pos_jugador, self.pos_oro)
            
            if camino_inicio and camino_oro:
                tunel_bloqueado = True
                self.bloqueos.add((min(pos, v), max(pos, v)))
                self.notificar(f"¡Rocas gigantes han sellado el paso entre {pos} y {v}! Ese túnel ya no existe.")
                break
            else:
                self.grafo[pos].append(v)
                self.grafo[v].append(pos)
                
        if not tunel_bloqueado:
            self.notificar("¡Grandes rocas se desploman sobre el suelo rozándote! Logras esquivarlas a tiempo.")

    def mover(self, nueva_pos):
        """Mueve al jugador a un nodo adyacente usando las aristas del grafo."""
        if nueva_pos in self.grafo.get(self.pos_jugador, []):
            self.pos_jugador = nueva_pos
            self.habitaciones_visitadas.add(nueva_pos)
            self.notificar(f"\nTe has movido a {self.pos_jugador}")
            
            # Comprobar desprendimiento de rocas
            if self.pos_jugador == self.pos_derrumbe and not self.derrumbe_ocurrido:
                self.activar_derrumbe()
                
            self.verificar_estado()
            
            # Comprobar murciélagos gigantes si sigue vivo
            if self.vivo:
                self.verificar_murcielagos()
                
            # Avance de la cacería del Wumpus si el jugador sigue con vida
            if self.vivo and self.modo_caceria and self.wumpus_vivo:
                self.turnos_caceria += 1
                if self.turnos_caceria % 2 == 0:
                    self.cazar_jugador()
                else:
                    dist = self._distancia_al_jugador()
                    sufijo = "es" if dist > 1 else ""
                    self.notificar(f"\n¡Sientes un bufido cavernoso y el suelo vibrar! El Wumpus te acecha a {dist} habitación{sufijo}...")
        else:
            self.notificar(f"\n¡No hay camino hacia {nueva_pos}! Habitaciones conectadas: {self.grafo.get(self.pos_jugador, [])}")

    def verificar_murcielagos(self):
        """Comprueba si el jugador entró a la habitación de los murciélagos gigantes."""
        if self.pos_jugador in self.pos_murcielagos:
            self.notificar("\n¡¡SWOOOOSH!! ¡Una bandada de murciélagos gigantes te atrapa con sus garras y te alza en vuelo!")
            posibles = [h for h in self.grafo.keys() if h != self.pos_jugador]
            destino = random.choice(posibles)
            self.notificar(f"¡Te dejan caer en la habitación {destino} y huyen hacia la oscuridad!")
            self.pos_jugador = destino
            self.habitaciones_visitadas.add(destino)
            
            libres = [h for h in posibles if h != destino and h != (0, 0)]
            self.pos_murcielagos = [random.choice(libres)]
            
            self.verificar_estado()

    def verificar_estado(self):
        """Comprueba si el jugador cayó en un pozo o fue comido por el Wumpus."""
        if self.pos_jugador in self.pos_pozos:
            self.notificar("\n¡AAAAAAHHHH! Caíste en un pozo infinito. Fin del juego.")
            self.vivo = False
        elif self.pos_jugador == self.pos_wumpus and self.wumpus_vivo:
            self.notificar("\n¡CRUNCH! El Wumpus te ha devorado. Fin del juego.")
            self.vivo = False

    def lanzar_piedra(self, objetivo):
        """
        Lanza una piedra hacia una habitación adyacente para tantear su contenido.
        Si el Wumpus está en cacería, el ruido puede distraerlo temporalmente.
        """
        if self.piedras <= 0:
            self.notificar("\nYa no te quedan piedras en la bolsa.")
            return

        if objetivo not in self.grafo.get(self.pos_jugador, []):
            self.notificar(f"\nSolo puedes lanzar piedras a habitaciones directamente conectadas: {self.grafo.get(self.pos_jugador, [])}")
            return

        self.piedras -= 1
        self.notificar(f"\n¡Lanzas una piedra hacia {objetivo}! Escuchas atentamente...")

        if objetivo in self.pos_pozos:
            self.notificar("  > ... ¡SPLASH! Escuchas el eco lejano de la piedra cayendo al abismo de un pozo.")
        elif objetivo == self.pos_wumpus and self.wumpus_vivo:
            self.notificar("  > ... ¡¡ROAAAR!! La piedra golpeó al Wumpus y ruge enfurecido.")
            self.mover_wumpus_aleatorio()
        elif objetivo in self.pos_murcielagos:
            self.notificar("  > ... ¡¡CHIIIRP!! Escuchas un chillido agudo y un frenético aleteo. ¡Hay murciélagos gigantes!")
        elif objetivo == self.pos_derrumbe and not self.derrumbe_ocurrido:
            self.notificar("  > ... ¡CRAC! La piedra impacta el techo y cae polvo y guijarros. ¡El techo es inestable!")
        else:
            self.notificar("  > ... ¡Clac-clac! La piedra rueda por el suelo de roca sin novedad. Parece seguro.")

        # Distracción en cacería
        if self.modo_caceria and self.wumpus_vivo:
            self.notificar("  > ¡El eco confunde al Wumpus por un momento, retrasando su avance!")
            self.turnos_caceria = max(0, self.turnos_caceria - 1)

        self.notificar(f"Te quedan {self.piedras} piedras.")

    def agarrar(self):
        """Intenta agarrar el oro en la posición actual. Activa el modo cacería del Wumpus si está vivo."""
        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            self.tiene_oro = True
            self.notificar("\n¡Has agarrado el Oro!")
            
            if self.wumpus_vivo:
                self.modo_caceria = True
                self.notificar("\n" + "!" * 58)
                self.notificar(" ¡¡¡ROAAAR ENSORDECEDOR RESONANDO EN TODA LA CUEVA!!! ")
                self.notificar(" El Wumpus ha olido el brillo del oro y ENTRA EN CACERÍA. ")
                self.notificar(" ¡Te persigue activamente! Huye a (0, 0) antes de ser cazado. ")
                self.notificar("!" * 58)
            else:
                self.notificar("Ahora regresa a (0, 0) para escapar y ganar.")
        elif self.tiene_oro:
            self.notificar("\nYa tienes el oro en tu mochila.")
        else:
            self.notificar("\nNo hay nada que agarrar aquí.")

    def disparar(self, objetivo):
        """
        Dispara una flecha en línea recta hacia la dirección del objetivo.
        No descuenta la flecha si la dirección es inválida.
        Si mata al Wumpus, detiene la cacería.
        """
        if self.flechas <= 0:
            self.notificar("\nYa no te quedan flechas.")
            return

        if objetivo == self.pos_jugador:
            self.notificar("\nNo puedes disparar a tu propia habitación.")
            return

        x_orig, y_orig = self.pos_jugador
        x_dest, y_dest = objetivo

        dx = x_dest - x_orig
        dy = y_dest - y_orig

        if dx != 0 and dy != 0:
            self.notificar("\nNo puedes disparar en diagonal. Dispara en línea recta (arriba, abajo, izquierda o derecha).")
            return

        paso_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        paso_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

        self.flechas -= 1
        self.notificar(f"\n¡Disparas la flecha hacia ({paso_x:+d}, {paso_y:+d})! La flecha silba velozmente en la oscuridad...")

        cur_x, cur_y = x_orig + paso_x, y_orig + paso_y
        impacto = False

        while 0 <= cur_x < self.tamano and 0 <= cur_y < self.tamano:
            if (cur_x, cur_y) == self.pos_wumpus and self.wumpus_vivo:
                self.wumpus_vivo = False
                impacto = True
                self.notificar(f"¡¡¡GRITO ESCALOFRIANTE en ({cur_x}, {cur_y})!!! Has matado al Wumpus.")
                if self.modo_caceria:
                    self.modo_caceria = False
                    self.notificar("¡La cueva queda en silencio sepulcral! La cacería ha terminado, estás a salvo.")
                break
            cur_x += paso_x
            cur_y += paso_y

        if not impacto:
            self.notificar("¡Clac! La flecha se estrelló contra una pared lejana. No acertaste.")
            if self.wumpus_vivo and not self.modo_caceria:
                self.mover_wumpus_aleatorio()

    def mostrar_mapa(self, revelar_todo=False):
        """Muestra una representación gráfica en consola del mundo 4x4."""
        titulo = "--- MAPA DE LA CUEVA (REVELADO) ---" if revelar_todo else "--- MAPA EXPLORADO ---"
        print(f"\n{titulo}")
        print("   " + " ".join([f"  {x}  " for x in range(self.tamano)]))
        print("  +" + "------+" * self.tamano)
        
        for y in range(self.tamano - 1, -1, -1):
            fila_str = f"{y} |"
            for x in range(self.tamano):
                pos = (x, y)
                if pos == self.pos_jugador:
                    celda = "J+O" if self.tiene_oro else " J "
                elif revelar_todo:
                    if pos == self.pos_wumpus:
                        celda = " W " if self.wumpus_vivo else "MW "
                    elif pos == self.pos_oro:
                        celda = " O "
                    elif pos in self.pos_pozos:
                        celda = " P "
                    elif pos in self.pos_murcielagos:
                        celda = " M "
                    elif pos == self.pos_derrumbe:
                        celda = " R "
                    else:
                        celda = " . "
                else:
                    if pos in self.habitaciones_visitadas:
                        celda = " . "
                    else:
                        celda = " ? "
                fila_str += f" {celda} |"
            print(fila_str)
            print("  +" + "------+" * self.tamano)
            
        if not revelar_todo:
            leyenda = "Leyenda: [J]=Jugador, [J+O]=Jugador con Oro, [.]=Visitada, [?]=Desconocida"
        else:
            leyenda = "Leyenda: [J]=Jugador, [W]=Wumpus Vivo, [MW]=Wumpus Muerto, [O]=Oro, [P]=Pozo, [M]=Murcielagos, [R]=Rocas/Derrumbe, [.]=Vacio"
        print(f"  {leyenda}\n")


def parse_comando(entrada):
    """Interpreta la entrada del usuario de manera flexible y tolerante a espacios y comas."""
    texto = entrada.strip().lower()
    if not texto:
        return None, None

    numeros = re.findall(r'-?\d+', texto)
    partes = texto.split()
    cmd = partes[0]

    if cmd in ["salir", "exit", "quit", "q"]:
        return "salir", None
    if cmd in ["ayuda", "help", "?"]:
        return "ayuda", None
    if cmd in ["mapa", "ver", "m"]:
        return "mapa", None
    if cmd in ["agarrar", "coger", "tomar", "grab", "oro"]:
        return "agarrar", None

    if cmd in ["mover", "ir", "mov"]:
        if len(numeros) >= 2:
            return "mover", (int(numeros[0]), int(numeros[1]))
        return "mover_invalido", None

    if cmd in ["disparar", "flecha", "disp", "shoot"]:
        if len(numeros) >= 2:
            return "disparar", (int(numeros[0]), int(numeros[1]))
        return "disparar_invalido", None

    if cmd in ["lanzar", "piedra", "tirar", "rock", "p", "l"]:
        if len(numeros) >= 2:
            return "lanzar", (int(numeros[0]), int(numeros[1]))
        return "lanzar_invalido", None

    # Si el usuario solo escribió las coordenadas directamente (ej: '1,0' o '1 0')
    if len(numeros) == 2 and len(partes) <= 2:
        return "mover", (int(numeros[0]), int(numeros[1]))

    return "desconocido", texto


def imprimir_ayuda():
    """Muestra la lista de comandos disponibles."""
    print("\n--- COMANDOS DISPONIBLES ---")
    print("  mover X,Y    (o 'X,Y')      : Desplazarte a una habitación adyacente.")
    print("  disparar X,Y (o 'flecha X Y): Disparar la flecha en línea recta hacia esa dirección.")
    print("  lanzar X,Y   (o 'piedra X Y): Lanzar una piedra a una habitación adyacente para tantear o distraer.")
    print("  agarrar                     : Recoger el oro (¡activará la cacería del Wumpus!).")
    print("  mapa                        : Mostrar el mapa de las habitaciones exploradas.")
    print("  ayuda                       : Mostrar este mensaje de ayuda.")
    print("  salir                       : Abandonar el juego.")
    print("----------------------------\n")


# === BUCLE DE JUEGO CLI ===
def jugar_cli():
    juego = MundoWumpus()
    print("=========================================")
    print("   BIENVENIDO AL MUNDO DEL WUMPUS (v3)   ")
    print("=========================================")
    print("Objetivo: Encuentra el oro, cógelo y regresa a salvo a (0, 0).")
    print("¡CUIDADO! Al tomar el oro, el Wumpus comenzará a cazarte activamente.")
    print("Escribe 'ayuda' en cualquier momento para ver los comandos.\n")
    
    juego.mostrar_mapa()

    while juego.vivo:
        # Comprobar victoria al inicio del turno en (0,0) con el oro
        if juego.pos_jugador == (0, 0) and juego.tiene_oro:
            print("\n*********************************************************")
            print(" ¡¡¡FELICIDADES!!! Has escapado de la cueva con el oro. ")
            print("                  ¡¡¡HAS GANADO!!!                       ")
            print("*********************************************************")
            juego.mostrar_mapa(revelar_todo=True)
            break

        print(f"Estás en la habitación: {juego.pos_jugador}")
        percepciones = juego.percibir()
        
        if percepciones:
            print(f"  > Percibes: {', '.join(percepciones)}")
        else:
            print("  > No percibes nada inusual.")
            
        print(f"  > Habitaciones conectadas: {juego.grafo.get(juego.pos_jugador, [])}")
        estado_caceria = " | [¡¡ALERTA: WUMPUS EN CACERÍA!!]" if juego.modo_caceria and juego.wumpus_vivo else ""
        print(f"  > Flechas: {juego.flechas} | Piedras: {juego.piedras} | Oro: {'Sí' if juego.tiene_oro else 'No'}{estado_caceria}")
        
        entrada = input("\n¿Qué deseas hacer?: ")
        accion, args = parse_comando(entrada)
        
        if accion is None:
            continue
            
        if accion == "mover":
            juego.mover(args)
            if juego.vivo:
                juego.mostrar_mapa()
        elif accion == "mover_invalido":
            print("\n[!] Formato incorrecto. Especifica las coordenadas. Ejemplos: 'mover 1,0' o 'mover 1 0'.")
        elif accion == "disparar":
            juego.disparar(args)
        elif accion == "disparar_invalido":
            print("\n[!] Formato incorrecto. Especifica hacia dónde disparar. Ejemplo: 'disparar 1,0'.")
        elif accion == "lanzar":
            juego.lanzar_piedra(args)
        elif accion == "lanzar_invalido":
            print("\n[!] Formato incorrecto. Especifica a qué habitación lanzar la piedra. Ejemplo: 'lanzar 1,0'.")
        elif accion == "agarrar":
            juego.agarrar()
        elif accion == "mapa":
            juego.mostrar_mapa()
        elif accion == "ayuda":
            imprimir_ayuda()
        elif accion == "salir":
            print("\nHas abandonado la cueva cobardemente.")
            juego.mostrar_mapa(revelar_todo=True)
            break
        else:
            print(f"\n[!] Comando '{args}' no reconocido. Escribe 'ayuda' para ver las opciones disponibles.")

    if not juego.vivo:
        print("\nHas muerto en la oscuridad de la cueva.")
        juego.mostrar_mapa(revelar_todo=True)


if __name__ == "__main__":
    import sys
    if "--gui" in sys.argv:
        from gui import iniciar_gui
        iniciar_gui()
    else:
        jugar_cli()