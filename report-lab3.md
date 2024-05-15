# 编译实验3报告

## 小组成员及分工
#### 刘可盈：
完成'iget','iget-wide','iget-object','iget-boolean','iget-byte','iget-char','iget-short','iget-volatile','iget-wide-volatile','iget-object-volatile','iput','iput-wide','iput-object','iput-boolean','iput-byte','iput-char','iput-short','iput-volatile','iput-wide-volatile','iput-object-volatile','sget','sget-wide','sget-object','sget-boolean','sget-byte','sget-char','sget-short','sget-volatile','sget-wide-volatile','sget-object-volatile','sput','sput-wide','sput-object','sput-boolean','sput-byte','sput-char','sput-short','sput-volatile','sput-wide-volatile','sput-object-volatile','invoke-constructor','invoke-custom','invoke-direct','invoke-direct-empty','invoke-instance','invoke-interface','invoke-polymorphic','invoke-static','invoke-super','invoke-virtual','invoke-custom/range','invoke-direct/range','invoke-interface/range','invoke-object-init/range','invoke-polymorphic/range','invoke-static/range','invoke-super/range','invoke-virtual/range','neg-int','not-int','neg-long','not-long','neg-float','neg-double','int-to-long','int-to-float','int-to-double','long-to-int','long-to-float','long-to-double','float-to-int','float-to-long','float-to-double','double-to-int','double-to-long','double-to-float','int-to-byte','int-to-char','int-to-short','add-int','sub-int','mul-int','div-int','rem-int','and-int','or-int','xor-int','shl-int','shr-int','ushr-int','add-long','sub-long','mul-long','div-long','rem-long','and-long','or-long','xor-long','shl-long','shr-long','ushr-long','add-float','sub-float','mul-float','div-float','rem-float','add-double','sub-double','mul-double','div-double','rem-double','add-int/2addr','sub-int/2addr','mul-int/2addr','div-int/2addr','rem-int/2addr','and-int/2addr','or-int/2addr','xor-int/2addr','shl-int/2addr','shr-int/2addr','ushr-int/2addr','add-long/2addr','sub-long/2addr','mul-long/2addr','div-long/2addr','rem-long/2addr','and-long/2addr','or-long/2addr','xor-long/2addr','shl-long/2addr','shr-long/2addr','ushr-long/2addr','add-float/2addr','sub-float/2addr','mul-float/2addr','div-float/2addr','rem-float/2addr','add-double/2addr','sub-double/2addr','mul-double/2addr','div-double/2addr','rem-double/2addr','add-int/lit16','sub-int/lit16','mul-int/lit16','div-int/lit16','rem-int/lit16','and-int/lit16','or-int/lit16','xor-int/lit16','add-int/lit8','sub-int/lit8','mul-int/lit8','div-int/lit8','rem-int/lit8','and-int/lit8','or-int/lit8','xor-int/lit8','shl-int/lit8','shr-int/lit8','ushr-int/lit8','static-get','static-put','instance-get','instance-put','execute-inline','execute-inline/range','iget-quick','iget-wide-quick','iget-object-quick','iput-quick','iput-wide-quick','iput-object-quick','iput-boolean-quick','iput-byte-quick','iput-char-quick','iput-short-quick','invoke-virtual-quick','invoke-virtual-quick/range','invoke-super-quick','invoke-super-quick/range','rsub-int','rsub-int/lit8'的解析
#### 韩偲蔚：
完成'nop','move','move/from16','move/16','move-wide','move-wide/from16','move-wide/16','move-object','move-object/from16','move-object/16','move-result','move-result-wide''move-result-object','move-exception','return-void','return','return-wide','return-object','const/4','const/16','const','const/high16','const-wide/16','const-wide/32','const-wide','const-wide/high16','const-string','const-string/jumbo','const-class','const-method-handle','const-method-type','monitor-enter','monitor-exit','check-cast','instance-of','array-length','new-instance','new-array','filled-new-array','filled-new-array/range','fill-array-data','throw','throw-verification-error','goto','goto/16','goto/32','packed-switch','sparse-switch','cmpl-float','cmpg-float','cmpl-double','cmpg-double','cmp-long','if-eq','if-ne','if-lt','if-ge','if-gt','if-le','if-eqz','if-nez','if-ltz','if-gez','if-gtz','if-lez','aget','aget-wide','aget-object','aget-boolean','aget-byte','aget-char','aget-short','aput','aput-wide','aput-object','aput-boolean','aput-byte','aput-char','aput-short'的解析

## 实验思路

由于smali中expression只有唯一一种格式：
```javascript
expression: $ => seq(
    $.opcode,
    commaSep($.value),
    '\n',
),
```
我们便直接根据不同类型的opcode命令设计对应的转换策略。
```python
def check_expression_handler(self, node):
    EXPRESSION_HANDLER_MAP = {
        "expression": self.primary_expression
    }

    return EXPRESSION_HANDLER_MAP.get(node.type, None)

def primary_expression(self, node, statements):
    opcode = self.find_child_by_type(node, "opcode")
    shadow_opcode = self.read_node_text(opcode)
    ···
    if shadow_opcode == "nop":
        ···
    elif re.compile(r'^move.*').match(shadow_opcode):
        ···
    ···
```
此外我们起初准备将所有类型的value在一开始便保存到一个values的字典中，但由于value的类型过多，在一开始全部分类反而过于冗杂，因此对于常见一些类型'variable', 'parameter', 'number', 'string', 'float', 'character', 'identifier', 'list', 'body', 'class_identifier'进行了预先分类，其余仍使用find_child/children函数。预先分类代码如下：
```python
type_list = ['variable', 'parameter', 'number', 'string', 'float', 'character', 'identifier', 'list', 'body', 'class_identifier']

def primary_expression(self, node, statements):
    ···
    values = {}
    for type in type_list:
        values[type] = []
    for type in type_list:
        values[type].extend(self.find_children_by_type(node, type))
    ···
```

