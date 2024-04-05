from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS,cross_origin
from webScraper import main
from openai import OpenAI
import os
from os.path import join, dirname
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
app = Flask(__name__)
CORS(app)
csrf = CSRFProtect(app)
csrf.init_app(app)

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
    
class Chat(db.Model):
    chat_id = db.Column(db.BigInteger, primary_key=True)
    chat_sender_id = db.Column(db.Integer)
    chat_body = db.Column(db.Text)
    chat_role = db.Column(db.String(225))
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.now())
    
    def __init__(self, chat_sender_id, chat_body, chat_role):
        self.chat_sender_id = chat_sender_id
        self.chat_body = chat_body
        self.chat_role = chat_role
        

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

@csrf.exempt
@app.route('/api/chat/sendMessage', methods=['POST'])
def sendMessage():
    chatgpt_api_key = ServerConfig.query.filter_by(config_name='chatgpt_api_key').first()
    client = OpenAI(
        api_key=chatgpt_api_key,
    )
    data = request.get_json()
    
    # Check if data is None or if required keys are missing
    if data is None or 'chat_sender_id' not in data or 'chat_body' not in data:
        return jsonify({
            'headers': {
                "responseCode": 200,
                "responseMessage": "Missing key parameters"
            },
            'response': []
        })

    # If data is not None and required keys are present
    chat = Chat(
        chat_sender_id=data['chat_sender_id'], 
        chat_body=data['chat_body'], 
        chat_role='user'
    )

    db.session.add(chat)
    db.session.commit()

    # Fetch messages for the chat_sender_id
    messageList = []
    chats = Chat.query.filter_by(chat_sender_id=data['chat_sender_id']).all()
    
    for chat in chats:
        messageData = {}
        messageData['role'] = chat.chat_role
        messageData['content'] = chat.chat_body
        messageList.append(messageData)

    # If no messages were retrieved, return a failure response
    if not messageList:
        return jsonify({
            'headers': {
                "responseCode": 200,
                "responseMessage": "Failed"
            },
            'response': {}
        })
    else:
        # Generate completion using OpenAI model
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messageList
        )

        # Prepare and store the response message
        if completion.choices:
            sendMessage = Chat(
                chat_sender_id=data['chat_sender_id'],
                chat_body=completion.choices[0].message.content,
                chat_role=completion.choices[0].message.role
            )

            db.session.add(sendMessage)
            db.session.commit()

            return jsonify({
                'headers': {
                    "responseCode": 200,
                    "responseMessage": "Success"
                },
                'response': {}
            })
        else:
            return jsonify({
                'headers': {
                    "responseCode": 200,
                    "responseMessage": "Failed"
                },
                'response': {}
            })

@csrf.exempt
@app.route('/api/chat/getMessages', methods=['GET'])
def getMessage():
    output = []
    request_data = request.args
    if not request_data: return jsonify({
            'headers': {
                "responseCode": 200,
                "responseMessage": "Missing key parameters"
            },
            'response': output
        })
    else: chat = Chat.query.filter_by(chat_sender_id=request_data['chat_sender_id']).all()
    for chat in chat:
        chatData = {}
        chatData['chat_id'] = chat.chat_id
        chatData['chat_sender_id'] = chat.chat_sender_id
        chatData['chat_body'] = chat.chat_body
        chatData['chat_role'] = chat.chat_role
        chatData['timestamp'] = chat.timestamp
        output.append(chatData)
    return jsonify(
        {
            'headers': {
                "responseCode": 200,
                "responseMessage": "Success"
            },
            'response': output
        }
    )
    
    

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


