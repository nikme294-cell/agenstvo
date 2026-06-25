from ursina import *
import random
import math
import logging

logger = logging.getLogger()

class Core4(Entity):
    def __init__(self, position=Vec3(4, -3, 2)):
        super().__init__(model='sphere', color=color.magenta, position=position, scale=1.5, collider='sphere')
        self.name = "Core4"
        self.shield_points = []
        self.hit_history = []
        self.scout_hits = []
        self.metrics = {"score":0.0, "steps_survived":0, "core_hits":0, "shield_blocks":0, "eaten":0}
        self.AI_ACTIVATED = True          # всегда активен
        self.MAX_HISTORY = 20
        self.MAX_SHIELD_POINTS = 200      # в 2 раза больше
        self.SHIELD_SCALE_FACTOR = 0.5
        self.speed = 1.0                  # медленный
        self.target_position = None
        self.moving = False

        # Ядовитое ядро – параметры урона
        self.poison_damage = 0.025        # в 4 раза меньше щита (0.1 / 4)

        # Защитные щиты – ставит вокруг себя случайно, но не ищет врагов
        self.shield_timer = 0.0
        self.shield_interval = 0.5

        self.wireframe_entity = Entity(model='sphere', color=color.black, position=position, scale=self.scale*1.001)
        self.wireframe_entity.wireframe = True

    def update_wireframe(self):
        self.wireframe_entity.position = self.position
        self.wireframe_entity.scale = self.scale * 1.001
        self.wireframe_entity.rotation_y += 20 * time.dt

    def vector_sum(self, vecs):
        result = Vec3(0,0,0)
        for v in vecs:
            result += v
        return result

    def predict_shield_position(self):
        """Слепое размещение щитов – случайное направление вокруг себя."""
        theta, phi = random.uniform(0,2*math.pi), random.uniform(0,math.pi)
        dir_vec = Vec3(math.sin(phi)*math.cos(theta), math.sin(phi)*math.sin(theta), math.cos(phi)).normalized()
        dist = random.uniform(2.5, 4.0)
        return self.position + dir_vec * dist

    def update_ai(self, cores):
        self.metrics["steps_survived"] += 1

        # Ограничение радиуса 20
        if self.position.length() > 20:
            self.position = self.position.normalized() * 19

        # Создание щитов (по таймеру)
        self.shield_timer += time.dt
        if self.shield_timer >= self.shield_interval and len(self.shield_points) < self.MAX_SHIELD_POINTS:
            predicted = self.predict_shield_position()
            if predicted is not None:
                pt = Entity(model='sphere', color=color.magenta, position=predicted,
                            scale=self.scale * self.SHIELD_SCALE_FACTOR, collider='sphere')
                pt.owner = self
                self.shield_points.append(pt)
                self.metrics["score"] -= 0.1
            self.shield_timer = 0.0

        # Удаляем старые щиты (если превышен лимит)
        while len(self.shield_points) > self.MAX_SHIELD_POINTS:
            old = self.shield_points.pop(0)
            destroy(old)

        # Слепое движение – просто случайное блуждание (медленное)
        if random.random() < 0.01:
            self.target_position = self.position + Vec3(random.uniform(-5,5), random.uniform(-5,5), random.uniform(-5,5))
            self.moving = True
        if self.moving and self.target_position is not None:
            move = (self.target_position - self.position).normalized() * self.speed * time.dt
            if distance(self.position, self.target_position) > 0.5:
                self.position += move
            else:
                self.moving = False
                self.target_position = None

    def update_scouts(self, enemies, cores, all_shields):
        # Нет разведчиков – слепое ядро
        pass

    def destroy_core(self):
        for s in self.shield_points[:]: destroy(s)
        self.shield_points.clear()
        if hasattr(self, 'wireframe_entity'): destroy(self.wireframe_entity)
        destroy(self)