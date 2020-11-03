# Dots and boxes

import copy
import sys
import time
import pygame


class Game:
    LINES = None
    COLUMNS = None
    MIN = None
    MAX = None
    VAR = 2

    def __init__(self, board=None, score_min=0, score_max=0):
        """ Initializes the Game class.

        :param board: starting board
        :param score_min: MIN player score
        :param score_max: MAX player score

        Board configuration: tuple matrix with the segment encoding of a box on the first position (from the most
            significant bit, to the most insignificant, the positions are: up, right, down, left) and the symbol of the
            player that owns the box on the second position (' ' if no one owns it yet)

        Example: [
                    [(0100,' '), (1111, 'X'), (0001,' ')]
                    [(0,' '),    (1000,' '),  (0,' ')]
                ]

        Last_segment configuration: (line, column, player)
        """
        self.filled_box = False
        self.last_segment = (None, None, None)
        self.score_min = score_min
        self.score_max = score_max

        if board is not None:
            self.board = board
        else:
            self.board = [[(0, ' ')] * Game.COLUMNS for i in range(Game.LINES)]

    def __str__(self):
        """ Displays the Game class as string.

        :return: the Game class as string
        """
        sir = ''

        for i in range(Game.LINES):
            for j in range(Game.COLUMNS):
                sir += '*-' if self.board[i][j][0] & 8 else '* '
            sir += '*\n'

            for j in range(Game.COLUMNS):
                sir += '|' if self.board[i][j][0] & 1 else ' '
                sir += self.board[i][j][1]
            sir += ('|' if self.board[i][Game.COLUMNS - 1][0] & 4 else ' ') + '\n'

        for j in range(Game.COLUMNS):
            sir += '*-' if self.board[Game.LINES - 1][j][0] & 2 else '* '
        sir += '*'

        return sir

    def moves(self, player):
        """ Generates the next game moves.

        Navigates the positions from the game board and adds a segment to a valid free position.

        :param player: current player
        :return: next possible moves
        """
        moves = []

        for i in range(Game.LINES):
            for j in range(Game.COLUMNS):
                moves.append(add_segment(copy.deepcopy(self), (8, -1, 0, 2), i, j, player))
                moves.append(add_segment(copy.deepcopy(self), (1, 0, -1, 4), i, j, player))
            moves.append(add_segment(copy.deepcopy(self), (4, 0, 1, 1), i, Game.COLUMNS - 1, player))

        for j in range(Game.COLUMNS):
            moves.append(add_segment(copy.deepcopy(self), (2, 1, 0, 8), Game.LINES - 1, j, player))

        return moves

    def open_boxes(self, player):
        """ Calculates the score depending on the chosen variant.

        :param player: current player
        :return: player's maximum possible game score
        """
        if Game.VAR == 1:
            return self.open_boxes_1(player)

        else:
            return self.open_boxes_2(player)

    def open_boxes_1(self, player):
        """ Calculates how many boxes the current player can close.

        A player's score is equal to the number of boxes it already has plus the number of open boxes. This is a foolish
            approach of estimation.

        :param player: current player
        :return: player's score
        """
        if player == self.MIN:
            return self.LINES * self.COLUMNS - self.score_max

        else:
            return self.LINES * self.COLUMNS - self.score_min

    def open_boxes_2(self, player):
        """ Calculates how many boxes the current player can close.

        A player's score is equal to the number of boxes it already has and the number of boxes it can close next,
            before the opponent's turn starts. In this case it is preferred that the last segment used would be the
            third edge of an existing box. This estimate gets very close to the real score.

        :param player: current player
        :return: player's score
        """
        game = copy.deepcopy(self)

        if player == self.MIN:
            score = self.score_min
        else:
            score = self.score_max

        count = int((game.last_segment[2] == player and game.filled_box) or
                    (game.last_segment[2] != player and not game.filled_box))

        while count == 1:
            count = 0
            score += 1

            for d in [(8, -1, 0, 2), (1, 0, -1, 4), (4, 0, 1, 1), (2, 1, 0, 8)]:
                current_game = add_segment(game, d, game.last_segment[0], game.last_segment[1], player)
                if current_game is not None:
                    count += 1

        return score

    def estimate_score(self):
        """ Estimates the game score.

        If the state is final, returns an extreme value corresponding to the winner (or 0 if it's a tie). Otherwise, it
            estimates the current state score as the difference between the score for MAX and the score for MIN,
            calculated with the function open_boxes(player).

        :return: score
        """
        final = self.final()

        if final == Game.MAX:
            return 100000

        elif final == Game.MIN:
            return -100000

        elif final == 'tie':
            return 0

        else:
            return self.open_boxes(Game.MAX) - self.open_boxes(Game.MIN)

    def final(self):
        """ Tests whether the current state is final and finds the winner if it is.

        :return: 'False' if the state is not final, winner if it is
        """
        if self.score_min + self.score_max != self.LINES * self.COLUMNS:
            return False

        if self.score_min == self.score_max:
            return 'tie'

        if self.score_min > self.score_max:
            return self.MIN

        return self.MAX


