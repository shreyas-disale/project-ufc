from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.interval.LerpInterval import LerpScaleInterval, LerpColorScaleInterval
from direct.interval.IntervalGlobal import Sequence, Func
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletBoxShape, BulletPlaneShape
import sys
import random
import os
from panda3d.core import CardMaker, NodePath

class UFCGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Set up the camera
        self.camera.setPos(0, -20, 10)
        self.camera.lookAt(0, 0, 0)
        
        # Physics world setup
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))  # Gravity
        
        # Ground (physics-enabled plane)
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(0, 0, -8)
        self.world.attachRigidBody(node)
        
        # Load fighters (using Ralph as placeholder; replace with UFC models)
        self.fighter1 = self._make_fighter("models/ralph", {"run": "models/ralph-run", "walk": "models/ralph-walk"}, pos=Vec3(-5,0,0), h=0, color=(1,0.4,0.4,1))
        self.fighter1.setScale(0.5)
        # Add physics body to fighter1
        shape1 = BulletBoxShape(Vec3(0.5, 0.5, 1))  # Approximate box for fighter
        node1 = BulletRigidBodyNode('Fighter1')
        node1.setMass(70)  # Weight in kg
        node1.addShape(shape1)
        np1 = self.fighter1.attachNewNode(node1)
        np1.setPos(0, 0, 0)
        self.world.attachRigidBody(node1)
        self.fighter1_body = node1
        
        self.fighter2 = self._make_fighter("models/ralph", {"run": "models/ralph-run", "walk": "models/ralph-walk"}, pos=Vec3(5,0,0), h=180, color=(0.4,0.6,1,1))
        self.fighter2.setScale(0.5)
        # Add physics body to fighter2
        shape2 = BulletBoxShape(Vec3(0.5, 0.5, 1))
        node2 = BulletRigidBodyNode('Fighter2')
        node2.setMass(70)
        node2.addShape(shape2)
        np2 = self.fighter2.attachNewNode(node2)
        np2.setPos(0, 0, 0)
        self.world.attachRigidBody(node2)
        self.fighter2_body = node2
        
        # Health and timer
        self.health1 = 100
        self.health2 = 100
        self.timer = 180  # 3 minutes in seconds
        self.game_over = False
        # Stamina system
        self.max_stamina = 100
        self.stamina1 = self.max_stamina
        self.stamina2 = self.max_stamina
        self.stamina_recovery = 8  # per second
        self.stamina_cost_punch = 20
        # Blocking/combo systems
        self.block1 = False
        self.block2 = False
        self.block_stamina_cost = 8
        self.block_damage_reduction = 0.7  # fraction reduced
        # Combos
        self.combo_window = 0.8
        self.last_punch_time1 = 0.0
        self.last_punch_time2 = 0.0
        self.combo_count1 = 0
        self.combo_count2 = 0
        # AI
        self.ai_enabled = True
        self.ai_last_action = 0.0
        self.ai_action_cooldown = 1.0
        # Camera shake / hit feedback
        self.camera_shake_timer = 0.0
        self.camera_shake_duration = 0.25
        self.camera_shake_magnitude = 0.4
        self.orig_cam_pos = self.camera.getPos()
        self.hit_text_timer = 0.0
        # Sound effects (place hit.wav into assets/ to enable)
        sfx_path = os.path.join(os.path.dirname(__file__), 'assets', 'hit.wav')
        if os.path.exists(sfx_path):
            try:
                self.hit_sfx = loader.loadSfx(sfx_path)
            except Exception:
                self.hit_sfx = None
        else:
            self.hit_sfx = None
        # load additional sfx (optional)
        punch_path = os.path.join(os.path.dirname(__file__), 'assets', 'punch.wav')
        ko_path = os.path.join(os.path.dirname(__file__), 'assets', 'ko.wav')
        try:
            self.punch_sfx = loader.loadSfx(punch_path) if os.path.exists(punch_path) else None
        except Exception:
            self.punch_sfx = None
        try:
            self.ko_sfx = loader.loadSfx(ko_path) if os.path.exists(ko_path) else None
        except Exception:
            self.ko_sfx = None
        
        # UI Elements
        self.health_text1 = OnscreenText(text=f"Player 1 Health: {self.health1}", pos=(-1.3, 0.9), scale=0.07, fg=(1, 1, 1, 1))
        self.health_text2 = OnscreenText(text=f"Player 2 Health: {self.health2}", pos=(0.7, 0.9), scale=0.07, fg=(1, 1, 1, 1))
        self.timer_text = OnscreenText(text=f"Time: {self.timer // 60}:{self.timer % 60:02d}", pos=(0, 0.9), scale=0.07, fg=(1, 1, 1, 1))
        self.instructions = OnscreenText(text="WASD: Move P1 | Arrows: Move P2 | Space/Enter: Punch | R: Restart", pos=(0, -0.9), scale=0.05, fg=(1, 1, 1, 1))
        self.game_over_text = OnscreenText(text="", pos=(0, 0), scale=0.1, fg=(1, 0, 0, 1))
        # Stamina UI and AI status
        self.stamina_text1 = OnscreenText(text=f"Stamina: {self.stamina1}", pos=(-1.3, 0.82), scale=0.05, fg=(0.6, 0.9, 0.6, 1))
        self.stamina_text2 = OnscreenText(text=f"Stamina: {self.stamina2}", pos=(0.7, 0.82), scale=0.05, fg=(0.6, 0.9, 0.6, 1))
        self.ai_status_text = OnscreenText(text=f"AI: {'On' if self.ai_enabled else 'Off'} (press T)", pos=(0, 0.82), scale=0.05, fg=(1, 1, 0.6, 1))
        self.hit_text = OnscreenText(text="", pos=(0, 0.6), scale=0.12, fg=(1, 0.2, 0.2, 1))
        
        # Controls
        self.accept('w', self.moveFighter, [self.fighter1, self.fighter1_body, 0, 1, 0])
        self.accept('s', self.moveFighter, [self.fighter1, self.fighter1_body, 0, -1, 0])
        self.accept('a', self.moveFighter, [self.fighter1, self.fighter1_body, -1, 0, 0])
        self.accept('d', self.moveFighter, [self.fighter1, self.fighter1_body, 1, 0, 0])
        self.accept('space', self.punch, [self.fighter1_body, self.fighter2_body, 1])
        
        self.accept('arrow_up', self.moveFighter, [self.fighter2, self.fighter2_body, 0, 1, 0])
        self.accept('arrow_down', self.moveFighter, [self.fighter2, self.fighter2_body, 0, -1, 0])
        self.accept('arrow_left', self.moveFighter, [self.fighter2, self.fighter2_body, -1, 0, 0])
        self.accept('arrow_right', self.moveFighter, [self.fighter2, self.fighter2_body, 1, 0, 0])
        self.accept('enter', self.punch, [self.fighter2_body, self.fighter1_body, 2])
        # AI toggle
        self.accept('t', self.toggleAI)
        
        self.accept('r', self.restartGame)
        # Block controls: Player1 uses Shift, Player2 uses Control
        self.accept('shift', self.setBlock, [1, True])
        self.accept('shift-up', self.setBlock, [1, False])
        self.accept('control', self.setBlock, [2, True])
        self.accept('control-up', self.setBlock, [2, False])
        
        # Tasks
        self.taskMgr.add(self.updatePhysics, "updatePhysics")
        self.taskMgr.add(self.updateUI, "updateUI")
        self.taskMgr.add(self.updateTimer, "updateTimer")
        self.taskMgr.add(self.updateStamina, "updateStamina")
        self.taskMgr.add(self.updateAI, "updateAI")

    def _make_fighter(self, model_path, anims, pos=Vec3(0,0,0), h=0, color=(1,1,1,1)):
        """Try to create an Actor from model_path; fall back to a colored placeholder NodePath.
        `color` is RGBA tuple.
        """
        # try loading an Actor (may fail if sample models aren't present)
        try:
            fighter = Actor(model_path, anims)
            fighter.reparentTo(self.render)
            fighter.setPos(pos)
            fighter.setH(h)
            try:
                fighter.setColorScale(*color)
            except Exception:
                pass
            return fighter
        except Exception:
            # try loading a simple box model that may exist
            try:
                box = loader.loadModel('models/box')
                box.reparentTo(self.render)
                box.setPos(pos)
                box.setH(h)
                try:
                    box.setColorScale(*color)
                except Exception:
                    pass
                return box
            except Exception:
                # final fallback: a thin vertical card to represent the fighter
                cm = CardMaker('fighter_card')
                cm.setFrame(-0.6, 0.6, 0, 2.2)
                node = self.render.attachNewNode(cm.generate())
                node.setPos(pos)
                node.setH(h)
                node.setColorScale(*color)
                return node

    def _spawn_hit_effect(self, world_pos):
        """Spawn a short-lived radial hit effect at world_pos (Vec3)."""
        cm = CardMaker('hit_effect')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        card = self.render.attachNewNode(cm.generate())
        card.setBillboardPointEye()
        card.setPos(world_pos)
        card.setScale(0.1)
        card.setColorScale(1, 0.4, 0.2, 1)

        # scale up and fade out
        scale_i = LerpScaleInterval(card, 0.35, 2.4, startScale=0.1)
        fade_i = LerpColorScaleInterval(card, 0.35, (1,0.4,0.2,0), startColorScale=(1,0.4,0.2,1))
        seq = Sequence(scale_i, fade_i, Func(card.removeNode))
        seq.start()
    
    def moveFighter(self, fighter, body, x, y, z):
        if self.game_over:
            return
        speed = 5 if (body == self.fighter1_body and self.health1 > 50) or (body == self.fighter2_body and self.health2 > 50) else 2  # Slower if low health
        force = Vec3(x * speed, y * speed, z * speed)
        body.applyCentralForce(force)
        try:
            fighter.loop("walk")
        except Exception:
            pass
    
    def punch(self, attacker_body, target_body, player):
        if self.game_over:
            return
        # stamina check
        attacker = 1 if attacker_body == self.fighter1_body else 2
        if attacker == 1 and self.stamina1 < self.stamina_cost_punch:
            return
        if attacker == 2 and self.stamina2 < self.stamina_cost_punch:
            return

        distance = (attacker_body.getTransform().getPos() - target_body.getTransform().getPos()).length()
        if distance < 2:
            # consume stamina for attacker
            if attacker == 1:
                self.stamina1 = max(0, self.stamina1 - self.stamina_cost_punch)
            else:
                self.stamina2 = max(0, self.stamina2 - self.stamina_cost_punch)

            # combo handling
            t = globalClock.getFrameTime()
            if attacker == 1:
                if (t - self.last_punch_time1) <= self.combo_window:
                    self.combo_count1 += 1
                else:
                    self.combo_count1 = 1
                self.last_punch_time1 = t
                combo_count = self.combo_count1
            else:
                if (t - self.last_punch_time2) <= self.combo_window:
                    self.combo_count2 += 1
                else:
                    self.combo_count2 = 1
                self.last_punch_time2 = t
                combo_count = self.combo_count2

            combo_bonus = max(0, (combo_count - 1) * 5)

            # compute damage
            base_damage = 10
            damage = base_damage + combo_bonus

            # if target is blocking, reduce damage and consume blocker's stamina
            if target_body == self.fighter1_body and self.block1:
                damage = int(damage * (1 - self.block_damage_reduction))
                self.stamina1 = max(0, self.stamina1 - self.block_stamina_cost)
            if target_body == self.fighter2_body and self.block2:
                damage = int(damage * (1 - self.block_damage_reduction))
                self.stamina2 = max(0, self.stamina2 - self.block_stamina_cost)

            force = Vec3(0, 0, 10) if player == 1 else Vec3(0, 0, -10)  # Knockback
            target_body.applyCentralImpulse(force)

            # apply damage
            if player == 1:
                self.health2 -= damage
            else:
                self.health1 -= damage

            # audio/visual feedback
            self.camera_shake_timer = self.camera_shake_duration
            self.hit_text_timer = 0.6
            if combo_count > 1:
                self.hit_text.setText(f"HIT! x{combo_count}")
            else:
                self.hit_text.setText("HIT!")
            if self.hit_sfx:
                try:
                    self.hit_sfx.play()
                except Exception:
                    pass
            if hasattr(self, 'punch_sfx') and self.punch_sfx:
                try:
                    self.punch_sfx.play()
                except Exception:
                    pass

            if self.health1 <= 0 or self.health2 <= 0:
                # play KO sound
                if hasattr(self, 'ko_sfx') and self.ko_sfx:
                    try:
                        self.ko_sfx.play()
                    except Exception:
                        pass
                self.gameOver()
            # spawn hit effect at target position (slightly above ground)
            try:
                pos = target_body.getTransform().getPos()
                pos2 = Vec3(pos.x, pos.y, pos.z + 1.0)
                self._spawn_hit_effect(pos2)
            except Exception:
                pass
    
    def updatePhysics(self, task):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        # Sync actor positions with physics bodies
        self.fighter1.setPos(self.fighter1_body.getTransform().getPos())
        self.fighter2.setPos(self.fighter2_body.getTransform().getPos())
        # Camera shake effect
        if self.camera_shake_timer > 0:
            self.camera_shake_timer -= dt
            frac = max(0.0, self.camera_shake_timer / self.camera_shake_duration)
            offset = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.5, 0.5)) * self.camera_shake_magnitude * frac
            self.camera.setPos(self.orig_cam_pos + offset)
        else:
            self.camera.setPos(self.orig_cam_pos)

        # Hit text timer
        if self.hit_text_timer > 0:
            self.hit_text_timer -= dt
            if self.hit_text_timer <= 0:
                self.hit_text.setText("")

        return Task.cont
    
    def updateUI(self, task):
        self.health_text1.setText(f"Player 1 Health: {self.health1}")
        self.health_text2.setText(f"Player 2 Health: {self.health2}")
        self.stamina_text1.setText(f"Stamina: {int(self.stamina1)}")
        self.stamina_text2.setText(f"Stamina: {int(self.stamina2)}")
        self.ai_status_text.setText(f"AI: {'On' if self.ai_enabled else 'Off'} (press T)")
        # show blocking and combo
        block1_label = 'Blocking' if self.block1 else ''
        block2_label = 'Blocking' if self.block2 else ''
        # append to stamina texts
        self.stamina_text1.setText(f"Stamina: {int(self.stamina1)} {block1_label} {('x'+str(self.combo_count1)) if self.combo_count1>1 else ''}")
        self.stamina_text2.setText(f"Stamina: {int(self.stamina2)} {block2_label} {('x'+str(self.combo_count2)) if self.combo_count2>1 else ''}")
        return Task.cont

    def updateStamina(self, task):
        dt = globalClock.getDt()
        if not self.game_over:
            self.stamina1 = min(self.max_stamina, self.stamina1 + self.stamina_recovery * dt)
            self.stamina2 = min(self.max_stamina, self.stamina2 + self.stamina_recovery * dt)
        return Task.cont

    def updateAI(self, task):
        # Simple AI for fighter2
        if self.game_over or not self.ai_enabled:
            return Task.cont
        t = globalClock.getFrameTime()
        p1 = self.fighter1_body.getTransform().getPos()
        p2 = self.fighter2_body.getTransform().getPos()
        vec = p1 - p2
        dist = vec.length()
        dt = globalClock.getDt()

        # Move towards player when far
        if dist > 1.8:
            dir = vec.normalized()
            speed = 4
            self.fighter2_body.applyCentralForce(dir * speed)
            self.fighter2.loop("walk")
        else:
            # Try to punch when in range and cooldown passed
            if self.stamina2 >= self.stamina_cost_punch and (t - self.ai_last_action) >= self.ai_action_cooldown:
                self.punch(self.fighter2_body, self.fighter1_body, 2)
                self.ai_last_action = t

        return Task.cont

    def toggleAI(self):
        self.ai_enabled = not self.ai_enabled
        self.ai_status_text.setText(f"AI: {'On' if self.ai_enabled else 'Off'} (press T)")

    def setBlock(self, player, value):
        if player == 1:
            self.block1 = value
        else:
            self.block2 = value

    
    def updateTimer(self, task):
        if not self.game_over:
            self.timer -= 1
            self.timer_text.setText(f"Time: {self.timer // 60}:{self.timer % 60:02d}")
            if self.timer <= 0:
                self.gameOver()
        return Task.cont
    
    def gameOver(self):
        self.game_over = True
        winner = "Player 1" if self.health2 <= 0 else "Player 2" if self.health1 <= 0 else "Time's Up - Draw"
        self.game_over_text.setText(f"Game Over! Winner: {winner}\nPress R to Restart")
    
    def restartGame(self):
        self.health1 = 100
        self.health2 = 100
        self.timer = 180
        self.game_over = False
        self.game_over_text.setText("")
        # reset stamina, blocks, combos
        self.stamina1 = self.max_stamina
        self.stamina2 = self.max_stamina
        self.block1 = False
        self.block2 = False
        self.combo_count1 = 0
        self.combo_count2 = 0
        # Reset positions
        self.fighter1.setPos(-5, 0, 0)
        self.fighter2.setPos(5, 0, 0)
        self.fighter1_body.setTransform(TransformState.makePos(Vec3(-5, 0, 0)))
        self.fighter2_body.setTransform(TransformState.makePos(Vec3(5, 0, 0)))


# Run the game
if __name__ == '__main__':
    game = UFCGame()
    game.run()
