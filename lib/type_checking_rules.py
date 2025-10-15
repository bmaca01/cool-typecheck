from .cl_types import *
from .util import *

"""Helper functions"""
def oe_c(oe: dict[tuple[str, str], CLTypeIdent], c: CLClass) -> dict[tuple[str, str], CLTypeIdent]:
    """Produce a copy of an object environment where any instance of
    SELF_TYPE is annotated with the associted enclosing class

    :param oe: object env
    :type oe: dict[tuple[str,str], CLTypeIdent]
    :return: a copy of the object env 
    :rtype: dict of (str, str): CLTypeIdent
    """
    oe_rtn = copy.deepcopy(oe)
    for k, v in oe.items():
        if (v.name == 'SELF_TYPE'):
            oe_rtn[k].self_type_resolve = c.ident.name
        else:
            oe_rtn[k] = v
    return oe_rtn

def join(cst: dict[str, CLClass], 
         type_A: CLTypeIdent, 
         type_B: CLTypeIdent) -> CLTypeIdent | None:
    """Calculate the 'least type' between 2 types, used in type checking if expr

    :param cst: the dict produced by `init_class_table`
    :type cst: dict[str, CLClass]
    :param type_A: Type of true block
    :type type_A: CLTypeIdent
    :param type_A: Type of false block
    :type type_A: CLTypeIdent
    :return: The type of the least common ancestor
    :rtype: CLTypeIdent
    """
    # Return the least type C s.t. A<=C and B<=C
    if ((type_A.name == type_B.name) or
        (type_A.name == 'Object') or
        (type_B.name == 'Object')):
        return type_A
    # Get the ancestors of A and B
    anc_A = get_ancestors(cst, cst[type_A.name]) if type_A.name != 'SELF_TYPE' else \
            get_ancestors(cst, cst[type_A.self_type_resolve])
    anc_B = get_ancestors(cst, cst[type_B.name]) if type_B.name != 'SELF_TYPE' else \
            get_ancestors(cst, cst[type_B.self_type_resolve])
    len_A = len(anc_A)
    len_B = len(anc_B)
    
    curr_A = cst[type_A.name] if type_A.name != 'SELF_TYPE' else \
             cst[type_A.self_type_resolve]
    curr_B = cst[type_B.name] if type_B.name != 'SELF_TYPE' else \
             cst[type_B.self_type_resolve]
    while (len_A != len_B):
        if (len_A > len_B):
            curr_A = anc_A.pop()
            len_A -= 1
        else:
            curr_B = anc_B.pop()
            len_B -= 1
    while (curr_A.ident.name != curr_B.ident.name):
        try:
            curr_A = anc_A.pop()
            curr_B = anc_B.pop()
        except:
            return None
        else:
            len_A -= 1
            len_B -= 1
    return CLTypeIdent(curr_A.ident.line, curr_A.ident.name)

def join_case(cst: dict[str, CLClass], types: list[CLTypeIdent]) -> CLTypeIdent | None:
    """Calculate the 'least type' between a list types, used in type checking `case` expr

    :param cst: the dict produced by `init_class_table`
    :type cst: dict[str, CLClass]
    :param types: List of type in case expression
    :type types: list[CLTypeIdent]
    :return: The type of the least common ancestor among all cases
    :rtype: CLTypeIdent
    """
    for t in types:
        if (t.name == 'Object'):
            return t
    
    # Helper functions
    def ti2cs(ti: CLTypeIdent) -> str:
        if (ti.name == 'SELF_TYPE'):
            return ti.self_type_resolve
        else:
            return ti.name
    def cst_val(cs: str) -> CLClass:
        return cst[cs]
    def get_anc(c: CLClass) -> deque[CLClass]:
        d = get_ancestors(cst, c)
        d.append(c)
        return d
    
    str_types = map(ti2cs, types)
    cls_types = map(cst_val, str_types)
    anc_types = list(map(get_anc, cls_types))
    anc_types_lens = map(len, anc_types)
    min_len = min(anc_types_lens)
    # make all deques the same len
    for anc_deque in anc_types:
        while (len(anc_deque) != min_len):
            anc_deque.pop()
    
    # peek at left most items in all deques
    try:
        curr_its = [d[-1].ident.name for d in anc_types]
    except:
        return None
    
    # lots of side effects here - careful!!!
    while (not all(it == curr_its[0] for it in curr_its)):              # While not all items in curr_its are the same, 
        try: 
            #(d.pop() for d in anc_types)    # Pop from right on all deques of anc_types
            #map(lambda d: d.pop(), anc_types)
            for d in anc_types:
                d.pop()
        except:                                         # If something goes wrong just return None
            return None
        else:
            curr_its = [d[-1].ident.name for d in anc_types]    # reassign curr_its to be the list of the last item of all deques
    # now, hopefully all items in the deques of anc_types are the same
    # so, get the rightmost item of the deque (which should be the least common ancestor of all `types`)
    if (all(it.name == 'SELF_TYPE' for it in types)):
        return types[0]
    else:
        return CLTypeIdent(anc_types[0][-1].ident.line, anc_types[0][-1].ident.name)



