from flask import Flask, jsonify, request, Response, send_file
from flask_restful import Api, Resource
from flask_cors import CORS
from flasgger import Swagger
from functools import wraps
from pitcherOdds import get_pitcher_strikeout_odds, save_odds_to_json
from StrikeoutSuitePy import main as strikeout_suite_main
from StrikeoutPredictionsImage import generate_image
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
api = Api(app)
swagger = Swagger(app)

# Authentication setup
def check_auth(username, password):
    """Check if a username/password combination is valid."""
    return username == 'admin' and password == 'slide1234'  # Replace with your desired username and password

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

class GeneratePitcherOdds(Resource):
    @requires_auth
    def get(self):
        """
        Generate pitcher strikeout odds JSON
        ---
        tags:
          - Pitcher Odds
        responses:
          200:
            description: Pitcher strikeout odds generated successfully
          500:
            description: An error occurred while generating odds
        """
        try:
            api_key = '7ceaebfb8ad303152dfbabdcf2f4dfac'  # Replace with your actual API key
            odds = get_pitcher_strikeout_odds(api_key)
            save_odds_to_json(odds)
            return {"message": "Pitcher strikeout odds generated and saved successfully"}, 200
        except Exception as e:
            return {"error": str(e)}, 500

class GenerateStrikeoutPredictions(Resource):
    @requires_auth
    def get(self):
        """
        Generate strikeout predictions CSV
        ---
        tags:
          - Strikeout Predictions
        responses:
          200:
            description: Strikeout predictions CSV generated successfully
          500:
            description: An error occurred while generating predictions
        """
        try:
            strikeout_suite_main()
            return {"message": "Strikeout predictions CSV generated successfully"}, 200
        except Exception as e:
            return {"error": str(e)}, 500

class GeneratePredictionsImage(Resource):
    @requires_auth
    def get(self):
        """
        Generate and return the strikeout predictions image
        ---
        tags:
          - Predictions Image
        responses:
          200:
            description: Strikeout predictions image generated successfully
            content:
              image/png:
                schema:
                  type: string
                  format: binary
          500:
            description: An error occurred while generating the image
        """
        try:
            image_path = generate_image()
            return send_file(image_path, mimetype='image/png')
        except Exception as e:
            return {'error': str(e)}, 500

api.add_resource(GeneratePitcherOdds, "/generate-pitcher-odds")
api.add_resource(GenerateStrikeoutPredictions, "/generate-strikeout-predictions")
api.add_resource(GeneratePredictionsImage, "/generate-predictions-image")

if __name__ == "__main__":
    app.run(debug=True)
