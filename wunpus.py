import os
import random
import re
from collections import deque

def limpiar_consola():
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        print("\033[H\033[2J", end="")

def imprimir_novedades():
    print("""
======================================================================
                              NOVEDADES
======================================================================
1. Modo Cacería del Wumpus:
   * Al tomar el oro, el Wumpus despierta e inicia cacería activa cada 2 turnos.
   * Debes huir a tiempo de regreso hasta la Cueva 1 para escapar.

2. Lanzamiento de Piedras (4 en bolsa):
   * Arroja piedras ('lanzar X' o 'p X') para tantear riesgos:
     Splash (pozo), Rugido (Wumpus), Aleteo (murciélagos), Crujido (derrumbe).

3. Cebo de Carne (Equipo Inicial):
   * Lanza carne ('cebo X' o 'c X') para distraer al Wumpus por 2 turnos.

4. Brújula de Exploración (Objeto en Cueva):
   * Oculta en una cueva. Al tomarla ('tomar' o 't'), te orienta hacia el objetivo.

5. Partida Siempre Ganable y Mapa de 25 Cuevas:
   * Cuadrícula de 5x5 con camino seguro garantizado hacia el oro y la salida.

6. Sistema de Puntuación y Eficiencia:
   * Puntos por explorar, cazar y recursos. Bonus por menor cantidad de pasos.
======================================================================
""")

