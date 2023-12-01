from utils.tools import new_tool
from utils.logger import Logger
import requests

logger = Logger('tool_browse')

@new_tool('browse', {
    'name': 'browse',
    'description': 'Reads the full contents of a website verbatim.',
    'parameters': {
      'type': 'object',
      'properties': {
        'url': {
          'type': 'string',
          'description': 'The URL of the website to browse.',
        }
      },
      'required': ['url']
    }
  }
)
def browse(data):
  url = data['url']
  try:
    response = requests.get(url)
    content = response.text
    return [{'role': 'system', 'content': content}]
  except Exception as e:
    logger.error(e)
    return [{'role': 'system', 'content': f'Error: {e}'}]