"""Type checking functions"""
def tc_basic_class_inheritance(cst: dict[str, CLClass]) -> bool:
    """Type checks all classes to check inheritance from Int, String, or Bool"""
    # Look for inheritance for Int, String, or Bool
    for cls in cst.values():
        if (cls.inherits):
            match cls.superclass.name:
                case 'Int':
                    print(f'ERROR: {cls.ident.line}: Type-Check: class {cls.ident.name} inherits from Int')
                    sys.exit()
                case 'String':
                    print(f'ERROR: {cls.ident.line}: Type-Check: class {cls.ident.name} inherits from String')
                    sys.exit()
                case 'Bool':
                    print(f'ERROR: {cls.ident.line}: Type-Check: class {cls.ident.name} inherits from Bool')
                    sys.exit()
                case _:
                    if (cls.superclass.name not in cst):
                        print(f'ERROR: {cls.superclass.line}: Type-Check: class {cls.ident.name} inherits from unknown class {cls.superclass.name}')
                        sys.exit()
    return True 

def tc_main_method(cst: dict[str, CLClass]) -> bool:
    """Type checks the Main class for method main. Aborts if main is declared with more than 0 parameters"""
    # Check for main method in Main declared with 0 params
    if ('Main' in cst):
        main_fs = get_class_methods(cst['Main'])
        if (len(main_fs) != 0):
            while (True):
                curr_method = main_fs.popleft()
                if ((curr_method.f_ident.name == 'main') and
                    (len(curr_method.m_formals)) != 0):
                    print(f'ERROR: 0: Type-Check: class Main method main with 0 parameters not found')
                    sys.exit()
                    return False
                if (len(main_fs) == 0):
                    break
    else:
        print(f'ERROR: 0: Type-Check: class Main not found')
        sys.exit()
        return False
    return True

def tc_class_self_type(cst: dict[str, CLClass]) -> bool:
    """Checks program if there exists a declared class with name SELF_TYPE"""
    if ('SELF_TYPE' in cst):
        print(f'ERROR: {cst["SELF_TYPE"].ident.line}: Type-Check: class named SELF_TYPE')
        sys.exit()
        return False
    return True

def type_check(cst: dict[str, CLClass], 
               me: dict[tuple[str, str], list[CLTypeIdent]], 
               oe: dict[tuple[str, str], CLTypeIdent]) -> list[list[CLTypeIdent]]:
    """Given an ast, type check all classes. Returns a list of lists, where each item corresponds to a class. 
    Each item in each list contains a CLTypeIdent, the static type of each class's feature"""
    tc_basic_class_inheritance(cst)
    tc_main_method(cst)
    tc_class_self_type(cst)
    c_types = []
    for c in cst.values():
        res = tc_class(cst, me, oe, c)
        if (res is None):
            return None
        c_types.append(res)
    return c_types

def tc_class(cst: dict[str, CLClass], 
             me: dict[tuple[str, str], list[CLTypeIdent]], 
             oe: dict[tuple[str, str], CLTypeIdent], 
             c: CLClass) -> list[CLTypeIdent] | None:
    """Type check a class. Return None iff None is a member of `f_types`.

    `tc_class` will resolve any instance of SELF_TYPE in the object env by calling `oe_c` on the obj env passed to it. 
    The extended object env is then passed to type check frame called for each feature of the class.
    """
    oe_ext = oe_c(oe, c)
    f_types = []
    for f in c.features:
        match f.f_type:
            case 'attribute_no_init' | 'attribute_init':
                res = tc_attr(cst, me, oe_ext, c, f)
            case 'method':
                res = tc_method(cst, me, oe_ext, c, f)
            case _:
                print('ERROR: 0: Type-Check: feature is not attribute or method')   # is this a type checking error or syntax error?
                sys.exit()
                return None
        f_types.append(res)
    if (None in f_types):
        return None
    return f_types

