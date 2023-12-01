from utils.tools import new_tool
from utils.logger import Logger
import configparser
from utils.memory_client import MemoryClient

logger = Logger('mem_search')
conf = configparser.ConfigParser()

description = """Searches your vector database for information matching the query.
The results will be provided to you as a system message.
returns the top result from memory along with the uuid.
"""

@new_tool('mem_search', {
    'name': 'mem_search',
    'description': description,
    'parameters': {
      'type': 'object',
      'properties': {
        'query': {
          'type': 'string',
          'description': 'The query to search for.',
        }
      },
      'required': ['query']
    }
  }
)
def mem_search(query):
  conf.read('config.ini')
  base_url = conf.get('memory', 'base_url')
  from utils.memory_client import MemoryClient
  client = MemoryClient(base_url)
  client.login()
  response = client.search('terminal-assistant', query)
  data = {
    'uuid': response[0]['uuid'],
    'data': response[0]['text'],
  }
  return [
    {
      'role': 'system',
      'content': f"""MEMORY SEARCH RESULTS:\nThe information you recall is below.\n{data}\nCan you use this information to answer the user's question?""",
      'resend': True
    }
  ]