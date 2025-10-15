import sys
from .cl_types import *

class ParseStates:
    CLPROG = 1
    CLCLASS = 2
    CLFEATURE = 3
    CLFORMAL = 4
    CLEXPR = 5
    CLLIST = 6

# A COOLParser Object is responsible for handling the input file
# It tracks the current "item"
class COOLParser:
    """Object responsible for parsing the serialized cl-ast
    
    Attributes:
        idx: current position
        it: current lexeme
        lines: the list of lines of the cl-ast
        line_len: length of the lines list
        parse_state: one of ParseState
    """
    idx = 0
    it = ''
    lines = []
    line_len = 0
    parse_state = None

    def __init__(self, l: list[str]):
        self.lines = l
        self.it = l[0]
        self.line_len = len(l)
        self.parse_state = ParseStates.CLPROG

    def print_it(self):
        print(self.it)

    def print_idx(self):
        print(self.idx)

    def print_curr_state(self):
        print(f'''(idx: {self.idx}, it: "{self.it}", line_len: {self.line_len}, parse_state: {self.parse_state})''')

    def peek_next(self):
        """Return as a tuple the index and next item of lines"""
        if (self.idx + 1 == self.line_len):
            return None

        idx_next = self.idx + 1
        it_next = self.lines[idx_next]
        return (idx_next, it_next)

    def peek_prev(self):
        if (self.idx - 1 < 0):
            return None
        
        idx_prev = self.idx - 1
        it_prev = self.lines[idx_prev]
        return (idx_prev, it_prev)

    def get_next(self):
        if (self.idx + 1 == self.line_len):
            return None
        
        self.idx += 1
        self.it = self.lines[self.idx]
        return (self.idx, self.it)

    def get_prev(self):
        if (self.idx - 1 < 0):
            return None
        
        self.idx -= 1
        self.it = self.lines[self.idx]
        return (self.idx, self.it)

    def get_curr(self):
        return (self.idx, self.it)

    def push_back(self):
        self.get_prev()

    def set_parse_state(self, new_state: ParseStates):
        self.parse_state = new_state
        return

    def reset_parser(self):
        self.idx = 0
        self.it = self.lines[0]
        self.parse_state = ParseStates.CLPROG

def read_prog(parser: COOLParser) -> CLAST:
    parser.set_parse_state(ParseStates.CLPROG)
    class_list: list[CLClass] = []
    class_cnt = int(parser.it)
    parser.get_next()

    parser.set_parse_state(ParseStates.CLLIST)
    for i in range(class_cnt):
        cl_cls = read_class(parser)

        if (cl_cls.ident.name in {c.ident.name for c in class_list}):
            print(f'ERROR: {cl_cls.ident.line}: Type-Check: class {cl_cls.ident.name} redefined')
            sys.exit()
            return
        class_list.append(cl_cls)

    return CLAST(class_list)

def read_class(parser: COOLParser) -> CLClass:
    parser.set_parse_state(ParseStates.CLCLASS)

    curr_class_id = read_class_ident(parser)    # Returns a CLClassIdent & moves parser forward

    curr_class_inh = True if parser.it == 'inherits' else False
    parser.get_next()

    curr_superclass_id = None if not curr_class_inh else read_class_ident(parser)

    curr_class_feature_list: list[CLFeature] = []

    curr_class_feature_cnt = int(parser.it)
    parser.get_next()

    parser.set_parse_state(ParseStates.CLLIST)
    for i in range(curr_class_feature_cnt):
        cl_ft = read_feature(parser)
        curr_ms = {m.f_ident.name for m in filter(lambda f: f.f_type == 'method', curr_class_feature_list)}
        if (cl_ft.f_ident.name in curr_ms):
            print(f'ERROR: {cl_ft.f_ident.line}: Type-Check: class {curr_class_id.name} redefines method {cl_ft.f_ident.name}')
            sys.exit()
            return

        curr_class_feature_list.append(cl_ft)

    return(CLClass(curr_class_id, curr_class_feature_list, curr_class_inh, curr_superclass_id))

