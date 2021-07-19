from application import app, models, db, socketio
from flask import render_template, request, url_for, redirect, jsonify
from application.forms import StartGameForm
from flask_socketio import join_room, leave_room
import itertools, random

@app.route("/")
@app.route("/index")
@app.route("/index/<msg>")
def index(msg=''):
	form = StartGameForm()
	return render_template("index.html", form=form, msg=msg)

@app.route('/game', methods=['POST'])
def game():
	form = StartGameForm(request.form)
	team = models.Team.BLUE
	if form.team.data == models.Team.RED.value:
		team = models.Team.RED
	player = models.Player(name=form.name.data, team=team)
	# joining existing game
	if form.submitJoin.data:
		game = models.Game.query.filter_by(id=form.game_id.data).first()
		if game is None:	#no game found with this name
			return redirect(url_for('index', msg="Room name is invalid - check again"))
		count = 0
		partner = None
		opponents = []
		left_opponent = None
		right_opponent = None
		for p in game.players:
			if form.team.data == p.team.value:
				count = count + 1
			else:
				opponents.append(p)

		if count == 2:	#no seats left in this team
			return redirect(url_for('index', msg="Room already has 2 players in Team "+form.team.data+" - select another team"))
		elif count == 1:	#partner already in game
			for p in game.players:
				if form.team.data == p.team.value:
					player.order = p.order + 2
					partner = p
					break
		else:	#first player in this team
			player.order = 1
		for o in opponents:
			if player.order != 3:
				if o.order < player.order:
					left_opponent = o
				else:
					right_opponent = o
			else:
				if o.order == 2:
					left_opponent = o
				else:
					right_opponent = o
		game.players.insert(player.order, player)
		db.session.commit()

		return render_template("game.html", game=game, player=player, partner=partner, left_opponent=left_opponent, right_opponent=right_opponent)
	# creating new game
	player.order = 0
	game = models.Game(players=[player], red_score=0, blue_score=0)
	db.session.add(player)
	db.session.add(game)
	db.session.commit()
	return render_template("game.html", game=game, player=player)


@socketio.on('join')
def on_join(data):
	game_id = data['game_id']
	player_id = data['player_id']
	game = models.Game.query.filter_by(id=int(data['game_id'])).first()
	player = models.Player.query.filter_by(id=player_id).first()
	join_room(game_id)
	socketio.emit('update_game', {'type':'new_player', 'info': {'player_id': player.id, 'player_order': player.order,
															   'player_name': player.name}, 'status':"New player "+str(player.name)+" joined"}, to=game_id)
	if len(game.players) == 4:
		startGame(game, game_id)


def startGame(game, game_id):
	for p in game.players:
		p.deck.clear()
	db.session.commit()
	temp = models.CardSuite.list()
	temp.remove(models.CardSuite.NOTRUMP.value)
	deck = list(itertools.product(models.CardNumber.list(), temp))
	random.shuffle(deck)
	deal_cards(deck, game)
	player0 = models.Player.query.filter_by(game_id=game.id).filter_by(order=0).first().as_dict()
	player1 = models.Player.query.filter_by(game_id=game.id).filter_by(order=1).first().as_dict()
	player2 = models.Player.query.filter_by(game_id=game.id).filter_by(order=2).first().as_dict()
	player3 = models.Player.query.filter_by(game_id=game.id).filter_by(order=3).first().as_dict()
	socketio.emit('update_game', {'type':'bid_start', 'info':{'player0':player0, 'player1':player1, 'player2':player2, 'player3':player3}, 'status':"Bidding turn - "+player0['name']}, to=game_id)


def deal_cards(deck, game):
	init = 0
	for j in range(2):
		for p in game.players:
			for i in range(4):
				suite = models.CardSuite(deck[init][1])
				number = models.CardNumber.get_by_number(deck[init][0]['number'])
				card = models.Card(player_id=p.id, number=number, suite=suite)
				init = init+1
				p.deck.append(card)
				db.session.commit()