## 核心代码
#### nop
    不进行任何操作，`return `

#### move类
    move命令中  'move'，'move/from16'，'move/16'，'move-wide'，'move-wide/from16'，'move-wide/16'，'move-object'，'move-object/from16'，'move-object/16'与assignment指令相似，格式为move vA, vB，作用是将vB寄存器的值赋给vA寄存器。
    转换核心代码为：
    ```python
    v0 = self.read_node_text(values["variable"][0])
    v1 = self.read_node_text(values["variable"][1])
    statements.append({"assign_stmt": {"target": v0, "operand": v1}})
    return v0
    ```
    此外还有'move-result'类和'move-exception'命令，它们分别是将上一个invoke类型指令操作的结果赋给寄存器和保存一个运行时发生的异常到vAA寄存器。我们设定invoke指令运行结果储存到‘tmp_return’中，运行异常被储存到‘tmp_exception’中，两者皆为全局变量。
    ```python
    // result
    v0 = self.read_node_text(values["variable"][0])
    statements.append({"assign_stmt": {"target": v0, "operand": tmp_return, "operator": "result"}})

    //exception
    v0 = self.read_node_text(values["variable"][0])
    statements.append({"assign_stmt": {"target": v0, "operand": tmp_exception, "operator": "exception"}})
    ```

#### return类
    包含'return-void'，'return'，'return-wide'，'return-object'，'return-void'后无参数，其余指令为return vA形式，核心代码如下：
    ```python
    if "void" in shadow_opcode:
        statements.append({"return_stmt": {"target": ''}})
        return ''
    else:
        v0 = self.read_node_text(values["variable"][0])
        statements.append({"return_stmt": {"target": v0}})
        return v0
    ```

#### const类
    包含const类、const-string类、const-class和const-method类。const类是将数字常量赋值给寄存器，const-string类是将字符串常量存入到寄存器，const-class为将类的引用赋值给寄存器，指令格式均为const vA B。由于无法找到与const-method相关的资料，暂时忽略这一指令。核心代码如下：
    ```python
    v0 = self.read_node_text(values["variable"][0])
    if 'string' in shadow_opcode:
        string = self.find_child_by_type(values["string"][0], 'string_fragment')
        shadow_string = self.read_node_text(string)
        statements.append({"assign_stmt": {"target": v0, "operand": shadow_string}})
    elif 'class' in shadow_opcode: 
        class_identifier = values['class_identifier'][0]
        shadow_class = self.read_node_text(class_identifier)
        statements.append({"assign_stmt": {"target": v0, "operand": shadow_class}})
    else:
        number = values["number"][0]
        shadow_number = self.read_node_text(number)
        statements.append({"assign_stmt": {"target": v0, "operand": shadow_number}})
    return v0
    ```

#### monitor类
    'monitor-enter'，'monitor-exit'分别为获取锁和释放锁，由于glang不支持该指令，忽略。

#### check-cast
    指令格式为check-cast vA, 类型ID，作用为检查vA寄存器中的对象引用是否可以转换成类型ID对应类型的实例。如不可转换，抛出ClassCastException 异常，否则继续执行。由于glang不支持该指令，暂且用assignment指令取代。核心代码如下：
    ```python
    v0 = self.read_node_text(values["variable"][0])
    class_identifier = values['class_identifier'][0]
    shadow_class = self.read_node_text(class_identifier)
    statements.append({"assign_stmt": {"target": v0, "operand": shadow_class, "operator": "check-cast"}})
    return v0
    ```

#### instance-of
    指令格式为instance-of vA, vB,类型ID，作用是检查vB寄存器中的对象引用是否是类型ID对应类型的实例，如果是，vA存入非0值，否则vA存入0。由于glang中不支持检查类型的指令，暂且用assignment指令取代，并假设如果能转换则返回非0值，否则返回0。核心代码如下：
    ```python
    v1 = self.read_node_text(values["variable"][1])
    v2 = self.parse(values[2], statements)
    tmp_var = self.tmp_variable(statements)
    statements.append({"assign_stmt":
                            {"target": tmp_var, "operator": "instanceof", "operand": v1,
                            "operand2": v2}})
    v0 = self.read_node_text(values["variable"][0])
    statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
    return v0
    ```

#### array-length
    指令格式为array-length vA, vB，作用是计算vB寄存器中数组引用的元素长度并将长度存入vA。由于glang中不支持该指令，暂且用assignment指令取代。
    ```python
    v0 = self.read_node_text(values["variable"][0])
    v1 = self.read_node_text(values["variable"][1])
    statements.append({"assign_stmt": {"target": v0, "operand": v1, "operator": "array-length"}})
    return v0
    ```

