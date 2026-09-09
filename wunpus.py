import random
import math
import sys
from collections import deque
import pygame

COLOR_BG = (18, 20, 32)
COLOR_PANEL = (28, 30, 46)
COLOR_BORDER = (46, 50, 72)
COLOR_TEXT = (205, 214, 244)
COLOR_SUBTEXT = (166, 173, 200)
COLOR_GOLD = (249, 226, 175)
COLOR_RED = (243, 139, 168)
COLOR_GREEN = (166, 227, 161)
COLOR_CYAN = (137, 220, 235)
COLOR_PURPLE = (203, 166, 247)
COLOR_ORANGE = (250, 179, 135)

COLOR_TUNNEL = (48, 52, 76)
COLOR_TUNNEL_ACTIVE = (72, 78, 115)
COLOR_TUNNEL_BLOCKED = (180, 70, 90)

COLOR_NODE_FOG = (22, 24, 38)
COLOR_NODE_FOG_BORDER = (38, 42, 62)
COLOR_NODE_VISITED = (36, 40, 62)
COLOR_NODE_VISITED_BORDER = (75, 82, 120)
COLOR_NODE_PLAYER = (32, 70, 115)
COLOR_NODE_PLAYER_BORDER = (137, 180, 250)
COLOR_NODE_NEIGHBOR = (50, 60, 90)
COLOR_NODE_NEIGHBOR_BORDER = (137, 220, 235)

SIGNIFICADO_PERCEPCIONES = {
    "Hedor": ("Hedor", "El Wumpus está cerca", COLOR_RED),
    "Brisa": ("Brisa", "Pozo sin fondo cerca", COLOR_CYAN),
    "Aleteo": ("Aleteo", "Murciélagos gigantes cerca", COLOR_PURPLE),
    "Crujido": ("Crujido", "Roca inestable / derrumbe", COLOR_ORANGE),
    "Brillo": ("Brillo", "Cofre de oro en esta cueva", COLOR_GOLD),
    "Destello metálico": ("Destello", "Brújula antigua en el suelo", COLOR_CYAN)
}


