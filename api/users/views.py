from flask_restx import Resource, Namespace, abort, fields
from flask import request, jsonify
from ..models import User
# from .schemas import  user_namespace,signup_model, login_model, user_model, password_update_model, user_update_model, request_password_reset, reset_password_model
from flask_jwt_extended import get_jwt_identity, jwt_required, create_access_token, create_refresh_token
from http import HTTPStatus
from werkzeug.security import generate_password_hash, check_password_hash
from ..utils import db, cache, limiter
from ..utils.utils import send_forgot_password_email, decode_token




user_namespace = Namespace('users', description='Namespace For All Registered users')

signup_model = user_namespace.model(
    'User_Signup',{
        'email': fields.String(description = 'Add Email Address', required = True),
        'first name': fields.String(description = 'Add First Name', required = True),
        'last_name': fields.String(description = 'Add Last name', required = True),
        'username': fields.String(description = 'Add A Username', required = True),
        'password': fields.String(description = 'Enter Password', required = True),
        'confirm_password': fields.String(description = 'Confirm Password', required = True)
    }
)

login_model = user_namespace.model(
    'User_Login',{
        'email': fields.String(description ='Add Email Address', required = True),
        'password': fields.String(description = 'Enter Your Password', required = True)
    }
)

user_model = user_namespace.model(
    'User',{
        'id': fields.String(description = 'ID of the user', readonly = True),
        'email': fields.String(description = 'Add Email Address', required = True),
        'first_name': fields.String(description = 'Add First Name', required = True),
        'last_name': fields.String(description = 'Add Last name', required = True),
        'username': fields.String(description = 'Add A Username', required = True)
    }
)

password_update_model = user_namespace.model(
    'UpdatePassword',{
        'old_password': fields.String(description = 'enter the current password', required = True),
        'new_password': fields.String(description = 'The New password to be changed', required = True)
    }
)


user_update_model = user_namespace.model(
    'UserUpdate',{
        'first_name': fields.String(description = 'Add First Name'),
        'last_name': fields.String(description = 'Add Last name'),
        'username': fields.String(description = 'Add A Username')
    }
)

request_password_reset = user_namespace.model(
    'RequestPasswordRequest',{
        'email': fields.String(description = 'Add Email Address', required = True)
    }
)


reset_password_model = user_namespace.model(
    'ResetPassword',{
        'new_password': fields.String(description = 'Add The New password', required = True),
        'confirm_password': fields.String(description = 'Confirm The Password', required = True)
    }
)


@user_namespace.route('/signup')
class UserSignup(Resource):

    
    
    @user_namespace.expect(signup_model)
    @user_namespace.doc(description = "Create A User")
    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    def post(self):
        
        """
        Create A User
        """
    
        data = request.get_json()

        if User.query.filter_by(username = data.get('username')).first() or User.query.filter_by(email = data.get('emaill')).first():
            return {'message': 'Username or Email already in use'}, HTTPStatus.FORBIDDEN
        
        check_password_match = data.get('password') == data.get('confirm_password')

        if not check_password_match:

            return {'message': 'passwords do not match'}, HTTPStatus.FORBIDDEN
        
        new_user = User(
            first_name = data.get('first_name'),
            last_name = data.get('last_name'),
            email = data.get('email'),
            username = data.get('username'),
            password_hash = generate_password_hash(data.get('password'))
        )

        new_user.save()

        return {'message': 'User Created Successfully'}, HTTPStatus.CREATED
        
        

@user_namespace.route('/login')
class UserLogin(Resource):
    

    @user_namespace.expect(signup_model)
    @user_namespace.doc(description = "Create a User Login Token")
    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)    
    @user_namespace.expect(login_model)
    def post(self):

        """
            Create a User Login Token
        """    

        data = request.get_json()

        user = User.query.filter_by(email = data.get('email')).first()

        if user and check_password_hash(user.password_hash, data.get('password')):

            access_token = create_access_token(identity=user.username)
            refresh_token = create_refresh_token(identity=user.username)

            return {'access_token': access_token, 'refresh_token': refresh_token}, HTTPStatus.CREATED
        
        else:
            {'message': 'email or password incorrect'}, HTTPStatus.BAD_REQUEST


@user_namespace.route('/refresh')
class GenerateRefreshToken(Resource):


    

    @user_namespace.doc(description = "Get Refresh Token")
    @jwt_required(refresh=True)
    def post(self):
        """
            Get Refresh Token
        """

        username = get_jwt_identity()

        access_token = create_access_token(identity=username)

        return {'access_token': access_token}, HTTPStatus.CREATED