#### new类
    包含'new-instance'与'new-array'。
    'new-instance'指令格式为new-instance vA, 类型ID，作用是根据类型ID或类型新建一个对象实例，并将新建的对象的引用存入vA。代码如下：
    ```python
    glang_node = {}
    mytype = self.read_node_text(values['class_identifier'][0])
    glang_node["data_type"] = mytype
    tmp_var = self.tmp_variable(statements)
    glang_node["target"] = tmp_var
    statements.append({"new_instance": glang_node})
    v0 = self.read_node_text(values["variable"][0])
    statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
    return v0
    ```
    'new-array'指令格式为new-array vA, vB,类型ID，作用是根据类型ID或类型新建一个数组，vB存入数组的长度，vA存入数组的引用。代码如下：
    ```python
    type = self.read_node_text(self.find_child_by_type_type(node, "array_type", "primitive_type"))
    v0 = self.read_node_text(values["variable"][0])
    v1 = self.read_node_text(values["variable"][1])
    tmp_var = self.tmp_variable(statements)
    statements.append({"new_array": {"type": type, "target": tmp_var}})
    statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
    statements.append({"assign_stmt": {"target": v1, "operand": v0, "operator": "array-length"}})
    return tmp_var
    ```

#### fill类
    分为'filled-new-array'，'filled-new-array/range'和'fill-array-data'。
    filled-new-array的指令格式为filled-new-array {参数列表}, 类型ID，作用是根据类型ID或类型新建一个数组并通过参数填充。代码如下：
    ```python
    type = self.read_node_text(self.find_child_by_type_type(node, "array_type", "primitive_type"))
    list = self.find_child_by_type(node, "list")
    vs = self.find_children_by_type(list,"variable")
    tmp_var = self.tmp_variable(statements)
    statements.append({"new_array": {"type": type, "target": tmp_var}})
    for i in range(len(vs)):
        name = self.read_node_text(vs[i])
        statements.append({"assign_stmt": {"target": name, "operand": f'{tmp_var}[{i}]'}})
    return tmp_var
    ```
    filled-new-array/range的指令格式为filled-new-array-range {vA..vB}, 类型ID，作用是根据类型ID或类型新建一个数组并以寄存器范围为参数填充。代码如下：
    ```python
    type = self.read_node_text(self.find_child_by_type_type(node, "array_type", "primitive_type"))
    range_node = self.read_node_text(self.find_child_by_type(node,"range"))
    matches = re.findall(r'v(\d+)', range_node)
    tmp_var = self.tmp_variable(statements)
    statements.append({"new_array": {"type": type, "target": tmp_var}})
    for i in range(int(matches[0]),int(matches[1])+1):
        statements.append({"assign_stmt": {"target": f'v{i}', "operand": tmp_var, "operator": "filled-new-array/range"}})
    return tmp_var
    ```
    fill-array-data的指令格式为fill-array-data vA, 偏移量，作用是用标记处数据，赋值于vA寄存器，由于glang没有对应的标记语法，暂且用assignment取代，代码如下：
    ```python
    v0 = self.read_node_text(values["variable"][0])
    label = self.read_node_text(self.find_child_by_type(node, "label"))
    statements.append({"assign_stmt": {"target": v0, "operand": label, "operator": "fill-array-data"}})
    return v0
    ```

#### throw
    指令格式为throw vA， 作用是抛出异常对象，异常对象的引用在vA寄存器。代码如下：
    ```python
    shadow_expr = self.read_node_text(values["variable"][0])
    statements.append({"throw_stmt": {"target": shadow_expr}})
    return
    ```
#### goto类
    包含'goto'，'goto/16'，'goto/32'，指令格式为goto 目标，作用是无条件跳转到目标。代码如下：
    ```python
    label = self.read_node_text(self.find_child_by_type(node, "label"))
    statements.append({"goto": {"target": label}})
    return
    ```
#### switch类
    包含'packed-switch'，'sparse-switch'
    packed-switch格式为packed-switch vx, 索引表偏移量，作用是实现一个switch 语句，case常量是连续的。这个指令使用索引表，vx是在表中找到具体case的指令偏移量的索引，如果无法在表中找到vx对应的索引将继续执行下一个指令。
    sparse-switch格式为sparse-switch vx, 查询表偏移量，作用是实现一个switch 语句，case常量是非连续的。这个指令使用查询表，用于表示case常量和每个case常量的偏移量。如果vx无法在表中匹配将继续执行下一个指令。
    由于表达式中仅使用了跳转到表所在标签的操作，两者的代码一致，如下所示：
    ```python
    p0 = self.read_node_text(values["parameter"][0])
    label = self.read_node_text(self.find_child_by_type(node, "label"))
    statements.append({"assign_stmt": {"target": p0, "operand": label, "operator": "switch"}})
    return p0
    ```