class State:
    def __init__(self, game, current_player, depth, score=None):
        """ Initializes the State class.

        :param game: current game
        :param current_player: current player
        :param depth: current depth
        :param score: current score
        """
        self.game = game
        self.current_player = current_player
        self.depth = depth
        self.score = score
        self.possible_moves = []
        self.next_state = None

    def __str__(self):
        """ Displays the State class as string.

        :return: the State class as a string.
        """
        return str(self.game)

    def next_player(self):
        """ Finds which player's turn is next.

        :return: next player
        """
        return Game.MAX if (self.current_player == Game.MIN and not self.game.filled_box) or \
                           (self.current_player == Game.MAX and self.game.filled_box) \
            else Game.MIN

    def moves(self):
        """ Generates the next game moves.

        For every possible game move, it adds to the list a State consisting of it, the next player and the new depth.

        :return: next possible moves
        """
        games = self.game.moves(self.current_player)
        moves = []

        for game in games:
            if game is not None:
                moves.append(State(game,
                                   self.next_player() if not game.filled_box else self.current_player,
                                   self.depth - 1))

        return moves


class Graphics:
    def __init__(self):
        self.screen = None
        self.box_length = 50
        self.screen_width = (2 * Game.COLUMNS + 1) * self.box_length
        self.screen_height = (2 * Game.LINES + 1) * self.box_length

        self.line_image = pygame.image.load('line.png')
        self.dot_image = pygame.image.load('dot.png')
        self.x_image = pygame.image.load('x.png')
        self.o_image = pygame.image.load('o.png')

        self.horizontal_line = pygame.transform.scale(self.line_image, (self.box_length, self.box_length))
        self.vertical_line = pygame.transform.rotate(self.horizontal_line, 90)
        self.dot = pygame.transform.scale(self.dot_image, (self.box_length, self.box_length))
        self.x = pygame.transform.scale(self.x_image, (self.box_length, self.box_length))
        self.o = pygame.transform.scale(self.o_image, (self.box_length, self.box_length))


def add_segment(game, d, i, j, player):
    """ Adds a new segment to the game board, if the position is valid.

    :param game: current game
    :param d: tuple with current direction
    :param i: current position line index
    :param j: current position column index
    :param player: current player
    :return: the updated game
    """
    if not game.board[i][j][0] & d[0]:
        game = complete_box(game, d[0], i, j, player)

        if in_scope(i + d[1], j + d[2]):
            game = complete_box(game, d[3], i + d[1], j + d[2], player)

        return game


def complete_box(game, d, i, j, player):
    """ Adds a new segment to the game board.

    If, with that segment, a box closes, updates the game details accordingly.

    :param game: current game
    :param d: direction code
    :param i: current position line index
    :param j: current position column index
    :param player: current player
    :return: the updated game
    """
    game.board[i][j] = (int(game.board[i][j][0] + d), game.board[i][j][1])
    game.last_segment = (i, j, player)

    if game.board[i][j][0] & 15 == 15:
        game.filled_box = True
        game.board[i][j] = (game.board[i][j][0], player)

        if player == Game.MIN:
            game.score_min += 1
        else:
            game.score_max += 1

    return game


def in_scope(i, j):
    """ Checks whether the position with the given indexes is on the board.

    :param i: line index
    :param j: column index
    :return: 'True' if the position is on the board, 'False' otherwise
    """
    return 0 <= i < Game.LINES and 0 <= j < Game.COLUMNS