class MundoWumpus:
    def __init__(self, tamano=5):
        self.tamano = tamano
        self.total_cuevas = tamano * tamano
        self.grafo = {}
        self.construir_grafo()
        
        self.pos_jugador = 1
        self.pos_wumpus = None
        self.pos_oro = None
        self.pos_brujula = None
        self.pos_pozos = []
        self.pos_murcielagos = []
        self.pos_derrumbe = None
        self.derrumbe_ocurrido = False
        self.bloqueos = set()
        
        self.vivo = True
        self.tiene_oro = False
        self.tiene_brujula = False
        self.wumpus_vivo = True
        self.modo_caceria = False
        self.turnos_caceria = 0
        self.distraccion_wumpus = 0
        self.cebo_distrajo_wumpus = False
        self.flechas = 1
        self.piedras = 4 if self.total_cuevas >= 25 else 3
        self.cebos = 1
        self.habitaciones_visitadas = {self.pos_jugador}
        
        self.movimientos_totales = 0
        self.ecos_detectados = 0
        self.causa_muerte = ""
        self.mensajes = ["Nueva expedición. Encuentra el oro, tómalo y regresa a Cueva 1."]
        
        self.inicializar_elementos()

    def notificar(self, mensaje):
        self.mensajes.append(mensaje)

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

    def _calcular_camino_optimo_oro(self):
        cola = deque([[1]])
        visitados = {1}
        while cola:
            camino = cola.popleft()
            actual = camino[-1]
            if actual == self.pos_oro:
                return camino
            for vecino in self.grafo.get(actual, []):
                if vecino not in self.pos_pozos and vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(camino + [vecino])
        return None

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
            
            num_bats = 2 if self.total_cuevas >= 25 else 1
            self.pos_murcielagos = []
            for _ in range(num_bats):
                bat = random.choice(cuevas)
                self.pos_murcielagos.append(bat)
                cuevas.remove(bat)
            
            self.pos_derrumbe = random.choice(cuevas)
            cuevas.remove(self.pos_derrumbe)

            self.pos_brujula = random.choice(cuevas)
            cuevas.remove(self.pos_brujula)
            
            self.pos_pozos = [c for c in cuevas if random.random() < 0.2]
            
            if self._existe_camino_seguro(1, self.pos_oro):
                break

    def percibir(self):
        percepciones = []
        vecinos = self.grafo.get(self.pos_jugador, [])
        
        if any(v == self.pos_wumpus for v in vecinos) and self.wumpus_vivo:
            percepciones.append("Hedor (Wumpus cerca)")
        if any(v in self.pos_pozos for v in vecinos):
            percepciones.append("Brisa (Pozo cerca)")
        if any(v in self.pos_murcielagos for v in vecinos):
            percepciones.append("Aleteo (Murciélagos cerca)")
        if any(v == self.pos_derrumbe for v in vecinos) and not self.derrumbe_ocurrido:
            percepciones.append("Crujido (Roca inestable)")
        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            percepciones.append("Brillo (¡Oro aquí!)")
        if self.pos_jugador == self.pos_brujula and not self.tiene_brujula:
            percepciones.append("Destello metálico (¡Brújula aquí!)")
            
        return percepciones

    def mover_wumpus_aleatorio(self):
        vecinos = [c for c in self.grafo.get(self.pos_wumpus, []) if c not in self.pos_pozos]
        if vecinos:
            self.pos_wumpus = random.choice(vecinos)
            if self.pos_wumpus == self.pos_jugador:
                self.notificar("El Wumpus entró a tu cueva mientras huía.")
                self.verificar_estado()

    def cazar_jugador(self):
        camino = self._obtener_camino_wumpus()
        if camino and len(camino) > 1:
            paso_siguiente = camino[1]
            self.pos_wumpus = paso_siguiente
            
            dist = len(camino) - 2
            if dist == 0:
                self.notificar("El Wumpus ha entrado a tu cueva.")
                self.causa_muerte = "El Wumpus te alcanzó y te devoró."
                self.vivo = False
            else:
                sufijo = "s" if dist > 1 else ""
                self.notificar(f"El suelo tiembla... El Wumpus avanzó. Está a {dist} cueva{sufijo} de ti.")
        else:
            self.mover_wumpus_aleatorio()

    def activar_derrumbe(self):
        if self.derrumbe_ocurrido:
            return
            
        vecinos = list(self.grafo.get(self.pos_jugador, []))
        random.shuffle(vecinos)
        
        bloqueado = False
        for v in vecinos:
            self.grafo[self.pos_jugador].remove(v)
            self.grafo[v].remove(self.pos_jugador)
            
            camino_ok = self._existe_camino_seguro(self.pos_jugador, 1)
            if not self.tiene_oro and camino_ok:
                camino_ok = self._existe_camino_seguro(self.pos_jugador, self.pos_oro)
                
            if camino_ok:
                arista = (min(self.pos_jugador, v), max(self.pos_jugador, v))
                self.bloqueos.add(arista)
                self.derrumbe_ocurrido = True
                bloqueado = True
                self.notificar(f"Derrumbe: túnel entre Cueva {self.pos_jugador} y Cueva {v} sellado.")
                break
            else:
                self.grafo[self.pos_jugador].append(v)
                self.grafo[v].append(self.pos_jugador)
                self.grafo[self.pos_jugador].sort()
                self.grafo[v].sort()
                
        if not bloqueado:
            self.derrumbe_ocurrido = True
            self.notificar("Un temblor sacude la cueva, pero los túneles resisten.")

    def mover(self, nueva_pos):
        vecinos = self.grafo.get(self.pos_jugador, [])
        if nueva_pos in vecinos:
            self.pos_jugador = nueva_pos
            self.habitaciones_visitadas.add(nueva_pos)
            self.movimientos_totales += 1
            self.notificar(f"Te has desplazado a la Cueva {nueva_pos}.")
            
            if self.pos_jugador == self.pos_derrumbe and not self.derrumbe_ocurrido:
                self.activar_derrumbe()
                
            self.verificar_estado()
            
            if self.vivo:
                self.verificar_murcielagos()
                
            if self.vivo and self.modo_caceria and self.wumpus_vivo:
                if self.distraccion_wumpus > 0:
                    self.distraccion_wumpus -= 1
                    self.notificar(f"Wumpus distraído comiendo cebo ({self.distraccion_wumpus} turno(s) restantes).")
                else:
                    self.turnos_caceria += 1
                    if self.turnos_caceria % 2 == 0:
                        self.cazar_jugador()
                    else:
                        dist = self._distancia_al_jugador()
                        sufijo = "s" if dist > 1 else ""
                        self.notificar(f"El Wumpus te acecha a {dist} cueva{sufijo} de distancia...")
        else:
            vecinos = self.grafo.get(self.pos_jugador, [])
            self.notificar(f"Sin túnel directo a Cueva {nueva_pos}. Conectadas: {vecinos}")

    def verificar_murcielagos(self):
        if self.pos_jugador in self.pos_murcielagos:
            self.notificar("¡Murciélagos gigantes te atrapan y te llevan por el aire!")
            posibles = [c for c in range(1, self.total_cuevas + 1) if c != self.pos_jugador]
            destino = random.choice(posibles)
            self.notificar(f"Te dejan caer en la Cueva {destino}.")
            bat_actual = self.pos_jugador
            self.pos_jugador = destino
            self.habitaciones_visitadas.add(destino)
            
            libres = [c for c in posibles if c != destino and c != 1 and c not in self.pos_murcielagos]
            if libres:
                self.pos_murcielagos.remove(bat_actual)
                self.pos_murcielagos.append(random.choice(libres))
            
            self.verificar_estado()

    def verificar_estado(self):
        if self.pos_jugador in self.pos_pozos:
            self.notificar("Caíste en un pozo sin fondo. Fin del juego.")
            self.causa_muerte = "Caíste en un pozo."
            self.vivo = False
        elif self.pos_jugador == self.pos_wumpus and self.wumpus_vivo:
            self.notificar("El Wumpus te ha devorado. Fin del juego.")
            self.causa_muerte = "El Wumpus te ha devorado."
            self.vivo = False

    def lanzar_piedra(self, objetivo):
        if self.piedras <= 0:
            self.notificar("Ya no te quedan piedras en la bolsa.")
            return

        if objetivo not in self.grafo.get(self.pos_jugador, []):
            self.notificar(f"Solo puedes lanzar piedras a cuevas conectadas: {self.grafo.get(self.pos_jugador, [])}")
            return

        self.piedras -= 1
        self.notificar(f"Lanzas una piedra hacia la Cueva {objetivo}...")

        if objetivo in self.pos_pozos:
            self.notificar("  > Splash. Eco de piedra cayendo al fondo de un pozo.")
            self.ecos_detectados += 1
        elif objetivo == self.pos_wumpus and self.wumpus_vivo:
            self.notificar("  > Rugido. Golpeaste al Wumpus y ruge; huye a otra cueva.")
            self.ecos_detectados += 1
            self.mover_wumpus_aleatorio()
        elif objetivo in self.pos_murcielagos:
            self.notificar("  > Chillidos y aleteo. Hay murciélagos en esa cueva.")
            self.ecos_detectados += 1
        elif objetivo == self.pos_derrumbe and not self.derrumbe_ocurrido:
            self.notificar("  > Crujido y polvo. Techo inestable a punto de caer.")
            self.ecos_detectados += 1
        else:
            self.notificar("  > La piedra rueda por el suelo de roca sin novedad. Parece seguro.")

    def lanzar_cebo(self, objetivo):
        if self.cebos <= 0:
            self.notificar("Ya no te quedan cebos en el morral.")
            return

        vecinos = self.grafo.get(self.pos_jugador, [])
        if objetivo not in vecinos:
            self.notificar(f"Solo puedes lanzar el cebo a una cueva conectada: {vecinos}")
            return

        self.cebos -= 1
        self.notificar(f"Lanzas carne hacia la Cueva {objetivo}...")

        if objetivo == self.pos_wumpus and self.wumpus_vivo:
            self.distraccion_wumpus = 2
            self.cebo_distrajo_wumpus = True
            self.notificar("  > El Wumpus devora la carne y se distrae por 2 turnos.")
        elif self.modo_caceria and self.wumpus_vivo:
            self.distraccion_wumpus = 2
            self.cebo_distrajo_wumpus = True
            if objetivo not in self.pos_pozos:
                self.pos_wumpus = objetivo
            self.notificar("  > El Wumpus huele la carne, salta a esa cueva y se distrae 2 turnos.")
        else:
            self.notificar("  > El cebo queda en el suelo de la cueva.")

    def consultar_brujula(self, silencioso=False):
        if not self.tiene_brujula:
            if not silencioso:
                self.notificar("No tienes ninguna brújula en tu inventario.")
            return None

        if not self.tiene_oro:
            obj_cueva = self.pos_oro
            nombre_meta = "el cofre de oro"
        else:
            obj_cueva = 1
            nombre_meta = "la salida (Cueva 1)"

        if self.pos_jugador == obj_cueva:
            msg = f"La aguja gira: ¡{nombre_meta} está aquí!"
        else:
            xj, yj = self._cueva_a_xy(self.pos_jugador)
            xo, yo = self._cueva_a_xy(obj_cueva)
            dy = yo - yj
            dx = xo - xj

            if dy > 0 and dx > 0: rumbo = "Noreste"
            elif dy > 0 and dx < 0: rumbo = "Noroeste"
            elif dy < 0 and dx > 0: rumbo = "Sureste"
            elif dy < 0 and dx < 0: rumbo = "Suroeste"
            elif dy > 0: rumbo = "Norte"
            elif dy < 0: rumbo = "Sur"
            elif dx > 0: rumbo = "Este"
            else: rumbo = "Oeste"
            msg = f"Apunta al {rumbo} (hacia {nombre_meta})."

        if not silencioso:
            self.notificar(f"[Brújula]: {msg}")
        return msg

    def tomar(self):
        algo_tomado = False

        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            self.tiene_oro = True
            algo_tomado = True
            self.notificar("¡Has tomado el cofre de oro (+1000 pts)! Regresa a Cueva 1 para escapar.")
            if self.tiene_brujula:
                self.notificar("(La brújula ahora apunta de vuelta a Cueva 1)")
            
            if self.wumpus_vivo:
                self.modo_caceria = True
                self.notificar("¡El Wumpus despertó por el olor a oro! Modo cacería activado.")

        if self.pos_jugador == self.pos_brujula and not self.tiene_brujula:
            self.tiene_brujula = True
            algo_tomado = True
            self.notificar("¡Has tomado la brújula (+300 pts)! Te orienta hacia el objetivo.")

        if not algo_tomado:
            if self.tiene_oro and self.pos_jugador == self.pos_oro:
                self.notificar("Ya tienes el oro en tu mochila.")
            elif self.tiene_brujula and self.pos_jugador == self.pos_brujula:
                self.notificar("Ya tomaste la brújula de esta cueva.")
            else:
                self.notificar("No hay nada que tomar en esta cueva.")

    def disparar(self, objetivo):
        if self.flechas <= 0:
            self.notificar("Ya no te quedan flechas.")
            return

        vecinos = self.grafo.get(self.pos_jugador, [])
        if objetivo not in vecinos:
            self.notificar(f"Solo puedes disparar a través de un túnel conectado: {vecinos}")
            return

        self.flechas -= 1
        self.notificar(f"Disparas la flecha hacia la Cueva {objetivo}.")

        xj, yj = self._cueva_a_xy(self.pos_jugador)
        xo, yo = self._cueva_a_xy(objetivo)
        paso_x = xo - xj
        paso_y = yo - yj

        cur_x, cur_y = xo, yo
        impacto = False

        while 0 <= cur_x < self.tamano and 0 <= cur_y < self.tamano:
            cur_cueva = self._xy_a_cueva(cur_x, cur_y)
            if cur_cueva == self.pos_wumpus and self.wumpus_vivo:
                self.wumpus_vivo = False
                impacto = True
                self.notificar(f"¡Has matado al Wumpus en la Cueva {cur_cueva} (+1000 pts)!")
                if self.modo_caceria:
                    self.modo_caceria = False
                    self.notificar("La cueva queda en silencio. La cacería ha terminado.")
                break
            cur_x += paso_x
            cur_y += paso_y

        if not impacto:
            self.notificar("La flecha chocó contra la roca. Has fallado.")
            if self.wumpus_vivo and not self.modo_caceria:
                self.mover_wumpus_aleatorio()

    def mostrar_mapa(self, revelar_todo=False):
        for y in range(self.tamano - 1, -1, -1):
            fila_nodos = "  "
            for x in range(self.tamano):
                c = self._xy_a_cueva(x, y)
                if c == self.pos_jugador:
                    tag = "JO" if self.tiene_oro else "J "
                elif revelar_todo:
                    if c == self.pos_wumpus: tag = "W " if self.wumpus_vivo else "MW"
                    elif c == self.pos_oro: tag = "O "
                    elif c == self.pos_brujula and not self.tiene_brujula: tag = "B "
                    elif c in self.pos_pozos: tag = "P "
                    elif c in self.pos_murcielagos: tag = "M "
                    elif c == self.pos_derrumbe: tag = "R "
                    else: tag = ". "
                else:
                    tag = ". " if c in self.habitaciones_visitadas else "? "
                
                fila_nodos += f"[{c:>2}:{tag}]"
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

    def describir_cueva(self):
        percepciones = self.percibir()
        p_txt = ", ".join(percepciones) if percepciones else "Silencio (sin peligros)"
        print(f"ESTÁS EN CUEVA {self.pos_jugador} | {p_txt}")

        if self.tiene_brujula:
            lectura = self.consultar_brujula(silencioso=True)
            print(f"[Brújula]: {lectura}")

        vecinos = self.grafo.get(self.pos_jugador, [])
        lista_vecinos = ", ".join(f"Cueva {v}" for v in vecinos)
        ej_v = vecinos[0] if vecinos else 2
        print(f"[Túneles]: {lista_vecinos} (ej: escribe '{ej_v}' o 'mover {ej_v}')")

        if self.modo_caceria and self.wumpus_vivo:
            if self.distraccion_wumpus > 0:
                print(f"[Cacería]: Wumpus comiendo cebo ({self.distraccion_wumpus} turno(s) restantes).")
            elif self.cebos > 0:
                print("[Cacería]: ¡Wumpus buscándote! Usa 'cebo N' para distraerlo o huye a Cueva 1.")
            else:
                print("[Cacería]: ¡Wumpus buscándote! Regresa a Cueva 1 para escapar.")

        brujula_txt = "Sí" if self.tiene_brujula else "No"
        print(f"[Inventario]: Flechas: {self.flechas} | Piedras: {self.piedras} | Cebos: {self.cebos} | Brújula: {brujula_txt} | Oro: {'Sí' if self.tiene_oro else 'No'}")

    def calcular_puntuacion(self):
        puntos_cuevas = len(self.habitaciones_visitadas) * 50
        puntos_oro = 1000 if self.tiene_oro else 0
        puntos_brujula = 300 if self.tiene_brujula else 0
        puntos_wumpus = 1000 if not self.wumpus_vivo else 0
        puntos_ecos = self.ecos_detectados * 100
        puntos_flecha = 200 if self.flechas > 0 else 0
        puntos_piedras = self.piedras * 50
        puntos_cebo_usado = 150 if self.cebo_distrajo_wumpus else 0
        puntos_cebo_guardado = self.cebos * 100
        puntos_escape = 2000 if (self.pos_jugador == 1 and self.tiene_oro and self.vivo) else 0

        subtotal_base = (
            puntos_cuevas + puntos_oro + puntos_brujula + puntos_wumpus +
            puntos_ecos + puntos_flecha + puntos_piedras + puntos_cebo_usado +
            puntos_cebo_guardado + puntos_escape
        )

        camino_optimo = self._calcular_camino_optimo_oro()
        movs_minimos = (len(camino_optimo) - 1) * 2 if camino_optimo else 8

        if self.tiene_oro and self.movimientos_totales > 0:
            ratio = min(1.0, movs_minimos / self.movimientos_totales)
            multiplicador = round(1.0 + 1.5 * ratio, 2) if (self.pos_jugador == 1 and self.vivo) else round(1.0 + 0.5 * ratio, 2)
        else:
            multiplicador = 1.00
            ratio = 0.0

        puntos_totales = int(subtotal_base * multiplicador)

        return {
            "puntos_cuevas": puntos_cuevas,
            "cuevas_visitadas": len(self.habitaciones_visitadas),
            "puntos_oro": puntos_oro,
            "puntos_brujula": puntos_brujula,
            "puntos_wumpus": puntos_wumpus,
            "puntos_ecos": puntos_ecos,
            "ecos_detectados": self.ecos_detectados,
            "puntos_flecha": puntos_flecha,
            "puntos_piedras": puntos_piedras,
            "puntos_cebo_usado": puntos_cebo_usado,
            "puntos_cebo_guardado": puntos_cebo_guardado,
            "puntos_escape": puntos_escape,
            "subtotal_base": subtotal_base,
            "movs_minimos": movs_minimos,
            "movs_jugador": self.movimientos_totales,
            "ratio": ratio,
            "multiplicador": multiplicador,
            "puntos_totales": puntos_totales
        }

    def imprimir_resumen_puntuacion(self):
        stats = self.calcular_puntuacion()
        print("\n" + "=" * 64)
        tit = "RESUMEN DE PUNTUACIÓN - VICTORIA" if (self.pos_jugador == 1 and self.tiene_oro and self.vivo) else "RESUMEN DE PUNTUACIÓN"
        print(f"                 {tit}")
        print("=" * 64)

        if not self.vivo: causa = self.causa_muerte
        elif self.pos_jugador == 1 and self.tiene_oro: causa = "Regresaste con el oro a la Cueva 1."
        else: causa = "Saliste de la cueva."
        print(f"Causa del desenlace: {causa}")

        print("\nDesglose de Puntos:")
        print(f"  * Cuevas exploradas ({stats['cuevas_visitadas']}/{self.total_cuevas}):           +{stats['puntos_cuevas']:>5} pts")
        if stats['puntos_oro'] > 0: print(f"  * Cofre de oro tomado:                      +{stats['puntos_oro']:>5} pts")
        if stats['puntos_brujula'] > 0: print(f"  * Brújula recuperada:                       +{stats['puntos_brujula']:>5} pts")
        if stats['puntos_wumpus'] > 0: print(f"  * Wumpus derrotado:                         +{stats['puntos_wumpus']:>5} pts")
        if stats['ecos_detectados'] > 0: print(f"  * Pistas con piedras ({stats['ecos_detectados']}):                   +{stats['puntos_ecos']:>5} pts")
        if stats['puntos_cebo_usado'] > 0: print(f"  * Cebo usado con éxito:                     +{stats['puntos_cebo_usado']:>5} pts")
        if stats['puntos_flecha'] > 0: print(f"  * Flecha conservada:                        +{stats['puntos_flecha']:>5} pts")
        if stats['puntos_piedras'] > 0: print(f"  * Piedras conservadas ({self.piedras}):                  +{stats['puntos_piedras']:>5} pts")
        if stats['puntos_cebo_guardado'] > 0: print(f"  * Cebo conservado ({self.cebos}):                       +{stats['puntos_cebo_guardado']:>5} pts")
        if stats['puntos_escape'] > 0: print(f"  * Bonificación de escape:                  +{stats['puntos_escape']:>5} pts")
        print("-" * 64)
        print(f"Subtotal Base:                                {stats['subtotal_base']:>6} pts")
        if self.tiene_oro:
            print(f"Eficiencia: {round(stats['ratio']*100, 1)}% ({stats['movs_jugador']} pasos vs {stats['movs_minimos']} óptimos) -> Multiplicador x{stats['multiplicador']}")
        print(f"PUNTUACIÓN FINAL:                             {stats['puntos_totales']:>6} PUNTOS")
        print("=" * 64 + "\n")


