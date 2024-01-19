import pygame
import os
import sys

# ---------- GLOBAL ----------


WIDTH, HEIGHT = 800, 600
SIZE = WIDTH, HEIGHT
CLOCK = pygame.time.Clock()
T_WIDTH = T_HEIGHT = 50

# ---------- GROUPS ----------


all_sprites = pygame.sprite.Group()
tile_sprites = pygame.sprite.Group()
solid_sprites = pygame.sprite.Group()
mob_sprites = pygame.sprite.Group()

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
        self.passable = passable
        self.rect = self.image.get_rect().move(x * T_WIDTH, y * T_HEIGHT)


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
        self.gravity = 5

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
        self.frame = (self.frame + 1) % len(self.sheets[self.sheet])
        self.image = self.sheets[self.sheet][self.frame]
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y)


class Turtle(Mob):
    def __init__(self, x, y, sheets):
        super().__init__(x, y, sheets)
        self.sheet = 'run_left'
        self.direction = 'run_left'
        self.falling = False
        self.jumping = False

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
        self.y_speed = -10

    def fall(self):
        self.jumping = False
        self.falling = True
        self.y_speed = 0
        print("actfall")

    def hook_keyboard(self):
        keys = pygame.key.get_pressed()
        self.x_speed = 0
        self.y_speed = 0
        if keys[pygame.K_a]:
            self.run_left()
        elif keys[pygame.K_d]:
            self.run_right()
        if keys[pygame.K_SPACE]:
            self.jump()

    def is_collide_flat(self):
        if pygame.sprite.spritecollideany(self, solid_sprites):
            target = pygame.sprite.spritecollide(self, solid_sprites, False)[0]
            pygame.draw.rect(screen, pygame.color.Color(0, 255, 0), target.rect)
            if self.rect.left < target.rect.right and self.x_speed < 0:
                self.rect.left = target.rect.right
                self.x_speed = 0
                print('rightx')
            elif self.rect.right > target.rect.left and self.x_speed > 0:
                self.rect.right = target.rect.left
                self.x_speed = 0
                print('leftx')

    def is_collide_updown(self):
        if pygame.sprite.spritecollideany(self, solid_sprites):
            target = pygame.sprite.spritecollide(self, solid_sprites, False)[0]
            pygame.draw.rect(screen, pygame.color.Color(0, 255, 0), target.rect)
            if self.rect.top < target.rect.bottom and self.y_speed < 0:
                print(self.y_speed)
                self.rect.top = target.rect.bottom
                self.fall()
            elif self.rect.bottom > target.rect.top and self.y_speed >= 0:
                self.rect.bottom = target.rect.top
                self.falling = False
                self.y_speed = 0
                print('s1')
            else:
                self.falling = False
                self.y_speed = 0

    def will_fall(self):
        self.rect = self.rect.move(0, self.rect.h)
        if pygame.sprite.spritecollideany(self, solid_sprites):
            target = pygame.sprite.spritecollide(self, solid_sprites, False)[0]
            if self.rect.bottom > target.rect.top:
                self.rect = self.rect.move(0, -self.rect.h)
                return False
        else:
            self.rect = self.rect.move(0, -self.rect.h)
            return True

    def apply_movement(self):
        if self.will_fall() and not self.jumping:
            self.falling = True
        if self.direction == 'run_right':
            self.rect = self.rect.move(self.x_speed, 0)
            self.is_collide_flat()
        elif self.direction == 'run_left':
            self.rect = self.rect.move(self.x_speed, 0)
            self.is_collide_flat()
        if self.jumping:
            self.y_speed += self.gravity
            if self.y_speed >= 0:
                self.jumping = False
                self.falling = True
                self.apply_movement()
            self.rect = self.rect.move(0, self.y_speed)
            self.is_collide_updown()
        elif self.falling:
            self.y_speed += self.gravity
            self.rect = self.rect.move(0, self.y_speed)
            self.is_collide_updown()

    def update(self):
        self.apply_movement()
        if self.falling:
            print("fa")
        super().update()
        pygame.draw.rect(screen, pygame.color.Color(255, 0, 0), self.rect)
# ----------- INIT -----------


pygame.init()
screen = pygame.display.set_mode(SIZE)


# ---------- ASSETS ----------

assets = {
    'empty': load_image('empty.png'),
    'wall': load_image('asset_type5.png'),
    'err': load_image('err.png')
    # 'bg': load_image('background.png')
}

turtle_anim = [
    ('run_left', load_image('turtle_run_left.png'), 3, 1),
    ('run_right', load_image('turtle_run_right.png'), 3, 1)
]

maps = {
    'test': 'level0.txt',
}


# ------- GAME PROCESS -------


turtle, *map_size = Map(maps['test']).generate_map()
camera = Camera()
# a = AnimatedSprite(load_image("aaa.png"), 3, 1, WIDTH // 2, HEIGHT // 2)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((0, 0, 0))
    turtle.hook_keyboard()
    turtle.update()
    camera.update(turtle)
    for sprite in all_sprites:
        camera.apply(sprite)
    # a.update()
    all_sprites.draw(screen)
    CLOCK.tick(30)
    pygame.display.flip()