def read_feature(parser: COOLParser) -> CLFeature:
    parser.set_parse_state(ParseStates.CLFEATURE)

    feature_type = parser.it
    parser.get_next()

    match feature_type:
        case 'attribute_no_init':
            attr_name = read_var_ident(parser)
            attr_type = read_type_ident(parser)

            return CLFeature(feature_type, attr_name, attr_type)
        case 'attribute_init':
            attr_name = read_var_ident(parser)
            attr_type = read_type_ident(parser)
            attr_init_expr = read_expr(parser)
            
            return CLFeature(feature_type, attr_name, attr_type, None, attr_init_expr)
        case 'method':
            method_name = read_method_ident(parser)
            
            method_formals_cnt = int(parser.it)
            method_formals_ls = []
            parser.get_next()

            parser.set_parse_state(ParseStates.CLLIST)
            for i in range(method_formals_cnt):
                method_formals_ls.append(read_formal(parser))

            method_type = read_type_ident(parser)
            method_body = read_expr(parser)
            
            return CLFeature(feature_type, method_name, method_type, method_formals_ls, None, method_body)
        case _:
            sys.exit("how did we get here?")

def read_formal(parser: COOLParser) -> CLFormal:
    parser.set_parse_state(ParseStates.CLFORMAL)

    formal_name = read_var_ident(parser)
    formal_type = read_type_ident(parser)
    return CLFormal(formal_name, formal_type)

def read_expr(parser: COOLParser) -> CLExpr:
    # Every Expr must terminate =>
    # Every 'read_expr()' call will return a CLExpr object
    parser.set_parse_state(ParseStates.CLEXPR)

    expr_line_num = parser.it
    parser.get_next()

    expr_type = parser.it
    parser.get_next()

    match expr_type:
        case 'true' | 'false':
            parser.push_back()
            return(CLExpr(expr_line_num, expr_type, read_expr_constant(parser, expr_line_num)))
        case 'integer' | 'string':
            return(CLExpr(expr_line_num, expr_type, read_expr_constant(parser, expr_line_num)))
        case 'identifier':
            return(CLExpr(expr_line_num, expr_type, read_expr_ident(parser)))
        case 'assign':
            var = read_var_ident(parser)
            rhs = read_expr(parser)

            return(CLExpr(expr_line_num, expr_type, CLAssign(var, rhs)))
        case 'new':
            return(CLExpr(expr_line_num, expr_type, CLNew(read_type_ident(parser))))
        case 'isvoid':
            return(CLExpr(expr_line_num, expr_type, CLIsvoid(read_expr(parser))))
        case 'not':
            e = read_expr(parser)
            return(CLExpr(expr_line_num, expr_type, CLNOT(e)))
        case 'negate':
            e = read_expr(parser)
            return(CLExpr(expr_line_num, expr_type, CLNegate(e)))
        case 'plus':
            lhs = read_expr(parser)
            rhs = read_expr(parser)
            return(CLExpr(expr_line_num, expr_type, CLPlus(lhs, rhs)))
        case 'minus':
            lhs = read_expr(parser)
            rhs = read_expr(parser)
            return(CLExpr(expr_line_num, expr_type, CLMinus(lhs, rhs)))
        case 'times':
            lhs = read_expr(parser)
            rhs = read_expr(parser)
            return(CLExpr(expr_line_num, expr_type, CLTimes(lhs, rhs)))
        case 'divide':
            lhs = read_expr(parser)
            rhs = read_expr(parser)
            return(CLExpr(expr_line_num, expr_type, CLDivide(lhs, rhs)))
        case 'lt':
            lhs = read_expr(parser)
            rhs = read_expr(parser)
            return(CLExpr(expr_line_num, expr_type, CLLT(lhs, rhs)))
        case 'le':
            lhs = read_expr(parser)
            rhs = read_expr(parser)
            return(CLExpr(expr_line_num, expr_type, CLLE(lhs, rhs)))
        case 'eq':
            lhs = read_expr(parser)
            rhs = read_expr(parser)
            return(CLExpr(expr_line_num, expr_type, CLEQ(lhs, rhs)))
        case 'dynamic_dispatch':
            caller_obj = read_expr(parser)
            method_call = read_method_ident(parser)

            argc = int(parser.it)
            parser.get_next()

            argv = []

            parser.set_parse_state(ParseStates.CLLIST)
            for i in range(argc):
                argv.append(read_expr(parser))
            
            return(CLExpr(expr_line_num, expr_type, CLDynDispatch(caller_obj, method_call, argv)))
        case 'static_dispatch':
            caller_obj = read_expr(parser)
            typeclass = read_type_ident(parser)
            method_call = read_method_ident(parser)

            argc = int(parser.it)
            parser.get_next()

            argv = []

            parser.set_parse_state(ParseStates.CLLIST)
            for i in range(argc):
                argv.append(read_expr(parser))
            
            return(CLExpr(expr_line_num, expr_type, CLStaticDispatch(caller_obj, typeclass, method_call, argv)))
        case 'self_dispatch':
            method_call = read_method_ident(parser)

            argc = int(parser.it)
            parser.get_next()

            argv = []

            parser.set_parse_state(ParseStates.CLLIST)
            for i in range(argc):
                argv.append(read_expr(parser))
            
            return(CLExpr(expr_line_num, expr_type, CLSelfDispatch(method_call, argv)))
        case 'if':
            predicate = read_expr(parser)
            then_expr = read_expr(parser)
            else_expr = read_expr(parser)

            return(CLExpr(expr_line_num, expr_type, CLIf(predicate, then_expr, else_expr)))
        case 'while':
            predicate = read_expr(parser)
            body = read_expr(parser)

            return(CLExpr(expr_line_num, expr_type, CLWhile(predicate, body)))
        case 'block':
            exp_ls = []
            exp_cnt = int(parser.it)
            parser.get_next()

            parser.set_parse_state(ParseStates.CLLIST)
            for i in range(exp_cnt):
                exp_ls.append(read_expr(parser))
            
            return(CLExpr(expr_line_num, expr_type, CLBlock(exp_ls)))
        case 'let':
            bind_cnt = int(parser.it)
            parser.get_next()

            bind_list = []

            parser.set_parse_state(ParseStates.CLLIST)
            for i in range(bind_cnt):
                bind_type = parser.it
                parser.get_next()

                match bind_type:
                    case 'let_binding_no_init':
                        var_name = read_var_ident(parser)
                        var_type = read_type_ident(parser)
                        bind_list.append(CLLetBindingElem(bind_type, var_name, var_type))
                    case 'let_binding_init':
                        var_name = read_var_ident(parser)
                        var_type = read_type_ident(parser)
                        init_expr = read_expr(parser)
                        bind_list.append(CLLetBindingElem(bind_type, var_name, var_type, init_expr))
            
            let_body = read_expr(parser)
            
            return(CLExpr(expr_line_num, expr_type, CLLet(bind_list, let_body)))
        case 'case':
            case_expr = read_expr(parser)
            case_cnt = int(parser.it)
            parser.get_next()

            case_list = []

            parser.set_parse_state(ParseStates.CLLIST)
            for i in range(case_cnt):
                # Now reading case elements:
                case_var = read_var_ident(parser)
                case_type = read_type_ident(parser)
                case_body = read_expr(parser)
                case_list.append(CLCaseElem(case_var, case_type, case_body))
            
            return(CLExpr(expr_line_num, expr_type, CLCase(expr_line_num, case_expr, case_list)))

        case _:     # Unknown error
            parser.print_curr_state()
            print(f"expr_line_num: {expr_line_num}")
            print(f"expr_type: {expr_type}")
            sys.exit('unknown expr type')

