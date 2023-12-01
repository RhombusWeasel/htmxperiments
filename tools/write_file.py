from utils.logger import Logger
from utils.tools import new_tool
import configparser

logger = Logger('tool_write')
conf = configparser.ConfigParser()
conf.read('config.ini')
working_directory = conf.get('term', 'working_directory')

@new_tool('write_file', {
  'name': 'write_file',
  'description': 'Writes to a file.',
  'parameters': {
    'type': 'object',
    'properties': {
      'file': {
        'type': 'string',
        'description': 'The path to the file to write to.',
      },
      'content': {
        'type': 'string',
        'description': 'The content to write to the file.',
      }
    },
    'required': ['file', 'content']
  }
})
def write_file(data):
  with open(working_directory +'/'+ data['file'], 'w') as f:
    f.write(data['content'])
  return [{'role': 'system', 'content': f'Wrote to file: {data["file"]}'}]