def tc_attr(cst: dict[str, CLClass],
            me: dict[tuple[str, str], list[CLTypeIdent]], 
            oe: dict[tuple[str, str], CLTypeIdent], 
            c: CLClass, 
            expr: CLFeature) -> CLTypeIdent | None:
    '''This should be called from tc_class, where tc_class already calls `oe_c()` on oe'''
    if ((expr.att_type.name != 'SELF_TYPE') and (expr.att_type.name not in cst)):
        print(f'ERROR: {expr.att_type.line}: Type-Check: unknown type {expr.att_type.name}')
        sys.exit()
        return None
    c1 = (c.ident.name, expr.f_ident.name) in oe.keys()
    if (not c1):
        print(f'ERROR: {expr.f_ident.line}: Type-Check: unbound attribute identifier {expr.f_ident.name}')
        sys.exit()
        return None
    if (expr.f_type == 'attribute_init'):
        oe_ext = copy.deepcopy(oe)
        oe_ext.update({(c.ident.name, 'self'): CLTypeIdent('0', 'SELF_TYPE')})
        oe_ext[(c.ident.name, 'self')].self_type_resolve = c.ident.name
        # Check the initializer
        c2 = tc_expr(cst, me, oe_ext, c, expr.att_init)
        if (c2 is None):
            print(f'ERROR: tc_expr with expr {expr} returned none')
            sys.exit()
            return None
        if (((oe[(c.ident.name, expr.f_ident.name)].name == 'SELF_TYPE') and (c2.name == 'SELF_TYPE') and 
             (not conforms(cst, c, CLTypeIdent(expr.att_init.line_num, c.ident.name), oe[(c.ident.name, expr.f_ident.name)]))) or
            ((oe[(c.ident.name, expr.f_ident.name)].name == 'SELF_TYPE') and 
             (not conforms(cst, c, c2, oe[(c.ident.name, expr.f_ident.name)]))) or 
            ((c2.name == 'SELF_TYPE') and 
             (not conforms(cst, c, CLTypeIdent(expr.att_init.line_num, c.ident.name), oe[(c.ident.name, expr.f_ident.name)]))) or 
            (not conforms(cst, c, c2, oe[(c.ident.name, expr.f_ident.name)]))
        ):
            print(f'ERROR: {expr.f_ident.line}: Type-Check: initializer of attribute {expr.f_ident.name} does not conform to {oe_ext[(c.ident.name, expr.f_ident.name)]}')
            sys.exit()
            return None
    expr.s_type = oe[(c.ident.name, expr.f_ident.name)]
    return oe[(c.ident.name, expr.f_ident.name)]

def tc_method(cst: dict[str, CLClass],
              me: dict[tuple[str, str], list[CLTypeIdent]], 
              oe: dict[tuple[str, str], CLTypeIdent], 
              c: CLClass, 
              expr: CLFeature) -> CLTypeIdent | None:
    '''This should be called from tc_class, where tc_class already calls `oe_c()` on oe'''
    if ((expr.m_type.name != 'SELF_TYPE') and (expr.m_type.name not in cst)):
        print(f'ERROR: {expr.m_type.line}: Type-Check: unknown type {expr.m_type.name}')
        sys.exit()
        return None
    c1 = (c.ident.name, expr.f_ident.name) in me.keys()
    if (not c1):    # Method name not found somehow
        print(f'ERROR: {expr.f_ident.line}: Type-Check: unknown method {expr.f_ident.name}')
        sys.exit()
        return None
    # Extend the object environment with `self` identifier and each formal
    oe_ext = copy.deepcopy(oe)
    oe_ext.update({(c.ident.name, 'self'): CLTypeIdent('0', 'SELF_TYPE')})
    oe_ext[(c.ident.name, 'self')].self_type_resolve = c.ident.name
    visited: set[str]
    visited = set()
    for f in expr.m_formals:
        if (f.name.name == 'self'):
            print(f'ERROR: {expr.f_ident.line}: Type-Check: class {c.ident.name} has method {expr.f_ident.name} with formal parameter named self')
            sys.exit()
            return None
        if (f.type.name not in cst):
            print(f'ERROR: {f.type.line}: Type-Check: unknown type {f.type.name}')
            sys.exit()
            return None
        if (f.name.name in visited):
            print(f'ERROR: {expr.f_ident.line}: Type-Check: class {c.ident.name} has method {expr.f_ident.name} with duplicate formal parameter {f.name.name}')
            sys.exit()
            return None
        visited.add(f.name.name)
        new_k = (c.ident.name, f.name.name)
        new_v = f.type
        oe_ext.update({new_k: new_v})
    
    # Check the static type of the method body and compare it against declared type
    c2 = tc_expr(cst, me, oe_ext, c, expr.m_body)
    expected_rtn = copy.deepcopy(me[c.ident.name, expr.f_ident.name][-1])
    # We do this SELF_TYPE resolution for the sake of type checking
    if (expected_rtn.name == 'SELF_TYPE'):
        expected_rtn.self_type_resolve = c.ident.name
    if (c2 is None):
        return None
    # Accd to type checking rules for methods, we only need to CHECK the 
    # method body static type and ensure it conforms to the declared return type
    if ((not conforms(cst, c, c2, expected_rtn))):
        print(f'ERROR: {expr.f_ident.line}: Type-Check: body of method {expr.f_ident.name} with type {c2.name} does not conform to {expected_rtn.name}')
        sys.exit()
        return None
    # We return the declared type
    expr.s_type = me[c.ident.name, expr.f_ident.name][-1]
    return expr.s_type

