import pygame
import os
import sys
import pymorphy2

# ---------- GLOBAL ----------


WIDTH, HEIGHT = 800, 600
SIZE = WIDTH, HEIGHT
CLOCK = pygame.time.Clock()
T_WIDTH = T_HEIGHT = 50
FPS = 30


# ---------- GROUPS ----------


def init_groups():
    global all_sprites, \
        tile_sprites, \
        solid_sprites, \
        win_sprites, \
        mob_sprites, \
        obj_sprites, \
        bubble_gen_sprites, \
        bubbles_sprites, \
        oxytile_sprites

    all_sprites = pygame.sprite.Group()
    tile_sprites = pygame.sprite.Group()
    solid_sprites = pygame.sprite.Group()
    win_sprites = pygame.sprite.Group()
    mob_sprites = pygame.sprite.Group()
    obj_sprites = pygame.sprite.Group()
    bubble_gen_sprites = pygame.sprite.Group()
    bubbles_sprites = pygame.sprite.Group()
    oxytile_sprites = pygame.sprite.Group()


init_groups()


# -------- FUNCTIONS ---------


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def load_level(filename):
    filename = "data/" + filename

    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


# --------- CLASSES ----------


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - HEIGHT // 2)


class Tile(pygame.sprite.Sprite):
    def __init__(self, texture='empty', x=0, y=0, passable=False):
        super(Tile, self).__init__(all_sprites, tile_sprites)
        if not passable:
            self.add(solid_sprites)
            self.image = pygame.transform.scale(assets[texture], (T_WIDTH, T_HEIGHT))
        else:
            self.image = assets[texture]
        self.passable = passable
        self.rect = self.image.get_rect().move(x * T_WIDTH, y * T_HEIGHT)


class WinTile(Tile):
    def __init__(self, texture='empty', x=0, y=0, passable=False):
        super().__init__(texture, x, y, passable)
        self.add(win_sprites)


class OxyTile(Tile):
    def __init__(self, texture='empty', x=0, y=0, passable=False):
        super().__init__(texture, x, y, passable)
        self.add(oxytile_sprites)


class BubbleGenerator(Tile):
    def __init__(self, texture='empty', x=0, y=0, passable=False):
        super().__init__(texture, x, y, passable)
        self.add(bubble_gen_sprites)
        self.bubbles = []
        self.cd_max = 22
        self.countdown = 0

    def generate_bubble(self):
        new = Bubble(*self.rect.midtop, bubble_anim, 20)
        self.bubbles.append(new)

    def update(self):
        if self.countdown >= self.cd_max:
            self.generate_bubble()
            self.countdown = -1
        self.countdown += 1


class Map:
    def __init__(self, map_file):
        self.map_list = load_level(map_file)
        self.size_x, self.size_y = len(self.map_list), len(self.map_list[0])
        self.tiles = []

    def generate_map(self):
        turtle_obj, x, y = None, None, None
        for y in range(len(self.map_list)):
            for x in range(len(self.map_list[y])):
                if self.map_list[y][x] == '.':
                    tile = Tile('empty', x, y, True)
                elif self.map_list[y][x] == '#':
                    tile = Tile('wall', x, y)
                elif self.map_list[y][x] == '%':
                    tile = Tile('coral', x, y)
                elif self.map_list[y][x] == '-':
                    tile = WinTile('empty', x, y, True)
                elif self.map_list[y][x] == '$':
                    tile = BubbleGenerator('bubblegen', x, y, True)
                elif self.map_list[y][x] == '^':
                    tile = OxyTile('empty', x, y, True)
                elif self.map_list[y][x] == '@':
                    tile = Tile('empty', x, y, True)
                    turtle_obj = Turtle(x, y, turtle_anim)
                self.tiles.append(tile)
        return turtle_obj, x, y


