# 编译实验3报告

## 小组成员及分工
#### 刘可盈：
负责restart_local_directive、end_local_directive、label 和 jmp_label、packed_switch_directive、sparse_switch_directive、array_data_directive、catch_directive和catchall_directive、if_statement

#### 韩偲蔚：
负责annotation_directive、param_directive、parameter_directive、parameter_directive、local_directive

## 实验思路
由于smali的语句的形式大多为指令，没有类似于其他语言的statement语句。因此，本次实验我们完成了smali的一部分directive的解析，并且修改了上次实验中不完善的部分。

## 核心代码
### restart_local_directive
```python
    def restart_local_directive(self, node, statements):
        #print(node.sexp())
        register = self.read_node_text(node.named_children[0])
        statements.append({"variable_decl": { "name": register }})
        return register
```
restart_local_directive表示重新启用某个寄存器。node只有一个子节点，为被启用的寄存器。此语句可以看作重新声明了变量，转换为glang的variable_decl.

#### end_local_directive
```python
    def end_local_directive(self, node, statements):
        register = node.named_children[0]
        if register == None:
            pass
        register = self.read_node_text(register)
        statements.append({"del_statement": { "target": register }})
```
end_local_directive表示某个寄存器的使用结束。node的有一个子节点，表示结束使用的寄存器名称。转换为glang的del_statement，target为寄存器名称。
#### label 和 jmp_label
```python
    def label_statement(self, node, statements):
        label= self.read_node_text(node)
        statements.append({"label_stmt": { "name": label }})
        label_list[label]= len(statements)
        global latest_label
        latest_label = label
```
label表示smali的标签，jmp_label表示跳转标签。均转换为glang的label_stmt。用label_list记录当前label在statements中的未知，以便完成其他关于label的操作。用latest_label记录当前最后一个label

