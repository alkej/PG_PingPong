from const import *
from Pad import *

from _thread import *
import socket
import pygame
import random
import time

import json


class BallServer:
    def __init__(self, position):
        self.rect = pygame.Rect(position[0], position[1], ball_size[0], ball_size[1])
        if random.randint(0, 10) < 5:
            coef = 1
        else:
            coef = -1
        self.speed = [coef*max_speed[0], 0]

    def get_position(self):
        return self.rect.left, self.rect.top


class Player:
    def __init__(self, position):
        self.pad = Pad(position[0], position[1], pad_size[0], pad_size[1], None)

        self.lives = lives_num
        self.score = 0
        self.has_lost = 0
        self.send_data = {
            "another_player": {
                "id": 0,
                "x": 0,
                "y": 0,
            },
            "ball": {
                "x": 0,
                "y": 0,
            },
            "push_ball_mode": 0,
            "score": {
                "0": 0,
                "1": 0,
            },
            "lives": {
                "0": 0,
                "1": 0,
            },
            "has_lost": {
                "0": 0,
                "1": 0,
            }
        }

    def update_position(self, position):
        self.pad.rect.left = position[0]
        self.pad.rect.top = position[1]

    def get_position(self):
        return self.pad.rect.left, self.pad.rect.top


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind(("", port))
except socket.error as e:
    print(str(e))
    exit()

s.listen(2)
print("Waiting for a connection")

current_id = 0
connected_players = 0
clients = []

players = [Player([players_pos[0][0], players_pos[0][1]]),
           Player([players_pos[1][0], players_pos[1][1]])]

ball = BallServer(ball_pos_init)

miss_the_ball = [False, False]


clock = pygame.time.Clock()

lock = allocate_lock()


def ball_position():
    global ball, connected_players, miss_the_ball, lock

    x = ball.rect.left
    y = ball.rect.top

    while True:
        if connected_players == 2:
            clock.tick(60)
            if not miss_the_ball[0] and not miss_the_ball[1]:
                try:
                    lock.acquire()

                    x += ball.speed[0]
                    y += ball.speed[1]

                    if y <= 0 or y >= screen_size[1] - ball_size[1]:
                        ball.speed[1] = -ball.speed[1]

                    if x < 0:
                        miss_the_ball[0] = True
                        players[0].lives -= 1
                        if players[0].lives == 0:
                            players[0].has_lost = 1
                    elif x > screen_size[0]:
                        miss_the_ball[1] = True
                        players[1].lives -= 1
                        if players[1].lives == 0:
                            players[1].has_lost = 1

                    ball.rect.left = x
                    ball.rect.top = y
                finally:
                    lock.release()
            else:
                try:
                    lock.acquire()
                    if miss_the_ball[0]:
                        pad_pos = players[1].pad.rect.midleft
                        x = int(pad_pos[0] - ball_size[0])
                        y = int(pad_pos[1] - ball_size[1]/2)

                    elif miss_the_ball[1]:
                        pad_pos = players[0].pad.rect.midright
                        x = int(pad_pos[0])
                        y = int(pad_pos[1] - ball_size[1]/2)

                    ball.rect.left = x
                    ball.rect.top = y

                finally:
                    lock.release()


def check_collision():
    global ball, lock, players

    add_score_player = None
    check_flag = True

    while True:
            while check_flag:
                try:
                    lock.acquire()
                    for player in players:
                        if ball.rect.colliderect(player.pad.rect):
                            ball.speed[0] = -ball.speed[0]
                            ball.speed[1] = random.randint(-max_speed[1], max_speed[1])

                            add_score_player = player
                            check_flag = False
                finally:
                    lock.release()
            if add_score_player is not None:
                try:
                    lock.acquire()
                    add_score_player.score += 1
                    check_flag = True
                finally:
                    lock.release()
            time.sleep(1)


def threaded_client(conn):
    global current_id, connected_players, miss_the_ball, lock

    local_id = 0

    try:
        lock.acquire()

        connected_players += 1
        conn.send(str.encode(str(current_id)))
        current_id = (current_id + 1) % 2
    finally:
        lock.release()

    while True:
        clock.tick(60)
        try:
            data = conn.recv(2048).decode("utf-8")
            try:
                reply = json.loads(data)
            except json.decoder.JSONDecodeError:
                break
            if not data:
                break
            else:
                # print("Recieved: " + str(reply))
                local_id = reply["id"]

                sender_id = reply["id"]
                sender_pos = (reply["x"], reply["y"])
                sender_released_ball = reply["push_ball_mode"]
                sender_start_new_game = reply["start_new_game"]

                rec_id = (sender_id + 1) % 2  # receiver user (player) id
                try:
                    lock.acquire()
                    players[sender_id].update_position(sender_pos)

                    if miss_the_ball[rec_id] and sender_released_ball == 2:
                        miss_the_ball[rec_id] = False
                        ball.speed[1] = 0

                    if players[rec_id].has_lost == 1 and sender_start_new_game == 2:
                        for player in players:
                            player.lives = 3
                            player.score = 0
                            player.has_lost = 0
                        miss_the_ball[rec_id] = True

                    players[rec_id].send_data["another_player"]["id"] = sender_id

                    player_pos = players[rec_id].get_position()
                    players[rec_id].send_data["another_player"]["x"] = player_pos[0]
                    players[rec_id].send_data["another_player"]["y"] = player_pos[1]

                    ball_pos = ball.get_position()
                    players[rec_id].send_data["ball"]["x"] = ball_pos[0]
                    players[rec_id].send_data["ball"]["y"] = ball_pos[1]
                    players[rec_id].send_data["push_ball_mode"] = int(miss_the_ball[rec_id])

                    players[rec_id].send_data["score"]["0"] = players[0].score
                    players[rec_id].send_data["score"]["1"] = players[1].score

                    players[rec_id].send_data["lives"]["0"] = players[0].lives
                    players[rec_id].send_data["lives"]["1"] = players[1].lives

                    players[rec_id].send_data["has_lost"]["0"] = players[0].has_lost
                    players[rec_id].send_data["has_lost"]["1"] = players[1].has_lost

                    json_data = json.dumps(players[rec_id].send_data)

                    conn.send(bytes(json_data, encoding="utf-8"))
                    # print("Sending: " + str(json_data))

                finally:
                    lock.release()
        except socket.error as e:
            print(str(e))

    try:
        lock.acquire()
        connected_players -= 1
        current_id = local_id
    finally:
        lock.release()

    # print("Connection Closed")
    conn.close()


# main
start_new_thread(ball_position, ())
start_new_thread(check_collision, ())


while True:
    conn, addr = s.accept()
    print("Connected to: ", addr)
    start_new_thread(threaded_client, (conn,))
