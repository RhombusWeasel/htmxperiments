import json
import re


def remove_text_outside_braces(text):
  start = text.find('{')
  end = text.rfind('}')
  if start == -1 or end == -1:
    return text
  else:
    return text[start:end+1]


def correct_json_string(json_string):
  # Remove any text outside if the {} braces
  json_string = remove_text_outside_braces(json_string)

  # Remove any codeblocks Jarvis may be trying to read aloud.
  json_string = re.sub(r'```[\s\S]*?```', '', json_string)

  # Remove comments (single and multi-line)
  json_string = re.sub(r'(\/\/.*\n|\/\*[\s\S]*?\*\/)', '', json_string)

  # Remove single-line comments (Python)
  no_single_line_comments = re.sub(r'(?m)^\s*#.*$', '', json_string)

  # Remove multi-line comments (Python)
  no_comments = re.sub(r'(\'\'\'[\s\S]*?\'\'\'|\"\"\"[\s\S]*?\"\"\")', '', no_single_line_comments)

  # Replace single quotes with double quotes, but not inside double-quoted strings
  json_string = re.sub(r'(?<!\\)(\'|")((?:\\\\|\\[^\\]|[^\\"])*)(?<!\\)(\'|")', lambda m: '"' + m.group(2).replace('"', r'\"') + '"', json_string)

  # Remove trailing commas after the last item in an array or object
  json_string = re.sub(r',(\s*[}\]])', r'\1', json_string)

  # Remove leading/trailing whitespaces and newlines
  json_string = json_string.strip()

  return json_string


def parse_json_string(json_string):
	try:
		return json.loads(json_string)
	except json.JSONDecodeError:
		corrected_json_string = correct_json_string(remove_text_outside_braces(json_string))
		try:
			return json.loads(corrected_json_string)
		except json.JSONDecodeError:
			raise ValueError("The input string could not be corrected to a valid JSON format")