#### cmp类
    包含'cmpl-float'，'cmpg-float'，'cmpl-double'，'cmpg-double'，'cmp-long'，指令格式是cmp vA, vB, vC，作用是比较vB和vC的值并在vA存入返回值。对于含l的指令，如果vB寄存器大于vC寄存器，结果为-1，相等则结果为0，小于的话结果为1，对于含g的指令和'cmp-long'，如果vB寄存器大于vC寄存器，结果为1，相等结果为0，小于的话结果为-1。
    由于glang中不含compare类语句，我们假定glang中存在一种compare_stmt语句，它有'target'，'operator'，'operand'，'oprand2'这四个属性，作用是根据operator比较operand和oprand2的大小，并将返回值存到target。operator分为'l'和'g'，对于'l'，如果operand大于oprand2，结果为-1，相等则结果为0，小于的话结果为1，对于'g'，如果operand大于oprand2，结果为1，相等结果为0，小于的话结果为-1。
    ```python
    v0 = self.read_node_text(values["variable"][0])
    v1 = self.read_node_text(values["variable"][1])
    v2 = self.read_node_text(values["variable"][2])
    tmp_var = self.tmp_variable(statements)
    if 'cmpl' in shadow_opcode:
        statements.append({"compare_stmt": {"target": tmp_var, "operator": 'l', "operand": v1,"operand2": v2}})
    else:
        statements.append({"compare_stmt": {"target": tmp_var, "operator": 'g', "operand": v1,"operand2": v2}})
    statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
    return v0
    ```

#### if类
    if分为两大类，if-op和if-opz。前者格式为if-op vA, vB, C，作用是根据op的要求将vA与vB进行比较判断，如果结果为真，则跳转到C位置。后者格式为if-op vA, C，作用时根据op的要求将vA与0进行比较判断，如果结果为真，则跳转到C位置。op分为'eq'，'ne'，'le'，'lt'，'ge'，'gt'，分别是相等、不等、小于等于、小于、大于等于、大于。由于glang的goto指令不含条件跳转功能，我们假定其有该功能，增加一个属性“condition”，如果condition是1则跳转，是0则不跳转。我们为上一条中设计的compare_stmt增加新的指令，当op为'eq'，'ne'，'le'，'lt'，'ge'，'gt'，分别对oprand和oprand2进行相等、不等、小于等于、小于、大于等于、大于的比较判断，结果为1或0写入target中。增添了以上功能后，转换代码如下：
    ```python
    op = re.search(r'if-(\w+)', shadow_opcode)
    v0 = self.read_node_text(values["variable"][0])
    if 'z' not in op:
        v1 = self.read_node_text(values["variable"][1])
    else:
        v1 = "0"
    tmp_var = self.tmp_variable(statements)
    statements.append({"compare_stmt": {"target": tmp_var, "operator": op, "operand": v0,"operand2": v1}})
    label = self.read_node_text(self.find_child_by_type(node, "label"))
    statements.append({"goto_stmt": {"target": label, "condition": tmp_var}})
    return 
    ```

#### aget类
    包含  'aget'，'aget-wide'，'aget-object'，'aget-boolean'，'aget-byte'，'aget-char'，'aget-short'，格式为aget vA, vB, vC，作用是从数组获取对于类型的值到vA，对象数组的引用位于vB，需获取的元素的索引位于vC。代码如下：
    ```python
    v0 = self.read_node_text(values["variable"][0])
    v1 = self.read_node_text(values["variable"][1])
    v2 = self.read_node_text(values["variable"][2])
    statements.append({"array_read": {"target": v0, "array": v1, "index": v2}})
    return v0
    ```

#### aput类
    包含  'aput'，'aput-wide'，'aput-object'，'aput-boolean'，'aput-byte'，'aput-char'，'aput-short'，格式为aput vA, vB, vC，作用是将vA的值按照类型存入数组，数组的引用位于vB，元素的索引位于vC。代码如下：
    ```python
    v0 = self.read_node_text(values["variable"][0])
    v1 = self.read_node_text(values["variable"][1])
    v2 = self.read_node_text(values["variable"][2])
    statements.append({"array_write": {"array": v1, "index": v2, "src": v0}})
    return v0
    ```

#### 二元运算（2地址）
指令格式为binop/2addr vA, vB  A: 目标寄存器和第一个源寄存器，B: 第二个源寄存器，含义是对两个源寄存器执行已确定的二元运算，并将结果存储到第一个源寄存器中。转换为assign_stmt，node的named_children[0]是opcode，对应operator。node.named_children[1]和node.named_children[2]分别对应2个operand。target是第一个源寄存器。
```Python
    def binary_expression_2addr(self, node, statements, op):
        dest = self.parse(node.named_children[1], statements)
        source = self.parse(node.named_children[2], statements)
        statements.append({"assign_stmt": {"target": dest, "operator": op, "operand": dest,"operand2": source}})
        return dest
```

#### 二元运算（3地址）
指令格式为binop vAA, vBB, vCC  A: 目标寄存器，B: 第一个源寄存器，C: 第二个源寄存器，含义是对两个源寄存器执行已确定的二元运算，并将结果存储到目标寄存器中。
或者binop/lit vA, vB, #+CCCC  A: 目标寄存器，B: 源寄存器，C: 有符号整数常量，含义是对指定的寄存器（第一个参数）和字面量值（第二个参数）执行指定的二元运算，并将结果存储到目标寄存器中。
转换为assign_stmt。node的named_children[0]是opcode，对应operator。node.named_children[1]对应target。node.named_children[2]和node.named_children[3]分别对应2个operand。
```Python
    def binary_expression(self, node, statements, op):
        dest = self.parse(node.named_children[1], statements)
        source1 = self.parse(node.named_children[2], statements)
        source2 = self.parse(node.named_children[3], statements)
        statements.append({"assign_stmt": {"target": dest, "operator": op, "operand": source1,"operand2": source2}})
        return dest
```