@socketio.on('bid_made')
def on_bid_made(data):
	game_id = data['game_id']
	player_order = data['player_order']
	bid = int(data['bid'])
	game = models.Game.query.filter_by(id=int(game_id)).first()
	next_player_order = -1
	if bid == -1:	#pass
		game.bid_stack.pop(str(player_order))
		db.session.commit()
		try:
			mainBidder = int(list(game.bid_stack)[0])
			print(player_order," passed - stack:",game.bid_stack," mainbidder:",mainBidder)
		except:
			game.bid_stack = {0:-1, 1:-1, 2:-1, 3:-1}
			db.session.commit()
			startGame(game, game_id)
			return True
		if len(game.bid_stack) == 1:	#only one player is left
			if game.bid_stack[str(mainBidder)] == -1:	#remaining player has never made any bid yet
				next_player_order = mainBidder
			else:	#bid is complete
				winner = models.Player.query.filter_by(order=mainBidder, game_id=int(game_id)).first()
				game.bid_winner = winner.team
				game.highest_bid = game.bid_stack[str(mainBidder)]
				db.session.commit()
				double_player = models.Player.query.filter_by(game_id=int(game_id)).filter(models.Player.team!=winner.team).order_by(models.Player.order.asc()).first()
				if game.double == 4:
					player = models.Player.query.filter_by(game_id=int(game_id), order=0).first()
					# socketio.emit("update_game", {'type':'game_start',  'screen':{'player_order':player_order, 'data':"Pass", 'type':'notImage', 'clear':0}, 'status':"Game starts with "+player.name}, to=game_id)
					socketio.emit("update_game",
								  {'type': 'set_trump', 'info': {'bid_winner_order': mainBidder, 'double_set': game.double},
								   'status': player.name + " has passed -- Bid winner setting trump",
								   'screen':{'player_order':player_order, 'data':"Pass", 'type':'notImage', 'clear':0}}, to=game_id)

				else:
					socketio.emit("update_game", {'type':'double', 'screen':{'player_order':player_order, 'data':"Pass", 'type':'notImage', 'clear':0},
											  'info':{'double_player_order':double_player.order, 'bid_winner':winner.name, 'highest_bid':game.highest_bid}, 'status':"Asking for double to "+double_player.name}, to=game_id)
				return True
		elif game.bid_stack[str(mainBidder)] == -1:	#game restart
			next_player_order = mainBidder
		else:	#a bid is won
			next_player_order = list(game.bid_stack)[1]
			game.highest_bid = game.bid_stack[str(mainBidder)]+1
		bid = "Pass"
		print("----next player:", next_player_order," has to bid min:",game.highest_bid)
	else:	#not pass
		game.highest_bid = bid
		game.bid_stack[str(player_order)] = bid
		db.session.commit()
		mainBidder = int(list(game.bid_stack)[0])
		print(player_order," bid ",game.bid_stack[str(player_order)]," - stack:",game.bid_stack," mainbidder:",mainBidder)

		if player_order == mainBidder:
			if len(game.bid_stack) == 1:	#only last player has made a bid - bid is complete
				winner = models.Player.query.filter_by(order=mainBidder, game_id=int(game_id)).first()
				game.bid_winner = winner.team
				game.highest_bid = game.bid_stack[str(mainBidder)]
				db.session.commit()
				double_player = models.Player.query.filter_by(game_id=int(game_id)).filter(
					models.Player.team != winner.team).order_by(models.Player.order.asc()).first()
				if game.double == 4:
					player = models.Player.query.filter_by(game_id=int(game_id), order=0).first()
					socketio.emit("update_game", {'type':'game_start', 'screen': {'player_order': player_order, 'data': game.highest_bid, 'type':'notImage', 'clear':0},'status':"Game starts with "+player.name}, to=game_id)
				else:
					socketio.emit("update_game",
							  {'type': 'double', 'screen': {'player_order': player_order, 'data': game.highest_bid, 'type':'notImage', 'clear':0},
							   'info': {'double_player_order': double_player.order, 'bid_winner': winner.name,
										'highest_bid': game.highest_bid},
							   'status': "Asking for double to " + double_player.name}, to=game_id)
				return True
			game.increment_highest_bid()
			next_player_order = int(list(game.bid_stack)[1])
		else:
			next_player_order = mainBidder
		print("----next player:", next_player_order, " has to bid min:", game.highest_bid)

	db.session.commit()
	next_player = models.Player.query.filter_by(game_id=int(game_id), order=next_player_order).first()
	socketio.emit("update_game", {'type':'bid', 'screen':{'player_order':player_order,  'data':bid, 'type':'notImage', 'clear':0},
								  'info':{'next_player_order':next_player_order,  'data':game.highest_bid}, 'status': "Bidding turn - "+next_player.name}, to=game_id)


