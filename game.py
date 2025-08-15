import pygame
import random
import sys

# 配置 & 全局状态
IMAGE_PATH = 'D:/2024爬虫/imgs/'
screen_width = 950  # 容纳滚动条的宽度
screen_height = 560
GAMEOVER = False
PAUSED = False
SELECTED_PLANT = None  # 当前选中要种植的植物类型


# 错误日志
def log_error(message):
    print(f"错误: {message}")


# 血量条绘制
def draw_health_bar(surface, x, y, current_hp, max_hp):
    bar_length = 50
    bar_height = 5
    fill = (current_hp / max_hp) * bar_length
    outline_rect = pygame.Rect(x, y, bar_length, bar_height)
    fill_rect = pygame.Rect(x, y, fill, bar_height)

    if current_hp / max_hp > 0.5:
        color = (0, 255, 0)  # 绿色
    elif current_hp / max_hp > 0.2:
        color = (255, 255, 0)  # 黄色
    else:
        color = (255, 0, 0)  # 红色

    pygame.draw.rect(surface, color, fill_rect)
    pygame.draw.rect(surface, (255, 255, 255), outline_rect, 1)


# 地图类
class Map():
    map_names_list = [IMAGE_PATH + 'map1.png', IMAGE_PATH + 'map2.png']

    def __init__(self, x, y, img_index):
        try:
            self.image = pygame.image.load(Map.map_names_list[img_index])
        except Exception as e:
            log_error(f"加载地图图片失败: {e}")
            self.image = pygame.Surface((80, 80))
            self.image.fill((100, 200, 100) if img_index == 0 else (120, 220, 120))
        self.position = (x, y)
        self.can_grow = True

    def load_map(self):
        MainGame.window.blit(self.image, self.position)


# 植物基类
class Plant(pygame.sprite.Sprite):
    def __init__(self):
        super(Plant, self).__init__()
        self.live = True

    def load_image(self):
        if hasattr(self, 'image') and hasattr(self, 'rect'):
            MainGame.window.blit(self.image, self.rect)
        else:
            log_error("植物图片加载失败")


# 向日葵
class Sunflower(Plant):
    def __init__(self, x, y):
        super(Sunflower, self).__init__()
        try:
            self.image = pygame.image.load(f'{IMAGE_PATH}sunflower.png')
        except Exception as e:
            log_error(f"加载向日葵图片失败: {e}")
            self.image = pygame.Surface((60, 60))
            self.image.fill((255, 255, 0))  # 黄色方块替代
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.price = 50
        self.hp = 100
        self.time_count = 0

    def produce_money(self):
        global PAUSED
        self.time_count += 1
        if self.time_count == 50 and not PAUSED:
            MainGame.money += 25
            self.time_count = 0

    def display_sunflower(self):
        MainGame.window.blit(self.image, self.rect)
        if self.hp < 100:
            draw_health_bar(MainGame.window, self.rect.x, self.rect.y - 10, self.hp, 100)


# 豌豆射手
class PeaShooter(Plant):
    def __init__(self, x, y):
        super(PeaShooter, self).__init__()
        try:
            self.image = pygame.image.load(f'{IMAGE_PATH}peashooter.png')
        except Exception as e:
            log_error(f"加载豌豆射手图片失败: {e}")
            self.image = pygame.Surface((60, 60))
            self.image.fill((0, 255, 0))  # 绿色方块替代
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.price = 100
        self.hp = 300
        self.shot_count = 0

    def shot(self):
        global PAUSED
        should_fire = False
        for zombie in MainGame.zombie_list:
            if zombie.rect.y == self.rect.y and zombie.rect.x < 800 and zombie.rect.x > self.rect.x:
                should_fire = True
        if self.live and should_fire and not PAUSED:
            self.shot_count += 1
            if self.shot_count == 30:  # 普通射速
                peabullet = PeaBullet(self)
                MainGame.peabullet_list.append(peabullet)
                self.shot_count = 0

    def display_peashooter(self):
        MainGame.window.blit(self.image, self.rect)
        if self.hp < 300:
            draw_health_bar(MainGame.window, self.rect.x, self.rect.y - 10, self.hp, 300)