def tc_expr(cst: dict[str, CLClass],
            me: dict[tuple[str, str], list[CLTypeIdent]], 
            oe: dict[tuple[str, str], CLTypeIdent], 
            c: CLClass, 
            expr: CLExpr) -> CLTypeIdent | None:
    res: CLTypeIdent = None
    match expr.type:
        case 'integer'|'string'|'true'|'false'|'internal':
            res = tc_const(expr.body)
        case 'identifier':
            if (((c.ident.name, expr.body.name) not in oe)):
                print(f'ERROR: {expr.body.line}: Type-Check: unbound variable {expr.body.name}')
                sys.exit()
                return None
            if (not (isinstance(expr.body, CLVarIdent) or isinstance(expr.body, CLSelfIdent))):
                print(f'not an identifier..?')
                sys.exit()
                return None
            res = tc_var(oe, c, expr.body)
            if (res.name == 'SELF_TYPE'):
                res.self_type_resolve = c.ident.name
        case 'assign':
            expr_assign: CLAssign = expr.body
            res = tc_assign(cst, me, oe, c, expr_assign.rhs, expr_assign.var)
            if (res is None):
                print(f'ERROR: {expr.line_num}: Type-Check: rhs does not conform to {oe[(c.ident.name, expr.body.var.name)]}')
                sys.exit()
                return None
            expr_assign.s_type = res
        case 'new':
            expr_new: CLNew = expr.body
            if (expr_new.type_id.name != 'SELF_TYPE' and expr_new.type_id.name not in cst):
                print(f'ERROR: {expr_new.type_id.line}: Type-Check: unknown type {expr_new.type_id.name}')
                sys.exit()
                return None
            res = tc_new(c, expr_new.type_id)
            if (res.name == 'SELF_TYPE'):
                res.self_type_resolve = c.ident.name
            expr_new.s_type = res
        case 'isvoid':
            expr_isvoid: CLIsvoid = expr.body
            res = tc_isvoid(cst, me, oe, c, expr_isvoid)
        case 'plus'|'minus'|'times'|'divide':
            expr_arith: (CLPlus|CLMinus|CLTimes|CLDivide) = expr.body
            res = tc_arith(cst, me, oe, c, expr_arith)
            if (res is None):
                print(f'ERROR: {expr.line_num}: Type-Check: Non-integer types used in arithmetic')
                sys.exit()
                return None
            expr_arith.s_type = res
        case 'lt'|'le'|'eq':
            expr_cmp: (CLLT|CLLE|CLEQ) = expr.body
            res = tc_equal(cst, me, oe, c, expr_cmp)
            if (res is None):
                print(f'ERROR: {expr.line_num}: Type-Check: Incompatible type comparison')
                sys.exit()
                return None
            expr_cmp.s_type = res
        case 'not':
            expr_not: CLNOT = expr.body
            res = tc_not(cst, me, oe, c, expr_not)
            if (res is None):
                print(f'ERROR: {expr.line_num}: Type-Check: not applied to non-boolean type')
                sys.exit()
                return None
            expr_not.s_type = res
        case 'negate':
            expr_neg: CLNegate = expr.body
            res = tc_neg(cst, me, oe, c, expr_neg)
            if (res is None):
                print(f'ERROR: {expr.line_num}: Type-Check: negate applied to non-integer type')
                sys.exit()
                return None
            expr_neg.s_type = res
        case 'block':
            expr_block: CLBlock = expr.body
            res = tc_sequence(cst, me, oe, c, expr_block)
            if (res is None):
                print(f'ERROR: {expr.line_num}: empty block expr not allowed')
                sys.exit()
                return None
            expr_block.s_type = res
        case 'dynamic_dispatch':
            expr_dyn_disp: CLDynDispatch = expr.body
            res = tc_dispatch(cst, me, oe, c, 
                              expr_dyn_disp.caller, 
                              expr_dyn_disp.method_name, 
                              expr_dyn_disp.args)
            if (res.name == 'SELF_TYPE'):
                expr_dyn_disp.s_type = expr_dyn_disp.caller.s_type
                res = CLTypeIdent(res.line, expr_dyn_disp.s_type.name)
                if (res.name == 'SELF_TYPE'):
                    res.self_type_resolve = expr_dyn_disp.s_type.self_type_resolve
            else:
                expr_dyn_disp.s_type = res
        case 'self_dispatch':
            expr_self_disp: CLSelfDispatch = expr.body
            self_caller = CLExpr(expr_self_disp.method_name.line, 
                                 'identifier', 
                                 CLSelfIdent(expr_self_disp.method_name.line, 'self')) 
            res = tc_dispatch(cst, me, oe, c, 
                              self_caller,
                              expr_self_disp.method_name, 
                              expr_self_disp.args)
            if (res.name == 'SELF_TYPE'):   # The method's formal return type is SELF_TYPE
                expr_self_disp.s_type = self_caller.s_type
                res = CLTypeIdent(res.line, expr_self_disp.s_type.name)
                if (res.name == 'SELF_TYPE'):   # The caller's static type is SELF_TYPE
                    res.self_type_resolve = expr_self_disp.s_type.self_type_resolve
            else:
                expr_self_disp.s_type = res
        case 'static_dispatch':
            expr_disp: CLStaticDispatch = expr.body
            if (expr_disp.type.name not in cst):
                print(f'ERROR: {expr_disp.type.line}: unknown type {expr_disp.type.name}')
                sys.exit()
                return None
            res = tc_static_dispatch(cst, me, oe, c, 
                                     expr_disp.caller, 
                                     expr_disp.type, 
                                     expr_disp.method_name, 
                                     expr_disp.args)
            if (res.name == 'SELF_TYPE'):
                expr_disp.s_type = expr_disp.caller.s_type
                res = CLTypeIdent(res.line, expr_disp.s_type.name)
            else:
                expr_disp.s_type = res
        case 'if':
            expr_if: CLIf = expr.body
            res = tc_if(cst, me, oe, c, expr_if)
            if (res is None):
                print(f'ERROR: {expr.line_num}: Type-Check: error in if expression')
                sys.exit()
                return None
            expr_if.s_type = res
        case 'while':
            expr_while: CLWhile = expr.body
            res = tc_loop(cst, me, oe, c, expr_while)
            if (res is None):
                print(f'ERROR: {expr.line_num}: Type-Check: error in while expression')
                sys.exit()
                return None
            expr_while.s_type = res
        case 'let':
            expr_let: CLLet = expr.body
            res = tc_let(cst, me, oe, c, 
                         expr_let.bind_list, 
                         expr_let.let_body)
            if (res is None):
                print(f'ERROR: {expr.line_num}: Type-Check: binding does not conform in let initialization')
                sys.exit()
                return None
            expr_let.s_type = res
        case 'case':
            expr_case: CLCase = expr.body
            res = tc_case(cst, me, oe, c, expr_case)
            if (res is None):
                print(f'ERROR: {expr.line_num}: Type-Check: Error with LUB in case')
                sys.exit()
                return None
            expr_case.s_type = res
        case _:
            print(f'ERROR: {expr.line_num}: Type-Check: expr is not in language')
            sys.exit()
            return None
    expr.s_type = res
    return res

