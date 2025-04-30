#!/usr/bin/env python3
"""
Advanced Brick Breaker with Lives, Score, Items using Pygame

Usage:
    python breakout.py [path/to/brick_map.png]

Dependencies:
    python -m pip install pygame pillow

Features:
 - 3 Lives, displayed as red circles top-right
 - Score (10 pts per brick) shown top-left
 - Game Over popup with final score
 - Items drop only after 20% of bricks broken
   * Multiball: spawns 2 new balls (label "mul")
   * Paddle Expand: paddle width ×3 for 15 sec (label "exp")
   * Slow Ball: ball speed ×0.5 for 10 sec (label "slw")
"""
import sys, os, math, random
import pygame
from PIL import Image

# --- 설정값 ---
GRID_COUNT = 100           # 100×100 grid
DEFAULT_PADDLE_W = 128
PADDLE_H = 20              # paddle height
BALL_RADIUS = 8
BALL_SPEED = 300           # px/sec
BOTTOM_MARGIN = 100
FPS = 60
BRICK_SCORE = 10           # points per brick
ITEM_CHANCE = 0.1          # 10% chance after threshold
EXPAND_DURATION = 15000    # ms
SLOW_DURATION = 10000      # ms for slow ball
SLOW_FACTOR = 0.5          # ball speed multiplier

# 의존성 확인
try:
    pygame.init()
    pygame.font.init()
    from PIL import Image
except ImportError:
    print("python -m pip install pygame pillow 필요")
    sys.exit(1)

# 이미지 로드 및 bricks 생성
img_path = sys.argv[1] if len(sys.argv) > 1 else 'brick_map.png'
if not os.path.exists(img_path):
    print(f"이미지 없음: {img_path}")
    sys.exit(1)
pil = Image.open(img_path).convert('RGBA')
IMG_W, IMG_H = pil.size
TILE_W = IMG_W // GRID_COUNT
TILE_H = IMG_H // GRID_COUNT
cols, rows = GRID_COUNT, GRID_COUNT
bricks = []
for r in range(rows):
    for c in range(cols):
        tile = pil.crop((c*TILE_W, r*TILE_H, (c+1)*TILE_W, (r+1)*TILE_H))
        if tile.getbbox():
            surf = pygame.image.fromstring(tile.tobytes(), (TILE_W, TILE_H), 'RGBA')
            rect = pygame.Rect(c*TILE_W, r*TILE_H, TILE_W, TILE_H)
            bricks.append({'surf': surf, 'rect': rect})

# 전체 브릭 수 및 드롭 임계치
total_bricks = len(bricks)
bricks_broken = 0
drop_threshold = total_bricks * 0.01

# 화면 초기화
screen_w = cols * TILE_W
screen_h = rows * TILE_H + BOTTOM_MARGIN
screen = pygame.display.set_mode((screen_w, screen_h))
clock = pygame.time.Clock()
pygame.display.set_caption('Advanced Brick Breaker')
font = pygame.font.SysFont(None, 24)
bigfont = pygame.font.SysFont(None, 64)

