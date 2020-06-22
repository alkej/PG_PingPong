screen_size = (800, 600)

screen_center = (400, 300)

ball_size = (35, 35)
ball_pos_init = [int(screen_center[0] - ball_size[0]/2), int(screen_center[1] - ball_size[1]/2)]
max_speed = [5, 3]

pad_size = (20, 125)

pad_top = 362.5  # (screen_size[1] + pad_size[1])/2
pad_indent = 10  # pad_size[0] / 2

players_pos = ((10, 362), (770, 362))

lives_num = 3

colors = {'white':          [255, 255, 255],
          'black':          [0, 0, 0],
          'living coral':   [255, 111, 97],
          'greenery':       [136, 176, 75],
          'rose quartz':    [247, 202, 201]}


port = 9091