#### 一元运算
指令格式为unop vA, vB  A: 目标寄存器，B: 源寄存器，含义是对源寄存器执行已确定的一元运算，并将结果存储到目标寄存器中。转换为assign_stmt。node.named_children[1]对应target。node.named_children[2]对应operand
```Python
    def unary_expression(self, node, statements,op):
        dest = self.parse(node.named_children[1], statements)
        source = self.parse(node.named_children[2], statements)
        statements.append({"assign_stmt": {"target": dest, "operator": op, "operand": source}})
        return dest
```

#### 实例对象成员变量的取值和赋值
指令格式为iinstanceop vA, vB, field@CCCC  A: 值寄存器；可以是源寄存器，也可以是目标寄存器，B: 对象寄存器，C: 实例字段引用索引。对已标识的字段执行已确定的对象实例字段运算，并将结果加载或存储到值寄存器中。转换为field_write或field_read。node的node.named_children[1]在iput是source，在iget中是target。node.named_children[2]是receiver_object。node.named_children[3]的格式是class_identifier->field_identifier，其中的field_identifier作为glang的field。
```Python
    elif re.compile(r'^iput.*').match(shadow_opcode) or shadow_opcode=='instance-get': 
        source = self.parse(node.named_children[1], statements)
        receiver_object = self.parse(node.named_children[2], statements)
        field=self.find_child_by_type(node.named_children[3],"field_identifier")
        shadow_field=self.read_node_text(field)
        statements.append({"field_write": {"receiver_object": receiver_object, "field": shadow_field, "source": source}})
    elif re.compile(r'^iget.*').match(shadow_opcode) or shadow_opcode=='instance-get':
        target = self.parse(node.named_children[1], statements)
        receiver_object = self.parse(node.named_children[2], statements)
        field=self.find_child_by_type(node.named_children[3],"field_identifier")
        shadow_field=self.read_node_text(field)
        statements.append({"field_read": {"target": target, "receiver_object": receiver_object, "field": shadow_field}})
```

#### 静态对象成员变量的取值和赋值
指令格式为sstaticop vAA, field@BBBB  A: 值寄存器；可以是源寄存器，也可以是目标寄存器，B: 静态字段引用索引。对已标识的静态字段执行已确定的对象静态字段运算，并将结果加载或存储到值寄存器中。转换为field_write或field_read。node的node.named_children[1]在sput是source，在sget中是target。node.named_children[2]的格式是class_identifier->field_identifier，其中的field_identifier作为glang的field，class_identifier作为glang的receiver_object。
```Python
    elif re.compile(r'^sget.*').match(shadow_opcode) or shadow_opcode=='static-get':
        target = self.parse(node.named_children[1], statements)
        source = node.named_children[2]
        receiver_object = self.find_child_by_type(source,"class_identifier")
        shadow_receiver_object=self.read_node_text(receiver_object)
        field = self.find_child_by_type(source,"field_identifier")
        shadow_field = self.read_node_text(field)
        statements.append({"field_read": {"target": target, "receiver_object": shadow_receiver_object, "field": shadow_field}})
    elif re.compile(r'^sput.*').match(shadow_opcode) or shadow_opcode=='static-put':
        source = self.parse(node.named_children[1], statements)
        target = node.named_children[2]
        receiver_object = self.find_child_by_type(target,"class_identifier")
        shadow_receiver_object=self.read_node_text(receiver_object)
        field = self.find_child_by_type(target,"field_identifier")
        shadow_field = self.read_node_text(field)
        statements.append({"field_write": {"receiver_object": shadow_receiver_object, "field": shadow_field, "source": source}})
```

#### 函数调用
一般的指令格式为invoke-custom {vC, vD, vE, vF, vG}, call_site@BBBB B: 调用点引用索引，C..G: 参数寄存器（每个寄存器各占 4 位）
若参数较多时，指令格式为invoke-custom/range {vCCCC .. vNNNN}, call_site@BBBB
如果函数有原型，指令格式为invoke-polymorphic {vC, vD, vE, vF, vG}, meth@BBBB, proto@HHHH  H: 原型引用索引
转换为call_stmt。
node的named_children[1]是参数列表。如果opcode中有range，则先取到起始寄存器和中止寄存器，再把中间的寄存器还原出来并加入arg_list。如果非range，则直接取出args的child加入arg_list。node.named_children[2]对应函数及返回类型，从中取出class_name和method_identifier组成完整的函数名，再从中取出data_type。如果是invoke-polymorphic，则node.named_children[3]对应prototype。
```Python
elif re.compile(r'^invoke.*').match(shadow_opcode) or shadow_opcode=='execute-inline' or shadow_opcode=='excute-inline-range':
    tmp_return=self.tmp_variable(statements)
    args_list = []
    args=node.named_children[1]
    if 'range' in shadow_opcode:
        start=self.read_node_text(self.find_child_by_field(args,"start"))
        end=self.read_node_text(self.find_child_by_field(args,"end"))
        s=start[1:]
        e=end[1:]
        register_type=start[0]
        for arg_num in range(int(s), int(e)+1):
            arg=register_type+str(arg_num)
            args_list.append(arg)
    else: 
        if args.named_child_count > 0:
            for child in args.named_children:
                shadow_variable = self.parse(child, statements)
                if shadow_variable:
                    args_list.append(shadow_variable)
    function=self.find_child_by_type(node.named_children[2],"full_method_signature")
    method = self.find_child_by_type(function,"method_signature")
    class_type=self.read_node_text(function.named_children[0])
    method_name = self.read_node_text(self.find_child_by_type(method,"method_identifier"))
    data_type = self.read_node_text(method.named_children[2])
    if 'polymorphic' in shadow_opcode:
        prototype=self.read_node_text(node.named_children[3])
    else :
       prototype=""
    statements.append({"call_stmt": {"target": tmp_return, "name": class_type+'->'+method_name, "args": args_list,"data_type":data_type,"prototype":prototype}})
```

