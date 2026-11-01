import pygame
import math
import time
import os

class SpriteSheetAnimator:
    def __init__(self, image_path, frame_count, speed=0.15):
        self.frames = []
        self.current_frame = 0
        self.speed = speed
        self.frame_count = frame_count
        self.finished = False # لمعرفة هل انتهت الحركة (مهم للموت والهجوم)
        
        try:
            self.sprite_sheet = pygame.image.load(image_path).convert_alpha()
            sheet_width = self.sprite_sheet.get_width()
            sheet_height = self.sprite_sheet.get_height()
            
            self.frame_width = sheet_width // frame_count
            self.frame_height = sheet_height
            
            for i in range(frame_count):
                rect = pygame.Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
                image = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
                image.blit(self.sprite_sheet, (0, 0), rect)
                self.frames.append(image)
        except FileNotFoundError:
            print(f"تنبيه: لم يتم العثور على صورة العدو: {image_path}")

    def update(self):
        if not self.frames: return
        self.current_frame += self.speed
        if self.current_frame >= len(self.frames):
            self.current_frame = 0
            self.finished = True
        else:
            self.finished = False

    def get_current_image(self, facing_right=True):
        if not self.frames: return None
        image = self.frames[int(self.current_frame)]
        if not facing_right:
            image = pygame.transform.flip(image, True, False)
        return image


