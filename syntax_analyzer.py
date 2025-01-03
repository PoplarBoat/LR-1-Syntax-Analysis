import pickle

from exp import get_tokens
from tqdm import tqdm

from semantic_calculating import shift_in,semantic_computing,Unit

LeftPart=str                 #产生式左部 是一个非终结符
RightPart=(tuple[str],int)   #产生式右部 形如(('E','+','F'),0)
item_set_number = -1
def get_item_set_number():
    global item_set_number
    item_set_number = item_set_number + 1
    return item_set_number

class Item:
    def __init__(self,left_part:LeftPart,right_part:RightPart,index:int,look_ahead:str):
        self.left_part=left_part
        self.right_part=right_part
        self.index=index
        self.look_ahead=look_ahead
        if index > len(right_part[0]):
            raise IndexError(f"Index out of range in item{left_part}->{right_part},index:{index}")
    def get_next(self):
        """
        如果是归约项目，返回1和None，如果是非归约项目，返回0和下一个符号
        :return:
        """
        if self.index ==len(self.right_part[0]):
            return 1,None
        return 0,self.right_part[0][self.index]
    def is_start(self):
        """
        判断是否为起始项目
        :return:
        """
        if self.index==0:
            return True
        return False
    def is_end(self):
        """
        判断是否为规约项目
        :return:
        """
        if self.index==len(self.right_part):
            return True
        return False
    def get_after_next(self):
        """
        获得项目在当前index之后的所有符号，包括向前搜索符号
        :return:
        """
        result=[]
        flag,next_one=self.get_next()
        if flag==1:
            result.append(self.look_ahead)
        else:
            for i in range(self.index+1,len(self.right_part[0])):
                result.append(self.right_part[0][i])
            result.append(self.look_ahead)
        return result
    def __repr__(self):
        result=''
        result+=f"{self.left_part} --> "
        for i in range(len(self.right_part[0])):
            if self.index==i:
                result+="· "
            result+=f"{self.right_part[0][i]} "
        if self.index==len(self.right_part[0]):
            result+="· "
        result+=f',{self.look_ahead}\n'

        return result
    def __eq__(self, other):
        if self.__repr__()==other.__repr__():
            return True
        return False
    def __hash__(self):
        return hash((self.index,self.look_ahead,self.right_part[1]))