#### packed_switch_directive
```python
    def packed_switch_directive(self, node, statements):
        #print(node.sexp())
        global latest_label
        switch_label = latest_label
        condition = self.read_node_text(self.find_child_by_type(node, "number"))
        if '0x' in condition:
            shadow_condition = int(condition,base=16)
        else:
            shadow_condition = int(condition,base=10)
        cases = []
        for child in node.named_children:
            if child.type == "label" or child.type == "jmp_label":
                label = self.read_node_text(child)
                cases.append({"case_stmt": {"condition": str(shadow_condition), "body": [{"goto_stmt": {"target": label}}]}})
                shadow_condition += 1
        switch_table[switch_label] = cases
        if switch_label in unsolved_switch.keys():
            stmt_id = unsolved_switch[switch_label]
            del unsolved_switch[switch_label]
            statements[stmt_id]["switch_stmt"]['body']= cases
```
packed_switch_directive表示smali中的packed_switch跳转表。packed_switch_directive语句的前一句必须是一个label语句，通过label将packed_switch_directive与expression中的packed_switch指令匹配起来。因此当前的最后一个label作为switch_label。packed_switch_directive中有一个number是第一个label的跳转条件，后面的label的跳转条件是number依次递增加一。依次找到node的子节点中为label或jmp_label的子节点，跳转条件的值依次加一，转换成glang的case_stmt，condition为当前跳转条件的值，body中只有一个goto_stmt语句，target为当前的label。cases_stmt加入到cases列表中。最后以switch_label为键，cased列表为值，加入到swtich_table中。如果switch_label已经出现在unsolved_swtich中，则将statements中对应的switch_stmt的body替换为当前的cases列表。
修改前次实验的expression中的switch指令的转换。
```python
        elif re.search(r'-switch$', shadow_opcode):
            p0 = self.read_node_text(node.named_children[1])
            switch_label = self.read_node_text(node.named_children[2])
            cases = None
            if switch_label in switch_table:
                cases = switch_table[switch_label]
            else:
                unsolved_switch[switch_label]= len(statements)
            statements.append({"switch_stmt": {"condition": p0, "body": cases}})
            return p0
```
switch指令的格式为：一个寄存器，是分支条件，一个label，对应packed_switch_directive或sparse_switch_directive跳转表的label。如果switch_table中已有switch_label，则直接取出cases列表。如果没有，则cases暂时为None，并将switch_table作为键，statements的下标作为值加入unsolved_switch。在statements中添加一个switch_stmt，condition是寄存器，body是cases列表。
#### sparse_switch_directive
```python
    def sparse_switch_directive(self, node, statements):
        #print(node.sexp())
        global latest_label
        switch_label = latest_label
        conditions = self.find_children_by_type(node, "number")
        labels = self.find_children_by_type(node, "label")
        cases = []
        for condition,label in zip(conditions,labels):
            shadow_condition = self.read_node_text(condition)
            shadow_label = self.read_node_text(label)
            cases.append({"case_stmt": {"condition": str(shadow_condition), "body": [{"goto_stmt": {"target": shadow_label}}]}})
        switch_table[switch_label] = cases
        if switch_label in unsolved_switch.keys():
            stmt_id = unsolved_switch[switch_label]
            del(unsolved_switch[switch_label])
            statements[stmt_id]["switch_stmt"]['body']= cases
```
sparse_switch_directive中是一个number作为跳转条件对应一个label作为跳转目标。因此依次提取出node的子节点中的number子节点和label子节点，一一对应转换成case_stmt。其余部分与packed_switch_directive类似。
#### array_data_directive
```python
    def array_data_directive(self, node, statements):
        #print(node.sexp())
        element_width = self.find_child_by_field(node, "element_width")
        values = self.find_children_by_field(node,"value")
        global latest_label
        array_data_label= latest_label
        shadow_values = []
        for value in values:
            shadow_values.append(self.read_node_text(value))
        array_data_list[array_data_label] = shadow_values
        if array_data_label in unsolved_array_data.keys():
            stmt_id = unsolved_array_data[array_data_label]["stmt_id"]
            array = unsolved_array_data[array_data_label]["array"]
            del(unsolved_array_data[array_data_label])
            for i in range(len(shadow_values)):
                statements.insert(stmt_id, {"array_write": {"array": array , "index":i , "src":shadow_values[i] }})
                stmt_id += 1
```
array_data_directive的前一个语句是array_data的标签。依次取出array_data_directive中的"value"field，是填充数组的值。以array_data_label为键，values列表为值，加入array_data_list。如果array_data_label已经出现在unsolved_array_data中，则在statements的对应位置加入array_write语句。
修改expression中的fill-array-data的转换。
```python
        elif re.compile(r'^fill-.*').match(shadow_opcode):
            v0 = self.read_node_text(node.named_children[1])
            array_label = self.read_node_text(node.named_children[2])
            if array_label in array_data_list.keys():
                shadow_values= array_data_list[array_label]
                for i in range(len(shadow_values)):
                    statements.append({"array_write": {"array": v0 , "index":i , "src":shadow_values[i] }})
            else:
                unsolved_array_data[array_label] = {'array': v0, 'stmt_id':len(statements)}
            return v0
```
如果对应标签已出现在array_data_list中，则直接将array_data_list的值转换为array_write语句。否则，在unsolved_array_data记录标签、数组名称、应当插入statements的语句位置。
#### catch_directive和catchall_directive
```python
        def catch_directive(self, node, statements):
        exception= self.read_node_text(self.find_child_by_type(node,"class_identifier"))
        global tmp_exception
        tmp_exception = exception
        labels=[]
        for child in node.named_children:
            if child.type == "label" or child.type == "jmp_label":
                labels.append(self.read_node_text(child))
        try_start_label = labels[0]
        try_end_label = labels[1]
        handler_label = labels[2]
        stmt_start_id = label_list[try_start_label]
        stmt_end_id = label_list[try_end_label]
        body=[]
        for id in range(stmt_start_id,stmt_end_id-1):
            body.append(statements[id])
        del(statements[stmt_start_id:stmt_end_id-1])
        if exception is not None:
            catch_body=[{"catch_clause":{"exception":exception,"body":[{"goto_stmt":{"target":handler_label}}]}}]
        else:
            catch_body=[{"catch_stmt":{"body":[{"goto_stmt":{"target":handler_label}}]}}]
        statements.append({"try_stmt":{"body":body,"catch_body":catch_body}})
        for key,value in label_list.items():
            if value > stmt_end_id:
                label_list[key] -= stmt_end_id - stmt_start_id - 1
        for key,value in unsolved_switch.items():
            if value > stmt_end_id:
                unsolved_switch[key] -= stmt_end_id - stmt_start_id - 1
        for key,value in unsolved_array_data.items():
            if value["stmt_id"] > stmt_end_id:
                unsolved_array_data[key]["stmt_id"] -= stmt_end_id - stmt_start_id - 1
```
catch语句的形式为.catch exceptionName{try_start_label .. try_end_label}  handler_label
取出class_identifier，是exception名称。再取出所有为label的子节点。第一个是try_start_label，第二个是try_end_label，第三个是handler_label。再从label_list中得到try_start_label和try_end_label的语句位置。将try_start_label和try_end_label之间的语句加入catch_body，并从statements中删去。如果exceptionName不为空，则catch_body中加入catch_clause，exceptionName为exception名称。如果exceptionName为空，则catch_body中加入catch_stmt。两种的body都只有一个语句，即goto_stmt，goto_stmt的target为handler_label。加入try_stmt。最后因为删除了statements的语句，要调整一下全局的字典label_list、unsolved_switch、unsolved_array_data