class Enemy:
    def __init__(self, x, enemy_type, ground_y, stage=1):
        self.x = x
        self.y = ground_y - 90
        self.enemy_type = enemy_type
        
        self.width = 50
        self.height = 90

        self.vel_x = 0
        self.vel_y = 0
        self.gravity = 0.7
        self.on_ground = False

        self.facing = -1
        self.state = "idle"
        
        self.patrol_start_x = x
        self.patrol_range = 300

        # إعداد الطبقات: القوة والحجم بناءً على نوع العدو
        if self.enemy_type == "soldier":
            self.max_health = 50 + (stage * 10)
            self.speed = 2.5 + (stage * 0.1)
            self.damage = 10 + (stage * 2)
            self.attack_range = 60
            self.sight_range = 400
        elif self.enemy_type == "commander":
            self.max_health = 120 + (stage * 15)
            self.speed = 3.0 + (stage * 0.1)
            self.damage = 20 + (stage * 3)
            self.attack_range = 80
            self.sight_range = 500
        elif self.enemy_type == "guard":
            self.max_health = 200 + (stage * 20)
            self.speed = 2.0 + (stage * 0.1)
            self.damage = 30 + (stage * 4)
            self.attack_range = 90
            self.sight_range = 450
        elif self.enemy_type == "king":
            self.max_health = 500 + (stage * 50)
            self.speed = 3.5 + (stage * 0.1)
            self.damage = 45 + (stage * 5)
            self.attack_range = 130
            self.sight_range = 600
            
        self.health = self.max_health

        # تحميل حركات الهيكل العظمي مع تقطيعها الصحيح
        # تنبيه: إذا ظهر الهجوم بشكل مقطوع، افتح صورة Skeleton Attack وعدّ الهياكل فيها واكتب الرقم بدلاً من 18
        # تحميل حركات الهيكل العظمي بناءً على الأرقام الدقيقة التي قمت بعدها!
        self.animations = {
            #"idle": SpriteSheetAnimator("assets/Skeleton Idle.png", frame_count=11, speed=0.15),
            "walk": SpriteSheetAnimator("assets/Skeleton Walk.png", frame_count=13, speed=0.2),
            "attack": SpriteSheetAnimator("assets/Skeleton Attack.png", frame_count=18, speed=0.25),
            "hit": SpriteSheetAnimator("assets/Skeleton Hit.png", frame_count=8, speed=0.3),
            "dead": SpriteSheetAnimator("assets/Skeleton Dead.png", frame_count=15, speed=0.15)
            
            # يمكنك إضافة حركة React مستقبلاً إذا أردت استخدامها لرد فعل العدو عند رؤيتك
            # "react": SpriteSheetAnimator("assets/Skeleton React.png", frame_count=4, speed=0.2)
        }

    def is_alive(self):
        return self.health > 0

    def take_damage(self, amount, hit_dir, is_heavy=False):
        if not self.is_alive(): return
        
        self.health -= amount
        
        if self.health <= 0:
            self.health = 0
            self.state = "dead"
            if "dead" in self.animations:
                self.animations["dead"].current_frame = 0
        else:
            # تشغيل حركة تلقي الضربة عند الإصابة
            self.state = "hit"
            if "hit" in self.animations:
                self.animations["hit"].current_frame = 0
                
            if is_heavy:
                self.vel_y = -8
                self.vel_x = hit_dir * 10
            else:
                self.vel_y = -4
                self.vel_x = hit_dir * 5

    

    def update(self, player_x, player_y, stage_layout):
        # الجاذبية للميت حتى يسقط
        if not self.is_alive():
            self.vel_y += self.gravity
            self.y += self.vel_y
            self.ground_y = stage_layout.get_ground_y(self.x, self.width, self.height, self.y)
            if self.y >= self.ground_y - self.height:
                self.y = self.ground_y - self.height
                self.vel_y = 0
            return

        # نظام "الاستراحة" للهجوم لمنع الاهتزاز السريع
        if not hasattr(self, 'attack_cooldown'):
            self.attack_cooldown = 0
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        move_x = 0
        dist_x = player_x - self.x
        dist_y = player_y - self.y
        dist_to_player = math.hypot(dist_x, dist_y)

        # الانتظار حتى تنتهي حركة تلقي الضربة
        if self.state == "hit":
            if "hit" in self.animations and self.animations["hit"].finished:
                self.state = "idle"
                
        # الانتظار حتى تنتهي حركة الهجوم
        # الانتظار حتى تنتهي حركة الهجوم
        elif self.state == "attack":
            if "attack" in self.animations and self.animations["attack"].finished:
                self.state = "walk" 
                self.attack_cooldown = 40  
        else:
            # التحقق من مكان اللاعب
            player_is_reachable = abs(dist_y) < 160  # هل اللاعب على الأرض وليس فوق جبل؟
            
            # 1. الحالة الأولى: اللاعب في النطاق ويمكن الوصول إليه (هجوم ومطاردة)
            if dist_to_player <= self.sight_range and player_is_reachable:
                if dist_to_player <= self.attack_range:
                    if self.attack_cooldown <= 0:
                        self.state = "attack"
                        if "attack" in self.animations:
                            self.animations["attack"].current_frame = 0
                            self.animations["attack"].finished = False 
                        self.facing = 1 if dist_x > 0 else -1
                    else:
                        self.state = "walk"
                        move_x = 0
                        self.facing = 1 if dist_x > 0 else -1
                else:
                    self.state = "walk"
                    self.facing = 1 if player_x > self.x else -1
                    move_x = (self.speed * 1.3) * self.facing
                    
            # 2. الحالة الثانية (مباشرة): اللاعب ابتعد أو قفز فوق الجبل (يعود للفخ فوراً)
            else:
                self.state = "idle"
                move_x = 0  # يتجمد فوراً ويتحول لشجرة أو صخرة
                
        # الفيزياء والاصطدام
        self.x += move_x
        self.x += self.vel_x
        if self.on_ground: self.vel_x *= 0.8
        else: self.vel_x *= 0.98

        self.x, hit_wall = stage_layout.get_valid_x(self.x, self.y, self.width, self.height, (move_x + self.vel_x))

        # --- الحل العبقري للقفز والتعليق ---
        if hit_wall and self.state not in ["dead", "hit", "attack"]:
            if self.on_ground:
                self.vel_y = -6  # طيران خفيف/قفزة صغيرة للتحرر أو تجاوز الحجارة
            else:
                # إذا قام بالقفزة الصغيرة وما زال مصطدماً بالجدار (جبل عالي)، يعود للخلف!
                self.facing *= -1
                self.x += self.facing * 5

        self.vel_y += self.gravity
        self.y += self.vel_y

        self.ground_y = stage_layout.get_ground_y(self.x, self.width, self.height, self.y)
        target_y = self.ground_y - self.height

        if self.vel_y >= 0 and self.y >= target_y - 25:
            self.y = target_y
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False
    def draw(self, surface, camera_x, camera_y, screen_width):
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        
        if sx < -300 or sx > screen_width + 300: return

        current_anim = self.state
        if current_anim in ["patrol", "return", "chase"]: 
            current_anim = "walk"
            
        if current_anim not in self.animations or not self.animations[current_anim].frames:
            current_anim = "idle"
            
        animator = self.animations.get(current_anim)
        
        if animator and animator.frames:
            # إيقاف التحديث عند آخر لقطة للموت، وتجميد الأنيميشن أثناء النهاية
            if current_anim == "dead" and animator.current_frame >= len(animator.frames) - 1:
                pass
            elif current_anim in ["hit", "attack"] and animator.finished:
                pass
            else:
                animator.update()
                
            img = animator.get_current_image(facing_right=(self.facing == 1))
            
            # تحديد الأحجام للطبقات!
            target_height = 120 # الجندي
            if self.enemy_type == "commander": target_height = 150
            elif self.enemy_type == "guard": target_height = 180
            elif self.enemy_type == "king": target_height = 240 # الملك العملاق
                
            ratio = target_height / img.get_height()
            target_width = int(img.get_width() * ratio)
            img = pygame.transform.scale(img, (target_width, target_height))
            
            img_rect = img.get_rect(midbottom=(sx + self.width // 2, sy + self.height))
            
            # --- رسم الرداء الأسود للملك خلفه ---
            if self.enemy_type == "king" and self.is_alive():
                cape_x = img_rect.centerx - (20 * self.facing)
                cape_y = img_rect.top + 50
                cape_points = [
                    (cape_x, cape_y), 
                    (cape_x - (60 * self.facing), cape_y + 140), 
                    (cape_x - (40 * self.facing), cape_y + 180),
                    (cape_x + (10 * self.facing), cape_y + 180)
                ]
                pygame.draw.polygon(surface, (20, 20, 20), cape_points)
                
            # رسم صورة الهيكل العظمي
            surface.blit(img, img_rect)
            
            # --- رسم التاج الذهبي للملك فوق رأسه ---
            if self.enemy_type == "king" and self.is_alive():
                crown_x = img_rect.centerx + (5 * self.facing)
                crown_y = img_rect.top + 35
                crown_points = [
                    (crown_x - 15, crown_y), (crown_x - 20, crown_y - 25),
                    (crown_x - 5, crown_y - 10), (crown_x, crown_y - 30),
                    (crown_x + 5, crown_y - 10), (crown_x + 20, crown_y - 25),
                    (crown_x + 15, crown_y)
                ]
                pygame.draw.polygon(surface, (255, 215, 0), crown_points)
            
            # --- شريط الدم الدائم والجميل ---
            if self.is_alive():
                bar_width = target_width - 20
                bar_x = img_rect.centerx - (bar_width // 2)
                bar_y = img_rect.top - 15
                
                health_ratio = self.health / self.max_health
                pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, 6))
                pygame.draw.rect(surface, (210, 50, 50), (bar_x, bar_y, bar_width * health_ratio, 6))
        else:
            # ==========================================
            # نظام الأفخاخ العبقري (التخفي)
            # ==========================================
            # اختيار شكل التخفي بناءً على مكان العدو ليكون ثابتاً لكل عدو
            disguise = int(self.patrol_start_x) % 4 
            
            if disguise == 0:
                # 1. صخرة كبيرة
                pygame.draw.ellipse(surface, (100, 100, 100), (sx - 10, sy + self.height - 40, self.width + 20, 40))
                pygame.draw.ellipse(surface, (80, 80, 80), (sx + 5, sy + self.height - 50, self.width - 10, 30))
                pygame.draw.ellipse(surface, (120, 120, 120), (sx - 5, sy + self.height - 35, 20, 15))
                
            elif disguise == 1:
                # 2. شجرة
                trunk_w = 20
                # الجذع
                pygame.draw.rect(surface, (101, 67, 33), (sx + self.width//2 - trunk_w//2, sy + 20, trunk_w, self.height - 20))
                # الأوراق (دوائر متداخلة)
                pygame.draw.circle(surface, (34, 139, 34), (sx + self.width//2, sy + 20), 35)
                pygame.draw.circle(surface, (30, 120, 30), (sx + self.width//2 - 20, sy + 35), 25)
                pygame.draw.circle(surface, (40, 150, 40), (sx + self.width//2 + 20, sy + 35), 25)
                
            elif disguise == 2:
                # 3. منزل مهجور
                house_w = self.width + 30
                house_x = sx - 15
                # الجدار
                pygame.draw.rect(surface, (180, 160, 120), (house_x, sy + 40, house_w, self.height - 40))
                # السقف (مثلث أحمر)
                pygame.draw.polygon(surface, (150, 50, 50), [(house_x - 10, sy + 40), (house_x + house_w//2, sy), (house_x + house_w + 10, sy + 40)])
                # الباب المظلم
                pygame.draw.rect(surface, (30, 20, 10), (house_x + house_w//2 - 10, sy + self.height - 30, 20, 30))
                
            else:
                # 4. برج مراقبة خشبي
                # الأعمدة
                pygame.draw.rect(surface, (110, 70, 40), (sx, sy + 20, 8, self.height - 20))
                pygame.draw.rect(surface, (110, 70, 40), (sx + self.width - 8, sy + 20, 8, self.height - 20))
                # تقاطعات الخشب X
                pygame.draw.line(surface, (100, 60, 30), (sx, sy + 20), (sx + self.width, sy + self.height), 4)
                pygame.draw.line(surface, (100, 60, 30), (sx + self.width, sy + 20), (sx, sy + self.height), 4)
                # المنصة العلوية
                pygame.draw.rect(surface, (80, 50, 20), (sx - 10, sy + 10, self.width + 20, 20))