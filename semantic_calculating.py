semantic_map=dict()

cur_label = -1

# 语义信息，只包括类型、值和是否可变
class Unit:
    def __init__(self,name:str,value,variable:bool):
        self.name=name
        self.value=value
        self.variable=variable

start_stack=list[int] ()
judge_stack=list[int] ()
brk_stack=list[int] ()
ctn_stack=list[int] ()

variable_table=dict[str,bool]()


def get_new_label():
    global cur_label
    cur_label += 1
    return cur_label

name=-1
def get_new_name():
    global name
    name += 1
    return f'T{name}'

# 移进一个符号时候，应该做的操作
def shift_in(semantic_stack:list,symbol:list[str]):
    global cur_label
    if symbol[0] =='do':
        # 记录当前到达的label，加入循环开始栈
        global start_stack
        global judge_stack
        global brk_stack
        global ctn_stack
        ctn_stack.append(0)
        brk_stack.append(0)
        judge_stack.append(-1)
        start_stack.append(cur_label+1)
        # 语义栈操作
        do_unit=Unit('do',cur_label+1,False)
        semantic_stack.append(do_unit)
    elif symbol[0] =='while':
        # 记录当前循环的判断开始地址，加入判断开始栈
        judge_stack[len(judge_stack)-1]=cur_label
        # 语义栈操作
        while_unit=Unit('while',cur_label,False)
        semantic_stack.append(while_unit)
    elif symbol[0] == 'id':
        # 记录当前的id，语义栈操作
        id_unit=Unit('id',symbol[1],True)
        semantic_stack.append(id_unit)
    elif symbol[0] == 'value':
        # 把value推进语义栈
        value_unit=Unit('value',symbol[1],False)
        semantic_stack.append(value_unit)
    else:
        unit = Unit(symbol[0],symbol[1],False)
        semantic_stack.append(unit)
# 以下是变量定义语句相关的语义操作
# 用Vdu:id = R					为id创建一个符号，并且把R的值给id，语义为id的名称
def declare_with_value(semantic_stack : list[Unit],tac : list[list]):
    """
    声明的时候同时初始化
    :param tac:
    :param semantic_stack:
    :return:
    """
    # 取出第二操作数
    operand=semantic_stack.pop()
    number2=operand.value

    # 取出操作符
    semantic_stack.pop()

    # 取出被声明的变量名
    variable_name=semantic_stack.pop().value
    operator='declare'

    # 产生式左侧的语义信息压栈
    semantic_stack.append(Unit('Vdu',variable_name,True))

    # 加到符号表
    global variable_table
    variable_table[variable_name] = True

    # 返回四元式，操作符、-、值、变量名
    cur = get_new_label()
    tac.append([operator, '_', number2, variable_name])

    return [operator, '_', number2, variable_name]
# 用Vdu:id						为id创建一个符号，没有初始化的值，语义为id的名称
def declare_without_value(semantic_stack : list[Unit],tac : list[list]):
    """
    声明的时候同时,不初始化
    :param tac:
    :param semantic_stack:
    :return:
    """
    # 取出左操作数
    operand = semantic_stack.pop()

    variable_name = operand.value

    # 加到符号表
    global variable_table
    variable_table[variable_name] = True

    # 语义信息压栈
    semantic_stack.append(Unit('Vdu',variable_name,True))

    # 返回四元式，操作符、-、值、变量名
    cur = get_new_label()
    tac.append(['declare', '_', '_', variable_name])
    return ['declare', '_', '_', variable_name]
# 以下是表达式相关的语义操作
# 形如A : B / C
def binary_operating(semantic_stack : list,tac : list[list]):
    """
    双目运算归约的时候生成四元式的操作
    :param tac:
    :param semantic_stack: 语义栈
    :return:
    """
    # 取出第二个操作数
    operand2=semantic_stack.pop()
    number2=operand2.value

    # 取出运算符
    operator=semantic_stack.pop().value

    # 取出第一个操作数
    operand1=semantic_stack.pop()
    number1=operand1.value

    if operator == '=':
        if not operand1.variable:
            print(f"提示:赋值表达式必须具有可以修改的左值！")

    # 创建语义信息单元
    new_name = get_new_name()
    unit = Unit('id',new_name,operand1.variable and operand2.variable)
    semantic_stack.append(unit)

    # 新标志
    cur = get_new_label()
    # 四元式：操作符、操作数1、操作数2、变量名
    tac.append([operator, number1, number2,new_name])
    return [operator, number1, number2,new_name]
# 形如A : ! A
def unary_operating(semantic_stack : list,tac : list[list]):
    """
    单目运算被规约的时候，生成四元式的操作
    :param tac:
    :param semantic_stack:
    :return:
    """
    # 弹出操作数
    operand=semantic_stack.pop()
    number=operand.value

    # 弹出操作符
    operator=semantic_stack.pop().value

    # 添加新的语法单元
    new_name = get_new_name()
    unit = Unit('id',operand.value,False)
    semantic_stack.append(unit)

    #生成四元式
    cur = get_new_label()
    tac.append([operator, '_' , number, new_name])
    return [operator, '_' , number, new_name]
# 形如A : ( E )
def parentheses_operating(semantic_stack : list,tac : list[list]):
    """
    括号运算被归约的时候，生成四元式的操作
    :param tac:
    :param semantic_stack:
    :return:
    """
    operator='='

    # 取出括号2
    semantic_stack.pop()

    # 取出表达式
    operand=semantic_stack.pop()

    # 取出括号1
    semantic_stack.pop()


    # 新的语义单元
    new_name = get_new_name()
    unit = Unit('id',new_name,operand.variable)
    semantic_stack.append(unit)

    # 生成四元式
    cur = get_new_label()
    tac.append([operator, '_' , operand.value, new_name])
    return [operator , '_', operand.value , new_name]
