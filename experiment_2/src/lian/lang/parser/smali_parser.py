#!/usr/bin/env python3

from . import common_parser
import re


class Parser(common_parser.Parser):
    def is_comment(self, node):
        return node.type == "comment"
        #pass

    def is_identifier(self, node):
        return node.type == "identifier" or node.type == "variable" or node.type == "parameter" 
        # pass

    def obtain_literal_handler(self, node):
        LITERAL_MAP = {
            "number":self.regular_number_literal,
            "float" : self.regular_number_literal,
            "NaN":self.regular_literal,
            "Infinity":self.regular_literal,
            "string":self.string_literal,
            "boolean":self.regular_literal,
            "character":self.character_literal,
            "null":self.regular_literal
        }
        return LITERAL_MAP.get(node.type, None)

    def is_literal(self, node):
        return self.obtain_literal_handler(node) is not None

    def literal(self, node, statements, replacement):
        handler = self.obtain_literal_handler(node)
        return handler(node, statements, replacement)
    
    def string_literal(self, node, statements, replacement):
        replacement = []
        for child in node.named_children:
            self.parse(child, statements, replacement)

        ret = self.read_node_text(node)
        if replacement:
            for r in replacement:
                (expr, value) = r
                ret = ret.replace(self.read_node_text(expr), value)

        ret = self.handle_hex_string(ret)

        return self.escape_string(ret)

    def character_literal(self, node, statements, replacement):
        value = self.read_node_text(node)
        return "'%s'" % value
    
    def regular_number_literal(self, node, statements, replacement):
        value = self.read_node_text(node)
        #value=re.compile(r'[LlSsTtf]').sub("",value)
        value = self.common_eval(value)
        return self.read_node_text(node)

    def regular_literal(self, node, statements, replacement):
        return self.read_node_text(node)

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
        variables = self.find_children_by_type(node, "variable")
        parameters = self.find_children_by_type(node, "parameter")
        values = variables + parameters
        print(values)
        # return
        # values = self.find_children_by_type(node, "variable")
        if shadow_opcode == "nop":
            return ''
        elif re.compile(r'^move.*').match(shadow_opcode):
            if "result" in shadow_opcode or "exception" in shadow_opcode:
                v0 = self.read_node_text(values[0])
                tmp_var = self.tmp_variable(statements)
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
            else:
                v0 = self.read_node_text(values[0])
                v1 = self.read_node_text(values[1])
                statements.append({"assign_stmt": {"target": v0, "operand": v1}})
            return v0
        elif re.compile(r'^return.*').match(shadow_opcode):
            if "void" in shadow_opcode:
                statements.append({"return_stmt": {"target": ''}})
                return ''
            else:
                shadow_name = ""
                name = values[0]
                shadow_name = self.parse(name, statements)
                statements.append({"return_stmt": {"target": shadow_name}})
                return shadow_name
        elif re.compile(r'^const.*').match(shadow_opcode):
            print(values[0])
            print(self.read_node_text(values[0]))
            v0 = self.read_node_text(values[0])
            node = values[1]
            if self.find_child_by_type(node, 'literal'):
                v1 = self.read_node_text(self.find_child_by_type(node, 'literal').namedchildren[0])
            elif self.find_child_by_type(node, 'identifier'):
                v1 = self.read_node_text(self.find_child_by_type(node, 'identifier'))
            statements.append({"assign_stmt": {"target": v0, "operand": v1}})
            return v0
        elif re.compile(r'^check.*').match(shadow_opcode):
            pass
        elif shadow_opcode == "instance-of":
            v1 = self.read_node_text(values[1])
            v2 = self.parse(values[2], statements)
            tmp_var = self.tmp_variable(statements)
            statements.append({"assign_stmt":
                                   {"target": tmp_var, "operator": "instanceof", "operand": v1,
                                    "operand2": v2}})
            v0 = self.read_node_text(values[0])
            statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
            return v0
        elif shadow_opcode == 'array-length':
            v0 = self.read_node_text(values[0])
            v1 = self.read_node_text(values[1])
            statements.append({"assign_stmt": {"target": v0, "operand": v1, "operator": "array-length"}})
            # array-length v0, v1 将 v1 中数组的长度计算出来，然后将这个长度值存储到 v0 中
            pass
        elif re.compile(r'^new.*').match(shadow_opcode):
            # new-instance vA, type-id 创建一个类的新实例（对象）, type-id: 是该类的类型标识符，指定要创建哪个类的实例
            # new-array v0, v1, type-id 声明数组并为其分配内存和类型, 创建一个数组，其大小由寄存器v1的值决定。数组的引用将会被存储在v0寄存器中。
            if shadow_opcode == "new-instance":
                glang_node = {}
                mytype = self.parse(values[1], statements)
                glang_node["data_type"] = mytype
                tmp_var = self.tmp_variable(statements)
                glang_node["target"] = tmp_var
                statements.append({"new_instance": glang_node})
                v0 = self.read_node_text(values[0])
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
                return v0
            else:
                type = self.read_node_text(self.find_child_by_type(values[2], "primitives"))
                v1 = self.read_node_text(values[0])
                tmp_var = self.tmp_variable(statements)
                statements.append({"new_array": {"type": type, "target": tmp_var}})
                return tmp_var
        elif re.compile(r'^filled.*').match(shadow_opcode):
            # filled-new-array创建一个新的数组，并立即用给定的值填充它
            # filled-new-array {v0, v1, v2}, [I 这里，[I表示一个int类型的数组，v0, v1, v2是将被放入新数组的值所在的寄存器。数组创建和填充之后，其引用会被放置在某个寄存器中
            # filled-new-array/range {v0 .. v5}, [I 使用了v0到v5寄存器中的值来填充一个新的int数组
            pass
        elif re.compile(r'^fill-.*').match(shadow_opcode):
            # fill-array-data v0, :array_data 将预定义的数据集合填充到之前声明的数组中
            pass
        elif re.compile(r'^throw.*').match(shadow_opcode):
            shadow_expr = ""
            expr = values[0]
            shadow_expr = self.parse(expr, statements)
            statements.append({"throw_stmt": {"target": shadow_expr}})
            pass
        elif re.compile(r'^goto.*').match(shadow_opcode):
            # 跳转到同一方法内的指定位置继续执行代码
            # goto :label_start :label_start 是一个标签，可以在代码中跳转到它标记的位置。
            v0 = self.parse(values[0], statements)
            statements.append({"goto": {"target": v0}})
            pass
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
        
        elif re.compile(r'^invoke.*').match(shadow_opcode):
            pass

        elif re.compile(r'^rsub.*').match(shadow_opcode):
            dest = self.parse(node.named_children[1], statements)
            source1 = self.parse(node.named_children[2], statements)
            source2 = self.parse(node.named_children[3], statements)
            statements.append({"assign_stmt": {"target": dest, "operator": '-', "operand": source2,"operand2": source2}})
            return dest
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
        
        elif re.compile(r'^iput.*').match(shadow_opcode): 
            source = self.parse(node.named_children[1], statements)
            receiver_object = self.parse(node.named_children[2], statements)
            field=self.find_child_by_type(node.named_children[3],"field_identifier")
            shadow_field=self.read_node_text(field)
            statements.append({"field_write": {"receiver_object": receiver_object, "field": shadow_field, "source": source}})
        elif re.compile(r'^iget.*').match(shadow_opcode):
            target = self.parse(node.named_children[1], statements)
            receiver_object = self.parse(node.named_children[2], statements)
            field=self.find_child_by_type(node.named_children[3],"field_identifier")
            shadow_field=self.read_node_text(field)
            statements.append({"field_read": {"target": target, "receiver_object": receiver_object, "field": shadow_field}})
        elif re.compile(r'^sget.*').match(shadow_opcode):
            target = self.parse(node.named_children[1], statements)
            source = node.named_children[2]
            receiver_object = self.find_child_by_type(source,"class_identifier")
            shadow_receiver_object=self.read_node_text(receiver_object)
            field = self.find_child_by_type(source,"field_identifier")
            shadow_field = self.read_node_text(field)
            statements.append({"field_read": {"target": target, "receiver_object": shadow_receiver_object, "field": shadow_field}})
        elif re.compile(r'^sput.*').match(shadow_opcode):
            source = self.parse(node.named_children[1], statements)
            target = node.named_children[2]
            receiver_object = self.find_child_by_type(target,"class_identifier")
            shadow_receiver_object=self.read_node_text(receiver_object)
            field = self.find_child_by_type(target,"field_identifier")
            shadow_field = self.read_node_text(field)
            statements.append({"field_write": {"receiver_object": shadow_receiver_object, "field": shadow_field, "source": source}})

    
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
        