# 双发豌豆射手
class DoublePeaShooter(Plant):
    def __init__(self, x, y):
        super(DoublePeaShooter, self).__init__()
        try:
            self.image = pygame.image.load(f'{IMAGE_PATH}peashooter1.png')
        except Exception as e:
            log_error(f"加载双发豌豆射手图片失败: {e}")
            self.image = pygame.Surface((60, 60))
            self.image.fill((0, 255, 255))  # 青色方块替代
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.price = 200  # 价格更高
        self.hp = 400  # 血量更高
        self.shot_count = 0

    def shot(self):
        global PAUSED
        should_fire = False
        for zombie in MainGame.zombie_list:
            if zombie.rect.y == self.rect.y and zombie.rect.x < 800 and zombie.rect.x > self.rect.x:
                should_fire = True

        if self.live and should_fire and not PAUSED:
            self.shot_count += 1
            # 双发逻辑：更快的射速，每次发射2颗子弹
            if self.shot_count == 15:  # 比普通豌豆射手快一倍
                # 连续发射两颗子弹
                for _ in range(2):
                    peabullet = PeaBullet(self)
                    MainGame.peabullet_list.append(peabullet)
                self.shot_count = 0

    def display_peashooter(self):
        MainGame.window.blit(self.image, self.rect)
        if self.hp < 400:
            draw_health_bar(
                MainGame.window,
                self.rect.x,
                self.rect.y - 10,
                self.hp,
                400
            )


# 豌豆子弹
class PeaBullet(pygame.sprite.Sprite):
    def __init__(self, peashooter):
        self.live = True
        try:
            self.image = pygame.image.load(f'{IMAGE_PATH}peabullet.png')
        except Exception as e:
            log_error(f"加载豌豆子弹图片失败: {e}")
            self.image = pygame.Surface((10, 5))
            self.image.fill((0, 255, 0))  # 绿色小方块替代
        self.damage = 75
        self.speed = 10
        self.rect = self.image.get_rect()
        self.rect.x = peashooter.rect.x + 60
        self.rect.y = peashooter.rect.y + 15

    def move_bullet(self):
        global PAUSED
        if self.rect.x < 800 and not PAUSED:
            self.rect.x += self.speed
        else:
            self.live = False

    def hit_zombie(self):
        for zombie in MainGame.zombie_list:
            if pygame.sprite.collide_rect(self, zombie):
                self.live = False
                zombie.hp -= self.damage
                if zombie.hp <= 0:
                    zombie.live = False
                    self.nextLevel()

    def nextLevel(self):
        MainGame.score += 20
        MainGame.remnant_score -= 20
        for i in range(1, 100):
            if MainGame.score == 100 * i and MainGame.remnant_score == 0:
                MainGame.remnant_score = 100 * i
                MainGame.shaoguan += 1
                MainGame.produce_zombie = max(30, MainGame.produce_zombie - 10)
                MainGame.money += 100
                MainGame.show_level_up = True
                MainGame.level_up_timer = 0

    def display_peabullet(self):
        MainGame.window.blit(self.image, self.rect)


# 僵尸类（修改精英僵尸图片为zombie1）
class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y, zombie_type=1):
        super(Zombie, self).__init__()
        self.zombie_type = zombie_type  # 1:普通僵尸, 2:精英僵尸

        try:
            # 普通僵尸使用原zombie图片，精英僵尸使用zombie1图片
            if self.zombie_type == 1:
                self.image = pygame.image.load(f'{IMAGE_PATH}zombie.png')
            else:  # 精英僵尸
                self.image = pygame.image.load(f'{IMAGE_PATH}zombie1.png')
        except Exception as e:
            log_error(f"加载僵尸图片失败: {e}")
            # 加载失败时用不同颜色方块替代
            self.image = pygame.Surface((60, 100))
            self.image.fill((0, 0, 255) if zombie_type == 1 else (139, 0, 0))  # 普通蓝色，精英深红色

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # 僵尸属性设置
        if self.zombie_type == 1:
            self.hp = 1500
            self.max_hp = 1500
            self.damage = 2
            self.speed = 1
        else:  # 精英僵尸属性
            self.hp = 3000
            self.max_hp = 3000
            self.damage = 4
            self.speed = 0.7
            # 精英僵尸稍微放大
            self.image = pygame.transform.scale(self.image, (int(self.rect.width * 1.2), int(self.rect.height * 1.2)))
            self.rect = self.image.get_rect(x=x, y=y - 10)

        self.live = True
        self.stop = False

    def move_zombie(self):
        global PAUSED
        if self.live and not self.stop and not PAUSED:
            self.rect.x -= self.speed
            if self.rect.x < -80:
                MainGame().gameOver()

    def hit_plant(self):
        global PAUSED
        if PAUSED:
            return
        for plant in MainGame.plants_list:
            if pygame.sprite.collide_rect(self, plant):
                self.stop = True
                self.eat_plant(plant)

    def eat_plant(self, plant):
        plant.hp -= self.damage
        if plant.hp <= 0:
            a = plant.rect.y // 80 - 1
            b = plant.rect.x // 80
            if 0 <= a < len(MainGame.map_list) and 0 <= b < len(MainGame.map_list[a]):
                map_block = MainGame.map_list[a][b]
                map_block.can_grow = True
                plant.live = False
                self.stop = False

    def display_zombie(self):
        MainGame.window.blit(self.image, self.rect)
        draw_health_bar(
            MainGame.window,
            self.rect.x,
            self.rect.y - 10,
            self.hp,
            self.max_hp
        )
        # 显示精英僵尸标识
        if self.zombie_type == 2:
            font = pygame.font.SysFont('kaiti', 14)
            text = font.render('精英', True, (255, 0, 0))
            MainGame.window.blit(text, (self.rect.x + 55, self.rect.y - 10))


