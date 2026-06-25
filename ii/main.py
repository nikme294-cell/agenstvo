from ursina import *
import random
import math
import time as _time
import logging
import sys
from core1 import Core1
from core2 import Core2
from core3 import Core3
from core4 import Core4
from core5 import Core5

logging.basicConfig(filename='game_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger()
app = Ursina()

core1 = Core1(position=Vec3(0,0,0))
core2 = Core2(position=Vec3(8,2,6))
core3 = Core3(position=Vec3(-5,0,5))
core4 = Core4(position=Vec3(4,-3,2))
core5 = Core5(position=Vec3(-6,3,-4))
cores = [core1, core2, core3, core4, core5]

pivot = Entity()
camera.parent = pivot
camera.position = (0,0,-35)

def update_camera_target():
    if not cores: return
    center = Vec3(0,0,0)
    for c in cores:
        center += c.position
    center /= len(cores)
    pivot.position = center
    camera.look_at(center)

update_camera_target()

def check_shield_damage_and_poison():
    if len(cores) < 2: return
    all_shields = [s for c in cores for s in c.shield_points if s is not None]

    # Урон от щитов (Core3 не наносит урон)
    for core in cores[:]:
        for shield in all_shields[:]:
            try:
                if shield is None or core is None: continue
                if shield.owner is core: continue
                if shield.owner.name == "Core3":
                    continue
                dist = distance(core, shield)
                if dist < (core.scale_x/2 + shield.scale_x/2) * 0.9:
                    # Наносим урон
                    core.scale -= Vec3(0.1,0.1,0.1)
                    core.metrics["score"] -= 10.0
                    # Лечим Core5 (если он существует и не умер)
                    for c in cores:
                        if c.name == "Core5" and c.scale_x > 0.2:
                            c.heal(0.05)
                    if shield in shield.owner.shield_points:
                        shield.owner.shield_points.remove(shield)
                    destroy(shield)
                    logger.info(f"{core.name} получил урон от щита {shield.owner.name}! Новый размер: {core.scale_x:.2f}")
                    break
            except: continue

    # Ядовитый урон от касания ядер (Core4)
    for i in range(len(cores)):
        for j in range(i+1, len(cores)):
            a = cores[i]
            b = cores[j]
            try:
                if not hasattr(a, 'position') or not hasattr(b, 'position'): continue
                dist = distance(a.position, b.position)
                if dist < (a.scale_x/2 + b.scale_x/2) * 0.9:
                    if a.name == "Core4":
                        b.scale -= Vec3(0.025, 0.025, 0.025)
                        b.metrics["score"] -= 2.5
                        # Лечим Core5
                        for c in cores:
                            if c.name == "Core5" and c.scale_x > 0.2:
                                c.heal(0.05)
                        logger.info(f"{b.name} отравлен ядром Core4! Новый размер: {b.scale_x:.2f}")
                    elif b.name == "Core4":
                        a.scale -= Vec3(0.025, 0.025, 0.025)
                        a.metrics["score"] -= 2.5
                        for c in cores:
                            if c.name == "Core5" and c.scale_x > 0.2:
                                c.heal(0.05)
                        logger.info(f"{a.name} отравлен ядром Core4! Новый размер: {a.scale_x:.2f}")
            except: continue

paused = False
def update():
    global paused
    if held_keys['f']:
        paused = not paused
        _time.sleep(0.2)
    if paused: return

    for core in cores:
        core.update_wireframe()
        core.update_ai(cores)

    all_shields = [s for c in cores for s in c.shield_points if s is not None]
    core1.update_scouts([], cores, all_shields)
    core2.update_scouts([], cores, all_shields)
    # Core3, Core4, Core5 не имеют разведчиков

    check_shield_damage_and_poison()

    for core in cores:
        if core.AI_ACTIVATED and core.metrics["steps_survived"] % 100 == 0:
            print(f"{core.name} | {core.metrics['steps_survived']} | {core.scale_x:.2f} | {core.metrics['score']:.1f} | {len(core.shield_points)} | {core.metrics.get('eaten',0)}")

    # Завершение только когда все ядра погибли
    alive = [c for c in cores if c.scale_x > 0.2]
    if not alive:
        print("=== ЭПОХА ЗАВЕРШЕНА (все ядра погибли) ===")
        for c in cores:
            print(f"{c.name} метрики:", c.metrics)
        application.quit()
        sys.exit(0)

def update_camera_manual():
    if held_keys['left arrow']: pivot.rotation_y -= 100 * time.dt
    if held_keys['right arrow']: pivot.rotation_y += 100 * time.dt
    if held_keys['up arrow']: pivot.rotation_x -= 100 * time.dt
    if held_keys['down arrow']: pivot.rotation_x -= 100 * time.dt
    if held_keys['shift']:
        if held_keys['left arrow']: pivot.position += camera.left * 10 * time.dt
        if held_keys['right arrow']: pivot.position += camera.right * 10 * time.dt
        if held_keys['up arrow']: pivot.position += camera.up * 10 * time.dt
        if held_keys['down arrow']: pivot.position += camera.down * 10 * time.dt
    if held_keys['='] or held_keys['+']: camera.z += 5 * time.dt
    if held_keys['-']: camera.z -= 5 * time.dt
    camera.z = clamp(camera.z, -50, -5)

orig = update
def new_update():
    update_camera_manual()
    orig()
update = new_update

app.run()