from flask import Flask, render_template, request, redirect
from support_resistances import support_resistance_blueprint
from yahoo_api_historical_data import historical_blueprint

from flask import Blueprint




app = Flask(__name__)
# register routes from urls
app.register_blueprint(support_resistance_blueprint, url_prefix='/support_resistances')
# we can register routes with specific prefix
app.register_blueprint(historical_blueprint, url_prefix='/yahoo_api_historical_data')


index_blueprint = Blueprint('index', __name__,)

@index_blueprint.route('/')
def index():
    return render_template('index.html')

app.register_blueprint(index_blueprint, url_prefix='/')


if __name__ == "__main__":
    app.run(debug=True)
    

