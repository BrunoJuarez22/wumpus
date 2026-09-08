import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os

from wunpus import MundoWumpus

# Paleta de colores Dark / Dungeon (Catppuccin Mocha)
COLOR_BG = "#181825"
COLOR_CARD = "#1e1e2e"
COLOR_CARD_BORDER = "#313244"
COLOR_TEXT = "#cdd6f4"
COLOR_SUBTEXT = "#a6adc8"
COLOR_FOG = "#11111b"
COLOR_VISITED = "#282a36"
COLOR_PLAYER = "#89b4fa"
COLOR_GOLD = "#f9e2af"
COLOR_DANGER = "#f38ba8"
COLOR_SUCCESS = "#a6e3a1"
COLOR_CYAN = "#89dceb"
COLOR_PURPLE = "#cba6f7"
COLOR_ORANGE = "#fab387"

class WumpusGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏹 El Mundo del Wumpus - Edición Gráfica")
        self.root.geometry("1060x760")
        self.root.minsize(1000, 720)
        self.root.configure(bg=COLOR_BG)

        # Estado del juego
        self.modo_accion = "mover"  # "mover", "disparar", "lanzar"
        self.juego = None

        self._crear_interfaz()
        self._vincular_teclado()
        self.nueva_partida()

    def _crear_interfaz(self):
        # Header superior
        header_frame = tk.Frame(self.root, bg=COLOR_CARD, padx=20, pady=10, relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, side=tk.TOP, padx=12, pady=(12, 6))

        titulo_label = tk.Label(
            header_frame,
            text="🏹 EL MUNDO DEL WUMPUS",
            font=("Segoe UI", 18, "bold"),
            fg=COLOR_GOLD,
            bg=COLOR_CARD
        )
        titulo_label.pack(side=tk.LEFT)

        subtitulo_label = tk.Label(
            header_frame,
            text=" |  Encuentra el oro, elude los pozos y sobrevive a la cacería",
            font=("Segoe UI", 11, "italic"),
            fg=COLOR_SUBTEXT,
            bg=COLOR_CARD
        )
        subtitulo_label.pack(side=tk.LEFT, padx=6)

        btn_reiniciar = tk.Button(
            header_frame,
            text="🔄 Nueva Cueva",
            font=("Segoe UI", 10, "bold"),
            bg="#45475a",
            fg=COLOR_TEXT,
            activebackground=COLOR_CARD_BORDER,
            activeforeground=COLOR_TEXT,
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.nueva_partida
        )
        btn_reiniciar.pack(side=tk.RIGHT)

        btn_ayuda = tk.Button(
            header_frame,
            text="❓ Ayuda",
            font=("Segoe UI", 10, "bold"),
            bg="#45475a",
            fg=COLOR_TEXT,
            activebackground=COLOR_CARD_BORDER,
            activeforeground=COLOR_TEXT,
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.mostrar_ayuda
        )
        btn_ayuda.pack(side=tk.RIGHT, padx=8)

        # Contenedor principal (dos columnas)
        main_frame = tk.Frame(self.root, bg=COLOR_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        # === COLUMNA IZQUIERDA: Tablero Canvas ===
        left_frame = tk.Frame(main_frame, bg=COLOR_CARD, padx=14, pady=14)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6), pady=6)

        tablero_header = tk.Frame(left_frame, bg=COLOR_CARD)
        tablero_header.pack(fill=tk.X, pady=(0, 8))

        lbl_mapa_titulo = tk.Label(
            tablero_header,
            text="🗺️ Exploración de la Cueva (4x4)",
            font=("Segoe UI", 13, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD
        )
        lbl_mapa_titulo.pack(side=tk.LEFT)

        self.lbl_modo_actual = tk.Label(
            tablero_header,
            text="MODO: 🚶 Desplazarse",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_CYAN,
            bg="#24273a",
            padx=10,
            pady=2
        )
        self.lbl_modo_actual.pack(side=tk.RIGHT)

        # Canvas para la cuadrícula
        self.cell_size = 110
        self.margin = 30
        canvas_dim = self.margin * 2 + self.cell_size * 4

        self.canvas = tk.Canvas(
            left_frame,
            width=canvas_dim,
            height=canvas_dim,
            bg="#11111b",
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER
        )
        self.canvas.pack(pady=4)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Leyenda inferior del tablero
        leyenda_frame = tk.Frame(left_frame, bg=COLOR_CARD)
        leyenda_frame.pack(fill=tk.X, pady=(8, 0))

        leyenda_text = "Clic en casilla contigua para interactuar  |  Atajos: WASD / Flechas para mover"
        lbl_leyenda = tk.Label(leyenda_frame, text=leyenda_text, font=("Segoe UI", 9), fg=COLOR_SUBTEXT, bg=COLOR_CARD)
        lbl_leyenda.pack()

        # === COLUMNA DERECHA: Controles, Inventario y Bitácora ===
        right_frame = tk.Frame(main_frame, bg=COLOR_BG, width=440)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(6, 0), pady=6)

        # 1. Banner de Cacería
        self.banner_caceria = tk.Frame(right_frame, bg="#e78284", padx=10, pady=8)
        self.lbl_caceria = tk.Label(
            self.banner_caceria,
            text="🚨 ¡¡EL WUMPUS ESTÁ EN CACERÍA ACTIVA!!",
            font=("Segoe UI", 11, "bold"),
            fg="#11111b",
            bg="#e78284"
        )
        self.lbl_caceria.pack()
        # Inicialmente oculto

        # 2. Card de Inventario y Estado
        status_card = tk.LabelFrame(
            right_frame,
            text=" 🎒 Inventario y Percepciones ",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_GOLD,
            bg=COLOR_CARD,
            bd=1,
            relief=tk.SOLID,
            padx=12,
            pady=8
        )
        status_card.pack(fill=tk.X, pady=(0, 8))

        info_grid = tk.Frame(status_card, bg=COLOR_CARD)
        info_grid.pack(fill=tk.X)

        self.lbl_flechas = tk.Label(info_grid, text="🏹 Flechas: 1", font=("Segoe UI", 11), fg=COLOR_TEXT, bg=COLOR_CARD)
        self.lbl_flechas.grid(row=0, column=0, sticky="w", padx=8, pady=3)

        self.lbl_piedras = tk.Label(info_grid, text="🪨 Piedras: 3", font=("Segoe UI", 11), fg=COLOR_TEXT, bg=COLOR_CARD)
        self.lbl_piedras.grid(row=0, column=1, sticky="w", padx=8, pady=3)

        self.lbl_oro = tk.Label(info_grid, text="💰 Oro: No", font=("Segoe UI", 11), fg=COLOR_TEXT, bg=COLOR_CARD)
        self.lbl_oro.grid(row=1, column=0, sticky="w", padx=8, pady=3)

        self.lbl_pos = tk.Label(info_grid, text="📍 Posición: (0, 0)", font=("Segoe UI", 11), fg=COLOR_CYAN, bg=COLOR_CARD)
        self.lbl_pos.grid(row=1, column=1, sticky="w", padx=8, pady=3)

        self.lbl_percepciones = tk.Label(
            status_card,
            text="👂 Percepciones: Ninguna",
            font=("Segoe UI", 10, "italic"),
            fg=COLOR_SUBTEXT,
            bg=COLOR_CARD,
            wraplength=380,
            justify=tk.LEFT
        )
        self.lbl_percepciones.pack(anchor="w", pady=(6, 2), padx=8)

        # 3. Card de Acciones Rápidas
        actions_card = tk.LabelFrame(
            right_frame,
            text=" ⚡ Acciones ",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_GOLD,
            bg=COLOR_CARD,
            bd=1,
            relief=tk.SOLID,
            padx=10,
            pady=8
        )
        actions_card.pack(fill=tk.X, pady=(0, 8))

        btn_row = tk.Frame(actions_card, bg=COLOR_CARD)
        btn_row.pack(fill=tk.X, pady=3)

        self.btn_disparar = tk.Button(
            btn_row,
            text="🏹 Disparar (F)",
            font=("Segoe UI", 10, "bold"),
            bg="#585b70",
            fg=COLOR_TEXT,
            activebackground=COLOR_CARD_BORDER,
            bd=0,
            padx=8,
            pady=5,
            cursor="hand2",
            command=self.activar_modo_disparar
        )
        self.btn_disparar.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        self.btn_lanzar = tk.Button(
            btn_row,
            text="🪨 Piedra (P)",
            font=("Segoe UI", 10, "bold"),
            bg="#585b70",
            fg=COLOR_TEXT,
            activebackground=COLOR_CARD_BORDER,
            bd=0,
            padx=8,
            pady=5,
            cursor="hand2",
            command=self.activar_modo_lanzar
        )
        self.btn_lanzar.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        self.btn_agarrar = tk.Button(
            btn_row,
            text="💰 Agarrar Oro (G)",
            font=("Segoe UI", 10, "bold"),
            bg="#a6e3a1",
            fg="#11111b",
            activebackground="#94e2d5",
            bd=0,
            padx=8,
            pady=5,
            cursor="hand2",
            command=self.accion_agarrar
        )
        self.btn_agarrar.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        # Cruceta de movimiento en pantalla
        dpad_frame = tk.Frame(actions_card, bg=COLOR_CARD)
        dpad_frame.pack(pady=4)

        btn_up = tk.Button(dpad_frame, text="⬆️ Norte", width=8, bg="#313244", fg=COLOR_TEXT, bd=0, command=lambda: self.mover_direccion(0, 1))
        btn_up.grid(row=0, column=1, padx=2, pady=2)

        btn_left = tk.Button(dpad_frame, text="⬅️ Oeste", width=8, bg="#313244", fg=COLOR_TEXT, bd=0, command=lambda: self.mover_direccion(-1, 0))
        btn_left.grid(row=1, column=0, padx=2, pady=2)

        btn_center = tk.Label(dpad_frame, text="⏺️", font=("Segoe UI", 12), fg=COLOR_SUBTEXT, bg=COLOR_CARD)
        btn_center.grid(row=1, column=1)

        btn_right = tk.Button(dpad_frame, text="➡️ Este", width=8, bg="#313244", fg=COLOR_TEXT, bd=0, command=lambda: self.mover_direccion(1, 0))
        btn_right.grid(row=1, column=2, padx=2, pady=2)

        btn_down = tk.Button(dpad_frame, text="⬇️ Sur", width=8, bg="#313244", fg=COLOR_TEXT, bd=0, command=lambda: self.mover_direccion(0, -1))
        btn_down.grid(row=2, column=1, padx=2, pady=2)

        # 4. Card de Bitácora de Eventos (Event Log)
        log_card = tk.LabelFrame(
            right_frame,
            text=" 📜 Bitácora de Aventuras ",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_GOLD,
            bg=COLOR_CARD,
            bd=1,
            relief=tk.SOLID,
            padx=10,
            pady=6
        )
        log_card.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_card,
            bg="#11111b",
            fg=COLOR_TEXT,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bd=0,
            padx=6,
            pady=6
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # Configurar tags para colores en el log
        self.log_text.tag_config("rojo", foreground=COLOR_DANGER, font=("Consolas", 9, "bold"))
        self.log_text.tag_config("dorado", foreground=COLOR_GOLD, font=("Consolas", 9, "bold"))
        self.log_text.tag_config("verde", foreground=COLOR_SUCCESS, font=("Consolas", 9, "bold"))
        self.log_text.tag_config("cian", foreground=COLOR_CYAN)
        self.log_text.tag_config("morado", foreground=COLOR_PURPLE)
        self.log_text.tag_config("naranja", foreground=COLOR_ORANGE)

    def _vincular_teclado(self):
        self.root.bind("<Up>", lambda e: self.mover_direccion(0, 1))
        self.root.bind("<Down>", lambda e: self.mover_direccion(0, -1))
        self.root.bind("<Left>", lambda e: self.mover_direccion(-1, 0))
        self.root.bind("<Right>", lambda e: self.mover_direccion(1, 0))

        self.root.bind("<w>", lambda e: self.mover_direccion(0, 1))
        self.root.bind("<s>", lambda e: self.mover_direccion(0, -1))
        self.root.bind("<a>", lambda e: self.mover_direccion(-1, 0))
        self.root.bind("<d>", lambda e: self.mover_direccion(1, 0))

        self.root.bind("<f>", lambda e: self.activar_modo_disparar())
        self.root.bind("<p>", lambda e: self.activar_modo_lanzar())
        self.root.bind("<g>", lambda e: self.accion_agarrar())
        self.root.bind("<space>", lambda e: self.accion_agarrar())
        self.root.bind("<r>", lambda e: self.nueva_partida())
        self.root.bind("<Escape>", lambda e: self.cancelar_modo())

    def nueva_partida(self):
        """Reinicia el juego con un nuevo mundo de Wumpus solucionable."""
        self.juego = MundoWumpus(callback_notificar=self.recibir_mensaje)
        self.modo_accion = "mover"
        self._actualizar_etiqueta_modo()

        # Limpiar log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

        self.agregar_log("==================================================", "dorado")
        self.agregar_log("🗡️ ¡Comienza una nueva expedición en la cueva! (4x4)", "dorado")
        self.agregar_log("Encuentra el oro, agárralo y regresa a salvo a (0, 0).\n", "normal")

        self.actualizar_interfaz()

    def recibir_mensaje(self, mensaje):
        """Callback invocado por MundoWumpus cuando ocurre un evento."""
        msg = mensaje.strip()
        if not msg:
            return

        tag = "normal"
        if "CACERÍA" in msg or "DEVORA" in msg or "WUMPUS HA ENTRADO" in msg or "¡AAAAAAHHHH!" in msg:
            tag = "rojo"
        elif "ORO" in msg or "GANADO" in msg or "FELICIDADES" in msg:
            tag = "verde"
        elif "GRITO ESCALOFRIANTE" in msg or "matado al Wumpus" in msg:
            tag = "dorado"
        elif "Derrumbe" in msg or "BOOOM" in msg or "sellado el paso" in msg:
            tag = "naranja"
        elif "murciélagos" in msg or "SWOOOOSH" in msg:
            tag = "morado"
        elif "SPLASH" in msg or "Brisa" in msg or "Hedor" in msg:
            tag = "cian"

        self.agregar_log(msg, tag)

    def agregar_log(self, texto, tag="normal"):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{texto}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def actualizar_interfaz(self):
        """Redibuja el mapa y actualiza todos los contadores e indicadores."""
        self.lbl_pos.config(text=f"📍 Posición: {self.juego.pos_jugador}")
        self.lbl_flechas.config(text=f"🏹 Flechas: {self.juego.flechas}")
        self.lbl_piedras.config(text=f"🪨 Piedras: {self.juego.piedras}")
        self.lbl_oro.config(text=f"💰 Oro: {'¡Conseguido! 🏆' if self.juego.tiene_oro else 'No'}")

        # Percepciones
        percepciones = self.juego.percibir()
        if percepciones:
            self.lbl_percepciones.config(text=f"👂 Percibes: {', '.join(percepciones)}", fg=COLOR_GOLD)
        else:
            self.lbl_percepciones.config(text="👂 Percibes: Silencio absoluto.", fg=COLOR_SUBTEXT)

        # Banner de cacería
        if self.juego.modo_caceria and self.juego.wumpus_vivo:
            dist = self.juego._distancia_al_jugador()
            sufijo = "es" if dist > 1 else ""
            self.lbl_caceria.config(text=f"🚨 ¡¡WUMPUS EN CACERÍA!! Acechando a {dist} habitación{sufijo} de ti")
            self.banner_caceria.pack(fill=tk.X, pady=(0, 8), before=self.btn_disparar.master.master.master.children["!labelframe"])
        else:
            self.banner_caceria.pack_forget()

        # Dibujar cuadrícula Canvas
        self._dibujar_tablero()

        # Comprobar victoria o muerte
        if self.juego.pos_jugador == (0, 0) and self.juego.tiene_oro:
            self.agregar_log("\n🏆 ¡¡FELICIDADES!! ¡Has escapado con el tesoro!", "verde")
            self._dibujar_tablero(revelar_todo=True)
            messagebox.showinfo("¡Victoria!", "¡Enhorabuena! Has derrotado a los horrores de la cueva y escapado con el oro.")
        elif not self.juego.vivo:
            self._dibujar_tablero(revelar_todo=True)
            messagebox.showerror("Fin del Juego", "Has muerto en las profundidades de la cueva...")

    def _dibujar_tablero(self, revelar_todo=False):
        """Renderiza la cuadrícula 4x4 en el Canvas."""
        self.canvas.delete("all")
        m = self.margin
        sz = self.cell_size
        tam = self.juego.tamano

        # Coordenadas: y=3 arriba, y=0 abajo
        for grid_x in range(tam):
            for grid_y in range(tam):
                canvas_x0 = m + grid_x * sz
                canvas_y0 = m + (tam - 1 - grid_y) * sz
                canvas_x1 = canvas_x0 + sz
                canvas_y1 = canvas_y0 + sz
                pos = (grid_x, grid_y)

                es_jugador = (pos == self.juego.pos_jugador)
                es_visitada = (pos in self.juego.habitaciones_visitadas)

                # Color de fondo de la celda
                if es_jugador:
                    color_fondo = "#1e3a5f"
                elif es_visitada or revelar_todo:
                    color_fondo = COLOR_VISITED
                else:
                    color_fondo = COLOR_FOG

                # Dibujar rectángulo de casilla
                borde_color = COLOR_GOLD if es_jugador else COLOR_CARD_BORDER
                borde_ancho = 3 if es_jugador else 1

                self.canvas.create_rectangle(
                    canvas_x0, canvas_y0, canvas_x1, canvas_y1,
                    fill=color_fondo,
                    outline=borde_color,
                    width=borde_ancho
                )

                # Etiquetas de coordenadas sutiles
                self.canvas.create_text(
                    canvas_x0 + 16, canvas_y0 + 14,
                    text=f"{grid_x},{grid_y}",
                    font=("Segoe UI", 8),
                    fill="#585b70"
                )

                # Contenido de la celda
                if es_jugador:
                    avatar = "🤠💰" if self.juego.tiene_oro else "🧙‍♂️"
                    self.canvas.create_text(
                        (canvas_x0 + canvas_x1) / 2,
                        (canvas_y0 + canvas_y1) / 2 - 10,
                        text=avatar,
                        font=("Segoe UI Emoji", 26)
                    )
                    # Mostrar percepciones de la celda actual como iconos
                    percepciones = self.juego.percibir()
                    iconos = []
                    if "Hedor" in percepciones: iconos.append("🦨")
                    if "Brisa" in percepciones: iconos.append("💨")
                    if "Brillo" in percepciones: iconos.append("✨")
                    if "Aleteo" in percepciones: iconos.append("🦇")
                    if "Crujido" in percepciones: iconos.append("💥")

                    if iconos:
                        self.canvas.create_text(
                            (canvas_x0 + canvas_x1) / 2,
                            canvas_y1 - 18,
                            text=" ".join(iconos),
                            font=("Segoe UI Emoji", 12)
                        )
                elif revelar_todo:
                    # Mostrar todos los secretos de la cueva
                    if pos == self.juego.pos_wumpus:
                        icono = "👹" if self.juego.wumpus_vivo else "💀"
                        etiqueta = "Wumpus" if self.juego.wumpus_vivo else "Wumpus †"
                        color_txt = COLOR_DANGER
                    elif pos == self.juego.pos_oro:
                        icono, etiqueta, color_txt = "💰", "Oro", COLOR_GOLD
                    elif pos in self.juego.pos_pozos:
                        icono, etiqueta, color_txt = "🕳️", "Pozo", COLOR_CYAN
                    elif pos in self.juego.pos_murcielagos:
                        icono, etiqueta, color_txt = "🦇", "Murciélagos", COLOR_PURPLE
                    elif pos == self.juego.pos_derrumbe:
                        icono, etiqueta, color_txt = "🪨", "Derrumbe", COLOR_ORANGE
                    else:
                        icono, etiqueta, color_txt = "·", "Seguro", COLOR_SUBTEXT

                    self.canvas.create_text(
                        (canvas_x0 + canvas_x1) / 2, (canvas_y0 + canvas_y1) / 2 - 8,
                        text=icono, font=("Segoe UI Emoji", 22)
                    )
                    self.canvas.create_text(
                        (canvas_x0 + canvas_x1) / 2, canvas_y1 - 18,
                        text=etiqueta, font=("Segoe UI", 9, "bold"), fill=color_txt
                    )
                else:
                    if not es_visitada:
                        # Niebla de guerra
                        self.canvas.create_text(
                            (canvas_x0 + canvas_x1) / 2, (canvas_y0 + canvas_y1) / 2,
                            text="❓", font=("Segoe UI Emoji", 20), fill="#313244"
                        )

        # Dibujar bloqueos de túneles por derrumbes
        for (u, v) in self.juego.bloqueos:
            x1, y1 = u
            x2, y2 = v
            # Posición en canvas
            cx1 = m + x1 * sz + sz / 2
            cy1 = m + (tam - 1 - y1) * sz + sz / 2
            cx2 = m + x2 * sz + sz / 2
            cy2 = m + (tam - 1 - y2) * sz + sz / 2
            mid_x = (cx1 + cx2) / 2
            mid_y = (cy1 + cy2) / 2

            self.canvas.create_text(mid_x, mid_y, text="🪨❌", font=("Segoe UI Emoji", 14))

    def _on_canvas_click(self, event):
        """Maneja clics sobre las casillas del tablero."""
        if not self.juego.vivo:
            return

        m = self.margin
        sz = self.cell_size
        tam = self.juego.tamano

        if not (m <= event.x < m + sz * tam and m <= event.y < m + sz * tam):
            return

        grid_x = int((event.x - m) // sz)
        grid_y = tam - 1 - int((event.y - m) // sz)
        objetivo = (grid_x, grid_y)

        if self.modo_accion == "mover":
            if objetivo in self.juego.grafo.get(self.juego.pos_jugador, []):
                self.juego.mover(objetivo)
                self.actualizar_interfaz()
            elif objetivo == self.juego.pos_jugador:
                pass
            else:
                self.agregar_log(f"⚠️ ¡No puedes moverte a {objetivo}! No está directamente conectada.", "naranja")

        elif self.modo_accion == "disparar":
            self.juego.disparar(objetivo)
            self.modo_accion = "mover"
            self._actualizar_etiqueta_modo()
            self.actualizar_interfaz()

        elif self.modo_accion == "lanzar":
            self.juego.lanzar_piedra(objetivo)
            self.modo_accion = "mover"
            self._actualizar_etiqueta_modo()
            self.actualizar_interfaz()

    def mover_direccion(self, dx, dy):
        """Mueve al jugador usando desplazamiento relativo (N, S, E, O)."""
        if not self.juego.vivo:
            return

        x, y = self.juego.pos_jugador
        objetivo = (x + dx, y + dy)

        if self.modo_accion == "mover":
            self.juego.mover(objetivo)
        elif self.modo_accion == "disparar":
            self.juego.disparar(objetivo)
            self.modo_accion = "mover"
            self._actualizar_etiqueta_modo()
        elif self.modo_accion == "lanzar":
            self.juego.lanzar_piedra(objetivo)
            self.modo_accion = "mover"
            self._actualizar_etiqueta_modo()

        self.actualizar_interfaz()

    def activar_modo_disparar(self):
        if not self.juego.vivo or self.juego.flechas <= 0:
            self.agregar_log("⚠️ ¡No te quedan flechas!", "naranja")
            return
        self.modo_accion = "disparar"
        self._actualizar_etiqueta_modo()
        self.agregar_log("🏹 Modo DISPARAR activado: Haz clic en una casilla contigua o usa WASD/flechas.", "dorado")

    def activar_modo_lanzar(self):
        if not self.juego.vivo or self.juego.piedras <= 0:
            self.agregar_log("⚠️ ¡No te quedan piedras!", "naranja")
            return
        self.modo_accion = "lanzar"
        self._actualizar_etiqueta_modo()
        self.agregar_log("🪨 Modo LANZAR PIEDRA activado: Haz clic en una casilla contigua para tantear.", "dorado")

    def cancelar_modo(self):
        self.modo_accion = "mover"
        self._actualizar_etiqueta_modo()
        self.agregar_log("Modo de acción cancelado. Regresando a desplazamiento.", "normal")

    def accion_agarrar(self):
        if not self.juego.vivo:
            return
        self.juego.agarrar()
        self.actualizar_interfaz()

    def _actualizar_etiqueta_modo(self):
        if self.modo_accion == "mover":
            self.lbl_modo_actual.config(text="MODO: 🚶 Desplazarse", fg=COLOR_CYAN, bg="#24273a")
        elif self.modo_accion == "disparar":
            self.lbl_modo_actual.config(text="MODO: 🏹 Apuntando Flecha", fg=COLOR_DANGER, bg="#3b1e2e")
        elif self.modo_accion == "lanzar":
            self.lbl_modo_actual.config(text="MODO: 🪨 Lanzar Piedra", fg=COLOR_ORANGE, bg="#3b2e1e")

    def mostrar_ayuda(self):
        msg = (
            "📖 GUÍA DE SUPERVIVENCIA - MUNDO DEL WUMPUS:\n\n"
            "• Objetivo: Recoge el oro y regresa a (0, 0) para ganar.\n"
            "• Movimiento: Clic en casillas adyacentes o teclas WASD / Flechas.\n"
            "• Flecha (F): Solo tienes 1 flecha. Atraviesa pasillos en línea recta.\n"
            "• Piedras (P): Lánzalas para escuchar si hay pozos, Wumpus o murciélagos.\n"
            "• Oro (G / Espacio): Agárralo cuando brille.\n"
            "• ⚠️ Modo Cacería: Al tomar el oro, el Wumpus vivo te perseguirá.\n\n"
            "Percepciones:\n"
            "🦨 Hedor = Wumpus adyacente\n"
            "💨 Brisa = Pozo adyacente\n"
            "🦇 Aleteo = Murciélagos gigantes\n"
            "💥 Crujido = Derrumbe inestable"
        )
        messagebox.showinfo("Ayuda y Controles", msg)


def iniciar_gui():
    root = tk.Tk()
    app = WumpusGUI(root)
    root.mainloop()


if __name__ == "__main__":
    iniciar_gui()