def min_max(state):
    """ Minimax Algorithm.

    :param state: current state
    :return: the updated state
    """
    if state.depth == 0 or state.game.final():
        state.score = state.game.estimate_score()

        return state

    state.possible_moves = state.moves()
    moves_score = [min_max(x) for x in state.possible_moves]

    if state.current_player == Game.MAX:
        state.next_state = max(moves_score, key=lambda x: x.score)
    else:
        state.next_state = min(moves_score, key=lambda x: x.score)

    state.score = state.next_state.score

    return state


def alpha_beta_state(alpha, beta, state):
    """ Calculates the next state of the algorithm.

    :param alpha: lower score range limit
    :param beta: upper score range limit
    :param state: current state
    :return: the updated state
    """
    current_score = float('-inf') if state.current_player == Game.MAX else float('inf')

    for move in state.possible_moves:
        new_state = alpha_beta(alpha, beta, move)

        if state.current_player == Game.MAX:
            alpha = min(alpha, new_state.score)

            if current_score < new_state.score:
                state.next_state = new_state
                current_score = new_state.score
        else:
            beta = max(beta, new_state.score)

            if current_score > new_state.score:
                state.next_state = new_state
                current_score = new_state.score

        if alpha >= beta:
            break

    return state


def alpha_beta(alpha, beta, state):
    """ Alpha-Beta Algorithm.

    :param alpha: lower score range limit
    :param beta: upper score range limit
    :param state: current state
    :return: the updated state
    """
    if state.depth == 0 or state.game.final():
        state.score = state.game.estimate_score()

        return state

    if alpha > beta:
        return state

    state.possible_moves = state.moves()
    state = alpha_beta_state(alpha, beta, state)
    state.score = state.next_state.score

    return state


def read_algorithm():
    """ Gets the player's input on which algorithm the computer will use for the current game.

    :return: algorithm code
    """
    while True:
        algorithm_type = input("Opponent's algorithm? (answer with 1 or 2)\n 1.Minimax\n 2.Alpha-beta\n ")

        if algorithm_type in ['1', '2']:
            break

        print("The answer must be 1 or 2.")

    return algorithm_type


def read_symbol():
    """ Gets the player's input on which symbol he/she will use for the current game.

    :return: None
    """
    while True:
        Game.MIN = input("Do you want to play with X or with O? (X starts the game)\n ").upper()

        if Game.MIN in ['X', 'O']:
            break

        print("The answer must be X or O.")

    Game.MAX = 'O' if Game.MIN == 'X' else 'X'


def read_difficulty():
    """ Gets the player's input on the preferred difficulty.

    :return: difficulty code
    """
    while True:
        difficulty = input("Choose the difficulty level (answer with 1, 2 or 3):\n "
                           "1.Easy\n 2.Medium\n 3.Hard\n")

        if difficulty in ['1', '2', '3']:
            break

        print("The answer must be 1, 2 or 3.")

    return int(difficulty)


def read_lines_and_columns():
    """ Gets the player's input on the number of lines and the number of columns of the game board.

    :return: None
    """
    while True:
        try:
            lines = int(input("Enter the number of dots on one line: \n"))
            columns = int(input("Enter the number of dots on one column: \n"))

            if lines < 2 or columns < 2:
                print("The game must have minimum 2 lines and 2 columns.")
            elif lines > 8 or columns > 8:
                print("The game must have maximum 8 lines and 8 columns.")
            else:
                Game.LINES = lines - 1
                Game.COLUMNS = columns - 1
                break

        except ValueError:
            print("The entered values must be integers.")


def read_game_type():
    """ Gets the player's input on whether he/she would like to use the graphical interface

    :return: game type
    """
    while True:
        game_type = input("Would you like to use the graphical interface? (answer with 'yes' or 'no')\n")

        if game_type in ['yes', 'no']:
            break

        print("The answer must be 'yes' or 'no'.")

    return game_type == 'yes'