#### if_statement
修改了expression中的if语句，改为符合glang的格式。
```python
        elif re.compile(r'^if-.*').match(shadow_opcode):
            op = re.findall(r'if-([^ \n\r\t]+)', shadow_opcode)
            v0 = self.read_node_text(values["variable"][0])
            if 'z' not in op[0]:
                v1 = self.read_node_text(values["variable"][1])
            else:
                v1 = "0"
            tmp_var = self.tmp_variable(statements)
            statements.append({"compare_stmt": {"target": tmp_var, "operator": op[0], "operand": v0,"operand2": v1}})
            label = self.read_node_text(self.find_child_by_type(node, "label"))
            statements.append({"if_stmt":{"condition": tmp_var,"then_body":[{"goto_stmt": {"target": label}}]}})
            return tmp_var
```

#### annotation_directive

annotation是smali的注解，大致语法如下：
```smali
    .annotation [注解属性] <注解类名>
    [注解字段 = 值]
    .end annotation
```
如果注解的作用范围是类， .annotation 指令会直接定义在 smali 文件中，如果作用范围是方法或者字段，则会包含在方法或字段定义中。根据smali的语法将annotation转换为annotation_type_decl：`注解属性`作为`attr`，`注解类名`作为`name`，`注解字段:值`加入`init`字典。

实现代码如下：
```python
    def annotation_directive(self, node, statements):
        shadow_annotation_visibility = self.read_node_text(node.named_children[0])
        shadow_class_identifier = self.read_node_text(node.named_children[1])
        annotation_property_list = node.named_children[2:]
        glang_init_dict = {}
        for annotation_property in annotation_property_list:
            annotation_key = annotation_property.named_children[0]
            annotation_value = self.find_child_by_type(annotation_property, "annotation_value")
            glang_init_dict[self.read_node_text(annotation_key)] = self.read_node_text(annotation_value)
        statements.append({"annotation_type_decl": {"attr": shadow_annotation_visibility, "name": shadow_class_identifier, "init": [glang_init_dict]}})
        return
```
#### param_directive
smali的param_directive语法大致为`.param p, value`，作用是建立值为value的变量p，转为glang中的parameter_decl和assign_stmt。但根据`smali_grammar.js`，还存在一种语法是`.param p, repeat(annotation)`，因此根据是否存在annotation进行不同的转换，若存在便调用annotation_directive。

实现代码如下：
```python
    def param_directive(self, node, statements):
        name = self.read_node_text(self.find_child_by_type(node, "parameter"))
        annotation_list = self.find_children_by_type(node, "annotation_directive")
        if len(annotation_list):
            for annotation in annotation_list:
                self.annotation_directive(annotation, statements)
        else:
            shadow_value = self.read_node_text(node.named_children[1])
            statements.append({"parameter_decl": {"name": name}})
            statements.append({"assign_stmt": {"target": name, "operand": shadow_value}})
        return name
```
#### parameter_directive
由于难以找到parameter_directive的代码示例，根据`smali_grammar.js`，parameter_directive即为一系列annotation_directive，则实现代码如下：
```python
    def parameter_directive(self, node, statements):
        annotation_list = self.find_children_by_type(node, "annotation_directive")
        if len(annotation_list):
            for annotation in annotation_list:
                self.annotation_directive(annotation, statements)
        return
```
#### local_directive
smali的local声明格式为`.local 寄存器, 变量名:类型`，作用是声明变量名为指定的类型，且将寄存器中的值赋值给变量，转为glang中的variable_decl和assign_stmt。由于类型中包含基本类型、类标识符和数组类型，因此根据类型是否是数组设置variable_decl中的attr部分。
实现代码如下：
```python
    def variable_directive(self, node, statements):
        # print("variable:", node.sexp())
        shadow_register = self.read_node_text(node.named_children[0])
        if node.named_children[1]:
            shadow_local = self.read_node_text(node.named_children[1])
            shadow_data_type = self.read_node_text(node.named_children[2])
            if self.find_child_by_type(node, "array_type"):
                array_node = self.find_child_by_type(node, "array_type")
                shadow_data_type = self.read_node_text(array_node)
                statements.append({"variable_decl": {"name": shadow_local, "attr": "array", "data_type": shadow_data_type}})
            else:
                statements.append({"variable_decl": {"name": shadow_local, "data_type": shadow_data_type}})
            statements.append({"assign_stmt": {"target": shadow_local, "operand": shadow_register}})
        else:
            statements.append({"variable_decl": {"name": shadow_register}})
        return
```