def tc_const(id: CLConstant) -> CLTypeIdent:
    return id.type

def tc_var(oe: dict[tuple[str, str], CLTypeIdent], 
           c: CLClass, 
           id: CLVarIdent|CLSelfIdent) -> CLTypeIdent | None:
    if ((c.ident.name, id.name) in oe.keys()): 
        return oe[(c.ident.name, id.name)]
    return None

def tc_assign(cst: dict[str, CLClass],
              me: dict[tuple[str, str], list[CLTypeIdent]],
              oe: dict[tuple[str, str], CLTypeIdent], 
              c: CLClass, 
              expr: CLExpr,
              id: CLVarIdent) -> CLTypeIdent | None:
    c1 = tc_var(oe, c, id)
    if (c1 is None):
        print(f'ERROR: {id.line}: unbound variable {id.name} in assign')
        sys.exit()
        return None
    c2 = tc_expr(cst, me, oe, c, expr)
    if ((c2 is not None) and (conforms(cst, c, c2, oe[c.ident.name, id.name]))):
        return c2
    return None

def tc_new(c: CLClass, t_id: CLTypeIdent) -> CLTypeIdent:
    if (t_id.name == 'SELF_TYPE'):
        t_id.self_type_resolve = c.ident.name
    return t_id

def tc_dispatch(cst: dict[str, CLClass],
                me: dict[tuple[str, str], list[CLTypeIdent]],
                oe: dict[tuple[str, str], CLTypeIdent], 
                c: CLClass, 
                caller: CLExpr,
                m_name: CLMethodIdent,
                args: list[CLExpr]) -> CLTypeIdent | None:
    # "To type check a dispatch, each of the subexpressions must first be type checked"
    # The type T0 of e0 determines which declaration of the method f is used
    # 1) Type check the caller object
    subexpr_types: list[CLTypeIdent] = [tc_expr(cst, me, oe, c, caller)]
    # 2) Type check each argument and append the result to subexpr_types
    for arg in args:
        subexpr_types.append(tc_expr(cst, me, oe, c, arg))
    # 3) Resolve SELF_TYPE if the caller is of type SELF_TYPE
    t_0prime = subexpr_types[0].self_type_resolve if subexpr_types[0].name == 'SELF_TYPE' else subexpr_types[0].name
    # 4) Then check the caller indeed has access to the method being dispatched
    if ((t_0prime, m_name.name) not in me):
        print(f'ERROR: {m_name.line}: Type-Check: unknown method {m_name.name}')
        sys.exit()
        return None
    # 5) Then compare the formal method signature against the provided args
    m_signature = me[(t_0prime, m_name.name)]
    m_decl_ret = copy.deepcopy(m_signature[-1])
    # "The argument types of the dispatch must conform to the declared argument types"
    for i in range(0, len(m_signature) - 1):
        if (not conforms(cst, c, subexpr_types[i + 1], m_signature[i])):
            print(f'ERROR: {m_name.line}: Type-Check: argument #{i+1} in dispatch does not conform to declared formal param type {m_signature[i]}')
            sys.exit()
            return None

    if (m_decl_ret.name == 'SELF_TYPE'):
        m_decl_ret.self_type_resolve = subexpr_types[0].self_type_resolve if subexpr_types[0].name == 'SELF_TYPE' else subexpr_types[0].name
    return m_decl_ret