## 测试用例
```
.class public LHelloWorld;

.super Ljava/lang/Object;

.method public static main([Ljava/lang/String;)V
    .registers 2

    nop

    const/4 v0, 0x5 #数组长度赋值给v0寄存器
    new-array v0, v0, [I #创建指定类型[I即int数组，长度为v0即5，并将数组引用赋值于v0寄存器
    fill-array-data v0, :array_18 #用指定标记array_18处的数据填充数组
    iput-object v0, p0, Lcom/erlin/smali/SmaliParse;->intArray:[I #为数组赋值
    return-void

    const-string v1, "Hello World!"

    check-cast v1, Lcom/erlin/smali/SmaliParse$InnerClassExtends;
    instance-of v2, v0, Lcom/erlin/smali/SmaliParse$InnerClassExtends;

    const/4 v3, 0x3 #将0x3寄存给v3寄存器
    new-array v0, v3, [I #创建[I类型长度为v3寄存器数组，引用赋值给v0寄存器
    fill-array-data v0, :array_1a #用array_1a标记处数据，赋值于v0寄存器

    array-length v1, v0 #获取v0寄存器长度，赋值给v1寄存器
    new-array v2, v1, [Ljava/lang/String;

    const/4 v3, 0x0
    const-string v4, "A"
    aput-object v4, v2, v3 #v4寄存器值，赋值给v2寄存器数组，数组索引为v3

    invoke-virtual {v0, v1}, Ljava/util/Random;->nextInt(I)I
    move-result v0

    invoke-polymorphic {p1, v0, v1}, Ljava/lang/invoke/MethodHandle;->invoke([Ljava/lang/Object;)Ljava/lang/Object;, (II)V
    invoke-virtual/range {v0 .. v5}, Landroid/location/LocationManager;->requestLocationUpdates(Ljava/lang/String;JFLandroid/location/LocationListener;)V

    add-int v1,v2,v3
    sub-int/2addr v5,v6
    neg-long v6,v7
    int-to-double p8,p9
    add-int/lit16 v0, v1, 12345
    mul-int/lit16 v1, v2,10

    iput-boolean v0, p0, Lcom/disney/xx/XxActivity;->isRunning:Z
    sget-object v0, Lcom/disney/xx/XxActivity;->PREFS_INSTALLATION_ID:Ljava/lang/String;

    if-eqz v2, :cond_c

    packed-switch p1, :pswitch_data_c

    filled-new-array {v0,v1},[I
    filled-new-array/range {v19..v21}, [B
    
    :goto_7
    return-void

    :cond_8
    if-eq v0, v1, :cond_c

    add-int/2addr v1, v1

    goto :goto_7

    :cond_c
    return-void

    :array_18
    .array-data 4
        0x0
        0x1
        0x2
        0x3
        0x4
    .end array-data

    :pswitch_data_c
    .packed-switch 0x0
        :pswitch_6 #case 0
        :pswitch_9 #case 1
    .end packed-switch

.end method

```