## 测试用例
```
.class public Lcom/alipay/helloworld/MainActivity;
.super Landroid/app/Activity;
.source "MainActivity.java"


# direct methods
.method public constructor <init>()V
    .locals 0

    .prologue
    .line 7
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V

    return-void
.end method


# virtual methods
.method protected onCreate(Landroid/os/Bundle;)V
    .locals 3
    .parameter "savedInstanceState"

    .prologue
    .line 11
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    .line 12
    const/high16 v2, 0x7f03

    invoke-virtual {p0, v2}, Lcom/alipay/helloworld/MainActivity;->setContentView(I)V

    const-string v1, "92a8"

    :try_start
    invoke-static {v1}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v1
    :try_end
    .catch Ljava/lang/Exception;{:try_start .. :try_end}  :handler_1
    :goto_0
    return-void

    :handler_1
    move-exception v0
    invoke-virtual {v0}, Ljava/lang/Exception;->toString()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {p0, v0}, Lcom/alipay/helloworld/MainActivity;->showToastMessage(Ljava/lang/String;)V
    goto :goto_0
.end method


.method public showToastMessage(Ljava/lang/String;)V
    .locals 1
    const/4 v0, 0x01
    invoke-static {p0, p1, v0}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    return-void
.end method

.method public static main([Ljava/lang/String;)V
    
    fill-array-data v0, :ArrayData

    :ArrayData
    .array-data 4
        0x0
        0x1
        0x2
        0x3
        0x4
    .end array-data

    .local v0, "engine":Lorg/jf/Penroser/PenroserLiveWallpaper$PenroserGLEngine;
    .local p0, "this":Lblah;
    .local v1, "future":Lcom/android/volley/toolbox/RequestFuture;, "Lcom/android/volley/toolbox/RequestFuture<Ljava/lang/Void;>;"

    :switch
    packed-switch v0, :PackedSwitch

    :PackedSwitch
    .packed-switch 10
        :Label10
        :Label11
        :Label12
        :Label13
    .end packed-switch

    :pswitch_data_c
    .packed-switch 0x0
        :pswitch_6 #case 0
        :pswitch_9 #case 1
    .end packed-switch

    packed-switch p1, :pswitch_data_c
    .end local v0
    

    sparse-switch v0, :SparseSwitch
    .end local p0
    .end local v1
    :SparseSwitch
    .sparse-switch
        10 -> :Label10
        13 -> :Label13
        15 -> :Label12
        20 -> :Label11
        99 -> :Label13
    .end sparse-switch

    :Label10
    if-nez p1, :Label13
    :Label11
    :Label12
    :Label13
.end method

```


