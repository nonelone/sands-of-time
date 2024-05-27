from flask import Flask, render_template, request, redirect, Blueprint, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
#import secrets
from models import db, User, Card, Decks, Game, Lobby, getDeckFromSQL
#from faker import Faker
#fake = Faker('ja_JP')

import random


game_list = []

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///.db'
app.config['SECRET_KEY']= '533d7fde9e6c690443ada5aa0e6a46ac6b6ae2d571269e4db6c74b7a454714c9' 
# as per: python -c 'import secrets; print(secrets.token_hex())'


db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

def init_database():
    with app.app_context():
        db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@app.route('/home')
def home():
    highscore = User.query.order_by(User.score.desc()).limit(10)
    lowscore = User.query.order_by(User.score).limit(10)
    return render_template('home.html', highscore=highscore, lowscore=lowscore)

@app.route('/end_screen')
def end_screen():
    result = request.form.get('result')
    return render_template('end_screen.html', result = result)

@app.route('/vs_ai',  methods=['GET', 'POST'])
@login_required
def vs_ai():
    game = None
    for __game in game_list:
        if __game.player.id == current_user.id:
            game = __game


    if "end" == request.form.get('state'):
        if game != None:
            game_list.remove(game)
            return render_template('/end_screen.html', result = 'loose')

    if "endturn" == request.form.get('turn'):
        if game != None:
            if game.selected_card != None: #tura gracza
                if len(game.player.cards_on_table) < 5:
                    for card in game.player.hand:
                        if card[0] == game.selected_card:
                            if card[4] <= game.player.mana:
                                game.player.mana = game.player.mana - card[4]
                                game.player.hand = [card for card in game.player.hand if card[0] !=game.selected_card]
                                #game.player.cards_on_table.append(card)
                                game.kontestUJ(card, game.player)
                                break
                            else: break

                game.selected_card = None

            #koliste obijanie mordy:
            wynik_walki = game.obij_morde(game.ai)
            if wynik_walki != None: 
                game_list.remove(game)
                return render_template('/end_screen.html', result = 'vino')
            

            game.ai.mana += 1 #tura AI
            game.ai.play()
            print(game.ai.selected_card)
            game.kontestUJ(game.ai.selected_card, game.ai)
            game.ai.draw_card()

            #koliste obijanie mordy #2:
            wynik_walki = game.obij_morde(game.player)
            if wynik_walki != None: 
                game_list.remove(game)
                return render_template('/end_screen.html', result = 'loose')

            game.player.mana += 1 #"poczatek" tury gracza
            game.player.draw_card() 

            return render_template('vs_ai.html', game=game)

    selected_card = request.form.get('selected_card_id')
    if selected_card:
        if game:
            game.selected_card = selected_card
            return render_template('vs_ai.html', game=game, selected_card_id=selected_card)

    if request.method == 'POST' or game != None:
        return render_template('vs_ai.html', game=game)

    new_game = Game(current_user.id)
    game_list.append(new_game)
    return render_template('vs_ai.html', game=new_game)

#GAME TO BE FIXED (OR NOT):
@app.route('/game',  methods=['GET', 'POST'])
@login_required
def game():
    your_id = 0
    enemy_id = 0
    lobby_list = Lobby.query.all()
    print(game_list)
    for game in game_list:
        print(game.players)

    for lobby in lobby_list:
        #print(f"ID lobby: ${lobby.id}, host: ${lobby.host_id}, 2gi: ${lobby.joiner_id}")
        if lobby.host_id == current_user.id or lobby.joiner_id == current_user.id:
            if lobby.host_id == current_user: 
                enemy_id = 1
                your_id = 0
            else:
                your_id = 1
                enemy_id = 0
            new_game = Game(lobby.id, lobby.host_id, lobby.joiner_id)
            game_list.append(new_game)
            return render_template('game.html', lobby=lobby, game=new_game, player_data=new_game.players[your_id], enemy_data=new_game.players[enemy_id])

    if request.method == 'POST':
        lobby_id = int(request.form.get('lobby_id'))
        print(lobby_id)
        for lobby in lobby_list:
            if lobby.id == lobby_id:
                if lobby.host_id != current_user.id:
                    lobby.joiner_id = current_user.id
                    db.session.commit()
                    new_game = Game(lobby_id, lobby.host_id, lobby.joiner_id)
                    game_list.append(new_game)
                    enemy_id = 1
                else:
                    your_id = 1
                return render_template('game.html', lobby=lobby, game=new_game, player_data=new_game.players[your_id], enemy_data=new_game.players[enemy_id])

    return "404"


