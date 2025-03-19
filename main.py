from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, DirectionalLight, AmbientLight, LVecBase4, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerEvent, WindowProperties, TextureStage
import simplepbr
from panda3d.core import CardMaker
from direct.task import Task
import random
from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DirectEntry, OnscreenImage, DirectScrolledFrame
from direct.gui import DirectGuiGlobals as DGG
import os

loadPrcFile('settings.prc')

class AquaEscape(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        simplepbr.init()

        self.preload_models()

        #############################################################################
        #                       Titulo/Dimensão da Janela                           #
        #############################################################################
        props = WindowProperties()
        props.setTitle("AquaEscape")
        self.win.requestProperties(props)

        w, h = 1024, 768 

        props.setSize(w, h) 
        self.win.requestProperties(props) 

        #############################################################################
        #                       Luzes                                               #
        #############################################################################

        # Directional Light config
        d_light = DirectionalLight('d_light')
        d_light.setColor(LVecBase4(1, 1, 1, 1))  # cor
        d_lnp = self.render.attachNewNode(d_light)
        d_lnp.setHpr(-60, -60, 0)  # Ajusta direccao
        self.render.setLight(d_lnp)

        # Ambient Light Config
        a_light = AmbientLight('a_light')
        a_light.setColor(LVecBase4(0.3, 0.3, 0.3, 1))
        a_lnp = self.render.attachNewNode(a_light)
        self.render.setLight(a_lnp)

        #############################################################################
        #                       Texturas                                            #
        #############################################################################

        # sea textura
        ocean_texture_path = "images/ocean.jpg"
        ocean_texture = self.loader.loadTexture(ocean_texture_path)

        cm = CardMaker('ocean')
        cm.setFrame(-20, 20, -20, 20)
        self.ocean_plane = self.render.attachNewNode(cm.generate())
        self.ocean_plane.setTexture(ocean_texture)
        self.ocean_plane.setPos(0, 0, 0)

        # scale plane
        self.ocean_plane.setHpr(0, -90, 0)
        self.ocean_plane.setScale(10, 10, 10)

        # Carregar a textura do céu
        sky_texture_path = "images/ceu.jpg"
        sky_texture = self.loader.loadTexture(sky_texture_path)

        # Criar um plano e aplicar a textura do céu
        sky_cm = CardMaker('sky')
        sky_cm.setFrame(-20, 20, -20, 20)
        sky_plane = self.render.attachNewNode(sky_cm.generate())
        sky_plane.setTexture(sky_texture)
        sky_plane.setPos(0, 200, 75)  # Coloca o plano do céu à frente da câmera
        sky_plane.setHpr(0, 0, 0)  # Ajuste a rotação conforme necessário
        sky_plane.setScale(10, 10, 10)  # Ajuste a escala conforme necessário

        #############################################################################
        #                       Variáveis Movimento                                 #
        #############################################################################

        self.is_moving_left = False
        self.is_moving_right = False
        self.prancha_speed = 5
        self.boat_speed = 1
        self.boat_speed_increment = 0.3
        self.speed_increment_interval = 4
        self.obstacle_interval = random.uniform(0, 2)
        self.bonus_interval = random.uniform(0,4)
        self.floaters = []
        self.obstaculos = []
        self.bonus = []

        # Variáveis para o salto
        self.is_jumping = False
        self.jump_speed = 4
        self.gravity = -0.98
        self.vertical_speed = 0
        self.ground_y = 3  # Altura do chão

        #############################################################################
        #                       Load Models                                         #
        #############################################################################

        # Load board model
        prancha_model_path = "models/boardstickmen3.glb"
        self.prancha = self.loader.loadModel(prancha_model_path)
        self.prancha.reparentTo(self.render)
        x_position = random.uniform(-20, 20)
        self.prancha.setPos(x_position, -175, self.ground_y)

        # Adicionar nó de colisão à prancha
        prancha_collision_sphere = CollisionSphere(0, 0, 0, 1.5)
        prancha_collision_node = CollisionNode('prancha_collision')
        prancha_collision_node.addSolid(prancha_collision_sphere)
        self.prancha_collision_np = self.prancha.attachNewNode(prancha_collision_node)
        self.prancha_collision_np.show()

        # Definir a câmera inicial
        self.cam1 = self.camera
        self.cam2 = self.makeCamera(self.win, camName="cam2")
        
        self.cam1.reparentTo(self.prancha)
        self.cam1.setPos(0, 0, 0)
        
        self.cam2.reparentTo(self.prancha)
        self.cam2.setPos(0, -10, 10)
        
        self.current_camera = self.cam1
        self.cam2.node().getDisplayRegion(0).setActive(0)
        
        # Estado inicial do jogo
        self.game_started = False

        self.previous_menu = None

        # Criar menu inicial
        self.create_menu()

        # Criar menu de pausa
        self.create_pause_menu()

        # Inicializar a pontuação
        self.score = 0
        self.score_label = DirectLabel(text=f"Score: {self.score}",
                                       scale=0.1,
                                       pos=(0.6, 0, 0.8),
                                       frameColor=(0, 0, 0, 0),
                                       text_fg=(1, 1, 1, 1))
        self.score_label.hide()

        # Inicializar o timer
        self.timer = 10
        self.timer_label = DirectLabel(text=f"Time: {self.format_time(self.timer)}",
                                       scale=0.1,
                                       pos=(-0.6, 0, 0.8),
                                       frameColor=(0, 0, 0, 0),
                                       text_fg=(1, 1, 1, 1))
        self.timer_label.hide()

        #############################################################################
        #                       Música de Fundo                                     #
        #############################################################################

        self.background_music = self.loader.loadMusic('background_music.mp3')
        self.background_music.setLoop(True)
        self.background_music.play()

        # Configurar eventos de teclado
        self.accept("arrow_left", self.set_moving_left, [True])
        self.accept("arrow_left-up", self.set_moving_left, [False])
        self.accept("arrow_right", self.set_moving_right, [True])
        self.accept("arrow_right-up", self.set_moving_right, [False])
        self.accept("arrow_up", self.start_jump)
        self.accept("arrow_up-up", self.end_jump)
        self.accept("z", self.toggle_cam1)
        self.accept("x", self.toggle_cam2)
        self.accept("p", self.toggle_pause)
        self.accept("s", self.toggle_music)

        # Adicionar tarefa de atualização
        self.taskMgr.add(self.update_task, "update")
        self.taskMgr.doMethodLater(1, self.generate_obstacle_task, "generateObstacleTask")
        self.taskMgr.doMethodLater(self.bonus_interval, self.generate_bonus_task, "generateBonusTask")
        self.taskMgr.doMethodLater(self.speed_increment_interval, self.increment_boat_speed_task, "incrementBoatSpeedTask")

        # Configurar o gerenciador de colisões
        self.cTrav = CollisionTraverser()
        self.cHandler = CollisionHandlerEvent()
        self.cHandler.addInPattern('%fn-into-%in')

        self.accept('prancha_collision-into-obstacle_collision', self.on_collision)
        self.accept('prancha_collision-into-gelado_collision', self.on_bonus_collision)

        self.cTrav.addCollider(self.prancha_collision_np, self.cHandler)

        # Adicionar boias nos limites
        self.add_initial_floaters()

        # Mostrar imagem inicial
        self.show_intro_image()

        # Adicionar tarefa de atualização da textura do mar
        self.taskMgr.add(self.update_ocean_texture, "updateOceanTexture")

    def update_ocean_texture(self, task):
        if not self.game_started:
            return task.cont
        offset = task.time * 0.1
        self.ocean_plane.setTexOffset(TextureStage.getDefault(), 0, offset)
        return task.cont

    def preload_models(self):
        self.preloaded_models = {
            "boat": self.loader.loadModel("models/boat.glb"),
            "Shark2": self.loader.loadModel("models/Shark2.glb"),
            "gelado": self.loader.loadModel("models/gelado.glb"),
            "ilha": self.loader.loadModel("models/ilha.glb"),
        }    

    def toggle_music(self):
        if self.background_music.status() == self.background_music.PLAYING:
            self.background_music.stop()
        else:
            self.background_music.play()    

    def show_intro_image(self):
        self.intro_frame = DirectFrame(frameColor=(0, 0, 0, 1),
                                       frameSize=(-0.9, 0.9, -0.9, 0.7),
                                       pos=(0, 0, 0))
        self.intro_image = OnscreenImage(parent=self.intro_frame, image='images/titulo.jpg', scale=(1.33, 1, 1))
        
        # Contador decrescente
        self.countdown_label = DirectLabel(text="5",
                                           scale=0.5,
                                           pos=(0, 0, -0.8),
                                           frameColor=(0, 0, 0, 0),
                                           text_fg=(1, 1, 1, 1),
                                           parent=self.intro_frame)
        self.countdown_time = 5
        self.taskMgr.doMethodLater(1, self.update_countdown, "updateCountdown")

    def update_countdown(self, task):
        self.countdown_time -= 1
        if self.countdown_time > 0:
            self.countdown_label['text'] = str(self.countdown_time)
            return task.again
        else:
            self.hide_intro_image()
            return task.done

    def hide_intro_image(self):
        self.intro_frame.destroy()
        self.menu_frame.show()

    def create_menu(self):
        # Criar um frame para o menu
        self.menu_frame = DirectFrame(frameColor=(0, 0, 0, 0),
                                      frameSize=(-1, 1, -1, 1),
                                      pos=(0, 0, 0))

        # Adicionar imagem de fundo ao menu
        self.menu_bg_image = OnscreenImage(parent=self.menu_frame, image='images/base.jpg', scale=(1.33, 1, 1))
        self.menu_bg_image.setPos(0, 0, 0)
        
        # Botão Start
        self.start_button = DirectButton(text=("Start"),
                                         scale=0.1,
                                         command=self.start_game,
                                         pos=(0, 0, 0.3),
                                         parent=self.menu_frame)
        
         # Botão Controls (se quiser ter controles no menu de pausa também)
        self.pause_controls_button = DirectButton(text=("Controls"),
                                                    scale=0.1,
                                                    command=self.show_controls,
                                                    pos=(0, 0, 0.1),
                                                    parent=self.menu_frame)

        # Botão High Scores
        self.high_scores_button = DirectButton(text=("High Scores"),
                                               scale=0.1,
                                               command=self.show_high_scores,
                                               pos=(0, 0, -0.1),
                                               parent=self.menu_frame)

        # Botão Quit
        self.quit_button = DirectButton(text=("Quit"),
                                        scale=0.1,
                                        command=self.quit_game,
                                        pos=(0, 0, -0.3),
                                        parent=self.menu_frame)
        
     
    def create_pause_menu(self):
        # Criar um frame para o menu de pausa
        self.pause_menu_frame = DirectFrame(frameColor=(0, 0, 0, 0.5),
                                            frameSize=(-0.9, 0.9, -0.9, 0.7),
                                            pos=(0, 0, 0))
        self.pause_menu_frame.hide()

        # Adicionar imagem de fundo ao menu de pausa
        self.pause_bg_image = OnscreenImage(parent=self.pause_menu_frame, image='images/base.jpg', scale=(1.33, 1, 1))

        # Botão Resume
        self.resume_button = DirectButton(text=("Resume"),
                                          scale=0.1,
                                          command=self.resume_game,
                                          pos=(0, 0, 0.3),
                                          parent=self.pause_menu_frame)

        # Botão Controls
        self.pause_controls_button = DirectButton(text=("Controls"),
                                                  scale=0.1,
                                                  command=self.show_controls_from_pause,
                                                  pos=(0, 0, 0.1),
                                                  parent=self.pause_menu_frame)

        # Botão Quit
        self.pause_quit_button = DirectButton(text=("Quit"),
                                              scale=0.1,
                                              command=self.quit_game,
                                              pos=(0, 0, -0.1),
                                              parent=self.pause_menu_frame)

    def toggle_pause(self):
        if self.taskMgr.hasTaskNamed("update"):
            self.pause_game()
        else:
            self.resume_game()

    def pause_game(self):
        if self.game_started:
            self.taskMgr.remove("update")
            self.taskMgr.remove("generateObstacleTask")
            self.taskMgr.remove("generateBonusTask")
            self.taskMgr.remove("incrementBoatSpeedTask")
            self.taskMgr.remove("incrementScoreTask")
            self.taskMgr.remove("decrementTimerTask")
            self.pause_menu_frame.show()
            self.ignore_keys()

    def clear_obstacles(self):
        for obstacle in self.obstaculos:
            obstacle.removeNode()
        self.obstaculos.clear()

    def clear_bonus(self):
        for bonus in self.bonus:
            bonus.removeNode()
        self.bonus.clear()    

    def start_game(self):
        self.game_started = True
        self.timer = 120
        self.boat_speed = 1
        self.prancha.setPos(0, -175, self.ground_y)
        self.prancha.set_r(0)
        self.clear_obstacles()
        self.clear_bonus()
        self.menu_frame.hide()
        self.update_score(-self.score)
        self.timer_label['text'] = f"Time: {self.format_time(self.timer)}"
        self.score_label.show()
        self.timer_label.show()
        self.taskMgr.remove("incrementScoreTask")
        self.taskMgr.remove("decrementTimerTask")
        self.taskMgr.remove("generateObstacleTask")
        self.taskMgr.remove("generateBonusTask")
        self.taskMgr.remove("incrementBoatSpeedTask")
        self.taskMgr.doMethodLater(1, self.increment_score_task, "incrementScoreTask")
        self.taskMgr.doMethodLater(1, self.decrement_timer_task, "decrementTimerTask")
        self.taskMgr.doMethodLater(1, self.generate_obstacle_task, "generateObstacleTask")
        self.taskMgr.doMethodLater(self.bonus_interval, self.generate_bonus_task, "generateBonusTask")
        self.taskMgr.doMethodLater(self.speed_increment_interval, self.increment_boat_speed_task, "incrementBoatSpeedTask")
        self.accept_keys()

    def resume_game(self):
        self.taskMgr.remove("incrementScoreTask")
        self.taskMgr.remove("decrementTimerTask")
        self.taskMgr.remove("generateObstacleTask")
        self.taskMgr.remove("generateBonusTask")
        self.taskMgr.remove("incrementBoatSpeedTask")
        self.taskMgr.add(self.update_task, "update")
        self.taskMgr.doMethodLater(1, self.generate_obstacle_task, "generateObstacleTask")
        self.taskMgr.doMethodLater(self.bonus_interval, self.generate_bonus_task, "generateBonusTask")
        self.taskMgr.doMethodLater(self.speed_increment_interval, self.increment_boat_speed_task, "incrementBoatSpeedTask")
        self.taskMgr.doMethodLater(1, self.increment_score_task, "incrementScoreTask")
        self.taskMgr.doMethodLater(1, self.decrement_timer_task, "decrementTimerTask")
        self.pause_menu_frame.hide()
        self.accept_keys()
        
    def show_controls(self):
        self.menu_frame.hide()

        # Criar frame de controles
        self.controls_frame = DirectFrame(frameColor=(0, 0, 0, 0.5),
                                          frameSize=(-0.9, 0.9, -0.9, 0.7),
                                          pos=(0, 0, 0))

        # Exibir a imagem de controles
        self.controls_image = OnscreenImage(image="images/controlos.jpg",
                                            pos=(0, 0, 0),
                                            parent=self.controls_frame,
                                            scale=(1.33, 1, 1))

        # Botão de volta ao menu
        self.back_button = DirectButton(text=("Back"),
                                        scale=0.1,
                                        command=self.back_from_controls,
                                        pos=(0, 0, -0.8),
                                        parent=self.controls_frame)

    def show_controls_from_pause(self):
        self.previous_menu = "pause"
        self.pause_menu_frame.hide()
        self.show_controls()

    def back_from_controls(self):
        self.controls_frame.hide()
        if self.previous_menu == None:
            self.menu_frame.show()
        elif self.previous_menu == "pause":
            self.pause_menu_frame.show()

    def back_to_menu(self):
        self.controls_frame.hide()
        self.menu_frame.show()

    def back_to_menu_highscores(self):
        self.scores_frame.hide()
        self.menu_frame.show()

    def back_to_pause_menu(self):
        self.controls_frame.hide()
        self.pause_menu_frame.show()

    def show_high_scores(self):
        self.hide_all_frames()

        self.scores_frame = DirectScrolledFrame(canvasSize=(-0.7, 0.7, -2, 0.8),
                                                frameColor=(0, 0, 0, 0.7),
                                                frameSize=(-0.7, 0.7, -0.7, 0.7),
                                                pos=(0, 0, 0),
                                                scrollBarWidth=0.05,
                                                manageScrollBars=False,
                                                verticalScroll_relief=DGG.FLAT,
                                                horizontalScroll_relief=DGG.FLAT,
                                                autoHideScrollBars=False)

        self.scores_frame.verticalScroll.setPos(0.7, 0, 0)
        self.scores_frame.verticalScroll.setScale(1, 1, 0.7)
        self.scores_frame.verticalScroll.show()
        
        self.scores_frame.horizontalScroll.hide()
        self.scores_frame.horizontalScroll['state'] = DGG.DISABLED

        DirectLabel(text="High Scores",
                    scale=0.1,
                    pos=(0, 0, 0.65),
                    parent=self.scores_frame.getCanvas(),
                    frameColor=(0, 0, 0, 0),
                    text_fg=(1, 1, 1, 1))

        scores_list = []

        if os.path.exists("high_scores.txt"):
            with open("high_scores.txt", "r") as file:
                for line in file:
                    scores_list.append(line.strip())
        else:
            scores_list.append("Ainda não há pontuações.")

        y_position = 0.5
        for score in scores_list:
            DirectLabel(text=score,
                        scale=0.07,
                        pos=(0, 0, y_position),
                        parent=self.scores_frame.getCanvas(),
                        frameColor=(0, 0, 0, 0),
                        text_fg=(1, 1, 1, 1))
            y_position -= 0.1

        self.back_to_menu_button = DirectButton(text=("Back to Menu"),
                                                scale=0.1,
                                                command=self.back_to_menu_highscores,
                                                pos=(0, 0, y_position - 0.1),
                                                parent=self.scores_frame.getCanvas())
        
        self.accept("wheel_up", self.scroll_scores_frame, [-1])
        self.accept("wheel_down", self.scroll_scores_frame, [1])

    def scroll_scores_frame(self, direction):
        self.scores_frame.verticalScroll.setValue(self.scores_frame.verticalScroll['value'] + direction * 0.1)

    def hide_all_frames(self):
        if hasattr(self, 'menu_frame'):
            self.menu_frame.hide()
        if hasattr(self, 'name_frame'):
            self.name_frame.hide()
        if hasattr(self, 'scores_frame'):
            self.scores_frame.hide()
        self.score_label.hide()
        self.timer_label.hide()

    def quit_game(self):
        self.userExit()

    def toggle_cam1(self):
        base.cam.reparentTo(self.cam1)
        base.cam.setPos(0, 0, 0)
        base.cam.lookAt(self.prancha)

    def toggle_cam2(self):
        base.cam.reparentTo(self.cam2)
        base.cam.setPos(0, -30, 0)
        base.cam.lookAt(self.prancha)
 
    def set_moving_left(self, is_moving):
        self.is_moving_left = is_moving

    def set_moving_right(self, is_moving):
        self.is_moving_right = is_moving

    def start_jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.vertical_speed = self.jump_speed

    def end_jump(self):
        if self.is_jumping:
            self.vertical_speed += self.gravity  # Apply gravity immediately after releasing the jump key

    def update_jump(self, dt):
        if self.is_jumping:
            new_z = self.prancha.get_z() + self.vertical_speed * dt
            if new_z < self.ground_y:
                new_z = self.ground_y
                self.is_jumping = False
                self.vertical_speed = 0
            self.prancha.set_z(new_z)
            self.vertical_speed += self.gravity * dt

    ####################### Fuction to Generate Obstacle
    def generate_obstacle_task(self, task):
        if self.game_started:
            self.generate_boat_obstacle()
            self.generate_shark_obstacle()
            self.generate_ilha_obstacle()
        return task.again
    
    def generate_bonus_task(self, task):
        if self.game_started:
            self.generate_gelado_obstacle()
        return task.again

    def generate_boat_obstacle(self):
        obstacle = self.preloaded_models["boat"].copyTo(self.render)
        x_position = random.uniform(-20, 20)
        obstacle.setPos(x_position, 180, 12)
        obstacle.setScale(4, 4, 4)

        obstacle_collision_sphere = CollisionSphere(0.1, 0.2, -3, 1)
        obstacle_collision_node = CollisionNode('obstacle_collision')
        obstacle_collision_node.addSolid(obstacle_collision_sphere)
        obstacle_collision_np = obstacle.attachNewNode(obstacle_collision_node)
        #obstacle_collision_np.show()

        self.cTrav.addCollider(obstacle_collision_np, self.cHandler)
        self.obstaculos.append(obstacle)

    def generate_shark_obstacle(self):
        obstacle = self.preloaded_models["Shark2"].copyTo(self.render)
        x_position = random.uniform(-15, 15)
        obstacle.setPos(x_position, 180, 12)
        obstacle.setScale(6, 6, 6)

        obstacle_collision_sphere = CollisionSphere(0, 0, -1.5, 0.2)
        obstacle_collision_node = CollisionNode('obstacle_collision')
        obstacle_collision_node.addSolid(obstacle_collision_sphere)
        obstacle_collision_np = obstacle.attachNewNode(obstacle_collision_node)
        #obstacle_collision_np.show()

        self.cTrav.addCollider(obstacle_collision_np, self.cHandler)
        self.obstaculos.append(obstacle)

    def generate_ilha_obstacle(self):
        obstacle = self.preloaded_models["ilha"].copyTo(self.render)
        x_position = random.uniform(-20, 20)
        obstacle.setPos(x_position, 180, 12)
        obstacle.setScale(4, 4, 4)

        obstacle_collision_sphere = CollisionSphere(0.35, 0, -2.5, 0.75)
        obstacle_collision_node = CollisionNode('obstacle_collision')
        obstacle_collision_node.addSolid(obstacle_collision_sphere)
        obstacle_collision_np = obstacle.attachNewNode(obstacle_collision_node)
        #obstacle_collision_np.show()

        self.cTrav.addCollider(obstacle_collision_np, self.cHandler)
        self.obstaculos.append(obstacle)

    def generate_gelado_obstacle(self):
        if len(self.bonus) == 0:  # Verifica se não há outros bônus
            obstacle = self.preloaded_models["gelado"].copyTo(self.render)
            x_position = random.uniform(-20, 20)
            obstacle.setPos(x_position, 180, 4)
            obstacle.setScale(1, 1, 1)

            obstacle_collision_sphere = CollisionSphere(0, 0, -1, 0.5)
            obstacle_collision_node = CollisionNode('gelado_collision')
            obstacle_collision_node.addSolid(obstacle_collision_sphere)
            obstacle_collision_np = obstacle.attachNewNode(obstacle_collision_node)
            #obstacle_collision_np.show()

            self.cTrav.addCollider(obstacle_collision_np, self.cHandler)
            self.bonus.append(obstacle) 

    def increment_boat_speed_task(self, task):
        if self.game_started:
            self.boat_speed += self.boat_speed_increment
        return task.again

    def update_task(self, task):
        if not self.game_started:
            return Task.cont

        dt = 0.15
        if self.is_moving_left:
            new_x = self.prancha.get_x() - self.prancha_speed * dt
            if new_x >= -20:
                self.prancha.set_x(new_x)
                self.prancha.set_r(max(self.prancha.get_r() - 1, -5))
        elif self.is_moving_right:
            new_x = self.prancha.get_x() + self.prancha_speed * dt
            if new_x <= 20:
                self.prancha.set_x(new_x)
                self.prancha.set_r(min(self.prancha.get_r() + 1, 5))
        else:
            if self.prancha.get_r() > 0:
                self.prancha.set_r(max(self.prancha.get_r() - 1, 0))
            elif self.prancha.get_r() < 0:
                self.prancha.set_r(min(self.prancha.get_r() + 1, 0))

        self.update_jump(dt)

        for obstacle in self.obstaculos:
            obstacle.set_y(obstacle, -self.boat_speed * dt)
            if obstacle.get_y() < -200:
                obstacle.removeNode()
                self.obstaculos.remove(obstacle)

        for bonus in self.bonus:
            bonus.set_y(bonus, -self.boat_speed * dt)
            if bonus.get_y() < -200:
                bonus.removeNode()
                self.bonus.remove(bonus)        

        for floater in self.floaters:
            floater.set_y(floater, -self.boat_speed * dt)
            if floater.get_y() < -200:
                floater.set_y(200)

        self.cTrav.traverse(self.render)

        return Task.cont

    def on_collision(self, entry):
        if self.score < 50:
            self.update_score(-self.score)
        else:
            self.update_score(-50)

    def on_bonus_collision(self, entry):
        bonus = entry.getIntoNodePath().getParent()
        if bonus in self.bonus:
            self.update_score(100)
            bonus.removeNode()

    def add_initial_floaters(self):
        floater_model_path = "models/floater.glb"

        y_positions = range(-180, 201, 20)
        for y in y_positions:
            floater = self.loader.loadModel(floater_model_path)
            floater.reparentTo(self.render)
            floater.setPos(-23, y, 3)
            self.floaters.append(floater)

        for y in y_positions:
            floater = self.loader.loadModel(floater_model_path)
            floater.reparentTo(self.render)
            floater.setPos(23, y, 3)
            self.floaters.append(floater)

    def update_score(self, points):
        self.score += points
        self.score_label['text'] = f"Score: {self.score}"

    def increment_score_task(self, task):
        if self.game_started:
            self.update_score(10)
        return task.again

    def decrement_timer_task(self, task):
        if self.game_started:
            self.timer -= 1
            self.timer_label['text'] = f"Time: {self.format_time(self.timer)}"
            if self.timer <= 0:
                self.game_started = False
                print("Tempo esgotado!")
                self.prompt_for_name()
                return Task.done
        return task.again

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"
    
    def prompt_for_name(self):
        self.hide_all_frames()
        self.name_frame = DirectFrame(frameColor=(0, 0, 0, 0.7),
                                      frameSize=(-0.9, 0.9, -0.9, 0.7),
                                      pos=(0, 0, 0))

        self.title_label = DirectLabel(text="Introduza o seu nome",
                                       scale=0.1,
                                       pos=(0, 0, 0.2),
                                       parent=self.name_frame,
                                       frameColor=(0, 0, 0, 0),
                                       text_fg=(1, 1, 1, 1))

        self.name_entry = DirectEntry(text="",
                                      scale=0.1,
                                      pos=(-0.5, 0, 0),
                                      command=self.save_score,
                                      initialText="Enter your name",
                                      numLines=1,
                                      focus=1,
                                      focusInCommand=self.clear_text,
                                      parent=self.name_frame)

        self.ok_button = DirectButton(text=("OK"),
                                      scale=0.1,
                                      command=lambda: self.save_score(self.name_entry.get()),
                                      pos=(-0.3, 0, -0.2),
                                      parent=self.name_frame)

        self.cancel_button = DirectButton(text=("Cancelar"),
                                          scale=0.1,
                                          command=self.cancel_name_entry,
                                          pos=(0.2, 0, -0.2),
                                          parent=self.name_frame)
        
        self.ignore_keys()
        
    def clear_text(self):
        self.name_entry.enterText('')

    def cancel_name_entry(self):
        self.name_frame.hide()
        self.show_high_scores()
        self.accept_keys()

    def save_score(self, player_name):
        self.name_frame.hide()
        scores = []

        if os.path.exists("high_scores.txt"):
            with open("high_scores.txt", "r") as file:
                for line in file:
                    parts = line.split('-')
                    if len(parts) == 2:
                        name = parts[0].strip().split(' ', 1)[-1].strip()
                        score = parts[1].strip()
                        scores.append((name, int(score)))

        scores.append((player_name, self.score))
        scores.sort(key=lambda x: x[1], reverse=True)

        scores = scores[:20]

        with open("high_scores.txt", "w") as file:
            for index, (name, score) in enumerate(scores, start=1):
                file.write(f"{index}. {name} - {score}\n")

        self.show_high_scores()
        self.accept_keys()
     
    def ignore_keys(self):
        self.ignore("x")
        self.ignore("z")
        self.ignore("p")

    def accept_keys(self):
        self.accept("x", self.toggle_cam1)
        self.accept("z", self.toggle_cam2)
        self.accept("p", self.toggle_pause)     

game = AquaEscape()
game.run()
