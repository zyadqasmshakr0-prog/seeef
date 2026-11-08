import pygame
import random
import math


GROUND_Y = 570
WORLD_WIDTH = 35000


# ---------------------------------------------------------
# أسماء وأجواء المراحل
# ---------------------------------------------------------

STAGE_THEMES = [
    "meadows",
    "forest",
    "autumn",
    "pine",
    "mountains",
    "snow_mountains",
    "valley",
    "cliffs",

    "village",
    "stone_city",
    "royal_city",
    "war_city",
    "ruined_city",
    "night_city",
    "rain_city",
    "fog_city",

    "castle",
    "black_castle",
    "royal_palace",
    "mountain_castle",
    "siege_castle",
    "ice_castle",
    "fire_castle",
    "abandoned_castle",

    "desert",
    "gold_desert",
    "sand_valley",
    "desert_city",
    "desert_ruins",
    "sandstorm",
    "night_desert",
    "red_desert",

    "volcano",
    "fire_land",
    "hell",
    "hell_castle",
    "burned_land",
    "erupting_volcano",
    "lava_valley",
    "red_world",

    "ice",
    "ice_mountain",
    "ice_palace",
    "snowstorm",
    "frozen_village",
    "ice_cave",
    "white_land",
    "polar_night",

    "graveyard",
    "dead_city",
    "dark_forest",
    "haunted_castle",
    "dark_valley",
    "ancient_ruins",
    "fog_world",
    "ghost_world",

    "coast",
    "islands",
    "storm_sea",
    "coastal_city",
    "star_world",
    "space",
    "alien_planet",
    "final_world",
]


# ---------------------------------------------------------
# ألوان كل نوع عالم
# ---------------------------------------------------------

