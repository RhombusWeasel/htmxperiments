from functools import wraps

tools = {}

def new_tool(name, schema):
  '''
  Decorator to register a new tool.

  :param name:   The name of the tool.
  :type  name:   STR
  :param schema: The JSON schema of the tool.
  :type  schema: DICT

  https://platform.openai.com/docs/guides/gpt/function-calling

  :return: The decorated function.
  '''
  def decorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
      return function(*args, **kwargs)

    tools[name] = {
      'schema': schema,
      'function': wrapper
    }
    return wrapper
  return decorator