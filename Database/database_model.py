from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///sqliteDB', echo=False)

Session = sessionmaker(bind=engine)
db_session = Session()

Base = declarative_base()


class BetHistory(Base):
    __tablename__ = 'bet_history'

    bet_href = Column(String, primary_key=True)
    won = Column(Integer)
    bet_odds = Column(Float)
    profit = Column(Float)

    def __repr__(self):
        return "<Bet(bet_href='{}', won='{}', profit='{}')>".format(self.bet_href, self.won, self.profit)


Base.metadata.create_all(engine)
