tokens_dict = {
    "var":"VAR",
    "do": "DO",
    "while": "WHILE",
    "break": "BREAK",
    "continue": "CONTINUE",
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "/",
    "<": "<",
    "<=": "<=",
    ">": ">",
    ">=": ">=",
    "==": "==",
    "!=": "!=",
    "=": "=",
    ";": ";",
    ",": ",",
    "(": "(",
    ")": ")",
    "[": "[",
    "]": "]",
    "{": "{",
    "}": "}",
    "!": "!",
    "&&":"and",
    "||":"or"
}


def save_to_list(tokens: list, token: str):
    if token.isdigit():
        tokens.append((token, 'INTEGER'))
    else:
        tokens.append((token, 'NOT_INTEGER'))


def read_file_to_tokens(filename: str):
    with open(filename, 'r') as file:
        tokens = []
        token = ""
        while True:
            char = file.read(1)
            if char == "":
                break

            # 处理空格和分界符号直接返回已读入的单词
            if char == ' ' or char == '\n':
                if token != '':
                    save_to_list(tokens, token)
                    token = ''
                continue

            # 字符常量
            if char == "'":
                if token != '':
                    save_to_list(tokens, token)
                    token = ''
                next_char = file.read(1)
                while next_char != '"':
                    token = token + next_char
                    next_char = file.read(1)
                if token != '':
                    token = token
                    tokens.append((token, 'VALUE'))
                    token = ''
                continue
            # 字符串常量
            if char == '"':
                if token != '':
                    save_to_list(tokens, token)
                    token = ''
                next_char = file.read(1)
                while next_char != '"':
                    token = token + next_char
                    next_char = file.read(1)
                if token != '':
                    token = token
                    tokens.append((token, 'VALUE'))
                    token = ''
                continue

            # 处理数字、字母和下划线
            if char.isdigit() or char.isalpha() or char == '_':
                token = token + char
                continue

            # 处理括号和分界符，直接把收集到的非空串添加到读取的tokens里
            elif char in {',', ';', '{', '}', '[', ']', '(', ')'}:
                if token != '':
                    save_to_list(tokens, token)
                tokens.append((char, 'NOT_INTEGER'))
                token = ''
                continue

            # 处理运算符
            elif char in {'>', '<', '=', '!'}:
                print(token)
                if token != '':
                    save_to_list(tokens, token)
                token = ''
                token = token + char

                print(token)
                # 检查下一个字符
                next_char = file.read(1)

                if next_char == '=':
                    # 如果是‘=’就视为一个字符
                    token = token + next_char
                    print(token)

                    tokens.append((token, 'NOT_INTEGER'))
                    token = ''
                else:
                    # 如果不是等于，就回退
                    print(token)

                    tokens.append((token, 'NOT_INTEGER'))
                    token = ''
                    file.seek(file.tell() - 1)
                continue

            elif char in {'+', '-', '*', '/'}:
                if token != '':
                    tokens.append((token, 'NOT_INTEGER'))
                tokens.append((char, 'NOT_INTEGER'))
                token = ''
                continue

            elif char in {'&','|'}:
                if token != '':
                    tokens.append((token, 'NOT_INTEGER'))
                token = char
                next_char = file.read(1)
                if next_char!=char:
                    raise ValueError(f"invalid character {char} in {filename}")
                else:
                    token+=char
                    tokens.append((token, 'NOT_INTEGER'))
                    token = ''
                    continue

            else:
                print(tokens)
                raise Exception(f"invalid character after {tokens[-1]}.")

        return tokens


def lexical_analysis(tokens: list, dictionary: dict):
    analysed = []
    for token in tokens:
        tk = token[0]
        tp = token[1]
        if tp == 'INTEGER':
            analysed.append(f'VALUE {tk}')
        elif tp == 'STRING':
            analysed.append(f'VALUE {tk}')
        elif tp == 'CHAR':
            analysed.append(f'VALUE {tk}')
        else:
            try:
                analysed.append(f'{dictionary[tk]} {tk}')
            except Exception:
                analysed.append(f'ID {tk}')
    return analysed

def get_tokens():
    result = read_file_to_tokens('./code.txt')
    result = lexical_analysis(result,tokens_dict)
    tokens = []
    for r in result:
        rr=r.split(' ')
        tokens.append((rr[0].lower(),rr[1]))
    return tokens


if __name__ == '__main__':
    result = read_file_to_tokens('./code.txt')
    result = lexical_analysis(result,tokens_dict)

    print(get_tokens())