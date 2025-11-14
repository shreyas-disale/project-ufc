# project-ufc
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletBoxShape, BulletPlaneShape
import sys

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
        self.fighter1 = Actor("models/ralph", {"run": "models/ralph-run", "walk": "models/ralph-walk"})
        self.fighter1.reparentTo(self.render)
        self.fighter1.setPos(-5, 0, 0)
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
        
        self.fighter2 = Actor("models/ralph", {"run": "models/ralph-run", "walk": "models/ralph-walk"})
        self.fighter2.reparentTo(self.render)
        self.fighter2.setPos(5, 0, 0)
        self.fighter2.setScale(0.5)
        self.fighter2.setH(180)
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
        
        # UI Elements
        self.health_text1 = OnscreenText(text=f"Player 1 Health: {self.health1}", pos=(-1.3, 0.9), scale=0.07, fg=(1, 1, 1, 1))
        self.health_text2 = OnscreenText(text=f"Player 2 Health: {self.health2}", pos=(0.7, 0.9), scale=0.07, fg=(1, 1, 1, 1))
        self.timer_text = OnscreenText(text=f"Time: {self.timer // 60}:{self.timer % 60:02d}", pos=(0, 0.9), scale=0.07, fg=(1, 1, 1, 1))
        self.instructions = OnscreenText(text="WASD: Move P1 | Arrows: Move P2 | Space/Enter: Punch | R: Restart", pos=(0, -0.9), scale=0.05, fg=(1, 1, 1, 1))
        self.game_over_text = OnscreenText(text="", pos=(0, 0), scale=0.1, fg=(1, 0, 0, 1))
        
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
        
        self.accept('r', self.restartGame)
        
        # Tasks
        self.taskMgr.add(self.updatePhysics, "updatePhysics")
        self.taskMgr.add(self.updateUI, "updateUI")
        self.taskMgr.add(self.updateTimer, "updateTimer")
    
    def moveFighter(self, fighter, body, x, y, z):
        if self.game_over:
            return
        speed = 5 if (body == self.fighter1_body and self.health1 > 50) or (body == self.fighter2_body and self.health2 > 50) else 2  # Slower if low health
        force = Vec3(x * speed, y * speed, z * speed)
        body.applyCentralForce(force)
        fighter.loop("walk")
    
    def punch(self, attacker_body, target_body, player):
        if self.game_over:
            return
        distance = (attacker_body.getTransform().getPos() - target_body.getTransform().getPos()).length()
        if distance < 2:
            force = Vec3(0, 0, 10) if player == 1 else Vec3(0, 0, -10)  # Knockback
            target_body.applyCentralImpulse(force)
            if player == 1:
                self.health2 -= 10
            else:
                self.health1 -= 10
            if self.health1 <= 0 or self.health2 <= 0:
                self.gameOver()
    
    def updatePhysics(self, task):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        # Sync actor positions with physics bodies
        self.fighter1.setPos(self.fighter1_body.getTransform().getPos())
        self.fighter2.setPos(self.fighter2_body.getTransform().getPos())
        return Task.cont
    
    def updateUI(self, task):
        self.health_text1.setText(f"Player 1 Health: {self.health1}")
        self.health_text2.setText(f"Player 2 Health: {self.health2}")
        return Task.cont
    
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
        # Reset positions
        self.fighter1.setPos(-5, 0, 0)
        self.fighter2.setPos(5, 0, 0)
        self.fighter1_body.setTransform(TransformState.makePos(Vec3(-5, 0, 0)))
        self.fighter2_body.setTransform(TransformState.makePos(Vec3(5, 0, 0)))

# Run the game
game = UFCGame()
game.run()