def tc_static_dispatch(cst: dict[str, CLClass],
                       me: dict[tuple[str, str], list[CLTypeIdent]],
                       oe: dict[tuple[str, str], CLTypeIdent], 
                       c: CLClass, 
                       caller: CLExpr,
                       called_class: CLTypeIdent,
                       m_name: CLMethodIdent,
                       args: list[CLExpr]) -> CLTypeIdent | None:
    # "To type check a dispatch, each of the subexpressions must first be type checked"
    subexpr_types: list[CLTypeIdent] = [tc_expr(cst, me, oe, c, caller)]
    for arg in args:
        subexpr_types.append(tc_expr(cst, me, oe, c, arg))

    if (not conforms(cst, c, subexpr_types[0], called_class)):
        print(f'ERROR: {caller.line_num}: Type-Check: caller object does not conform to static class {called_class.name}')
        sys.exit()
        return None
    if ((called_class.name, m_name.name) not in me):
        print(f'ERROR: {m_name.line}: Type-Check: unknown method {m_name.name}')
        sys.exit()
        return None
    m_signature = me[(called_class.name, m_name.name)]

    # "The argument types of the dispatch must conform to the declared argument types"
    for i in range(0, len(m_signature) - 1):
        if (not conforms(cst, c, subexpr_types[i + 1], m_signature[i])):
            print(f'ERROR: {m_name.line}: Type-Check: argument #{i+1} in dispatch does not conform to declared formal param type {m_signature[i]}')
            sys.exit()
            return None

    return m_signature[-1]

def tc_if(cst: dict[str, CLClass],
          me: dict[tuple[str, str], list[CLTypeIdent]], 
          oe: dict[tuple[str, str], CLTypeIdent], 
          c: CLClass, 
          expr: CLIf) -> CLTypeIdent | None:
    c1 = tc_expr(cst, me, oe, c, expr.pred)
    if (c1.name != 'Bool'):
        return None
    c2 = tc_expr(cst, me, oe, c, expr.true_case)
    c3 = tc_expr(cst, me, oe, c, expr.false_case)
    if ((c2 is not None) and (c3 is not None)):
        return join(cst, c2, c3)
    return None

def tc_sequence(cst: dict[str, CLClass],
                me: dict[tuple[str, str], list[CLTypeIdent]], 
                oe: dict[tuple[str, str], CLTypeIdent], 
                c: CLClass, 
                expr: CLBlock) -> CLTypeIdent | None:
    if (len(expr.expr_list) == 0):
        return None
    for e in expr.expr_list:
        if e is expr.expr_list[-1]:
            return tc_expr(cst, me, oe, c, e)
        if (tc_expr(cst, me, oe, c, e) is None):
            return None

def tc_let(cst: dict[str, CLClass],
           me: dict[tuple[str, str], list[CLTypeIdent]], 
           oe: dict[tuple[str, str], CLTypeIdent], 
           c: CLClass, 
           bindings: list[CLLetBindingElem],
           expr_body: CLExpr) -> CLTypeIdent | None:
    # idea is to recurse into itself for each binding, where previous bindings are visible in the next
    if (len(bindings) > 0):
        if ((bindings[0].v_type.name != 'SELF_TYPE') and (bindings[0].v_type.name not in cst)):
            print(f'ERROR: {bindings[0].v_type.line}: unknown type {bindings[0].v_type.name}')
            sys.exit()
            return None
        t_prime_0 = bindings[0].v_type
        if (bindings[0].v_type.name == 'SELF_TYPE'):
            t_prime_0.self_type_resolve = c.ident.name

        if (bindings[0].bind_type == 'let_binding_init'):
            t_1 = tc_expr(cst, me, oe, c, bindings[0].v_init)
            if (t_1 is None):
                print(f'expr from let in line {bindings[0].v_init.line_num} is none')
                sys.exit()
                return None
            elif (not conforms(cst, c, t_1, t_prime_0)):
                return None
        if (bindings[0].v_name.name == 'self'):
            print(f'ERROR: {bindings[0].v_name.line}: Type-Check: binding to self not allowed in let')
            sys.exit()
            return None
        oe_ext = copy.deepcopy(oe)
        oe_ext.update({(c.ident.name, bindings[0].v_name.name): t_prime_0})
        return tc_let(cst, me, oe_ext, c, bindings[1:], expr_body)
    else:   # No more bindings to extend the object env with
        return tc_expr(cst, me, oe, c, expr_body)

