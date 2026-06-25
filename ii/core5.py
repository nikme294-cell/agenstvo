from ursina import *
import random
import math
import logging

logger = logging.getLogger()

class Core5(Entity):
    def __init__(self, position=Vec3(-6, 3, -4)):
        super().__init__(model='sphere', color=color.white, position=position, scale=1.2, collider='sphere')
        self.name = "Core5"
        self.shield_points = []
        self.hit_history = []
        self.scout_hits = []
        self.metrics = {"score":0.0, "steps_survived":0, "core_hits":0, "shield_blocks":0, "eaten":0}
        self.AI_ACTIVATED = True
        self.MAX_HISTORY = 20
        self.MAX_SHIELD_POINTS = 100
        self.SHIELD_SCALE_FACTOR = 0.5
        self.speed = 1.5

        # ---- Движение ----
        self.moving = False
        self.target_position = None

        # ---- Обманки ----
        self.decoys = []
        self.decoy_cost = 0.4
        self.decoy_interval = 2.0
        self.decoy_timer = 0.0
        self.decoy_lifetime = 5.0

        # ---- Лечение ----
        self.heal_amount = 0.05

        self.wireframe_entity = Entity(model='sphere', color=color.black, position=position, scale=self.scale*1.001)
        self.wireframe_entity.wireframe = True

    def update_wireframe(self):
        self.wireframe_entity.position = self.position
        self.wireframe_entity.scale = self.scale * 1.001
        self.wireframe_entity.rotation_y += 20 * time.dt

    def create_decoy(self):
        theta, phi = random.uniform(0,2*math.pi), random.uniform(0,math.pi)
        r = random.uniform(3.0, 6.0)
        pos = self.position + Vec3(r*math.sin(phi)*math.cos(theta), r*math.sin(phi)*math.sin(theta), r*math.cos(phi))
        decoy = Entity(model='sphere', color=color.gray, position=pos, scale=0.8, collider='sphere')
        decoy.lifetime = self.decoy_lifetime
        decoy.is_decoy = True
        decoy.owner = self
        self.decoys.append(decoy)
        self.metrics["score"] -= self.decoy_cost
        logger.info(f"{self.name} создал обманку в {pos}")

    def update_ai(self, cores):
        self.metrics["steps_survived"] += 1

        if self.position.length() > 20:
            self.position = self.position.normalized() * 19

        # Создание обманок
        self.decoy_timer += time.dt
        if self.decoy_timer >= self.decoy_interval:
            self.create_decoy()
            self.decoy_timer = 0.0

        # Удаление старых обманок
        for decoy in self.decoys[:]:
            decoy.lifetime -= time.dt
            if decoy.lifetime <= 0:
                self.decoys.remove(decoy)
                destroy(decoy)

        # Слепое блуждание
        if random.random() < 0.005:
            self.target_position = self.position + Vec3(random.uniform(-4,4), random.uniform(-4,4), random.uniform(-4,4))
            self.moving = True

        if self.moving and self.target_position is not None:
            move = (self.target_position - self.position).normalized() * self.speed * time.dt
            if distance(self.position, self.target_position) > 0.5:
                self.position += move
            else:
                self.moving = False
                self.target_position = None

    def heal(self, amount):
        self.scale += Vec3(amount, amount, amount)
        if self.scale_x > 2.0:
            self.scale = Vec3(2.0, 2.0, 2.0)
        logger.info(f"{self.name} полечился на {amount}, новый размер: {self.scale_x:.2f}")

    def update_scouts(self, enemies, cores, all_shields):
        pass

    def destroy_core(self):
        for d in self.decoys[:]: destroy(d)
        self.decoys.clear()
        if hasattr(self, 'wireframe_entity'): destroy(self.wireframe_entity)
        destroy(self)