@socketio.on('double_made')
def on_double_made(data):
	game_id = data['game_id']
	game = models.Game.query.filter_by(id=int(game_id)).first()
	player_team = data['player_team']
	team = models.Team.BLUE
	if player_team == models.Team.RED.value:
		team = models.Team.RED
	player_order = data['player_order']
	game.increment_double_counter()
	db.session.commit()
	player = models.Player.query.filter_by(game_id=int(game_id), order=player_order).first()

	print(player_team,":",player_order,"; gameDoubleCounter:",game.double_counter)
	if data['double'] == 1:
		game.set_double()
		game.double_counter = 0
		db.session.commit()
		if game.double == 4:
			p = int(list(game.bid_stack)[0])
			print("----doubled; gameDouble:",game.double,"; gameDoubleCounter:",game.double_counter,"; game starts with:",p)
			socketio.emit("update_game", {'type':'set_trump', 'info': {'bid_winner_order': p, 'double_set':game.double}, 'status':player.name+" has doubled -- Bid winner setting trump"}, to=game_id)
		else:
			double_player = models.Player.query.filter_by(game_id=int(game_id)).filter(models.Player.team != team).order_by(models.Player.order.asc()).first()
			print("----doubled; gameDouble:",game.double,"; gameDoubleCounter:",game.double_counter,"; next turn order:",double_player.order)
			socketio.emit("update_game", {'type': 'double', 'info': {'double_player_order': double_player.order, 'double_set':game.double}, 'status':player.name+" has doubled -- asking for double to "+double_player.name}, to=game_id)

	elif data['double'] == 0:
		if game.double_counter == 2:
			game.double_counter = 0
			db.session.commit()
			p = int(list(game.bid_stack)[0])
			print("----passed; gameDouble:", game.double, "; gameDoubleCounter:", game.double_counter,
				  "; game starts with:",p)
			socketio.emit("update_game", {'type': 'set_trump', 'info': {'bid_winner_order': p}, 'status':player.name+" has passed on double -- Bid winner setting trump"}, to=game_id)

		else:
			double_player = models.Player.query.filter_by(game_id=int(game_id),team=team).filter(models.Player.order != player_order).first()
			print("----passed; gameDouble:", game.double, "; gameDoubleCounter:", game.double_counter,
				  "; next turn order:",double_player.order)
			socketio.emit("update_game", {'type':'double', 'info':{'double_player_order':double_player.order}, 'status':player.name+" has passed on double -- asking for double to "+double_player.name}, to=game_id)


