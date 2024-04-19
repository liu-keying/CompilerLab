#!/usr/bin/env python3

from . import common_parser
import re

type_list = ['variable', 'parameter', 'number', 'string', 'float', 'character', 'identifier', 'list', 'body', 'class_identifier']

class Parser(common_parser.Parser):
    def is_comment(self, node):
        return node.type == "comment"
        #pass

    def is_identifier(self, node):
        return node.type == "identifier" or node.type == "variable" or node.type == "parameter" 
        # pass

    def obtain_literal_handler(self, node):
        LITERAL_MAP = {
        }

        return LITERAL_MAP.get(node.type, None)

    def is_literal(self, node):
        return self.obtain_literal_handler(node) is not None

    def literal(self, node, statements, replacement):
        handler = self.obtain_literal_handler(node)
        return handler(node, statements, replacement)

    def check_declaration_handler(self, node):
        DECLARATION_HANDLER_MAP = {
        }
        return DECLARATION_HANDLER_MAP.get(node.type, None)

    def is_declaration(self, node):
        return self.check_declaration_handler(node) is not None

    def declaration(self, node, statements):
        handler = self.check_declaration_handler(node)
        return handler(node, statements)

    def check_expression_handler(self, node):
        EXPRESSION_HANDLER_MAP = {
            "expression": self.primary_expression
        }

        return EXPRESSION_HANDLER_MAP.get(node.type, None)

    def is_expression(self, node):
        return self.check_expression_handler(node) is not None

    def expression(self, node, statements):
        handler = self.check_expression_handler(node)
        return handler(node, statements)

    def check_statement_handler(self, node):
        STATEMENT_HANDLER_MAP = {
        }
        return STATEMENT_HANDLER_MAP.get(node.type, None)

    def is_statement(self, node):
        return self.check_statement_handler(node) is not None

    def statement(self, node, statements):
        handler = self.check_statement_handler(node)
        return handler(node, statements)
    
    def primary_expression(self, node, statements):
        print(node.sexp())
        opcode = self.find_child_by_type(node, "opcode")
        shadow_opcode = self.read_node_text(opcode)
        print(shadow_opcode)
        values = {}
        for type in type_list:
            values[type] = []
        for type in type_list:
            values[type].extend(self.find_children_by_type(node, type))
        if shadow_opcode == "nop":
            return ''
        elif re.compile(r'^move.*').match(shadow_opcode):
            if "result" in shadow_opcode in shadow_opcode:
                v0 = self.read_node_text(values["variable"][0])
                tmp_var = self.tmp_variable(statements)
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_var, "operator": "result"}})
            elif "exception" in shadow_opcode:
                v0 = self.read_node_text(values["variable"][0])
                tmp_var = self.tmp_variable(statements)
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_var, "operator": "exception"}})
            else:
                v0 = self.read_node_text(values["variable"][0])
                v1 = self.read_node_text(values["variable"][1])
                statements.append({"assign_stmt": {"target": v0, "operand": v1}})
            return v0
        elif re.compile(r'^return.*').match(shadow_opcode):
            if "void" in shadow_opcode:
                statements.append({"return_stmt": {"target": ''}})
                return ''
            else:
                v0 = self.read_node_text(values["variable"][0])
                statements.append({"return_stmt": {"target": v0}})
                return v0
        elif re.compile(r'^const.*').match(shadow_opcode):
            v0 = self.read_node_text(values["variable"][0])
            if 'string' in shadow_opcode:
                string = self.find_child_by_type(values["string"][0], 'string_fragment')
                shadow_string = self.read_node_text(string)
                print(shadow_string)
                statements.append({"assign_stmt": {"target": v0, "operand": shadow_string}})
            elif 'class' in shadow_opcode: 
                pass
            else:
                number = values["number"][0]
                shadow_number = self.read_node_text(number)
                statements.append({"assign_stmt": {"target": v0, "operand": shadow_number}})
            return v0
        elif re.compile(r'^check.*').match(shadow_opcode):
            v0 = self.read_node_text(values["variable"][0])
            class_identifier = values['class_identifier'][0]
            shadow_class = self.read_node_text(class_identifier)
            statements.append({"assign_stmt": {"target": v0, "operand": shadow_class, "operator": "check-cast"}})
            return v0
        elif shadow_opcode == "instance-of":
            v1 = self.read_node_text(values["variable"][1])
            v2 = self.parse(values[2], statements)
            tmp_var = self.tmp_variable(statements)
            statements.append({"assign_stmt":
                                   {"target": tmp_var, "operator": "instanceof", "operand": v1,
                                    "operand2": v2}})
            v0 = self.read_node_text(values["variable"][0])
            statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
            return v0
        elif shadow_opcode == 'array-length':
            v0 = self.read_node_text(values["variable"][0])
            v1 = self.read_node_text(values["variable"][1])
            statements.append({"assign_stmt": {"target": v0, "operand": v1, "operator": "array-length"}})
            return v0
        elif re.compile(r'^new.*').match(shadow_opcode):
            # new-instance vA, type-id 创建一个类的新实例（对象）, type-id: 是该类的类型标识符，指定要创建哪个类的实例
            # new-array v0, v1, type-id 声明数组并为其分配内存和类型, 创建一个数组，其大小由寄存器v1的值决定。数组的引用将会被存储在v0寄存器中。
            if shadow_opcode == "new-instance":
                glang_node = {}
                mytype = self.read_node_text(values['class_identifier'][0])
                glang_node["data_type"] = mytype
                tmp_var = self.tmp_variable(statements)
                glang_node["target"] = tmp_var
                statements.append({"new_instance": glang_node})
                v0 = self.read_node_text(values["variable"][0])
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
                return v0
            else:
                type = self.read_node_text(self.find_child_by_type_type(node, "array_type", "primitive_type"))
                v0 = self.read_node_text(values["variable"][0])
                v1 = self.read_node_text(values["variable"][1])
                tmp_var = self.tmp_variable(statements)
                statements.append({"new_array": {"type": type, "attr": v1, "target": tmp_var}})
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
                return v0
        elif re.compile(r'^filled.*').match(shadow_opcode):
            # filled-new-array创建一个新的数组，并立即用给定的值填充它
            # filled-new-array {v0, v1, v2}, [I 这里，[I表示一个int类型的数组，v0, v1, v2是将被放入新数组的值所在的寄存器。数组创建和填充之后，其引用会被放置在某个寄存器中
            # filled-new-array/range {v0 .. v5}, [I 使用了v0到v5寄存器中的值来填充一个新的int数组
            if "range" in shadow_opcode:
                type = self.read_node_text(self.find_child_by_type_type(node, "array_type", "primitive_type"))
                range_node = self.read_node_text(self.find_child_by_type(node,"range"))
                tmp_var = self.tmp_variable(statements)
                statements.append({"new_array": {"type": type, "target": tmp_var}})
                statements.append({"assign_stmt": {"target": range_node, "operand": tmp_var, "operator": "filled-new-array/range"}})
                return range_node
            else:
                pass
                type = self.read_node_text(self.find_child_by_type_type(node, "array_type", "primitive_type"))
                v0 = self.read_node_text(values["list"][0])
                tmp_var = self.tmp_variable(statements)
                statements.append({"new_array": {"type": type, "target": tmp_var}})
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_var, "operator": "filled-new-array"}})
                return v0
        elif re.compile(r'^fill-.*').match(shadow_opcode):
            # fill-array-data v0, :array_data 将预定义的数据集合填充到之前声明的数组中
            v0 = self.read_node_text(values["variable"][0])
            label = self.read_node_text(self.find_child_by_type(node, "label"))
            statements.append({"assign_stmt": {"target": v0, "operand": label, "operator": "fill-array-data"}})
            return v0
        elif re.compile(r'^throw.*').match(shadow_opcode):
            shadow_expr = self.read_node_text(values["variable"][0])
            statements.append({"throw_stmt": {"target": shadow_expr}})
            return
        elif re.compile(r'^goto.*').match(shadow_opcode):
            # 跳转到同一方法内的指定位置继续执行代码
            # goto :label_start :label_start 是一个标签，可以在代码中跳转到它标记的位置。
            label = self.read_node_text(self.find_child_by_type(node, "label"))
            statements.append({"goto": {"target": label}})
            return
        elif re.search(r'-switch$', shadow_opcode):
            # packed switch语句的case标签密集排布时使用
            # sparse switch语句中的case标签稀疏分布时使用
            '''packed-switch 0x1
                :case_0x1
                :case_0x2
                :case_0x3'''
            '''sparse-switch
                0x1 -> :case_0x1
                0x3 -> :case_0x3
                0xA -> :case_0xA'''
            pass
        elif re.compile(r'^cmp.*').match(shadow_opcode):

            pass
        elif re.compile(r'^if-.*').match(shadow_opcode):
            pass
        elif re.compile(r'^aget.*').match(shadow_opcode):
            pass
        elif re.compile(r'^aput.*').match(shadow_opcode):
            pass
        

        elif re.compile(r'^add.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "+")
        elif re.compile(r'^sub.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "-")
        elif re.compile(r'^mul.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "*")
        elif re.compile(r'^div.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "/")
        elif re.compile(r'^rem.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "%")
        elif re.compile(r'^and.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "&")
        elif re.compile(r'^or.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "|")
        elif re.compile(r'^xor.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "^")
        elif re.compile(r'^shl.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "<<")
        elif re.compile(r'^shr.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, ">>")
        elif re.compile(r'^ushr.*/2addr').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, ">>>")
        elif re.compile(r'^add.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, "+")
        elif re.compile(r'^sub.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, "-")
        elif re.compile(r'^mul.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, "*")
        elif re.compile(r'^div.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, "/")
        elif re.compile(r'^rem.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, "%")
        elif re.compile(r'^and.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, "&")
        elif re.compile(r'^or.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, "|")
        elif re.compile(r'^xor.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, "^")
        elif re.compile(r'^shl.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, "<<")
        elif re.compile(r'^shr.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, ">>")
        elif re.compile(r'^ushr.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression(node, statements, ">>>")
        
        elif re.compile(r'^neg.*').match(shadow_opcode):
            return self.unary_expression(node, statements, "-")
        elif re.compile(r'^not.*').match(shadow_opcode):
            return self.unary_expression(node, statements, "~")
        
        elif shadow_opcode in ['int-to-long','int-to-float','int-to-double','long-to-int',
                               'long-to-float','long-to-double','float-to-int','float-to-long',
                               'float-to-double','double-to-int','double-to-long',
                               'double-to-float','int-to-byte','int-to-char','int-to-short']:
            return self.unary_expression(node, statements, 'cast')
        

    def unary_expression(self, node, statements,op):
        dest = self.parse(node.named_children[1], statements)
        source = self.parse(node.named_children[2], statements)
        statements.append({"assign_stmt": {"target": dest, "operator": op, "operand": source}})
        return dest
    
    def binary_expression_2addr(self, node, statements, op):
        dest = self.parse(node.named_children[1], statements)
        source = self.parse(node.named_children[2], statements)
        statements.append({"assign_stmt": {"target": dest, "operator": op, "operand": dest,"operand2": source}})
        return dest

    def binary_expression(self, node, statements, op):
        dest = self.parse(node.named_children[1], statements)
        source1 = self.parse(node.named_children[2], statements)
        source2 = self.parse(node.named_children[3], statements)
        statements.append({"assign_stmt": {"target": dest, "operator": op, "operand": source1,"operand2": source2}})
        return dest
        
