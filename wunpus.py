import random
import re
import math
import sys
from collections import deque
import pygame

COLOR_BG = (24, 24, 37)
COLOR_PANEL = (30, 30, 46)
COLOR_BORDER = (49, 50, 68)
COLOR_TEXT = (205, 214, 244)
COLOR_SUBTEXT = (166, 173, 200)
COLOR_GOLD = (249, 226, 175)
COLOR_RED = (243, 139, 168)
COLOR_GREEN = (166, 227, 161)
COLOR_CYAN = (137, 220, 235)
COLOR_PURPLE = (203, 166, 247)
COLOR_ORANGE = (250, 179, 135)

COLOR_TUNNEL = (45, 47, 65)
COLOR_TUNNEL_INNER = (65, 68, 95)
COLOR_PENT_FOG = (17, 17, 27)
COLOR_PENT_FOG_BORDER = (35, 36, 52)
COLOR_PENT_VISITED = (40, 42, 60)
COLOR_PENT_VISITED_BORDER = (75, 78, 108)
COLOR_PENT_PLAYER = (35, 60, 95)
COLOR_PENT_PLAYER_BORDER = (137, 180, 250)


class MundoWumpus:
    def __init__(self, tamano=4, callback_log=None):
        self.tamano = tamano
        self.callback_log = callback_log
        self.grafo = {}
        self.construir_grafo()
        
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

    def notificar(self, mensaje, tipo="normal"):
        if self.callback_log:
            self.callback_log(mensaje, tipo)
        else:
            print(mensaje)

    def construir_grafo(self):
        for x in range(self.tamano):
            for y in range(self.tamano):
                vecinos = []
                if x > 0: vecinos.append((x - 1, y))
                if x < self.tamano - 1: vecinos.append((x + 1, y))
                if y > 0: vecinos.append((x, y - 1))
                if y < self.tamano - 1: vecinos.append((x, y + 1))
                self.grafo[(x, y)] = vecinos

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
        return abs(self.pos_wumpus[0] - self.pos_jugador[0]) + abs(self.pos_wumpus[1] - self.pos_jugador[1])

    def inicializar_elementos(self):
        while True:
            habitaciones = list(self.grafo.keys())
            habitaciones.remove((0, 0))
            
            self.pos_wumpus = random.choice(habitaciones)
            habitaciones.remove(self.pos_wumpus)
            
            self.pos_oro = random.choice(habitaciones)
            habitaciones.remove(self.pos_oro)
            
            pos_bat = random.choice(habitaciones)
            self.pos_murcielagos = [pos_bat]
            habitaciones.remove(pos_bat)
            
            self.pos_derrumbe = random.choice(habitaciones)
            habitaciones.remove(self.pos_derrumbe)
            
            self.pos_pozos = [hab for hab in habitaciones if random.random() < 0.2]
            
            if self._existe_camino_seguro((0, 0), self.pos_oro):
                break

    def percibir(self):
        percepciones = []
        vecinos = self.grafo.get(self.pos_jugador, [])
        
        if self.wumpus_vivo and (self.pos_wumpus in vecinos or self.pos_jugador == self.pos_wumpus):
            percepciones.append("Hedor")
        if any(pozo in vecinos for pozo in self.pos_pozos):
            percepciones.append("Brisa")
        if any(bat in vecinos for bat in self.pos_murcielagos):
            percepciones.append("Aleteo")
        if self.pos_derrumbe in vecinos and not self.derrumbe_ocurrido:
            percepciones.append("Crujido")
        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            percepciones.append("Brillo")
            
        return percepciones

    def mover_wumpus_aleatorio(self):
        if not self.wumpus_vivo:
            return
            
        candidatos = [n for n in self.grafo.get(self.pos_wumpus, []) if n not in self.pos_pozos]
        if candidatos:
            self.pos_wumpus = random.choice(candidatos)
            self.notificar("¡Pasos pesados en la oscuridad! El Wumpus ha cambiado de cueva.", "alerta")
            if self.pos_wumpus == self.pos_jugador:
                self.notificar("¡¡EL WUMPUS HA ENTRADO EN TU HABITACIÓN!!", "peligro")
                self.verificar_estado()

    def cazar_jugador(self):
        if not self.wumpus_vivo or not self.modo_caceria:
            return

        camino = self._obtener_camino_wumpus()
        if camino and len(camino) >= 2:
            siguiente_paso = camino[1]
            self.pos_wumpus = siguiente_paso
            distancia_restante = len(camino) - 2
            
            if self.pos_wumpus == self.pos_jugador:
                self.notificar("¡¡EL WUMPUS TE ALCANZA Y TE DEVORA DE UN BOCADO!!", "peligro")
                self.verificar_estado()
            else:
                sufijo = "es" if distancia_restante > 1 else ""
                self.notificar(f"¡Garras en la piedra! El Wumpus acecha a {distancia_restante} cueva{sufijo}.", "alerta")
        else:
            self.notificar("Rugido lejano: el Wumpus busca otra ruta.", "alerta")
            self.mover_wumpus_aleatorio()

    def activar_derrumbe(self):
        if self.derrumbe_ocurrido:
            return
            
        self.derrumbe_ocurrido = True
        self.notificar("¡CRRAAAACK! ¡Derrumbe violento de rocas en el techo!", "derrumbe")
        
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
                self.notificar(f"¡Rocas sellan el túnel entre {pos} y {v}!", "derrumbe")
                break
            else:
                self.grafo[pos].append(v)
                self.grafo[v].append(pos)
                
        if not tunel_bloqueado:
            self.notificar("¡Rocas se desploman rozándote! Logras esquivarlas.", "derrumbe")

    def mover(self, nueva_pos):
        if nueva_pos in self.grafo.get(self.pos_jugador, []):
            self.pos_jugador = nueva_pos
            self.habitaciones_visitadas.add(nueva_pos)
            self.notificar(f"Te has movido a la cueva {self.pos_jugador}", "movimiento")
            
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
                    sufijo = "es" if dist > 1 else ""
                    self.notificar(f"Vibración en el suelo: el Wumpus está a {dist} cueva{sufijo}...", "alerta")
            return True
        else:
            self.notificar(f"No hay túnel directo hacia {nueva_pos}", "error")
            return False

    def verificar_murcielagos(self):
        if self.pos_jugador in self.pos_murcielagos:
            self.notificar("¡SWOOOSH! ¡Murciélagos gigantes te llevan por el aire!", "murcielago")
            posibles = [h for h in self.grafo.keys() if h != self.pos_jugador]
            destino = random.choice(posibles)
            self.notificar(f"¡Te dejan caer en la cueva {destino}!", "murcielago")
            self.pos_jugador = destino
            self.habitaciones_visitadas.add(destino)
            
            libres = [h for h in posibles if h != destino and h != (0, 0)]
            self.pos_murcielagos = [random.choice(libres)]
            self.verificar_estado()

    def verificar_estado(self):
        if self.pos_jugador in self.pos_pozos:
            self.notificar("¡¡AAAAAAHH!! Caíste en un pozo infinito. Fin del juego.", "muerte")
            self.vivo = False
        elif self.pos_jugador == self.pos_wumpus and self.wumpus_vivo:
            self.notificar("¡¡CRUNCH!! El Wumpus te ha devorado. Fin del juego.", "muerte")
            self.vivo = False

    def lanzar_piedra(self, objetivo):
        if self.piedras <= 0:
            self.notificar("Ya no te quedan piedras en la bolsa.", "error")
            return False

        if objetivo not in self.grafo.get(self.pos_jugador, []):
            self.notificar(f"Solo puedes lanzar piedras a cuevas adyacentes: {self.grafo.get(self.pos_jugador, [])}", "error")
            return False

        self.piedras -= 1
        self.notificar(f"Lanzas una piedra hacia {objetivo}...", "accion")

        if objetivo in self.pos_pozos:
            self.notificar("  > ... ¡SPLASH! Eco distante cayendo a un pozo sin fondo.", "pista")
        elif objetivo == self.pos_wumpus and self.wumpus_vivo:
            self.notificar("  > ... ¡¡ROAAAR!! Golpeaste al Wumpus y huye enfurecido.", "alerta")
            self.mover_wumpus_aleatorio()
        elif objetivo in self.pos_murcielagos:
            self.notificar("  > ... ¡¡CHIIIRP!! Chillidos y aleteo de murciélagos gigantes.", "pista")
        elif objetivo == self.pos_derrumbe and not self.derrumbe_ocurrido:
            self.notificar("  > ... ¡CRAC! Caen piedras del techo. Es una zona inestable.", "pista")
        else:
            self.notificar("  > ... ¡Clac-clac! Rueda tranquilamente por piedra sólida.", "pista")

        if self.modo_caceria and self.wumpus_vivo:
            self.notificar("  > El eco despista al Wumpus y retrasa su persecución.", "accion")
            self.turnos_caceria = max(0, self.turnos_caceria - 1)

        return True

    def agarrar(self):
        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            self.tiene_oro = True
            self.notificar("¡HAS COGIDO EL ORO! 💰 Regresa a (0, 0) para escapar.", "victoria")
            
            if self.wumpus_vivo:
                self.modo_caceria = True
                self.notificar("¡¡ROAAAR!! El Wumpus huele el oro e INICIA CACERÍA.", "alerta")
            return True
        elif self.tiene_oro:
            self.notificar("Ya tienes el oro en tu mochila.", "error")
            return False
        else:
            self.notificar("No hay nada que agarrar en esta cueva.", "error")
            return False

    def disparar(self, objetivo):
        if self.flechas <= 0:
            self.notificar("Ya no te quedan flechas.", "error")
            return False

        if objetivo == self.pos_jugador:
            self.notificar("No puedes disparar a tu propia cueva.", "error")
            return False

        x_orig, y_orig = self.pos_jugador
        x_dest, y_dest = objetivo

        dx = x_dest - x_orig
        dy = y_dest - y_orig

        if dx != 0 and dy != 0:
            self.notificar("Solo puedes disparar en línea recta (N, S, E, O).", "error")
            return False

        paso_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        paso_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

        self.flechas -= 1
        self.notificar(f"¡La flecha silba en dirección ({paso_x:+d}, {paso_y:+d})!", "accion")

        cur_x, cur_y = x_orig + paso_x, y_orig + paso_y
        impacto = False

        while 0 <= cur_x < self.tamano and 0 <= cur_y < self.tamano:
            if (cur_x, cur_y) == self.pos_wumpus and self.wumpus_vivo:
                self.wumpus_vivo = False
                impacto = True
                self.notificar(f"¡¡GRITO ESCALOFRIANTE en ({cur_x}, {cur_y})!! Has matado al Wumpus.", "victoria")
                if self.modo_caceria:
                    self.modo_caceria = False
                    self.notificar("La cueva queda en silencio. La cacería ha terminado.", "victoria")
                break
            cur_x += paso_x
            cur_y += paso_y

        if not impacto:
            self.notificar("¡Clac! La flecha se pierde en la oscuridad sin acertar.", "alerta")
            if self.wumpus_vivo and not self.modo_caceria:
                self.mover_wumpus_aleatorio()

        return True


class WumpusPygameApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.width = 1080
        self.height = 720
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("🏹 El Mundo del Wumpus - Mapa Pentagonal")

        self.clock = pygame.time.Clock()
        self.running = True

        self.font_title = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 22, bold=True)
        self.font_bold = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 15, bold=True)
        self.font_normal = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 13)
        self.font_small = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 11)
        self.font_emoji = pygame.font.SysFont(["segoe ui emoji", "segoe ui symbol", "arial"], 22)
        self.font_emoji_large = pygame.font.SysFont(["segoe ui emoji", "segoe ui symbol", "arial"], 28)

        self.log_mensajes = []
        self.modo_accion = "mover"
        self.juego = None
        self.pentagonos = {}
        self.radius = 46

        self._calcular_geometria_pentagonos()
        self.nueva_partida()

    def agregar_log(self, mensaje, tipo="normal"):
        self.log_mensajes.append((mensaje, tipo))
        if len(self.log_mensajes) > 12:
            self.log_mensajes.pop(0)

    def nueva_partida(self):
        self.log_mensajes.clear()
        self.juego = MundoWumpus(callback_log=self.agregar_log)
        self.modo_accion = "mover"
        self.agregar_log("⚔️ ¡Nueva expedición iniciada en la cueva!", "victoria")
        self.agregar_log("Encuentra el oro y regresa con vida a (0, 0).", "normal")

    def _calcular_geometria_pentagonos(self):
        self.pentagonos.clear()
        offset_x = 105
        offset_y = 120
        spacing_x = 142
        spacing_y = 142

        for x in range(4):
            for y in range(4):
                cx = offset_x + x * spacing_x
                cy = offset_y + (3 - y) * spacing_y
                vertices = []
                for k in range(5):
                    angle = -math.pi / 2 + k * (2 * math.pi / 5)
                    vx = cx + self.radius * math.cos(angle)
                    vy = cy + self.radius * math.sin(angle)
                    vertices.append((vx, vy))
                self.pentagonos[(x, y)] = {
                    "centro": (cx, cy),
                    "vertices": vertices
                }

    def obtener_cueva_bajo_cursor(self, mx, my):
        for pos, datos in self.pentagonos.items():
            cx, cy = datos["centro"]
            dist_sq = (mx - cx) ** 2 + (my - cy) ** 2
            if dist_sq <= self.radius ** 2:
                return pos
        return None

    def interactuar_con_cueva(self, objetivo):
        if not self.juego.vivo:
            return

        if self.modo_accion == "mover":
            if objetivo == self.juego.pos_jugador:
                if self.juego.pos_jugador == self.juego.pos_oro and not self.juego.tiene_oro:
                    self.juego.agarrar()
            elif objetivo in self.juego.grafo.get(self.juego.pos_jugador, []):
                self.juego.mover(objetivo)
            else:
                self.agregar_log("No hay túnel hacia esa cueva.", "error")

        elif self.modo_accion == "disparar":
            if self.juego.disparar(objetivo):
                self.modo_accion = "mover"

        elif self.modo_accion == "lanzar":
            if self.juego.lanzar_piedra(objetivo):
                self.modo_accion = "mover"

    def mover_direccion(self, dx, dy):
        if not self.juego.vivo:
            return
        x, y = self.juego.pos_jugador
        objetivo = (x + dx, y + dy)
        self.interactuar_con_cueva(objetivo)

    def run(self):
        while self.running:
            self.clock.tick(60)
            self._handle_events()
            self._render()

        pygame.quit()
        sys.exit()

    def _handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        cueva_hover = self.obtener_cueva_bajo_cursor(*mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Comprobar clics en botones de acción
                if self.btn_disparar_rect.collidepoint(event.pos):
                    if self.juego.flechas > 0 and self.juego.vivo:
                        self.modo_accion = "disparar" if self.modo_accion != "disparar" else "mover"
                        if self.modo_accion == "disparar":
                            self.agregar_log("Modo DISPARAR: Haz clic en una cueva contigua.", "alerta")
                    else:
                        self.agregar_log("No tienes flechas disponibles.", "error")

                elif self.btn_lanzar_rect.collidepoint(event.pos):
                    if self.juego.piedras > 0 and self.juego.vivo:
                        self.modo_accion = "lanzar" if self.modo_accion != "lanzar" else "mover"
                        if self.modo_accion == "lanzar":
                            self.agregar_log("Modo PIEDRA: Haz clic en una cueva contigua para escuchar.", "alerta")
                    else:
                        self.agregar_log("No te quedan piedras.", "error")

                elif self.btn_agarrar_rect.collidepoint(event.pos):
                    if self.juego.vivo:
                        self.juego.agarrar()

                elif self.btn_reiniciar_rect.collidepoint(event.pos):
                    self.nueva_partida()

                # Comprobar clics en el mapa pentagonal
                elif cueva_hover is not None:
                    self.interactuar_con_cueva(cueva_hover)

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_w, pygame.K_UP):
                    self.mover_direccion(0, 1)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.mover_direccion(0, -1)
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    self.mover_direccion(-1, 0)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.mover_direccion(1, 0)
                elif event.key == pygame.K_f:
                    if self.juego.flechas > 0 and self.juego.vivo:
                        self.modo_accion = "disparar" if self.modo_accion != "disparar" else "mover"
                elif event.key == pygame.K_p:
                    if self.juego.piedras > 0 and self.juego.vivo:
                        self.modo_accion = "lanzar" if self.modo_accion != "lanzar" else "mover"
                elif event.key in (pygame.K_g, pygame.K_SPACE):
                    if self.juego.vivo:
                        self.juego.agarrar()
                elif event.key == pygame.K_r:
                    self.nueva_partida()
                elif event.key == pygame.K_ESCAPE:
                    self.modo_accion = "mover"

    def _render(self):
        self.screen.fill(COLOR_BG)
        self._dibujar_mapa_pentagonal()
        self._dibujar_panel_derecho()
        self._dibujar_estado_final()
        pygame.display.flip()

    def _dibujar_mapa_pentagonal(self):
        mouse_pos = pygame.mouse.get_pos()
        cueva_hover = self.obtener_cueva_bajo_cursor(*mouse_pos)
        vecinos_jugador = self.juego.grafo.get(self.juego.pos_jugador, [])
        partida_terminada = (not self.juego.vivo) or (self.juego.pos_jugador == (0, 0) and self.juego.tiene_oro)

        # 1. Dibujar túneles (aristas del grafo no dirigido)
        trazados = set()
        for u, vecinos in self.juego.grafo.items():
            for v in vecinos:
                arista = (min(u, v), max(u, v))
                if arista not in trazados:
                    trazados.add(arista)
                    p1 = self.pentagonos[u]["centro"]
                    p2 = self.pentagonos[v]["centro"]
                    pygame.draw.line(self.screen, COLOR_TUNNEL, p1, p2, 10)
                    pygame.draw.line(self.screen, COLOR_TUNNEL_INNER, p1, p2, 6)

        # Dibujar túneles derrumbados / bloqueados
        for u, v in self.juego.bloqueos:
            p1 = self.pentagonos[u]["centro"]
            p2 = self.pentagonos[v]["centro"]
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            pygame.draw.circle(self.screen, (50, 20, 20), (int(mid_x), int(mid_y)), 15)
            pygame.draw.line(self.screen, COLOR_RED, (mid_x - 8, mid_y - 8), (mid_x + 8, mid_y + 8), 3)
            pygame.draw.line(self.screen, COLOR_RED, (mid_x - 8, mid_y + 8), (mid_x + 8, mid_y - 8), 3)

        # 2. Dibujar habitaciones pentagonales
        time_ms = pygame.time.get_ticks()
        for pos, datos in self.pentagonos.items():
            vertices = datos["vertices"]
            cx, cy = datos["centro"]
            es_jugador = (pos == self.juego.pos_jugador)
            es_visitada = (pos in self.juego.habitaciones_visitadas)
            es_vecino = (pos in vecinos_jugador)

            # Colores base según estado
            if es_jugador:
                color_fill = COLOR_PENT_PLAYER
                color_border = COLOR_PENT_PLAYER_BORDER
                pulse = 3 + int(2 * math.sin(time_ms * 0.006))
                border_width = 3 + pulse
            elif es_visitada or partida_terminada:
                color_fill = COLOR_PENT_VISITED
                color_border = COLOR_PENT_VISITED_BORDER
                border_width = 2
            else:
                color_fill = COLOR_PENT_FOG
                color_border = COLOR_PENT_FOG_BORDER
                border_width = 2

            # Resaltar si el cursor está encima y es vecina
            if cueva_hover == pos and es_vecino and self.juego.vivo:
                if self.modo_accion == "mover":
                    color_border = COLOR_CYAN
                elif self.modo_accion == "disparar":
                    color_border = COLOR_RED
                elif self.modo_accion == "lanzar":
                    color_border = COLOR_ORANGE
                border_width = 4

            # Relleno y borde pentagonal
            pygame.draw.polygon(self.screen, color_fill, vertices)
            pygame.draw.polygon(self.screen, color_border, vertices, border_width)

            # Coordenadas pequeñas de la cueva
            txt_coord = self.font_small.render(f"{pos[0]},{pos[1]}", True, (90, 95, 125))
            self.screen.blit(txt_coord, (cx - txt_coord.get_width() // 2, cy - 36))

            # Contenido dentro del pentágono
            if es_jugador:
                avatar = "🤠💰" if self.juego.tiene_oro else "🧙‍♂️"
                txt_avatar = self.font_emoji_large.render(avatar, True, COLOR_TEXT)
                self.screen.blit(txt_avatar, (cx - txt_avatar.get_width() // 2, cy - txt_avatar.get_height() // 2 - 2))

                # Percepciones dentro de la cueva del jugador
                percepciones = self.juego.percibir()
                iconos = []
                if "Hedor" in percepciones: iconos.append("🦨")
                if "Brisa" in percepciones: iconos.append("💨")
                if "Brillo" in percepciones: iconos.append("✨")
                if "Aleteo" in percepciones: iconos.append("🦇")
                if "Crujido" in percepciones: iconos.append("💥")

                if iconos:
                    txt_perc = self.font_small.render(" ".join(iconos), True, COLOR_GOLD)
                    self.screen.blit(txt_perc, (cx - txt_perc.get_width() // 2, cy + 16))

            elif partida_terminada:
                # Revelación de toda la cueva
                if pos == self.juego.pos_wumpus:
                    txt_item = self.font_emoji.render("👹" if self.juego.wumpus_vivo else "💀", True, COLOR_RED)
                    lbl = self.font_small.render("WUMPUS", True, COLOR_RED)
                elif pos == self.juego.pos_oro:
                    txt_item = self.font_emoji.render("💰", True, COLOR_GOLD)
                    lbl = self.font_small.render("ORO", True, COLOR_GOLD)
                elif pos in self.juego.pos_pozos:
                    txt_item = self.font_emoji.render("🕳️", True, COLOR_CYAN)
                    lbl = self.font_small.render("POZO", True, COLOR_CYAN)
                elif pos in self.juego.pos_murcielagos:
                    txt_item = self.font_emoji.render("🦇", True, COLOR_PURPLE)
                    lbl = self.font_small.render("MURCIÉLAGOS", True, COLOR_PURPLE)
                elif pos == self.juego.pos_derrumbe:
                    txt_item = self.font_emoji.render("🪨", True, COLOR_ORANGE)
                    lbl = self.font_small.render("DERRUMBE", True, COLOR_ORANGE)
                else:
                    txt_item = self.font_bold.render("·", True, COLOR_SUBTEXT)
                    lbl = self.font_small.render("SEGURO", True, (80, 85, 110))

                self.screen.blit(txt_item, (cx - txt_item.get_width() // 2, cy - 18))
                self.screen.blit(lbl, (cx - lbl.get_width() // 2, cy + 12))

            else:
                if not es_visitada:
                    txt_fog = self.font_bold.render("?", True, (65, 68, 90))
                    self.screen.blit(txt_fog, (cx - txt_fog.get_width() // 2, cy - txt_fog.get_height() // 2))

        # Ejes y Leyenda inferior del mapa
        txt_mapa_guia = self.font_small.render("⬟ Mapa Pentagonal: Las cuevas son pentágonos y las líneas son los túneles", True, COLOR_SUBTEXT)
        self.screen.blit(txt_mapa_guia, (75, self.height - 35))

    def _dibujar_panel_derecho(self):
        panel_x = 640
        panel_w = 415

        # 1. Cabecera y Título
        txt_titulo = self.font_title.render("🏹 EL MUNDO DEL WUMPUS", True, COLOR_GOLD)
        self.screen.blit(txt_titulo, (panel_x, 18))
        txt_sub = self.font_small.render("Exploración táctica y supervivencia en cueva pentagonal", True, COLOR_SUBTEXT)
        self.screen.blit(txt_sub, (panel_x, 48))

        # 2. Banner de Cacería Activa
        banner_y = 74
        if self.juego.modo_caceria and self.juego.wumpus_vivo:
            dist = self.juego._distancia_al_jugador()
            sufijo = "es" if dist > 1 else ""
            banner_rect = pygame.Rect(panel_x, banner_y, panel_w, 36)
            pygame.draw.rect(self.screen, COLOR_RED, banner_rect, border_radius=6)
            txt_cac = self.font_bold.render(f"🚨 ¡¡WUMPUS EN CACERÍA!! Acechando a {dist} cueva{sufijo}", True, (20, 20, 30))
            self.screen.blit(txt_cac, (panel_x + 14, banner_y + 8))
            inv_y = banner_y + 46
        else:
            inv_y = banner_y

        # 3. Tarjeta de Inventario y Estado
        inv_rect = pygame.Rect(panel_x, inv_y, panel_w, 88)
        pygame.draw.rect(self.screen, COLOR_PANEL, inv_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, inv_rect, 1, border_radius=8)

        txt_inv_titulo = self.font_bold.render("🎒 Inventario y Explorador", True, COLOR_GOLD)
        self.screen.blit(txt_inv_titulo, (panel_x + 14, inv_y + 10))

        txt_fl = self.font_normal.render(f"🏹 Flechas: {self.juego.flechas}", True, COLOR_TEXT)
        self.screen.blit(txt_fl, (panel_x + 16, inv_y + 36))

        txt_pd = self.font_normal.render(f"🪨 Piedras: {self.juego.piedras}", True, COLOR_TEXT)
        self.screen.blit(txt_pd, (panel_x + 160, inv_y + 36))

        oro_str = "¡CONSEGUIDO! 🏆" if self.juego.tiene_oro else "No"
        txt_oro = self.font_normal.render(f"💰 Oro: {oro_str}", True, COLOR_GOLD if self.juego.tiene_oro else COLOR_TEXT)
        self.screen.blit(txt_oro, (panel_x + 16, inv_y + 60))

        txt_pos = self.font_normal.render(f"📍 Cueva actual: {self.juego.pos_jugador}", True, COLOR_CYAN)
        self.screen.blit(txt_pos, (panel_x + 160, inv_y + 60))

        # 4. Percepciones Sensoriales
        perc_y = inv_y + 98
        perc_rect = pygame.Rect(panel_x, perc_y, panel_w, 62)
        pygame.draw.rect(self.screen, COLOR_PANEL, perc_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, perc_rect, 1, border_radius=8)

        txt_per_tit = self.font_bold.render("👂 Percepciones en esta cueva:", True, COLOR_TEXT)
        self.screen.blit(txt_per_tit, (panel_x + 14, perc_y + 10))

        percepciones = self.juego.percibir()
        if percepciones:
            txt_percs = self.font_bold.render("  •  " + "   •  ".join(percepciones), True, COLOR_GOLD)
        else:
            txt_percs = self.font_normal.render("Silencio y calma. No percibes nada inusual.", True, (110, 115, 140))
        self.screen.blit(txt_percs, (panel_x + 14, perc_y + 34))

        # 5. Botones de Acción
        btn_y = perc_y + 72
        self.btn_disparar_rect = pygame.Rect(panel_x, btn_y, 130, 36)
        self.btn_lanzar_rect = pygame.Rect(panel_x + 140, btn_y, 130, 36)
        self.btn_agarrar_rect = pygame.Rect(panel_x + 280, btn_y, 135, 36)
        self.btn_reiniciar_rect = pygame.Rect(panel_x, btn_y + 44, panel_w, 32)

        # Colores dinámicos según modo
        c_disp = COLOR_RED if self.modo_accion == "disparar" else (60, 65, 85)
        c_lanz = COLOR_ORANGE if self.modo_accion == "lanzar" else (60, 65, 85)
        c_agar = COLOR_GREEN if self.juego.pos_jugador == self.juego.pos_oro and not self.juego.tiene_oro else (50, 75, 60)

        pygame.draw.rect(self.screen, c_disp, self.btn_disparar_rect, border_radius=6)
        pygame.draw.rect(self.screen, c_lanz, self.btn_lanzar_rect, border_radius=6)
        pygame.draw.rect(self.screen, c_agar, self.btn_agarrar_rect, border_radius=6)
        pygame.draw.rect(self.screen, (45, 48, 65), self.btn_reiniciar_rect, border_radius=6)

        txt_b_disp = self.font_bold.render("🏹 Disparar (F)", True, (20, 20, 30) if self.modo_accion == "disparar" else COLOR_TEXT)
        txt_b_lanz = self.font_bold.render("🪨 Piedra (P)", True, (20, 20, 30) if self.modo_accion == "lanzar" else COLOR_TEXT)
        txt_b_agar = self.font_bold.render("💰 Agarrar (G)", True, (20, 20, 30) if c_agar == COLOR_GREEN else COLOR_TEXT)
        txt_b_rein = self.font_bold.render("🔄 Nueva Cueva Aleatoria (R)", True, COLOR_TEXT)

        self.screen.blit(txt_b_disp, (panel_x + 14, btn_y + 9))
        self.screen.blit(txt_b_lanz, (panel_x + 154, btn_y + 9))
        self.screen.blit(txt_b_agar, (panel_x + 292, btn_y + 9))
        self.screen.blit(txt_b_rein, (panel_x + 105, btn_y + 51))

        # 6. Bitácora de Eventos
        log_y = btn_y + 88
        log_h = self.height - log_y - 45
        log_rect = pygame.Rect(panel_x, log_y, panel_w, log_h)
        pygame.draw.rect(self.screen, (17, 17, 27), log_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, log_rect, 1, border_radius=8)

        txt_log_tit = self.font_bold.render("📜 Bitácora de la Aventura", True, COLOR_GOLD)
        self.screen.blit(txt_log_tit, (panel_x + 14, log_y + 8))

        line_y = log_y + 32
        for msg, tipo in self.log_mensajes[-7:]:
            if tipo == "peligro" or tipo == "muerte":
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
            line_y += 20

        # 7. Controles y atajos al pie
        txt_ctrls = self.font_small.render("Atajos: WASD / Flechas para mover | Clic para interactuar | Esc para cancelar", True, COLOR_SUBTEXT)
        self.screen.blit(txt_ctrls, (panel_x, self.height - 28))

    def _dibujar_estado_final(self):
        if self.juego.pos_jugador == (0, 0) and self.juego.tiene_oro:
            banner_rect = pygame.Rect(60, 20, 520, 50)
            pygame.draw.rect(self.screen, (30, 80, 50), banner_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_GREEN, banner_rect, 2, border_radius=8)
            txt_vic = self.font_bold.render("🏆 ¡¡HAS ESCAPADO CON EL ORO!! ¡¡VICTORIA!! (Pulsa R)", True, COLOR_GREEN)
            self.screen.blit(txt_vic, (banner_rect.centerx - txt_vic.get_width() // 2, banner_rect.centery - txt_vic.get_height() // 2))

        elif not self.juego.vivo:
            banner_rect = pygame.Rect(60, 20, 520, 50)
            pygame.draw.rect(self.screen, (70, 20, 30), banner_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_RED, banner_rect, 2, border_radius=8)
            txt_der = self.font_bold.render("💀 HAS MUERTO EN LA CUEVA. Cueva revelada. (Pulsa R)", True, COLOR_RED)
            self.screen.blit(txt_der, (banner_rect.centerx - txt_der.get_width() // 2, banner_rect.centery - txt_der.get_height() // 2))


def main():
    app = WumpusPygameApp()
    app.run()


if __name__ == "__main__":
    main()