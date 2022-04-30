# import os

# from flask import Flask
# from flask_sse import sse


# def create_app(script_info=None):

#     # instantiate the app
#     app = Flask(
#         __name__,
#         template_folder="../client/templates",
#         static_folder="../client/static",
#     )

#     # set config
#     app_settings = os.getenv("APP_SETTINGS")
#     app.config.from_object(app_settings)       
    


#     # register blueprints
#     from project.server.main.views import main_blueprint

#     app.register_blueprint(main_blueprint)
#     app.register_blueprint(sse, url_prefix='/stream')

#     # shell context for flask cli
#     app.shell_context_processor({"app": app})

#     return app
