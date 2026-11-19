import math
import os
import random
import sys

import pygame

from scripts.calculations import ALLOWED_INPUTS, DERIVATIVE_FORMULAS
from scripts.clouds import Clouds
from scripts.enemy_data import LEVEL_ENEMIES
from scripts.entities import Enemy, Player
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.tilemap import Tilemap
from scripts.utils import Animation, load_image, load_images


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Derivative Defender")
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((640, 480), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((640, 480))
        self.clock = pygame.time.Clock()

        self.font_small = pygame.font.Font(None, 16)
        self.font = pygame.font.Font(None, 22)
        self.input_function = ""
        self.formulas_open = False
        self.won = False
        self.movement = [False, False]

        self.assets = {
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "player": load_image("entities/player.png"),
            "background": pygame.transform.smoothscale(load_image("background.png"), (640, 480)),
            "clouds": load_images("clouds"),
            "enemy/idle": Animation(load_images("entities/enemy/idle"), img_dur=6),
            "enemy/run": Animation(load_images("entities/enemy/run"), img_dur=4),
            "player/idle": Animation(load_images("entities/player/idle"), img_dur=6),
            "player/run": Animation(load_images("entities/player/run"), img_dur=4),
            "player/jump": Animation(load_images("entities/player/jump")),
            "player/slide": Animation(load_images("entities/player/slide")),
            "player/wall_slide": Animation(load_images("entities/player/wall_slide")),
            "particle/leaf": Animation(load_images("particles/leaf"), img_dur=20, loop=False),
            "particle/particle": Animation(load_images("particles/particle"), img_dur=6, loop=False),
            "gun": load_image("gun.png"),
            "projectile": load_image("projectile.png"),
        }

        self.sfx = {
            "jump": pygame.mixer.Sound("data/sfx/jump.wav"),
            "dash": pygame.mixer.Sound("data/sfx/dash.wav"),
            "hit": pygame.mixer.Sound("data/sfx/hit.wav"),
            "shoot": pygame.mixer.Sound("data/sfx/shoot.wav"),
            "ambience": pygame.mixer.Sound("data/sfx/ambience.wav"),
        }
        self.sfx["ambience"].set_volume(0.2)
        self.sfx["shoot"].set_volume(0.4)
        self.sfx["hit"].set_volume(0.8)
        self.sfx["dash"].set_volume(0.3)
        self.sfx["jump"].set_volume(0.7)

        self.clouds = Clouds(self.assets["clouds"], count=16)
        self.player = Player(self, (50, 50), (8, 15))
        self.tilemap = Tilemap(self, tile_size=16)
        self.level = 0
        self.last_level = max(
            int(name[:-5]) for name in os.listdir("data/maps")
            if name.endswith(".json") and name[:-5].isdigit()
        )
        self.load_level(self.level)
        self.screenshake = 0

    def load_level(self, map_id):
        self.tilemap.load("data/maps/" + str(map_id) + ".json")

        self.leaf_spawners = []
        for tree in self.tilemap.extract([("large_decor", 2)], keep=True):
            self.leaf_spawners.append(
                pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13)
            )

        spawners = self.tilemap.extract([("spawners", 0), ("spawners", 1)])
        player_spawners = [item for item in spawners if item["variant"] == 0]
        enemy_spawners = [item for item in spawners if item["variant"] == 1]

        if player_spawners:
            self.player.pos = list(player_spawners[0]["pos"])
        self.player.air_time = 0
        self.player.velocity = [0, 0]
        self.player.jumps = 2

        self.enemies = []
        definitions = LEVEL_ENEMIES[min(map_id, len(LEVEL_ENEMIES) - 1)]
        count = min(len(definitions), len(enemy_spawners))
        if count == 1:
            indexes = [0]
        else:
            indexes = [
                round(i * (len(enemy_spawners) - 1) / (count - 1))
                for i in range(count)
            ]

        for definition, index in zip(definitions, indexes):
            kind, function = definition
            self.enemies.append(
                Enemy(self, enemy_spawners[index]["pos"], (8, 15),
                      kind, function)
            )

        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        self.won = False
        self.win_timer = 0
        self.player.shot_cooldown = 0

    def update_projectiles(self, render_scroll):
        for projectile in self.projectiles.copy():
            projectile["pos"][0] += projectile["speed"]
            projectile["timer"] += 1
            image = self.assets["projectile"]
            draw_pos = (
                projectile["pos"][0] - image.get_width() / 2 - render_scroll[0],
                projectile["pos"][1] - image.get_height() / 2 - render_scroll[1],
            )
            self.display.blit(image, draw_pos)

            point = projectile["pos"]
            hitbox = pygame.Rect(int(point[0]) - 2, int(point[1]) - 2, 4, 4)
            remove = bool(self.tilemap.solid_check(point)) or projectile["timer"] > 100

            if not remove and projectile["team"] == "enemy":
                if not self.dead and hitbox.colliderect(self.player.rect()):
                    self.dead = 1
                    self.screenshake = max(16, self.screenshake)
                    self.sfx["hit"].play()
                    remove = True
            elif not remove and projectile["team"] == "player":
                for enemy in self.enemies.copy():
                    if not hitbox.colliderect(enemy.rect()):
                        continue

                    correct, defeated = enemy.receive_answer(projectile["answer"])
                    if correct:
                        self.sfx["hit"].play()
                        for _ in range(6):
                            self.sparks.append(
                                Spark(enemy.rect().center, random.random() * math.tau,
                                      2 + random.random())
                            )
                        if defeated:
                            self.enemies.remove(enemy)
                    remove = True
                    break

            if remove:
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)
                for _ in range(3):
                    angle = random.random() * math.tau
                    self.sparks.append(Spark(point, angle, 1.5 + random.random()))

    def draw_hud(self):
        pygame.draw.rect(self.display, (20, 22, 32), (8, 410, 624, 62))
        pygame.draw.rect(self.display, (112, 123, 158), (8, 410, 624, 62), 1)
        prompt = self.font_small.render(
            "DERIVATIVE ANSWER (type, then ENTER)", True, (173, 193, 255)
        )
        self.display.blit(prompt, (16, 418))
        answer = self.input_function[-38:] or "_"
        self.display.blit(self.font.render(answer, True, (255, 255, 255)), (16, 442))

        if self.formulas_open:
            self.draw_formula_help()

    def draw_win_message(self):
        panel = pygame.Rect(170, 180, 300, 100)
        pygame.draw.rect(self.display, (18, 21, 34), panel)
        pygame.draw.rect(self.display, (176, 194, 255), panel, 2)

        title = self.font.render("You Win!", True, (255, 238, 160))
        title_rect = title.get_rect(center=(panel.centerx, panel.y + 35))
        self.display.blit(title, title_rect)

        message = self.font_small.render(
            "Returning to the start...", True, (238, 240, 250)
        )
        message_rect = message.get_rect(center=(panel.centerx, panel.y + 70))
        self.display.blit(message, message_rect)

    def draw_formula_help(self):
        panel = pygame.Rect(86, 10, 468, 380)
        pygame.draw.rect(self.display, (18, 21, 34), panel)
        pygame.draw.rect(self.display, (176, 194, 255), panel, 1)
        title = self.font.render("DERIVATIVE QUICK GUIDE", True, (255, 238, 160))
        self.display.blit(title, (110, 20))
        for index, line in enumerate(DERIVATIVE_FORMULAS):
            image = self.font_small.render(line, True, (238, 240, 250))
            self.display.blit(image, (110, 50 + index * 24))
        close_text = self.font_small.render("Press q to close", True, (173, 193, 255))
        self.display.blit(close_text, (110, 500))

    def run(self):
        pygame.mixer.music.load("data/music.wav")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        self.sfx["ambience"].play(-1)

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets["background"], (0, 0))
            self.screenshake = max(0, self.screenshake - 1)
            if self.transition < 0:
                self.transition += 1

            if self.won:
                self.win_timer -= 1
                if self.win_timer <= 0:
                    self.level = 0
                    self.input_function = ""
                    self.load_level(self.level)
            elif not self.enemies and not self.dead:
                if self.level < self.last_level:
                    self.transition += 1
                    if self.transition > 30:
                        self.level += 1
                        self.load_level(self.level)
                else:
                    self.won = True
                    self.win_timer = 180

            if self.dead:
                self.dead += 1
                if self.dead > 40:
                    self.load_level(self.level)

            self.scroll[0] += (
                self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]
            ) / 30
            self.scroll[1] += (
                self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]
            ) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)
            self.tilemap.render(self.display, offset=render_scroll)

            if not self.formulas_open and not self.dead and not self.won:
                for rect in self.leaf_spawners:
                    if random.random() * 49999 < rect.width * rect.height:
                        pos = (rect.x + random.random() * rect.width,
                               rect.y + random.random() * rect.height)
                        self.particles.append(
                            Particle(self, "leaf", pos, velocity=[-0.1, 0.3],
                                     frame=random.randint(0, 20))
                        )

                for enemy in self.enemies.copy():
                    enemy.update(self.tilemap)
                    enemy.render(self.display, offset=render_scroll)

                self.player.update(
                    self.tilemap, (self.movement[1] - self.movement[0], 0)
                )
                self.player.render(self.display, offset=render_scroll)
                self.update_projectiles(render_scroll)

                for spark in self.sparks.copy():
                    if spark.update():
                        self.sparks.remove(spark)
                    else:
                        spark.render(self.display, offset=render_scroll)

                for particle in self.particles.copy():
                    kill = particle.update()
                    particle.render(self.display, offset=render_scroll)
                    if particle.type == "leaf":
                        particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                    if kill:
                        self.particles.remove(particle)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.formulas_open = not self.formulas_open
                        continue
                    if self.formulas_open or self.dead or self.won:
                        continue

                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key in (pygame.K_UP, pygame.K_SPACE):
                        if self.player.jump():
                            self.sfx["jump"].play()
                    if event.key == pygame.K_RETURN:
                        self.player.shoot(self.input_function)
                    if event.key == pygame.K_BACKSPACE:
                        self.input_function = self.input_function[:-1]
                    if event.key == pygame.K_DELETE:
                        self.input_function = ""
                    if event.unicode and event.unicode.lower() in ALLOWED_INPUTS:
                        if len(self.input_function) < 48:
                            self.input_function += event.unicode.lower()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                radius = max(0, (30 - abs(self.transition)) * 16)
                pygame.draw.circle(
                    transition_surf, (255, 255, 255),
                    (self.display.get_width() // 2, self.display.get_height() // 2),
                    radius
                )
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            self.draw_hud()
            if self.won:
                self.draw_win_message()
            self.display_2.blit(self.display, (0, 0))
            shake = self.screenshake
            shake_offset = (
                random.random() * shake - shake / 2,
                random.random() * shake - shake / 2,
            )
            self.screen.blit(
                self.display_2,
                shake_offset
            )
            pygame.display.update()
            self.clock.tick(60)


Game().run()
