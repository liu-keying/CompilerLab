#!/usr/bin/env python3

from . import common_parser
import re


class Parser(common_parser.Parser):
    def is_comment(self, node):
        return node.type == "comment"
        #pass

    def is_identifier(self, node):
        return node.type == "identifier"
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
            "primary_expression": self.primary_expression
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
        opcode = self.find_child_by_field(node, "opcode")
        shadow_opcode = self.read_node_text(opcode)
        if shadow_opcode == "nop":
            return self.tmp_variable(statements)
        elif re.compile(r'^move.*').match(shadow_opcode):
            values = self.find_children_by_field(node, "value")
            v0 = self.read_node_text(values[0])
            v1 = self.read_node_text(values[1])
            statements.append({"assign_stmt": {"target": v0, "operand": v1}})
            return v0
        elif re.compile(r'^return.*').match(shadow_opcode):
            pass
        elif re.compile(r'^add.*/2addr').match(shadow_opcode):
            return self.binary_expression(node, statements, "+")
        elif re.compile(r'^sub.*/2addr').match(shadow_opcode):
            return self.binary_expression(node, statements, "-")
        elif re.compile(r'^add.*[^/2addr]').match(shadow_opcode):
            return self.binary_expression_2addr(node, statements, "+")

    def binary_expression_2addr(self, node, statements, op):
        values = self.find_children_by_field(node, "value")
        dest = self.read_node_text(values[0])
        source = self.read_node_text(values[1])
        statements.append({"assign_stmt": {"target": dest, "operator": op, "operand": dest,"operand2": source}})
        return dest

    def binary_expression(self, node, statements, op):
        values = self.find_children_by_field(node, "value")
        dest = self.read_node_text(values[0])
        source1 = self.read_node_text(values[1])
        source2 = self.read_node_text(values[2])
        statements.append({"assign_stmt": {"target": dest, "operator": op, "operand": source1,"operand2": source2}})
        return dest
        