class SyntaxAnalyzer:
    def __init__(self,grammar_filename:str):
        self.lr_analysis_table = dict[int,dict[str,str]]()
        self.DFA = None
        self.grammar_filename = grammar_filename
        self.v=set()
        self.v_n=set()
        self.v_t=set()
        self.productions=list[dict[str,list[str]]]()
        self.production_dict=dict[LeftPart,list[RightPart]]()
        self._get_productions()
        self._get_vn_and_vt()
        self.first_set=dict[str,set[str]]()
        self.nullable=dict[str,bool]()
        self.get_nullable()
        self.init_first_set()

        self.transitions=dict[int,dict[str,int]]() # 状态转移表
        self.item_set_dict=dict[int, set[Item]]() # 状态号和项目集的对应

    def _get_productions(self):
        with open(self.grammar_filename,'r') as g:
            productions=g.readlines()
        print("正在从文件中读入文法产生式...")
        for production in tqdm(productions):
            if production == '\n':
                continue
            right = production.split(':')[1].strip().split(' ')
            left = production.split(':')[0].strip()
            #print(f"{left} --> {right}")
            if left not in self.production_dict.keys():
                self.production_dict[left]=[]
            self.productions.append({left:right})
        print(self.productions)
    def _get_vn_and_vt(self):
        print("正在提取非终结符...")
        for item in tqdm(self.productions):
            for key in item.keys():
                if key not in self.production_dict.keys():
                    self.production_dict[key]=[]
                self.production_dict[key].append((tuple(item[key]),self.productions.index(item)))
                self.v_n.add(key)
                self.v.add(key)
        #print(self.v_n)
        print("正在提取终结符...")
        for item in tqdm(self.productions):
            for value in item.values():
                for c in value:
                    self.v.add(c)
        self.v_t=self.v-self.v_n
        #print(self.v_t)
        print("提取字符集完成")
    def get_nullable(self):
        # 先把所有直接可空的找出来
        # 首先所有非终结符不可空
        for t in self.v_t:
            self.nullable[t]=False
        # 能直接推导出空串的可空
        for nt in self.v_n:
            right_list = self.production_dict[nt]
            self.nullable[nt]=False
            for right in right_list:
                produce = right[0]
                if len(produce)==1 and produce[0] == '$':
                    self.nullable[nt]=True
        while True:
            now_sum = sum(self.nullable.values())
            for nt in self.v_n:
                # 如果已经可空，直接continue
                if self.nullable[nt]:
                    continue
                # 否则考察每一个产生式
                isnull = True
                for right in self.production_dict[nt]:
                    produce = right[0]
                    # 考察每一个符号
                    for char in produce:
                        # 如果有一个不可空，直接跳出来,考察下一个产生式
                        if not self.nullable[char]:
                            isnull=False
                            break
                # 更新状态
                self.nullable[nt]=isnull
            change = now_sum - sum(self.nullable.values())
            #print(self.nullable)
            if change==0:
                break
    def __get_first_set(self, cur_status, all_elem,related:dict[str,set[str]]):
        """if cur_status in self.first_set:
            return self.first_set[cur_status]"""
        if cur_status in self.first_set:
            return self.first_set[cur_status]
        all_elem.add(cur_status)
        cur_status_set = set()
        for right_list in self.production_dict[cur_status]:
            for right in right_list[0]:
                right_set = None
                # 记录和当前计算的符号相关的非终结符
                if right in self.v_n:
                    related[cur_status].add(right)
                # 防止无限递归，如果当前右部的最左符号在前文的递归内容中，需要跳出来，考察下一个产生式
                if right in all_elem:

                    if self.nullable[right]:
                        continue
                    break
                # 如果该产生式已经被计算了，添加到该产生式右部的集合中
                if right in self.first_set:
                    right_set = self.first_set[right]
                # 否则计算该符号的first集合
                else:
                    right_set = self.__get_first_set(right, all_elem,related)
                cur_status_set |= right_set
                if '$' not in right_set:
                    break
        return cur_status_set
    def init_first_set(self):
        print("正在计算终结符的first集")
        for t in tqdm(self.v_t):
            self.first_set[t] = {t}
        related_set = dict[str,set[str]]()
        print("正在计算非终结符的first集")
        for key in self.v_n:
            related_set[key] = set[str]()
        for nt in tqdm(self.v_n):
            self.first_set[nt] = self.__get_first_set(
                nt, set(), related_set)
            if not self.nullable[nt]:
                if '$' in self.first_set[nt]:
                    self.first_set[nt].remove('$')
        # 前面的计算可能不全，接下里进行first集合的合并
        # 用所有first集合的长度和，刻画是否first集合是否嗐发生变化
        changed = sum([len(item) for item in  self.first_set.values()])
        print("迭代更新first集合")
        i=1
        while True:
            # 遍历每个非终结符号
            print(f"第{i}轮:")
            i+=1
            for nt in tqdm(self.v_n):
                related = related_set[nt]
                for related_nt in related:
                    for char in self.first_set[related_nt]:
                        self.first_set[nt].add(char)
            # 计算changed,如果，没有变化，就是0
            changed = changed - sum([len(item) for item in  self.first_set.values()])
            if changed == 0:
                break
        print("算得first集合如下")
        for key, value in self.first_set.items():
            print(f"{key}的first集合如下：")
            print(value)
        #print("算的相关集合如下")
        #print(related_set)
    def closure(self,I : set[Item]):
        v_n = self.v_n
        v_t = self.v_t
        v = self.v
        result = set[Item]()
        old_set = set[Item]()
        for item in I:
            result.add(item)

        length = len(result)
        while True:
            old_set=result.copy()
            for item in old_set:
                result.add(item)
                code,next_char = item.get_next()
                # 取出所有产生式
                if next_char in v_n:
                    # 找到所有可能的向前搜索符号
                    look_ahead_set = set[str]()
                    after_next_char = item.get_after_next()
                    for char in after_next_char:
                        if char == '#':
                            look_ahead_set.add(char)
                            break
                        # 把char的first集合加入向前搜索集合，除了'$'
                        look_ahead_set|=(self.first_set[char]-{'$'})
                        if not self.nullable[char]:
                            break
                    productions = self.production_dict[next_char]
                    for production in productions:
                        for look_ahead in look_ahead_set:
                            new_item = Item(left_part=next_char,right_part=production,index=0,look_ahead=look_ahead)
                            result.add(new_item)

            if len(old_set) < len(result):
                continue
            else:
                break
        return result
    def go(self,I:set[Item],char:str):
        new_set = set[Item]()
        for item in I:
            code,next_char = item.get_next()
            if next_char==char:
                # 右移
                transited=Item(left_part=item.left_part,
                               right_part=item.right_part,
                               index=item.index+1,
                               look_ahead=item.look_ahead)
                new_set.add(transited)

        return self.closure(new_set)
    def calculating_item_set(self):
        # 初始化入口集合
        I0 = self.closure(self.get_start_item_set())
        print(f'入口为\n{I0}')
        number=get_item_set_number()
        self.item_set_dict[number]=I0
        new = self.item_set_dict.copy()

        i = 1
        while True:
            print(f'第{i}轮转移与闭包')
            i+=1
            old = new.copy()
            new.clear()
            for key,item_set in tqdm(old.items()):
                # 找到所有可能的转移符号
                next_char_list=[]
                for item in item_set:
                    code,char = item.get_next()
                    if code == 0:
                        next_char_list.append(char)
                # 对每一个转移符号进行go操作
                for char in next_char_list:
                    new_item_set = self.go(item_set,char)
                    target = -1
                    if len(new_item_set) <= 0:
                        continue
                    # 如果new_item_set已经存在于项目集列表,target为其编号
                    if new_item_set in self.item_set_dict.values():
                        for num,val in self.item_set_dict.items():
                            if new_item_set == val:
                                target = num
                                break
                    # 否则target是新编号，并加入状态机和
                    else:
                        target = get_item_set_number()
                        self.item_set_dict[target]=new_item_set
                        new.update({target:new_item_set})
                    # 更新transition
                    if key not in self.transitions.keys():
                        self.transitions[key]=dict[str,int]()
                    self.transitions[key][char]=target
            if len(new)==0:
                break
        return
    def get_start_item_set(self):
        for left in self.production_dict.keys():
            if left =='Start':
                production = self.production_dict[left]
                item = Item(left_part=left,right_part=production[0],index=0,look_ahead='#')
                return set[item]([item])

        return None
    def display_item_set(self):
        for key,value in self.item_set_dict.items():
            print(f"I{key}:\n")
            for item in value:
                print(item)
    def get_lr_analysis_table(self):
        """
        构造lr分析表
        :return:
        """
        # 按照项目集顺序来构造
        cnt=0
        for state,item_set in self.item_set_dict.items():
            if state not in self.transitions.keys():
                self.transitions[state]=dict[str,int]()
            # 取出state的所有可能转移方式
            transition_dict =self.transitions[state]
            # 如果state的分析表还没被构造，先初始化
            if state not in self.lr_analysis_table.keys():
                self.lr_analysis_table[state]=dict[str,str]()
            # 对每个项目进行考察

            for item in item_set:

                # 如果该项目可以acc
                if item.left_part == 'Start':
                    print(cnt)
                    cnt += 1
                    if item.index == len(item.right_part[0]):
                        if item.look_ahead == '#':
                            if '#' in self.lr_analysis_table[state].keys():
                                print("发生冲突，需要调整文法")
                            self.lr_analysis_table[state]['#']='acc'
                            continue
                # 如果该项目是归约项目，S : A a · ,look_ahead
                if item.index ==len(item.right_part[0]):
                    print(cnt)
                    cnt += 1
                    produce_number = item.right_part[1]
                    if item.look_ahead in self.lr_analysis_table[state].keys():
                        print("发生冲突，需要调整文法")
                    # 置action[state,look_ahead]=r{produce_number}
                    self.lr_analysis_table[state][item.look_ahead]=f"r{produce_number}"
                    continue
                # 如果是已经规约的项目
                code,next_char = item.get_next()
                if next_char in self.v_n:
                    print(cnt)
                    cnt += 1
                    target=self.transitions[state][next_char]
                    if next_char in self.lr_analysis_table[state].keys():
                        print("发生冲突，需要调整文法")
                    self.lr_analysis_table[state][next_char]=f"g{target}"
                    continue


                # 如果是移进项目
                code,next_char = item.get_next()
                # 没有到达最末部分
                if item.index < len(item.right_part[0]):
                    if next_char in self.v_t:
                        print(cnt)
                        cnt += 1
                        target = self.transitions[state][next_char]
                        if next_char in self.lr_analysis_table[state].keys():
                            print("发生冲突，需要调整文法")
                        self.lr_analysis_table[state][next_char]=f"s{target}"
                        continue

        for key,value in self.lr_analysis_table.items():
            print(f"状态{key}的转移表")
            print(value)
    def analysis(self,tokens:list[list]):
        symbol_stack=['#']
        state_stack=[0]
        semantic_stack=[Unit('start','_',False)]
        tac=list[list]()
        idx =0
        analysis_table=self.lr_analysis_table
        cnt = 1
        while idx<len(tokens):
            print(f"\n\n==========第{cnt}轮操作=========")
            cnt += 1
            print(f"读入第{idx}个字符,{tokens[idx]}：")
            print(f"符号栈:{symbol_stack}")
            print(f"状态栈:{state_stack}")
            now_tk=tokens[idx][0]
            now_st=state_stack[-1]
            try:
                action = analysis_table[now_st][now_tk]
            except KeyError:
                print(f"语法分析发生错误，在第{idx+1}个单词处出错！")
                return
            if action=='acc':
                print(f"语法分析成功，源代码可以为文法所接受！")
                break
            elif action[0]=='s':
                # 移进操作
                print(f"动作：移进操作，将符号{tokens[idx]}移进，将状态{int(action[1:])}移进。")
                symbol_stack.append(now_tk)
                state_stack.append(int(action[1:]))
                shift_in(semantic_stack,tokens[idx])
                idx+=1

                continue
            elif action[0]=='r':
                # 规约操作

                produce_number=int(action[1:])
                print(f"动作：归约，使用第{produce_number}条产生式归约。")
                production = self.productions[produce_number]

                for key,value in production.items():
                    print(f"使用产生式{key} --> {value} 归约。")
                    beta=len(value)
                    for i in range(beta):
                        try:
                            symbol_stack.pop()
                            state_stack.pop()
                        except IndexError:
                            print(f"语法分析发生错误，在第{idx+1}个单词处出错！")
                            return
                    now_st = state_stack[-1]
                    symbol_stack.append(key)
                    try:
                        next_state = int(analysis_table[now_st][key][1:])
                        state_stack.append(next_state)
                    except KeyError:
                        print(f"语法分析发生错误，在第{idx+1}个单词处出错！")
                        return
                    semantic_computing(semantic_stack, tac, produce_number, self.productions)
            else:
                raise ValueError("分析表中出现异常字符，请检查")
        cnt=0
        for i in tac:
            print(f'{cnt} : {tuple(i)}')
            cnt+=1




