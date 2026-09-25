#!/usr/bin/env python3
"""Citrine Court — neon squash / hoop arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "CITRINE COURT"
HANDLE = "x.com/ElbowOS"
BG, INK = (18, 8, 6), (255, 246, 220)
GOLD, AMBER = (255, 196, 48), (255, 140, 32)
MAG, ROSE = (255, 64, 140), (255, 120, 170)
CREAM, DEEP = (255, 230, 170), (42, 16, 12)
LIME = (180, 255, 90)


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 64)
        self.font_md = pygame.font.Font(None, 46)
        self.font_sm = pygame.font.Font(None, 30)
        self.court = pygame.Rect(70, 250, W - 140, H - 430)
        self.reset()

    def reset(self) -> None:
        self.px = self.court.centerx
        self.pw = 210
        self.ph = 28
        self.py = self.court.bottom - 48
        self.bx = self.court.centerx
        self.by = self.court.centery + 80
        ang = random.uniform(-0.7, 0.7)
        spd = random.uniform(620, 780)
        self.bvx = spd * math.sin(ang)
        self.bvy = -spd * math.cos(ang)
        self.br = 22
        self.hoop_x = self.court.centerx
        self.hoop_w = 200
        self.hoop_y = self.court.top + 90
        self.hoop_vx = random.choice((-140, 140))
        self.gems = self._gems(6)
        self.score = getattr(self, "score", 0) if getattr(self, "keep_score", False) else 0
        self.keep_score = True
        self.sparks: list[Spark] = []
        self.pulse = 0.0
        self.flash = 0.0
        self.combo = 0

    def _gems(self, n: int):
        gems = []
        for i in range(n):
            gems.append({
                "x": random.uniform(self.court.left + 50, self.court.right - 50),
                "y": random.uniform(self.court.top + 180, self.court.bottom - 280),
                "r": random.randint(16, 24),
                "ph": random.random() * 6.28,
                "spin": random.uniform(1.4, 3.2),
            })
        return gems

    def burst(self, x, y, col, n=18) -> None:
        for _ in range(n):
            a = random.random() * 6.283
            spd = random.uniform(50, 380)
            self.sparks.append(Spark(x, y, spd * math.cos(a), spd * math.sin(a),
                                     random.uniform(0.22, 0.7), col, random.randint(3, 8)))

    def autoplay(self, dt: float) -> None:
        aim = self.bx + self.bvx * 0.18
        if self.bvy > 0:
            aim += (self.bx - self.px) * 0.05
        target = max(self.court.left + self.pw / 2, min(self.court.right - self.pw / 2, aim))
        self.px += (target - self.px) * min(1.0, 11.0 * dt)

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.flash = max(0.0, self.flash - dt)
        if self.record:
            self.autoplay(dt)
        else:
            keys = pygame.key.get_pressed()
            spd = 920
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.px -= spd * dt
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.px += spd * dt
        self.px = max(self.court.left + self.pw / 2, min(self.court.right - self.pw / 2, self.px))

        self.hoop_x += self.hoop_vx * dt
        if self.hoop_x - self.hoop_w / 2 < self.court.left + 20:
            self.hoop_x = self.court.left + 20 + self.hoop_w / 2
            self.hoop_vx = abs(self.hoop_vx)
        if self.hoop_x + self.hoop_w / 2 > self.court.right - 20:
            self.hoop_x = self.court.right - 20 - self.hoop_w / 2
            self.hoop_vx = -abs(self.hoop_vx)

        self.bvy += 420 * dt
        self.bx += self.bvx * dt
        self.by += self.bvy * dt

        if self.bx - self.br < self.court.left:
            self.bx = self.court.left + self.br
            self.bvx = abs(self.bvx) * 0.98
            self.burst(self.bx, self.by, AMBER, 8)
        if self.bx + self.br > self.court.right:
            self.bx = self.court.right - self.br
            self.bvx = -abs(self.bvx) * 0.98
            self.burst(self.bx, self.by, AMBER, 8)
        if self.by - self.br < self.court.top:
            self.by = self.court.top + self.br
            self.bvy = abs(self.bvy) * 0.96
            self.burst(self.bx, self.by, GOLD, 8)

        pad = pygame.Rect(self.px - self.pw / 2, self.py - self.ph / 2, self.pw, self.ph)
        if pad.collidepoint(self.bx, self.by + self.br) and self.bvy > 0:
            self.by = pad.top - self.br
            self.bvy = -abs(self.bvy) * 1.03 - 40
            off = (self.bx - self.px) / (self.pw / 2)
            self.bvx += off * 280
            cap = 900
            self.bvx = max(-cap, min(cap, self.bvx))
            self.bvy = max(-980, min(-360, self.bvy))
            self.burst(self.bx, self.by, ROSE, 12)
            self.score += 2

        hx0, hx1 = self.hoop_x - self.hoop_w / 2, self.hoop_x + self.hoop_w / 2
        if self.bvy < 0 and abs(self.by - self.hoop_y) < 18 and hx0 + 12 < self.bx < hx1 - 12:
            self.score += 40 + self.combo * 8
            self.combo += 1
            self.flash = 0.28
            self.burst(self.bx, self.hoop_y, GOLD, 28)
            self.bvy = abs(self.bvy) * 0.55
            self.hoop_vx *= -1.05
            self.hoop_vx = max(-240, min(240, self.hoop_vx))

        live = []
        for g in self.gems:
            g["ph"] += g["spin"] * dt
            g["x"] += math.sin(g["ph"]) * 18 * dt
            dx, dy = self.bx - g["x"], self.by - g["y"]
            if dx * dx + dy * dy < (self.br + g["r"]) ** 2:
                self.score += 15
                self.burst(g["x"], g["y"], MAG, 16)
                live.append({
                    "x": random.uniform(self.court.left + 50, self.court.right - 50),
                    "y": random.uniform(self.court.top + 180, self.court.bottom - 280),
                    "r": random.randint(16, 24),
                    "ph": random.random() * 6.28,
                    "spin": random.uniform(1.4, 3.2),
                })
            else:
                live.append(g)
        self.gems = live

        if self.by - self.br > self.court.bottom + 20:
            self.flash = 0.4
            self.combo = 0
            self.score = max(0, self.score - 8)
            self.burst(self.bx, self.court.bottom, MAG, 22)
            self.bx = self.court.centerx
            self.by = self.court.centery
            self.bvx = random.uniform(-220, 220)
            self.bvy = -640

        spd = math.hypot(self.bvx, self.bvy)
        if spd > 1000:
            self.bvx *= 1000 / spd
            self.bvy *= 1000 / spd

        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            sp.vy += 240 * dt
            alive.append(sp)
        self.sparks = alive

    def handle(self, ev) -> None:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
            self.keep_score = False
            self.reset()

    def draw(self, s: pygame.Surface) -> None:
        s.fill(BG)
        for i in range(16):
            y = int((self.pulse * 90 + i * 140) % (H + 60)) - 30
            pygame.draw.line(s, (48, 18, 10), (0, y), (W, y), 2)
        glow = 0.55 + 0.45 * math.sin(self.pulse * 3.4)
        pygame.draw.rect(s, DEEP, self.court.inflate(18, 18), border_radius=28)
        pygame.draw.rect(s, GOLD, self.court.inflate(18, 18), width=5, border_radius=28)
        pygame.draw.rect(s, (28, 10, 8), self.court, border_radius=16)
        for k in range(5):
            yy = self.court.top + 40 + k * 280
            pygame.draw.line(s, (70, 28, 16), (self.court.left + 16, yy), (self.court.right - 16, yy), 2)

        hx, hy, hw = int(self.hoop_x), int(self.hoop_y), int(self.hoop_w)
        pygame.draw.rect(s, (80, 20, 30), (hx - hw // 2 - 8, hy - 10, hw + 16, 20), border_radius=10)
        pygame.draw.rect(s, MAG, (hx - hw // 2, hy - 7, hw, 14), border_radius=8)
        pygame.draw.rect(s, INK, (hx - hw // 2 + 10, hy - 3, hw - 20, 6), border_radius=4)
        pygame.draw.circle(s, ROSE, (hx - hw // 2, hy), 12)
        pygame.draw.circle(s, ROSE, (hx + hw // 2, hy), 12)

        for g in self.gems:
            gx, gy, gr = int(g["x"]), int(g["y"]), g["r"]
            pts = []
            for i in range(6):
                a = g["ph"] + i * math.pi / 3
                pts.append((gx + int(math.cos(a) * gr), gy + int(math.sin(a) * gr)))
            pygame.draw.polygon(s, GOLD, pts)
            pygame.draw.polygon(s, AMBER, pts, 2)
            pygame.draw.circle(s, INK, (gx, gy), max(3, gr // 3))

        pad = pygame.Rect(int(self.px - self.pw / 2), int(self.py - self.ph / 2), int(self.pw), int(self.ph))
        pygame.draw.rect(s, ROSE, pad.inflate(10, 10), border_radius=16)
        pygame.draw.rect(s, GOLD, pad, border_radius=14)
        pygame.draw.rect(s, INK, pad.inflate(-18, -10), border_radius=8)

        bx, by = int(self.bx), int(self.by)
        pygame.draw.circle(s, (255, 80, 40), (bx, by), self.br + 8)
        pygame.draw.circle(s, GOLD, (bx, by), self.br)
        pygame.draw.circle(s, INK, (bx - 5, by - 6), 6)
        pygame.draw.circle(s, CREAM, (bx - 4, by - 7), 3)

        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x), int(sp.y)), max(1, int(sp.r * sp.life * 2)))

        title = self.font_lg.render(TITLE, True, GOLD)
        s.blit(title, title.get_rect(center=(W // 2, 72)))
        handle = self.font_sm.render(HANDLE, True, MAG)
        s.blit(handle, handle.get_rect(center=(W // 2, 122)))
        score = self.font_md.render(f"SCORE  {self.score}    COMBO  {self.combo}", True, CREAM)
        s.blit(score, score.get_rect(center=(W // 2, 186)))
        hint = self.font_sm.render("A / D  or  arrows  slide the paddle    R reset    hoop + gems", True, ROSE)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 58)))
        if self.flash > 0:
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            flash.fill((255, 180, 40, int(70 * glow * self.flash / 0.4)))
            s.blit(flash, (0, 0))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/CITRINE_COURT_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
