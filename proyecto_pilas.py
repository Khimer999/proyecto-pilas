from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import pygame


WIDTH, HEIGHT = 800, 600
ROOT = Path(__file__).resolve().parent
BACKGROUND = "#f3f6ef"
INK = "#172a23"
MUTED = "#52665d"
GREEN = "#195e46"
LINE = "#ccd8ce"
WHITE = "#ffffff"
RED = "#9c3434"

ASSETS = {
    "pila_final.png": (120, 208),
    "blanca.png": (70, 132),
    "verde.png": (70, 132),
    "negra.png": (70, 132),
    "contenedor.png": (95, 132),
    "pez.jpg": (232, 238),
}
IMAGE_CROPS = {
    "negra.png": (0, 0, 112, 237),
    "pez.jpg": (150, 46, 329, 367),
}
COMPONENTS = (
    ("Zinc", "Ánodo (−)", "#dcebf6"),
    ("Dióxido de manganeso", "Cátodo (+)", "#f0e4f4"),
    ("Acero", "Carcasa", "#e5ece8"),
)
DESTINATIONS = (
    ("blanca.png", "Aprovechables", "Caneca blanca"),
    ("verde.png", "Orgánicos", "Caneca verde"),
    ("negra.png", "No aprovechables", "Caneca negra"),
    ("contenedor.png", "Punto de recolección", "Para pilas usadas"),
)
ZONE = pygame.Rect(376, 144, 376, 334)
CONTINUE = pygame.Rect(532, 505, 220, 50)
RESTART = pygame.Rect(48, 473, 230, 48)
DESTINATION_CARDS = [
    pygame.Rect(48 + 180 * index, 192, 164, 258)
    for index in range(len(DESTINATIONS))
]


class Stage(Enum):
    ASSEMBLY = auto()
    DISPOSAL = auto()
    RESULT = auto()


@dataclass
class Component:
    name: str
    role: str
    color: str
    home: pygame.Rect
    placed: bool = False
    rect: pygame.Rect = field(init=False)

    def __post_init__(self):
        self.rect = self.home.copy()