## 测试结果
```bash
[{'call_stmt': {'target': '%v0',
                'name': 'Landroid/app/Activity;-><init>',
                'args': ['p0'],
                'data_type': 'V',
                'prototype': ''}},
 {'return_stmt': {'target': ''}},
 {'call_stmt': {'target': '%v1',
                'name': 'Landroid/app/Activity;->onCreate',
                'args': ['p0', 'p1'],
                'data_type': 'V',
                'prototype': ''}},
 {'assign_stmt': {'target': 'v2', 'operand': '0x7f03'}},
 {'call_stmt': {'target': '%v2',
                'name': 'Lcom/alipay/helloworld/MainActivity;->setContentView',
                'args': ['p0', 'v2'],
                'data_type': 'V',
                'prototype': ''}},
 {'assign_stmt': {'target': 'v1', 'operand': '92a8'}},
 {'label_stmt': {'name': ':try_start'}}, {'label_stmt': {'name': ':try_end'}},
 {'try_stmt': {'body': [{'call_stmt': {'target': '%v3',
                                       'name': 'Ljava/lang/Integer;->parseInt',
                                       'args': ['v1'],
                                       'data_type': 'I',
                                       'prototype': ''}},
                        {'assign_stmt': {'target': 'v1',
                                         'operand': '%v3',
                                         'operator': 'result'}}],
               'catch_body': [{'catch_clause': {'exception': 'Ljava/lang/Exception;',
                                                'body': [{'goto_stmt': {'target': ':handler_1'}}]}}]}},
 {'label_stmt': {'name': ':goto_0'}}, {'return_stmt': {'target': ''}},
 {'label_stmt': {'name': ':handler_1'}},
 {'assign_stmt': {'target': 'v0',
                  'operand': 'Ljava/lang/Exception;',
                  'operator': 'exception'}},
 {'call_stmt': {'target': '%v4',
                'name': 'Ljava/lang/Exception;->toString',
                'args': ['v0'],
                'data_type': 'Ljava/lang/String;',
                'prototype': ''}},
 {'assign_stmt': {'target': 'v0', 'operand': '%v4', 'operator': 'result'}},
 {'call_stmt': {'target': '%v5',
                'name': 'Lcom/alipay/helloworld/MainActivity;->showToastMessage',
                'args': ['p0', 'v0'],
                'data_type': 'V',
                'prototype': ''}},
 {'goto_stmt': {'target': ':goto_0'}},
 {'assign_stmt': {'target': 'v0', 'operand': '0x01'}},
 {'call_stmt': {'target': '%v6',
                'name': 'Landroid/widget/Toast;->makeText',
                'args': ['p0', 'p1', 'v0'],
                'data_type': 'Landroid/widget/Toast;',
                'prototype': ''}},
 {'assign_stmt': {'target': 'v0', 'operand': '%v6', 'operator': 'result'}},
 {'call_stmt': {'target': '%v7',
                'name': 'Landroid/widget/Toast;->show',
                'args': ['v0'],
                'data_type': 'V',
                'prototype': ''}},
 {'return_stmt': {'target': ''}},
 {'array_write': {'array': 'v0', 'index': 0, 'src': '0x0'}},
 {'array_write': {'array': 'v0', 'index': 1, 'src': '0x1'}},
 {'array_write': {'array': 'v0', 'index': 2, 'src': '0x2'}},
 {'array_write': {'array': 'v0', 'index': 3, 'src': '0x3'}},
 {'array_write': {'array': 'v0', 'index': 4, 'src': '0x4'}},
 {'label_stmt': {'name': ':ArrayData'}},
 {'variable_decl': {'name': '"engine"',
                    'data_type': 'Lorg/jf/Penroser/PenroserLiveWallpaper$PenroserGLEngine;'}},
 {'assign_stmt': {'target': '"engine"', 'operand': 'v0'}},
 {'variable_decl': {'name': '"this"', 'data_type': 'Lblah;'}},
 {'assign_stmt': {'target': '"this"', 'operand': 'p0'}},
 {'variable_decl': {'name': '"future"',
                    'data_type': 'Lcom/android/volley/toolbox/RequestFuture;'}},
 {'assign_stmt': {'target': '"future"', 'operand': 'v1'}},
 {'label_stmt': {'name': ':switch'}},
 {'switch_stmt': {'condition': 'v0',
                  'body': [{'case_stmt': {'condition': '10',
                                          'body': [{'goto_stmt': {'target': ':Label10'}}]}},
                           {'case_stmt': {'condition': '11',
                                          'body': [{'goto_stmt': {'target': ':Label11'}}]}},
                           {'case_stmt': {'condition': '12',
                                          'body': [{'goto_stmt': {'target': ':Label12'}}]}},
                           {'case_stmt': {'condition': '13',
                                          'body': [{'goto_stmt': {'target': ':Label13'}}]}}]}},
 {'label_stmt': {'name': ':PackedSwitch'}},
 {'label_stmt': {'name': ':pswitch_data_c'}},
 {'switch_stmt': {'condition': 'p1',
                  'body': [{'case_stmt': {'condition': '0',
                                          'body': [{'goto_stmt': {'target': ':pswitch_6'}}]}},
                           {'case_stmt': {'condition': '1',
                                          'body': [{'goto_stmt': {'target': ':pswitch_9'}}]}}]}},
 {'del_statement': {'target': 'v0'}},
 {'switch_stmt': {'condition': 'v0',
                  'body': [{'case_stmt': {'condition': '10',
                                          'body': [{'goto_stmt': {'target': ':Label10'}}]}},
                           {'case_stmt': {'condition': '13',
                                          'body': [{'goto_stmt': {'target': ':Label13'}}]}},
                           {'case_stmt': {'condition': '15',
                                          'body': [{'goto_stmt': {'target': ':Label12'}}]}},
                           {'case_stmt': {'condition': '20',
                                          'body': [{'goto_stmt': {'target': ':Label11'}}]}},
                           {'case_stmt': {'condition': '99',
                                          'body': [{'goto_stmt': {'target': ':Label13'}}]}}]}},
 {'del_statement': {'target': 'p0'}}, {'del_statement': {'target': 'v1'}},
 {'label_stmt': {'name': ':SparseSwitch'}},
 {'label_stmt': {'name': ':Label10'}},
 {'compare_stmt': {'target': '%v8',
                   'operator': 'nez',
                   'operand': 'p1',
                   'operand2': '0'}},
 {'if_stmt': {'condition': '%v8',
              'then_body': [{'goto_stmt': {'target': ':Label13'}}]}},
 {'label_stmt': {'name': ':Label11'}}, {'label_stmt': {'name': ':Label12'}},
 {'label_stmt': {'name': ':Label13'}}]
[{'operation': 'call_stmt',
  'stmt_id': 1,
  'target': '%v0',
  'name': 'Landroid/app/Activity;-><init>',
  'args': "['p0']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 2, 'target': ''},
 {'operation': 'call_stmt',
  'stmt_id': 3,
  'target': '%v1',
  'name': 'Landroid/app/Activity;->onCreate',
  'args': "['p0', 'p1']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 4,
  'target': 'v2',
  'operand': '0x7f03'},
 {'operation': 'call_stmt',
  'stmt_id': 5,
  'target': '%v2',
  'name': 'Lcom/alipay/helloworld/MainActivity;->setContentView',
  'args': "['p0', 'v2']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'assign_stmt', 'stmt_id': 6, 'target': 'v1', 'operand': '92a8'},
 {'operation': 'label_stmt', 'stmt_id': 7, 'name': ':try_start'},
 {'operation': 'label_stmt', 'stmt_id': 8, 'name': ':try_end'},
 {'operation': 'try_stmt', 'stmt_id': 9, 'body': 10, 'catch_body': 13},
 {'operation': 'block_start', 'stmt_id': 10, 'parent_stmt_id': 9},
 {'operation': 'call_stmt',
  'stmt_id': 11,
  'target': '%v3',
  'name': 'Ljava/lang/Integer;->parseInt',
  'args': "['v1']",
  'data_type': 'I',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 12,
  'target': 'v1',
  'operand': '%v3',
  'operator': 'result'},
 {'operation': 'block_end', 'stmt_id': 10, 'parent_stmt_id': 9},
 {'operation': 'block_start', 'stmt_id': 13, 'parent_stmt_id': 9},
 {'operation': 'catch_clause',
  'stmt_id': 14,
  'exception': 'Ljava/lang/Exception;',
  'body': 15},
 {'operation': 'block_start', 'stmt_id': 15, 'parent_stmt_id': 14},
 {'operation': 'goto_stmt', 'stmt_id': 16, 'target': ':handler_1'},
 {'operation': 'block_end', 'stmt_id': 15, 'parent_stmt_id': 14},
 {'operation': 'block_end', 'stmt_id': 13, 'parent_stmt_id': 9},
 {'operation': 'label_stmt', 'stmt_id': 17, 'name': ':goto_0'},
 {'operation': 'return_stmt', 'stmt_id': 18, 'target': ''},
 {'operation': 'label_stmt', 'stmt_id': 19, 'name': ':handler_1'},
 {'operation': 'assign_stmt',
  'stmt_id': 20,
  'target': 'v0',
  'operand': 'Ljava/lang/Exception;',
  'operator': 'exception'},
 {'operation': 'call_stmt',
  'stmt_id': 21,
  'target': '%v4',
  'name': 'Ljava/lang/Exception;->toString',
  'args': "['v0']",
  'data_type': 'Ljava/lang/String;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 22,
  'target': 'v0',
  'operand': '%v4',
  'operator': 'result'},
 {'operation': 'call_stmt',
  'stmt_id': 23,
  'target': '%v5',
  'name': 'Lcom/alipay/helloworld/MainActivity;->showToastMessage',
  'args': "['p0', 'v0']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'goto_stmt', 'stmt_id': 24, 'target': ':goto_0'},
 {'operation': 'assign_stmt', 'stmt_id': 25, 'target': 'v0', 'operand': '0x01'},
 {'operation': 'call_stmt',
  'stmt_id': 26,
  'target': '%v6',
  'name': 'Landroid/widget/Toast;->makeText',
  'args': "['p0', 'p1', 'v0']",
  'data_type': 'Landroid/widget/Toast;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 27,
  'target': 'v0',
  'operand': '%v6',
  'operator': 'result'},
 {'operation': 'call_stmt',
  'stmt_id': 28,
  'target': '%v7',
  'name': 'Landroid/widget/Toast;->show',
  'args': "['v0']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 29, 'target': ''},
 {'operation': 'array_write',
  'stmt_id': 30,
  'array': 'v0',
  'index': 0,
  'src': '0x0'},
 {'operation': 'array_write',
  'stmt_id': 31,
  'array': 'v0',
  'index': 1,
  'src': '0x1'},
 {'operation': 'array_write',
  'stmt_id': 32,
  'array': 'v0',
  'index': 2,
  'src': '0x2'},
 {'operation': 'array_write',
  'stmt_id': 33,
  'array': 'v0',
  'index': 3,
  'src': '0x3'},
 {'operation': 'array_write',
  'stmt_id': 34,
  'array': 'v0',
  'index': 4,
  'src': '0x4'},
 {'operation': 'label_stmt', 'stmt_id': 35, 'name': ':ArrayData'},
 {'operation': 'variable_decl',
  'stmt_id': 36,
  'name': '"engine"',
  'data_type': 'Lorg/jf/Penroser/PenroserLiveWallpaper$PenroserGLEngine;'},
 {'operation': 'assign_stmt',
  'stmt_id': 37,
  'target': '"engine"',
  'operand': 'v0'},
 {'operation': 'variable_decl',
  'stmt_id': 38,
  'name': '"this"',
  'data_type': 'Lblah;'},
 {'operation': 'assign_stmt',
  'stmt_id': 39,
  'target': '"this"',
  'operand': 'p0'},
 {'operation': 'variable_decl',
  'stmt_id': 40,
  'name': '"future"',
  'data_type': 'Lcom/android/volley/toolbox/RequestFuture;'},
 {'operation': 'assign_stmt',
  'stmt_id': 41,
  'target': '"future"',
  'operand': 'v1'},
 {'operation': 'label_stmt', 'stmt_id': 42, 'name': ':switch'},
 {'operation': 'switch_stmt', 'stmt_id': 43, 'condition': 'v0', 'body': 44},
 {'operation': 'block_start', 'stmt_id': 44, 'parent_stmt_id': 43},
 {'operation': 'case_stmt', 'stmt_id': 45, 'condition': '10', 'body': 46},
 {'operation': 'block_start', 'stmt_id': 46, 'parent_stmt_id': 45},
 {'operation': 'goto_stmt', 'stmt_id': 47, 'target': ':Label10'},
 {'operation': 'block_end', 'stmt_id': 46, 'parent_stmt_id': 45},
 {'operation': 'case_stmt', 'stmt_id': 48, 'condition': '11', 'body': 49},
 {'operation': 'block_start', 'stmt_id': 49, 'parent_stmt_id': 48},
 {'operation': 'goto_stmt', 'stmt_id': 50, 'target': ':Label11'},
 {'operation': 'block_end', 'stmt_id': 49, 'parent_stmt_id': 48},
 {'operation': 'case_stmt', 'stmt_id': 51, 'condition': '12', 'body': 52},
 {'operation': 'block_start', 'stmt_id': 52, 'parent_stmt_id': 51},
 {'operation': 'goto_stmt', 'stmt_id': 53, 'target': ':Label12'},
 {'operation': 'block_end', 'stmt_id': 52, 'parent_stmt_id': 51},
 {'operation': 'case_stmt', 'stmt_id': 54, 'condition': '13', 'body': 55},
 {'operation': 'block_start', 'stmt_id': 55, 'parent_stmt_id': 54},
 {'operation': 'goto_stmt', 'stmt_id': 56, 'target': ':Label13'},
 {'operation': 'block_end', 'stmt_id': 55, 'parent_stmt_id': 54},
 {'operation': 'block_end', 'stmt_id': 44, 'parent_stmt_id': 43},
 {'operation': 'label_stmt', 'stmt_id': 57, 'name': ':PackedSwitch'},
 {'operation': 'label_stmt', 'stmt_id': 58, 'name': ':pswitch_data_c'},
 {'operation': 'switch_stmt', 'stmt_id': 59, 'condition': 'p1', 'body': 60},
 {'operation': 'block_start', 'stmt_id': 60, 'parent_stmt_id': 59},
 {'operation': 'case_stmt', 'stmt_id': 61, 'condition': '0', 'body': 62},
 {'operation': 'block_start', 'stmt_id': 62, 'parent_stmt_id': 61},
 {'operation': 'goto_stmt', 'stmt_id': 63, 'target': ':pswitch_6'},
 {'operation': 'block_end', 'stmt_id': 62, 'parent_stmt_id': 61},
 {'operation': 'case_stmt', 'stmt_id': 64, 'condition': '1', 'body': 65},
 {'operation': 'block_start', 'stmt_id': 65, 'parent_stmt_id': 64},
 {'operation': 'goto_stmt', 'stmt_id': 66, 'target': ':pswitch_9'},
 {'operation': 'block_end', 'stmt_id': 65, 'parent_stmt_id': 64},
 {'operation': 'block_end', 'stmt_id': 60, 'parent_stmt_id': 59},
 {'operation': 'del_statement', 'stmt_id': 67, 'target': 'v0'},
 {'operation': 'switch_stmt', 'stmt_id': 68, 'condition': 'v0', 'body': 69},
 {'operation': 'block_start', 'stmt_id': 69, 'parent_stmt_id': 68},
 {'operation': 'case_stmt', 'stmt_id': 70, 'condition': '10', 'body': 71},
 {'operation': 'block_start', 'stmt_id': 71, 'parent_stmt_id': 70},
 {'operation': 'goto_stmt', 'stmt_id': 72, 'target': ':Label10'},
 {'operation': 'block_end', 'stmt_id': 71, 'parent_stmt_id': 70},
 {'operation': 'case_stmt', 'stmt_id': 73, 'condition': '13', 'body': 74},
 {'operation': 'block_start', 'stmt_id': 74, 'parent_stmt_id': 73},
 {'operation': 'goto_stmt', 'stmt_id': 75, 'target': ':Label13'},
 {'operation': 'block_end', 'stmt_id': 74, 'parent_stmt_id': 73},
 {'operation': 'case_stmt', 'stmt_id': 76, 'condition': '15', 'body': 77},
 {'operation': 'block_start', 'stmt_id': 77, 'parent_stmt_id': 76},
 {'operation': 'goto_stmt', 'stmt_id': 78, 'target': ':Label12'},
 {'operation': 'block_end', 'stmt_id': 77, 'parent_stmt_id': 76},
 {'operation': 'case_stmt', 'stmt_id': 79, 'condition': '20', 'body': 80},
 {'operation': 'block_start', 'stmt_id': 80, 'parent_stmt_id': 79},
 {'operation': 'goto_stmt', 'stmt_id': 81, 'target': ':Label11'},
 {'operation': 'block_end', 'stmt_id': 80, 'parent_stmt_id': 79},
 {'operation': 'case_stmt', 'stmt_id': 82, 'condition': '99', 'body': 83},
 {'operation': 'block_start', 'stmt_id': 83, 'parent_stmt_id': 82},
 {'operation': 'goto_stmt', 'stmt_id': 84, 'target': ':Label13'},
 {'operation': 'block_end', 'stmt_id': 83, 'parent_stmt_id': 82},
 {'operation': 'block_end', 'stmt_id': 69, 'parent_stmt_id': 68},
 {'operation': 'del_statement', 'stmt_id': 85, 'target': 'p0'},
 {'operation': 'del_statement', 'stmt_id': 86, 'target': 'v1'},
 {'operation': 'label_stmt', 'stmt_id': 87, 'name': ':SparseSwitch'},
 {'operation': 'label_stmt', 'stmt_id': 88, 'name': ':Label10'},
 {'operation': 'compare_stmt',
  'stmt_id': 89,
  'target': '%v8',
  'operator': 'nez',
  'operand': 'p1',
  'operand2': '0'},
 {'operation': 'if_stmt', 'stmt_id': 90, 'condition': '%v8', 'then_body': 91},
 {'operation': 'block_start', 'stmt_id': 91, 'parent_stmt_id': 90},
 {'operation': 'goto_stmt', 'stmt_id': 92, 'target': ':Label13'},
 {'operation': 'block_end', 'stmt_id': 91, 'parent_stmt_id': 90},
 {'operation': 'label_stmt', 'stmt_id': 93, 'name': ':Label11'},
 {'operation': 'label_stmt', 'stmt_id': 94, 'name': ':Label12'},
 {'operation': 'label_stmt', 'stmt_id': 95, 'name': ':Label13'}]
```