from flask import Flask, request, jsonify, render_template
from types import SimpleNamespace
from utils.async_ai import Agent
from utils.tools import tools
from openai import OpenAI
from utils import logger
import configparser
import requests
import colorama
import logging
import openai
import json
import time
import sys
import os

colorama.init()
resend = False
conf = configparser.ConfigParser()
conf.read('config.ini')

working_directory = os.path.dirname(os.path.abspath(__file__))

log = logging.getLogger('werkzeug')
log.level = logging.ERROR
log.disabled = True
log = logging.getLogger('flask_web_server_daemon')
log.level = logging.ERROR
log.disabled = True

sys.path.append(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), os.pardir))
log = logger.Logger('api', log_level=logger.Logger.INFO)

tool_data = {}
agent = Agent(name_prefix='ai')


def load_tools():
    # Iterate the tools folder and import all tools
    files = os.listdir(os.path.join(working_directory, 'tools'))
    for file in files:
        if file.endswith('.py'):
            tool = file[:-3]
            if tool not in tools:
                __import__(f'tools.{tool}')
                tool_data[tool] = {
                    'name': tool.replace('_', ' ').title(),
                    'key': tool,
                    'description': tools[tool]['schema']['description'],
                    'schema': tools[tool]['schema'],
                    'active': False
                }
                log.info(f'Loaded tool {tool}')


app = Flask(__name__)


def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


with open('secrets.json') as f:
    secrets = json.load(f)
    f.close()


client = OpenAI()

prompt = """
You are the AI assistant. The assistant is helpful, creative, clever, and very friendly.
"""
msg = []


def add_message(queue, role, content):
    queue.append({
        "role": role,
        "content": content
    })


def print_tokens(response):
    usage = response.usage
    log.data('===========TOKENS===========')
    if usage.total_tokens <= 2000:
        log.data(f'Used {usage.total_tokens} tokens.')
    elif usage.total_tokens <= 3000:
        log.warn(f'Used {usage.total_tokens} tokens.')
    elif usage.total_tokens <= 3500:
        log.error(f'Used {usage.total_tokens} tokens.')
        log.info('Clearing chat history')
        clear()


def get_active_tools():
    active_tools = [value['schema']
                    for key, value in tool_data.items() if value['active']]
    return active_tools


def process_query(query, m, agent, resend=False):
    funcs = get_active_tools()
    if not resend:
        m.append({'role': 'user', 'content': query})
    response = agent.get_response(msg, functions=funcs, temperature=0.6)
    print(response)
    tokens = response['tokens']
    response = response['text']
    if response.content and response.content != None:
        m.append({'role': 'assistant', 'content': response.content})
    if response.function_call:
        key = response.function_call.name
        args = response.function_call.arguments
        if response.content and response.content != None:
            m.append(response.content)

        if type(args) != dict:
            try:
                args = json.loads(args)
            except:
                args = {}
        responses = tools[key]['function'](args)
        for i, res in enumerate(responses):
            print(f'Processing response {i + 1} of {len(responses)}')
            print(f'Response: {res}')
            if 'content' in res and res['content'] != None:
                m.append(res)
            if i < len(responses) - 1:
                pass
            if 'resend' in res:
                m[-1].pop('resend', None)
                # New data has been added to the message list, so we need to resend it to OpenAI with the new data
                m = process_query(query, m, agent, resend=True)
    token_limit = conf.getint('ai', 'token_limit')
    if tokens.total_tokens > token_limit:
        m.append({'role': 'system', 'content': f'Token limit exceeded.  to conserve information please now summarize the above conversation and respond with the notes in as few tokens as possible.  Use various techniques to compress as much information into the response as possible as you will not see the information after this message.'})
        response = agent.get_response(msg, functions=funcs, temperature=0.6)
        m = reset_prompt()
        m.append({'role': 'user', 'content': response['text']})
    return m


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    global msg
    print(request.form['input'])
    transcription = request.form['input']
    if not transcription or transcription == '':
        return jsonify({"error": "No transcription provided."}), 400
    msg = process_query(transcription, msg, agent)
    return render_template('msglist.html', msglist=msg), 200


@app.route('/get_chat', methods=['GET'])
def get_history():
    global msg
    return render_template('msglist.html', msglist=msg)


@app.route('/clear_chat', methods=['POST'])
def reset_prompt():
    global msg
    msg = []
    add_message(msg, 'system', prompt)
    return {"response": "Cleared"}, 200


@app.route('/get_tools', methods=['GET'])
def get_tools():
    global tool_data
    return render_template('tools.html', tools=tool_data), 200


@app.route('/toggle_tool/<tool>', methods=['POST'])
def toggle_tool(tool):
    global tool_data
    if tool in tool_data:
        tool_data[tool]['active'] = not tool_data[tool]['active']
        if tool_data[tool]['active']:
            log.info(f'Activated tool {tool}')
        else:
            log.info(f'Deactivated tool {tool}')
        return render_template('tools.html', tools=tool_data), 200


if __name__ == "__main__":
    log.info('API started.')
    load_tools()
    add_message(msg, 'system', prompt)
    app.run(port=5000)