class Mob(pygame.sprite.Sprite):
    def __init__(self, x, y, sheets):  # sheets = list[tuple[name: str, file: pygame.image, cols: int, rows: int]]
        super(Mob, self).__init__(all_sprites, mob_sprites)
        self.frame = 0
        self.sheets = {}
        for name, sheet, cols, rows in sheets:
            self.cut_sheet(name, sheet, cols, rows)
        self.sheet = 'err'
        self.image = self.sheets[self.sheet][self.frame]
        self.rect = self.image.get_rect().move(x * T_WIDTH, y * T_HEIGHT)
        self.x_speed = 0
        self.y_speed = 0
        self.gravity = 1
        self.countdown = 0
        self.anim_speed = 3

    def cut_sheet(self, name, sheet, columns, rows):
        if 'err' not in self.sheets.keys():
            self.sheets['err'] = [assets['err'].subsurface(pygame.Rect(
                (0, 0), assets['err'].get_size()))]
        self.sheets[name] = []
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.sheets[name].append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        if self.countdown >= self.anim_speed:
            self.frame = (self.frame + 1) % len(self.sheets[self.sheet])
            self.image = self.sheets[self.sheet][self.frame]
            self.rect = self.image.get_rect().move(self.rect.x, self.rect.y)
            self.countdown = 0
        else:
            self.countdown += 1


class Turtle(Mob):
    def __init__(self, x, y, sheets):
        super().__init__(x, y, sheets)
        self.sheet = 'run_right'
        self.image = self.sheets[self.sheet][0]
        self.direction = 'run_left'
        self.falling = False
        self.jumping = False
        self.moving = False
        self.hp_max = 80
        self.oxy_max = 2000
        self.hp = 80
        self.oxy = 1000
        self.healthbar = Bar(self, 0, self.rect.h // 2 + 5, self.rect.width, 10)
        self.oxybar = Bar(self, 0, self.rect.h // 2 + 20, self.rect.width, 10,
                          pygame.color.Color("#00B7EB"), pygame.color.Color("#808080"))

    def run_right(self):
        self.direction = 'run_right'
        self.sheet = 'run_right'
        self.x_speed = 10

    def run_left(self):
        self.direction = 'run_left'
        self.sheet = 'run_left'
        self.x_speed = -10

    def jump(self):
        if self.falling or self.jumping:
            return
        self.jumping = True
        self.y_speed = -18

    def fall(self):
        self.jumping = False
        self.falling = True
        self.y_speed = 0
        print("actfall")

    def hook_keyboard(self):
        keys = pygame.key.get_pressed()
        self.x_speed = 0
        self.moving = False
        if keys[pygame.K_a]:
            self.moving = True
            self.run_left()
        elif keys[pygame.K_d]:
            self.moving = True
            self.run_right()
        if keys[pygame.K_SPACE]:
            self.moving = True
            self.jump()
        if keys[pygame.K_g]:  # debug
            self.hp -= 1
            if self.hp < 0:
                self.hp = 20

    def is_collide_flat(self):
        if pygame.sprite.spritecollideany(self, solid_sprites):
            target = pygame.sprite.spritecollide(self, solid_sprites, False)[0]
            if self.rect.left < target.rect.right and self.x_speed < 0:
                self.rect.left = target.rect.right
                self.x_speed = 0
                print('rightx')
            elif self.rect.right > target.rect.left and self.x_speed > 0:
                self.rect.right = target.rect.left
                self.x_speed = 0
                print('leftx')

    def is_collide_updown(self):
        if not pygame.sprite.spritecollideany(self, solid_sprites):
            return
        target = pygame.sprite.spritecollide(self, solid_sprites, False)[0]
        if win_sprites in target.groups():
            return
        # pygame.draw.rect(screen, pygame.color.Color(0, 255, 0), target.rect)
        if self.rect.top < target.rect.bottom and self.y_speed < 0:
            print(self.y_speed)
            self.rect.top = target.rect.bottom
            self.fall()
        elif self.rect.bottom > target.rect.top and self.y_speed >= 0 and not self.jumping and self.falling:
            self.rect.bottom = target.rect.top
            self.falling = False
            self.y_speed = 0
            print('s1')

    def will_fall(self):
        self.rect = self.rect.move(0, 2)
        if pygame.sprite.spritecollideany(self, solid_sprites):
            target = pygame.sprite.spritecollide(self, solid_sprites, False)[0]
            if self.rect.bottom > target.rect.top:
                self.rect = self.rect.move(0, -2)
                return False
        else:
            self.rect = self.rect.move(0, -2)
            return True

    def apply_movement(self):
        if self.will_fall() and not self.falling and not self.jumping:
            self.falling = True
            print("willfall")
        if self.direction == 'run_right':
            self.rect = self.rect.move(self.x_speed, 0)
            self.is_collide_flat()
        elif self.direction == 'run_left':
            self.rect = self.rect.move(self.x_speed, 0)
            self.is_collide_flat()
        if self.jumping:
            self.y_speed += self.gravity
            print("jump")
            if self.y_speed >= 0:
                self.jumping = False
                self.falling = True
                self.apply_movement()
                print("j-")
                return
            self.rect = self.rect.move(0, self.y_speed)
            self.is_collide_updown()
        elif self.falling:
            self.y_speed += self.gravity
            self.rect = self.rect.move(0, self.y_speed)
            self.is_collide_updown()

    def handle_bubbles(self):
        global bubbles_eaten
        touched = []
        for sprite in bubbles_sprites:
            if pygame.sprite.collide_rect(self, sprite):
                touched.append(sprite)
        if not touched:
            return
        for sprite in touched:
            if sprite.dying:
                continue
            self.oxy = min(self.oxy_max, self.oxy + 400)
            bubbles_eaten += 1
            sprite.pop()

    def handle_health(self):
        if pygame.sprite.spritecollideany(self, oxytile_sprites):
            return
        self.oxy = max(0, self.oxy - 10)
        if self.oxy <= 0:
            self.hp -= 1

    def update(self):
        # pygame.draw.rect(screen, pygame.color.Color(255, 0, 0), self.rect)
        self.healthbar.update(self.hp_max, self.hp)
        self.oxybar.update(self.oxy_max, self.oxy)
        self.apply_movement()
        self.handle_bubbles()
        self.handle_health()
        if self.falling:
            print("fa")
        if self.jumping:
            print("jp")
        if self.falling or self.jumping or self.moving:
            super().update()


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, sheets):  # sheets = list[tuple[name: str, file: pygame.image, cols: int, rows: int]]
        super().__init__(all_sprites)
        self.frame = 0
        self.sheets = {}
        for name, sheet, cols, rows in sheets:
            self.cut_sheet(name, sheet, cols, rows)
        self.sheet = 'fly'
        self.image = self.sheets[self.sheet][self.frame]
        self.rect = self.image.get_rect().move(x, y)
        self.countdown = 0
        self.anim_speed = 3

    def cut_sheet(self, name, sheet, columns, rows):
        if 'err' not in self.sheets.keys():
            self.sheets['err'] = [assets['err'].subsurface(pygame.Rect(
                (0, 0), assets['err'].get_size()))]
        self.sheets[name] = []
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.sheets[name].append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        if self.countdown == self.anim_speed:
            self.frame = (self.frame + 1) % len(self.sheets[self.sheet])
            self.image = self.sheets[self.sheet][self.frame]
            self.rect = self.image.get_rect().move(self.rect.x, self.rect.y)
            self.countdown = 0
        else:
            self.countdown += 1