@socketio.on('trump_made')
def on_trump_made(data):
	game_id = data['game_id']
	trump = data['trump']
	trump_order = data['trump_order']
	game = models.Game.query.filter_by(id=int(game_id)).first()
	player_24 = models.Player.query.filter_by(game_id=int(game_id)).filter(
		models.Player.team != game.bid_winner).order_by(models.Player.order.asc()).first()
	game.trump_order = trump_order
	if trump == 0:
		game.trump = models.CardSuite.SPADE
	elif trump == 1:
		game.trump = models.CardSuite.HEART
	elif trump == 2:
		game.trump = models.CardSuite.CLUB
	elif trump == 3:
		game.trump = models.CardSuite.DIAMOND
	elif trump == 4:
		game.trump = models.CardSuite.NOTRUMP
	game.double_counter = 0
	db.session.commit()
	if game.aukat_set:
		player0 = models.Player.query.filter_by(game_id=int(game_id), order=0).first()
		socketio.emit("update_game", {'type': 'game_start',  'status':"Game starts with "+player0.name}, to=game_id)
	else:
		socketio.emit("update_game",
				  {'type': 'show_all_cards', 'info': {'player_24_order': player_24.order, 'data': 24}, 'status':"Trump set -- Asking for 24 to "+player_24.name}, to=game_id)


@socketio.on('24_made')
def on_24_made(data):
	game_id = data['game_id']
	game = models.Game.query.filter_by(id=int(game_id)).first()
	player_order = data['player_order']
	player = models.Player.query.filter_by(game_id=int(game_id), order=player_order).first()
	player_24_partner = models.Player.query.filter_by(game_id=int(game_id)).filter(
		models.Player.team != game.bid_winner).filter(models.Player.order != player_order).first()
	if data['aukat'] == 1:
		player_bid_winner = models.Player.query.filter_by(game_id=int(game_id), order=int(list(game.bid_stack)[0])).first()
		player_bid_winner_partner = models.Player.query.filter_by(game_id=int(game_id), team=game.bid_winner).filter(
			models.Player.order != int(list(game.bid_stack)[0])).first()

		game.bid_stack = {str(player_order):24, str(player_bid_winner.order):-1, str(player_bid_winner_partner.order):-1, str(player_24_partner.order):-1}
		game.highest_bid = 25
		game.bid_winner = None
		game.trump = None
		game.trump_order = None
		game.aukat_set = True
		if game.double != 4:
			game.set_double()
		db.session.commit()
		socketio.emit("update_game", {'type': 'bid', 'screen': {'player_order': player_order, 'data': 24, 'type':'notImage', 'clear':0},
									  'info': {'next_player_order': player_bid_winner.order, 'data': game.highest_bid, 'double_set':game.double}, 'status':"Bidding turn - "+player_bid_winner.name},
					  to=game_id)
	else:
		game.increment_double_counter()
		db.session.commit()
		if game.double_counter == 2:
			game.double_counter = 0
			db.session.commit()
			player0 = models.Player.query.filter_by(game_id=int(game_id), order=0).first()
			socketio.emit("update_game", {'type': 'game_start',  'status':player.name+" has passed -- Game starts with "+player0.name}, to=game_id)
		else:
			socketio.emit("update_game",
						  {'type': 'ask_for_24', 'info': {'player_24_order': player_24_partner.order, 'data': 24}, 'status':player.name+" has passed -- Asking for 24 to "+player_24_partner.name}, to=game_id)


@socketio.on('trump_revealed')
def on_trump_reveal(data):
	game_id = data['game_id']
	game = models.Game.query.filter_by(id=int(game_id)).first()
	game.trump_revealed = True
	db.session.commit()
	player_order = data['player_order']
	player = models.Player.query.filter_by(game_id=int(game_id), order=player_order).first()
	restrictions = []
	trump_suite = game.trump
	trump_order = game.trump_order
	for c in player.deck:
		if c.suite != trump_suite:
			restrictions.append(c.id)
	if len(restrictions) == len(player.deck):
		restrictions.clear()

	trump = ""
	if trump_suite.value == 'no_trump' and trump_order == 0:
		trump = "red_joker"
	elif trump_suite.value == 'no_trump' and trump_order == 1:
		trump = "red_joker_reverse"
	elif trump_order == 0:
		trump = "5_of_"+trump_suite.value
	elif trump_order == 1:
		trump = "2_of_"+trump_suite.value

	status = player.name+" revealed Trump - "+trump_suite
	if trump_order == 1:
		status = status+" - Reverse"

	socketio.emit("update_game", {'type':'deal_card', 'info':{'next_player_order':player_order, 'restrictions':restrictions, 'allow_trump_reveal':0},
								  'trump':trump, 'status':status}, to=game_id)


