from const import *
from Pad import *
import pygame
from network import *


class Canvas:
    def __init__(self, w, h, title="None"):
        self.width = w
        self.height = h
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption(title)

    @staticmethod
    def update():
        pygame.display.update()

    def get_canvas(self):
        return self.screen

    def draw_ball(self, ball):
        self.screen.blit(ball.image, ball.rect)

    def draw_text(self, text, size, x, y):
        pygame.font.init()
        font = pygame.font.Font(None, size)

        render = font.render(text, 1, colors['living coral'])

        self.screen.blit(render, (x, y))

    def draw_background(self):
        self.screen.fill(colors['black'])


class Player:
    def __init__(self, name, color):
        self.name = name
        self.score = 0
        self.color = color
        self.lives = 0
        self.pad = None
        self.lost = False

        self.push_ball_mode = 0

        self.send_data = {
            "id": 0,
            "x": 0,
            "y": 0,
            "push_ball_mode": 0,
            "start_new_game": 0,
        }

    def create_pad(self, left, top, width, height):
        self.pad = Pad(left, top, width, height, self.color)

    def draw(self, c):
        pygame.draw.rect(c, self.color, self.pad)

    def draw_score(self, c):
        c.draw_text(str(self.score), 25, self.pad.left, 10)

    def draw_lives(self, c, counter):
        counter -= 5
        text = "Lives:"
        text = text + str(self.lives)
        c.draw_text(text, 25, self.pad.left-50*counter, screen_size[1] - 40)

    def draw_finish_screen(self, c, win_control, player_id):
        c.draw_background()
        text = "Game Over"
        if player_id == 0:
            if win_control["0"] == 0:
                text = "You won the game"
            else:
                text = "You lost the game"
        if player_id == 1:
            if win_control["1"] == 0:
                text = "You won the game"
            else:
                text = "You lost the game"
        c.draw_text(text, 25, screen_center[0]-50, screen_center[1])


class Ball(pygame.sprite.Sprite):
    def __init__(self, path, speed, pos):
        pygame.sprite.Sprite.__init__(self)

        self.path = path
        self.speed = speed

        self.ball_size = ball_size  # const ref

        self.image = pygame.image.load(path).convert_alpha()
        self.image = pygame.transform.scale(self.image, self.ball_size)

        self.rect = self.image.get_rect()

        self.resize()

        self.rect.left, self.rect.right = pos

    def resize(self):
        self.rect.width = self.ball_size[0]
        self.rect.height = self.ball_size[1]


class Game:
    def __init__(self, w, h):
        self.net = Network()

        self.player_id = int(self.net.id)
        self.another_player_id = (self.player_id + 1) % 2

        self.width = w
        self.height = h

        self.canvas = Canvas(self.width, self.height, "PR Pong Projekt")

        self.players = [Player('R', colors['white']),
                        Player('P', colors['white'])]

        self.players[0].create_pad(players_pos[0][0], players_pos[0][1], pad_size[0], pad_size[1])
        self.players[1].create_pad(players_pos[1][0], players_pos[1][1], pad_size[0], pad_size[1])

        self.players[self.player_id].send_data["id"] = self.player_id
        self.players[self.player_id].send_data["x"] = self.players[self.player_id].pad.rect.left
        self.players[self.player_id].send_data["y"] = self.players[self.player_id].pad.rect.top
        self.players[self.player_id].send_data["push_ball_mode"] = self.players[self.player_id].push_ball_mode

        self.ball = Ball('ball.png', [0, 0], (0, 0))

    def set_another_player_position(self, pos):
        id = self.another_player_id
        self.players[id].pad.rect.left, self.players[id].pad.rect.top = pos[0], pos[1]

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEMOTION:
                    self.players[self.player_id].pad.rect.centery = event.pos[1]

                elif event.type == pygame.KEYDOWN:
                    if self.players[self.player_id].push_ball_mode == 1 and event.key == pygame.K_SPACE:
                        self.players[self.player_id].push_ball_mode = 2

                    elif self.players[self.another_player_id].lost == 1 and event.key == pygame.K_RETURN:
                        self.players[self.player_id].lost = 2

            # Send Network Stuff

            self.players[self.player_id].send_data["x"] = self.players[self.player_id].pad.rect.left
            self.players[self.player_id].send_data["y"] = self.players[self.player_id].pad.rect.top
            self.players[self.player_id].send_data["push_ball_mode"] = self.players[self.player_id].push_ball_mode
            self.players[self.player_id].send_data["start_new_game"] = self.players[self.player_id].lost

            network_data = self.net.send(self.players[self.player_id].send_data)

            if network_data is None:
                break

            opp = network_data["another_player"]  # opponent
            self.set_another_player_position((opp["x"], opp["y"]))

            ball_pos = network_data["ball"]
            self.ball.rect.left, self.ball.rect.top = ball_pos["x"], ball_pos["y"]
            self.players[self.player_id].push_ball_mode = network_data["push_ball_mode"]

            score = network_data["score"]
            self.players[0].score = score["0"]
            self.players[1].score = score["1"]

            lives = network_data["lives"]
            self.players[0].lives = lives["0"]
            self.players[1].lives = lives["1"]

            win_control = network_data["has_lost"]
            self.players[0].lost = win_control["0"]
            self.players[1].lost = win_control["1"]

            # Update Canvas
            self.canvas.draw_background()
            # kółko
            self.canvas.draw_ball(self.ball)

            counter = 5
            # gracze,zycia i punkty
            for player in self.players:
                player.draw(self.canvas.get_canvas())
                player.draw_score(self.canvas)
                player.draw_lives(self.canvas, counter)
                counter += 1

            # linia w srodku
            for i in range(0, 15):
                x = self.width/2
                y = i * 70
                indent = 35
                pygame.draw.line(self.canvas.get_canvas(), colors['white'],
                                 (x, y + indent), (x, y))
            for player in self.players:
                if self.players[0].lost == 1 or self.players[1].lost == 1:
                    player.draw_finish_screen(self.canvas, win_control, self.player_id)
            self.canvas.update()

        self.net.close()
        pygame.quit()


g = Game(screen_size[0], screen_size[1])
g.run()