def load_image(filename, bounds):
    path = ROOT / filename
    try:
        image = pygame.image.load(path).convert_alpha()
    except (OSError, pygame.error) as error:
        raise RuntimeError(f"No se pudo cargar {path.name}: {error}") from error
    if filename in IMAGE_CROPS:
        image = image.subsurface(IMAGE_CROPS[filename])
    size = image.get_rect().fit(pygame.Rect((0, 0), bounds)).size
    return pygame.transform.smoothscale(image, size)


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.images = {
            filename: load_image(filename, bounds)
            for filename, bounds in ASSETS.items()
        }
        self.fonts = {
            "title": pygame.font.SysFont("segoeui", 36, bold=True),
            "label": pygame.font.SysFont("segoeui", 19, bold=True),
            "body": pygame.font.SysFont("segoeui", 18),
            "small": pygame.font.SysFont("segoeui", 15),
        }
        self.reset()

    def reset(self):
        self.stage = Stage.ASSEMBLY
        self.components = [
            Component(name, role, color, pygame.Rect(48, 172 + 98 * i, 286, 76))
            for i, (name, role, color) in enumerate(COMPONENTS)
        ]
        self.dragged = None
        self.drag_offset = (0, 0)
        self.correct = False
        self.feedback = ""

    @property
    def assembled(self):
        return all(component.placed for component in self.components)

    def release_component(self, position=None):
        component = self.dragged
        self.dragged = None
        component.rect.topleft = component.home.topleft
        if position is not None and ZONE.collidepoint(position):
            component.placed = True
            self.feedback = (
                "¡Pila ensamblada! Pulsa Continuar."
                if self.assembled
                else f"{component.name} añadido al ensamblaje."
            )
        elif position is not None:
            self.feedback = "Suelta la pieza dentro de la zona de ensamblaje."

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_RETURN:
                if self.stage is Stage.ASSEMBLY and self.assembled:
                    self.stage = Stage.DISPOSAL
                elif self.stage is Stage.RESULT:
                    self.reset()
        elif event.type == pygame.WINDOWFOCUSLOST and self.dragged:
            self.release_component()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.dragged:
            x, y = event.pos
            dx, dy = self.drag_offset
            self.dragged.rect.topleft = (x - dx, y - dy)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragged:
            self.release_component(event.pos)
        return True

    def click(self, position):
        if self.stage is Stage.ASSEMBLY:
            if self.assembled and CONTINUE.collidepoint(position):
                self.stage = Stage.DISPOSAL
            elif self.dragged is None:
                for component in self.components:
                    if not component.placed and component.rect.collidepoint(position):
                        self.dragged = component
                        x, y = position
                        self.drag_offset = (x - component.rect.x, y - component.rect.y)
                        break
        elif self.stage is Stage.DISPOSAL:
            for (filename, _, _), rect in zip(DESTINATIONS, DESTINATION_CARDS):
                if rect.collidepoint(position):
                    self.correct = filename == "contenedor.png"
                    self.stage = Stage.RESULT
                    break
        elif RESTART.collidepoint(position):
            self.reset()

    def text(self, content, position, style="body", color=INK, *, center=False):
        image = self.fonts[style].render(content, True, color)
        rect = image.get_rect(center=position) if center else image.get_rect(topleft=position)
        self.screen.blit(image, rect)

    def card(self, rect, fill=WHITE, border=LINE):
        pygame.draw.rect(self.screen, fill, rect, border_radius=16)
        pygame.draw.rect(self.screen, border, rect, width=1, border_radius=16)

    def button(self, title, rect):
        color = "#267655" if rect.collidepoint(pygame.mouse.get_pos()) else GREEN
        pygame.draw.rect(self.screen, color, rect, border_radius=12)
        self.text(title, rect.center, "label", WHITE, center=True)

    def illustration(self, filename, center):
        image = self.images[filename]
        self.screen.blit(image, image.get_rect(center=center))

    def header(self, step, title, instructions):
        self.text(step, (48, 32), "small", GREEN)
        self.text(title, (48, 53), "title")
        self.text(instructions, (49, 108), color=MUTED)

    def draw_component(self, component):
        rect = component.rect
        self.card(rect, component.color)
        self.text(component.name, (rect.x + 17, rect.y + 13), "label")
        self.text(component.role, (rect.x + 17, rect.y + 42), "small", MUTED)

    def draw_assembly(self):
        self.header("PASO 1 DE 2", "Construye una pila alcalina",
                    "Arrastra las tres piezas de la izquierda a la zona de ensamblaje.")
        self.card(ZONE, "#e7eee4")
        self.text("Zona de ensamblaje", (ZONE.centerx, 174), "label", center=True)
        placed = [component for component in self.components if component.placed]
        if self.assembled:
            self.illustration("pila_final.png", (ZONE.centerx, 311))
        elif placed:
            for i, component in enumerate(placed):
                rect = pygame.Rect(ZONE.x + 33, 215 + i * 62, ZONE.width - 66, 47)
                self.card(rect, component.color)
                self.text(component.name, rect.center, "label", center=True)
        else:
            self.text("Suelta las piezas aquí", ZONE.center, color=MUTED, center=True)
        self.text(f"{len(placed)} de {len(self.components)} piezas colocadas",
                  (ZONE.centerx, 452), "small", GREEN, center=True)
        for component in self.components:
            if not component.placed and component is not self.dragged:
                self.draw_component(component)
        if self.feedback:
            self.text(self.feedback, (48, 513), color=GREEN)
        if self.assembled:
            self.button("Continuar", CONTINUE)
        if self.dragged:
            self.draw_component(self.dragged)

    def draw_disposal(self):
        self.header("PASO 2 DE 2", "La pila se agotó",
                    "Elige dónde entregar la pila usada.")
        for (filename, title, caption), rect in zip(DESTINATIONS, DESTINATION_CARDS):
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            self.card(rect, "#e7eee4" if hovered else WHITE, GREEN if hovered else LINE)
            self.illustration(filename, (rect.centerx, 286))
            self.text(title, (rect.centerx, 382), "small", INK, center=True)
            self.text(caption, (rect.centerx, 409), "small", MUTED, center=True)

    def draw_result(self):
        if self.correct:
            self.header("RESULTADO", "Elegiste bien",
                        "La pila usada va a un punto de recolección autorizado.")
            self.text("Allí se gestiona de forma segura", (48, 245), "label")
            self.text("y algunos materiales pueden recuperarse.", (48, 276))
            self.illustration("contenedor.png", (590, 280))
        else:
            self.header("RESULTADO", "La pila necesita otro destino",
                        "Llévala a un punto de recolección autorizado para pilas.")
            self.text("Una gestión inadecuada puede", (48, 245), "label", RED)
            self.text("contaminar el agua y el suelo.", (48, 276))
            self.illustration("pez.jpg", (590, 280))
        self.button("Jugar de nuevo", RESTART)

    def draw(self):
        self.screen.fill(BACKGROUND)
        self.text("R  Reiniciar     Esc  Salir", (48, 571), "small", MUTED)
        if self.stage is Stage.ASSEMBLY:
            self.draw_assembly()
        elif self.stage is Stage.DISPOSAL:
            self.draw_disposal()
        else:
            self.draw_result()


def main():
    pygame.display.init()
    pygame.font.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Reto de sostenibilidad · El ciclo de la pila")
        game = Game(screen)
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if not game.handle_event(event):
                    return
            game.draw()
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