class Bubble(Object):
    def __init__(self, x, y, sheets, duration):
        super().__init__(x, y, sheets)
        self.sheet = 'fly'
        self.add(bubbles_sprites)
        self.duration = duration
        self.gravity = -1
        self.dying = False
        print(self.rect.x, self.rect.y)

    def is_collide_updown(self):
        if not pygame.sprite.spritecollideany(self, solid_sprites):
            return
        target = pygame.sprite.spritecollide(self, solid_sprites, False)[0]
        if win_sprites in target.groups():
            self.pop()
            return
        # pygame.draw.rect(screen, pygame.color.Color(255, 255, 0), target.rect)
        # if self.rect.top < target.rect.bottom:
        # self.rect.top = target.rect.bottom

    def apply_movement(self):
        self.rect = self.rect.move(0, self.gravity)
        self.is_collide_updown()

    def pop(self):
        self.sheet = 'pop'
        self.dying = True
        self.countdown = 0
        self.anim_speed = 3

    def update(self):
        self.apply_movement()
        if self.countdown == self.anim_speed:
            self.duration -= 1
            print(self.duration, self.sheet, self.frame, len(self.sheets[self.sheet]))
            if self.duration <= 0 and not self.dying:
                self.pop()
            if self.dying and self.frame == len(self.sheets[self.sheet]) - 1:
                self.kill()
        super().update()
        # print('upd')


