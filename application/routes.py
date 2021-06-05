from application import app
from flask import render_template, request, url_for, redirect
from application.forms import StartGameForm
from application import models, db

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
		game = models.Game.query.filter_by(id=form.gameid.data).first()
		if game is None:	#no game found with this id
			return redirect(url_for('index', msg="Game ID is invalid - check again"))
		count = 0
		for p in game.players:
			if form.name.data.lower() == p.name.lower() and form.team.data == p.team.value:	#returning player
				return "returning player"
			if form.team.data == p.team.value:
				count = count + 1
		if count == 2:	#no seats left in this team
			return redirect(url_for('index', msg="Game already has 2 players in Team "+form.team.data+" - select another team"))
		elif count == 1:	#partner already in game
			for p in game.players:
				if form.team.data == p.team.value:
					player.order = p.order + 2
					break
		else:	#first player in this team
			player.order = 1
		game.players.insert(player.order, player)
		db.session.commit()
		return "joining game"
	# creating new game
	player.order = 0
	game = models.Game(players=[player])
	db.session.add(player)
	db.session.add(game)
	db.session.commit()
	return render_template("game.html", game=game, player=player)