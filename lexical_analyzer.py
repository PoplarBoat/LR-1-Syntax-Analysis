class LexicalAnalyzer:
    def __init__(self,filename:str):
        with open(filename,'r',encoding='utf-8') as f:
            self.text = f.read()
        self.tokens = []
    def divide(self):
        text = self.text
        tokens = []
        token = []
        i=0
        while i < len(text):
            cur = text[i]

            # 如果为空，保存当前token
            if cur == ' ' or cur == '\n':
                if len(token) > 0:
                    tokens.append(''.join(token))
                    token = []
                i+=1
                continue

            # 如果为界符
            if cur in [';','{','}','[',']','(',')']:
                if token:
                    tokens.append(''.join(token))
                    token = []
                tokens.append(cur)
                i+=1
                continue

            # 如果为算术运算符
            if cur in ['+','-','*','/']:
                if token:
                    tokens.append(''.join(token))
                    token = []
                tokens.append(cur)
                i+=1
                continue

            # 如果为比较运算符或取反运算符
            if cur in ['<','>','!','=']:
                if token:
                    tokens.append(''.join(token))
                    token = []
                # 向前查看一个单位
                if i != len(text) - 1:
                    # 如果发现是等于运算符
                    if text[i + 1] == '=':
                        tokens.append('==')
                        i+=2
                    else:
                        tokens.append(cur)
                        i+=1

                    continue
                else:
                    tokens.append(cur)
                    i+=1
                    continue

            # 如果为逻辑运算符
            if cur in ['&','|']:
                if token:
                    tokens.append(''.join(token))
                    token = []
                if i==len(text) - 1:
                    raise ValueError(f"词法分析阶段：第{len(tokens)}词附近出现错误,{cur}是非法的")
                else:
                    if text[i+1] != cur:
                        raise ValueError(f"词法分析阶段：第{len(tokens)}词附近出现错误,{cur}是非法的")
                    tokens.append(cur+cur)
                    i+=2
                    continue

            token.append(cur)
            i+=1
        self.tokens=tokens.copy()
        result=[]
        for tk in tokens:
            if tk.isdigit():
                result.append((tk))




if __name__ == '__main__':
    lexical_analyzer = LexicalAnalyzer('code.txt')
    lexical_analyzer.divide()
    for token in lexical_analyzer.tokens:
        print(token)