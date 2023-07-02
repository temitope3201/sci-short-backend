from flask import request, abort
from flask_restx import Namespace, Resource, fields
from ..models import User, Url
from flask_jwt_extended import jwt_required, get_jwt_identity
from http import HTTPStatus
from ..utils.utils import check_valid_url, generate_short_url, extract_url_info
from ..utils import db, cache, limiter
import qrcode
import os
from imgurpython import ImgurClient
from decouple import config






urls_namespace = Namespace('urls', description='Namespace for the urls')

# shorten_url_model = urls_namespace.model(
#     'shorten_url',{
#         'long_url': fields.String(description = 'enter the url to shorten', required = True)
#     }
# )
shorten_url_model = urls_namespace.model(
    'customized_urls',{
        'long_url': fields.String(description = 'enter the url to shorten', required = True),
        'custom_url': fields.String(description = 'enter your custom url name')
    }
)

url_update_model = urls_namespace.model(
    'updateModel',{
        'custom_url' : fields.String(description = 'enter your custom url name')
    }
)

url_model = urls_namespace.model(
    'UrlModel',{
      'id': fields.Integer(description = 'id of the url', readonly = True),
      'true_url' : fields.String(required=True , description='Long url'),
      'short_url' : fields.String(required=True , description='Short url'),
      'name' : fields.String(required=True , description='Short url name'),
      'title' : fields.String(required=True , description='Long url title'),
      'description' : fields.String(required=True , description='Long url description'),
      'date_created' : fields.DateTime(),
      'qrcodescans': fields.Integer(description = 'Number of times the qrcode was scanned'),
      'no_of_clicks' : fields.Integer(required=True , description='Number of clicks'),
      'unique_code': fields.String(description = 'Url uuid'),
      'qr_image_url': fields.String(descrition = 'url of the imgur image'),
      'qr_created': fields.Boolean(description='Has Qr Code Been Created?')
    }
)


@urls_namespace.route('/shorten')
class ShortenUrlView(Resource):


    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @urls_namespace.doc(description = "Shorten a given url")
    @urls_namespace.expect(shorten_url_model)
    @jwt_required()
    def post(self):

        """
            Shorten a given url
        """

        data = request.get_json()
        url = data.get('long_url')
        custom_url = data.get('custom_url')
        username = get_jwt_identity()

        url_is_valid = check_valid_url(url)

        if url_is_valid:
            if custom_url:
                short_url_string =custom_url

            else:
                short_url_string = generate_short_url()

            user = User.query.filter_by(username = username).first()
            title, description = extract_url_info(url)

            new_url = Url(
                true_url = url,
                short_url = short_url_string,
                title = title,
                description = description,
                url_creator = user
            )

            try:
                new_url.save()

            except:
                db.session.rollback()
                response = { 'message' : 'An error occurred'} 
                return response , HTTPStatus.INTERNAL_SERVER_ERROR 
            
            return {'Short URL': f'http://{request.host}/{short_url_string}', 'message': 'Url Shortened successfully'}, HTTPStatus.CREATED

            
        else:

            return {'message': 'The URL is not valid'}, HTTPStatus.BAD_REQUEST
        
@urls_namespace.route('/curren_user')
class GetCurrentUserLinks(Resource):


    @urls_namespace.marshal_list_with(url_model)
    @urls_namespace.doc(description = "Get Urls for a logged In user")
    @jwt_required()
    def get(self):

        """ 
            Get Urls for a logged In user
        """

        current_user = User.query.filter_by(username = get_jwt_identity()).first()

        urls = Url.query.filter_by(user_id = current_user.id).order_by(Url.date_created.desc()).all()

        return urls, HTTPStatus.OK
        

@urls_namespace.route('/get_urls/<int:user_id>')
class GetUserUrls(Resource):


    @urls_namespace.marshal_list_with(url_model)
    @jwt_required()
    @urls_namespace.doc(description = "Get The URLS shortened by a user", params = {"user_id":"User ID"})
    def get(self, user_id):

        """ 
            Get The URLS shortened by a user
        """
        

        current_user = User.query.filter_by(username = get_jwt_identity()).first()

        url_creator = User.get_by_id(user_id)

        if current_user == url_creator:

            urls = Url.query.filter_by(user_id = current_user.id).order_by(Url.date_created.desc()).all()

            return urls, HTTPStatus.OK

        else:

            abort('You are not permitted to view this info'), HTTPStatus.FORBIDDEN

        