def parse_comando(entrada):
    texto = entrada.strip().lower()
    if not texto:
        return None, None

    partes = texto.split()
    cmd = partes[0]

    if cmd in ["salir", "exit", "quit", "q"]: return "salir", None
    if cmd in ["ayuda", "help", "?", "h"]: return "ayuda", None
    if cmd in ["mapa", "ver", "m"]: return "mapa", None
    if cmd in ["novedades", "reglas"]: return "novedades", None
    if cmd in ["tomar", "agarrar", "grab", "oro", "t", "g", "a"]: return "tomar", None
    if cmd in ["brujula", "b", "compass"]: return "brujula", None
    if texto.isdigit(): return "mover", int(texto)

    numeros = re.findall(r'\d+', texto)
    num = int(numeros[0]) if numeros else None

    if cmd in ["mover", "ir", "mov"]:
        return ("mover", num) if num is not None else ("mover_invalido", None)
    if cmd in ["disparar", "flecha", "disp", "shoot", "f", "d"]:
        return ("disparar", num) if num is not None else ("disparar_invalido", None)
    if cmd in ["lanzar", "piedra", "tirar", "rock", "p", "l"]:
        return ("lanzar", num) if num is not None else ("lanzar_invalido", None)
    if cmd in ["cebo", "carne", "c"]:
        return ("cebo", num) if num is not None else ("cebo_invalido", None)

    return "desconocido", texto