def compete(c1, p1, c2, p2, order = 0):
	if order == 0:
		if c1.number.value['priority'] > c2.number.value['priority']:
			return p1
		else:
			return p2
	else:
		if c1.number.value['priority'] < c2.number.value['priority']:
			return p1
		else:
			return p2


def decide_winner_points(round_history, trump_revealed, trump_order, trump):
	first_player_order = list(round_history)[0]
	first_card_id = round_history[first_player_order]
	round_history.pop(first_player_order)
	first_card = models.Card.query.filter_by(id=first_card_id).first()
	first_suite = first_card.suite
	points = first_card.number.value['points']
	winner_player_order = first_player_order
	winner_card = first_card
	for player_order, card_id in round_history.items():
		card = models.Card.query.filter_by(id=card_id).first()
		points = points + card.number.value['points']
		if card.suite == first_suite:
			if trump_revealed:
				winner_player_order = compete(winner_card, winner_player_order, card, player_order, trump_order)
			else:
				winner_player_order = compete(winner_card, winner_player_order, card, player_order)
		elif trump_revealed and trump != models.CardSuite.NOTRUMP and card.suite == trump:
			winner_player_order = compete(winner_card, winner_player_order, card, player_order, trump_order)
		winner_card = round_history.get(winner_player_order)
	result = {'winner_player_order':winner_player_order, 'points':points}
	return result


@socketio.on('card_dealt')
def on_card_dealt(data):
	game_id = data['game_id']
	player_order = data['player_order']
	card_id = int(data['card'])
	card = models.Card.query.filter_by(id=card_id).first()
	game = models.Game.query.filter_by(id=int(game_id)).first()
	game.round[player_order] = card.id
	player = models.Player.query.filter_by(game_id=int(game_id), order=player_order).first()
	player.deck.remove(card)
	db.session.commit()
	screen = {'player_order': player_order, 'data': card.number.value['name'] + "_of_" + card.suite.value,
			  'type': 'image', 'clear':0}
	restrictions = []
	info = {'next_player_order':-1, 'restrictions':restrictions, 'allow_trump_reveal':0}
	status = ""
	if len(game.round) == 4:
		result = decide_winner_points(game.round, game.trump_revealed, game.trump_order, game.trump)
		winner_player_order = result['winner_player_order']
		winner = models.Player.query.filter_by(game_id=int(game_id), order=int(winner_player_order)).first()
		points = result['points']
		game.assign_points(winner, points)
		#TODO: send last round info to view
		game.round.clear()
		db.session.commit()
		info['next_player_order'] = winner.order
		status = "Team " + winner.team.value + " has won " + points + " points -- Next player: " + winner.name
	else:
		next_player_order = -1
		if player_order == 3:
			next_player_order = 0
		else:
			next_player_order = player_order + 1
		next_player = models.Player.query.filter_by(game_id=int(game_id), order=next_player_order).first()
		starting_player_order = list(game.round)[0]
		starting_card_id = game.round[starting_player_order]
		starting_card = models.Card.query.filter_by(id=starting_card_id).first()
		print(starting_card.suite.value)
		for c in next_player.deck:
			print("card:",c.suite.value)
			if c.suite.value != starting_card.suite.value:
				restrictions.append(c.id)
		print("restrictions:",restrictions)
		if len(restrictions) == len(next_player.deck):
			restrictions.clear()
			if game.trump_revealed == False:
				info['allow_trump_reveal'] = 1
		if player_order == 0:
			screen['clear'] = 1
		info['next_player_order'] = next_player_order
		info['restrictions'] = restrictions
		status = "Next player: "+next_player.name

	socketio.emit("update_game", {'type':'deal_card', 'info':info, 'screen':screen, 'status':status}, to=game_id)