def find_relative_position(line, column, board):
    """ Checks whether the given position represents a horizontal line, a vertical line or a non-valid line.
    
    :param line: line index
    :param column: column index
    :param board: current game board
    :return: the type of line
    """
    if line == 2 * Game.LINES:
        if not board[line // 2 - 1][column // 2][0] & 2:
            return 'horizontal'

    elif line % 2 == 0:
        if not board[line // 2][column // 2][0] & 8:
            return 'horizontal'

    elif column == 2 * Game.COLUMNS:
        if not board[line // 2][column // 2 - 1][0] & 4:
            return 'vertical'

    else:
        if not board[line // 2][column // 2][0] & 1:
            return 'vertical'

    return 'non-valid'


def check_position(line, column, state):
    """ Checks the validity of the player's move.

    :param line: line index
    :param column: column index
    :param state: current state
    :return: whether the move would be valid or not.
    """
    if line in range(2 * Game.LINES + 1) and column in range(2 * Game.COLUMNS + 1) and (line + column) % 2 == 1:
        direction = find_relative_position(line, column, state.game.board)
        line //= 2
        column //= 2

        if direction == 'horizontal':
            if in_scope(line, column):
                state.game = complete_box(state.game, 8, line, column, Game.MIN)
            if in_scope(line - 1, column):
                state.game = complete_box(state.game, 2, line - 1, column, Game.MIN)

            return True

        elif direction == 'vertical':
            if in_scope(line, column):
                state.game = complete_box(state.game, 1, line, column, Game.MIN)
            if in_scope(line, column - 1):
                state.game = complete_box(state.game, 4, line, column - 1, Game.MIN)

            return True

        else:
            print("There is a symbol on the given position already.")
    else:
        print("Non-valid line or column.")

    return False


def player_turn_graphic(state, boxes):
    """ Shows the player's move on the graphical interface.

    :param state: current state
    :param boxes: the batch of boxes from the graphical interface
    :return: None
    """
    played = False

    while not played:
        for current_event in pygame.event.get():
            if current_event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if current_event.type == pygame.MOUSEBUTTONDOWN:
                position = pygame.mouse.get_pos()

                for line in range(2 * Game.LINES + 1):
                    for column in range(2 * Game.COLUMNS + 1):
                        if boxes[line][column].collidepoint(position) and line % 2 != column % 2:
                            played = check_position(line, column, state)


def player_turn(state):
    """ Executes the player's move. Checks whether he/she wants to continue the game or not.

    :param state: current state
    :return: the updated state if the player wants to continue playing, None otherwise
    """
    print("Which dots would you like to connect?")
    valid = False

    while not valid:
        try:
            line = int(input("line = "))
            if line == -1:
                return None

            column = int(input("column = "))
            if column == -1:
                return None

            valid = check_position(line, column, state)

        except ValueError:
            print("The line and column must be integers.")

    return state


def computer_turn(state, algorithm_type):
    """ Executes the computer's move.

    :param state: current state
    :param algorithm_type: code corresponding to the algorithm chosen by the player
    :return: the updated state
    """
    if algorithm_type == '1':
        state.game = min_max(state).next_state.game
    else:
        state.game = alpha_beta(-5000, 5000, state).next_state.game

    return state


def print_if_final(state):
    """ Checks whether the state is final; if it is, prints the winner.

    :param state: current state
    :return: whether the state is final or not
    """
    final = state.game.final()

    if not final:
        return False

    if final == "tie":
        print("It's a tie!")
    else:
        print(final + " won!")

    return True


def run_algorithm(algorithm_type, state, player_moves, computer_moves, game_type, boxes, graphics):
    """ Alternatively executes the player's and the computer's turns.

    :param algorithm_type: code corresponding to the algorithm chosen by the player
    :param state: current state
    :param player_moves: how many moves the player had so far
    :param computer_moves: how many moves the computer had so far
    :param game_type: whether the game is shown on the graphical interface or not
    :param boxes: the batch of boxes from the graphical interface
    :param graphics: constants specific to the graphical interface
    :return: the number of player moves, the number of computer moves
    """
    final = False

    while not final:
        turn_start_time = int(round(time.time() * 1000))

        if state.current_player == Game.MIN:
            print("Player's turn:")
            player_moves += 1

            if game_type:
                player_turn_graphic(state, boxes)
            else:
                state = player_turn(state)

                if state is None:
                    break
        else:
            print("Computer's turn:")
            computer_moves += 1
            state = computer_turn(state, algorithm_type)

        turn_end_time = int(round(time.time() * 1000))
        boxes = display_game_board(state.game.board, graphics)
        print("\nThe board after the move:\n" + str(state))
        print("Thinking time: " + str(turn_end_time - turn_start_time) + " milliseconds.\n")

        final = print_if_final(state)
        state.current_player = state.next_player()
        state.game.filled_box = False

    return player_moves, computer_moves


def display_box(board, graphics, line, column):
    """ Displays the inside of a box.

    :param board: current game board
    :param graphics: constants specific to the graphical interface
    :param line: current box line index
    :param column: current box column index
    :return: None
    """
    if line % 2 == 0 and column % 2 == 0:
        graphics.screen.blit(graphics.dot, (column * graphics.box_length, line * graphics.box_length))
    elif line % 2 == 0 and (line == 2 * Game.LINES and board[line // 2 - 1][column // 2][0] & 2 or
                            line != 2 * Game.LINES and board[line // 2][column // 2][0] & 8):
        graphics.screen.blit(graphics.horizontal_line, (column * graphics.box_length, line * graphics.box_length))
    elif column % 2 == 0 and (column == 2 * Game.COLUMNS and board[line // 2][column // 2 - 1][0] & 4 or
                              column != 2 * Game.COLUMNS and board[line // 2][column // 2][0] & 1):
        graphics.screen.blit(graphics.vertical_line, (column * graphics.box_length, line * graphics.box_length))
    elif line % 2 == column % 2 == 1 and board[line // 2][column // 2][1] == 'X':
        graphics.screen.blit(graphics.x, (column * graphics.box_length, line * graphics.box_length))
    elif line % 2 == column % 2 == 1 and board[line // 2][column // 2][1] == 'O':
        graphics.screen.blit(graphics.o, (column * graphics.box_length, line * graphics.box_length))


def display_game_board(board, graphics):
    """ Displays the current game board.

    :param board: current game board
    :param graphics: constants specific to the graphical interface
    :return: the batch of boxes used for the graphical interface
    """
    boxes = []
    graphics.screen.fill((255, 255, 255))

    for line in range(2 * Game.LINES + 1):
        box_line = []

        for column in range(2 * Game.COLUMNS + 1):
            area = pygame.Rect(column * (graphics.box_length + 1),
                               line * (graphics.box_length + 1),
                               graphics.box_length,
                               graphics.box_length)
            box_line.append(area)
            pygame.draw.rect(graphics.screen, (255, 255, 255), area)
            display_box(board, graphics, line, column)

        boxes.append(box_line)

    pygame.display.flip()

    return boxes


def init_graphics(state):
    """ Initializes the necessary constants for the game.

    :param state: current state
    :return: the batch of boxes used for the graphical interface, the constants specific to the graphical interface
    """
    pygame.init()
    pygame.display.set_caption('Dots and Boxes')
    graphics = Graphics()
    graphics.screen = pygame.display.set_mode((graphics.screen_width, graphics.screen_height))
    boxes = display_game_board(state.game.board, graphics)
    print("\nInitial game board:\n" + str(state.game))

    return boxes, graphics


def main():
    """ Main function. Reads necessary constants for the current game, starts the game and shows the final statistics.

    :return: None
    """
    print("After the game has started, enter '-1' during your turn if you want to stop before finishing the game.\n")

    algorithm_type = read_algorithm()
    read_symbol()
    max_depth = read_difficulty()
    read_lines_and_columns()
    game_type = read_game_type()
    state = State(Game(), 'X', max_depth)
    boxes, graphics = init_graphics(state)
    player_moves = 0
    computer_moves = 0

    game_start_time = int(round(time.time() * 1000))
    player_moves, computer_moves = \
        run_algorithm(algorithm_type, state, player_moves, computer_moves, game_type, boxes, graphics)
    game_end_time = int(round(time.time() * 1000))

    print("\nTotal play time: " + str(game_end_time - game_start_time) + " milliseconds.\n")
    print("Player moves: " + str(player_moves) + "\nComputer moves: " + str(computer_moves))
    print("\nPlayer score: " + str(state.game.score_min) +
          "\nComputer score: " + str(state.game.score_max))


if __name__ == "__main__":
    main()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