## 测试结果
```bash
[{'assign_stmt': {'target': 'v0', 'operand': '0x5'}},
 {'new_array': {'type': 'I', 'attr': 'v0', 'target': '%v0'}},
 {'assign_stmt': {'target': 'v0', 'operand': '%v0'}},
 {'assign_stmt': {'target': 'v0',
                  'operand': ':array_18',
                  'operator': 'fill-array-data'}},
 {'field_write': {'receiver_object': 'p0',
                  'field': 'intArray',
                  'source': 'v0'}},
 {'return_stmt': {'target': ''}},
 {'assign_stmt': {'target': 'v1', 'operand': 'Hello World!'}},
 {'assign_stmt': {'target': 'v1',
                  'operand': 'Lcom/erlin/smali/SmaliParse$InnerClassExtends;',
                  'operator': 'check-cast'}},
 {'assign_stmt': {'target': '%v1',
                  'operator': 'instanceof',
                  'operand': 'v0',
                  'operand2': 'v0'}},
 {'assign_stmt': {'target': 'v2', 'operand': '%v1'}},
 {'assign_stmt': {'target': 'v3', 'operand': '0x3'}},
 {'new_array': {'type': 'I', 'attr': 'v3', 'target': '%v2'}},
 {'assign_stmt': {'target': 'v0', 'operand': '%v2'}},
 {'assign_stmt': {'target': 'v0',
                  'operand': ':array_1a',
                  'operator': 'fill-array-data'}},
 {'assign_stmt': {'target': 'v1', 'operand': 'v0', 'operator': 'array-length'}},
 {'new_array': {'type': '', 'attr': 'v1', 'target': '%v3'}},
 {'assign_stmt': {'target': 'v2', 'operand': '%v3'}},
 {'assign_stmt': {'target': 'v3', 'operand': '0x0'}},
 {'assign_stmt': {'target': 'v4', 'operand': 'A'}},
 {'array_write': {'array': 'v2', 'index': 'v3', 'src': 'v4'}},
 {'call_stmt': {'target': '%v4',
                'name': 'Ljava/util/Random;->nextInt',
                'args': ['v0', 'v1'],
                'data_type': 'I',
                'prototype': ''}},
 {'assign_stmt': {'target': 'v0', 'operand': '%v4', 'operator': 'result'}},
 {'call_stmt': {'target': '%v5',
                'name': 'Ljava/lang/invoke/MethodHandle;->invoke',
                'args': ['p1', 'v0', 'v1'],
                'data_type': 'Ljava/lang/Object;',
                'prototype': '(II)V'}},
 {'call_stmt': {'target': '%v6',
                'name': 'Landroid/location/LocationManager;->requestLocationUpdates',
                'args': ['v0', 'v1', 'v2', 'v3', 'v4', 'v5'],
                'data_type': 'V',
                'prototype': ''}},
 {'assign_stmt': {'target': 'v1',
                  'operator': '+',
                  'operand': 'v2',
                  'operand2': 'v3'}},
 {'assign_stmt': {'target': 'v5',
                  'operator': '-',
                  'operand': 'v5',
                  'operand2': 'v6'}},
 {'assign_stmt': {'target': 'v6', 'operator': '-', 'operand': 'v7'}},
 {'assign_stmt': {'target': 'p8', 'operator': 'cast', 'operand': 'p9'}},
 {'assign_stmt': {'target': 'v0',
                  'operator': '+',
                  'operand': 'v1',
                  'operand2': '12345'}},
 {'assign_stmt': {'target': 'v1',
                  'operator': '*',
                  'operand': 'v2',
                  'operand2': '10'}},
 {'field_write': {'receiver_object': 'p0',
                  'field': 'isRunning',
                  'source': 'v0'}},
 {'field_read': {'target': 'v0',
                 'receiver_object': 'Lcom/disney/xx/XxActivity;',
                 'field': 'PREFS_INSTALLATION_ID'}},
 {'compare_stmt': {'target': '%v7',
                   'operator': 'eqz',
                   'operand': 'v2',
                   'operand2': '0'}},
 {'goto_stmt': {'target': ':cond_c', 'condition': '%v7'}},
 {'assign_stmt': {'target': 'p1',
                  'operand': ':pswitch_data_c',
                  'operator': 'switch'}},
 {'new_array': {'type': 'I', 'target': '%v8'}},
 {'assign_stmt': {'target': 'v0', 'operand': '%v8[0]'}},
 {'assign_stmt': {'target': 'v1', 'operand': '%v8[1]'}},
 {'new_array': {'type': 'B', 'target': '%v9'}},
 {'assign_stmt': {'target': 'v19',
                  'operand': '%v9',
                  'operator': 'filled-new-array/range'}},
 {'assign_stmt': {'target': 'v20',
                  'operand': '%v9',
                  'operator': 'filled-new-array/range'}},
 {'assign_stmt': {'target': 'v21',
                  'operand': '%v9',
                  'operator': 'filled-new-array/range'}},
 {'return_stmt': {'target': ''}},
 {'compare_stmt': {'target': '%v10',
                   'operator': 'eq',
                   'operand': 'v0',
                   'operand2': 'v1'}},
 {'goto_stmt': {'target': ':cond_c', 'condition': '%v10'}},
 {'assign_stmt': {'target': 'v1',
                  'operator': '+',
                  'operand': 'v1',
                  'operand2': 'v1'}},
 {'goto': {'target': ':goto_7'}}, {'return_stmt': {'target': ''}}]
[{'operation': 'assign_stmt', 'stmt_id': 1, 'target': 'v0', 'operand': '0x5'},
 {'operation': 'new_array',
  'stmt_id': 2,
  'type': 'I',
  'attr': 'v0',
  'target': '%v0'},
 {'operation': 'assign_stmt', 'stmt_id': 3, 'target': 'v0', 'operand': '%v0'},
 {'operation': 'assign_stmt',
  'stmt_id': 4,
  'target': 'v0',
  'operand': ':array_18',
  'operator': 'fill-array-data'},
 {'operation': 'field_write',
  'stmt_id': 5,
  'receiver_object': 'p0',
  'field': 'intArray',
  'source': 'v0'},
 {'operation': 'return_stmt', 'stmt_id': 6, 'target': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 7,
  'target': 'v1',
  'operand': 'Hello World!'},
 {'operation': 'assign_stmt',
  'stmt_id': 8,
  'target': 'v1',
  'operand': 'Lcom/erlin/smali/SmaliParse$InnerClassExtends;',
  'operator': 'check-cast'},
 {'operation': 'assign_stmt',
  'stmt_id': 9,
  'target': '%v1',
  'operator': 'instanceof',
  'operand': 'v0',
  'operand2': 'v0'},
 {'operation': 'assign_stmt', 'stmt_id': 10, 'target': 'v2', 'operand': '%v1'},
 {'operation': 'assign_stmt', 'stmt_id': 11, 'target': 'v3', 'operand': '0x3'},
 {'operation': 'new_array',
  'stmt_id': 12,
  'type': 'I',
  'attr': 'v3',
  'target': '%v2'},
 {'operation': 'assign_stmt', 'stmt_id': 13, 'target': 'v0', 'operand': '%v2'},
 {'operation': 'assign_stmt',
  'stmt_id': 14,
  'target': 'v0',
  'operand': ':array_1a',
  'operator': 'fill-array-data'},
 {'operation': 'assign_stmt',
  'stmt_id': 15,
  'target': 'v1',
  'operand': 'v0',
  'operator': 'array-length'},
 {'operation': 'new_array',
  'stmt_id': 16,
  'type': '',
  'attr': 'v1',
  'target': '%v3'},
 {'operation': 'assign_stmt', 'stmt_id': 17, 'target': 'v2', 'operand': '%v3'},
 {'operation': 'assign_stmt', 'stmt_id': 18, 'target': 'v3', 'operand': '0x0'},
 {'operation': 'assign_stmt', 'stmt_id': 19, 'target': 'v4', 'operand': 'A'},
 {'operation': 'array_write',
  'stmt_id': 20,
  'array': 'v2',
  'index': 'v3',
  'src': 'v4'},
 {'operation': 'call_stmt',
  'stmt_id': 21,
  'target': '%v4',
  'name': 'Ljava/util/Random;->nextInt',
  'args': "['v0', 'v1']",
  'data_type': 'I',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 22,
  'target': 'v0',
  'operand': '%v4',
  'operator': 'result'},
 {'operation': 'call_stmt',
  'stmt_id': 23,
  'target': '%v5',
  'name': 'Ljava/lang/invoke/MethodHandle;->invoke',
  'args': "['p1', 'v0', 'v1']",
  'data_type': 'Ljava/lang/Object;',
  'prototype': '(II)V'},
 {'operation': 'call_stmt',
  'stmt_id': 24,
  'target': '%v6',
  'name': 'Landroid/location/LocationManager;->requestLocationUpdates',
  'args': "['v0', 'v1', 'v2', 'v3', 'v4', 'v5']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 25,
  'target': 'v1',
  'operator': '+',
  'operand': 'v2',
  'operand2': 'v3'},
 {'operation': 'assign_stmt',
  'stmt_id': 26,
  'target': 'v5',
  'operator': '-',
  'operand': 'v5',
  'operand2': 'v6'},
 {'operation': 'assign_stmt',
  'stmt_id': 27,
  'target': 'v6',
  'operator': '-',
  'operand': 'v7'},
 {'operation': 'assign_stmt',
  'stmt_id': 28,
  'target': 'p8',
  'operator': 'cast',
  'operand': 'p9'},
 {'operation': 'assign_stmt',
  'stmt_id': 29,
  'target': 'v0',
  'operator': '+',
  'operand': 'v1',
  'operand2': '12345'},
 {'operation': 'assign_stmt',
  'stmt_id': 30,
  'target': 'v1',
  'operator': '*',
  'operand': 'v2',
  'operand2': '10'},
 {'operation': 'field_write',
  'stmt_id': 31,
  'receiver_object': 'p0',
  'field': 'isRunning',
  'source': 'v0'},
 {'operation': 'field_read',
  'stmt_id': 32,
  'target': 'v0',
  'receiver_object': 'Lcom/disney/xx/XxActivity;',
  'field': 'PREFS_INSTALLATION_ID'},
 {'operation': 'compare_stmt',
  'stmt_id': 33,
  'target': '%v7',
  'operator': 'eqz',
  'operand': 'v2',
  'operand2': '0'},
 {'operation': 'goto_stmt',
  'stmt_id': 34,
  'target': ':cond_c',
  'condition': '%v7'},
 {'operation': 'assign_stmt',
  'stmt_id': 35,
  'target': 'p1',
  'operand': ':pswitch_data_c',
  'operator': 'switch'},
 {'operation': 'new_array', 'stmt_id': 36, 'type': 'I', 'target': '%v8'},
 {'operation': 'assign_stmt',
  'stmt_id': 37,
  'target': 'v0',
  'operand': '%v8[0]'},
 {'operation': 'assign_stmt',
  'stmt_id': 38,
  'target': 'v1',
  'operand': '%v8[1]'},
 {'operation': 'new_array', 'stmt_id': 39, 'type': 'B', 'target': '%v9'},
 {'operation': 'assign_stmt',
  'stmt_id': 40,
  'target': 'v19',
  'operand': '%v9',
  'operator': 'filled-new-array/range'},
 {'operation': 'assign_stmt',
  'stmt_id': 41,
  'target': 'v20',
  'operand': '%v9',
  'operator': 'filled-new-array/range'},
 {'operation': 'assign_stmt',
  'stmt_id': 42,
  'target': 'v21',
  'operand': '%v9',
  'operator': 'filled-new-array/range'},
 {'operation': 'return_stmt', 'stmt_id': 43, 'target': ''},
 {'operation': 'compare_stmt',
  'stmt_id': 44,
  'target': '%v10',
  'operator': 'eq',
  'operand': 'v0',
  'operand2': 'v1'},
 {'operation': 'goto_stmt',
  'stmt_id': 45,
  'target': ':cond_c',
  'condition': '%v10'},
 {'operation': 'assign_stmt',
  'stmt_id': 46,
  'target': 'v1',
  'operator': '+',
  'operand': 'v1',
  'operand2': 'v1'},
 {'operation': 'goto', 'stmt_id': 47, 'target': ':goto_7'},
 {'operation': 'return_stmt', 'stmt_id': 48, 'target': ''}]
```