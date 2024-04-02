from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS,cross_origin
from webScraper import main

app = Flask(__name__)
CORS(app)

#Configure the PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://debarunlahiri:password@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ServerConfig(db.Model):
    __tablename__ = 'server-config'
    id = db.Column(db.Integer, primary_key=True)
    config_name = db.Column(db.String(225))
    config_value = db.Column(db.String(225))
    config_type = db.Column(db.String(225))
    flag = db.Column(db.Integer)

    def __init__(self, server, database):
        self.server = server
        self.database = database

    def __repr__(self):
        return '<ServerConfig %r>' % self.server

#API Routes
@app.route('/api/getServerConfig', methods=['GET'])
def getServerConfig():
    serverConfigs = ServerConfig.query.all()
    output = []
    for serverconfig in serverConfigs:
        serverConfigData = {}
        serverConfigData['id'] = serverconfig.id
        serverConfigData['config_name'] = serverconfig.config_name
        serverConfigData['config_value'] = serverconfig.config_value
        serverConfigData['config_type'] = serverconfig.config_type
        serverConfigData['flag'] = serverconfig.flag
        output.append(serverConfigData)
    return jsonify({'serverConfigs': output})

@app.route('/api/initWebScraper', methods=['GET'])
def webScrapper():
    
    links = main()
    
    output = []
    for url in links:
        urlData = {}
        urlData['url'] = url
        output.append(urlData)
        
    return jsonify({
        'message': 'Web Scraper Initialized!',
        'links': output
    })



if __name__ == '__main__':
    app.run(debug=True)