# 植物选择滚动条
class PlantSelector:
    """植物选择滚动条：点击选择植物 → 地图左击种植"""

    def __init__(self):
        self.bar_x = 820  # 滚动条X坐标
        self.bar_y = 100  # 滚动条Y坐标
        self.bar_width = 120  # 滚动条宽度
        self.bar_height = 400  # 滚动条高度
        # 植物项：(植物类, 显示名称, 预览图路径, 价格, 是否选中)
        self.plants = [
            (Sunflower, "向日葵", f"{IMAGE_PATH}sunflower.png", 50, False),
            (PeaShooter, "豌豆射手", f"{IMAGE_PATH}peashooter.png", 100, False),
            (DoublePeaShooter, "双发豌豆", f"{IMAGE_PATH}peashooter1.png", 200, False),
        ]
        self.scroll_offset = 0  # 滚动偏移量
        self.item_height = 100  # 每个植物项高度

    def draw_selector(self):
        """绘制滚动条背景 + 植物项"""
        # 绘制滚动条背景
        pygame.draw.rect(
            MainGame.window,
            (200, 200, 200),
            (self.bar_x, self.bar_y, self.bar_width, self.bar_height)
        )
        pygame.draw.rect(
            MainGame.window,
            (100, 100, 100),
            (self.bar_x, self.bar_y, self.bar_width, self.bar_height),
            2  # 边框
        )

        # 绘制标题
        title = MainGame().draw_text("植物选择", 20, (0, 0, 0))
        MainGame.window.blit(title, (self.bar_x + 10, self.bar_y - 30))

        # 绘制植物项
        for i, (plant_class, name, img_path, price, is_selected) in enumerate(self.plants):
            item_y = self.bar_y + self.scroll_offset + i * self.item_height
            if item_y + self.item_height < self.bar_y:
                continue
            if item_y > self.bar_y + self.bar_height:
                break

            # 绘制项背景（选中时高亮）
            bg_color = (220, 220, 220) if not is_selected else (150, 255, 150)
            pygame.draw.rect(
                MainGame.window,
                bg_color,
                (self.bar_x + 5, item_y + 5, self.bar_width - 10, self.item_height - 10)
            )

            # 加载并绘制预览图
            try:
                img = pygame.image.load(img_path)
                img = pygame.transform.scale(img, (60, 60))
            except:
                img = pygame.Surface((60, 60))
                img.fill((200, 200, 200))  # 灰色方块替代

            MainGame.window.blit(img, (self.bar_x + 15, item_y + 10))

            # 绘制植物名称和价格
            font = pygame.font.SysFont('kaiti', 16)
            name_text = font.render(name, True, (0, 0, 0))
            price_text = font.render(f"${price}", True, (0, 150, 0))  # 价格绿色

            MainGame.window.blit(name_text, (self.bar_x + 15, item_y + 80))
            MainGame.window.blit(price_text, (self.bar_x + 70, item_y + 80))

    def handle_click(self, mouse_pos):
        """处理点击事件：选择植物 / 取消选择"""
        mx, my = mouse_pos
        if self.bar_x <= mx <= self.bar_x + self.bar_width and self.bar_y <= my <= self.bar_y + self.bar_height:
            for i, (_, _, _, _, is_selected) in enumerate(self.plants):
                item_y = self.bar_y + self.scroll_offset + i * self.item_height
                if item_y <= my <= item_y + self.item_height:
                    # 切换选中状态
                    for j in range(len(self.plants)):
                        self.plants[j] = (
                            self.plants[j][0],
                            self.plants[j][1],
                            self.plants[j][2],
                            self.plants[j][3],
                            False
                        )
                    self.plants[i] = (
                        self.plants[i][0],
                        self.plants[i][1],
                        self.plants[i][2],
                        self.plants[i][3],
                        True
                    )
                    global SELECTED_PLANT
                    SELECTED_PLANT = self.plants[i]
                    return True
        return False

    def handle_scroll(self, dy):
        """处理鼠标滚轮滚动"""
        max_offset = max(0, len(self.plants) * self.item_height - self.bar_height)
        self.scroll_offset = max(0, min(self.scroll_offset - dy, max_offset))


