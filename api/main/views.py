from flask import request, redirect 
from flask_restx import Resource, Namespace, fields
from ..models import Url, User, Clicks
from http import HTTPStatus
from ..utils import db, limiter, cache
from .utils import get_location
from user_agents import parse





main_namespace = Namespace('', description='Namespace for the main page', path='')


@main_namespace.route('/<string:short_url>')
class VisitPageview(Resource):

  
  

    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @main_namespace.doc(description = "get the page for the short url", params = {"short_url": "Short URL String"})
    def get(self, short_url):

        """ 
            get the page for the short url
        """

        url = Url.query.filter_by(short_url = short_url).first()

        if url:

            url_to_view = url.true_url

            ip_address = request.remote_addr
            
            user_agent = parse(request.headers.get('user_agent'))
            device_type = user_agent.device.family
            location = get_location(ip_address)

           
            if url.no_of_clicks is None:
                url.no_of_clicks = 1

            else:
                url.no_of_clicks +=1


            db.session.commit()
            click = Clicks(
                location = location,
                ip_address = ip_address,
                device_type = device_type
            )

            click.save()

            return {'message': 'URL redirected', 'data': url_to_view}
        
        else:
            return {'message': 'The url does not exist'}, HTTPStatus.BAD_REQUEST
        

@main_namespace.route('/s/<string:short_url>')
class VisitScannedPage(Resource):

   

    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @main_namespace.doc(description = "get the page for the short url", params = {"short_url": "Short URL String"})
    def get(self, short_url):

        """ 
            go to a page for a scanned qrcode
        """
        url = Url.query.filter_by(short_url = short_url).first()

        if url:

            ip_address = request.remote_addr
            
            user_agent = parse(request.headers.get('user_agent'))
            device_type = user_agent.device.family
            location = get_location(ip_address)
            url_to_view = url.true_url

            url.qrcodescans += 1

            db.session.commit()
            click = Clicks(
                location = location,
                ip_address = ip_address,
                device_type = device_type
            )

            click.save()

            return redirect(url_to_view, 302)
        
        else:
            return {'message': 'The url does not exist'}, HTTPStatus.BAD_REQUEST
        

@main_namespace.route('/home/real')
class HomeView(Resource):

    def get(self):

        """ Home Page """

        return {'message': 'Welcome To the Shortener'}, HTTPStatus.OK