def tc_case(cst: dict[str, CLClass],
            me: dict[tuple[str, str], list[CLTypeIdent]], 
            oe: dict[tuple[str, str], CLTypeIdent], 
            c: CLClass, 
            expr: CLCase) -> CLTypeIdent | None:
    t_0 = tc_expr(cst, me, oe, c, expr.c_expr)
    if (t_0 is None):
        return None
    
    visited: set[str] = set()
    branch_types: list[CLTypeIdent] = []
    for branch in expr.c_list:
        if (branch.type.name not in cst):
            print(f'ERROR: {branch.type.line}: Type-Check: unknown type {branch.type.name}')
            sys.exit()
            return None
        if (branch.type.name in visited):
            print(f'ERROR: {branch.ident.line}: Type-Check: case branch type {branch.type.line} is bound twice')
            sys.exit()
            return None
        if (branch.ident.name == 'self'):
            print(f'ERROR: {branch.ident.line}: Type-Check: bind to self in case not allowed')
            sys.exit()
            return None
        if (branch.type.name == 'SELF_TYPE'):
            print(f'ERROR: {branch.type.line}: Type-Check: using SELF_TYPE as case branch type not allowed')
            sys.exit()
            return None
        oe_ext = copy.deepcopy(oe)
        oe_ext.update({(c.ident.name, branch.ident.name): branch.type})
        visited.add(branch.type.name)
        # Evaluate static type of each branch
        branch_type = tc_expr(cst, me, oe_ext, c, branch.body)
        if (branch_type is None):
            return None
        # Then add to list of evaluated static types
        branch_types.append(branch_type)
    
    return join_case(cst, branch_types)

def tc_loop(cst: dict[str, CLClass],
            me: dict[tuple[str, str], list[CLTypeIdent]], 
            oe: dict[tuple[str, str], CLTypeIdent], 
            c: CLClass, 
            expr: CLWhile) -> CLTypeIdent | None:
    if ((tc_expr(cst, me, oe, c, expr.pred).name != 'Bool') or
        (tc_expr(cst, me, oe, c, expr.body) is None)):
        return None
    return CLTypeIdent(expr.pred.line_num, 'Object')

def tc_isvoid(cst: dict[str, CLClass],
              me: dict[tuple[str, str], list[CLTypeIdent]], 
              oe: dict[tuple[str, str], CLTypeIdent], 
              c: CLClass, 
              expr: CLIsvoid) -> CLTypeIdent | None:
    if (tc_expr(cst, me, oe, c, expr.expr) is None):
        return None
    return CLTypeIdent(expr.expr.line_num, 'Bool')

def tc_not(cst: dict[str, CLClass],
           me: dict[tuple[str, str], list[CLTypeIdent]], 
           oe: dict[tuple[str, str], CLTypeIdent], 
           c: CLClass, 
           expr: CLNOT) -> CLTypeIdent | None:
    c1 = tc_expr(cst, me, oe, c, expr.expr)
    if ((c1 is None) or (c1.name != 'Bool')):
        return None
    return c1

def tc_neg(cst: dict[str, CLClass],
           me: dict[tuple[str, str], list[CLTypeIdent]], 
           oe: dict[tuple[str, str], CLTypeIdent], 
           c: CLClass, 
           expr: CLNegate) -> CLTypeIdent | None:
    c1 = tc_expr(cst, me, oe, c, expr.expr)
    if ((c1 is None) or (c1.name != 'Int')):
        return None
    return c1

def tc_arith(cst: dict[str, CLClass],
             me: dict[tuple[str, str], list[CLTypeIdent]], 
             oe: dict[tuple[str, str], CLTypeIdent], 
             c: CLClass, 
             expr: CLPlus|CLMinus|CLTimes|CLDivide) -> CLTypeIdent | None:
    if (not ((isinstance(expr, CLPlus)) or 
             (isinstance(expr, CLMinus)) or 
             (isinstance(expr, CLDivide)) or 
             (isinstance(expr, CLTimes)))):
        return None
    c1 = tc_expr(cst, me, oe, c, expr.lhs)
    c2 = tc_expr(cst, me, oe, c, expr.rhs)
    if (((c1 is None) or (c2 is None)) or
        ((c1.name != 'Int') or (c2.name != 'Int'))):
        return None
    
    return c1

def tc_equal(cst: dict[str, CLClass],
             me: dict[tuple[str, str], list[CLTypeIdent]], 
             oe: dict[tuple[str, str], CLTypeIdent], 
             c: CLClass, 
             expr: CLEQ|CLLT|CLLE) -> CLTypeIdent | None:
    c1 = tc_expr(cst, me, oe, c, expr.lhs)
    c2 = tc_expr(cst, me, oe, c, expr.rhs)
    consts = set(('Int', 'String', 'Bool'))
    if ((c1 is None) or (c2 is None) or
        ((c1.name in consts) or (c2.name in consts)) and 
        (c1.name != c2.name)):
        return None
    
    return CLTypeIdent(expr.lhs.line_num, 'Bool')

"""Print functions"""
def print_class_map(cst: dict[str,CLClass]):
    """Print class map accd to `spec <https://kelloggm.github.io/martinjkellogg.com/teaching/cs485-sp25/projects/pa2.html>`_"""
    cm = gen_class_map_a(cst)
    print('class_map')
    print(len(cst))
    for c in cm:
        print(c[0])
        print(len(c[1]))
        for att in c[1]:
            has_init = (not isinstance(att[2], CLConstant))
            if (not has_init):
                print('no_initializer')
                print(att[0])
                print(att[1])
            else:
                print('initializer')
                print(att[0])
                print(att[1])
                CLExpr_print(att[2])

