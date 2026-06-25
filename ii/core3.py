from ursina import *
import random
import math
import logging

logger = logging.getLogger()

class Core3(Entity):
    def __init__(self, position=Vec3(-5, 0, 5)):
        super().__init__(model='sphere', color=color.green, position=position, scale=1.0, collider='sphere')
        self.name = "Core3"
        self.shield_points = []
        self.hit_history = []
        self.scout_hits = []
        self.metrics = {"score":0.0, "steps_survived":0, "core_hits":0, "shield_blocks":0, "eaten":0}
        self.AI_ACTIVATED = True
        self.speed = 5.0
        self.target_position = None
        self.moving = False

        self.intervention_distance = 6.0
        self.push_strength = 1.0

        self.wireframe_entity = Entity(model='sphere', color=color.black, position=position, scale=self.scale*1.001)
        self.wireframe_entity.wireframe = True

    def update_wireframe(self):
        self.wireframe_entity.position = self.position
        self.wireframe_entity.scale = self.scale * 1.001
        self.wireframe_entity.rotation_y += 20 * time.dt

    def update_ai(self, cores):
        if self.position.length() > 20:
            self.position = self.position.normalized() * 19

        self.metrics["steps_survived"] += 1

        other_cores = [c for c in cores if c is not self]
        if len(other_cores) < 2:
            return

        # Проверяем расстояния между другими ядрами
        for i in range(len(other_cores)):
            for j in range(i+1, len(other_cores)):
                a = other_cores[i]
                b = other_cores[j]
                dist = distance(a.position, b.position)
                if dist < self.intervention_distance:
                    mid = (a.position + b.position) / 2
                    self.position = mid + Vec3(random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)).normalized() * 0.5
                    dir_ab = (b.position - a.position).normalized()
                    a.position += dir_ab * self.push_strength * 0.5
                    b.position -= dir_ab * self.push_strength * 0.5
                    logger.info(f"{self.name} разнял {a.name} и {b.name} в {mid}")
                    return

        center = Vec3(0,0,0)
        for c in other_cores:
            center += c.position
        center /= len(other_cores)
        if distance(self.position, center) > 2.0:
            self.target_position = center
            self.moving = True
        else:
            self.moving = False

        if self.moving and self.target_position is not None:
            move = (self.target_position - self.position).normalized() * self.speed * time.dt
            if distance(self.position, self.target_position) > 0.5:
                self.position += move
            else:
                self.moving = False
                self.target_position = None

    def update_scouts(self, enemies, cores, all_shields):
        pass

    def destroy_core(self):
        if hasattr(self, 'wireframe_entity'):
            destroy(self.wireframe_entity)
        destroy(self)