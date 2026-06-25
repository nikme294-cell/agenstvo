from ursina import *
import random
import math
import logging

logger = logging.getLogger()

class Core1(Entity):
    def __init__(self, position=Vec3(0,0,0)):
        super().__init__(model='sphere', color=color.red, position=position, scale=1.0, collider='sphere')
        self.name = "Core1"
        self.shield_points = []
        self.hit_history = []
        self.scout_hits = []
        self.metrics = {"score":0.0, "steps_survived":0, "core_hits":0, "shield_blocks":0, "eaten":0}
        self.AI_ACTIVATED = False
        self.MAX_HISTORY = 20
        self.MAX_SHIELD_POINTS = 100
        self.SHIELD_SCALE_FACTOR = 0.5
        self.speed = 2.0
        self.target_position = None
        self.moving = False

        self.scout_active = True
        self.veer_size = 16
        self.veer_interval = 1.5
        self.scout_timer = 0.0
        self.scout_speed = 12.0
        self.scout_lifetime = 5.0
        self.scout_sense_radius = 3.0
        self.veer_angle_offset = 0.0
        self.veer_precession_speed = 0.2
        self.scouts = []

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
        if not self.hit_history:
            theta, phi = random.uniform(0,2*math.pi), random.uniform(0,math.pi)
            dir_vec = Vec3(math.sin(phi)*math.cos(theta), math.sin(phi)*math.sin(theta), math.cos(phi)).normalized()
        else:
            recent = self.hit_history[-self.MAX_HISTORY:]
            avg = self.vector_sum(recent) / len(recent)
            dir_vec = (avg - self.position).normalized()
            if dir_vec.length() < 0.001:
                dir_vec = Vec3(random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)).normalized()
        dist = random.uniform(2.5, 4.0)
        return self.position + dir_vec * dist

    def teleport_to_avg(self):
        if len(self.scout_hits) >= 2:
            recent = self.scout_hits[-10:]
            avg = self.vector_sum(recent) / len(recent)
            if distance(avg, self.position) > 10.0:
                self.position = avg
                logger.info(f"{self.name} телепортировался в {avg}")
                self.scout_hits.clear()
                return True
            else:
                self.target_position = avg
                self.moving = True
        return False

    def emergency_teleport(self):
        if self.scale_x < 0.4 and len(self.scout_hits) > 5:
            center = self.vector_sum(self.scout_hits) / len(self.scout_hits)
            safe = self.position + (self.position - center).normalized() * 8.0
            self.position = safe
            logger.info(f"{self.name} экстренно телепортировался в {safe}")
            self.scout_hits.clear()
            return True
        return False

    def update_ai(self, cores):
        if not self.AI_ACTIVATED: return
        self.metrics["steps_survived"] += 1

        if self.emergency_teleport():
            pass
        elif not self.teleport_to_avg():
            if self.moving and self.target_position is not None:
                move = (self.target_position - self.position).normalized() * self.speed * time.dt
                if distance(self.position, self.target_position) > 0.5:
                    self.position += move
                else:
                    self.moving = False
                    self.target_position = None

        if self.position.length() > 20:
            self.position = self.position.normalized() * 19

        predicted = self.predict_shield_position()
        if predicted is not None:
            if len(self.shield_points) >= self.MAX_SHIELD_POINTS:
                old = self.shield_points.pop(0)
                destroy(old)
            pt = Entity(model='sphere', color=color.azure, position=predicted,
                        scale=self.scale * self.SHIELD_SCALE_FACTOR, collider='sphere')
            pt.owner = self
            self.shield_points.append(pt)
            self.metrics["score"] -= 0.1

    def launch_veer(self):
        self.veer_angle_offset += self.veer_precession_speed * time.dt
        for d in self.generate_veer_directions(self.veer_size):
            scout = Entity(model='sphere', color=color.yellow, position=self.position + d*1.5,
                           scale=0.3, collider='sphere')
            scout.velocity = d * self.scout_speed
            scout.lifetime = self.scout_lifetime
            scout.owner = self
            scout.sense_radius = self.scout_sense_radius
            self.scouts.append(scout)

    def generate_veer_directions(self, count):
        dirs = []
        golden = (1 + math.sqrt(5)) / 2
        for i in range(count):
            theta = 2 * math.pi * i / golden + self.veer_angle_offset
            phi = math.acos(1 - 2 * (i + 0.5) / count)
            dirs.append(Vec3(math.sin(phi)*math.cos(theta), math.sin(phi)*math.sin(theta), math.cos(phi)).normalized())
        return dirs

    def update_scouts(self, enemies, cores, all_shields):
        if not self.scout_active: return
        self.scout_timer += time.dt
        if self.scout_timer >= self.veer_interval:
            self.launch_veer()
            self.scout_timer = 0.0

        for scout in self.scouts[:]:
            try:
                scout.position += scout.velocity * time.dt
                scout.lifetime -= time.dt
            except: continue

            for shield in all_shields:
                try:
                    if shield.owner is self: continue
                    dist = distance(scout, shield)
                    if dist < scout.sense_radius:
                        self.scout_hits.append(shield.position)
                        if len(self.scout_hits) > 20: self.scout_hits.pop(0)
                        if not self.AI_ACTIVATED:
                            self.AI_ACTIVATED = True
                            logger.info(f"{self.name} активирован (щит) в {shield.position}")
                        if dist < (scout.scale_x/2 + shield.scale_x/2) * 0.9:
                            if shield in shield.owner.shield_points:
                                shield.owner.shield_points.remove(shield)
                            destroy(shield)
                            self.scouts.remove(scout); destroy(scout)
                            break
                except: continue

            if scout in self.scouts:
                for core in cores:
                    try:
                        if core is self: continue
                        dist = distance(scout, core)
                        if dist < scout.sense_radius:
                            self.scout_hits.append(core.position)
                            if len(self.scout_hits) > 20: self.scout_hits.pop(0)
                            if not self.AI_ACTIVATED:
                                self.AI_ACTIVATED = True
                                logger.info(f"{self.name} активирован (ядро) в {core.position}")
                            self.scouts.remove(scout); destroy(scout)
                            break
                    except: continue

            if scout in self.scouts and scout.lifetime <= 0:
                self.scouts.remove(scout); destroy(scout)

    def destroy_core(self):
        for s in self.shield_points[:]: destroy(s)
        self.shield_points.clear()
        for s in self.scouts[:]: destroy(s)
        self.scouts.clear()
        if hasattr(self, 'wireframe_entity'): destroy(self.wireframe_entity)
        destroy(self)