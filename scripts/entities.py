import math
import random

import pygame
import sympy as sp

from scripts.calculations import check_derivative, differentiate, format_expression, parse_expression
from scripts.spark import Spark


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {"up": False, "down": False, "right": False, "left": False}
        self.action = ""
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action("idle")
        self.last_movement = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {"up": False, "down": False, "right": False, "left": False}
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions["right"] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions["left"] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
        self.last_movement = movement
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0
        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        image = pygame.transform.flip(self.animation.img(), self.flip, False)
        surf.blit(image, (self.pos[0] - offset[0] + self.anim_offset[0],
                          self.pos[1] - offset[1] + self.anim_offset[1]))


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size, kind, function):
        super().__init__(game, "enemy", pos, size)
        self.kind = kind
        self.function = parse_expression(function)
        self.walking = 0
        if kind == "polynomial":
            self.max_health = None
        if kind == "hybrid":
            self.max_health = 1
        if kind in ["exponential", "trigonometric", "logarithmic"]:
            self.max_health = 2
        if kind == "boss_trigonometric":
            self.max_health = 6
        self.health = self.max_health

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions["right"] or self.collisions["left"]:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                self.shoot_at_player()
        elif random.random() < 0.01:
            self.walking = random.randint(30, 90)

        super().update(tilemap, movement=movement)
        self.set_action("run" if movement[0] != 0 else "idle")
        if abs(self.game.player.dashing) >= 50 and self.rect().colliderect(self.game.player.rect()):
            self.game.screenshake = max(16, self.game.screenshake)
            self.game.sfx["hit"].play()
            return True
        return False

    def shoot_at_player(self):
        if self.game.dead or self.game.won:
            return
        difference = (self.game.player.pos[0] - self.pos[0],
                      self.game.player.pos[1] - self.pos[1])
        if abs(difference[1]) >= 32 or abs(difference[0]) > 220:
            return
        if self.flip and difference[0] < 0:
            speed = -1.5
        elif not self.flip and difference[0] > 0:
            speed = 1.5
        else:
            return

        start = [self.rect().centerx + (7 if speed > 0 else -7), self.rect().centery]
        self.game.projectiles.append({
            "pos": start, "speed": speed, "timer": 0, "team": "enemy",
        })
        self.game.sfx["shoot"].play()
        for _ in range(4):
            angle = random.random() - 0.5 + (0 if speed > 0 else math.pi)
            self.game.sparks.append(Spark(start, angle, 2 + random.random()))

    def receive_answer(self, answer):
        if not check_derivative(answer, self.function):
            return False, False
        self.function = differentiate(self.function)
        if self.kind == "polynomial":
            defeated = sp.simplify(self.function) == 0
        else:
            self.health -= 1
            defeated = self.health <= 0
        return True, defeated

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        if self.flip:
            gun = pygame.transform.flip(self.game.assets["gun"], True, False)
            gun_x = self.rect().centerx - 4 - gun.get_width()
        else:
            gun = self.game.assets["gun"]
            gun_x = self.rect().centerx + 4
        surf.blit(gun, (gun_x - offset[0], self.rect().centery - offset[1]))

        label = self.game.font_small.render(
            format_expression(self.function),
            True, (255, 255, 255)
        )
        label_x = self.rect().centerx - label.get_width() // 2 - offset[0]
        label_y = self.rect().top - 24 - offset[1]
        label_x = max(1, min(surf.get_width() - label.get_width() - 1, label_x))
        pygame.draw.rect(surf, (24, 26, 39),
                         (label_x - 2, label_y - 1, label.get_width() + 4, label.get_height() + 2))
        surf.blit(label, (label_x, label_y))

        if self.max_health is not None:
            bar_width = 16
            bar_x = self.rect().centerx - bar_width // 2 - offset[0]
            bar_y = self.rect().top - 30 - offset[1]
            pygame.draw.rect(surf, (45, 45, 55), (bar_x, bar_y, bar_width, 3))
            fill_width = int(bar_width * self.health / self.max_health)
            if fill_width:
                pygame.draw.rect(surf, (245, 90, 94), (bar_x, bar_y, fill_width, 3))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        self.air_time = 0
        self.jumps = 2
        self.wall_slide = False
        self.dashing = 0
        self.shot_cooldown = 0

    def update(self, tilemap, movement=(0, 0)):
        if self.shot_cooldown:
            self.shot_cooldown -= 1

        super().update(tilemap, movement=movement)
        self.air_time += 1
        if self.air_time > 120 and not self.game.dead:
            self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead = 1
        if self.collisions["down"]:
            self.air_time = 0
            self.jumps = 2

        self.wall_slide = False
        if (self.collisions["right"] or self.collisions["left"]) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            self.flip = not self.collisions["right"]
            self.set_action("wall_slide")
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action("jump")
            elif movement[0] != 0:
                self.set_action("run")
            else:
                self.set_action("idle")
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def shoot(self, answer):
        if answer == "":
            answer = "0"
        if (self.shot_cooldown or self.game.dead or self.game.formulas_open
                or self.game.won):
            return

        direction = -1 if self.flip else 1
        start = [self.rect().centerx + direction * 9, self.rect().centery]
        self.game.projectiles.append({
            "pos": start, "speed": direction * 4, "timer": 0, "team": "player", "answer": answer,
        })
        self.shot_cooldown = 12
        self.game.sfx["shoot"].play()

        for _ in range(4):
            angle = random.random() - 0.5 + (0 if direction > 0 else math.pi)
            self.game.sparks.append(Spark(start, angle, 2 + random.random()))

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        if self.flip:
            gun = pygame.transform.flip(self.game.assets["gun"], True, False)
            gun_x = self.rect().centerx - 4 - gun.get_width()
        else:
            gun = self.game.assets["gun"]
            gun_x = self.rect().centerx + 4
        surf.blit(gun, (gun_x - offset[0], self.rect().centery - offset[1]))

    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0], self.velocity[1] = 3.5, -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            if not self.flip and self.last_movement[0] > 0:
                self.velocity[0], self.velocity[1] = -3.5, -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True
        return False
