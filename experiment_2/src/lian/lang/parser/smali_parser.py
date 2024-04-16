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
        #print(node.sexp())
        opcode = self.find_child_by_type(node, "opcode")
        shadow_opcode = self.read_node_text(opcode)
        if shadow_opcode == "nop":
            return self.tmp_variable(statements)
        elif re.compile(r'^move.*').match(shadow_opcode):
            values = self.find_child_by_type(node, "value")
            v0 = self.read_node_text(values[0])
            v1 = self.read_node_text(values[1])
            statements.append({"assign_stmt": {"target": v0, "operand": v1}})
            return v0
        elif re.compile(r'^return.*').match(shadow_opcode):
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
        