# 게임 상태 초기화
lives = 3
score = 0
balls = [{'x': screen_w//2, 'y': screen_h - BOTTOM_MARGIN - BALL_RADIUS*2, 'vx': 0, 'vy': 0}]
paddle_w = DEFAULT_PADDLE_W
paddle = pygame.Rect((screen_w-paddle_w)//2, screen_h-PADDLE_H-10, paddle_w, PADDLE_H)
items = []  # 파워업 낙하 리스트
expand_end = 0
slow_end = 0
game_over = False

# 멀티볼 생성 함수
def spawn_ball(centerx):
    ang = random.uniform(math.radians(30), math.radians(150))
    return {
        'x': centerx,
        'y': paddle.top - BALL_RADIUS*2,
        'vx': BALL_SPEED * math.cos(ang),
        'vy': -BALL_SPEED * math.sin(ang)
    }

# 메인 루프
while True:
    dt = clock.tick(FPS)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            sys.exit(0)
        if not game_over:
            if e.type == pygame.MOUSEMOTION:
                mx, _ = e.pos
                paddle.x = max(0, min(mx - paddle_w//2, screen_w - paddle_w))
                # 대기 중인 공은 패들에 붙여 이동
                for b in balls:
                    if b['vx'] == 0 and b['vy'] == 0:
                        b['x'] = paddle.centerx
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for b in balls:
                    if b['vx'] == 0 and b['vy'] == 0:
                        click_x, _ = e.pos
                        rel = (click_x - paddle.centerx) / (paddle_w / 2)
                        max_angle = math.radians(75)
                        angle = rel * max_angle
                        b['vx'] = BALL_SPEED * math.sin(angle)
                        b['vy'] = -abs(BALL_SPEED * math.cos(angle))

    if not game_over:
        now = pygame.time.get_ticks()
        # 패들 확장 타이머
        if expand_end and now > expand_end:
            paddle_w = DEFAULT_PADDLE_W
            expand_end = 0
        # 슬로우 타이머 복원
        if slow_end and now > slow_end:
            for b in balls:
                speed = math.hypot(b['vx'], b['vy'])
                ratio = BALL_SPEED / speed
                b['vx'] *= ratio
                b['vy'] *= ratio
            slow_end = 0

        # 공 이동 및 충돌
        for b in list(balls):
            b['x'] += b['vx'] * dt / 1000
            b['y'] += b['vy'] * dt / 1000
            # 벽 충돌
            if b['x'] - BALL_RADIUS < 0 or b['x'] + BALL_RADIUS > screen_w:
                b['vx'] *= -1
            if b['y'] - BALL_RADIUS < 0:
                b['vy'] *= -1
            # 바닥(out)
            if b['y'] - BALL_RADIUS > screen_h:
                balls.remove(b)
                lives -= 1
                if lives > 0:
                    balls.append({'x': paddle.centerx, 'y': paddle.top - BALL_RADIUS*2, 'vx': 0, 'vy': 0})
                continue
            # 패들 반사
            if paddle.collidepoint(b['x'], b['y'] + BALL_RADIUS):
                rel = (b['x'] - paddle.centerx) / (paddle_w / 2)
                max_angle = math.radians(75)
                bounce = rel * max_angle
                speed = math.hypot(b['vx'], b['vy'])
                b['vx'] = speed * math.sin(bounce)
                b['vy'] = -abs(speed * math.cos(bounce))
            # 브릭 충돌
            ball_rect = pygame.Rect(b['x'] - BALL_RADIUS, b['y'] - BALL_RADIUS, BALL_RADIUS*2, BALL_RADIUS*2)
            for br in list(bricks):
                if br['rect'].colliderect(ball_rect):
                    bricks.remove(br)
                    score += BRICK_SCORE
                    bricks_broken += 1
                    b['vy'] *= -1
                    # 아이템 드롭: 20% 이상 깨진 후 확률 적용
                    if bricks_broken >= drop_threshold and random.random() < ITEM_CHANCE:
                        itype = random.choice(['multiball', 'expand', 'slow'])
                        items.append({
                            'type': itype,
                            'rect': pygame.Rect(br['rect'].centerx, br['rect'].centery, 16, 16),
                            'vy': 100
                        })
                    break

        # 아이템 낙하 및 획득
        for it in list(items):
            it['rect'].y += it['vy'] * dt / 1000
            if it['rect'].colliderect(paddle):
                if it['type'] == 'multiball':
                    balls.extend([spawn_ball(paddle.centerx), spawn_ball(paddle.centerx)])
                elif it['type'] == 'expand':
                    paddle_w = DEFAULT_PADDLE_W * 3
                    expand_end = pygame.time.get_ticks() + EXPAND_DURATION
                elif it['type'] == 'slow':
                    for b in balls:
                        b['vx'] *= SLOW_FACTOR
                        b['vy'] *= SLOW_FACTOR
                    slow_end = pygame.time.get_ticks() + SLOW_DURATION
                items.remove(it)
            elif it['rect'].y > screen_h:
                items.remove(it)

        if lives <= 0:
            game_over = True

    # 그리기
    screen.fill((0, 0, 0))
    for br in bricks:
        screen.blit(br['surf'], br['rect'])
    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(paddle.x, paddle.y, paddle_w, PADDLE_H))
    # 공: 항상 빨간색
    for b in balls:
        pygame.draw.circle(screen, (255, 0, 0), (int(b['x']), int(b['y'])), BALL_RADIUS)
    # 목숨 표시
    for i in range(lives):
        pygame.draw.circle(screen, (255, 0, 0), (screen_w - 20 - i*20, 20), 8)
    # 점수 표시
    scr_s = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(scr_s, (10, 10))
    # 아이템 표시 (텍스트 레이블)
    text_map = {'multiball': 'mul', 'expand': 'exp', 'slow': 'slw'}
    for it in items:
        label = text_map[it['type']]
        text_surf = font.render(label, True, (255, 255, 255))
        label_rect = text_surf.get_rect(center=it['rect'].center)
        screen.blit(text_surf, label_rect)  

    # 게임 오버 표시
    if game_over:
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        go = bigfont.render("GAME OVER", True, (255, 50, 50))
        screen.blit(go, ((screen_w - go.get_width())//2, screen_h//2 - 50))
        fs = font.render(f"Final Score: {score}", True, (255, 255, 255))
        screen.blit(fs, ((screen_w - fs.get_width())//2, screen_h//2 + 20))

    pygame.display.flip()