# 主游戏类
class MainGame():
    shaoguan = 1
    score = 0
    remnant_score = 100
    money = 300
    show_level_up = False
    level_up_timer = 0
    map_points_list = []
    map_list = []
    plants_list = []
    peabullet_list = []
    zombie_list = []
    count_zombie = 0
    produce_zombie = 100
    # 暂停按钮
    pause_button_rect = pygame.Rect(820, 10, 100, 30)
    pause_text = "暂停"
    # 植物选择器实例
    plant_selector = PlantSelector()

    def init_window(self):
        pygame.display.init()
        pygame.font.init()
        MainGame.window = pygame.display.set_mode([screen_width, screen_height])
        pygame.display.set_caption("植物大战僵尸（精英僵尸形象更新）")

    def draw_text(self, content, size, color):
        font = pygame.font.SysFont('kaiti', size)
        return font.render(content, True, color)

    def load_help_text(self):
        global PAUSED
        # 游戏操作提示
        text1 = self.draw_text('操作: 滚动条选择植物 → 地图左击种植', 22, (255, 0, 0))
        MainGame.window.blit(text1, (5, 5))

        # 暂停按钮
        pygame.draw.rect(MainGame.window, (200, 200, 200), MainGame.pause_button_rect)
        pygame.draw.rect(MainGame.window, (0, 0, 0), MainGame.pause_button_rect, 2)
        pause_text_surf = self.draw_text(MainGame.pause_text, 20, (0, 0, 0))
        text_rect = pause_text_surf.get_rect(center=MainGame.pause_button_rect.center)
        MainGame.window.blit(pause_text_surf, text_rect)

        # 显示暂停状态
        if PAUSED:
            pause_overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            pause_overlay.fill((0, 0, 0, 100))
            MainGame.window.blit(pause_overlay, (0, 0))
            paused_text = self.draw_text('游戏已暂停', 60, (255, 255, 255))
            text_rect = paused_text.get_rect(center=(400, screen_height // 2))
            MainGame.window.blit(paused_text, text_rect)

        # 显示关卡提升信息
        if MainGame.show_level_up:
            level_text = self.draw_text(f'进入第{MainGame.shaoguan}关!', 40, (255, 215, 0))
            text_rect = level_text.get_rect(center=(400, screen_height // 2 - 50))
            MainGame.window.blit(level_text, text_rect)
            MainGame.level_up_timer += 1
            if MainGame.level_up_timer > 100:
                MainGame.show_level_up = False

    def init_plant_points(self):
        for y in range(1, 7):
            points = []
            for x in range(10):
                point = (x, y)
                points.append(point)
            MainGame.map_points_list.append(points)

    def init_map(self):
        for points in MainGame.map_points_list:
            temp_map_list = list()
            for point in points:
                if (point[0] + point[1]) % 2 == 0:
                    map_block = Map(point[0] * 80, point[1] * 80, 0)
                else:
                    map_block = Map(point[0] * 80, point[1] * 80, 1)
                temp_map_list.append(map_block)
            MainGame.map_list.append(temp_map_list)

    def load_map(self):
        for temp_map_list in MainGame.map_list:
            for map_block in temp_map_list:
                map_block.load_map()

    def load_plants(self):
        global PAUSED
        for plant in list(MainGame.plants_list):
            if plant.live:
                if isinstance(plant, Sunflower):
                    plant.display_sunflower()
                    if not PAUSED:
                        plant.produce_money()
                elif isinstance(plant, PeaShooter) or isinstance(plant, DoublePeaShooter):
                    plant.display_peashooter()
                    plant.shot()
            else:
                MainGame.plants_list.remove(plant)

    def load_peabullets(self):
        for bullet in list(MainGame.peabullet_list):
            if bullet.live:
                bullet.display_peabullet()
                bullet.move_bullet()
                bullet.hit_zombie()
            else:
                MainGame.peabullet_list.remove(bullet)

    def deal_events(self):
        global PAUSED, SELECTED_PLANT
        eventList = pygame.event.get()
        for e in eventList:
            if e.type == pygame.QUIT:
                self.gameOver()

            elif e.type == pygame.MOUSEBUTTONDOWN:
                # 检查是否点击了暂停按钮
                if MainGame.pause_button_rect.collidepoint(e.pos):
                    PAUSED = not PAUSED
                    MainGame.pause_text = "继续" if PAUSED else "暂停"
                    return

                # 游戏暂停时不处理其他点击
                if PAUSED:
                    return

                # 处理植物选择器点击
                if MainGame.plant_selector.handle_click(e.pos):
                    return

                # 处理地图种植
                if SELECTED_PLANT and e.button == 1:
                    plant_class, _, _, price, _ = SELECTED_PLANT
                    x = e.pos[0] // 80
                    y = e.pos[1] // 80

                    if (0 <= y - 1 < len(MainGame.map_list) and
                            0 <= x < len(MainGame.map_list[y - 1]) and
                            e.pos[0] < 800):

                        map_block = MainGame.map_list[y - 1][x]
                        if map_block.can_grow and MainGame.money >= price:
                            plant = plant_class(map_block.position[0], map_block.position[1])
                            MainGame.plants_list.append(plant)
                            map_block.can_grow = False
                            MainGame.money -= price

            # 处理鼠标滚轮
            elif e.type == pygame.MOUSEWHEEL:
                MainGame.plant_selector.handle_scroll(e.y * 20)

            # 按P键暂停/继续
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_p:
                    PAUSED = not PAUSED
                    MainGame.pause_text = "继续" if PAUSED else "暂停"

    def init_zombies(self):
        for i in range(1, 7):
            # 随关卡提升增加精英僵尸概率
            zombie_type = 2 if random.random() < min(0.3, MainGame.shaoguan * 0.05) else 1
            dis = random.randint(1, 5) * 200
            zombie = Zombie(800 + dis, i * 80, zombie_type)
            MainGame.zombie_list.append(zombie)

    def load_zombies(self):
        for zombie in list(MainGame.zombie_list):
            if zombie.live:
                zombie.display_zombie()
                zombie.move_zombie()
                zombie.hit_plant()
            else:
                MainGame.zombie_list.remove(zombie)

    def start_game(self):
        global PAUSED
        self.init_window()
        self.init_plant_points()
        self.init_map()
        self.init_zombies()

        while not GAMEOVER:
            MainGame.window.fill((255, 255, 255))

            # 绘制状态信息
            MainGame.window.blit(
                self.draw_text(f'当前钱数$: {MainGame.money}', 26, (255, 0, 0)),
                (500, 40)
            )
            MainGame.window.blit(
                self.draw_text(
                    f'当前关数{MainGame.shaoguan}，得分{MainGame.score},距离下关还差{MainGame.remnant_score}分',
                    22, (255, 0, 0)
                ),
                (5, 40)
            )

            self.load_help_text()
            self.load_map()
            self.load_plants()
            self.load_peabullets()
            self.load_zombies()
            MainGame.plant_selector.draw_selector()
            self.deal_events()

            if not PAUSED:
                MainGame.count_zombie += 1
                if MainGame.count_zombie >= MainGame.produce_zombie:
                    self.init_zombies()
                    MainGame.count_zombie = 0

            pygame.time.Clock().tick(30)
            pygame.display.update()

    def gameOver(self):
        global GAMEOVER
        GAMEOVER = True
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        MainGame.window.blit(overlay, (0, 0))

        game_over_text = self.draw_text('游戏结束', 60, (255, 0, 0))
        score_text = self.draw_text(f'最终得分: {MainGame.score}', 30, (255, 255, 255))
        level_text = self.draw_text(f'达到关卡: {MainGame.shaoguan}', 30, (255, 255, 255))

        game_over_rect = game_over_text.get_rect(center=(400, screen_height // 2 - 50))
        score_rect = score_text.get_rect(center=(400, screen_height // 2 + 20))
        level_rect = level_text.get_rect(center=(400, screen_height // 2 + 60))

        MainGame.window.blit(game_over_text, game_over_rect)
        MainGame.window.blit(score_text, score_rect)
        MainGame.window.blit(level_text, level_rect)

        pygame.display.update()
        pygame.time.wait(5000)
        pygame.quit()
        sys.exit()


# 启动游戏
if __name__ == '__main__':
    game = MainGame()
    game.start_game()
