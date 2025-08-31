import sys
import os
import subprocess
from pathlib import Path
import readline

list_buildin_cmd = ['exit', 'echo', 'type', 'pwd', 'cd']

def get_executables_in_path():
    executables = set()
    path_env = os.environ.get('PATH', '')

    for directory in path_env.split(':'):
        if not directory or not os.path.isdir(directory):
            continue

        try:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath) and os.access(filepath, os.X_OK):
                    executables.add(filename)
        except (OSError, PermissionError):
            continue

    return list(executables)

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
    i = 0

    while i < len(input_line):
        char = input_line[i]

        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == "\\":
            if not in_double_quote and not in_single_quote:
                if i + 1 < len(input_line):
                    current_arg += input_line[i+1]
                    i += 1        
            else:
                if i + 1 < len(input_line):
                    if input_line[i+1] == '\\' or (input_line[i+1] == '"' and not in_single_quote):
                        current_arg += input_line[i+1]
                        i += 1
                    else:
                        current_arg += char
        elif char == ' ' and not in_double_quote and not in_single_quote:
            if current_arg:
                args.append(current_arg)
                current_arg = ""
        else:
            current_arg += char

        i += 1

    if current_arg:
        args.append(current_arg)

    return args

def extract_stdout_redirection(args):
    if len(args) < 2:
        return args, None, None, False
    
    cleaned = []
    stdout_path = None
    stderr_path = None
    append = False
    i = 0

    while i < len(args):
        token = args[i]
        if token in ('>', '1>'):
            if i + 1 < len(args):
                stdout_path = args[i + 1]
                i += 2
                continue
            else:
                # No filename provided; ignore malformed redirection
                i += 1
                continue

        if token == '2>':
            if i + 1 < len(args):
                stderr_path = args[i + 1]
                i += 2
                continue

            i += 1
            continue

        if token in ('>>', '1>>'):
            if i + 1 < len(args):
                stdout_path = args[i + 1]
                append = True
                i += 2
                continue
            
            i += 1
            continue

        if token == '2>>':
            if i + 1 < len(args):
                stderr_path = args[i + 1]
                append = True
                i += 2
                continue
            
            i += 1
            continue

        # support form like '>file' and '1>file'
        if token.startswith('>') and len(token) > 1:
            stdout_path = token[1:]
            i += 1
            continue
        if token.startswith('1>') and len(token) > 2:
            stdout_path = token[2:]
            i += 1
            continue
        if token.startswith('2>') and len(token) > 2:
            stderr_path = token[2:]
            i += 1
            continue
        
        cleaned.append(token)
        i += 1

    return cleaned, stdout_path, stderr_path, append

def cprint(text, file=None, append=False):
    mode = 'w' if not append else 'a'
    try:
        if file:
            with open(file, mode) as f:
                f.write(text)
        else:
            print(text)
    except Exception as e:
        print(f"Error: {e}")

def completer(text, state):
    builtin_options = [cmd for cmd in list_buildin_cmd if cmd.startswith(text)]
    external_options = []
    if text:
        executables = get_executables_in_path()
        external_options = [exe for exe in executables if exe.startswith(text)]

    all_options = builtin_options + external_options

    if state < len(all_options):
        return all_options[state] + ' '
    return None

def main():
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

    while True:
        sys.stdout.write("$ ")

        # Wait for user input
        input_line = input()
        if input_line == "":
            continue

        command_with_args = parse_command_line(input_line)
        command = command_with_args[0]
        command_with_args, stdout_redirect, stderr_redirect, append = extract_stdout_redirection(command_with_args)

        # Create/truncate redirection targets up front so files exist even if nothing is written
        mode = 'w' if not append else 'a'
        if stdout_redirect:
            try:
                open(stdout_redirect, mode).close()
            except Exception:
                pass
        if stderr_redirect:
            try:
                open(stderr_redirect, mode).close()
            except Exception:
                pass

        match command:
            case "exit":
                break
            case "echo":
                if stdout_redirect:
                    cprint(" ".join(command_with_args[1:]) + "\n", stdout_redirect, append)
                else:
                    cprint(" ".join(command_with_args[1:]))
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
                            if stdout_redirect:
                                cprint(result.stdout, stdout_redirect, append)
                            else:
                                print(result.stdout, end='')
                        
                        if result.stderr:
                            if stderr_redirect:
                                cprint(result.stderr, stderr_redirect, append)
                            else:
                                print(result.stderr, end='')

                        # if result.returncode != 0:
                        #     sys.exit(result.returncode)

                    except subprocess.TimeoutExpired:
                        print(f"{command}: command time out")
                    except Exception as e:
                        print(f"{command}: execution failed: {e}")
                else:
                    print(f"{command}: command not found")
        

if __name__ == "__main__":
    main()
