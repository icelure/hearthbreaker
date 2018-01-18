import curses
import curses.textpad
import sys

import pygame

from hearthbreaker.agents import registry
from hearthbreaker.cards.heroes import hero_for_class
from hearthbreaker.constants import CHARACTER_CLASS
from hearthbreaker.engine import Game, Deck, card_lookup
from hearthbreaker.ui.game_printer import GameRender
from hearthbreaker.cards import *
from hearthbreaker.ui.end_turn_button import End_turn_btn

from pygame.locals import *
from time import time, sleep


def load_deck(filename):
    cards = []
    character_class = CHARACTER_CLASS.MAGE

    with open(filename, "r") as deck_file:
        contents = deck_file.read()
        items = contents.splitlines()
        for line in items[0:]:
            parts = line.split(" ", 1)
            count = int(parts[0])
            for i in range(0, count):
                card = card_lookup(parts[1])
                if card.character_class != CHARACTER_CLASS.ALL:
                    character_class = card.character_class
                cards.append(card)

    if len(cards) > 30:
        pass

    return Deck(cards, hero_for_class(character_class))


def print_usage():
    usage = """usage: python text_runner.py deck1 deck2

       deck1 and deck2 are the decks to be used by the players
       deck1 is for the human player
       deck2 is for the computer

       The decks are a comma separated list of cards, preceded by the
       character class associated with the deck
    """
    print(usage)


