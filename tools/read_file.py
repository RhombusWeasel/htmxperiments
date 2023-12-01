from utils.tools import new_tool
from utils.logger import Logger
import configparser
import os

logger = Logger('tool_read')
conf = configparser.ConfigParser()
conf.read('config.ini')

@new_tool('read_file', {
    'name': 'read_file',
    'description': 'Reads a file.',
    'parameters': {
      'type': 'object',
      'properties': {
        'file': {
          'type': 'string',
          'description': 'The path to the file to read.',
        }
      },
      'required': ['file']
    }
  }
)
def read_file(file):
  working_directory = conf.get('term', 'working_directory')
  path = os.path.join(working_directory, file['file'])
  try:
    with open(path, 'r') as f:
      content = f.read()
    return [{'role': 'system', 'content': content}]
  except Exception as e:
    logger.error(e)
    return [{'role': 'system', 'content': f'Error: {e}'}]