if __name__=="__main__":
#    grammar_filename="test_grammar.txt"
#    syntax_analyzer=SyntaxAnalyzer(grammar_filename)
#    syntax_analyzer.calculating_item_set()
#    syntax_analyzer.display_item_set()
#    syntax_analyzer.get_lr_analysis_table()
    # 将对象序列化到文件
#    with open("./syntax_analyzer.pkl", "wb") as file:
#        pickle.dump(syntax_analyzer, file)
# 反序列化读取数据
    with open('syntax_analyzer.pkl', 'rb') as file:
        syntax_analyzer = pickle.load(file)

    analysis_table=syntax_analyzer.lr_analysis_table
    print(f"分析表共有{len(analysis_table)}个状态，如下")
    print(f"state\tlookahead\taction")
    for start,value in syntax_analyzer.lr_analysis_table.items():
        for lookahead,action in value.items():
            print(f"{start}\t\t{lookahead}\t\t{action}")
    while True:
        string = input("是否分析code.txt中的程序：")
        if string=='exit':
            exit(0)
        else:
            tokens = get_tokens()
            tokens.append('#')
            print(tokens)
            syntax_analyzer.analysis(tokens)
"""    item = Item('A',['A','B','d','C'],3,look_ahead='#')
    print(item.get_next())
    print(item.get_after_next())
    print(syntax_analyzer.get_start_item())"""