THEME_COLORS = {
    "meadows": ((105, 190, 245), (90, 150, 70), (105, 75, 45)),
    "forest": ((75, 145, 190), (40, 115, 45), (75, 65, 45)),
    "autumn": ((190, 135, 95), (150, 95, 45), (100, 65, 40)),
    "pine": ((80, 130, 155), (35, 80, 55), (70, 70, 65)),

    "mountains": ((105, 165, 210), (75, 120, 65), (90, 75, 55)),
    "snow_mountains": ((125, 175, 215), (220, 225, 225), (100, 105, 110)),
    "valley": ((95, 165, 205), (65, 125, 65), (85, 70, 50)),
    "cliffs": ((80, 125, 155), (85, 100, 70), (75, 65, 55)),

    "village": ((130, 185, 225), (80, 145, 65), (105, 75, 45)),
    "stone_city": ((115, 145, 175), (80, 110, 75), (90, 90, 85)),
    "royal_city": ((100, 160, 220), (65, 125, 65), (110, 85, 55)),
    "war_city": ((100, 110, 125), (70, 80, 65), (75, 65, 60)),
    "ruined_city": ((90, 100, 115), (70, 80, 60), (65, 60, 55)),
    "night_city": ((25, 35, 70), (40, 65, 45), (45, 45, 50)),
    "rain_city": ((70, 95, 120), (50, 85, 60), (65, 65, 65)),
    "fog_city": ((135, 145, 150), (90, 105, 90), (85, 80, 75)),

    "castle": ((100, 155, 210), (70, 120, 65), (100, 90, 75)),
    "black_castle": ((35, 40, 55), (45, 60, 50), (55, 55, 60)),
    "royal_palace": ((120, 180, 230), (70, 135, 70), (120, 95, 60)),
    "mountain_castle": ((80, 120, 160), (75, 95, 75), (85, 80, 75)),
    "siege_castle": ((80, 85, 100), (60, 75, 55), (65, 60, 55)),
    "ice_castle": ((100, 165, 210), (190, 215, 225), (120, 135, 145)),
    "fire_castle": ((95, 55, 50), (80, 65, 45), (70, 45, 40)),
    "abandoned_castle": ((65, 75, 85), (55, 70, 55), (65, 65, 65)),

    "desert": ((235, 185, 115), (190, 145, 65), (135, 95, 55)),
    "gold_desert": ((245, 205, 125), (210, 165, 70), (145, 105, 60)),
    "sand_valley": ((220, 170, 105), (175, 125, 55), (125, 90, 55)),
    "desert_city": ((230, 180, 115), (180, 135, 65), (145, 105, 65)),
    "desert_ruins": ((205, 160, 110), (155, 125, 70), (125, 95, 65)),
    "sandstorm": ((190, 145, 100), (150, 115, 65), (115, 85, 60)),
    "night_desert": ((35, 45, 80), (80, 75, 45), (75, 60, 50)),
    "red_desert": ((180, 85, 65), (125, 85, 50), (105, 65, 50)),

    "volcano": ((75, 45, 50), (75, 60, 40), (65, 45, 40)),
    "fire_land": ((100, 45, 35), (80, 55, 35), (65, 40, 35)),
    "hell": ((45, 20, 25), (70, 35, 30), (45, 30, 30)),
    "hell_castle": ((35, 20, 25), (65, 35, 30), (45, 25, 25)),
    "burned_land": ((60, 55, 55), (55, 55, 45), (50, 45, 45)),
    "erupting_volcano": ((75, 35, 30), (65, 50, 35), (55, 40, 35)),
    "lava_valley": ((55, 25, 25), (70, 40, 30), (45, 30, 25)),
    "red_world": ((85, 25, 30), (75, 40, 35), (50, 30, 30)),

    "ice": ((165, 210, 235), (210, 225, 230), (165, 180, 190)),
    "ice_mountain": ((130, 185, 220), (220, 235, 240), (155, 170, 180)),
    "ice_palace": ((110, 180, 225), (210, 230, 240), (145, 165, 180)),
    "snowstorm": ((150, 170, 185), (210, 220, 225), (145, 155, 160)),
    "frozen_village": ((140, 185, 215), (190, 215, 225), (135, 150, 160)),
    "ice_cave": ((55, 95, 130), (110, 145, 165), (70, 85, 100)),
    "white_land": ((205, 225, 235), (230, 240, 240), (190, 200, 205)),
    "polar_night": ((20, 35, 65), (75, 105, 125), (65, 75, 90)),

    "graveyard": ((45, 55, 70), (50, 65, 50), (55, 55, 55)),
    "dead_city": ((45, 50, 60), (45, 55, 45), (50, 50, 50)),
    "dark_forest": ((25, 45, 40), (25, 70, 35), (45, 50, 40)),
    "haunted_castle": ((25, 25, 40), (40, 45, 40), (45, 40, 45)),
    "dark_valley": ((35, 45, 55), (40, 60, 45), (50, 45, 45)),
    "ancient_ruins": ((55, 60, 65), (55, 70, 55), (65, 60, 55)),
    "fog_world": ((100, 105, 115), (75, 85, 75), (70, 70, 70)),
    "ghost_world": ((35, 45, 65), (45, 65, 65), (50, 55, 65)),

    "coast": ((80, 180, 225), (70, 150, 75), (120, 105, 70)),
    "islands": ((70, 170, 220), (70, 155, 70), (115, 95, 65)),
    "storm_sea": ((45, 70, 95), (55, 90, 70), (75, 75, 70)),
    "coastal_city": ((90, 175, 220), (65, 130, 70), (110, 100, 75)),
    "star_world": ((20, 30, 65), (45, 75, 65), (50, 55, 70)),
    "space": ((5, 8, 25), (25, 35, 40), (30, 30, 40)),
    "alien_planet": ((35, 70, 85), (70, 105, 70), (65, 55, 75)),
    "final_world": ((10, 10, 25), (55, 70, 65), (45, 40, 55)),
}


# ---------------------------------------------------------
# العالم
# ---------------------------------------------------------