@app.route('/deckbuilder', methods=['GET', 'POST'])
@login_required
def deckbuilder():
    if not current_user.is_authenticated:
        return 503
    
    card_list = Card.query.all()
    card_ids = Decks.query.filter_by(owner_id=current_user.id).with_entities(Decks.card_id).all()
    card_ids = [card[0] for card in card_ids] if card_ids else [] #do int

    if request.method == 'POST':
        print(getDeckFromSQL(current_user.id))
        card_id = request.form.get('card_id')
        if int(card_id) in card_ids:
            card = Decks.query.filter_by(owner_id=current_user.id, card_id=card_id).first()
            db.session.delete(card)
            db.session.commit()
        else:
            if Decks.query.filter_by(owner_id=current_user.id).with_entities(Decks.card_id).count() < 15:
                card = Decks(owner_id=current_user.id, card_id=card_id)
                db.session.add(card)
                db.session.commit()
        deck_done = Decks.query.filter_by(owner_id=current_user.id).with_entities(Decks.card_id).count() == 15
        return render_template('deckbuilder.html', card_list=Card.query.all(), deck_done=deck_done)
    else:
        for card in card_list:
            if card.id in card_ids:
                card.used = True
            else:
                card.used = False
        deck_done = Decks.query.filter_by(owner_id=current_user.id).with_entities(Decks.card_id).count() == 15
        return render_template('deckbuilder.html', card_list=card_list, deck_done=deck_done)

@app.route('/lobby', methods=['GET', 'POST'])
@login_required
def lobby():
    lobby_list = Lobby.query.all()
    print('lobby')
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        for lobby in lobby_list:
            print(lobby.host_id, lobby.joiner_id, lobby.id)
            if current_user.id == lobby.host_id: #jesli gracz jest juz hostem:
                return render_template('lobby.html', lobby_list=lobby_list)

        #utworz lobby z graczem jako host
        new_lobby = Lobby(host_id=user_id, host_name=current_user.name)
        db.session.add(new_lobby)
        db.session.commit()
    return render_template('lobby.html', lobby_list=lobby_list)

#AUTH:
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not User.query.filter_by(name=username).first():
            hashed_password = generate_password_hash(password)
            new_user = User(name=username, password=hashed_password, score=0)
            db.session.add(new_user)
            db.session.commit()
            new_deck = Decks(owner_id=new_user.id)
            db.session.add(new_deck)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(name=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('deckbuilder'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


#GENERATORY:
def add_user(name, password):
    with app.app_context():
        if User.query.filter_by(name=name).first() is None:
            new_user = User(name=name, password=generate_password_hash(password), score=0)
            db.session.add(new_user)
            db.session.commit()

        else:
            print(User.query.filter_by(name=name).first())

def generUJ(n):
    with app.app_context():
        for i in range(n):
            new_card = Card(name=str(i), image=(str(i)+".jpg"), attack=random.randint(1, 4), defence=random.randint(1, 5), cost=random.randint(1, 3))
            db.session.add(new_card)
            db.session.commit()

if __name__ == '__main__':
    init_database()
    try:
        generUJ(50)
        add_user('parsec', '1234')
        add_user('moon', '1234')
    except:
        print("cant generate fake data")
    #add_user('sus1', '1234')
    #add_user('sus1', '1234')
    #add_user('sus2', '1234')
    app.run(debug=True, port=12137)