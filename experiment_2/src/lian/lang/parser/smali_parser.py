#!/usr/bin/env python3

from . import common_parser
import re

type_list = ['variable', 'parameter', 'number', 'string', 'float', 'character', 'identifier', 'list', 'body', 'class_identifier']

label_list = []
switch_table={}
unsolved_switch={}
array_data_list={}
unsolved_array_data={}

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
            "local_directive" : self.local_directive,
            "restart_local_directive" : self.local_directive,
            "end_local_directive" : self.end_local_directive,
            "label" : self.label_statement,
            "jmp_label": self.label_statement,
            "packed_switch_directive": self.packed_switch_directive,
            "sparse_switch_directive": self.sparse_switch_directive,
            "array_data_directive": self.array_data_directive,
        }
        return STATEMENT_HANDLER_MAP.get(node.type, None)

    def is_statement(self, node):
        return self.check_statement_handler(node) is not None

    def statement(self, node, statements):
        handler = self.check_statement_handler(node)
        return handler(node, statements)
    
    def local_directive(self, node, statements):
        #print(node.sexp())
        register = node.named_children[0]
        if register == None:
            pass
        register = self.read_node_text(register)
        variable = None
        data_type = None
        if len(node.named_children)>1:
            variable = node.named_children[1]
            if variable.type == "string":
                variable = self.read_node_text(self.find_child_by_type(variable, "string_fragment"))
            else:
                variable = self.read_node_text(variable)
            data_type = self.read_node_text(node.named_children[2])
            if len(node.named_children)>3:
                full_type = node.named_children[3]
                data_type = self.read_node_text(self.find_child_by_type(full_type, "string_fragment"))
        if variable:
            statements.append({"variable_decl": { "data_type": data_type, "name": register, "original_name": variable }})
        else:
            statements.append({"variable_decl": { "name": register }})
        return register
    
    def end_local_directive(self, node, statements):
        register = node.named_children[0]
        if register == None:
            pass
        register = self.read_node_text(register)
        statements.append({"del_statement": { "target": register }})

    def label_statement(self, node, statements):
        label= self.read_node_text(node)
        statements.append({"label_stmt": { "name": label }})
        label_list.append(label)

    def packed_switch_directive(self, node, statements):
        #print(node.sexp())
        switch_label = label_list[-1]
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
        if switch_label in unsolved_switch:
            stmt_id = unsolved_switch[switch_label]
            del unsolved_switch[switch_label]
            #print(statements[stmt_id])
            statements[stmt_id]["switch_stmt"]['body']= cases

    def sparse_switch_directive(self, node, statements):
        switch_label = label_list[-1]
        conditions = self.find_children_by_type(node, "number")
        labels = self.find_children_by_type(node, "label")
        cases = []
        for condition,label in zip(conditions,labels):
            shadow_condition = self.read_node_text(condition)
            shadow_label = self.read_node_text(label)
            cases.append({"case_stmt": {"condition": str(shadow_condition), "body": [{"goto_stmt": {"target": shadow_label}}]}})
        switch_table[switch_label] = cases
        if switch_label in unsolved_switch:
            stmt_id = unsolved_switch[switch_label]
            del unsolved_switch[switch_label]
            #print(statements[stmt_id])
            statements[stmt_id]["switch_stmt"]['body']= cases

    def array_data_directive(self, node, statements):
        #print(node.sexp())
        element_width = self.find_child_by_field(node, "element_width")
        values = self.find_children_by_field(node,"value")
        array_data_label= label_list[-1]
        shadow_values = []
        for value in values:
            shadow_values.append(self.read_node_text(value))
        array_data_list[array_data_label] = shadow_values
        if array_data_label in unsolved_array_data:
            stmt_id = unsolved_array_data[array_data_label]["stmt_id"]
            array = unsolved_array_data[array_data_label]["array"]
            del unsolved_array_data[array_data_label]
            for i in range(len(shadow_values)):
                statements.insert(stmt_id, {"array_write": {"array": array , "index":i , "src":shadow_values[i] }})
                stmt_id += 1
            

    def primary_expression(self, node, statements):
        #print(node.sexp())
        opcode = self.find_child_by_type(node, "opcode")
        shadow_opcode = self.read_node_text(opcode)
        #print(shadow_opcode)
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
                global tmp_return
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_return, "operator": "result"}})
            elif "exception" in shadow_opcode:
                v0 = self.read_node_text(values["variable"][0])
                global tmp_exception
                statements.append({"assign_stmt": {"target": v0, "operand": tmp_exception, "operator": "exception"}})
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
        elif re.compile(r'^check.*').match(shadow_opcode):
            v0 = self.read_node_text(values["variable"][0])
            class_identifier = values['class_identifier'][0]
            shadow_class = self.read_node_text(class_identifier)
            statements.append({"assign_stmt": {"target": v0, "operand": shadow_class, "operator": "check-cast"}})
            return v0
        elif shadow_opcode == "instance-of":
            v1 = self.read_node_text(values["variable"][1])
            v2 = self.read_node_text(values["variable"][1])
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
            if "range" in shadow_opcode:
                type = self.read_node_text(self.find_child_by_type_type(node, "array_type", "primitive_type"))
                range_node = self.read_node_text(self.find_child_by_type(node,"range"))
                matches = re.findall(r'v(\d+)', range_node)
                tmp_var = self.tmp_variable(statements)
                statements.append({"new_array": {"type": type, "target": tmp_var}})
                for i in range(int(matches[0]),int(matches[1])+1):
                    statements.append({"assign_stmt": {"target": f'v{i}', "operand": tmp_var, "operator": "filled-new-array/range"}})
                return tmp_var
            else:
                type = self.read_node_text(self.find_child_by_type_type(node, "array_type", "primitive_type"))
                type = self.read_node_text(self.find_child_by_type_type(node, "array_type", "primitive_type"))
                list = self.find_child_by_type(node, "list")
                vs = self.find_children_by_type(list,"variable")
                tmp_var = self.tmp_variable(statements)
                statements.append({"new_array": {"type": type, "target": tmp_var}})
                for i in range(len(vs)):
                    name = self.read_node_text(vs[i])
                    statements.append({"assign_stmt": {"target": name, "operand": f'{tmp_var}[{i}]'}})
                return tmp_var
        elif re.compile(r'^fill-.*').match(shadow_opcode):
            v0 = self.read_node_text(node.named_children[1])
            array_label = self.read_node_text(node.named_children[2])
            if array_label in array_data_list:
                shadow_values= array_data_list[array_label]
                for i in range(len(shadow_values)):
                    statements.append({"array_write": {"array": v0 , "index":i , "src":shadow_values[i] }})
            else:
                unsolved_array_data[array_label] = {'array': v0, 'stmt_id':len(statements)}
                
            
            return v0
        elif re.compile(r'^throw.*').match(shadow_opcode):
            shadow_expr = self.read_node_text(values["variable"][0])
            statements.append({"throw_stmt": {"target": shadow_expr}})
            return
        elif re.compile(r'^goto.*').match(shadow_opcode):
            label = self.read_node_text(self.find_child_by_type(node, "label"))
            statements.append({"goto_stmt": {"target": label}})
            return
        elif re.search(r'-switch$', shadow_opcode):
            p0 = self.read_node_text(node.named_children[1])
            switch_label = self.read_node_text(self.find_child_by_type(node, "label"))
            cases = None
            if switch_label in switch_table:
                cases = switch_table[switch_label]
            else:
                unsolved_switch[switch_label]= len(statements)
            statements.append({"switch_stmt": {"condition": p0, "body": cases}})
            return p0
        elif re.compile(r'^cmp.*').match(shadow_opcode):
            v0 = self.read_node_text(values["variable"][0])
            v1 = self.read_node_text(values["variable"][1])
            v2 = self.read_node_text(values["variable"][2])
            tmp_var = self.tmp_variable(statements)
            if 'cmpl' in shadow_opcode:
                statements.append({"compare_stmt": {"target": tmp_var, "operator": 'lt', "operand": v1,"operand2": v2}})
            else:
                statements.append({"compare_stmt": {"target": tmp_var, "operator": 'gt', "operand": v1,"operand2": v2}})
            statements.append({"assign_stmt": {"target": v0, "operand": tmp_var}})
            return v0
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
            statements.append({"goto_stmt": {"target": label, "condition": tmp_var}})
            return tmp_var
        elif re.compile(r'^aget.*').match(shadow_opcode):
            v0 = self.read_node_text(values["variable"][0])
            v1 = self.read_node_text(values["variable"][1])
            v2 = self.read_node_text(values["variable"][2])
            statements.append({"array_read": {"target": v0, "array": v1, "index": v2}})
            return v0
        elif re.compile(r'^aput.*').match(shadow_opcode):
            v0 = self.read_node_text(values["variable"][0])
            v1 = self.read_node_text(values["variable"][1])
            v2 = self.read_node_text(values["variable"][2])
            statements.append({"array_write": {"array": v1, "index": v2, "src": v0}})
            return v0
        
        elif re.compile(r'^invoke.*').match(shadow_opcode) or shadow_opcode=='execute-inline' or shadow_opcode=='excute-inline-range':
            #global tmp_return
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
        