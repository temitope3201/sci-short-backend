import jwt
from datetime import datetime, timezone, timedelta
from decouple import config
import os
from flask_mail import Message, Mail
from flask import request
import re
import string
import secrets
import random
from bs4 import BeautifulSoup
from ..models import Url
import requests


mail = Mail()


SECRET_KEY = config('SECRET_KEY', 'secret')

def create_reset_token(user):

    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=1),
        'id': str(user.unique_code)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return token


def decode_token(token):
    
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms="HS256",
        options={"require_exp": True}
    )

def check_token(token):

    try:

        jwt.decode(
            token,
            SECRET_KEY,
            algorithms="HS256",
            options={"require_exp": True}
        )

        return True
    except:

        return False
    

def get_user_id(token):

    data = jwt.decode(
            token,
            SECRET_KEY,
            algorithms="HS256",
            options={"require_exp": True}
        )
    
    return data['id']



def send_forgot_password_email(user):
    
    current_site = request.url_root
    mail_subject = "Reset your password"
    domain = current_site
    token = create_reset_token(user)
    msg = Message(
        mail_subject, sender=os.environ.get("MAIL_USER"), recipients=[user.email]
    )
    msg.html = f"Please click on the link to reset your password, {domain}/user/reset_password/{token}"
    mail.send(msg)


def check_valid_url(url):

    regex = re.compile(					
    r'^(https?|ftp)://'  # http://, https://, or ftp://					
    r'([A-Za-z0-9.-]+)'  # domain					
    r'(\.[A-Za-z]{2,})'  # top-level domain					
    r'(:\d+)?'  # port (optional)					
    r'(/.*)?'  # path (optional)					
    )					
    return bool(regex.match(url))					

def generate_short_url():

 
	# Randomly choose characters from letters for the given length of the string
    short_url = ''.join(secrets.choice(string.ascii_letters+string.digits) for i in range(7))

    url_exist = Url.check_url(short_url)

    if url_exist:

        generate_short_url()

    else:
        return short_url
    

def extract_url_info(url):

    response = requests.get(url)


    page = BeautifulSoup(response.content, 'html.parser')

    title = page.title.string if page.title else ''

    meta_tags = page.find_all('meta')

    description = ''

    for meta in meta_tags:
        if 'name' in meta.attrs and meta.attrs['name'].lower == 'description':

            description = meta.attrs['content']

    
    
    return description, title