class Bar:
    def __init__(self, target=None, x_offset=0, y_offset=0, x_size=0, y_size=0,
                 full_color=pygame.color.Color("green"), none_color=pygame.color.Color("red")):
        self.target = target
        self.x_off = x_offset
        self.y_off = y_offset
        self.size = (x_size, y_size)
        self.fcolor = full_color
        self.ncolor = none_color

    def update(self, full, remain):
        if self.target is None:
            self.x = self.x_off
            self.y = self.y_off
        else:
            self.x = self.target.rect.x + self.x_off
            self.y = self.target.rect.y + self.y_off
        fxsize = int(self.size[0] * min(full, max(0, remain)) / full)
        pygame.draw.rect(screen, self.fcolor, pygame.rect.Rect(self.x, self.y,
                                                               fxsize, self.size[1]))

        pygame.draw.rect(screen, self.ncolor, pygame.rect.Rect(self.x + fxsize,
                                                               self.y, self.size[0] - fxsize, self.size[1]))


# ----------------------------

def start_screen():
    intro_text = ["ЧЕРЕПАШКА - В ПОИСКАХ ДОМА", "",
                  "Правила игры:",
                  "Вы - черепашка, которой нужно выбраться из морской пучины",
                  "Управление: влево/вправо - AD, прыжок - Пробел",
                  "Задыхаетесь? Подберите пузыри из подводных залежей воздуха"]

    fon = pygame.transform.scale(load_image('bg.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        CLOCK.tick(FPS)


def win_screen():
    intro_text = ["Вы выиграли!", "",
                  "Поздравляю, вы спасли черепашку,",
                  f"собрав при этом {bubbles_eaten} "
                  f"{pymorphy2.MorphAnalyzer().parse('пузырёк')[0].make_agree_with_number(bubbles_eaten).word}!"]

    fon = pygame.transform.scale(load_image('bg.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                sys.exit()
        pygame.display.flip()
        CLOCK.tick(FPS)


def death_screen():
    intro_text = ["Вы проиграли!", "",
                  "Черепашка не вернулась домой",
                  "Попробуйте ещё раз!"]

    fon = pygame.transform.scale(load_image('bg.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        CLOCK.tick(FPS)


# ----------- INIT -----------

pygame.init()
screen = pygame.display.set_mode(SIZE)

# ---------- ASSETS ----------

assets = {
    'empty': load_image('empty.png'),
    'wall': load_image('sand_type1.png'),
    'coral': load_image('sand_type2.png'),
    'err': load_image('err.png'),
    'bg': pygame.transform.scale(load_image('bg.jpg'), (1200, 600)),
    'bubblegen': load_image('bubblegen.png')
}

turtle_anim = [
    ('run_left', load_image('turtle_run_left.png'), 3, 1),
    ('run_right', load_image('turtle_run_right.png'), 3, 1)
]

bubble_anim = [
    ('fly', load_image('bubble_fly.png'), 3, 1),
    ('pop', load_image('bubble_pop.png'), 3, 1)
]

maps = ['level0.txt', 'level1.txt']

# ------- GAME PROCESS -------

start_screen()

map_idx = 0
turtle, *map_size = Map(maps[map_idx]).generate_map()
bubbles_eaten = 0
camera = Camera()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((0, 0, 0))
    screen.blit(assets['bg'], (0, 0))
    turtle.hook_keyboard()
    for sprite in all_sprites:
        camera.apply(sprite)
    all_sprites.draw(screen)
    turtle.update()
    camera.update(turtle)
    if turtle.hp <= 0:
        death_screen()
        map_idx = 0
        init_groups()
        turtle, *map_size = Map(maps[map_idx]).generate_map()
    for sprite in bubble_gen_sprites:
        sprite.update()
    for sprite in win_sprites:
        if pygame.sprite.collide_rect(turtle, sprite):
            if map_idx == len(maps) - 1:
                win_screen()
                break
            map_idx += 1
            init_groups()
            turtle, *map_size = Map(maps[map_idx]).generate_map()
    for sprite in bubbles_sprites:
        sprite.update()
    CLOCK.tick(FPS)
    pygame.display.flip()
