from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def add_boat_instance(name: str, url: str, city: str, port: str, note: str = None):
    from models import Boat
    boat = Boat(name=name, url=url, city=city, port=port, note=note)
    db.session.add(boat)
    try:
        db.session.commit()
        return boat
    except Exception:
        db.session.rollback()
        raise

def get_all_boats():
    from models import Boat
    return Boat.query.order_by(Boat.id).all()

def get_boat_by_id(boat_id: int):
    from models import Boat
    return Boat.query.get(boat_id)

# 추가: 배 삭제 함수
def delete_boat(boat_id: int):
    from models import Boat
    boat = Boat.query.get(boat_id)
    if not boat:
        raise ValueError("등록된 배를 찾을 수 없습니다.")
    db.session.delete(boat)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

def update_boat(boat_id: int, name: str, url: str, city: str, port: str, note: str = None):
    from models import Boat
    boat = Boat.query.get(boat_id)
    if not boat:
        raise ValueError("등록된 배를 찾을 수 없습니다.")
    boat.name = name
    boat.url = url
    boat.city = city
    boat.port = port
    boat.note = note
    try:
        db.session.commit()
        return boat
    except Exception:
        db.session.rollback()
        raise