def read_expr_ident(parser: COOLParser) -> CLSelfIdent | CLVarIdent:
    expr_line_num = parser.it
    parser.get_next()

    expr_var = parser.it
    parser.get_next()

    match expr_var:
        case 'self':
            return(CLSelfIdent(expr_line_num, expr_var))
        case _:
            return(CLVarIdent(expr_line_num, expr_var))

def read_expr_constant(parser: COOLParser, line_num: str) -> CLConstant:
    const_val = parser.it
    parser.get_next()

    match const_val:
        case 'true' | 'false':
            return(CLConstant(CLTypeIdent(line_num, 'Bool'), const_val))
        case _:
            try:
                int_v = int(const_val)
                return(CLConstant(CLTypeIdent(line_num, 'Int'), int_v))
            except:
                return(CLConstant(CLTypeIdent(line_num, 'String'), const_val))

def read_class_ident(parser: COOLParser) -> CLClassIdent:
    line_num = parser.it
    parser.get_next()

    class_name = parser.it
    parser.get_next()

    return(CLClassIdent(line_num, class_name))

def read_var_ident(parser: COOLParser) -> CLVarIdent:
    line_num = parser.it
    parser.get_next()

    var_name = parser.it
    parser.get_next()

    return(CLVarIdent(line_num, var_name))

def read_method_ident(parser: COOLParser) -> CLMethodIdent:
    line_num = parser.it
    parser.get_next()

    var_name = parser.it
    parser.get_next()

    return(CLMethodIdent(line_num, var_name))

def read_type_ident(parser: COOLParser) -> CLTypeIdent:
    line_num = parser.it
    parser.get_next()

    type_name = parser.it
    parser.get_next()

    return(CLTypeIdent(line_num, type_name))