def render_game(stdscr):
    class TextAgent:

        def __init__(self, game_window, prompt_window, text_window):
            self.window = prompt_window
            self.game_window = game_window
            self.text_window = text_window
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_CYAN)
            curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_GREEN)

        def do_turn(self, player):
            renderer.draw_game()
            index = 0
            action = self.choose_action()
            while not (action == "quit" or action == "end"):
                if action == "play":
                    card = self.choose_card(player)
                    if card is not None:
                        player.game.play_card(card)
                elif action == "attack":
                    attacker = self.choose_attacker(player)
                    if attacker is not None:
                        attacker.attack()
                elif action == "power":
                    if player.hero.power.can_use():
                        player.hero.power.use()
                index += 1
                renderer.draw_game()
                action = self.choose_action()
            if action == "quit":
                sys.exit(0)

        def choose_action(self):
            self.window.addstr(0, 0, "Choose action")
            actions = ["play", "attack", "power", "end", "quit"]
            index = 0
            selected = 0
            for action in actions:
                if index == selected:
                    color = curses.color_pair(4)
                else:
                    color = curses.color_pair(3)

                self.text_window.addstr(
                    0, index * 10, "{0:^9}".format(action), color)
                index += 1
            self.window.refresh()
            self.text_window.refresh()
            ch = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    selected -= 1
                    if selected < 0:
                        selected = len(actions) - 1
                if ch == curses.KEY_RIGHT:
                    selected += 1
                    if selected == len(actions):
                        selected = 0
                index = 0
                for action in actions:
                    if index == selected:
                        color = curses.color_pair(4)
                    else:
                        color = curses.color_pair(3)

                    self.text_window.addstr(
                        0, index * 10, "{0:^9}".format(action), color)
                    index += 1
                self.window.refresh()
                self.text_window.refresh()
            if ch == 27:
                return None

            return actions[selected]

        def choose_card(self, player):
            filtered_cards = [card for card in filter(
                lambda card: card.can_use(player, player.game), player.hand)]
            if len(filtered_cards) is 0:
                return None
            renderer.targets = filtered_cards
            renderer.selected_target = renderer.targets[0]
            renderer.draw_game()
            self.window.addstr(0, 0, "Choose Card")
            self.window.refresh()
            ch = 0
            index = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()

                if ch == curses.KEY_LEFT:
                    index -= 1
                    if index < 0:
                        index = len(renderer.targets) - 1
                if ch == curses.KEY_RIGHT:
                    index += 1
                    if index == len(renderer.targets):
                        index = 0
                renderer.selected_target = renderer.targets[index]
                renderer.draw_game()
                self.window.addstr(0, 0, "Choose Card")
                self.window.refresh()
            renderer.targets = None
            if ch == 27:
                return None

            return renderer.selected_target

        def choose_attacker(self, player):
            filtered_attackers = [minion for minion in filter(
                lambda minion: minion.can_attack(), player.minions)]
            if player.hero.can_attack():
                filtered_attackers.append(player.hero)
            if len(filtered_attackers) is 0:
                return None
            renderer.targets = filtered_attackers
            renderer.selected_target = renderer.targets[0]
            renderer.draw_game()
            self.window.addstr(0, 0, "Choose attacker")
            self.window.refresh()
            ch = 0
            index = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                self.window.addstr(0, 0, "{0}".format(ch))
                self.window.refresh()
                if ch == curses.KEY_LEFT:
                    index -= 1
                    if index < 0:
                        index = len(renderer.targets) - 1
                if ch == curses.KEY_RIGHT:
                    index += 1
                    if index == len(renderer.targets):
                        index = 0
                renderer.selected_target = renderer.targets[index]
                renderer.draw_game()
                self.window.refresh()
            renderer.targets = None
            if ch == 27:
                return None

            return renderer.selected_target

        def do_card_check(self, cards):

            self.window.addstr(
                0, 0, "Select cards to keep (space selects/deselects a card)")
            keeping = [True, True, True]
            if len(cards) > 3:
                keeping.append(True)
            index = 0
            selected = 0
            for card in cards:
                if keeping[index]:
                    if index == selected:
                        color = curses.color_pair(6)
                    else:
                        color = curses.color_pair(5)
                else:
                    if index == selected:
                        color = curses.color_pair(4)
                    else:
                        color = curses.color_pair(0)

                self.text_window.addstr(
                    0, index * 20, "{0:^19}".format(card.name[:19]), color)
                index += 1
            self.window.refresh()
            self.text_window.refresh()
            ch = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    selected -= 1
                    if selected < 0:
                        selected = len(cards) - 1
                if ch == curses.KEY_RIGHT:
                    selected += 1
                    if selected == len(cards):
                        selected = 0
                if ch == 32:
                    keeping[selected] = not keeping[selected]
                index = 0
                for card in cards:
                    if keeping[index]:
                        if index == selected:
                            color = curses.color_pair(6)
                        else:
                            color = curses.color_pair(5)
                    else:
                        if index == selected:
                            color = curses.color_pair(4)
                        else:
                            color = curses.color_pair(0)

                    self.text_window.addstr(
                        0, index * 20, "{0:^19}".format(card.name[:19]), color)
                    index += 1
                self.window.refresh()
                self.text_window.refresh()
            if ch == 27:
                return None

            return keeping

        def choose_target(self, targets):

            if len(targets) is 0:
                return None
            renderer.targets = targets
            renderer.selected_target = renderer.targets[0]
            renderer.draw_game()
            self.window.addstr(0, 0, "Choose target")
            self.window.refresh()
            ch = 0
            index = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    index -= 1
                    if index < 0:
                        index = len(renderer.targets) - 1
                if ch == curses.KEY_RIGHT:
                    index += 1
                    if index == len(renderer.targets):
                        index = 0
                renderer.selected_target = renderer.targets[index]
                renderer.draw_game()
                self.window.refresh()
            renderer.targets = None
            if ch == 27:
                return None

            return renderer.selected_target

        def choose_index(self, card, player):
            renderer.selection_index = 0
            renderer.draw_game()
            self.window.addstr(0, 0, "Choose placement location")
            self.window.refresh()
            ch = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    renderer.selection_index -= 1
                    if renderer.selection_index < 0:
                        renderer.selection_index = len(player.minions)
                if ch == curses.KEY_RIGHT:
                    renderer.selection_index += 1
                    if renderer.selection_index > len(player.minions):
                        renderer.selection_index = 0
                renderer.draw_game()
                self.window.refresh()
            index = renderer.selection_index
            renderer.selection_index = -1
            if ch == 27:
                return -1

            return index

        def choose_option(self, options, player):
            self.window.addstr(0, 0, "Choose option")
            index = 0
            selected = 0
            for option in options:
                if index == selected:
                    color = curses.color_pair(4)
                else:
                    color = curses.color_pair(3)

                if isinstance(option, Card):
                    self.text_window.addstr(
                        0, index * 20, "{0:^19}".format(option.name[:19]), color)
                else:
                    self.text_window.addstr(
                        0, index * 20, "{0:^19}".format(option.card.name[:19]), color)
                index += 1
            self.window.refresh()
            self.text_window.refresh()
            ch = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    starting_selected = selected
                    selected -= 1
                    if selected < 0:
                        selected = len(options) - 1

                    while not options[selected].can_choose(player) and selected != starting_selected:
                        selected -= 1
                        if selected < 0:
                            selected = len(options) - 1
                if ch == curses.KEY_RIGHT:
                    starting_selected = selected
                    selected += 1
                    if selected == len(options):
                        selected = 0
                    while not options[selected].can_choose(player) and selected != starting_selected:
                        selected += 1
                        if selected == len(options):
                            selected = 0

                index = 0
                for option in options:
                    if index == selected:
                        color = curses.color_pair(4)
                    else:
                        color = curses.color_pair(3)
                    if isinstance(option, Card):
                        self.text_window.addstr(
                            0, index * 20, "{0:^19}".format(option.name[:19]), color)
                    else:
                        self.text_window.addstr(
                            0, index * 20, "{0:^19}".format(option.card.name[:19]), color)
                    index += 1
                self.window.refresh()
                self.text_window.refresh()
            if ch == 27:
                return None

            return options[selected]

    class GraphAgent:

        def __init__(self, game_window, prompt_window, text_window):
            self.window = prompt_window
            self.game_window = game_window
            self.text_window = text_window
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_CYAN)
            curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_GREEN)

        def do_turn(self, player):
            renderer.draw_game()
            index = 0
            action = self.choose_action()
            while not (action == "quit" or action == "end"):
                if action == "play":
                    card = self.choose_card(player)
                    if card is not None:
                        player.game.play_card(card)
                elif action == "attack":
                    attacker = self.choose_attacker(player)
                    if attacker is not None:
                        attacker.attack()
                elif action == "power":
                    if player.hero.power.can_use():
                        player.hero.power.use()
                index += 1
                renderer.draw_game()
                action = self.choose_action()
            if action == "quit":
                sys.exit(0)

        def choose_action(self):
            self.window.addstr(0, 0, "Choose action")
            actions = ["play", "attack", "power", "end", "quit"]
            index = 0
            selected = 0
            for action in actions:
                if index == selected:
                    color = curses.color_pair(4)
                else:
                    color = curses.color_pair(3)

                self.text_window.addstr(
                    0, index * 10, "{0:^9}".format(action), color)
                index += 1
            self.window.refresh()
            self.text_window.refresh()
            ch = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    selected -= 1
                    if selected < 0:
                        selected = len(actions) - 1
                if ch == curses.KEY_RIGHT:
                    selected += 1
                    if selected == len(actions):
                        selected = 0
                index = 0
                for action in actions:
                    if index == selected:
                        color = curses.color_pair(4)
                    else:
                        color = curses.color_pair(3)

                    self.text_window.addstr(
                        0, index * 10, "{0:^9}".format(action), color)
                    index += 1
                self.window.refresh()
                self.text_window.refresh()
            if ch == 27:
                return None

            return actions[selected]

        def choose_card(self, player):
            filtered_cards = [card for card in filter(
                lambda card: card.can_use(player, player.game), player.hand)]
            if len(filtered_cards) is 0:
                return None
            renderer.targets = filtered_cards
            renderer.selected_target = renderer.targets[0]
            renderer.draw_game()
            self.window.addstr(0, 0, "Choose Card")
            self.window.refresh()
            ch = 0
            index = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()

                if ch == curses.KEY_LEFT:
                    index -= 1
                    if index < 0:
                        index = len(renderer.targets) - 1
                if ch == curses.KEY_RIGHT:
                    index += 1
                    if index == len(renderer.targets):
                        index = 0
                renderer.selected_target = renderer.targets[index]
                renderer.draw_game()
                self.window.addstr(0, 0, "Choose Card")
                self.window.refresh()
            renderer.targets = None
            if ch == 27:
                return None

            return renderer.selected_target

        def choose_attacker(self, player):
            filtered_attackers = [minion for minion in filter(
                lambda minion: minion.can_attack(), player.minions)]
            if player.hero.can_attack():
                filtered_attackers.append(player.hero)
            if len(filtered_attackers) is 0:
                return None
            renderer.targets = filtered_attackers
            renderer.selected_target = renderer.targets[0]
            renderer.draw_game()
            self.window.addstr(0, 0, "Choose attacker")
            self.window.refresh()
            ch = 0
            index = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                self.window.addstr(0, 0, "{0}".format(ch))
                self.window.refresh()
                if ch == curses.KEY_LEFT:
                    index -= 1
                    if index < 0:
                        index = len(renderer.targets) - 1
                if ch == curses.KEY_RIGHT:
                    index += 1
                    if index == len(renderer.targets):
                        index = 0
                renderer.selected_target = renderer.targets[index]
                renderer.draw_game()
                self.window.refresh()
            renderer.targets = None
            if ch == 27:
                return None

            return renderer.selected_target

        def do_card_check(self, cards):

            self.window.addstr(
                0, 0, "Select cards to keep (space selects/deselects a card)")
            keeping = [True, True, True]
            if len(cards) > 3:
                keeping.append(True)
            index = 0
            selected = 0
            for card in cards:
                if keeping[index]:
                    if index == selected:
                        color = curses.color_pair(6)
                    else:
                        color = curses.color_pair(5)
                else:
                    if index == selected:
                        color = curses.color_pair(4)
                    else:
                        color = curses.color_pair(0)

                self.text_window.addstr(
                    0, index * 20, "{0:^19}".format(card.name[:19]), color)
                index += 1
            self.window.refresh()
            self.text_window.refresh()
            ch = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    selected -= 1
                    if selected < 0:
                        selected = len(cards) - 1
                if ch == curses.KEY_RIGHT:
                    selected += 1
                    if selected == len(cards):
                        selected = 0
                if ch == 32:
                    keeping[selected] = not keeping[selected]
                index = 0
                for card in cards:
                    if keeping[index]:
                        if index == selected:
                            color = curses.color_pair(6)
                        else:
                            color = curses.color_pair(5)
                    else:
                        if index == selected:
                            color = curses.color_pair(4)
                        else:
                            color = curses.color_pair(0)

                    self.text_window.addstr(
                        0, index * 20, "{0:^19}".format(card.name[:19]), color)
                    index += 1
                self.window.refresh()
                self.text_window.refresh()
            if ch == 27:
                return None

            return keeping

        def choose_target(self, targets):

            if len(targets) is 0:
                return None
            renderer.targets = targets
            renderer.selected_target = renderer.targets[0]
            renderer.draw_game()
            self.window.addstr(0, 0, "Choose target")
            self.window.refresh()
            ch = 0
            index = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    index -= 1
                    if index < 0:
                        index = len(renderer.targets) - 1
                if ch == curses.KEY_RIGHT:
                    index += 1
                    if index == len(renderer.targets):
                        index = 0
                renderer.selected_target = renderer.targets[index]
                renderer.draw_game()
                self.window.refresh()
            renderer.targets = None
            if ch == 27:
                return None

            return renderer.selected_target

        def choose_index(self, card, player):
            renderer.selection_index = 0
            renderer.draw_game()
            self.window.addstr(0, 0, "Choose placement location")
            self.window.refresh()
            ch = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    renderer.selection_index -= 1
                    if renderer.selection_index < 0:
                        renderer.selection_index = len(player.minions)
                if ch == curses.KEY_RIGHT:
                    renderer.selection_index += 1
                    if renderer.selection_index > len(player.minions):
                        renderer.selection_index = 0
                renderer.draw_game()
                self.window.refresh()
            index = renderer.selection_index
            renderer.selection_index = -1
            if ch == 27:
                return -1

            return index

        def choose_option(self, options, player):
            self.window.addstr(0, 0, "Choose option")
            index = 0
            selected = 0
            for option in options:
                if index == selected:
                    color = curses.color_pair(4)
                else:
                    color = curses.color_pair(3)

                if isinstance(option, Card):
                    self.text_window.addstr(
                        0, index * 20, "{0:^19}".format(option.name[:19]), color)
                else:
                    self.text_window.addstr(
                        0, index * 20, "{0:^19}".format(option.card.name[:19]), color)
                index += 1
            self.window.refresh()
            self.text_window.refresh()
            ch = 0
            while ch != 10 and ch != 27:
                ch = self.game_window.getch()
                if ch == curses.KEY_LEFT:
                    starting_selected = selected
                    selected -= 1
                    if selected < 0:
                        selected = len(options) - 1

                    while not options[selected].can_choose(player) and selected != starting_selected:
                        selected -= 1
                        if selected < 0:
                            selected = len(options) - 1
                if ch == curses.KEY_RIGHT:
                    starting_selected = selected
                    selected += 1
                    if selected == len(options):
                        selected = 0
                    while not options[selected].can_choose(player) and selected != starting_selected:
                        selected += 1
                        if selected == len(options):
                            selected = 0

                index = 0
                for option in options:
                    if index == selected:
                        color = curses.color_pair(4)
                    else:
                        color = curses.color_pair(3)
                    if isinstance(option, Card):
                        self.text_window.addstr(
                            0, index * 20, "{0:^19}".format(option.name[:19]), color)
                    else:
                        self.text_window.addstr(
                            0, index * 20, "{0:^19}".format(option.card.name[:19]), color)
                    index += 1
                self.window.refresh()
                self.text_window.refresh()
            if ch == 27:
                return None

            return options[selected]

    def show_text(screen, position, text, color, font_bold=False,
                  font_size=13, font_italic=False):
        cur_font = pygame.font.SysFont("Monaco", font_size)

        cur_font.set_bold(font_bold)
        cur_font.set_italic(font_italic)
        text_fmt = cur_font.render(text, 1, color)
        screen.blit(text_fmt, position)

    def choose_agent(window):
        agents = registry.get_names()
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
        window.addstr(10, 34, "Choose agent")
        ch = 0
        selected = 0
        while ch != 10 and ch != 27:
            index = 0
            for agent in agents:
                if index == selected:
                    color = curses.color_pair(3)
                else:
                    color = curses.color_pair(0)
                window.addstr(index + 11, 25, "{:^30}".format(agent), color)
                index += 1

            window.refresh()
            ch = window.getch()
            if ch == curses.KEY_UP:
                selected -= 1
                if selected < 0:
                    selected = len(agents) - 1
            if ch == curses.KEY_DOWN:
                selected += 1
                if selected == len(agents):
                    selected = 0

        window.clear()
        if ch == 27:
            sys.exit(0)
        else:
            return registry.create_agent(agents[selected])

    stdscr.clear()

    pygame.init()
    game_window = pygame.display.set_mode((1366, 768), 0, 32)
    background = pygame.image.load('background.jpg').convert()
    o_field = pygame.image.load('field.png').convert()
    end_turn_btn = End_turn_btn(game_window, None, None, (1200, 370))

    field_size = width, height = 840, 240
    pygame.mouse.set_cursor(*pygame.cursors.tri_left)

    prompt_window = stdscr.derwin(1, 80, 23, 0)
    text_window = stdscr.derwin(1, 80, 24, 0)

    agent = registry.create_agent(registry.get_names()[0])

    deck1 = load_deck(sys.argv[1])
    deck2 = load_deck(sys.argv[2])
    game = Game([deck1, deck2], [TextAgent(
        stdscr, prompt_window, text_window), agent])
    if game.first_player == 0:
        renderer = GameRender(stdscr, game, game.players[0])
        pass
    else:
        renderer = GameRender(stdscr, game, game.players[1])
        pass
    current_player = game.players[1]
    game.pre_game()
    while(True):
        pygame.time.Clock().tick(40)
        for event in pygame.event.get():
            if event.type == QUIT:
                exit()
            if event.type == pygame.MOUSEMOTION:
                pass
            if event.type == pygame.MOUSEBUTTONDOWN:
                if end_turn_btn.isOver():
                    end_turn_btn.status = 'hover'
                pass
            if event.type == pygame.MOUSEBUTTONUP:
                if end_turn_btn.isOver():
                    if end_turn_btn.status == 'hover':
                        game._end_turn()
                        end_turn_btn.status = 'unclicked'
                else:
                    end_turn_btn.status = 'unclicked'
                    pass
            #TODO: Render tables
            game_window.blit(background, (0, 0))
            #opponent's field
            game_window.blit(o_field, ((1366 - 880) / 2, 768 / 2 - height - 1))
            #my field
            game_window.blit(o_field, ((1366 - 880) / 2, 768 / 2 + 1))

            end_turn_btn.render()
            show_text(game_window, (end_turn_btn.position),end_turn_btn.status,(150,150,150))

            #TODO: Capture mouse status and generate action

            pygame.display.update()
            #刷新一下画面

    # self.pre_game()
    # self.current_player = self.players[1]
    # while not self.game_ended:
    # self.play_single_turn()
    game.start()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print_usage()
        sys.exit()
    curses.wrapper(render_game)