def imprimir_ayuda():
    print("\n--- COMANDOS DISPONIBLES ---")
    print("  mover N     (o solo 'N')     : Desplazarte a la Cueva N conectada (ej: 'mover 2' o '2').")
    print("  disparar N  (o 'f N', 'd N') : Disparar una flecha en línea recta hacia la Cueva N.")
    print("  lanzar N    (o 'p N', 'l N') : Lanzar una piedra a la Cueva N para tantear peligros.")
    print("  cebo N      (o 'c N')        : Lanzar carne a la Cueva N para distraer al Wumpus 2 turnos.")
    print("  tomar       (o 't', 'oro')   : Tomar el oro o la brújula que se encuentre en la cueva.")
    print("  brujula     (o 'b')          : Consultar la dirección cardinal al oro o a la salida.")
    print("  mapa        (o 'm')          : Refrescar el mapa con la numeración de cuevas y niebla.")
    print("  novedades   (o 'reglas')     : Ver las novedades del juego.")
    print("  ayuda       (o '?')          : Mostrar esta lista de comandos.")
    print("  salir       (o 'q')          : Abandonar la partida.")
    print("----------------------------\n")


def ejecutar_juego():
    juego = MundoWumpus()
    limpiar_consola()
    print("=========================================================")
    print("           BIENVENIDO AL MUNDO DEL WUMPUS                ")
    print("=========================================================")
    print("Objetivo: Explora las cuevas, encuentra el oro, tómalo y")
    print("regresa hasta la Cueva 1 para escapar.")
    print("Escribe 'ayuda' para ver los comandos disponibles.")

    imprimir_novedades()
    input("Presiona Enter para comenzar la expedición...")

    while True:
        limpiar_consola()

        if not juego.vivo:
            print("================== HAS MUERTO EN LA CUEVA ==================")
            if juego.mensajes:
                for m in juego.mensajes: print(f"  * {m}")
            juego.mostrar_mapa(revelar_todo=True)
            juego.imprimir_resumen_puntuacion()
            break

        if juego.pos_jugador == 1 and juego.tiene_oro:
            print("****************** ¡VICTORIA! ESCAPASTE CON EL ORO ******************")
            if juego.mensajes:
                for m in juego.mensajes: print(f"  * {m}")
            juego.mostrar_mapa(revelar_todo=True)
            juego.imprimir_resumen_puntuacion()
            break

        print("=================== EL MUNDO DEL WUMPUS ===================")
        if juego.mensajes:
            print("[Último suceso]:")
            for m in juego.mensajes:
                print(f"  * {m}")
            juego.mensajes.clear()

        print("--- MAPA EXPLORADO (J=Tú, .=Visitada, ?=Niebla) ---")
        juego.mostrar_mapa()
        juego.describir_cueva()

        percepciones_actuales = juego.percibir()
        vecinos_actuales = juego.grafo.get(juego.pos_jugador, [])
        ej_cueva = vecinos_actuales[0] if vecinos_actuales else 2

        if juego.pos_jugador == juego.pos_oro and not juego.tiene_oro:
            prompt_texto = f"¿Qué deseas hacer? (escribe 'tomar' para el oro o '{ej_cueva}' para moverte): "
        elif juego.pos_jugador == juego.pos_brujula and not juego.tiene_brujula:
            prompt_texto = f"¿Qué deseas hacer? (escribe 'tomar' para la brújula o '{ej_cueva}' para moverte): "
        elif juego.modo_caceria and juego.wumpus_vivo and juego.cebos > 0:
            prompt_texto = f"¿Qué deseas hacer? (ej: '{ej_cueva}' para moverte o 'cebo {ej_cueva}' para distraer): "
        elif any("Hedor" in p for p in percepciones_actuales) and juego.wumpus_vivo:
            prompt_texto = f"¿Qué deseas hacer? (ej: 'disparar {ej_cueva}', 'lanzar {ej_cueva}' o '{ej_cueva}'): "
        elif any("Brisa" in p for p in percepciones_actuales):
            prompt_texto = f"¿Qué deseas hacer? (ej: 'lanzar {ej_cueva}' con piedra o 'mover {ej_cueva}'): "
        else:
            prompt_texto = f"¿Qué deseas hacer? (ej: 'mover {ej_cueva}' o simplemente '{ej_cueva}'): "

        print("-" * 59)
        print("Consejo: Escribe 'ayuda' para ver comandos | 'salir' para terminar")
        entrada = input(prompt_texto)
        accion, args = parse_comando(entrada)

        if accion is None:
            continue

        if accion == "mover":
            juego.mover(args)
        elif accion == "mover_invalido":
            juego.notificar("[!] Especifica a qué cueva moverte. Ejemplos: 'mover 2' o '2'.")
        elif accion == "disparar":
            juego.disparar(args)
        elif accion == "disparar_invalido":
            juego.notificar("[!] Especifica hacia qué cueva disparar. Ejemplo: 'disparar 2' o 'f 2'.")
        elif accion == "lanzar":
            juego.lanzar_piedra(args)
        elif accion == "lanzar_invalido":
            juego.notificar("[!] Especifica a qué cueva lanzar la piedra. Ejemplo: 'lanzar 2' o 'p 2'.")
        elif accion == "cebo":
            juego.lanzar_cebo(args)
        elif accion == "cebo_invalido":
            juego.notificar("[!] Especifica a qué cueva lanzar el cebo. Ejemplo: 'cebo 2' o 'c 2'.")
        elif accion == "tomar":
            juego.tomar()
        elif accion == "brujula":
            juego.consultar_brujula()
        elif accion == "mapa":
            juego.notificar("Mapa actualizado.")
        elif accion == "novedades":
            limpiar_consola()
            imprimir_novedades()
            input("\nPresiona Enter para regresar a la partida...")
        elif accion == "ayuda":
            limpiar_consola()
            imprimir_ayuda()
            input("\nPresiona Enter para regresar a la partida...")
        elif accion == "salir":
            limpiar_consola()
            print("================== HAS SALIDO DE LA CUEVA ==================")
            juego.causa_muerte = "Saliste de la cueva."
            juego.mostrar_mapa(revelar_todo=True)
            juego.imprimir_resumen_puntuacion()
            break
        else:
            juego.notificar(f"[!] Comando '{args}' no reconocido. Escribe 'ayuda' para consultar comandos.")


if __name__ == "__main__":
    ejecutar_juego()