class World:

    def __init__(self, stage=1):

        self.stage = max(1, min(64, stage))

        self.theme = STAGE_THEMES[self.stage - 1]

        self.width = WORLD_WIDTH
        self.ground_y = GROUND_Y

        self.trees = []
        self.castles = []
        self.obstacles = []
        self.buildings = []
        self.mountains = []
        self.clouds = []
        self.stars = []
        self.particles = []
        self._sky_cache_surface = None
        self._sky_cache_key = None
        self._fog_cache_surface = None
        self._fog_cache_size = None

        self.rng = random.Random(
            self.stage * 918273
        )

        self.generate_stage()

    # -----------------------------------------------------
    # توليد المرحلة
    # -----------------------------------------------------

    def generate_stage(self):

        r = self.rng

        # الجبال
        for x in range(
            -200,
            self.width + 500,
            r.randint(350, 500)
        ):
            self.mountains.append({
                "x": x,
                "height": r.randint(130, 280),
                "width": r.randint(300, 500),
            })

        # السحب
        if self.theme not in (
            "space",
            "alien_planet",
            "final_world",
        ):
            for x in range(
                -200,
                self.width + 500,
                r.randint(300, 600)
            ):
                self.clouds.append({
                    "x": x,
                    "y": r.randint(60, 230),
                    "size": r.randint(50, 110),
                })

        # النجوم
        if self.theme in (
            "night_city",
            "night_desert",
            "polar_night",
            "graveyard",
            "dead_city",
            "dark_forest",
            "haunted_castle",
            "ghost_world",
            "star_world",
            "space",
            "alien_planet",
            "final_world",
        ):
            for i in range(180):
                self.stars.append({
                    "x": r.randint(0, self.width),
                    "y": r.randint(20, 430),
                    "size": r.choice([1, 1, 2, 2, 3]),
                })

        # أشجار
        tree_themes = (
            "meadows",
            "forest",
            "autumn",
            "pine",
            "valley",
            "village",
            "dark_forest",
            "coast",
            "islands",
        )

        if self.theme in tree_themes:

            x = 180

            while x < self.width - 150:

                self.trees.append({
                    "x": x,
                    "size": r.randint(75, 145),
                    "type": r.randint(0, 3),
                })

                x += r.randint(170, 350)

        # القصور
        castle_themes = (
            "castle",
            "black_castle",
            "royal_palace",
            "mountain_castle",
            "siege_castle",
            "ice_castle",
            "fire_castle",
            "abandoned_castle",
            "hell_castle",
            "haunted_castle",
            "final_world",
        )

        if self.theme in castle_themes:

            x = 700

            while x < self.width - 400:

                self.castles.append({
                    "x": x,
                    "size": r.randint(170, 300),
                    "type": r.randint(0, 2),
                })

                x += r.randint(750, 1200)

        # المدن والمباني
        city_themes = (
            "village",
            "stone_city",
            "royal_city",
            "war_city",
            "ruined_city",
            "night_city",
            "rain_city",
            "fog_city",
            "desert_city",
            "dead_city",
            "coastal_city",
        )

        if self.theme in city_themes:

            x = 150

            while x < self.width:

                self.buildings.append({
                    "x": x,
                    "width": r.randint(70, 150),
                    "height": r.randint(100, 240),
                    "roof": r.randint(0, 2),
                })

                x += r.randint(130, 240)

        # العقبات
        x = 300

        while x < self.width - 100:

            if r.random() < 0.55:

                self.obstacles.append({
                    "x": x,
                    "width": r.randint(45, 100),
                    "height": r.randint(35, 90),
                    "type": r.randint(0, 3),
                })

            x += r.randint(250, 450)

    # -----------------------------------------------------
    # لون الجبال
    # -----------------------------------------------------

    def _mountain_color(self):

        if self.theme in (
            "snow_mountains",
            "ice",
            "ice_mountain",
            "white_land",
        ):
            return (190, 205, 215)

        if self.theme in (
            "volcano",
            "fire_land",
            "hell",
            "red_world",
            "lava_valley",
        ):
            return (75, 45, 45)

        if self.theme in (
            "graveyard",
            "dead_city",
            "dark_forest",
            "haunted_castle",
            "final_world",
        ):
            return (45, 50, 55)

        return (85, 115, 130)

    # -----------------------------------------------------
    # السحاب
    # -----------------------------------------------------

    def _draw_cloud(
        self,
        screen,
        x,
        y,
        size
    ):

        color = (225, 230, 230)

        pygame.draw.circle(
            screen,
            color,
            (int(x), int(y)),
            size // 3
        )

        pygame.draw.circle(
            screen,
            color,
            (
                int(x + size // 3),
                int(y - 15)
            ),
            size // 4
        )

        pygame.draw.circle(
            screen,
            color,
            (
                int(x + size // 2),
                int(y)
            ),
            size // 3
        )

        pygame.draw.rect(
            screen,
            color,
            (
                int(x - size // 3),
                int(y),
                size,
                size // 4
            )
        )

    # -----------------------------------------------------
    # الأرض
    # -----------------------------------------------------

    def draw_ground(self, screen):

        width, height = screen.get_size()

        sky, grass, ground = THEME_COLORS[
            self.theme
        ]

        pygame.draw.rect(
            screen,
            ground,
            (
                0,
                self.ground_y,
                width,
                height - self.ground_y
            )
        )

        pygame.draw.rect(
            screen,
            grass,
            (
                0,
                self.ground_y - 10,
                width,
                10
            )
        )

        # أرض الصحراء
        if "desert" in self.theme or self.theme in (
            "sand_valley",
            "red_desert",
        ):

            for x in range(0, width, 80):

                pygame.draw.arc(
                    screen,
                    (160, 115, 60),
                    (
                        x,
                        self.ground_y + 20,
                        80,
                        30
                    ),
                    0,
                    math.pi,
                    2
                )

        # الثلج
        if self.theme in (
            "ice",
            "ice_mountain",
            "ice_palace",
            "snowstorm",
            "frozen_village",
            "ice_cave",
            "white_land",
            "polar_night",
        ):

            pygame.draw.rect(
                screen,
                (225, 235, 240),
                (
                    0,
                    self.ground_y - 10,
                    width,
                    10
                )
            )

        # الحمم
        if self.theme in (
            "volcano",
            "fire_land",
            "hell",
            "hell_castle",
            "erupting_volcano",
            "lava_valley",
            "red_world",
        ):

            for x in range(30, width, 130):

                pygame.draw.line(
                    screen,
                    (230, 75, 25),
                    (
                        x,
                        self.ground_y + 20
                    ),
                    (
                        x + 40,
                        self.ground_y + 50
                    ),
                    5
                )

    # -----------------------------------------------------
    # الأشجار
    # -----------------------------------------------------

    def draw_tree(
        self,
        screen,
        x,
        size,
        tree_type
    ):

        ground = self.ground_y

        trunk_width = max(
            10,
            size // 7
        )

        trunk_height = size // 2

        pygame.draw.rect(
            screen,
            (90, 55, 30),
            (
                x - trunk_width // 2,
                ground - trunk_height,
                trunk_width,
                trunk_height
            )
        )

        if self.theme == "autumn":

            colors = [
                (190, 80, 35),
                (220, 125, 35),
                (165, 55, 30),
            ]

        elif self.theme == "pine":

            colors = [
                (25, 80, 50),
                (30, 105, 55),
                (20, 65, 45),
            ]

        elif self.theme == "dark_forest":

            colors = [
                (20, 65, 35),
                (25, 80, 40),
                (15, 50, 30),
            ]

        else:

            colors = [
                (35, 120, 45),
                (45, 145, 50),
                (30, 100, 40),
            ]

        color = colors[
            tree_type % len(colors)
        ]

        if tree_type == 3:

            pygame.draw.polygon(
                screen,
                color,
                [
                    (x, ground - size),
                    (
                        x - size // 2,
                        ground - size // 3
                    ),
                    (
                        x + size // 2,
                        ground - size // 3
                    ),
                ]
            )

        else:

            pygame.draw.circle(
                screen,
                color,
                (
                    x,
                    ground - size + 20
                ),
                size // 3
            )

            pygame.draw.circle(
                screen,
                color,
                (
                    x - size // 4,
                    ground - size + 35
                ),
                size // 3
            )

            pygame.draw.circle(
                screen,
                color,
                (
                    x + size // 4,
                    ground - size + 35
                ),
                size // 3
            )

    # -----------------------------------------------------
    # القلاع والقصور
    # -----------------------------------------------------

    def draw_castle(
        self,
        screen,
        x,
        size,
        castle_type
    ):

        ground = self.ground_y

        wall_width = size
        wall_height = int(
            size * 0.65
        )

        left = int(
            x - wall_width / 2
        )

        top = int(
            ground - wall_height
        )

        if self.theme in (
            "black_castle",
            "haunted_castle",
            "hell_castle",
        ):

            wall = (55, 55, 65)
            roof = (35, 25, 35)

        elif self.theme in (
            "ice_castle",
            "ice_palace",
        ):

            wall = (185, 220, 235)
            roof = (100, 155, 200)

        elif self.theme in (
            "fire_castle",
            "hell_castle",
        ):

            wall = (95, 55, 45)
            roof = (50, 30, 30)

        else:

            wall = (145, 140, 130)
            roof = (100, 50, 45)

        # جسم القصر
        pygame.draw.rect(
            screen,
            wall,
            (
                left,
                top,
                wall_width,
                wall_height
            )
        )

        tower_width = max(
            35,
            size // 5
        )

        tower_height = int(
            size * 0.95
        )

        for tower_x in (
            left,
            left + wall_width - tower_width
        ):

            pygame.draw.rect(
                screen,
                wall,
                (
                    tower_x,
                    ground - tower_height,
                    tower_width,
                    tower_height
                )
            )

            pygame.draw.polygon(
                screen,
                roof,
                [
                    (
                        tower_x - 5,
                        ground - tower_height
                    ),
                    (
                        tower_x + tower_width // 2,
                        ground - tower_height - 45
                    ),
                    (
                        tower_x + tower_width + 5,
                        ground - tower_height
                    ),
                ]
            )

            # نافذة
            pygame.draw.rect(
                screen,
                (35, 35, 40),
                (
                    tower_x + tower_width // 3,
                    ground - tower_height + 30,
                    tower_width // 3,
                    35
                )
            )

        # البوابة
        gate_width = max(
            40,
            size // 4
        )

        gate_height = wall_height // 2

        pygame.draw.rect(
            screen,
            (50, 45, 45),
            (
                x - gate_width // 2,
                ground - gate_height,
                gate_width,
                gate_height
            )
        )

        # علم
        pygame.draw.line(
            screen,
            (55, 45, 40),
            (
                int(x),
                top - 5
            ),
            (
                int(x),
                top - 75
            ),
            4
        )

        flag_color = (
            (180, 35, 40)
            if castle_type % 2 == 0
            else (45, 55, 150)
        )

        pygame.draw.polygon(
            screen,
            flag_color,
            [
                (x, top - 70),
                (x + 45, top - 58),
                (x, top - 45),
            ]
        )

    # -----------------------------------------------------
    # المباني
    # -----------------------------------------------------

    def draw_building(
        self,
        screen,
        x,
        width,
        height,
        roof
    ):

        ground = self.ground_y

        left = int(
            x - width / 2
        )

        top = int(
            ground - height
        )

        wall = (150, 135, 115)

        if self.theme in (
            "ruined_city",
            "dead_city",
        ):
            wall = (90, 90, 85)

        pygame.draw.rect(
            screen,
            wall,
            (
                left,
                top,
                width,
                height
            )
        )

        if roof == 0:

            pygame.draw.polygon(
                screen,
                (90, 50, 45),
                [
                    (left - 10, top),
                    (
                        left + width // 2,
                        top - 45
                    ),
                    (
                        left + width + 10,
                        top
                    ),
                ]
            )

        elif roof == 1:

            pygame.draw.rect(
                screen,
                (70, 70, 75),
                (
                    left - 5,
                    top - 12,
                    width + 10,
                    15
                )
            )

        else:

            pygame.draw.polygon(
                screen,
                (110, 85, 50),
                [
                    (left - 5, top),
                    (
                        left + width // 2,
                        top - 30
                    ),
                    (
                        left + width + 5,
                        top
                    ),
                ]
            )

        # النوافذ
        window_w = max(
            10,
            width // 7
        )

        for wx in (
            left + width // 4,
            left + (width * 3) // 4
        ):

            pygame.draw.rect(
                screen,
                (45, 60, 70),
                (
                    int(wx - window_w // 2),
                    top + 30,
                    window_w,
                    30
                )
            )

    # -----------------------------------------------------
    # العقبات
    # -----------------------------------------------------

    def draw_obstacle(
        self,
        screen,
        x,
        width,
        height,
        obstacle_type
    ):

        ground = self.ground_y

        if self.theme in (
            "ice",
            "ice_mountain",
            "ice_palace",
            "snowstorm",
            "frozen_village",
            "ice_cave",
            "white_land",
            "polar_night",
        ):

            color = (150, 190, 210)

        elif self.theme in (
            "volcano",
            "fire_land",
            "hell",
            "hell_castle",
            "erupting_volcano",
            "lava_valley",
            "red_world",
        ):

            color = (75, 45, 40)

        else:

            color = (105, 100, 90)

        if obstacle_type == 0:

            points = [
                (
                    x - width // 2,
                    ground
                ),
                (
                    x - width // 3,
                    ground - height
                ),
                (
                    x + width // 5,
                    ground - height + 10
                ),
                (
                    x + width // 2,
                    ground
                ),
            ]

            pygame.draw.polygon(
                screen,
                color,
                points
            )

        elif obstacle_type == 1:

            barrel = (
                (125, 75, 35)
                if "desert" not in self.theme
                else (150, 95, 40)
            )

            pygame.draw.rect(
                screen,
                barrel,
                (
                    x - width // 2,
                    ground - height,
                    width,
                    height
                ),
                border_radius=8
            )

            pygame.draw.line(
                screen,
                (65, 45, 30),
                (
                    x - width // 2,
                    ground - height // 2
                ),
                (
                    x + width // 2,
                    ground - height // 2
                ),
                4
            )

        elif obstacle_type == 2:

            pygame.draw.rect(
                screen,
                color,
                (
                    x - width // 2,
                    ground - height,
                    width,
                    height
                )
            )

            pygame.draw.rect(
                screen,
                (60, 60, 60),
                (
                    x - width // 2,
                    ground - height,
                    width,
                    height
                ),
                3
            )

        else:

            # جذع ساقط
            pygame.draw.rect(
                screen,
                (95, 60, 30),
                (
                    x - width // 2,
                    ground - height // 2,
                    width,
                    max(15, height // 4)
                ),
                border_radius=8
            )

    # -----------------------------------------------------
    # تفاصيل خاصة
    # -----------------------------------------------------

    def draw_special_details(
        self,
        screen,
        camera_x
    ):

        width, height = screen.get_size()

        # المطر
        if self.theme in (
            "rain_city",
            "storm_sea",
            "snowstorm",
        ):

            rain_color = (
                (190, 210, 225)
                if self.theme != "snowstorm"
                else (240, 245, 250)
            )

            for i in range(100):

                x = (
                    i * 137
                    - int(camera_x * 0.4)
                ) % max(1, width)

                y = (
                    i * 83
                ) % max(
                    1,
                    self.ground_y
                )

                pygame.draw.line(
                    screen,
                    rain_color,
                    (x, y),
                    (x - 6, y + 22),
                    2
                )

        # ضباب (محفوظ مسبقاً في الذاكرة لتجنب إنشاء Surface كل إطار)
        if self.theme in (
            "fog_city",
            "fog_world",
            "ghost_world",
            "dark_valley",
        ):
            if self._fog_cache_surface is None or self._fog_cache_size != (width, height):
                self._fog_cache_surface = pygame.Surface((width, height), pygame.SRCALPHA)
                self._fog_cache_surface.fill((190, 195, 200, 35))
                self._fog_cache_size = (width, height)
            screen.blit(self._fog_cache_surface, (0, 0))

        # برق
        if self.theme == "storm_sea":

            if (
                pygame.time.get_ticks() // 700
            ) % 9 == 0:

                pygame.draw.line(
                    screen,
                    (240, 240, 255),
                    (width - 300, 80),
                    (width - 340, 180),
                    4
                )

                pygame.draw.line(
                    screen,
                    (240, 240, 255),
                    (width - 340, 180),
                    (width - 300, 260),
                    4
                )

        # نار صغيرة
        if self.theme in (
            "fire_land",
            "hell",
            "hell_castle",
            "burned_land",
            "lava_valley",
            "red_world",
        ):

            for i in range(12):

                x = (
                    i * 173
                    - int(camera_x * 0.3)
                ) % max(1, width)

                y = self.ground_y - 5

                pygame.draw.circle(
                    screen,
                    (235, 75, 25),
                    (x, y),
                    5
                )

                pygame.draw.circle(
                    screen,
                    (255, 180, 40),
                    (x, y - 6),
                    3
                )

        # حلقات كوكب
        if self.theme in (
            "space",
            "final_world",
        ):

            pygame.draw.ellipse(
                screen,
                (150, 120, 190),
                (
                    width - 350,
                    120,
                    280,
                    70
                ),
                6
            )

    # -----------------------------------------------------
    # الخلفية
    # -----------------------------------------------------

    def draw_background(self, screen, camera_x, camera_y):

        width, height = screen.get_size()
        sky, grass, ground = THEME_COLORS[self.theme]

        # رسم تدرج السماء مرة واحدة وحفظه في الكاش بدلاً من 720 عملية رسم كل إطار
        cache_key = (self.theme, width, height)
        if self._sky_cache_surface is None or self._sky_cache_key != cache_key:
            sky_surf = pygame.Surface((width, height))
            top = sky
            bottom = tuple(max(0, min(255, c + 20)) for c in sky)
            for y in range(height):
                ratio = y / max(1, height)
                color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
                pygame.draw.line(sky_surf, color, (0, y), (width, y))
            self._sky_cache_surface = sky_surf
            self._sky_cache_key = cache_key

        screen.blit(self._sky_cache_surface, (0, 0))

        # النجوم (الحفاظ على التوزيع الأصلي مع رسم الظاهر داخل الشاشة فقط)
        for star in self.stars:
            sx = int(star["x"])
            if 0 <= sx <= width:
                sy = int(star["y"] - (camera_y * 0.2))
                if -5 <= sy <= height + 5:
                    pygame.draw.circle(screen, (235, 235, 210), (sx, sy), star["size"])

        # الشمس
        if self.theme not in ("space", "final_world", "ghost_world", "graveyard"):
            pygame.draw.circle(screen, (255, 225, 125), (width - 170, 105), 48)

        # القمر
        if self.theme in ("night_city", "night_desert", "polar_night", "graveyard", "dead_city", "dark_forest", "haunted_castle", "ghost_world", "star_world", "space", "final_world"):
            pygame.draw.circle(screen, (225, 230, 215), (width - 180, 100), 38)
            pygame.draw.circle(screen, sky, (width - 165, 90), 38)

        # كواكب
        if self.theme in ("space", "alien_planet", "final_world"):
            pygame.draw.circle(screen, (100, 75, 150), (180, 150), 70)
            pygame.draw.circle(screen, (55, 130, 160), (width - 230, 230), 45)

        # الجبال (رسم الجبال الواقعة ضمن نطاق رؤية الكاميرا فقط)
        mtn_color = self._mountain_color()
        for mountain in self.mountains:
            mx = mountain["x"] - (camera_x * 0.1)
            mw = mountain["width"]
            if mx + mw // 2 < -80 or mx - mw // 2 > width + 80:
                continue
            mh = mountain["height"]
            points = [
                (mx - mw // 2, self.ground_y),
                (mx, self.ground_y - mh),
                (mx + mw // 2, self.ground_y),
            ]
            pygame.draw.polygon(screen, mtn_color, points)

        # السحب (رسم السحب الواقعة ضمن نطاق رؤية الكاميرا فقط)
        for cloud in self.clouds:
            cx = cloud["x"] - (camera_x * 0.05)
            csize = cloud["size"]
            if cx + csize < -80 or cx - csize > width + 80:
                continue
            cy = cloud["y"] - (camera_y * 0.5)
            if -csize <= cy <= height + csize:
                self._draw_cloud(screen, cx, cy, csize)


    # -----------------------------------------------------
    # الرسم الرئيسي
    # -----------------------------------------------------

    def draw(self, screen, camera_x, camera_y):
        width, _ = screen.get_size()

        # خدعة برمجية: نخصم الكاميرا من موقع الأرض مؤقتاً
        # لكي ترتسم الأشجار والمباني والجبال في مكانها الصحيح تلقائياً
        original_ground_y = self.ground_y
        self.ground_y = original_ground_y - camera_y

        # رسم العالم
        self.draw_background(screen, camera_x, camera_y)
        self.draw_ground(screen)

        # الأشجار
        for tree in self.trees:
            sx = int(tree["x"] - camera_x)
            if -200 < sx < width + 200:
                self.draw_tree(screen, sx, tree["size"], tree["type"])

        # المباني
        for building in self.buildings:
            sx = int(building["x"] - camera_x)
            if -250 < sx < width + 250:
                self.draw_building(screen, sx, building["width"], building["height"], building["roof"])

        # القصور
        for castle in self.castles:
            sx = int(castle["x"] - camera_x)
            if -400 < sx < width + 400:
                self.draw_castle(screen, sx, castle["size"], castle["type"])

        # العقبات
        for obstacle in self.obstacles:
            sx = int(obstacle["x"] - camera_x)
            if -150 < sx < width + 150:
                self.draw_obstacle(screen, sx, obstacle["width"], obstacle["height"], obstacle["type"])

        self.draw_special_details(screen, camera_x)

        # إعادة الأرض لقيمتها الأصلية حتى لا تختل اللعبة
        self.ground_y = original_ground_y


    def prune_behind(self, cutoff_x):
        """تخلص من تفاصيل العالم التي أصبحت خلف اللاعب نهائياً."""
        for name in ("trees", "castles", "obstacles", "buildings",
                     "mountains", "clouds", "stars", "particles"):
            items = getattr(self, name, None)
            if not isinstance(items, list):
                continue
            kept = []
            for item in items:
                x = item.get("x", cutoff_x) if isinstance(item, dict) else getattr(item, "x", cutoff_x)
                width = item.get("width", item.get("size", 0)) if isinstance(item, dict) else 0
                if x + width >= cutoff_x:
                    kept.append(item)
            setattr(self, name, kept)

    # -----------------------------------------------------
    # تغيير المرحلة
    # -----------------------------------------------------

    def set_stage(self, stage):

        self.stage = max(
            1,
            min(64, stage)
        )

        self.theme = STAGE_THEMES[
            self.stage - 1
        ]

        self.trees.clear()
        self.castles.clear()
        self.obstacles.clear()
        self.buildings.clear()
        self.mountains.clear()
        self.clouds.clear()
        self.stars.clear()

        self.rng = random.Random(
            self.stage * 918273
        )

        self.generate_stage()