def print_implementation_map(cst: dict[str,CLClass]):
    """Print implementation map accd to `spec <https://kelloggm.github.io/martinjkellogg.com/teaching/cs485-sp25/projects/pa2.html>`_"""
    im = gen_implementation_map(cst)
    print('implementation_map')
    print(len(cst))
    for it in im:
        print(it[0])
        print(len(it[1]))
        for m in it[1]:
            print(m[0].f_ident.name)
            print(len(m[0].m_formals))
            for f in m[0].m_formals:
                print(f.name.name)
            print(m[1].ident.name)
            CLExpr_print(m[0].m_body)

def print_parent_map(cst: dict[str,CLClass]):
    """Print parent map accd to `spec <https://kelloggm.github.io/martinjkellogg.com/teaching/cs485-sp25/projects/pa2.html>`_"""
    pm = gen_parent_map(cst)
    print('parent_map')
    print(len(pm))
    for it in pm:
        print(it[0])
        print(it[1])

def print_annot_ast(ast: CLAST):
    """Print annotated AST accd to `spec <https://kelloggm.github.io/martinjkellogg.com/teaching/cs485-sp25/projects/pa2.html>`_"""
    print(len(ast.classes))
    for c in ast.classes:
        CLIdent_print(c.ident)
        if (c.inherits):
            print('inherits')
            CLIdent_print(c.superclass)
        else:
            print('no_inherits')
        print(len(c.features))
        for f in c.features:
            print(f.f_type)
            match f.f_type:
                case 'attribute_no_init':
                    CLIdent_print(f.f_ident)
                    CLIdent_print(f.att_type)
                case 'attribute_init':
                    CLIdent_print(f.f_ident)
                    CLIdent_print(f.att_type)
                    CLExpr_print(f.att_init)
                case 'method':
                    CLIdent_print(f.f_ident)
                    print(len(f.m_formals))
                    for fl in f.m_formals:
                        CLIdent_print(fl.name)
                        CLIdent_print(fl.type)
                    CLIdent_print(f.m_type)
                    CLExpr_print(f.m_body)

def CLExpr_print(e: CLExpr):
    print(e.line_num)                               # Output line num of expr
    print(e.s_type)                                 # Output type associated with the expr
    print(e.type)                                   # Output name of expression
    match(e.type):
        case 'true'|'false':
            pass
        case 'integer'|'string'|'internal':
            print(e.body.value)
        case 'identifier':
            CLIdent_print(e.body)
        case 'new':
            CLIdent_print(e.body.type_id)
        case 'assign':
            CLIdent_print(e.body.var)
            CLExpr_print(e.body.rhs)
        case 'isvoid'|'not'|'negate':
            CLExpr_print(e.body.expr)
        case 'plus'|'minus'|'times'|'divide'|'lt'|'le'|'eq':
            CLExpr_print(e.body.lhs)
            CLExpr_print(e.body.rhs)
        case 'while':
            CLExpr_print(e.body.pred)
            CLExpr_print(e.body.body)
        case 'if':
            CLExpr_print(e.body.pred)
            CLExpr_print(e.body.true_case)
            CLExpr_print(e.body.false_case)
        case 'block':
            print(len(e.body.expr_list))
            for ex in e.body.expr_list:
                CLExpr_print(ex)
        case 'self_dispatch':
            CLIdent_print(e.body.method_name)
            print(len(e.body.args))
            for arg in e.body.args:
                CLExpr_print(arg)
        case 'dynamic_dispatch':
            CLExpr_print(e.body.caller)
            CLIdent_print(e.body.method_name)
            print(len(e.body.args))
            for arg in e.body.args:
                CLExpr_print(arg)
        case 'static_dispatch':
            CLExpr_print(e.body.caller)
            CLIdent_print(e.body.type)
            CLIdent_print(e.body.method_name)
            print(len(e.body.args))
            for arg in e.body.args:
                CLExpr_print(arg)
        case 'let':
            print(len(e.body.bind_list))
            for binding in e.body.bind_list:
                print(binding.bind_type)
                CLIdent_print(binding.v_name)
                CLIdent_print(binding.v_type)
                if (binding.bind_type == 'let_binding_init'):
                    CLExpr_print(binding.v_init)
            CLExpr_print(e.body.let_body)
        case 'case':
            CLExpr_print(e.body.c_expr)
            print(len(e.body.c_list))
            for cs in e.body.c_list:
                CLIdent_print(cs.ident)
                CLIdent_print(cs.type)
                CLExpr_print(cs.body)
    return

def CLIdent_print(id: CLClassIdent|CLMethodIdent|CLVarIdent|CLSelfIdent|CLTypeIdent):
    print(id.line)
    print(id.name)
    return