@urls_namespace.route('/<int:url_id>/url')
class GetUpdateDeleteAUrl(Resource):


    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @urls_namespace.doc(description = "Get Info on one Url", params = {"url_id": "URL ID"})
    @urls_namespace.marshal_with(url_model)
    @jwt_required()
    def get(self, url_id):

        """ 
            Get Info on one Url
        """

        url_to_view = Url.get_by_id(url_id)

        current_user = User.query.filter_by(username = get_jwt_identity()).first()
        url_creator = url_to_view.url_creator
    

        if current_user == url_creator:

            return url_to_view,  HTTPStatus.OK
        
        else:

            abort('You are not permitted to view this info'), HTTPStatus.FORBIDDEN


    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @urls_namespace.doc(description = "Update A short Url", params = {"url_id": "URL ID"})
    @urls_namespace.expect(url_update_model) 
    @jwt_required()
    def put(self, url_id):

        """ 
            Update A short Url
        """

        data = request.json()
        custom_url = data.get('custom_url')
        url_to_update = Url.get_by_id(url_id)


        current_user = User.query.filter_by(username = get_jwt_identity()).first()
        url_creator = url_to_update.url_creator

        if current_user == url_creator:

            if custom_url:
                new_short_string = custom_url

            else:
                new_short_string = generate_short_url()


            url_to_update.short_url = new_short_string

            db.session.commit()

            return {'message': 'Short Url Refreshed', 'short_url': f'http://{request.host}/{new_short_string}'}, HTTPStatus.CREATED
        
        else:
            return{'message': 'User is not permitted to update this url'}, HTTPStatus.FORBIDDEN



    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @urls_namespace.doc(description = "Delete A Created URL", params = {"url_id": "URL ID"})
    @jwt_required()
    def delete(self, url_id):
        """ 
            Delete A Created Url
        """
        url_to_delete = Url.get_by_id(url_id)


        current_user = User.query.filter_by(username = get_jwt_identity()).first()
        url_creator = url_to_delete.url_creator

        if current_user == url_creator:

            db.session.delete(url_to_delete)
            db.session.commit()

            return {'message': 'url deleted successfully'}, HTTPStatus.OK
        
        else:
            return{'message': 'User is not permitted to delete this url'}, HTTPStatus.FORBIDDEN



@urls_namespace.route('/generate_qr/<int:url_id>')
class GenerateQrCode(Resource):


    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @urls_namespace.doc(description = "Generate QRcode for A url", params = {"url_id": "URL ID"})
    @jwt_required()
    def get(self, url_id):

        """ 
            generate the qrcode for the url 
        """
        imgur_client_id = config('IMGUR_CLIENT_ID')
        imgur_client_secret = config('IMGUR_CLIENT_SECRET')

        imgur_client = ImgurClient(imgur_client_id, imgur_client_secret)

        current_user = User.query.filter_by(username = get_jwt_identity()).first()
        main_url = Url.get_by_id(url_id)
        url_creator = main_url.url_creator
        image_name = main_url.unique_code
        short_url = main_url.short_url
        url_to_generate = f'http://{request.host}/s/{short_url}'


        if current_user == url_creator:

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url_to_generate)
            qr.make(fit=True)

            img = qr.make_image(fill = 'black', back_color = 'white')

            picture_fn = image_name+'.png'
            picture_path = os.path.join(request.root_path, 'static/qrcodes', picture_fn)

            img.save(picture_path)

            main_url.qr_created = True
            
            uploaded_image = imgur_client.upload_from_path(picture_path, config=None, anon=True)
            main_url.qr_image_url = uploaded_image['link']

            db.session.commit()
            


            return {'message': 'QRCode created successfully'}, HTTPStatus.CREATED
        
        else:

            return {'message': 'User not permitted to create qrcode for this url'}, HTTPStatus.FORBIDDEN
        

# @urls_namespace.route('/custom_url')
# class GenerateCustomUrl(Resource):

#     @jwt_required()
#     @urls_namespace.expect(create_customized_url_model)
#     def post(self):

#         """ 
#             Create a customized URL for the USer
#         """

#         data = request.get_json()
#         url = data.get('long_url')
#         username = get_jwt_identity()

#         url_is_valid = check_valid_url(url)

#         if url_is_valid:
#             short_url_string = data.get('custom_url')

#             user = User.query.filter_by(username = username).first()
#             title, description = extract_url_info(url)

#             new_url = Url(
#                 true_url = url,
#                 short_url = short_url_string,
#                 title = title,
#                 description = description,
#                 url_creator = user
#             )

#             try:
#                 new_url.save()

#             except:
#                 db.session.rollback()
#                 response = { 'message' : 'An error occurred'} 
#                 return response , HTTPStatus.INTERNAL_SERVER_ERROR 
            
#             return {'Short URL': f'https://{request.host}/{short_url_string}'}, HTTPStatus.CREATED

            
#         else:

#             return {'message': 'The URL is not valid'}, HTTPStatus.BAD_REQUEST
        


