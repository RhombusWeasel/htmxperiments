from utils.tools import new_tool
from utils.logger import Logger
from utils.memory_client import MemoryClient
from utils.async_ai import Agent
import configparser
import json

logger = Logger('mem_archive')
conf = configparser.ConfigParser()

agent_prompt = """You are the memory archive assistant.
Your role is to maintain the memory archive and ensure consistency.
Each entry in the archive is a JSON string describing a particular collection of data.
The data is tagged with a set of tags that describe the data's context to the user and the system.
Your task is to ensure that the archive is kept up to date and that the data is accurate.
Does any new information you see need a new category adding or is it to be included in an existing category?
Take a deep breath, let's work through the problem down step by step.

Review the below information against the archive data provided.
If it is new information you should add it to the archive with a descriptive set of tags using mem_add.
If it is a modification you should update the existing information with mem_modify, ensure the tags are current and contextually accurate.
If it is a duplicate you should call mem_ignore.
"""

tools = [
  {
    'name': 'mem_new',
    'description': "Add new data to the memory archive",
    'parameters': {
      'type': 'object',
      'properties': {
        'data': {
          'type': 'string',
          'description': 'The memory to add as a JSON formatted string.',
        }
      },
      'required': ['data']
    }
  },
  {
    'name': 'mem_modify',
    'description': "Modify existing data in the memory archive",
    'parameters': {
      'type': 'object',
      'properties': {
        'uuid': {
          'type': 'integer',
          'description': 'The uuid of the memory to modify.',
        },
        'data': {
          'type': 'string',
          'description': 'The modified data to be written as JSON. This data overwrites the existing archive data completely, it does not append to it.',
        },
      },
      'required': ['uuid', 'data']
    }
  },
  {
    'name': 'mem_ignore',
    'description': "Ignore the data and do nothing.",
    'parameters': {
      'type': 'object',
      'properties': {
        'msg': {
          'type': 'string',
          'description': 'short sentence stating why the memory is safe to ignore.',
        },
      },
      'required': ['msg']
    }
  },
]

@new_tool('mem_archive', {
    'name': 'mem_archive',
    'description': "If the user or system specifically requests it add data to the archive.",
    'parameters': {
      'type': 'object',
      'properties': {
        'tags': { 'type': 'array', 'items': { 'type': 'string' }, 'description': 'The list of tags to add to the data, be descriptive and include multiple tags.' },
        'data': { 'type': 'string', 'description': 'The data to archive, the archivist does not see the conversation, you must pass all the relevant data to them.' },
        'instructions': { 'type': 'string', 'description': 'The instructions for the archivist agent, what should it do with the data you provide?' }
      },
      'required': ['tags', 'data', 'instructions']
    }
  }
)
def mem_archive(data):
  conf.read('config.ini')
  base_url = conf.get('memory', 'base_url')
  client = MemoryClient(base_url)
  client.login()
  # print('Checking data against archive...')
  tags = f'{" ".join(data["tags"])}'
  results = client.search('terminal-assistant', tags)
  # print(results)
  agent = Agent(print_tokens=False, log_level=logger.DEBUG, model='gpt-3.5-turbo-16k')
  m = [
    {"role": "system", "content": agent_prompt},
    {"role": "system", "content": """Here are the tags that were searched to get the archive data:\n\n['mother', 'date of birth']\n\nHere are the top 2 results from our search of the provided tags:\n\n[{'distance': 0.7682497501373291, 'uuid': 1, 'text': '{"tags": ["family", "parents", "siblings"], "mother": {"name": "Hazel", "location": "Yorkshire, England", "birthday": "August 24th, 1964", "interests": ["knitting", "reading", "cooking"]}, "father": {"name": "James", "location": "Yorkshire, England", "birthday": "January 15th, 1960", "interests": ["gardening", "60\'s, 70\'s and 80\'s music", "the outdoors"]}}'}, {'distance': 1.0330601930618286, 'uuid': 2, 'text': '{"tags": ["food", "recipes", "cooking"], "favourites": {"breakfast": "eggs and bacon", "lunch": "a sandwich", "dinner": "steak with peppercorn sauce", "dessert": "creme brulee"}}'}]\n\nHere is the new information for you to review:\n\n"Mothers Birthday is 24th August 1963"\n\nInstructions provided:\n\nAdd updated date of birth\nDoes the new information need to be merged with one of the existing objects or is it completely unrelated?\nCall the correct function to complete the task."""},
    {
      "role": "assistant",
      "content": "Updated date of birth information for mother.",
      "function_call": {
        "name": "mem_modify",
        "arguments": """{"uuid": 1, "data": {"tags": ["family", "parents", "siblings"], "mother": {"name": "Hazel", "location": "Yorkshire, England", "birthday": "August 24th, 1963", "interests": ["knitting", "reading", "cooking"]}, "father": {"name": "James", "location": "Yorkshire, England", "birthday": "January 15th, 1960", "interests": ["gardening", "60's, 70's and 80's music", "the outdoors"]}}}"""
      },
    },
    {"role": "system", "content": f"Here are the tags that were searched to get the archive data:\n\n{data['tags']}\n\nHere are the top 2 results from our search of the provided tags:\n\n{results}\n\nHere is the new information for you to review:\n\n{data['data']}\n\nInstructions provided:\n\n{data['instructions']}\nDoes the new information need to be merged with one of the existing objects or is it completely unrelated?\nCall the correct function to complete the task."}
  ]
  # print('getting response...')
  response = agent.get_response(m, functions=tools)['text']
  # print(response)
  if 'function_call' in response:
    print(response['function_call'])
    args = json.loads(response['function_call']['arguments'])
    if response['function_call']['name'] == 'mem_new':
      client.add_text_if_unique('terminal-assistant', response['function_call']['arguments'])
    if response['function_call']['name'] == 'mem_modify':
      try:
        store_data = json.dumps(args['data'])
      except:
        store_data = args['data']
      client.modify_entry('terminal-assistant', int(args['uuid']), store_data)
    return [{'role': 'system', 'content': 'Memory updated.'}]
  else:
    return [{'role': 'system', 'content': 'Memory already present.'}]