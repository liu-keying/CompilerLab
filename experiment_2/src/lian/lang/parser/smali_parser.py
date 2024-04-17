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
        opcode = self.find_child_by_field(node, "opcode")
        shadow_opcode = self.read_node_text(opcode)
        values = self.find_children_by_field(node, "value")
        if shadow_opcode == "nop":
            return None
        elif re.compile(r'^move.*').match(shadow_opcode):
            if "result" in shadow_opcode or "exception" in shadow_opcode:
                v0 = self.read_node_text(self.find_child_by_field(values[0], "register").namedchildren[0])
                tmp_var = self.tmp_variable(statements)
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
            else:
                v0 = self.read_node_text(self.find_child_by_field(values[0], "register").namedchildren[0])
                v1 = self.read_node_text(self.find_child_by_field(values[1], "register").namedchildren[0])
                statements.append({"assign_stmt": {"target": v0, "operand": v1}})
            return v0
        elif re.compile(r'^return.*').match(shadow_opcode):
            if "void" in shadow_opcode:
                statements.append({"return_stmt": {"target": None}})
                return None
            else:
                v0 = self.read_node_text(self.find_child_by_field(values[0], "register").namedchildren[0])
                statements.append({"return_stmt": {"target": v0}})
                return v0
        elif re.compile(r'^const.*').match(shadow_opcode):
            v0 = self.read_node_text(self.find_child_by_field(values[0], "register").namedchildren[0])
            node = values[1]
            if self.find_child_by_field(node, 'literal'):
                v1 = self.read_node_text(self.find_child_by_field(node, 'literal').namedchildren[0])
            elif self.find_child_by_field(node, 'identifier'):
                v1 = self.read_node_text(self.find_child_by_field(node, 'identifier'))
            statements.append({"assign_stmt": {"target": v0, "operand": v1}})
            return v0
        elif re.compile(r'^check.*').match(shadow_opcode):
            pass
        elif shadow_opcode == "instance-of":
            v1 = self.read_node_text(self.find_child_by_field(values[1], "register").namedchildren[0])
            v2 = self.read_node_text(values[1])
            statements.append({"assert_stmt": {"condition": f"{v1} is {v2}"}})
        elif shadow_opcode == 'array-length':
            pass
        elif re.compile(r'^new.*').match(shadow_opcode):
            pass
        elif re.compile(r'^filled.*').match(shadow_opcode):
            pass
        elif re.compile(r'^fill-.*').match(shadow_opcode):
            pass
        elif re.compile(r'^throw.*').match(shadow_opcode):
            pass
        elif re.compile(r'^goto.*').match(shadow_opcode):
            pass
        elif re.search(r'-switch$', shadow_opcode):
            pass
        elif re.compile(r'^cmp.*').match(shadow_opcode):

            pass
        elif re.compile(r'^if-.*').match(shadow_opcode):
            pass
        elif re.compile(r'^aget.*').match(shadow_opcode):
            pass
        elif re.compile(r'^aput.*').match(shadow_opcode):
            pass

        
