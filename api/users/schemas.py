from flask_restx import Namespace
from flask_restx import fields


user_namespace = Namespace('user', description='Namespace For All Registered users')

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
        'first name': fields.String(description = 'Add First Name', required = True),
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
        'email': fields.String(description = 'Add Email Address'),
        'first name': fields.String(description = 'Add First Name'),
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