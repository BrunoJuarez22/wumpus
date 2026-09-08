# 🏹 El Mundo del Wumpus (Wumpus World) en Python

Una implementación moderna, estratégica y dinámica en consola del clásico juego de inteligencia artificial y deducción **El Mundo del Wumpus**, modelado mediante **grafos no dirigidos** y algoritmos de búsqueda (**BFS**).

---

## 📖 Descripción del Juego

Eres un valiente aventurero que se adentra en una cueva oscura y peligrosa compuesta por una cuadrícula de $4 \times 4$ habitaciones. Tu objetivo es encontrar el **Oro**, recogerlo y regresar con vida a la casilla de inicio `(0, 0)`.

Sin embargo, la cueva está llena de peligros mortales y sorpresas:
- **El temible Wumpus:** Un monstruo subterráneo que te devorará si entras a su habitación... ¡y que empezará a cazarte en cuanto tomes el oro!
- **Pozos sin fondo:** Caer en uno significa una muerte instantánea.
- **Murciélagos gigantes (*Super Bats*):** Te arrebatarán por los aires y te soltarán en una habitación aleatoria de la cueva.
- **Desprendimientos de rocas:** Zonas inestables que pueden colapsar y bloquear permanentemente túneles en el grafo de la cueva.

---

## ⚙️ Modelado Matemático y Algoritmos

- **Grafo No Dirigido:** La cueva se modela como un grafo no dirigido con listas de adyacencia donde cada habitación $(x, y)$ se conecta bidireccionalmente con sus vecinos válidos en la cuadrícula.
- **Garantía de Solubilidad (BFS):** Cada mapa se valida automáticamente mediante Búsqueda en Anchura (BFS) para garantizar que el jugador nunca aparezca atrapado y que siempre exista una ruta transitable sin pozos hacia el oro y la victoria.
- **Cacería Inteligente:** Cuando el Wumpus entra en modo cacería, calcula mediante BFS la ruta más corta hacia el jugador esquivando pozos para perseguirlo activamente.
- **Grafo Dinámico:** Los derrumbes de rocas eliminan aristas del grafo en tiempo real, alterando la topología de la cueva de forma controlada sin aislar al jugador.

---

## 🎮 Comandos Disponibles

El analizador de comandos es flexible y admite múltiples formatos:

| Comando | Sintaxis Alternativa | Descripción |
| :--- | :--- | :--- |
| `mover X,Y` | `mover X Y`, `1,0` | Desplazarse a una habitación adyacente conectada. |
| `disparar X,Y`| `disparar X Y`, `flecha X Y` | Disparar tu única flecha en línea recta por todo el túnel. |
| `lanzar X,Y` | `piedra X Y`, `tirar X,Y` | Arrojar una piedra a una habitación contigua para escuchar qué hay (o distraer al Wumpus). |
| `agarrar` | `oro`, `tomar`, `coger` | Recoger el oro (¡activa el modo cacería si el Wumpus está vivo!). |
| `mapa` | `ver`, `m` | Mostrar el mapa de la cueva explorada con niebla de guerra. |
| `ayuda` | `help`, `?` | Mostrar la lista de comandos y opciones. |
| `salir` | `exit`, `q` | Abandonar la cueva y revelar el mapa completo. |

---

## 👂 Sistema de Percepciones Sensoriales

Al entrar a cada habitación, recibirás pistas del entorno:
- 🦨 **Hedor:** El Wumpus vivo está en una habitación contigua.
- 💨 **Brisa:** Hay al menos un pozo sin fondo en una habitación vecina.
- ✨ **Brillo:** Estás exactamente en la habitación que contiene el oro.
- 🦇 **Aleteo:** Hay murciélagos gigantes acechando en una habitación contigua.
- 💥 **Crujido:** El techo de una habitación cercana es inestable y puede sufrir un desprendimiento de rocas.

---

## 🚀 Requisitos e Instalación

No se requieren librerías externas; utiliza únicamente la biblioteca estándar de Python:

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/wumpus.git

# Entrar al directorio
cd wumpus

# Ejecutar el juego
python wunpus.py
```

---

## 👤 Autor
Desarrollado con pasión por los juegos clásicos de IA y la teoría de grafos.
