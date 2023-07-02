from api import create_app
from api.config import config_dict

# config=config_dict['prod']
app = create_app()

if __name__ == "__main__":

    app.run()