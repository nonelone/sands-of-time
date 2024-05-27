from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

import random

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Integer, nullable=False)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    image = db.Column(db.String(30), nullable=False, unique=True)
    attack = db.Column(db.Integer, nullable=False)
    defence = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Integer, nullable=False)

class Decks(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    card_id = db.Column(db.Integer, db.ForeignKey(Card.id), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey(User.id))

class Lobby(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    host_id = db.Column(db.Integer, db.ForeignKey(User.id))
    joiner_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable = True)
    host_name = db.Column(db.String(30), nullable=False, unique=True)

def getDeckFromSQL(user_id):
    cards_data = db.session.query(Card.name, Card.image, Card.attack, Card.defence, Card.cost) \
                    .join(Decks, Decks.card_id == Card.id) \
                    .filter(Decks.owner_id == user_id) \
                    .all()
    res = []
    for card in cards_data:
        res.append([card.name, card.image, card.attack, card.defence, card.cost])
    return res

def createDeckFromSQL(n=15):
    cards_data = db.session.query(Card.name, Card.image, Card.attack, Card.defence, Card.cost).all()
    res = []
    for i in range(n):
        __card = random.choices(cards_data)[0]
        cards_data = [card for card in cards_data if card != __card]
        res.append(list(__card))
    return res

class Player:
    def __init__(self, id):
        self.id = id
        self.name = User.query.get(id).name
        self.hp = 30
        self.deck = getDeckFromSQL(id)
        self.hand = []
        self.cards_on_table = []
        self.mana = 1
        try:
            self.draw_card(4)
        except:
            print('error drawing initial hand!')

    def draw_card(self, n=1):
        try:
            for i in range(n):
                __card = random.choices(self.deck)[0]
                self.deck = [card for card in self.deck if card != __card]
                if len(self.hand) < 5:
                    self.hand.append(__card)
        except:
            print('error drawing card!')


class AI(Player):
    def __init__(self):
        self.hp = 45
        self.deck = createDeckFromSQL()
        self.hand = []
        self.cards_on_table = []
        self.mana = 0
        self.selected_card = None
        try:
            self.draw_card(4)
        except:
            print('error drawing initial hand!')

    def play(self):
        can_play = []
        if len(self.cards_on_table) < 5:
            for card in self.hand:
                if card[4] <= self.mana: can_play.append(card)

            if can_play != []:
                card_played = random.choices(can_play)[0]
                print("I want to play:", card_played)
                self.hand = [card for card in self.hand if card != card_played]
                self.mana = self.mana - card_played[4]
                self.selected_card = card_played

class Game():
    ai = None
    player = None
    selected_card = None

    def __init__(self,player_id):
        self.player = Player(player_id)
        self.ai = AI()
        
    def obij_morde(self, komu):
        res = None
        if komu == self.player:
            for card in self.ai.cards_on_table:
                self.player.hp = self.player.hp - card[2]
                if self.player.hp <= 0: return 'loose'

        else:
            for card in self.player.cards_on_table:
                self.ai.hp = self.ai.hp - card[2]
                if self.ai.hp <= 0: return 'vino'

    def kontestUJ(self, antyperspirant, wlasciciel):
        if antyperspirant != None:
            #patrzymy sie na karty na stole przeciwnika
            przecwnik = self.ai if wlasciciel == self.player else self.player
            for card in przecwnik.cards_on_table:
                print('typ karty wybranej ', type(antyperspirant))
                print('karta na stole przeciwnika', card)
                #robimy damage, antyperspirant ma pierwszenstwo aby nie robić zatorow
                if antyperspirant[3] > 0: #poki zyje
                    card[3] = card[3] - antyperspirant[2] #przeciwnika nie zdzierze
                    antyperspirant[3] = antyperspirant[3] - card[2]
                    if card[3] <= 0:
                        przecwnik.cards_on_table.remove(card)
                else:
                    break
            
            if antyperspirant[3] > 0:
                wlasciciel.cards_on_table.append(antyperspirant)