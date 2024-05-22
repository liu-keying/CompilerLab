# 编译实验5报告

## 小组成员及分工
#### 刘可盈：
负责编写class_definition，method_definition，field_definition的解析代码。
#### 韩偲蔚：
负责测试，并完善代码。

## 实验思路
上次实验已完成大部分的declaration，本次实验还剩下：类的定义class_definition，方法定义method_definition，域定义field_definition。smali中，一个文件定义一个类，方法和域必须定义在类中，按此逻辑进行解析。

## 核心代码
#### class_definition
```python
    def class_definition(self,node, statements):
        class_directive = self.find_child_by_type(node, "class_directive")
        access_modifiers=self.find_child_by_type(class_directive,"access_modifiers")
        attr=[]
        if access_modifiers is not None:
            access_modifier = self.find_children_by_type(access_modifiers,"access_modifier")
            for modifier in access_modifier:
                attr.append(self.read_node_text(modifier))
        class_name = self.read_node_text(self.find_child_by_type(class_directive,"class_identifier"))
        supers =[]
        super_class = self.read_node_text(self.find_child_by_type_type(node,"super_directive","class_identifier"))
        supers.append(super_class)
        interfaces = self.find_children_by_type(node,"implements_directive")
        for interface in interfaces:
            interface_name = self.read_node_text(self.find_child_by_type(interface,"class_identifier"))
            supers.append(interface_name)
        methods = []
        fields = []
        static_init = []
        init = []
        for child in node.named_children:
            if child.type == "method_definition":
                self.parse(child,methods)
            if child.type == "field_definition":
                self.field_definition(child,fields,static_init,init,statements)
            if child.type == "annotation_directive":
                self.parse(child,statements)
        statements.append({"class_decl":{"attr":attr,"name":class_name,"supers":supers,"static_init":static_init,"init":init,"fields":fields,"methods":methods}})
```
找出所有的access_modifier加入attr列表。找出class_identifier子节点作为类的名字。找到super_directive，表示类的父类，加入supers列表。找到所有implements_directive，表示类实现的接口，也加入supers列表。再遍历所有子节点，如果是method_definition，对其解析加入methods列表。如果是field_definition，对其解析加入fields列表。如果是注解，对其解析加入statements。最后在statements列表中加入class_decl。
#### method_definition
```python
    def method_definition(self,node, statements):
        #print(node.sexp())
        access_modifiers=self.find_children_by_type(node,"access_modifier")
        attr=[]
        for modifier in access_modifiers:
            attr.append(self.read_node_text(modifier))
        if 'constructor' in self.read_node_text(node):
            attr.append('constructor')
        method_signature = self.find_child_by_type(node,"method_signature")
        method_name = self.read_node_text(self.find_child_by_type(method_signature,"method_identifier"))
        data_type = self.read_node_text(method_signature.named_children[-1])
        parameter=self.find_child_by_type(method_signature,"parameters")
        parameters_type =[]
        if parameter:
            for p in parameter.named_children:
                parameters_type.append(self.read_node_text(p))
        type_index=0
        parameters=[]
        init=[]
        body=[]
        for child in node.named_children:
            temp_parameters=[]
            if child.type == "method_signature" or child.type == "access_modifier":
                pass
            elif child.type == "param_directive":
                self.param_directive(child,temp_parameters)
            elif child.type == "parameter_directive":
                self.parameter_directive(child,temp_parameters)
            else:
                self.parse(child,body)
            for para in temp_parameters:
                if "parameter_decl" in para:
                    shadow_type=parameters_type[type_index]
                    type_index+=1
                    para["parameter_decl"]["data_type"] = shadow_type
                    parameters.append(para)
                elif "assign_stmt" in para:
                    init.append(para)
                else:
                    body.append(para)
        while type_index<len(parameters_type):
            shadow_type=parameters_type[type_index]
            type_index+=1
            parameters.append({"parameter_decl":{"name":None,"data_type":shadow_type}})
        statements.append({"method_decl":{"attr":attr,"data_type":data_type,"name":method_name,"parameters":parameters,"body":body}})
```
首先找出所有的access_modifier，且如果有constructor字段，也加入attr。找到method_signature中的method_identifier，是方法名。method_signature的最后一个子节点是方法的返回值类型。method_signature的parameters子节点是参数的类型。遍历node的子节点，跳过method_signature和access_modifier，对param_directive和parameter_directive进行解析。得到的parameter_decl语句中加上前面解析得到的参数类型，加入parameters，得到的assign_stmt语句加入init。node其余的子节点解析后加入body。如果有参数类型没有对应上，在parameters列表中加入name为空的parameter_decl。最后在statements中加入method_decl语句
#### field_definition
```python
    def field_definition(self,node, fields,static_init,init,body):
        #print(node.sexp())
        access_modifiers=self.find_child_by_type(node,"access_modifiers")
        attr=[]
        if access_modifiers is not None:
            access_modifier = self.find_children_by_type(access_modifiers,"access_modifier")
            for modifier in access_modifier:
                attr.append(self.read_node_text(modifier))
        field_identifier = self.read_node_text(self.find_child_by_type(node,"field_identifier"))
        field_type = self.read_node_text(self.find_child_by_type(node,"field_type"))
        shadow_value = None
        for child in node.named_children:
            if child.type != "access_modifiers" and child.type != "field_identifier" and child.type != "field_type" and child.type!= "annotation_directive":
                shadow_value = self.read_node_text(child)
            if child.type == "annotation_directive":
                self.parse(child,body)
        fields.append({"variable_decl":{"attr":attr,"name":field_identifier,"type":field_type}})
        if shadow_value:
            if "static" in attr:
                static_init.append({"field_write": {"receiver_object": self.global_this(),
                                                          "field": field_identifier, "source": shadow_value}})
            else:
                init.append({"field_write": {"receiver_object": self.global_this(),
                                                          "field": field_identifier, "source": shadow_value}})
```
找到所有access_modifier，加入attr。找到field_identifier，是域的名字。找到field_type，是域的类型。域的初值可能是多种类型的，不方便直接找，所以需要遍历所有子节点，找到shadow_value。如果是annotation，因为没有合适的位置加入，暂时放在最上层的statement中。如果有static字段，则将field_write语句加入static_init，否则加入init。
## 测试用例
#### 样例1：BracketedMemberNames.smali
```
.class public LBracketedMemberNames;

.super Ljava/lang/Object;

.field public static <test_field>:Ljava/lang/String; = "Hello World!"

.method public static main([Ljava/lang/String;)V
    .registers 2

    invoke-static {}, LBracketedMemberNames;->test_method()V

    return-void
.end method

.method public static test_method()V
    .registers 2

    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;

    sget-object v1, LBracketedMemberNames;-><test_field>:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V

    return-void
.end method

.method public static <test_method>()V
    .registers 2

    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;

    sget-object v1, LBracketedMemberNames;-><test_field>:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V

    # this will cause a verification error
    invoke-static {}, LBracketedMemberNames;-><test_method>()V

    return-void
.end method
```
#### 样例2：AnnotationTypes/Main.smali
```
.class public LMain;
.super Ljava/lang/Object;


#expected output:
#@ClassAnnotation()
#@MethodAnnotation()
#@FieldAnnotation()
#@ParameterAnnotation()


.method public static main([Ljava/lang/String;)V
    .registers 1

    invoke-static {}, LMain;->testClassAnnotation()V

    invoke-static {}, LMain;->testMethodAnnotation()V

    invoke-static {}, LMain;->testFieldAnnotation()V

    const-string v0, ""

    invoke-static {v0}, LMain;->testParameterAnnotation(Ljava/lang/String;)V 

	return-void
.end method

.annotation runtime LClassAnnotation;
.end annotation

.method public static testClassAnnotation()V
    .registers 3

    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;

    const-class v1, LMain;
    const-class v2, LClassAnnotation;

    invoke-virtual {v1, v2}, Ljava/lang/Class;->getAnnotation(Ljava/lang/Class;)Ljava/lang/annotation/Annotation;
    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/Object;)V

    return-void
.end method



.method public static testMethodAnnotation()V
    .registers 4

    .annotation runtime LMethodAnnotation;
    .end annotation

    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;

    const-class v1, LMain;
    const-string v2, "testMethodAnnotation"

    const/4 v3, 0
    new-array v3, v3, [Ljava/lang/Class;

    invoke-virtual {v1, v2, v3}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;
    move-result-object v1

    const-class v2, LMethodAnnotation;

    invoke-virtual {v1, v2}, Ljava/lang/reflect/Method;->getAnnotation(Ljava/lang/Class;)Ljava/lang/annotation/Annotation;
    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/Object;)V

    return-void
.end method


.field public static fieldAnnotationTest:Ljava/lang/Object;
    .annotation runtime LFieldAnnotation;
    .end annotation
.end field

.method public static testFieldAnnotation()V
    .registers 3

    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;

    const-class v1, LMain;
    const-string v2, "fieldAnnotationTest"

    invoke-virtual {v1, v2}, Ljava/lang/Class;->getField(Ljava/lang/String;)Ljava/lang/reflect/Field;
    move-result-object v1

    const-class v2, LFieldAnnotation;

    invoke-virtual {v1, v2}, Ljava/lang/reflect/Field;->getAnnotation(Ljava/lang/Class;)Ljava/lang/annotation/Annotation;
    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/Object;)V

    return-void
.end method


.method public static testParameterAnnotation(Ljava/lang/String;)V
    .registers 6

    .param p0    # Ljava/lang/String;
        .annotation runtime LParameterAnnotation;
        .end annotation
    .end param


    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;

    const-class v1, LMain;
    const-string v2, "testParameterAnnotation"

    const/4 v3, 1
    new-array v3, v3, [Ljava/lang/Class;

    const-class v4, Ljava/lang/String;
    const/4 v5, 0
    aput-object v4, v3, v5

    invoke-virtual {v1, v2, v3}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;
    move-result-object v1


    invoke-virtual {v1}, Ljava/lang/reflect/Method;->getParameterAnnotations()[[Ljava/lang/annotation/Annotation;
    move-result-object v1

    aget-object v1, v1, v5
    aget-object v1, v1, v5

    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/Object;)V

    return-void
.end method
```
#### 样例3：Enum.smali
```
.class public final enum LEnum;
.super Ljava/lang/Enum;

.field private static final synthetic $VALUES:[LEnum;

.field public static final enum 12:LEnum;

.method static constructor <clinit>()V
    .registers 4

    const/4 v3, 1
    const/4 v2, 0
    new-instance v0, LEnum;
    const-string v1, "12"
    invoke-direct {v0, v1, v2}, LEnum;-><init>(Ljava/lang/String;I)V
    sput-object v0, LEnum;->12:LEnum;

    const/4 v0, 1
    new-array v0, v0, [LEnum;
    sget-object v1, LEnum;->12:LEnum;
    aput-object v1, v0, v2
    
    sput-object v0, LEnum;->$VALUES:[LEnum;
    return-void
.end method

.method private constructor <init>(Ljava/lang/String;I)V
    .registers 3

    invoke-direct {p0, p1, p2}, Ljava/lang/Enum;-><init>(Ljava/lang/String;I)V
    return-void
.end method

.method public static valueOf(Ljava/lang/String;)LEnum;
    .registers 2

    const-class v0, LEnum;
    invoke-static {v0, p0}, Ljava/lang/Enum;->valueOf(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/Enum;
    move-result-object v1
    check-cast v1, LEnum;
    return-object v1
.end method

.method public static values()[LEnum;
    .registers 1

    sget-object v0, LEnum;->$VALUES:[LEnum;
    invoke-virtual {v0}, [LEnum;->clone()Ljava/lang/Object;
    move-result-object v0
    check-cast v0, [LEnum;
    return-object v0
.end method
```
## 测试结果
#### 样例1
```bash
[{'class_decl': {'attr': ['public'],
                 'name': 'LBracketedMemberNames;',
                 'supers': ['Ljava/lang/Object;'],
                 'static_init': [{'field_write': {'receiver_object': '@this',
                                                  'field': '<test_field>',
                                                  'source': '"Hello World!"'}}],
                 'init': [],
                 'fields': [{'variable_decl': {'attr': ['public', 'static'],
                                               'name': '<test_field>',
                                               'type': 'Ljava/lang/String;'}}],
                 'methods': [{'method_decl': {'attr': ['public', 'static'],
                                              'data_type': 'V',
                                              'name': 'main',
                                              'parameters': [{'parameter_decl': {'name': None,
                                                                                 'data_type': '[Ljava/lang/String;'}}],
                                              'body': [{'call_stmt': {'target': '%v0',
                                                                      'name': 'LBracketedMemberNames;->test_method',
                                                                      'args': [],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'return_stmt': {'target': ''}}]}},
                             {'method_decl': {'attr': ['public', 'static'],
                                              'data_type': 'V',
                                              'name': 'test_method',
                                              'parameters': [],
                                              'body': [{'field_read': {'target': 'v0',
                                                                       'receiver_object': 'Ljava/lang/System;',
                                                                       'field': 'out'}},
                                                       {'field_read': {'target': 'v1',
                                                                       'receiver_object': 'LBracketedMemberNames;',
                                                                       'field': '<test_field>'}},
                                                       {'call_stmt': {'target': '%v0',
                                                                      'name': 'Ljava/io/PrintStream;->println',
                                                                      'args': ['v0',
                                                                               'v1'],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'return_stmt': {'target': ''}}]}},
                             {'method_decl': {'attr': ['public', 'static'],
                                              'data_type': 'V',
                                              'name': '<test_method>',
                                              'parameters': [],
                                              'body': [{'field_read': {'target': 'v0',
                                                                       'receiver_object': 'Ljava/lang/System;',
                                                                       'field': 'out'}},
                                                       {'field_read': {'target': 'v1',
                                                                       'receiver_object': 'LBracketedMemberNames;',
                                                                       'field': '<test_field>'}},
                                                       {'call_stmt': {'target': '%v0',
                                                                      'name': 'Ljava/io/PrintStream;->println',
                                                                      'args': ['v0',
                                                                               'v1'],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'call_stmt': {'target': '%v1',
                                                                      'name': 'LBracketedMemberNames;-><test_method>',
                                                                      'args': [],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'return_stmt': {'target': ''}}]}}]}}]
[{'operation': 'class_decl',
  'stmt_id': 1,
  'attr': "['public']",
  'name': 'LBracketedMemberNames;',
  'supers': "['Ljava/lang/Object;']",
  'static_init': 2,
  'init': None,
  'fields': 4,
  'methods': 6},
 {'operation': 'block_start', 'stmt_id': 2, 'parent_stmt_id': 1},
 {'operation': 'field_write',
  'stmt_id': 3,
  'receiver_object': '@this',
  'field': '<test_field>',
  'source': '"Hello World!"'},
 {'operation': 'block_end', 'stmt_id': 2, 'parent_stmt_id': 1},
 {'operation': 'block_start', 'stmt_id': 4, 'parent_stmt_id': 1},
 {'operation': 'variable_decl',
  'stmt_id': 5,
  'attr': "['public', 'static']",
  'name': '<test_field>',
  'type': 'Ljava/lang/String;'},
 {'operation': 'block_end', 'stmt_id': 4, 'parent_stmt_id': 1},
 {'operation': 'block_start', 'stmt_id': 6, 'parent_stmt_id': 1},
 {'operation': 'method_decl',
  'stmt_id': 7,
  'attr': "['public', 'static']",
  'data_type': 'V',
  'name': 'main',
  'parameters': 8,
  'body': 10},
 {'operation': 'block_start', 'stmt_id': 8, 'parent_stmt_id': 7},
 {'operation': 'parameter_decl',
  'stmt_id': 9,
  'name': None,
  'data_type': '[Ljava/lang/String;'},
 {'operation': 'block_end', 'stmt_id': 8, 'parent_stmt_id': 7},
 {'operation': 'block_start', 'stmt_id': 10, 'parent_stmt_id': 7},
 {'operation': 'call_stmt',
  'stmt_id': 11,
  'target': '%v0',
  'name': 'LBracketedMemberNames;->test_method',
  'args': None,
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 12, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 10, 'parent_stmt_id': 7},
 {'operation': 'method_decl',
  'stmt_id': 13,
  'attr': "['public', 'static']",
  'data_type': 'V',
  'name': 'test_method',
  'parameters': None,
  'body': 14},
 {'operation': 'block_start', 'stmt_id': 14, 'parent_stmt_id': 13},
 {'operation': 'field_read',
  'stmt_id': 15,
  'target': 'v0',
  'receiver_object': 'Ljava/lang/System;',
  'field': 'out'},
 {'operation': 'field_read',
  'stmt_id': 16,
  'target': 'v1',
  'receiver_object': 'LBracketedMemberNames;',
  'field': '<test_field>'},
 {'operation': 'call_stmt',
  'stmt_id': 17,
  'target': '%v0',
  'name': 'Ljava/io/PrintStream;->println',
  'args': "['v0', 'v1']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 18, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 14, 'parent_stmt_id': 13},
 {'operation': 'method_decl',
  'stmt_id': 19,
  'attr': "['public', 'static']",
  'data_type': 'V',
  'name': '<test_method>',
  'parameters': None,
  'body': 20},
 {'operation': 'block_start', 'stmt_id': 20, 'parent_stmt_id': 19},
 {'operation': 'field_read',
  'stmt_id': 21,
  'target': 'v0',
  'receiver_object': 'Ljava/lang/System;',
  'field': 'out'},
 {'operation': 'field_read',
  'stmt_id': 22,
  'target': 'v1',
  'receiver_object': 'LBracketedMemberNames;',
  'field': '<test_field>'},
 {'operation': 'call_stmt',
  'stmt_id': 23,
  'target': '%v0',
  'name': 'Ljava/io/PrintStream;->println',
  'args': "['v0', 'v1']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'call_stmt',
  'stmt_id': 24,
  'target': '%v1',
  'name': 'LBracketedMemberNames;-><test_method>',
  'args': None,
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 25, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 20, 'parent_stmt_id': 19},
 {'operation': 'block_end', 'stmt_id': 6, 'parent_stmt_id': 1}]
```
#### 样例2
```bash
[{'annotation_type_decl': {'attr': 'runtime',
                           'name': 'LClassAnnotation;',
                           'init': [{}]}},
 {'annotation_type_decl': {'attr': 'runtime',
                           'name': 'LFieldAnnotation;',
                           'init': [{}]}},
 {'class_decl': {'attr': ['public'],
                 'name': 'LMain;',
                 'supers': ['Ljava/lang/Object;'],
                 'static_init': [],
                 'init': [],
                 'fields': [{'variable_decl': {'attr': ['public', 'static'],
                                               'name': 'fieldAnnotationTest',
                                               'type': 'Ljava/lang/Object;'}}],
                 'methods': [{'method_decl': {'attr': ['public', 'static'],
                                              'data_type': 'V',
                                              'name': 'main',
                                              'parameters': [{'parameter_decl': {'name': None,
                                                                                 'data_type': '[Ljava/lang/String;'}}],
                                              'body': [{'call_stmt': {'target': '%v0',
                                                                      'name': 'LMain;->testClassAnnotation',
                                                                      'args': [],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'call_stmt': {'target': '%v1',
                                                                      'name': 'LMain;->testMethodAnnotation',
                                                                      'args': [],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'call_stmt': {'target': '%v2',
                                                                      'name': 'LMain;->testFieldAnnotation',
                                                                      'args': [],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v0',
                                                                        'operand': ''}},
                                                       {'call_stmt': {'target': '%v3',
                                                                      'name': 'LMain;->testParameterAnnotation',
                                                                      'args': ['v0'],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'return_stmt': {'target': ''}}]}},
                             {'method_decl': {'attr': ['public', 'static'],
                                              'data_type': 'V',
                                              'name': 'testClassAnnotation',
                                              'parameters': [],
                                              'body': [{'field_read': {'target': 'v0',
                                                                       'receiver_object': 'Ljava/lang/System;',
                                                                       'field': 'out'}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': 'LMain;'}},
                                                       {'assign_stmt': {'target': 'v2',
                                                                        'operand': 'LClassAnnotation;'}},
                                                       {'call_stmt': {'target': '%v0',
                                                                      'name': 'Ljava/lang/Class;->getAnnotation',
                                                                      'args': ['v1',
                                                                               'v2'],
                                                                      'data_type': 'Ljava/lang/annotation/Annotation;',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': '%v0',
                                                                        'operator': 'result'}},
                                                       {'call_stmt': {'target': '%v1',
                                                                      'name': 'Ljava/io/PrintStream;->println',
                                                                      'args': ['v0',
                                                                               'v1'],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'return_stmt': {'target': ''}}]}},
                             {'method_decl': {'attr': ['public', 'static'],
                                              'data_type': 'V',
                                              'name': 'testMethodAnnotation',
                                              'parameters': [],
                                              'body': [{'annotation_type_decl': {'attr': 'runtime',
                                                                                 'name': 'LMethodAnnotation;',
                                                                                 'init': [{}]}},
                                                       {'field_read': {'target': 'v0',
                                                                       'receiver_object': 'Ljava/lang/System;',
                                                                       'field': 'out'}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': 'LMain;'}},
                                                       {'assign_stmt': {'target': 'v2',
                                                                        'operand': 'testMethodAnnotation'}},
                                                       {'assign_stmt': {'target': 'v3',
                                                                        'operand': '0'}},
                                                       {'new_array': {'type': '[Ljava/lang/Class;',
                                                                      'attr': 'v3',
                                                                      'target': '%v0'}},
                                                       {'assign_stmt': {'target': 'v3',
                                                                        'operand': '%v0'}},
                                                       {'call_stmt': {'target': '%v1',
                                                                      'name': 'Ljava/lang/Class;->getMethod',
                                                                      'args': ['v1',
                                                                               'v2',
                                                                               'v3'],
                                                                      'data_type': 'Ljava/lang/reflect/Method;',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': '%v1',
                                                                        'operator': 'result'}},
                                                       {'assign_stmt': {'target': 'v2',
                                                                        'operand': 'LMethodAnnotation;'}},
                                                       {'call_stmt': {'target': '%v2',
                                                                      'name': 'Ljava/lang/reflect/Method;->getAnnotation',
                                                                      'args': ['v1',
                                                                               'v2'],
                                                                      'data_type': 'Ljava/lang/annotation/Annotation;',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': '%v2',
                                                                        'operator': 'result'}},
                                                       {'call_stmt': {'target': '%v3',
                                                                      'name': 'Ljava/io/PrintStream;->println',
                                                                      'args': ['v0',
                                                                               'v1'],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'return_stmt': {'target': ''}}]}},
                             {'method_decl': {'attr': ['public', 'static'],
                                              'data_type': 'V',
                                              'name': 'testFieldAnnotation',
                                              'parameters': [],
                                              'body': [{'field_read': {'target': 'v0',
                                                                       'receiver_object': 'Ljava/lang/System;',
                                                                       'field': 'out'}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': 'LMain;'}},
                                                       {'assign_stmt': {'target': 'v2',
                                                                        'operand': 'fieldAnnotationTest'}},
                                                       {'call_stmt': {'target': '%v0',
                                                                      'name': 'Ljava/lang/Class;->getField',
                                                                      'args': ['v1',
                                                                               'v2'],
                                                                      'data_type': 'Ljava/lang/reflect/Field;',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': '%v0',
                                                                        'operator': 'result'}},
                                                       {'assign_stmt': {'target': 'v2',
                                                                        'operand': 'LFieldAnnotation;'}},
                                                       {'call_stmt': {'target': '%v1',
                                                                      'name': 'Ljava/lang/reflect/Field;->getAnnotation',
                                                                      'args': ['v1',
                                                                               'v2'],
                                                                      'data_type': 'Ljava/lang/annotation/Annotation;',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': '%v1',
                                                                        'operator': 'result'}},
                                                       {'call_stmt': {'target': '%v2',
                                                                      'name': 'Ljava/io/PrintStream;->println',
                                                                      'args': ['v0',
                                                                               'v1'],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'return_stmt': {'target': ''}}]}},
                             {'method_decl': {'attr': ['public', 'static'],
                                              'data_type': 'V',
                                              'name': 'testParameterAnnotation',
                                              'parameters': [{'parameter_decl': {'name': None,
                                                                                 'data_type': 'Ljava/lang/String;'}}],
                                              'body': [{'annotation_type_decl': {'attr': 'runtime',
                                                                                 'name': 'LParameterAnnotation;',
                                                                                 'init': [{}]}},
                                                       {'field_read': {'target': 'v0',
                                                                       'receiver_object': 'Ljava/lang/System;',
                                                                       'field': 'out'}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': 'LMain;'}},
                                                       {'assign_stmt': {'target': 'v2',
                                                                        'operand': 'testParameterAnnotation'}},
                                                       {'assign_stmt': {'target': 'v3',
                                                                        'operand': '1'}},
                                                       {'new_array': {'type': '[Ljava/lang/Class;',
                                                                      'attr': 'v3',
                                                                      'target': '%v0'}},
                                                       {'assign_stmt': {'target': 'v3',
                                                                        'operand': '%v0'}},
                                                       {'assign_stmt': {'target': 'v4',
                                                                        'operand': 'Ljava/lang/String;'}},
                                                       {'assign_stmt': {'target': 'v5',
                                                                        'operand': '0'}},
                                                       {'array_write': {'array': 'v3',
                                                                        'index': 'v5',
                                                                        'src': 'v4'}},
                                                       {'call_stmt': {'target': '%v1',
                                                                      'name': 'Ljava/lang/Class;->getMethod',
                                                                      'args': ['v1',
                                                                               'v2',
                                                                               'v3'],
                                                                      'data_type': 'Ljava/lang/reflect/Method;',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': '%v1',
                                                                        'operator': 'result'}},
                                                       {'call_stmt': {'target': '%v2',
                                                                      'name': 'Ljava/lang/reflect/Method;->getParameterAnnotations',
                                                                      'args': ['v1'],
                                                                      'data_type': '[[Ljava/lang/annotation/Annotation;',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': '%v2',
                                                                        'operator': 'result'}},
                                                       {'array_read': {'target': 'v1',
                                                                       'array': 'v1',
                                                                       'index': 'v5'}},
                                                       {'array_read': {'target': 'v1',
                                                                       'array': 'v1',
                                                                       'index': 'v5'}},
                                                       {'call_stmt': {'target': '%v3',
                                                                      'name': 'Ljava/io/PrintStream;->println',
                                                                      'args': ['v0',
                                                                               'v1'],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'return_stmt': {'target': ''}}]}}]}}]
[{'operation': 'annotation_type_decl',
  'stmt_id': 1,
  'attr': 'runtime',
  'name': 'LClassAnnotation;',
  'init': '[{}]'},
 {'operation': 'annotation_type_decl',
  'stmt_id': 2,
  'attr': 'runtime',
  'name': 'LFieldAnnotation;',
  'init': '[{}]'},
 {'operation': 'class_decl',
  'stmt_id': 3,
  'attr': "['public']",
  'name': 'LMain;',
  'supers': "['Ljava/lang/Object;']",
  'static_init': None,
  'init': None,
  'fields': 4,
  'methods': 6},
 {'operation': 'block_start', 'stmt_id': 4, 'parent_stmt_id': 3},
 {'operation': 'variable_decl',
  'stmt_id': 5,
  'attr': "['public', 'static']",
  'name': 'fieldAnnotationTest',
  'type': 'Ljava/lang/Object;'},
 {'operation': 'block_end', 'stmt_id': 4, 'parent_stmt_id': 3},
 {'operation': 'block_start', 'stmt_id': 6, 'parent_stmt_id': 3},
 {'operation': 'method_decl',
  'stmt_id': 7,
  'attr': "['public', 'static']",
  'data_type': 'V',
  'name': 'main',
  'parameters': 8,
  'body': 10},
 {'operation': 'block_start', 'stmt_id': 8, 'parent_stmt_id': 7},
 {'operation': 'parameter_decl',
  'stmt_id': 9,
  'name': None,
  'data_type': '[Ljava/lang/String;'},
 {'operation': 'block_end', 'stmt_id': 8, 'parent_stmt_id': 7},
 {'operation': 'block_start', 'stmt_id': 10, 'parent_stmt_id': 7},
 {'operation': 'call_stmt',
  'stmt_id': 11,
  'target': '%v0',
  'name': 'LMain;->testClassAnnotation',
  'args': None,
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'call_stmt',
  'stmt_id': 12,
  'target': '%v1',
  'name': 'LMain;->testMethodAnnotation',
  'args': None,
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'call_stmt',
  'stmt_id': 13,
  'target': '%v2',
  'name': 'LMain;->testFieldAnnotation',
  'args': None,
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'assign_stmt', 'stmt_id': 14, 'target': 'v0', 'operand': ''},
 {'operation': 'call_stmt',
  'stmt_id': 15,
  'target': '%v3',
  'name': 'LMain;->testParameterAnnotation',
  'args': "['v0']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 16, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 10, 'parent_stmt_id': 7},
 {'operation': 'method_decl',
  'stmt_id': 17,
  'attr': "['public', 'static']",
  'data_type': 'V',
  'name': 'testClassAnnotation',
  'parameters': None,
  'body': 18},
 {'operation': 'block_start', 'stmt_id': 18, 'parent_stmt_id': 17},
 {'operation': 'field_read',
  'stmt_id': 19,
  'target': 'v0',
  'receiver_object': 'Ljava/lang/System;',
  'field': 'out'},
 {'operation': 'assign_stmt',
  'stmt_id': 20,
  'target': 'v1',
  'operand': 'LMain;'},
 {'operation': 'assign_stmt',
  'stmt_id': 21,
  'target': 'v2',
  'operand': 'LClassAnnotation;'},
 {'operation': 'call_stmt',
  'stmt_id': 22,
  'target': '%v0',
  'name': 'Ljava/lang/Class;->getAnnotation',
  'args': "['v1', 'v2']",
  'data_type': 'Ljava/lang/annotation/Annotation;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 23,
  'target': 'v1',
  'operand': '%v0',
  'operator': 'result'},
 {'operation': 'call_stmt',
  'stmt_id': 24,
  'target': '%v1',
  'name': 'Ljava/io/PrintStream;->println',
  'args': "['v0', 'v1']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 25, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 18, 'parent_stmt_id': 17},
 {'operation': 'method_decl',
  'stmt_id': 26,
  'attr': "['public', 'static']",
  'data_type': 'V',
  'name': 'testMethodAnnotation',
  'parameters': None,
  'body': 27},
 {'operation': 'block_start', 'stmt_id': 27, 'parent_stmt_id': 26},
 {'operation': 'annotation_type_decl',
  'stmt_id': 28,
  'attr': 'runtime',
  'name': 'LMethodAnnotation;',
  'init': '[{}]'},
 {'operation': 'field_read',
  'stmt_id': 29,
  'target': 'v0',
  'receiver_object': 'Ljava/lang/System;',
  'field': 'out'},
 {'operation': 'assign_stmt',
  'stmt_id': 30,
  'target': 'v1',
  'operand': 'LMain;'},
 {'operation': 'assign_stmt',
  'stmt_id': 31,
  'target': 'v2',
  'operand': 'testMethodAnnotation'},
 {'operation': 'assign_stmt', 'stmt_id': 32, 'target': 'v3', 'operand': '0'},
 {'operation': 'new_array',
  'stmt_id': 33,
  'type': '[Ljava/lang/Class;',
  'attr': 'v3',
  'target': '%v0'},
 {'operation': 'assign_stmt', 'stmt_id': 34, 'target': 'v3', 'operand': '%v0'},
 {'operation': 'call_stmt',
  'stmt_id': 35,
  'target': '%v1',
  'name': 'Ljava/lang/Class;->getMethod',
  'args': "['v1', 'v2', 'v3']",
  'data_type': 'Ljava/lang/reflect/Method;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 36,
  'target': 'v1',
  'operand': '%v1',
  'operator': 'result'},
 {'operation': 'assign_stmt',
  'stmt_id': 37,
  'target': 'v2',
  'operand': 'LMethodAnnotation;'},
 {'operation': 'call_stmt',
  'stmt_id': 38,
  'target': '%v2',
  'name': 'Ljava/lang/reflect/Method;->getAnnotation',
  'args': "['v1', 'v2']",
  'data_type': 'Ljava/lang/annotation/Annotation;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 39,
  'target': 'v1',
  'operand': '%v2',
  'operator': 'result'},
 {'operation': 'call_stmt',
  'stmt_id': 40,
  'target': '%v3',
  'name': 'Ljava/io/PrintStream;->println',
  'args': "['v0', 'v1']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 41, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 27, 'parent_stmt_id': 26},
 {'operation': 'method_decl',
  'stmt_id': 42,
  'attr': "['public', 'static']",
  'data_type': 'V',
  'name': 'testFieldAnnotation',
  'parameters': None,
  'body': 43},
 {'operation': 'block_start', 'stmt_id': 43, 'parent_stmt_id': 42},
 {'operation': 'field_read',
  'stmt_id': 44,
  'target': 'v0',
  'receiver_object': 'Ljava/lang/System;',
  'field': 'out'},
 {'operation': 'assign_stmt',
  'stmt_id': 45,
  'target': 'v1',
  'operand': 'LMain;'},
 {'operation': 'assign_stmt',
  'stmt_id': 46,
  'target': 'v2',
  'operand': 'fieldAnnotationTest'},
 {'operation': 'call_stmt',
  'stmt_id': 47,
  'target': '%v0',
  'name': 'Ljava/lang/Class;->getField',
  'args': "['v1', 'v2']",
  'data_type': 'Ljava/lang/reflect/Field;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 48,
  'target': 'v1',
  'operand': '%v0',
  'operator': 'result'},
 {'operation': 'assign_stmt',
  'stmt_id': 49,
  'target': 'v2',
  'operand': 'LFieldAnnotation;'},
 {'operation': 'call_stmt',
  'stmt_id': 50,
  'target': '%v1',
  'name': 'Ljava/lang/reflect/Field;->getAnnotation',
  'args': "['v1', 'v2']",
  'data_type': 'Ljava/lang/annotation/Annotation;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 51,
  'target': 'v1',
  'operand': '%v1',
  'operator': 'result'},
 {'operation': 'call_stmt',
  'stmt_id': 52,
  'target': '%v2',
  'name': 'Ljava/io/PrintStream;->println',
  'args': "['v0', 'v1']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 53, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 43, 'parent_stmt_id': 42},
 {'operation': 'method_decl',
  'stmt_id': 54,
  'attr': "['public', 'static']",
  'data_type': 'V',
  'name': 'testParameterAnnotation',
  'parameters': 55,
  'body': 57},
 {'operation': 'block_start', 'stmt_id': 55, 'parent_stmt_id': 54},
 {'operation': 'parameter_decl',
  'stmt_id': 56,
  'name': None,
  'data_type': 'Ljava/lang/String;'},
 {'operation': 'block_end', 'stmt_id': 55, 'parent_stmt_id': 54},
 {'operation': 'block_start', 'stmt_id': 57, 'parent_stmt_id': 54},
 {'operation': 'annotation_type_decl',
  'stmt_id': 58,
  'attr': 'runtime',
  'name': 'LParameterAnnotation;',
  'init': '[{}]'},
 {'operation': 'field_read',
  'stmt_id': 59,
  'target': 'v0',
  'receiver_object': 'Ljava/lang/System;',
  'field': 'out'},
 {'operation': 'assign_stmt',
  'stmt_id': 60,
  'target': 'v1',
  'operand': 'LMain;'},
 {'operation': 'assign_stmt',
  'stmt_id': 61,
  'target': 'v2',
  'operand': 'testParameterAnnotation'},
 {'operation': 'assign_stmt', 'stmt_id': 62, 'target': 'v3', 'operand': '1'},
 {'operation': 'new_array',
  'stmt_id': 63,
  'type': '[Ljava/lang/Class;',
  'attr': 'v3',
  'target': '%v0'},
 {'operation': 'assign_stmt', 'stmt_id': 64, 'target': 'v3', 'operand': '%v0'},
 {'operation': 'assign_stmt',
  'stmt_id': 65,
  'target': 'v4',
  'operand': 'Ljava/lang/String;'},
 {'operation': 'assign_stmt', 'stmt_id': 66, 'target': 'v5', 'operand': '0'},
 {'operation': 'array_write',
  'stmt_id': 67,
  'array': 'v3',
  'index': 'v5',
  'src': 'v4'},
 {'operation': 'call_stmt',
  'stmt_id': 68,
  'target': '%v1',
  'name': 'Ljava/lang/Class;->getMethod',
  'args': "['v1', 'v2', 'v3']",
  'data_type': 'Ljava/lang/reflect/Method;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 69,
  'target': 'v1',
  'operand': '%v1',
  'operator': 'result'},
 {'operation': 'call_stmt',
  'stmt_id': 70,
  'target': '%v2',
  'name': 'Ljava/lang/reflect/Method;->getParameterAnnotations',
  'args': "['v1']",
  'data_type': '[[Ljava/lang/annotation/Annotation;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 71,
  'target': 'v1',
  'operand': '%v2',
  'operator': 'result'},
 {'operation': 'array_read',
  'stmt_id': 72,
  'target': 'v1',
  'array': 'v1',
  'index': 'v5'},
 {'operation': 'array_read',
  'stmt_id': 73,
  'target': 'v1',
  'array': 'v1',
  'index': 'v5'},
 {'operation': 'call_stmt',
  'stmt_id': 74,
  'target': '%v3',
  'name': 'Ljava/io/PrintStream;->println',
  'args': "['v0', 'v1']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 75, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 57, 'parent_stmt_id': 54},
 {'operation': 'block_end', 'stmt_id': 6, 'parent_stmt_id': 3}]
```
#### 样例3
```bash
[{'class_decl': {'attr': ['public', 'final', 'enum'],
                 'name': 'LEnum;',
                 'supers': ['Ljava/lang/Enum;'],
                 'static_init': [],
                 'init': [],
                 'fields': [{'variable_decl': {'attr': ['private', 'static',
                                                        'final', 'synthetic'],
                                               'name': '$VALUES',
                                               'type': '[LEnum;'}},
                            {'variable_decl': {'attr': ['public', 'static',
                                                        'final', 'enum'],
                                               'name': '12',
                                               'type': 'LEnum;'}}],
                 'methods': [{'method_decl': {'attr': ['static', 'constructor'],
                                              'data_type': 'V',
                                              'name': '<clinit>',
                                              'parameters': [],
                                              'body': [{'assign_stmt': {'target': 'v3',
                                                                        'operand': '1'}},
                                                       {'assign_stmt': {'target': 'v2',
                                                                        'operand': '0'}},
                                                       {'new_instance': {'data_type': 'LEnum;',
                                                                         'target': '%v0'}},
                                                       {'assign_stmt': {'target': 'v0',
                                                                        'operand': '%v0'}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': '12'}},
                                                       {'call_stmt': {'target': '%v1',
                                                                      'name': 'LEnum;-><init>',
                                                                      'args': ['v0',
                                                                               'v1',
                                                                               'v2'],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'field_write': {'receiver_object': 'LEnum;',
                                                                        'field': '12',
                                                                        'source': 'v0'}},
                                                       {'assign_stmt': {'target': 'v0',
                                                                        'operand': '1'}},
                                                       {'new_array': {'type': '[LEnum;',
                                                                      'attr': 'v0',
                                                                      'target': '%v2'}},
                                                       {'assign_stmt': {'target': 'v0',
                                                                        'operand': '%v2'}},
                                                       {'field_read': {'target': 'v1',
                                                                       'receiver_object': 'LEnum;',
                                                                       'field': '12'}},
                                                       {'array_write': {'array': 'v0',
                                                                        'index': 'v2',
                                                                        'src': 'v1'}},
                                                       {'field_write': {'receiver_object': 'LEnum;',
                                                                        'field': '$VALUES',
                                                                        'source': 'v0'}},
                                                       {'return_stmt': {'target': ''}}]}},
                             {'method_decl': {'attr': ['private',
                                                       'constructor'],
                                              'data_type': 'V',
                                              'name': '<init>',
                                              'parameters': [{'parameter_decl': {'name': None,
                                                                                 'data_type': 'Ljava/lang/String;'}},
                                                             {'parameter_decl': {'name': None,
                                                                                 'data_type': 'I'}}],
                                              'body': [{'call_stmt': {'target': '%v0',
                                                                      'name': 'Ljava/lang/Enum;-><init>',
                                                                      'args': ['p0',
                                                                               'p1',
                                                                               'p2'],
                                                                      'data_type': 'V',
                                                                      'prototype': ''}},
                                                       {'return_stmt': {'target': ''}}]}},
                             {'method_decl': {'attr': ['public', 'static'],
                                              'data_type': 'LEnum;',
                                              'name': 'valueOf',
                                              'parameters': [{'parameter_decl': {'name': None,
                                                                                 'data_type': 'Ljava/lang/String;'}}],
                                              'body': [{'assign_stmt': {'target': 'v0',
                                                                        'operand': 'LEnum;'}},
                                                       {'call_stmt': {'target': '%v0',
                                                                      'name': 'Ljava/lang/Enum;->valueOf',
                                                                      'args': ['v0',
                                                                               'p0'],
                                                                      'data_type': 'Ljava/lang/Enum;',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v1',
                                                                        'operand': '%v0',
                                                                        'operator': 'result'}},
                                                       {'type_cast_stmt': {'target': '%v1',
                                                                           'data_type': 'LEnum;',
                                                                           'source': 'v1',
                                                                           'error': '%v2'}},
                                                       {'return_stmt': {'target': 'v1'}}]}},
                             {'method_decl': {'attr': ['public', 'static'],
                                              'data_type': '[LEnum;',
                                              'name': 'values',
                                              'parameters': [],
                                              'body': [{'field_read': {'target': 'v0',
                                                                       'receiver_object': 'LEnum;',
                                                                       'field': '$VALUES'}},
                                                       {'call_stmt': {'target': '%v0',
                                                                      'name': '[LEnum;->clone',
                                                                      'args': ['v0'],
                                                                      'data_type': 'Ljava/lang/Object;',
                                                                      'prototype': ''}},
                                                       {'assign_stmt': {'target': 'v0',
                                                                        'operand': '%v0',
                                                                        'operator': 'result'}},
                                                       {'type_cast_stmt': {'target': '%v1',
                                                                           'data_type': '[LEnum;',
                                                                           'source': 'v0',
                                                                           'error': '%v2'}},
                                                       {'return_stmt': {'target': 'v0'}}]}}]}}]
[{'operation': 'class_decl',
  'stmt_id': 1,
  'attr': "['public', 'final', 'enum']",
  'name': 'LEnum;',
  'supers': "['Ljava/lang/Enum;']",
  'static_init': None,
  'init': None,
  'fields': 2,
  'methods': 5},
 {'operation': 'block_start', 'stmt_id': 2, 'parent_stmt_id': 1},
 {'operation': 'variable_decl',
  'stmt_id': 3,
  'attr': "['private', 'static', 'final', 'synthetic']",
  'name': '$VALUES',
  'type': '[LEnum;'},
 {'operation': 'variable_decl',
  'stmt_id': 4,
  'attr': "['public', 'static', 'final', 'enum']",
  'name': '12',
  'type': 'LEnum;'},
 {'operation': 'block_end', 'stmt_id': 2, 'parent_stmt_id': 1},
 {'operation': 'block_start', 'stmt_id': 5, 'parent_stmt_id': 1},
 {'operation': 'method_decl',
  'stmt_id': 6,
  'attr': "['static', 'constructor']",
  'data_type': 'V',
  'name': '<clinit>',
  'parameters': None,
  'body': 7},
 {'operation': 'block_start', 'stmt_id': 7, 'parent_stmt_id': 6},
 {'operation': 'assign_stmt', 'stmt_id': 8, 'target': 'v3', 'operand': '1'},
 {'operation': 'assign_stmt', 'stmt_id': 9, 'target': 'v2', 'operand': '0'},
 {'operation': 'new_instance',
  'stmt_id': 10,
  'data_type': 'LEnum;',
  'target': '%v0'},
 {'operation': 'assign_stmt', 'stmt_id': 11, 'target': 'v0', 'operand': '%v0'},
 {'operation': 'assign_stmt', 'stmt_id': 12, 'target': 'v1', 'operand': '12'},
 {'operation': 'call_stmt',
  'stmt_id': 13,
  'target': '%v1',
  'name': 'LEnum;-><init>',
  'args': "['v0', 'v1', 'v2']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'field_write',
  'stmt_id': 14,
  'receiver_object': 'LEnum;',
  'field': '12',
  'source': 'v0'},
 {'operation': 'assign_stmt', 'stmt_id': 15, 'target': 'v0', 'operand': '1'},
 {'operation': 'new_array',
  'stmt_id': 16,
  'type': '[LEnum;',
  'attr': 'v0',
  'target': '%v2'},
 {'operation': 'assign_stmt', 'stmt_id': 17, 'target': 'v0', 'operand': '%v2'},
 {'operation': 'field_read',
  'stmt_id': 18,
  'target': 'v1',
  'receiver_object': 'LEnum;',
  'field': '12'},
 {'operation': 'array_write',
  'stmt_id': 19,
  'array': 'v0',
  'index': 'v2',
  'src': 'v1'},
 {'operation': 'field_write',
  'stmt_id': 20,
  'receiver_object': 'LEnum;',
  'field': '$VALUES',
  'source': 'v0'},
 {'operation': 'return_stmt', 'stmt_id': 21, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 7, 'parent_stmt_id': 6},
 {'operation': 'method_decl',
  'stmt_id': 22,
  'attr': "['private', 'constructor']",
  'data_type': 'V',
  'name': '<init>',
  'parameters': 23,
  'body': 26},
 {'operation': 'block_start', 'stmt_id': 23, 'parent_stmt_id': 22},
 {'operation': 'parameter_decl',
  'stmt_id': 24,
  'name': None,
  'data_type': 'Ljava/lang/String;'},
 {'operation': 'parameter_decl', 'stmt_id': 25, 'name': None, 'data_type': 'I'},
 {'operation': 'block_end', 'stmt_id': 23, 'parent_stmt_id': 22},
 {'operation': 'block_start', 'stmt_id': 26, 'parent_stmt_id': 22},
 {'operation': 'call_stmt',
  'stmt_id': 27,
  'target': '%v0',
  'name': 'Ljava/lang/Enum;-><init>',
  'args': "['p0', 'p1', 'p2']",
  'data_type': 'V',
  'prototype': ''},
 {'operation': 'return_stmt', 'stmt_id': 28, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 26, 'parent_stmt_id': 22},
 {'operation': 'method_decl',
  'stmt_id': 29,
  'attr': "['public', 'static']",
  'data_type': 'LEnum;',
  'name': 'valueOf',
  'parameters': 30,
  'body': 32},
 {'operation': 'block_start', 'stmt_id': 30, 'parent_stmt_id': 29},
 {'operation': 'parameter_decl',
  'stmt_id': 31,
  'name': None,
  'data_type': 'Ljava/lang/String;'},
 {'operation': 'block_end', 'stmt_id': 30, 'parent_stmt_id': 29},
 {'operation': 'block_start', 'stmt_id': 32, 'parent_stmt_id': 29},
 {'operation': 'assign_stmt',
  'stmt_id': 33,
  'target': 'v0',
  'operand': 'LEnum;'},
 {'operation': 'call_stmt',
  'stmt_id': 34,
  'target': '%v0',
  'name': 'Ljava/lang/Enum;->valueOf',
  'args': "['v0', 'p0']",
  'data_type': 'Ljava/lang/Enum;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 35,
  'target': 'v1',
  'operand': '%v0',
  'operator': 'result'},
 {'operation': 'type_cast_stmt',
  'stmt_id': 36,
  'target': '%v1',
  'data_type': 'LEnum;',
  'source': 'v1',
  'error': '%v2'},
 {'operation': 'return_stmt', 'stmt_id': 37, 'target': 'v1'},
 {'operation': 'block_end', 'stmt_id': 32, 'parent_stmt_id': 29},
 {'operation': 'method_decl',
  'stmt_id': 38,
  'attr': "['public', 'static']",
  'data_type': '[LEnum;',
  'name': 'values',
  'parameters': None,
  'body': 39},
 {'operation': 'block_start', 'stmt_id': 39, 'parent_stmt_id': 38},
 {'operation': 'field_read',
  'stmt_id': 40,
  'target': 'v0',
  'receiver_object': 'LEnum;',
  'field': '$VALUES'},
 {'operation': 'call_stmt',
  'stmt_id': 41,
  'target': '%v0',
  'name': '[LEnum;->clone',
  'args': "['v0']",
  'data_type': 'Ljava/lang/Object;',
  'prototype': ''},
 {'operation': 'assign_stmt',
  'stmt_id': 42,
  'target': 'v0',
  'operand': '%v0',
  'operator': 'result'},
 {'operation': 'type_cast_stmt',
  'stmt_id': 43,
  'target': '%v1',
  'data_type': '[LEnum;',
  'source': 'v0',
  'error': '%v2'},
 {'operation': 'return_stmt', 'stmt_id': 44, 'target': 'v0'},
 {'operation': 'block_end', 'stmt_id': 39, 'parent_stmt_id': 38},
 {'operation': 'block_end', 'stmt_id': 5, 'parent_stmt_id': 1}]
```