# 形如 A : E
def copy_operating(semantic_stack : list,tac : list[list]):
    """
    为了优先级定义而设定的产生式被归约的时候生成的四元式，其实是冗余的，后续可以考虑删除！
    :param tac:
    :param semantic_stack:
    :return:
    """
    # 取出右值
    operand=semantic_stack.pop()
    op='='

    # 添加新的语义单元

    unit = Unit('id',operand.value,operand.variable)
    semantic_stack.append(unit)

    # 生成四元式
    #cur = get_new_label()
    #tac.append([op , '_', operand, new_name])
    #return [op , '_', operand, new_name]
# 以下和循环相关操作
# 循环语句被归约的时候 Dw : do { Dwblk } while ( R )
def on_dw_reducing(semantic_stack : list[Unit],tac : list[list]):
    # )
    semantic_stack.pop()
    # R
    R = semantic_stack.pop()
    # (
    semantic_stack.pop()
    # while
    while_unit=semantic_stack.pop()
    # { Dwblk }
    semantic_stack.pop()
    semantic_stack.pop()
    semantic_stack.pop()
    # do
    do_unit=semantic_stack.pop()

    global start_stack
    start=start_stack.pop()

    # 新的四元式，如果R为True，转到start
    cur = get_new_label()
    new_tac=['JT','_',R.value,start]
    tac.append(new_tac)

    # 回填brk的跳转地，是cur+1
    global brk_stack
    brk_count=brk_stack.pop()
    cnt=0
    # 从后往前遍历
    for i in range(len(tac)-1,-1,-1):
        if tac[i][0]=='brk':
            tac[i][3]=cur+1
            cnt+=1
        if cnt==brk_count:
            break

    # 回填continue的跳转地，是while_unit的value
    global judge_stack
    judge_stack.pop()
    global ctn_stack
    ctn_count=ctn_stack.pop()
    cnt=0
    for i in range(len(tac)-1,-1,-1):
        if tac[i][0]=='ctn':
            tac[i][3]=while_unit.value
            cnt+=1
        if cnt==ctn_count:
            break

    # 新的语义信息入栈
    unit = Unit('Dw','Dw',False)
    semantic_stack.append(unit)

    return new_tac
# 形如Dwst: break ;的产生式归约
def on_break_reducing(semantic_stack : list[Unit],tac : list[list]):
    # 弹栈两次
    semantic_stack.pop()
    semantic_stack.pop()

    # 新的tac
    new_tac = ['brk','_','_',-1]
    tac.append(new_tac)

    # 多一次break
    global brk_stack
    brk_stack[-1]+=1

    semantic_stack.append(Unit('Dwst','Dwst',False))
    cur = get_new_label()

    return ['brk','_','_',-1]
# 形如Dwst: continue ;的产生式归约
def on_continue_reducing(semantic_stack : list[Unit],tac : list[list]):
    # 弹栈两次
    semantic_stack.pop()
    semantic_stack.pop()

    # 新的tac
    new_tac = ['ctn','_','_',-1]
    tac.append(new_tac)

    # 多一次continue
    global ctn_stack
    ctn_stack[-1]+=1

    cur = get_new_label()

    semantic_stack.append(Unit('Dwst','Dwst',False))

    return ['ctn','_','_',-1]
# 以下是整个程序归约完毕语义动作 Start : S
def finish(semantic_stack : list[Unit],tac : list[list]):
    # 弹栈
    semantic_stack.pop()

    cur = get_new_label()

    # 新tac
    new_tac = ['end','_','_','_']
    tac.append(new_tac)

    # 新语义压栈
    semantic_stack.append(Unit('end','end',False))

    return ['end','_','_','_']
# 分析完毕的语义动作
semantic_map[0]=finish
# 带初始化的声明的语义动作
semantic_map[10]=declare_with_value
# 不带初始化的声明的语义动作
semantic_map[11]=declare_without_value
# 双目运算符的语义动作绑定
for i in [21,23,25,27,28,29,30,31,32,34,35,37,38]:
    semantic_map[i]=binary_operating
# 单目运算符绑定
for i in [40]:
    semantic_map[i]=unary_operating
# 括号运算符的绑定
for i in [42]:
    semantic_map[i]=parentheses_operating
# 复制操作的绑定
for i in [22,24,26,33,36,39,41,43,44]:
    semantic_map[i]=copy_operating
# 循环语句被归约的时候 Dw : do { Dwblk } while ( R )的语义动作的绑定
semantic_map[12]=on_dw_reducing
# break语句被归约
semantic_map[18]=on_break_reducing
# continue语句被归约
semantic_map[19]=on_continue_reducing
# 对外暴露的接口，传入产生式列表、语义栈和tac栈
def semantic_computing(semantic_stack : list[Unit],
                       tac : list[list],
                       production_number,
                       production_list):
    reducing=None
    try:
        reducing=semantic_map[production_number]
    except KeyError:
        a=1
    if reducing is not None:
        reducing(semantic_stack, tac)
    else:
        # 默认操作
        production=production_list[production_number]
        for key,value in production.items():
            for _ in range(len(value)):
                semantic_stack.pop()
            unit=Unit(key,key,False)
            semantic_stack.append(unit)

if __name__ == '__main__':
    print('a')