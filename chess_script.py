import chess
import chess.svg
import chess.pgn
import asyncio
from pyodide.http import open_url
from js import console

import js
from js import document
from pyodide import create_proxy


async def get_square(event):
    global board
    piece = js.get_object()
    if len(piece) > 0:
        pyscript.write('move', f'Focused on piece: {piece}')
        draw(board, focus=piece)


def draw(board, draw_text=False, focus=False):
    fill = {}
    if focus:
        fill = dict.fromkeys(board.attacks(chess.parse_square(focus)), "#ff0000aa") | {chess.parse_square(focus): "#fdda0dff"}
    if not draw_text:
        b_svg = chess.svg.board(
            board=board,
            fill=fill,
            colors={'margin':'#30ac10'},
            size=700)
        pyscript.write('svg', b_svg)
    else:
        pyscript.write('svg', '')
        pyscript.write('text', '')
        for row in str(board).split('\n'):
            pyscript.write('text', row, append=True)

async def toggle_button():
     current = document.querySelector('#mainbutton').innerHTML
     
     if current == 'Watch':
         new_value = 'Pause'
     else:
         new_value = 'Watch'
     document.querySelector('#mainbutton').innerHTML = new_value


async def watch(*args, **kwargs):
    global board
    global started
    global current_game
    global moves

    await toggle_button()
    if not started:
        started = True
        while started:
            try:
                move = next(moves)
                # if not started:
                #     break # stop playing automatically
                board.push(move)
                # reverse of what you might expect ...
                white_turn = board.turn == chess.BLACK
                if white_turn:
                    turn = 'White'
                else:
                    turn = 'Black'
                try:
                    mv = current_game.board().san(move)
                except:
                    mv = "&nbsp;"
                    console.log('UCI of problem move: ' + move.uci())
                pyscript.write('move', turn + "'s move: " + mv)
                draw(board)
                await asyncio.sleep(3)
            except StopIteration:
                pyscript.write('move', 'End of game')
                await asyncio.sleep(10)
                started = False
                await toggle_button()
                await _new_game(None)
    else:
        started = False

def load_games(pgn_location = "/kasparov-deep-blue-1997.pgn"):
    pgn = open_url(pgn_location)
    offsets = []
    games = []
    while True:
        offset = pgn.tell()
        headers = chess.pgn.read_headers(pgn)
        if headers is None:
            break
        offsets.append(offset)
        games.append(headers.get("Site", "") + " - White: " + headers.get("White", "")+ " | Black: " + headers.get("Black", ""))
    #print(f'There are {len(offsets)} games, with offsets of: {offsets}')
    return pgn, offsets, games

def populate_dropdown(item_list, select_id):
    document.querySelector(select_id).length = 0
    for idx, item in enumerate(item_list):
        item_option = document.createElement("option")
        item_option.value = idx
        item_option.text = item
        document.querySelector(select_id).add(item_option, None)


async def _new_game(event):
    global current_game
    global board
    global moves

    console.log('New game')
    gameId = int(document.querySelector('#gameselect').value)

    pgn.seek(offsets[gameId])
    current_game = chess.pgn.read_game(pgn)
    board = current_game.board()
    draw(board)

    title = current_game.headers["Event"] + " - " + current_game.headers["Site"]
    pyscript.write('title', title)

    players = "White: " + current_game.headers["White"] + " | Black: " + current_game.headers["Black"]
    pyscript.write('players', players)

    pyscript.write('move', '&nbsp;')

    moves = iter(current_game.mainline_moves())


async def _new_match(event):
    global pgn
    global offsets
    global games
    console.log('New match')
    fileId = int(document.querySelector('#fileselect').value)
    pgn, offsets, games = load_games(files[fileId])
    populate_dropdown(games, '#gameselect')
    await _new_game(None)

new_game = create_proxy(_new_game)
document.querySelector("#gameselect").addEventListener("change", new_game)

new_match = create_proxy(_new_match)
document.querySelector("#fileselect").addEventListener("change", new_match)

click_proxy = create_proxy(get_square)
# TODO: see if this can be made more specific ???? (I think maybe just within SVG???)
document.addEventListener("click", click_proxy)

started = False
board = chess.Board()
draw(board)

matches = ["Spassky | Bronstein 1960", "Fischer | Larsen 1971", "Kasparov | Deep Blue 1997"]
files = ["/spassky_bronstein_1960.pgn", "/fischer_larsen_1971.pgn", "/kasparov-deep-blue-1997.pgn"]
populate_dropdown(matches, '#fileselect')
await _new_match(None)