@user_namespace.route('/change_password')
class UserPasswordChange(Resource):

    @jwt_required()
    @user_namespace.expect(password_update_model)
    @user_namespace.doc(description = "User Password Change")
    def get(self):

        """ 
            User Password Change
        """

        username = get_jwt_identity()


        current_user = User.query.filter_by(username = username).first()

        data = request.get_json()

        old_password = data.get('old_password')
        new_password = data.get('new_password')


        if check_password_hash(current_user.password_hash, old_password):

            current_user.password_hash = generate_password_hash(new_password)

            db.session.commit()

            return {'message': 'Password Updated Successfully'}, HTTPStatus.OK
        
        else:

            return {'message': 'Wrong Passowrd entered'}, HTTPStatus.FORBIDDEN


@user_namespace.route('/user/getuser')
class GetLoggedInUser(Resource):

    @jwt_required()
    @user_namespace.marshal_with(user_model)
    @user_namespace.doc(description = "get details for the logged in user")
    def get(self):
        
        """ 
         get details for the logged in user
        """

        username = get_jwt_identity()

        user = User.query.filter_by(username = username).first()

        return user, HTTPStatus.OK


@user_namespace.route('/user/<int:user_id>')
class GetUpdateDeleteUser(Resource):

    

    @user_namespace.doc(description = "get User details by ID", params = {"user_id": "User ID"})
    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @jwt_required()
    @user_namespace.marshal_with(user_model)
    
    def get(self, user_id):

        """ 
            get User details by ID
        """

        user = User.get_by_id(user_id)

        return user, HTTPStatus.OK

    @user_namespace.doc(description = "Update A User Information", params = {"user_id": "User ID"})
    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @jwt_required()
    @user_namespace.marshal_with(user_model)
    @user_namespace.expect(user_update_model)
    def put(self, user_id):
        """ 
            Update A User Information

        """

        current_username = get_jwt_identity()

        user_to_update = User.get_by_id(user_id)
        current_user = User.query.filter_by(username = current_username).first()

        if current_user != user_to_update:
            abort ('You Are Not Permittted To Edit This User'), HTTPStatus.FORBIDDEN
        
        else:
            data = request.get_json()

            user_to_update.username = data.get('username')
            user_to_update.first_name = data.get('first_name')
            user_to_update.last_name = data.get('last_name')


            db.session.commit()

            return user_to_update, HTTPStatus.ACCEPTED
        
    @user_namespace.doc(description = "Delete a user account", params = {"user_id": "User ID"})
    @limiter.limit("10 per minute")
    @cache.cached(timeout=300)
    @jwt_required()
    def delete(self, user_id):

        """ 
            Delete a user account
        """
        current_username = get_jwt_identity()

        user_to_delete = User.get_by_id(user_id)
        current_user = User.query.filter_by(username = current_username).first()

        if current_user != user_to_delete:
            abort ('You Are Not Permittted To Delete This User'), HTTPStatus.FORBIDDEN

        else:
            db.session.delete(user_to_delete)
            db.session.commit()

            return {'message': 'user was deleted successfully'}, HTTPStatus.OK

    
    

@user_namespace.route('/reset_request')
class RequestPasswordReset(Resource):

    @user_namespace.expect(request_password_reset)
    def post(self):

        """ 
            Send A Request To reset forgotten passwords
        """

        data = request.get_json()

        email_user = User.query.filter_by(email = data.get('email')).first()

        if email_user is None:

            return {'message': 'Email does not exist'}, HTTPStatus.BAD_REQUEST
        
        send_forgot_password_email(email_user)

        return {'message': 'Password reset Instructions have been sent to your mail'}, HTTPStatus.OK
    

    

@user_namespace.route('/reset_password/<string:token>')
class ResetPassword(Resource):

    @user_namespace.expect(reset_password_model)
    def post(self, token):

        """ 
            Reset A Password
        """

        data = request.get_json()

        user_code = decode_token(token)

        user = User.query.filter_by(unique_code = user_code).first()

        if user is None:

            return {'message':'No record found for this email, Signup now'}, HTTPStatus.FORBIDDEN
        

        if data.get('new_password') != data.get('confirm_password'):

            return {'message': 'Passwords Do not Match Please Retry'}, HTTPStatus.BAD_REQUEST
        

        user.password = generate_password_hash(data.get('new_password'))

        db.session.commit()

        return {'message': 'Password Updated successfully'}, HTTPStatus.ACCEPTED



