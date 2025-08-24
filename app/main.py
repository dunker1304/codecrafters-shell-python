import sys
import os
import subprocess
from pathlib import Path

list_buildin_cmd = ['exit', 'echo', 'type', 'pwd', 'cd']

def find_executable(command):
    path_env = os.environ.get('PATH', '')
    for d in path_env.split(':'):
        if not d:
            continue
        candidate = os.path.join(d, command)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None                

def parse_command_line(input_line):
    args = []
    current_arg = ""
    in_single_quote = False
    in_double_quote = False

    for char in input_line:
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == ' ' and not in_double_quote and not in_single_quote:
            if current_arg:
                args.append(current_arg)
                current_arg = ""
        else:
            current_arg += char

    if current_arg:
        args.append(current_arg)

    return args

def main():
    # Uncomment this block to pass the first stage
    while True:
        sys.stdout.write("$ ")

        # Wait for user input
        input_line = input()
        if input_line == "":
            continue

        command_with_args = parse_command_line(input_line)
        command = command_with_args[0]

        match command:
            case "exit":
                break
            case "echo":
                print(" ".join(command_with_args[1:]))
            case "type":
                if len(command_with_args) < 2:
                    continue

                query = command_with_args[1]
                if query in list_buildin_cmd:
                    print(f"{query} is a shell builtin")
                else:
                    executable_path = find_executable(query)
                    if executable_path:
                        print(f"{query} is {executable_path}")
                    else:
                        print(f"{query} not found") 

            case "pwd":
                print(os.getcwd())

            case "cd":
                try:
                    if len(command_with_args) < 2:
                        os.chdir(Path.home())
                        continue
                    
                    if command_with_args[1] == '~':
                        os.chdir(Path.home())
                        continue

                    os.chdir(command_with_args[1])
                except Exception as e:
                    print(f"cd: {command_with_args[1]}: No such file or directory")

            case _:
                executable_path = find_executable(command)
                if executable_path:
                    try:
                        # [executable_path] + command_with_args[1:],
                        result = subprocess.run(
                            command_with_args,
                            capture_output=True,
                            text=True,
                            timeout=20
                        )

                        if result.stdout:
                            print(result.stdout, end='')
                        
                        if result.stderr:
                            print(result.stderr, end='')

                        if result.returncode != 0:
                            sys.exit(result.returncode)

                    except subprocess.TimeoutExpired:
                        print(f"{command}: command time out")
                    except Exception as e:
                        print(f"{command}: execution failed: {e}")
                else:
                    print(f"{command}: command not found")
        

if __name__ == "__main__":
    main()