class MundoWumpusCuadricula:
    def __init__(self, tamano=5, callback_log=None):
        self.tamano = tamano
        self.total_cuevas = tamano * tamano
        self.callback_log = callback_log
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
        self.piedras = 4
        self.cebos = 1
        self.habitaciones_visitadas = {self.pos_jugador}
        
        self.movimientos_totales = 0
        self.ecos_detectados = 0
        self.causa_muerte = ""
        
        self.inicializar_elementos()

    def notificar(self, mensaje, tipo="normal"):
        if self.callback_log:
            self.callback_log(mensaje, tipo)

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
            percepciones.append("Hedor")
        if any(v in self.pos_pozos for v in vecinos):
            percepciones.append("Brisa")
        if any(v in self.pos_murcielagos for v in vecinos):
            percepciones.append("Aleteo")
        if any(v == self.pos_derrumbe for v in vecinos) and not self.derrumbe_ocurrido:
            percepciones.append("Crujido")
        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            percepciones.append("Brillo")
        if self.pos_jugador == self.pos_brujula and not self.tiene_brujula:
            percepciones.append("Destello metálico")
            
        return percepciones

    def mover_wumpus_aleatorio(self):
        vecinos = [c for c in self.grafo.get(self.pos_wumpus, []) if c not in self.pos_pozos]
        if vecinos:
            self.pos_wumpus = random.choice(vecinos)
            if self.pos_wumpus == self.pos_jugador:
                self.notificar("El Wumpus ha entrado a tu cueva mientras huía.", "peligro")
                self.verificar_estado()

    def cazar_jugador(self):
        camino = self._obtener_camino_wumpus()
        if camino and len(camino) > 1:
            paso_siguiente = camino[1]
            self.pos_wumpus = paso_siguiente
            
            dist = len(camino) - 2
            if dist == 0:
                self.notificar("El Wumpus ha entrado a tu cueva.", "muerte")
                self.causa_muerte = "El Wumpus te alcanzó y te devoró."
                self.vivo = False
            else:
                sufijo = "s" if dist > 1 else ""
                self.notificar(f"El suelo tiembla... El Wumpus avanzó. Está a {dist} cueva{sufijo} de ti.", "alerta")
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
                self.notificar(f"Un derrumbe ha sellado el túnel entre la Cueva {self.pos_jugador} y la Cueva {v}.", "derrumbe")
                break
            else:
                self.grafo[self.pos_jugador].append(v)
                self.grafo[v].append(self.pos_jugador)
                self.grafo[self.pos_jugador].sort()
                self.grafo[v].sort()
                
        if not bloqueado:
            self.derrumbe_ocurrido = True
            self.notificar("Un temblor sacude la cueva y caen rocas, pero los túneles resisten.", "normal")

    def mover(self, nueva_pos):
        vecinos = self.grafo.get(self.pos_jugador, [])
        if nueva_pos in vecinos:
            self.pos_jugador = nueva_pos
            self.habitaciones_visitadas.add(nueva_pos)
            self.movimientos_totales += 1
            self.notificar(f"Te has desplazado a la Cueva {nueva_pos}.", "normal")
            
            if self.pos_jugador == self.pos_derrumbe and not self.derrumbe_ocurrido:
                self.activar_derrumbe()
                
            self.verificar_estado()
            
            if self.vivo:
                self.verificar_murcielagos()
                
            if self.vivo and self.modo_caceria and self.wumpus_vivo:
                if self.distraccion_wumpus > 0:
                    self.distraccion_wumpus -= 1
                    self.notificar(f"El Wumpus come el cebo y no avanza ({self.distraccion_wumpus} turno(s) restantes).", "pista")
                else:
                    self.turnos_caceria += 1
                    if self.turnos_caceria % 2 == 0:
                        self.cazar_jugador()
                    else:
                        dist = self._distancia_al_jugador()
                        sufijo = "s" if dist > 1 else ""
                        self.notificar(f"El Wumpus te acecha a {dist} cueva{sufijo} de distancia...", "alerta")
            return True
        else:
            self.notificar(f"No hay túnel directo hacia la Cueva {nueva_pos}.", "error")
            return False

    def verificar_murcielagos(self):
        if self.pos_jugador in self.pos_murcielagos:
            self.notificar("Unos murciélagos gigantes te atrapan y te llevan por el aire.", "murcielago")
            posibles = [c for c in range(1, self.total_cuevas + 1) if c != self.pos_jugador]
            destino = random.choice(posibles)
            self.notificar(f"Te dejan caer en la Cueva {destino}.", "murcielago")
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
            self.notificar("Caíste en un pozo sin fondo.", "muerte")
            self.causa_muerte = "Caíste en un pozo."
            self.vivo = False
        elif self.pos_jugador == self.pos_wumpus and self.wumpus_vivo:
            self.notificar("El Wumpus te ha devorado.", "muerte")
            self.causa_muerte = "El Wumpus te ha devorado."
            self.vivo = False

    def lanzar_piedra(self, objetivo):
        if self.piedras <= 0:
            self.notificar("Ya no te quedan piedras en la bolsa.", "error")
            return False

        if objetivo not in self.grafo.get(self.pos_jugador, []):
            self.notificar(f"Solo puedes lanzar piedras a cuevas contiguas.", "error")
            return False

        self.piedras -= 1
        self.notificar(f"Lanzas una piedra hacia la Cueva {objetivo}...", "normal")

        if objetivo in self.pos_pozos:
            self.notificar("Splash. Escuchas el eco cayendo al fondo de un pozo.", "pista")
            self.ecos_detectados += 1
        elif objetivo == self.pos_wumpus and self.wumpus_vivo:
            self.notificar("Rugido. La piedra golpeó al Wumpus y ruge al moverse.", "alerta")
            self.ecos_detectados += 1
            self.mover_wumpus_aleatorio()
        elif objetivo in self.pos_murcielagos:
            self.notificar("Escuchas chillidos y aleteo. Hay murciélagos en esa cueva.", "pista")
            self.ecos_detectados += 1
        elif objetivo == self.pos_derrumbe and not self.derrumbe_ocurrido:
            self.notificar("Crujido. La piedra impacta y cae polvo. El techo es inestable.", "pista")
            self.ecos_detectados += 1
        else:
            self.notificar("La piedra rueda por el suelo de roca sin novedad. Parece seguro.", "normal")
        return True

    def lanzar_cebo(self, objetivo):
        if self.cebos <= 0:
            self.notificar("Ya no te quedan cebos en el morral.", "error")
            return False

        if objetivo not in self.grafo.get(self.pos_jugador, []):
            self.notificar(f"Solo puedes lanzar el cebo a una cueva contigua.", "error")
            return False

        self.cebos -= 1
        self.notificar(f"Lanzas carne fresca hacia la Cueva {objetivo}...", "normal")

        if objetivo == self.pos_wumpus and self.wumpus_vivo:
            self.distraccion_wumpus = 2
            self.cebo_distrajo_wumpus = True
            self.notificar("El Wumpus devora la carne con avidez y se distrae por 2 turnos.", "victoria")
        elif self.modo_caceria and self.wumpus_vivo:
            self.distraccion_wumpus = 2
            self.cebo_distrajo_wumpus = True
            if objetivo not in self.pos_pozos:
                self.pos_wumpus = objetivo
            self.notificar("El Wumpus huele la carne, salta a la cueva y se distrae 2 turnos.", "victoria")
        else:
            self.notificar("El cebo queda en el suelo de la cueva.", "normal")
        return True

    def consultar_brujula(self):
        if not self.tiene_brujula:
            return None

        if not self.tiene_oro:
            obj_cueva = self.pos_oro
            nombre_meta = "el oro"
        else:
            obj_cueva = 1
            nombre_meta = "la salida (Cueva 1)"

        if self.pos_jugador == obj_cueva:
            return f"La aguja gira sobre sí misma: ¡{nombre_meta} está aquí!"
        else:
            xj, yj = self._cueva_a_xy(self.pos_jugador)
            xo, yo = self._cueva_a_xy(obj_cueva)
            dy = yo - yj
            dx = xo - xj

            if dy > 0 and dx > 0:
                rumbo = "Noreste"
            elif dy > 0 and dx < 0:
                rumbo = "Noroeste"
            elif dy < 0 and dx > 0:
                rumbo = "Sureste"
            elif dy < 0 and dx < 0:
                rumbo = "Suroeste"
            elif dy > 0:
                rumbo = "Norte"
            elif dy < 0:
                rumbo = "Sur"
            elif dx > 0:
                rumbo = "Este"
            else:
                rumbo = "Oeste"

            return f"Apunta hacia el {rumbo} (hacia {nombre_meta})"

    def tomar(self):
        algo_tomado = False

        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            self.tiene_oro = True
            algo_tomado = True
            self.notificar("Has tomado el cofre de oro (+1000 pts).", "victoria")
            self.notificar("Ahora debes regresar a la Cueva 1 para escapar.", "alerta")
            
            if self.wumpus_vivo:
                self.modo_caceria = True
                self.notificar("El Wumpus huele el oro y despierta. ¡Modo cacería activado!", "alerta")

        if self.pos_jugador == self.pos_brujula and not self.tiene_brujula:
            self.tiene_brujula = True
            algo_tomado = True
            self.notificar("Has tomado la brújula de exploración (+300 pts).", "victoria")
            self.notificar("La aguja magnética te indicará el rumbo hacia el oro.", "pista")

        if not algo_tomado:
            if self.tiene_oro and self.pos_jugador == self.pos_oro:
                self.notificar("Ya tienes el oro en tu mochila.", "normal")
            elif self.tiene_brujula and self.pos_jugador == self.pos_brujula:
                self.notificar("Ya tomaste la brújula de esta cueva.", "normal")
            else:
                self.notificar("No hay nada que tomar en esta cueva.", "normal")
        return algo_tomado

    def agarrar(self):
        return self.tomar()

    def disparar(self, objetivo):
        if self.flechas <= 0:
            self.notificar("Ya no te quedan flechas.", "error")
            return False

        vecinos = self.grafo.get(self.pos_jugador, [])
        if objetivo not in vecinos:
            self.notificar(f"Solo puedes disparar a través de un túnel conectado.", "error")
            return False

        x_orig, y_orig = self._cueva_a_xy(self.pos_jugador)
        x_dest, y_dest = self._cueva_a_xy(objetivo)

        dx = x_dest - x_orig
        dy = y_dest - y_orig

        paso_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        paso_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

        self.flechas -= 1
        self.notificar(f"Disparas la flecha hacia la Cueva {objetivo}.", "normal")

        cur_x, cur_y = x_orig + paso_x, y_orig + paso_y
        impacto = False

        while 0 <= cur_x < self.tamano and 0 <= cur_y < self.tamano:
            cur_cueva = self._xy_a_cueva(cur_x, cur_y)
            if cur_cueva == self.pos_wumpus and self.wumpus_vivo:
                self.wumpus_vivo = False
                impacto = True
                self.notificar(f"Has matado al Wumpus en la Cueva {cur_cueva} (+1000 pts).", "victoria")
                if self.modo_caceria:
                    self.modo_caceria = False
                    self.notificar("La cueva queda en silencio. La cacería ha terminado.", "victoria")
                break
            cur_x += paso_x
            cur_y += paso_y

        if not impacto:
            self.notificar("La flecha chocó contra la pared. Has fallado.", "peligro")
            if self.wumpus_vivo and not self.modo_caceria:
                self.mover_wumpus_aleatorio()

        return True

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
            puntos_cuevas +
            puntos_oro +
            puntos_brujula +
            puntos_wumpus +
            puntos_ecos +
            puntos_flecha +
            puntos_piedras +
            puntos_cebo_usado +
            puntos_cebo_guardado +
            puntos_escape
        )

        camino_oro = self._calcular_camino_optimo_oro()
        pasos_min_ida = len(camino_oro) - 1 if camino_oro else 1
        movs_minimos = pasos_min_ida * 2

        if self.tiene_oro and self.movimientos_totales > 0:
            ratio = min(1.0, movs_minimos / self.movimientos_totales)
            if self.pos_jugador == 1 and self.vivo:
                multiplicador = round(1.0 + 1.5 * ratio, 2)
            else:
                multiplicador = round(1.0 + 0.5 * ratio, 2)
        else:
            multiplicador = 1.0
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


class WumpusPygameApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.width = 1140
        self.height = 760
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("El Mundo del Wumpus - Cuadrícula de 25 Cuevas")

        self.clock = pygame.time.Clock()
        self.running = True

        self.font_title = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 20, bold=True)
        self.font_bold = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 14, bold=True)
        self.font_btn = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 13, bold=True)
        self.font_normal = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 13)
        self.font_small = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 11)

        self.log_mensajes = []
        self.modo_accion = "mover"
        self.juego = None
        self.coords_cuevas = {}
        self.radio_cueva = 24

        self.mostrar_menu_mecanicas = False
        self.btn_mecanicas_rect = None
        self.btn_cerrar_mecanicas_rect = None
        self.dropdown_mecanicas_rect = None

        self.botones_vecinos = []
        self.btn_disparar_rect = None
        self.btn_lanzar_rect = None
        self.btn_cebo_rect = None
        self.btn_tomar_rect = None
        self.btn_reiniciar_rect = None

        self._calcular_coordenadas_cuadricula()
        self.nueva_partida()

    def agregar_log(self, mensaje, tipo="normal"):
        self.log_mensajes.append((mensaje, tipo))
        if len(self.log_mensajes) > 12:
            self.log_mensajes.pop(0)

    def nueva_partida(self):
        self.log_mensajes.clear()
        self.juego = MundoWumpusCuadricula(tamano=5, callback_log=self.agregar_log)
        self.modo_accion = "mover"
        self.agregar_log("Nueva expedición.", "victoria")
        self.agregar_log("Encuentra el oro, tómalo y regresa a la Cueva 1 para escapar.", "normal")

    def _calcular_coordenadas_cuadricula(self):
        self.coords_cuevas.clear()
        cx = 325
        cy = 380
        spacing = 110

        for y in range(5):
            for x in range(5):
                c = y * 5 + x + 1
                px = cx + (x - 2) * spacing
                py = cy - (y - 2) * spacing
                self.coords_cuevas[c] = (px, py)

    def obtener_cueva_bajo_cursor(self, mx, my):
        for c, (cx, cy) in self.coords_cuevas.items():
            if (mx - cx) ** 2 + (my - cy) ** 2 <= (self.radio_cueva + 4) ** 2:
                return c
        return None

    def interactuar_con_cueva(self, objetivo):
        if not self.juego.vivo:
            return

        if self.juego.pos_jugador == 1 and self.juego.tiene_oro:
            return

        if self.modo_accion == "mover":
            self.juego.mover(objetivo)
        elif self.modo_accion == "disparar":
            if self.juego.disparar(objetivo):
                self.modo_accion = "mover"
        elif self.modo_accion == "lanzar":
            if self.juego.lanzar_piedra(objetivo):
                self.modo_accion = "mover"
        elif self.modo_accion == "cebo":
            if self.juego.lanzar_cebo(objetivo):
                self.modo_accion = "mover"

    def run(self):
        while self.running:
            self._handle_events()
            self._render()
            self.clock.tick(30)
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        cueva_hover = self.obtener_cueva_bajo_cursor(*mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_mecanicas_rect and self.btn_mecanicas_rect.collidepoint(event.pos):
                    self.mostrar_menu_mecanicas = not self.mostrar_menu_mecanicas
                    continue

                if self.mostrar_menu_mecanicas:
                    if self.btn_cerrar_mecanicas_rect and self.btn_cerrar_mecanicas_rect.collidepoint(event.pos):
                        self.mostrar_menu_mecanicas = False
                    elif self.dropdown_mecanicas_rect and self.dropdown_mecanicas_rect.collidepoint(event.pos):
                        pass
                    else:
                        self.mostrar_menu_mecanicas = False
                    continue

                if self.btn_disparar_rect and self.btn_disparar_rect.collidepoint(event.pos):
                    if self.juego.flechas > 0 and self.juego.vivo:
                        self.modo_accion = "disparar" if self.modo_accion != "disparar" else "mover"
                        if self.modo_accion == "disparar":
                            self.agregar_log("Modo DISPARAR: Haz clic en una cueva vecina.", "alerta")
                    else:
                        self.agregar_log("No tienes flechas disponibles.", "error")

                elif self.btn_lanzar_rect and self.btn_lanzar_rect.collidepoint(event.pos):
                    if self.juego.piedras > 0 and self.juego.vivo:
                        self.modo_accion = "lanzar" if self.modo_accion != "lanzar" else "mover"
                        if self.modo_accion == "lanzar":
                            self.agregar_log("Modo PIEDRA: Haz clic en una cueva vecina para tantear.", "alerta")
                    else:
                        self.agregar_log("No te quedan piedras en la bolsa.", "error")

                elif self.btn_cebo_rect and self.btn_cebo_rect.collidepoint(event.pos):
                    if self.juego.cebos > 0 and self.juego.vivo:
                        self.modo_accion = "cebo" if self.modo_accion != "cebo" else "mover"
                        if self.modo_accion == "cebo":
                            self.agregar_log("Modo CEBO: Haz clic en una cueva vecina para distraer al Wumpus.", "alerta")
                    else:
                        self.agregar_log("No te quedan cebos en el morral.", "error")

                elif self.btn_tomar_rect and self.btn_tomar_rect.collidepoint(event.pos):
                    if self.juego.vivo:
                        self.juego.tomar()

                elif self.btn_reiniciar_rect and self.btn_reiniciar_rect.collidepoint(event.pos):
                    self.nueva_partida()

                for btn_rect, cueva_vec in self.botones_vecinos:
                    if btn_rect.collidepoint(event.pos):
                        self.interactuar_con_cueva(cueva_vec)
                        break

                if cueva_hover is not None:
                    self.interactuar_con_cueva(cueva_hover)

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_m, pygame.K_h):
                    self.mostrar_menu_mecanicas = not self.mostrar_menu_mecanicas
                    continue

                if event.key == pygame.K_ESCAPE:
                    if self.mostrar_menu_mecanicas:
                        self.mostrar_menu_mecanicas = False
                        continue
                    else:
                        self.modo_accion = "mover"
                        continue

                vecinos = self.juego.grafo.get(self.juego.pos_jugador, [])
                if event.key == pygame.K_1 and len(vecinos) >= 1:
                    self.interactuar_con_cueva(vecinos[0])
                elif event.key == pygame.K_2 and len(vecinos) >= 2:
                    self.interactuar_con_cueva(vecinos[1])
                elif event.key == pygame.K_3 and len(vecinos) >= 3:
                    self.interactuar_con_cueva(vecinos[2])
                elif event.key == pygame.K_4 and len(vecinos) >= 4:
                    self.interactuar_con_cueva(vecinos[3])
                elif event.key == pygame.K_f:
                    if self.juego.flechas > 0 and self.juego.vivo:
                        self.modo_accion = "disparar" if self.modo_accion != "disparar" else "mover"
                elif event.key == pygame.K_p:
                    if self.juego.piedras > 0 and self.juego.vivo:
                        self.modo_accion = "lanzar" if self.modo_accion != "lanzar" else "mover"
                elif event.key == pygame.K_c:
                    if self.juego.cebos > 0 and self.juego.vivo:
                        self.modo_accion = "cebo" if self.modo_accion != "cebo" else "mover"
                elif event.key in (pygame.K_t, pygame.K_g, pygame.K_SPACE):
                    if self.juego.vivo:
                        self.juego.tomar()
                elif event.key == pygame.K_r:
                    self.nueva_partida()

    def _render(self):
        self.screen.fill(COLOR_BG)
        self._dibujar_red_cuadricula()
        self._dibujar_panel_derecho()
        self._dibujar_estado_final()
        if self.mostrar_menu_mecanicas:
            self._dibujar_menu_mecanicas()
        pygame.display.flip()

    def _dibujar_red_cuadricula(self):
        mouse_pos = pygame.mouse.get_pos()
        cueva_hover = self.obtener_cueva_bajo_cursor(*mouse_pos)
        vecinos_jugador = self.juego.grafo.get(self.juego.pos_jugador, [])
        partida_terminada = (not self.juego.vivo) or (self.juego.pos_jugador == 1 and self.juego.tiene_oro)

        for c in range(1, self.juego.total_cuevas + 1):
            x, y = self.juego._cueva_a_xy(c)
            p1 = self.coords_cuevas[c]

            if x < self.juego.tamano - 1:
                c_este = self.juego._xy_a_cueva(x + 1, y)
                p2 = self.coords_cuevas[c_este]
                arista = (min(c, c_este), max(c, c_este))
                
                if arista in self.juego.bloqueos:
                    pygame.draw.line(self.screen, COLOR_TUNNEL_BLOCKED, p1, p2, 5)
                    mx, my = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
                    pygame.draw.line(self.screen, COLOR_RED, (mx - 6, my - 6), (mx + 6, my + 6), 3)
                    pygame.draw.line(self.screen, COLOR_RED, (mx - 6, my + 6), (mx + 6, my - 6), 3)
                elif c_este in self.juego.grafo.get(c, []):
                    c_tun = COLOR_TUNNEL_ACTIVE if (c == self.juego.pos_jugador or c_este == self.juego.pos_jugador) else COLOR_TUNNEL
                    pygame.draw.line(self.screen, c_tun, p1, p2, 4)

            if y < self.juego.tamano - 1:
                c_norte = self.juego._xy_a_cueva(x, y + 1)
                p2 = self.coords_cuevas[c_norte]
                arista = (min(c, c_norte), max(c, c_norte))
                
                if arista in self.juego.bloqueos:
                    pygame.draw.line(self.screen, COLOR_TUNNEL_BLOCKED, p1, p2, 5)
                    mx, my = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
                    pygame.draw.line(self.screen, COLOR_RED, (mx - 6, my - 6), (mx + 6, my + 6), 3)
                    pygame.draw.line(self.screen, COLOR_RED, (mx - 6, my + 6), (mx + 6, my - 6), 3)
                elif c_norte in self.juego.grafo.get(c, []):
                    c_tun = COLOR_TUNNEL_ACTIVE if (c == self.juego.pos_jugador or c_norte == self.juego.pos_jugador) else COLOR_TUNNEL
                    pygame.draw.line(self.screen, c_tun, p1, p2, 4)

        for c, (cx, cy) in self.coords_cuevas.items():
            es_jugador = (c == self.juego.pos_jugador)
            es_visitada = (c in self.juego.habitaciones_visitadas)
            es_vecino = (c in vecinos_jugador) and (not partida_terminada)
            es_hover = (c == cueva_hover)

            if es_jugador:
                c_bg = COLOR_NODE_PLAYER
                c_border = COLOR_NODE_PLAYER_BORDER
                ancho_border = 3
            elif es_hover and es_vecino:
                c_bg = (60, 75, 110)
                c_border = COLOR_GOLD
                ancho_border = 3
            elif es_vecino:
                c_bg = COLOR_NODE_NEIGHBOR
                c_border = COLOR_NODE_NEIGHBOR_BORDER
                ancho_border = 2
            elif es_visitada:
                c_bg = COLOR_NODE_VISITED
                c_border = COLOR_NODE_VISITED_BORDER
                ancho_border = 2
            else:
                c_bg = COLOR_NODE_FOG
                c_border = COLOR_NODE_FOG_BORDER
                ancho_border = 1

            pygame.draw.circle(self.screen, c_bg, (cx, cy), self.radio_cueva)
            pygame.draw.circle(self.screen, c_border, (cx, cy), self.radio_cueva, ancho_border)

            if partida_terminada:
                if c == self.juego.pos_jugador:
                    tag = "JO" if self.juego.tiene_oro else "J"
                    col = COLOR_GOLD if self.juego.tiene_oro else COLOR_CYAN
                elif c == self.juego.pos_wumpus:
                    tag = "W" if self.juego.wumpus_vivo else "MW"
                    col = COLOR_RED if self.juego.wumpus_vivo else (120, 120, 140)
                elif c == self.juego.pos_oro:
                    tag = "O"
                    col = COLOR_GOLD
                elif c == self.juego.pos_brujula and not self.juego.tiene_brujula:
                    tag = "B"
                    col = COLOR_CYAN
                elif c in self.juego.pos_pozos:
                    tag = "P"
                    col = COLOR_PURPLE
                elif c in self.juego.pos_murcielagos:
                    tag = "M"
                    col = (180, 130, 240)
                elif c == self.juego.pos_derrumbe:
                    tag = "R"
                    col = COLOR_ORANGE
                else:
                    tag = str(c)
                    col = COLOR_SUBTEXT

                txt_nodo = self.font_bold.render(tag, True, col)
                self.screen.blit(txt_nodo, (cx - txt_nodo.get_width() // 2, cy - txt_nodo.get_height() // 2))

            else:
                if es_jugador:
                    tag = "JO" if self.juego.tiene_oro else "J"
                    col = COLOR_GOLD if self.juego.tiene_oro else (255, 255, 255)
                    txt_nodo = self.font_bold.render(tag, True, col)
                elif es_visitada:
                    txt_nodo = self.font_small.render(str(c), True, COLOR_TEXT)
                else:
                    txt_nodo = self.font_small.render(str(c), True, (90, 95, 125))

                self.screen.blit(txt_nodo, (cx - txt_nodo.get_width() // 2, cy - txt_nodo.get_height() // 2))

    def _dibujar_panel_derecho(self):
        panel_x = 675
        panel_w = 435

        txt_titulo = self.font_title.render("EL MUNDO DEL WUMPUS", True, COLOR_GOLD)
        self.screen.blit(txt_titulo, (panel_x, 14))
        txt_sub = self.font_small.render("Cuadrícula de 25 cuevas (5x5)", True, COLOR_SUBTEXT)
        self.screen.blit(txt_sub, (panel_x, 40))

        self.btn_mecanicas_rect = pygame.Rect(panel_x + panel_w - 125, 12, 125, 26)
        mouse_pos = pygame.mouse.get_pos()
        es_hover_mec = self.btn_mecanicas_rect.collidepoint(mouse_pos)
        c_bg_mec = (55, 65, 95) if (es_hover_mec or self.mostrar_menu_mecanicas) else (40, 45, 68)
        pygame.draw.rect(self.screen, c_bg_mec, self.btn_mecanicas_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_GOLD, self.btn_mecanicas_rect, 1, border_radius=6)

        simbolo = "[^]" if self.mostrar_menu_mecanicas else "[v]"
        txt_btn_mec = self.font_btn.render(f"Novedades {simbolo}", True, COLOR_GOLD)
        self.screen.blit(txt_btn_mec, (self.btn_mecanicas_rect.centerx - txt_btn_mec.get_width() // 2,
                                       self.btn_mecanicas_rect.centery - txt_btn_mec.get_height() // 2))

        cur_y = 66
        if self.juego.modo_caceria and self.juego.wumpus_vivo:
            banner_rect = pygame.Rect(panel_x, cur_y, panel_w, 32)
            if self.juego.distraccion_wumpus > 0:
                pygame.draw.rect(self.screen, (70, 70, 30), banner_rect, border_radius=6)
                pygame.draw.rect(self.screen, COLOR_GOLD, banner_rect, 1, border_radius=6)
                txt_cac = self.font_bold.render(f"Wumpus comiendo el cebo ({self.juego.distraccion_wumpus} turnos restantes)", True, COLOR_GOLD)
            else:
                dist = self.juego._distancia_al_jugador()
                sufijo = "s" if dist > 1 else ""
                pygame.draw.rect(self.screen, COLOR_RED, banner_rect, border_radius=6)
                txt_cac = self.font_bold.render(f"¡WUMPUS EN CACERÍA! A {dist} cueva{sufijo} de distancia", True, (20, 20, 30))
            self.screen.blit(txt_cac, (banner_rect.centerx - txt_cac.get_width() // 2, banner_rect.centery - txt_cac.get_height() // 2))
            cur_y += 38

        en_oro = (self.juego.pos_jugador == self.juego.pos_oro and not self.juego.tiene_oro)
        en_brujula = (self.juego.pos_jugador == self.juego.pos_brujula and not self.juego.tiene_brujula)
        
        if en_oro:
            rem_rect = pygame.Rect(panel_x, cur_y, panel_w, 28)
            pygame.draw.rect(self.screen, (60, 55, 20), rem_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_GOLD, rem_rect, 1, border_radius=6)
            txt_rem = self.font_bold.render("¡Cofre de oro en esta cueva! Haz clic en 'Tomar' o pulsa T", True, COLOR_GOLD)
            self.screen.blit(txt_rem, (rem_rect.centerx - txt_rem.get_width() // 2, rem_rect.centery - txt_rem.get_height() // 2))
            cur_y += 34
        elif en_brujula:
            rem_rect = pygame.Rect(panel_x, cur_y, panel_w, 28)
            pygame.draw.rect(self.screen, (20, 50, 60), rem_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_CYAN, rem_rect, 1, border_radius=6)
            txt_rem = self.font_bold.render("¡Brújula antigua encontrada! Haz clic en 'Tomar' o pulsa T", True, COLOR_CYAN)
            self.screen.blit(txt_rem, (rem_rect.centerx - txt_rem.get_width() // 2, rem_rect.centery - txt_rem.get_height() // 2))
            cur_y += 34

        inv_rect = pygame.Rect(panel_x, cur_y, panel_w, 82)
        pygame.draw.rect(self.screen, COLOR_PANEL, inv_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, inv_rect, 1, border_radius=8)

        txt_inv_titulo = self.font_bold.render("Estado del Explorador", True, COLOR_GOLD)
        self.screen.blit(txt_inv_titulo, (panel_x + 14, cur_y + 8))

        txt_fl = self.font_normal.render(f"Flechas: {self.juego.flechas}", True, COLOR_TEXT)
        self.screen.blit(txt_fl, (panel_x + 16, cur_y + 30))

        txt_pd = self.font_normal.render(f"Piedras: {self.juego.piedras}", True, COLOR_TEXT)
        self.screen.blit(txt_pd, (panel_x + 140, cur_y + 30))

        txt_cb = self.font_normal.render(f"Cebos: {self.juego.cebos}", True, COLOR_TEXT)
        self.screen.blit(txt_cb, (panel_x + 270, cur_y + 30))

        oro_str = "Sí" if self.juego.tiene_oro else "No"
        txt_oro = self.font_normal.render(f"Oro: {oro_str}", True, COLOR_GOLD if self.juego.tiene_oro else COLOR_TEXT)
        self.screen.blit(txt_oro, (panel_x + 16, cur_y + 54))

        bru_str = "Sí" if self.juego.tiene_brujula else "No"
        txt_bru = self.font_normal.render(f"Brújula: {bru_str}", True, COLOR_CYAN if self.juego.tiene_brujula else COLOR_TEXT)
        self.screen.blit(txt_bru, (panel_x + 140, cur_y + 54))

        txt_pos = self.font_normal.render(f"Cueva: {self.juego.pos_jugador}/25", True, COLOR_TEXT)
        self.screen.blit(txt_pos, (panel_x + 270, cur_y + 54))
        cur_y += 90

        if self.juego.tiene_brujula:
            bru_rect = pygame.Rect(panel_x, cur_y, panel_w, 32)
            pygame.draw.rect(self.screen, (22, 35, 48), bru_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_CYAN, bru_rect, 1, border_radius=6)
            lectura = self.juego.consultar_brujula()
            txt_bru_lect = self.font_bold.render(f"Brújula: {lectura}", True, COLOR_CYAN)
            self.screen.blit(txt_bru_lect, (panel_x + 14, cur_y + 7))
            cur_y += 38

        percepciones = self.juego.percibir()
        h_perc = 32 + max(1, len(percepciones)) * 20
        perc_rect = pygame.Rect(panel_x, cur_y, panel_w, h_perc)
        pygame.draw.rect(self.screen, COLOR_PANEL, perc_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, perc_rect, 1, border_radius=8)

        txt_per_tit = self.font_bold.render("Percepciones en esta cueva:", True, COLOR_TEXT)
        self.screen.blit(txt_per_tit, (panel_x + 14, cur_y + 7))

        if percepciones:
            line_p_y = cur_y + 28
            for p in percepciones:
                if p in SIGNIFICADO_PERCEPCIONES:
                    nombre, desc, col = SIGNIFICADO_PERCEPCIONES[p]
                    txt_p = self.font_normal.render(f"• {nombre}: {desc}", True, col)
                else:
                    txt_p = self.font_normal.render(f"• {p}", True, COLOR_GOLD)
                self.screen.blit(txt_p, (panel_x + 16, line_p_y))
                line_p_y += 19
        else:
            txt_percs = self.font_normal.render("• Silencio. No percibes peligros contiguos.", True, (120, 125, 150))
            self.screen.blit(txt_percs, (panel_x + 16, cur_y + 28))

        cur_y += h_perc + 8

        tun_rect = pygame.Rect(panel_x, cur_y, panel_w, 62)
        pygame.draw.rect(self.screen, COLOR_PANEL, tun_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, tun_rect, 1, border_radius=8)

        txt_tun_tit = self.font_bold.render(f"Túneles desde Cueva {self.juego.pos_jugador}:", True, COLOR_TEXT)
        self.screen.blit(txt_tun_tit, (panel_x + 14, cur_y + 6))

        vecinos = self.juego.grafo.get(self.juego.pos_jugador, [])
        self.botones_vecinos = []
        btn_w = 95
        for idx, v in enumerate(vecinos):
            bx = panel_x + 10 + idx * (btn_w + 8)
            by = cur_y + 28
            b_rect = pygame.Rect(bx, by, btn_w, 26)
            self.botones_vecinos.append((b_rect, v))
            pygame.draw.rect(self.screen, (42, 46, 70), b_rect, border_radius=5)
            txt_btn_v = self.font_bold.render(f"[{idx+1}] Cueva {v}", True, COLOR_CYAN)
            self.screen.blit(txt_btn_v, (b_rect.centerx - txt_btn_v.get_width() // 2, b_rect.centery - txt_btn_v.get_height() // 2))
        cur_y += 70

        btn_w_action = 98
        self.btn_disparar_rect = pygame.Rect(panel_x, cur_y, btn_w_action, 34)
        self.btn_lanzar_rect = pygame.Rect(panel_x + 106, cur_y, btn_w_action, 34)
        self.btn_cebo_rect = pygame.Rect(panel_x + 212, cur_y, btn_w_action, 34)
        self.btn_tomar_rect = pygame.Rect(panel_x + 318, cur_y, 117, 34)
        self.btn_reiniciar_rect = pygame.Rect(panel_x, cur_y + 40, panel_w, 30)

        c_disp = COLOR_RED if self.modo_accion == "disparar" else (50, 54, 75)
        c_lanz = COLOR_ORANGE if self.modo_accion == "lanzar" else (50, 54, 75)
        c_cebo = COLOR_PURPLE if self.modo_accion == "cebo" else (50, 54, 75)
        c_tomar = COLOR_GREEN if (en_oro or en_brujula) else (45, 65, 55)

        pygame.draw.rect(self.screen, c_disp, self.btn_disparar_rect, border_radius=6)
        pygame.draw.rect(self.screen, c_lanz, self.btn_lanzar_rect, border_radius=6)
        pygame.draw.rect(self.screen, c_cebo, self.btn_cebo_rect, border_radius=6)
        pygame.draw.rect(self.screen, c_tomar, self.btn_tomar_rect, border_radius=6)
        pygame.draw.rect(self.screen, (40, 44, 62), self.btn_reiniciar_rect, border_radius=6)

        txt_b_disp = self.font_bold.render("Disparar (F)", True, (20, 20, 30) if self.modo_accion == "disparar" else COLOR_TEXT)
        txt_b_lanz = self.font_bold.render("Piedra (P)", True, (20, 20, 30) if self.modo_accion == "lanzar" else COLOR_TEXT)
        txt_b_cebo = self.font_bold.render("Cebo (C)", True, (20, 20, 30) if self.modo_accion == "cebo" else COLOR_TEXT)
        txt_b_tomar = self.font_bold.render("Tomar (T)", True, (20, 20, 30) if c_tomar == COLOR_GREEN else COLOR_TEXT)
        txt_b_rein = self.font_bold.render("Nueva Partida (R)", True, COLOR_TEXT)

        self.screen.blit(txt_b_disp, (self.btn_disparar_rect.centerx - txt_b_disp.get_width() // 2, self.btn_disparar_rect.centery - txt_b_disp.get_height() // 2))
        self.screen.blit(txt_b_lanz, (self.btn_lanzar_rect.centerx - txt_b_lanz.get_width() // 2, self.btn_lanzar_rect.centery - txt_b_lanz.get_height() // 2))
        self.screen.blit(txt_b_cebo, (self.btn_cebo_rect.centerx - txt_b_cebo.get_width() // 2, self.btn_cebo_rect.centery - txt_b_cebo.get_height() // 2))
        self.screen.blit(txt_b_tomar, (self.btn_tomar_rect.centerx - txt_b_tomar.get_width() // 2, self.btn_tomar_rect.centery - txt_b_tomar.get_height() // 2))
        self.screen.blit(txt_b_rein, (self.btn_reiniciar_rect.centerx - txt_b_rein.get_width() // 2, self.btn_reiniciar_rect.centery - txt_b_rein.get_height() // 2))
        cur_y += 78

        log_h = self.height - cur_y - 28
        log_rect = pygame.Rect(panel_x, cur_y, panel_w, log_h)
        pygame.draw.rect(self.screen, (15, 16, 26), log_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, log_rect, 1, border_radius=8)

        txt_log_tit = self.font_bold.render("Bitácora de la Aventura", True, COLOR_GOLD)
        self.screen.blit(txt_log_tit, (panel_x + 14, cur_y + 8))

        line_y = cur_y + 28
        for msg, tipo in self.log_mensajes[-7:]:
            if tipo in ("peligro", "muerte"):
                c = COLOR_RED
            elif tipo == "victoria":
                c = COLOR_GREEN
            elif tipo == "alerta":
                c = COLOR_GOLD
            elif tipo == "pista":
                c = COLOR_CYAN
            elif tipo == "derrumbe":
                c = COLOR_ORANGE
            elif tipo == "murcielago":
                c = COLOR_PURPLE
            else:
                c = COLOR_TEXT

            txt_line = self.font_normal.render(f"• {msg}", True, c)
            self.screen.blit(txt_line, (panel_x + 14, line_y))
            line_y += 18

        txt_ctrls = self.font_small.render("Atajos: 1..4 en túneles | F: Disparo | P: Piedra | C: Cebo | T: Tomar | R: Reiniciar", True, COLOR_SUBTEXT)
        self.screen.blit(txt_ctrls, (panel_x, self.height - 20))

    def _dibujar_estado_final(self):
        partida_ganada = (self.juego.pos_jugador == 1 and self.juego.tiene_oro and self.juego.vivo)
        partida_perdida = (not self.juego.vivo)

        if not (partida_ganada or partida_perdida):
            return

        box_w = 440
        box_h = 320
        box_x = 105
        box_y = 220
        modal_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 140))
        self.screen.blit(s, (0, 0))

        pygame.draw.rect(self.screen, (25, 27, 42), modal_rect, border_radius=10)
        c_borde = COLOR_GREEN if partida_ganada else COLOR_RED
        pygame.draw.rect(self.screen, c_borde, modal_rect, 2, border_radius=10)

        tit = "RESUMEN DE PUNTUACIÓN - VICTORIA" if partida_ganada else "RESUMEN DE PUNTUACIÓN"
        txt_tit = self.font_bold.render(tit, True, c_borde)
        self.screen.blit(txt_tit, (modal_rect.centerx - txt_tit.get_width() // 2, box_y + 14))

        stats = self.juego.calcular_puntuacion()
        causa = "Regresaste con el oro a la Cueva 1." if partida_ganada else self.juego.causa_muerte
        txt_causa = self.font_normal.render(f"Causa: {causa}", True, COLOR_TEXT)
        self.screen.blit(txt_causa, (box_x + 20, box_y + 40))

        lines = [
            f"• Cuevas exploradas ({stats['cuevas_visitadas']}/25): +{stats['puntos_cuevas']} pts",
            f"• Oro tomado: +{stats['puntos_oro']} pts" if stats['puntos_oro'] > 0 else None,
            f"• Brújula obtenida: +{stats['puntos_brujula']} pts" if stats['puntos_brujula'] > 0 else None,
            f"• Wumpus derrotado: +{stats['puntos_wumpus']} pts" if stats['puntos_wumpus'] > 0 else None,
            f"• Ecos detectados ({stats['ecos_detectados']}): +{stats['puntos_ecos']} pts" if stats['ecos_detectados'] > 0 else None,
            f"• Cebo usado con éxito: +{stats['puntos_cebo_usado']} pts" if stats['puntos_cebo_usado'] > 0 else None,
            f"• Bonificación de escape: +{stats['puntos_escape']} pts" if stats['puntos_escape'] > 0 else None,
        ]
        lines = [l for l in lines if l is not None]

        y_offset = box_y + 64
        for l in lines[:6]:
            txt_l = self.font_small.render(l, True, COLOR_SUBTEXT)
            self.screen.blit(txt_l, (box_x + 20, y_offset))
            y_offset += 18

        pygame.draw.line(self.screen, COLOR_BORDER, (box_x + 20, box_y + 205), (box_x + box_w - 20, box_y + 205), 1)

        txt_subt = self.font_normal.render(f"Subtotal Base: {stats['subtotal_base']} pts", True, COLOR_TEXT)
        self.screen.blit(txt_subt, (box_x + 20, box_y + 215))

        txt_mult = self.font_normal.render(f"Multiplicador de Eficiencia: x{stats['multiplicador']}", True, COLOR_GOLD)
        self.screen.blit(txt_mult, (box_x + 20, box_y + 238))

        txt_final = self.font_bold.render(f"PUNTUACIÓN FINAL: {stats['puntos_totales']} PUNTOS", True, COLOR_GOLD)
        self.screen.blit(txt_final, (box_x + 20, box_y + 262))

        txt_rein = self.font_bold.render("Pulsa R o clic en 'Nueva Partida' para reiniciar", True, COLOR_CYAN)
        self.screen.blit(txt_rein, (modal_rect.centerx - txt_rein.get_width() // 2, box_y + 292))

    def _dibujar_menu_mecanicas(self):
        box_w = 440
        box_h = 420
        box_x = 670
        box_y = 44
        self.dropdown_mecanicas_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(self.screen, (24, 26, 40), self.dropdown_mecanicas_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_GOLD, self.dropdown_mecanicas_rect, 2, border_radius=8)

        txt_tit = self.font_bold.render("NOVEDADES", True, COLOR_GOLD)
        self.screen.blit(txt_tit, (box_x + 16, box_y + 12))

        self.btn_cerrar_mecanicas_rect = pygame.Rect(box_x + box_w - 30, box_y + 8, 22, 22)
        pygame.draw.rect(self.screen, (50, 30, 40), self.btn_cerrar_mecanicas_rect, border_radius=4)
        txt_x = self.font_bold.render("X", True, COLOR_RED)
        self.screen.blit(txt_x, (self.btn_cerrar_mecanicas_rect.centerx - txt_x.get_width() // 2,
                                  self.btn_cerrar_mecanicas_rect.centery - txt_x.get_height() // 2))

        mecanicas_texto = [
            ("1. Modo Cacería del Wumpus:", COLOR_GOLD),
            ("   Al tomar el oro, el Wumpus despierta y te persigue", COLOR_TEXT),
            ("   activamente cada 2 turnos. Debes regresar a la Cueva 1.", COLOR_TEXT),
            ("", COLOR_TEXT),
            ("2. Lanzamiento de Piedras (4 en bolsa):", COLOR_GOLD),
            ("   Arroja piedras a cuevas vecinas ('Piedra') para tantear:", COLOR_TEXT),
            ("   Splash (pozo), Rugido (Wumpus), Aleteo (murciélagos).", COLOR_SUBTEXT),
            ("", COLOR_TEXT),
            ("3. Cebo de Carne (Equipo Inicial):", COLOR_GOLD),
            ("   Lanza un trozo de carne ('Cebo') para distraer al Wumpus", COLOR_TEXT),
            ("   durante 2 turnos, deteniendo su avance para huir.", COLOR_TEXT),
            ("", COLOR_TEXT),
            ("4. Brújula Antigua de Exploración:", COLOR_GOLD),
            ("   Oculta en una cueva. Al tomarla, te orienta con rumbo", COLOR_TEXT),
            ("   magnético hacia el oro o hacia la salida (Cueva 1).", COLOR_TEXT),
            ("", COLOR_TEXT),
            ("5. Mapa de 25 Cuevas Siempre Ganable:", COLOR_GOLD),
            ("   Cuadrícula 5x5 con ruta transitable garantizada.", COLOR_TEXT),
            ("", COLOR_TEXT),
            ("6. Sistema de Puntuación y Eficiencia:", COLOR_GOLD),
            ("   Gana puntos por explorar, oro, cazar y recursos.", COLOR_TEXT),
            ("   Bonus multiplicativo (hasta x2.5) por menos pasos.", COLOR_SUBTEXT),
        ]

        text_y = box_y + 38
        for linea, color in mecanicas_texto:
            if linea == "":
                text_y += 4
                continue
            txt_surf = self.font_small.render(linea, True, color)
            self.screen.blit(txt_surf, (box_x + 16, text_y))
            text_y += 16


if __name__ == "__main__":
    app = WumpusPygameApp()
    app.run()
