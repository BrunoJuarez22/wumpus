import random
import math
import sys
from collections import deque, defaultdict
import pygame

COLOR_BG = (20, 20, 32)
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

COLOR_FACE = (26, 27, 42)
COLOR_FACE_BORDER = (38, 40, 60)
COLOR_TUNNEL = (50, 53, 76)
COLOR_TUNNEL_INNER = (72, 76, 108)

COLOR_NODE_FOG = (16, 16, 26)
COLOR_NODE_FOG_BORDER = (35, 36, 52)
COLOR_NODE_VISITED = (40, 43, 62)
COLOR_NODE_VISITED_BORDER = (80, 84, 118)
COLOR_NODE_PLAYER = (35, 65, 105)
COLOR_NODE_PLAYER_BORDER = (137, 180, 250)


class MundoWumpusDodecaedro:
    def __init__(self, callback_log=None):
        self.callback_log = callback_log
        self.grafo = defaultdict(list)
        self.caras_pentagonales = []
        self.construir_grafo_dodecaedro()
        
        self.pos_jugador = 0
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

    def construir_grafo_dodecaedro(self):
        self.grafo.clear()
        
        # Central pentagon: 0, 1, 2, 3, 4
        for i in range(5):
            self._agregar_arista(i, (i + 1) % 5)
            self._agregar_arista(i, i + 5)
            
        # Middle ring 1 (5..9) connects to Middle ring 2 (10..14)
        for i in range(5):
            r1 = i + 5
            r2_a = 10 + i
            r2_b = 10 + (i - 1) % 5
            self._agregar_arista(r1, r2_a)
            self._agregar_arista(r1, r2_b)
            
        # Middle ring 2 (10..14) connects to Outer ring (15..19)
        for i in range(5):
            self._agregar_arista(10 + i, 15 + i)
            
        # Outer pentagon: 15, 16, 17, 18, 19
        for i in range(5):
            self._agregar_arista(15 + i, 15 + (i + 1) % 5)
            
        # Definir las 11 caras pentagonales visibles
        self.caras_pentagonales = []
        # Cara 0 (Centro)
        self.caras_pentagonales.append([0, 1, 2, 3, 4])
        # Caras 1..5 (Anillo medio A)
        for i in range(5):
            self.caras_pentagonales.append([i, (i + 1) % 5, 5 + (i + 1) % 5, 10 + i, 5 + i])
        # Caras 6..10 (Anillo medio B)
        for i in range(5):
            self.caras_pentagonales.append([10 + i, 15 + i, 15 + (i + 1) % 5, 10 + (i + 1) % 5, 5 + (i + 1) % 5])

    def _agregar_arista(self, u, v):
        if v not in self.grafo[u]:
            self.grafo[u].append(v)
        if u not in self.grafo[v]:
            self.grafo[v].append(u)

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
        return 3

    def inicializar_elementos(self):
        while True:
            cuevas = list(range(20))
            cuevas.remove(0) # El inicio siempre es seguro en la cueva 0
            
            self.pos_wumpus = random.choice(cuevas)
            cuevas.remove(self.pos_wumpus)
            
            self.pos_oro = random.choice(cuevas)
            cuevas.remove(self.pos_oro)
            
            pos_bat = random.choice(cuevas)
            self.pos_murcielagos = [pos_bat]
            cuevas.remove(pos_bat)
            
            self.pos_derrumbe = random.choice(cuevas)
            cuevas.remove(self.pos_derrumbe)
            
            # Colocar 3 pozos en cuevas restantes
            self.pos_pozos = random.sample(cuevas, 3)
            
            # Validar que exista camino transitable hasta el oro
            if self._existe_camino_seguro(0, self.pos_oro):
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
            self.notificar("¡Pasos pesados en la oscuridad! El Wumpus se ha movido.", "alerta")
            if self.pos_wumpus == self.pos_jugador:
                self.notificar("¡¡EL WUMPUS HA ENTRADO EN TU CUEVA!!", "peligro")
                self.verificar_estado()

    def cazar_jugador(self):
        if not self.wumpus_vivo or not self.modo_caceria:
            return

        camino = self._obtener_camino_wumpus()
        if camino and len(camino) >= 2:
            siguiente_paso = camino[1]
            self.pos_wumpus = siguiente_paso
            distancia = len(camino) - 2
            
            if self.pos_wumpus == self.pos_jugador:
                self.notificar("¡¡EL WUMPUS TE ALCANZA Y TE DEVORA DE UN BOCADO!!", "peligro")
                self.verificar_estado()
            else:
                sufijo = "s" if distancia > 1 else ""
                self.notificar(f"¡Garras en la piedra! El Wumpus acecha a {distancia} cueva{sufijo}.", "alerta")
        else:
            self.notificar("Rugido lejano: el Wumpus busca otra ruta.", "alerta")
            self.mover_wumpus_aleatorio()

    def activar_derrumbe(self):
        if self.derrumbe_ocurrido:
            return
            
        self.derrumbe_ocurrido = True
        self.notificar("¡CRRAAAACK! ¡Derrumbe violento de rocas en un túnel!", "derrumbe")
        
        pos = self.pos_jugador
        vecinos = list(self.grafo.get(pos, []))
        random.shuffle(vecinos)
        
        tunel_bloqueado = False
        for v in vecinos:
            self.grafo[pos].remove(v)
            self.grafo[v].remove(pos)
            
            camino_inicio = self._existe_camino_seguro(self.pos_jugador, 0)
            camino_oro = True if self.tiene_oro else self._existe_camino_seguro(self.pos_jugador, self.pos_oro)
            
            if camino_inicio and camino_oro:
                tunel_bloqueado = True
                self.bloqueos.add((min(pos, v), max(pos, v)))
                self.notificar(f"¡Rocas gigantes sellan el túnel entre la cueva {pos} y {v}!", "derrumbe")
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
                    sufijo = "s" if dist > 1 else ""
                    self.notificar(f"Vibración en el suelo: el Wumpus está a {dist} cueva{sufijo}...", "alerta")
            return True
        else:
            self.notificar(f"No hay túnel directo hacia la cueva {nueva_pos}", "error")
            return False

    def verificar_murcielagos(self):
        if self.pos_jugador in self.pos_murcielagos:
            self.notificar("¡SWOOOSH! ¡Murciélagos gigantes te llevan por el aire!", "murcielago")
            posibles = [h for h in range(20) if h != self.pos_jugador]
            destino = random.choice(posibles)
            self.notificar(f"¡Te dejan caer en la cueva {destino}!", "murcielago")
            self.pos_jugador = destino
            self.habitaciones_visitadas.add(destino)
            
            libres = [h for h in posibles if h != destino and h != 0]
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
            self.notificar(f"Solo puedes lanzar piedras a cuevas conectadas: {self.grafo.get(self.pos_jugador, [])}", "error")
            return False

        self.piedras -= 1
        self.notificar(f"Lanzas una piedra hacia la cueva {objetivo}...", "accion")

        if objetivo in self.pos_pozos:
            self.notificar("  > ... ¡SPLASH! Eco distante cayendo al pozo.", "pista")
        elif objetivo == self.pos_wumpus and self.wumpus_vivo:
            self.notificar("  > ... ¡¡ROAAAR!! Golpeaste al Wumpus y huye enfurecido.", "alerta")
            self.mover_wumpus_aleatorio()
        elif objetivo in self.pos_murcielagos:
            self.notificar("  > ... ¡¡CHIIIRP!! Chillidos y aleteo de murciélagos gigantes.", "pista")
        elif objetivo == self.pos_derrumbe and not self.derrumbe_ocurrido:
            self.notificar("  > ... ¡CRAC! Caen piedras del techo. Cueva inestable.", "pista")
        else:
            self.notificar("  > ... ¡Clac-clac! Rueda tranquilamente por piedra sólida.", "pista")

        if self.modo_caceria and self.wumpus_vivo:
            self.notificar("  > El eco despista al Wumpus y retrasa su persecución.", "accion")
            self.turnos_caceria = max(0, self.turnos_caceria - 1)

        return True

    def agarrar(self):
        if self.pos_jugador == self.pos_oro and not self.tiene_oro:
            self.tiene_oro = True
            self.notificar("¡HAS COGIDO EL ORO! 💰 Regresa a la Cueva 0 para escapar.", "victoria")
            
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

        if objetivo not in self.grafo.get(self.pos_jugador, []):
            self.notificar(f"Solo puedes disparar a través de un túnel conectado: {self.grafo.get(self.pos_jugador, [])}", "error")
            return False

        self.flechas -= 1
        self.notificar(f"¡La flecha silba hacia la cueva {objetivo}!", "accion")

        # La flecha viaja hacia la cueva y puede atravesar
        camino_flecha = [objetivo]
        # Continuar la flecha 1 cueva más si está alineada
        vecinos_dest = [v for v in self.grafo.get(objetivo, []) if v != self.pos_jugador]
        if vecinos_dest:
            camino_flecha.append(random.choice(vecinos_dest))

        impacto = False
        for cueva_f in camino_flecha:
            if cueva_f == self.pos_wumpus and self.wumpus_vivo:
                self.wumpus_vivo = False
                impacto = True
                self.notificar(f"¡¡GRITO ESCALOFRIANTE en la cueva {cueva_f}!! Has matado al Wumpus.", "victoria")
                if self.modo_caceria:
                    self.modo_caceria = False
                    self.notificar("La cueva queda en silencio. La cacería ha terminado.", "victoria")
                break

        if not impacto:
            self.notificar("¡Clac! La flecha se estrella contra una pared sin acertar.", "alerta")
            if self.wumpus_vivo and not self.modo_caceria:
                self.mover_wumpus_aleatorio()

        return True


class WumpusPygameApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.width = 1100
        self.height = 740
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("🏹 El Mundo del Wumpus - Grafo de Pentágonos Pegados")

        self.clock = pygame.time.Clock()
        self.running = True

        self.font_title = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 20, bold=True)
        self.font_bold = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 14, bold=True)
        self.font_btn = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 13, bold=True)
        self.font_normal = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 13)
        self.font_small = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], 11)
        self.font_emoji = pygame.font.SysFont(["segoe ui emoji", "segoe ui symbol", "arial"], 20)
        self.font_emoji_large = pygame.font.SysFont(["segoe ui emoji", "segoe ui symbol", "arial"], 26)

        self.log_mensajes = []
        self.modo_accion = "mover"
        self.juego = None
        self.coords_cuevas = {}
        self.radio_cueva = 22

        self.mostrar_menu_mecanicas = False
        self.btn_mecanicas_rect = None
        self.btn_cerrar_mecanicas_rect = None
        self.dropdown_mecanicas_rect = None

        self._calcular_coordenadas_vertices()
        self.nueva_partida()

    def agregar_log(self, mensaje, tipo="normal"):
        self.log_mensajes.append((mensaje, tipo))
        if len(self.log_mensajes) > 12:
            self.log_mensajes.pop(0)

    def nueva_partida(self):
        self.log_mensajes.clear()
        self.juego = MundoWumpusDodecaedro(callback_log=self.agregar_log)
        self.modo_accion = "mover"
        self.agregar_log("⚔️ ¡Nueva expedición en la red pentagonal!", "victoria")
        self.agregar_log("Las aristas son túneles y los vértices son las 20 cuevas.", "normal")
        self.agregar_log("Encuentra el oro y regresa a la Cueva 0 para escapar.", "normal")

    def _calcular_coordenadas_vertices(self):
        self.coords_cuevas.clear()
        cx, cy = 330, 365
        r0, r1, r2, r3 = 70, 145, 215, 290

        # Anillo 0: Vértices 0..4 (Pentágono Central)
        for i in range(5):
            ang = -math.pi / 2 + i * (2 * math.pi / 5)
            self.coords_cuevas[i] = (int(cx + r0 * math.cos(ang)), int(cy + r0 * math.sin(ang)))

        # Anillo 1: Vértices 5..9 (Conexiones radiales desde Anillo 0)
        for i in range(5):
            ang = -math.pi / 2 + i * (2 * math.pi / 5)
            self.coords_cuevas[i + 5] = (int(cx + r1 * math.cos(ang)), int(cy + r1 * math.sin(ang)))

        # Anillo 2: Vértices 10..14 (Desfasados 36° para formar pentágonos)
        for i in range(5):
            ang = -math.pi / 2 + math.pi / 5 + i * (2 * math.pi / 5)
            self.coords_cuevas[10 + i] = (int(cx + r2 * math.cos(ang)), int(cy + r2 * math.sin(ang)))

        # Anillo 3: Vértices 15..19 (Pentágono Exterior)
        for i in range(5):
            ang = -math.pi / 2 + math.pi / 5 + i * (2 * math.pi / 5)
            self.coords_cuevas[15 + i] = (int(cx + r3 * math.cos(ang)), int(cy + r3 * math.sin(ang)))

    def obtener_cueva_bajo_cursor(self, mx, my):
        for cueva, (cx, cy) in self.coords_cuevas.items():
            dist_sq = (mx - cx) ** 2 + (my - cy) ** 2
            if dist_sq <= (self.radio_cueva + 6) ** 2:
                return cueva
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
                self.agregar_log(f"No hay túnel directo hacia la cueva {objetivo}.", "error")

        elif self.modo_accion == "disparar":
            if self.juego.disparar(objetivo):
                self.modo_accion = "mover"

        elif self.modo_accion == "lanzar":
            if self.juego.lanzar_piedra(objetivo):
                self.modo_accion = "mover"

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
                # 1. Clic en botón de menú desplegable de mecánicas
                if self.btn_mecanicas_rect and self.btn_mecanicas_rect.collidepoint(event.pos):
                    self.mostrar_menu_mecanicas = not self.mostrar_menu_mecanicas
                    continue

                # 2. Interacción exclusiva si el menú está desplegado
                if self.mostrar_menu_mecanicas:
                    if self.btn_cerrar_mecanicas_rect and self.btn_cerrar_mecanicas_rect.collidepoint(event.pos):
                        self.mostrar_menu_mecanicas = False
                    elif self.dropdown_mecanicas_rect and self.dropdown_mecanicas_rect.collidepoint(event.pos):
                        pass
                    else:
                        self.mostrar_menu_mecanicas = False
                    continue

                # Comprobar clics en botones de acción
                if self.btn_disparar_rect.collidepoint(event.pos):
                    if self.juego.flechas > 0 and self.juego.vivo:
                        self.modo_accion = "disparar" if self.modo_accion != "disparar" else "mover"
                        if self.modo_accion == "disparar":
                            self.agregar_log("Modo DISPARAR: Haz clic en una cueva vecina conectada.", "alerta")
                    else:
                        self.agregar_log("No tienes flechas disponibles.", "error")

                elif self.btn_lanzar_rect.collidepoint(event.pos):
                    if self.juego.piedras > 0 and self.juego.vivo:
                        self.modo_accion = "lanzar" if self.modo_accion != "lanzar" else "mover"
                        if self.modo_accion == "lanzar":
                            self.agregar_log("Modo PIEDRA: Haz clic en una cueva vecina para escuchar.", "alerta")
                    else:
                        self.agregar_log("No te quedan piedras.", "error")

                elif self.btn_agarrar_rect.collidepoint(event.pos):
                    if self.juego.vivo:
                        self.juego.agarrar()

                elif self.btn_reiniciar_rect.collidepoint(event.pos):
                    self.nueva_partida()

                # Clic en botones de acceso directo a vecinos (1, 2, 3)
                for btn_rect, cueva_vec in self.botones_vecinos:
                    if btn_rect.collidepoint(event.pos):
                        self.interactuar_con_cueva(cueva_vec)
                        break

                # Clic sobre vértices/cuevas en el mapa
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

    def _render(self):
        self.screen.fill(COLOR_BG)
        self._dibujar_red_pentagonal()
        self._dibujar_panel_derecho()
        self._dibujar_estado_final()
        if self.mostrar_menu_mecanicas:
            self._dibujar_menu_mecanicas()
        pygame.display.flip()

    def _dibujar_red_pentagonal(self):
        mouse_pos = pygame.mouse.get_pos()
        cueva_hover = self.obtener_cueva_bajo_cursor(*mouse_pos)
        vecinos_jugador = self.juego.grafo.get(self.juego.pos_jugador, [])
        partida_terminada = (not self.juego.vivo) or (self.juego.pos_jugador == 0 and self.juego.tiene_oro)

        # 1. Dibujar las 11 caras pentagonales pegadas (polígonos de fondo)
        for cara in self.juego.caras_pentagonales:
            puntos_poligono = [self.coords_cuevas[v] for v in cara]
            pygame.draw.polygon(self.screen, COLOR_FACE, puntos_poligono)
            pygame.draw.polygon(self.screen, COLOR_FACE_BORDER, puntos_poligono, 1)

        # 2. Dibujar las aristas (los túneles/pasadizos que unen los vértices)
        aristas_dibujadas = set()
        for u, vecinos in self.juego.grafo.items():
            for v in vecinos:
                arista = (min(u, v), max(u, v))
                if arista not in aristas_dibujadas:
                    aristas_dibujadas.add(arista)
                    p1 = self.coords_cuevas[u]
                    p2 = self.coords_cuevas[v]

                    # Si el jugador está en u o v, iluminar el túnel
                    es_tunel_activo = (u == self.juego.pos_jugador or v == self.juego.pos_jugador)
                    color_t = (80, 85, 120) if es_tunel_activo else COLOR_TUNNEL
                    color_ti = COLOR_CYAN if (es_tunel_activo and self.juego.vivo) else COLOR_TUNNEL_INNER

                    pygame.draw.line(self.screen, color_t, p1, p2, 8)
                    pygame.draw.line(self.screen, color_ti, p1, p2, 4)

        # Dibujar derrumbes bloqueados sobre aristas
        for u, v in self.juego.bloqueos:
            p1 = self.coords_cuevas[u]
            p2 = self.coords_cuevas[v]
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            pygame.draw.circle(self.screen, (60, 20, 20), (int(mid_x), int(mid_y)), 14)
            pygame.draw.line(self.screen, COLOR_RED, (mid_x - 7, mid_y - 7), (mid_x + 7, mid_y + 7), 3)
            pygame.draw.line(self.screen, COLOR_RED, (mid_x - 7, mid_y + 7), (mid_x + 7, mid_y - 7), 3)

        # 3. Dibujar los vértices (las 20 cuevas)
        time_ms = pygame.time.get_ticks()
        for cueva, (cx, cy) in self.coords_cuevas.items():
            es_jugador = (cueva == self.juego.pos_jugador)
            es_visitada = (cueva in self.juego.habitaciones_visitadas)
            es_vecino = (cueva in vecinos_jugador)

            r = self.radio_cueva
            if es_jugador:
                pulse = int(3 * math.sin(time_ms * 0.007))
                pygame.draw.circle(self.screen, (50, 90, 150), (cx, cy), r + 5 + pulse, 2)
                pygame.draw.circle(self.screen, COLOR_NODE_PLAYER, (cx, cy), r)
                pygame.draw.circle(self.screen, COLOR_NODE_PLAYER_BORDER, (cx, cy), r, 3)
            elif es_visitada or partida_terminada:
                pygame.draw.circle(self.screen, COLOR_NODE_VISITED, (cx, cy), r)
                pygame.draw.circle(self.screen, COLOR_NODE_VISITED_BORDER, (cx, cy), r, 2)
            else:
                pygame.draw.circle(self.screen, COLOR_NODE_FOG, (cx, cy), r)
                pygame.draw.circle(self.screen, COLOR_NODE_FOG_BORDER, (cx, cy), r, 2)

            # Resaltar si es cueva vecina disponible
            if es_vecino and self.juego.vivo:
                color_halo = COLOR_GREEN
                if self.modo_accion == "disparar":
                    color_halo = COLOR_RED
                elif self.modo_accion == "lanzar":
                    color_halo = COLOR_ORANGE

                if cueva_hover == cueva:
                    pygame.draw.circle(self.screen, color_halo, (cx, cy), r + 4, 3)
                else:
                    pygame.draw.circle(self.screen, color_halo, (cx, cy), r + 3, 1)

            # Contenido del vértice (cueva)
            if es_jugador:
                avatar = "🤠" if not self.juego.tiene_oro else "💰"
                txt_av = self.font_emoji.render(avatar, True, COLOR_TEXT)
                self.screen.blit(txt_av, (cx - txt_av.get_width() // 2, cy - txt_av.get_height() // 2))

                # Percepciones alrededor del jugador
                percepciones = self.juego.percibir()
                iconos = []
                if "Hedor" in percepciones: iconos.append("🦨")
                if "Brisa" in percepciones: iconos.append("💨")
                if "Brillo" in percepciones: iconos.append("✨")
                if "Aleteo" in percepciones: iconos.append("🦇")
                if "Crujido" in percepciones: iconos.append("💥")

                if iconos:
                    txt_ic = self.font_small.render("".join(iconos), True, COLOR_GOLD)
                    self.screen.blit(txt_ic, (cx - txt_ic.get_width() // 2, cy + 24))

            elif partida_terminada:
                if cueva == self.juego.pos_wumpus:
                    txt_item = self.font_emoji.render("👹" if self.juego.wumpus_vivo else "💀", True, COLOR_RED)
                elif cueva == self.juego.pos_oro:
                    txt_item = self.font_emoji.render("💰", True, COLOR_GOLD)
                elif cueva in self.juego.pos_pozos:
                    txt_item = self.font_emoji.render("🕳️", True, COLOR_CYAN)
                elif cueva in self.juego.pos_murcielagos:
                    txt_item = self.font_emoji.render("🦇", True, COLOR_PURPLE)
                elif cueva == self.juego.pos_derrumbe:
                    txt_item = self.font_emoji.render("🪨", True, COLOR_ORANGE)
                else:
                    txt_item = self.font_small.render(str(cueva), True, COLOR_SUBTEXT)

                self.screen.blit(txt_item, (cx - txt_item.get_width() // 2, cy - txt_item.get_height() // 2))

            else:
                if es_visitada:
                    txt_num = self.font_small.render(str(cueva), True, COLOR_TEXT)
                    self.screen.blit(txt_num, (cx - txt_num.get_width() // 2, cy - txt_num.get_height() // 2))
                else:
                    txt_fog = self.font_small.render("?", True, (80, 85, 110))
                    self.screen.blit(txt_fog, (cx - txt_fog.get_width() // 2, cy - txt_fog.get_height() // 2))



    def _dibujar_panel_derecho(self):
        panel_x = 655
        panel_w = 415

        # 1. Cabecera y Botón de Nuevas Mecánicas
        txt_titulo = self.font_title.render("EL MUNDO DEL WUMPUS", True, COLOR_GOLD)
        self.screen.blit(txt_titulo, (panel_x, 16))
        txt_sub = self.font_small.render("Grafo de pentágonos pegados (Dodecaedro de 20 cuevas)", True, COLOR_SUBTEXT)
        self.screen.blit(txt_sub, (panel_x, 44))

        # Botón de menú desplegable de mecánicas
        self.btn_mecanicas_rect = pygame.Rect(panel_x + panel_w - 150, 14, 150, 26)
        mouse_pos = pygame.mouse.get_pos()
        es_hover_mec = self.btn_mecanicas_rect.collidepoint(mouse_pos)
        c_bg_mec = (55, 65, 95) if (es_hover_mec or self.mostrar_menu_mecanicas) else (40, 45, 68)
        pygame.draw.rect(self.screen, c_bg_mec, self.btn_mecanicas_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_GOLD, self.btn_mecanicas_rect, 1, border_radius=6)

        simbolo = "▲" if self.mostrar_menu_mecanicas else "▼"
        txt_btn_mec = self.font_btn.render(f"Nuevas Mecánicas {simbolo}", True, COLOR_GOLD)
        self.screen.blit(txt_btn_mec, (self.btn_mecanicas_rect.centerx - txt_btn_mec.get_width() // 2,
                                       self.btn_mecanicas_rect.centery - txt_btn_mec.get_height() // 2))

        # 2. Banner de Cacería Activa
        banner_y = 68
        if self.juego.modo_caceria and self.juego.wumpus_vivo:
            dist = self.juego._distancia_al_jugador()
            sufijo = "s" if dist > 1 else ""
            banner_rect = pygame.Rect(panel_x, banner_y, panel_w, 36)
            pygame.draw.rect(self.screen, COLOR_RED, banner_rect, border_radius=6)
            txt_cac = self.font_bold.render(f"🚨 ¡¡WUMPUS EN CACERÍA!! Acechando a {dist} cueva{sufijo}", True, (20, 20, 30))
            self.screen.blit(txt_cac, (panel_x + 14, banner_y + 8))
            inv_y = banner_y + 44
        else:
            inv_y = banner_y

        # 3. Tarjeta de Inventario y Estado
        inv_rect = pygame.Rect(panel_x, inv_y, panel_w, 86)
        pygame.draw.rect(self.screen, COLOR_PANEL, inv_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, inv_rect, 1, border_radius=8)

        txt_inv_titulo = self.font_bold.render("🎒 Estado del Explorador", True, COLOR_GOLD)
        self.screen.blit(txt_inv_titulo, (panel_x + 14, inv_y + 10))

        txt_fl = self.font_normal.render(f"🏹 Flechas: {self.juego.flechas}", True, COLOR_TEXT)
        self.screen.blit(txt_fl, (panel_x + 16, inv_y + 34))

        txt_pd = self.font_normal.render(f"🪨 Piedras: {self.juego.piedras}", True, COLOR_TEXT)
        self.screen.blit(txt_pd, (panel_x + 160, inv_y + 34))

        oro_str = "¡CONSEGUIDO! 🏆" if self.juego.tiene_oro else "No"
        txt_oro = self.font_normal.render(f"💰 Oro: {oro_str}", True, COLOR_GOLD if self.juego.tiene_oro else COLOR_TEXT)
        self.screen.blit(txt_oro, (panel_x + 16, inv_y + 58))

        txt_pos = self.font_normal.render(f"📍 Cueva actual: {self.juego.pos_jugador}", True, COLOR_CYAN)
        self.screen.blit(txt_pos, (panel_x + 160, inv_y + 58))

        # 4. Percepciones
        perc_y = inv_y + 94
        perc_rect = pygame.Rect(panel_x, perc_y, panel_w, 60)
        pygame.draw.rect(self.screen, COLOR_PANEL, perc_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, perc_rect, 1, border_radius=8)

        txt_per_tit = self.font_bold.render("👂 Percepciones en esta cueva:", True, COLOR_TEXT)
        self.screen.blit(txt_per_tit, (panel_x + 14, perc_y + 8))

        percepciones = self.juego.percibir()
        if percepciones:
            txt_percs = self.font_bold.render("  •  " + "   •  ".join(percepciones), True, COLOR_GOLD)
        else:
            txt_percs = self.font_normal.render("Silencio absoluto. No percibes peligros contiguos.", True, (110, 115, 140))
        self.screen.blit(txt_percs, (panel_x + 14, perc_y + 32))

        # 5. Túneles conectados y botones de salto
        tun_y = perc_y + 68
        tun_rect = pygame.Rect(panel_x, tun_y, panel_w, 66)
        pygame.draw.rect(self.screen, COLOR_PANEL, tun_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, tun_rect, 1, border_radius=8)

        txt_tun_tit = self.font_bold.render(f"🚪 Túneles desde Cueva {self.juego.pos_jugador}:", True, COLOR_TEXT)
        self.screen.blit(txt_tun_tit, (panel_x + 14, tun_y + 8))

        vecinos = self.juego.grafo.get(self.juego.pos_jugador, [])
        self.botones_vecinos = []
        btn_w = 120
        for idx, v in enumerate(vecinos):
            bx = panel_x + 14 + idx * (btn_w + 10)
            by = tun_y + 30
            b_rect = pygame.Rect(bx, by, btn_w, 28)
            self.botones_vecinos.append((b_rect, v))
            pygame.draw.rect(self.screen, (45, 50, 75), b_rect, border_radius=5)
            txt_btn_v = self.font_bold.render(f"[{idx+1}] Cueva {v}", True, COLOR_CYAN)
            self.screen.blit(txt_btn_v, (bx + 20, by + 5))

        # 6. Botones de Acción
        btn_y = tun_y + 74
        self.btn_disparar_rect = pygame.Rect(panel_x, btn_y, 130, 36)
        self.btn_lanzar_rect = pygame.Rect(panel_x + 140, btn_y, 130, 36)
        self.btn_agarrar_rect = pygame.Rect(panel_x + 280, btn_y, 135, 36)
        self.btn_reiniciar_rect = pygame.Rect(panel_x, btn_y + 44, panel_w, 32)

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
        txt_b_rein = self.font_bold.render("🔄 Nueva Red Dodecaédrica (R)", True, COLOR_TEXT)

        self.screen.blit(txt_b_disp, (panel_x + 14, btn_y + 9))
        self.screen.blit(txt_b_lanz, (panel_x + 154, btn_y + 9))
        self.screen.blit(txt_b_agar, (panel_x + 292, btn_y + 9))
        self.screen.blit(txt_b_rein, (panel_x + 85, btn_y + 51))

        # 7. Bitácora de Eventos
        log_y = btn_y + 86
        log_h = self.height - log_y - 35
        log_rect = pygame.Rect(panel_x, log_y, panel_w, log_h)
        pygame.draw.rect(self.screen, (16, 16, 26), log_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, log_rect, 1, border_radius=8)

        txt_log_tit = self.font_bold.render("📜 Bitácora de la Aventura", True, COLOR_GOLD)
        self.screen.blit(txt_log_tit, (panel_x + 14, log_y + 8))

        line_y = log_y + 30
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
            line_y += 20

        txt_ctrls = self.font_small.render("Atajos: 1, 2, 3 o Clic en vértices | F: Disparo | P: Piedra | R: Reiniciar", True, COLOR_SUBTEXT)
        self.screen.blit(txt_ctrls, (panel_x, self.height - 22))



    def _dibujar_estado_final(self):
        if self.juego.pos_jugador == 0 and self.juego.tiene_oro:
            banner_rect = pygame.Rect(50, 16, 560, 46)
            pygame.draw.rect(self.screen, (30, 80, 50), banner_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_GREEN, banner_rect, 2, border_radius=8)
            txt_vic = self.font_bold.render("🏆 ¡¡HAS ESCAPADO CON EL ORO!! ¡¡VICTORIA!! (Pulsa R)", True, COLOR_GREEN)
            self.screen.blit(txt_vic, (banner_rect.centerx - txt_vic.get_width() // 2, banner_rect.centery - txt_vic.get_height() // 2))

        elif not self.juego.vivo:
            banner_rect = pygame.Rect(50, 16, 560, 46)
            pygame.draw.rect(self.screen, (70, 20, 30), banner_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_RED, banner_rect, 2, border_radius=8)
            txt_der = self.font_bold.render("💀 HAS MUERTO EN LA CUEVA. Cueva revelada. (Pulsa R)", True, COLOR_RED)
            self.screen.blit(txt_der, (banner_rect.centerx - txt_der.get_width() // 2, banner_rect.centery - txt_der.get_height() // 2))

    def _dibujar_menu_mecanicas(self):
        box_x = 635
        box_y = 48
        box_w = 440
        box_h = 575
        self.dropdown_mecanicas_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        # Fondo con sombra y borde dorado
        pygame.draw.rect(self.screen, (20, 22, 34), self.dropdown_mecanicas_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_GOLD, self.dropdown_mecanicas_rect, 2, border_radius=10)

        # Cabecera del menú
        header_rect = pygame.Rect(box_x, box_y, box_w, 36)
        pygame.draw.rect(self.screen, (32, 35, 52), header_rect, border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(self.screen, COLOR_BORDER, header_rect, 1, border_top_left_radius=10, border_top_right_radius=10)
        txt_head = self.font_bold.render("NOVEDADES VS. WUMPUS CLASICO (1972)", True, COLOR_GOLD)
        self.screen.blit(txt_head, (box_x + 14, box_y + 9))

        # Botón de cerrar [X]
        self.btn_cerrar_mecanicas_rect = pygame.Rect(box_x + box_w - 30, box_y + 6, 24, 24)
        mouse_pos = pygame.mouse.get_pos()
        es_hover_x = self.btn_cerrar_mecanicas_rect.collidepoint(mouse_pos)
        c_bg_x = (80, 30, 40) if es_hover_x else (50, 20, 30)
        pygame.draw.rect(self.screen, c_bg_x, self.btn_cerrar_mecanicas_rect, border_radius=4)
        pygame.draw.rect(self.screen, COLOR_RED, self.btn_cerrar_mecanicas_rect, 1, border_radius=4)
        txt_x = self.font_bold.render("X", True, COLOR_RED)
        self.screen.blit(txt_x, (self.btn_cerrar_mecanicas_rect.centerx - txt_x.get_width() // 2,
                                 self.btn_cerrar_mecanicas_rect.centery - txt_x.get_height() // 2))

        # Lista de nuevas mecánicas
        mecanicas = [
            ("1. Modo Cacería del Wumpus", COLOR_RED, [
                "• Original: El Wumpus era estático y solo se movía al fallar flechas.",
                "• Nuevo: ¡Al coger el Oro, el Wumpus despierta e inicia cacería!",
                "  Te persigue activamente por el grafo cada 2 turnos para devorarte.",
                "  Debes huir a tiempo de regreso hasta la Cueva 0 para escapar."
            ]),
            ("2. Lanzamiento de Piedras (3 en bolsa)", COLOR_CYAN, [
                "• Original: Solo contabas con una flecha para disparar a ciegas.",
                "• Nuevo: Arroja piedras a cuevas contiguas ('P') para tantear riesgos:",
                "    - Eco de chapoteo (Splash): Pozo mortal sin fondo.",
                "    - Rugido furioso: Golpeas al Wumpus, huye y retrasa la cacería.",
                "    - Chillidos y aleteo: Nido de murciélagos gigantes.",
                "    - Crujido de piedra: Techo inestable a punto de desplomarse."
            ]),
            ("3. Derrumbe Dinámico de Túneles", COLOR_ORANGE, [
                "• Original: La red de 30 túneles del dodecaedro era inalterable.",
                "• Nuevo: Hay una cueva inestable (percepción 'Crujido'). Al pisarla,",
                "  un derrumbe violento sella un túnel para siempre ('[X]'),",
                "  obligándote a buscar rutas alternativas en el grafo."
            ]),
            ("4. Garantía de Solubilidad con BFS", COLOR_GREEN, [
                "• Original: Los pozos al azar podían bloquear la cueva inicial.",
                "• Nuevo: Búsqueda en Anchura (BFS) valida matemáticamente que",
                "  siempre exista un camino seguro transitable de ida y vuelta."
            ]),
            ("5. Niebla de Guerra y Mosaico Pentagonal", COLOR_GOLD, [
                "• Original: Aventura clásica puramente en texto en terminal ciega.",
                "• Nuevo: Mosaico gráfico de pentágonos pegados con iluminación,",
                "  percepciones en tiempo real y revelación total al terminar."
            ])
        ]

        curr_y = box_y + 46
        for titulo, col_tit, lineas in mecanicas:
            self.screen.blit(self.font_bold.render(titulo, True, col_tit), (box_x + 14, curr_y))
            curr_y += 18
            for lin in lineas:
                self.screen.blit(self.font_normal.render(lin, True, COLOR_TEXT), (box_x + 20, curr_y))
                curr_y += 16
            curr_y += 6

        # Pie de página
        txt_foot = self.font_small.render("Haz clic en [X], en el botón o presiona ESC / M para cerrar", True, COLOR_SUBTEXT)
        self.screen.blit(txt_foot, (box_x + box_w // 2 - txt_foot.get_width() // 2, box_y + box_h - 22))


def main():
    app = WumpusPygameApp()
    app.run()


if __name__ == "__main__":
    main()