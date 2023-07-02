from ..utils import db
from datetime import datetime
from uuid import uuid4


class User(db.Model):

    id = db.Column(db.Integer(), primary_key = True)
    first_name = db.Column(db.String(60), nullable = False)
    last_name = db.Column(db.String(60), nullable = False)
    username = db.Column(db.String(60), nullable = False, unique = True)
    email = db.Column(db.String(), nullable = False, unique = True)
    password_hash = db.Column(db.String(), nullable = False)
    unique_code = db.Column(db.String())
    reset_password_token = db.Column(db.String())
    urls = db.relationship('Url', backref = 'url_creator', lazy = True)


    def save(self):

        self.unique_code = uuid4().hex
        db.session.add(self)
        db.session.commit()

    def delete(self):

        db.session.delete()
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):

        return cls.query.get_or_404(id)


    


class Url(db.Model):

    id = db.Column(db.Integer(), primary_key = True)
    true_url = db.Column(db.String(), nullable = False)
    short_url = db.Column(db.String(), nullable = False)
    unique_code = db.Column(db.String(), unique = True)
    title = db.Column(db.String())
    description = db.Column(db.String())
    clicks = db.relationship('Clicks', backref = 'own_url', lazy = True)
    qrcode = db.Column(db.String())
    date_created = db.Column(db.DateTime(), nullable = False, default = datetime.utcnow)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    qrcodescans = db.Column(db.Integer(), default = 0)
    no_of_clicks = db.Column(db.Integer(), default = 0)
    qr_image_url = db.Column(db.String())
    qr_created = db.Column(db.Boolean(), default = False)
     
    
    def save(self):

        self.unique_code = uuid4().hex
        db.session.add(self)
        db.session.commit()

    def delete(self):

        db.session.delete()
        db.session.commit()

    @classmethod
    def check_url(cls, url):

        url_exist = cls.query.filter_by(short_url = url).first()

        return True if url_exist else False
    
    @classmethod
    def get_by_id(cls, id):

        return cls.query.get_or_404(id)
    
    

class Clicks(db.Model):

    id = db.Column(db.Integer(), primary_key = True)
    location = db.Column(db.String())
    ip_address = db.Column(db.String())
    device_type = db.Column(db.String())
    timestamp = db.Column(db.DateTime(), nullable = False, default = datetime.utcnow)
    url = db.Column(db.Integer(), db.ForeignKey('url.id'))
    unique_code = db.Column(db.String())

    def save(self):

        self.unique_code = uuid4().hex
        db.session.add(self)
        db.session.commit()

    def delete(self):

        db.session.delete()
        db.session.commit()
