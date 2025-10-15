import sys
from .cl_types import *

import copy
from collections import deque

def set_object_as_ancestor(ast: CLAST) -> CLAST:
    """Return a copy of a CLAST where all classes explicitly inherit from `Object` if they don't have any explicity inheritance declarations from the source file"""
    ast_copy = copy.deepcopy(ast)
    for c in ast_copy.classes:
        if (not c.inherits):
            c.inherits = True
            c.superclass = CLOBJECTINSTANCE.ident
    return ast_copy

def init_class_table(ast: CLAST) -> dict[str, CLClass]:
    """Given a de-serialized ast from .cl-ast, return a table as a 
    `dict[str, CLClass]` where the name of a class as a string 
    maps to the `CLClass` object in the ast. Includes COOL basic 
    classes (Object, IO, Int, String, Bool)

    Each value of the dict is a CLClass pointer into the AST

    :param ast: the generated ast produced by ``./cool -parse``  
    :type ast: CLAST

    :returns: A dictionary that maps a class name to the instance of the class in the ast
    :rtype: dict {str: CLClass}
    """
    global CLOBJECTINSTANCE
    global CLSTRINGINSTANCE
    global CLIOINSTANCE
    global CLINTINSTANCE
    global CLBOOLINSTANCE

    ct = dict(zip([c.ident.name for c in ast.classes], ast.classes))
    ct.update({CLOBJECTINSTANCE.ident.name: CLOBJECTINSTANCE})
    ct.update({CLSTRINGINSTANCE.ident.name: CLSTRINGINSTANCE})
    ct.update({CLINTINSTANCE.ident.name: CLINTINSTANCE})
    ct.update({CLIOINSTANCE.ident.name: CLIOINSTANCE})
    ct.update({CLBOOLINSTANCE.ident.name: CLBOOLINSTANCE})
    return(dict(sorted(ct.items())))

def get_method_env_dict(ct: dict[str, CLClass]) -> dict[tuple[str, str], list[CLTypeIdent]]:
    """Produces a dictionary of strings, mapping class name and method 
    name to a list of param types and a return type
    
    :param ct: the dict produced by `init_class_table`
    :type ct: dict[str, CLClass]
    :return: Desc
    :rtype: dict[tuple[str,str], list[CLTypeIdent]]
    """
    rtn: dict[tuple[str, str], list[CLTypeIdent]]
    rtn = dict()

    def check_redefine(curr_cls: CLClass,
                       curr_method: CLFeature, 
                       r: dict[tuple[str, str], list[CLTypeIdent]]) -> bool:
        # 1) Check each key in the rtn dict;
        for key in r.keys():
            # a) check the 
            #   - method name of current key
            #   - class of the current key, if it is equal to curr_cls
            if ((curr_method.f_ident.name == key[1]) and
                (curr_cls.ident.name == key[0])):
                # i) check the method override formals len match
                if ((curr_method.m_formals is not None) and
                    (len(curr_method.m_formals) != (len(r[key]) - 1))):
                    print(f'ERROR: {curr_method.f_ident.line}: Type-Check: formal params not matching length')
                    sys.exit()
                    return False
                # ii) for each param, check newly declared param type match inherited param type
                if (curr_method.m_formals is not None):
                    for i in range(len(curr_method.m_formals)):
                        if (curr_method.m_formals[i].type.name != r[key][i].name):
                            print(f'ERROR: {curr_method.m_formals[i].type.line}: Type-Check: formal param {curr_method.m_formals[i].name.name}: {curr_method.m_formals[i].type.name}' \
                                  f' does not match param with type {r[key][i].name}')
                            sys.exit()
                            return False
                # iii) check return type of overridden method is exactly the return type of inherited method
                #if (not conforms(ct, curr_anc, curr_method.m_type, r[key][-1])):
                if (curr_method.m_type.name != r[key][-1].name):
                    print(f'ERROR: {curr_method.m_type.line}: Type-Check: return type of method {curr_method.f_ident.name}: {curr_method.m_type.name} in class {curr_cls.ident.name}'\
                          f' does not match inherited method return type {r[key][-1].name}')
                    sys.exit()
                    return False
        return True
    def iterate_methods(curr_anc: CLClass,
                        methods: deque[CLFeature], 
                        r: dict[tuple[str, str], list[CLTypeIdent]],
                        enclosing_cls: CLClass):
        if (len(methods) == 0):
            return
        curr_method = methods.popleft()
        # i) check for redefinitions
        check_redefine(curr_anc, curr_method, r)
        # ii) make a new key for rtn
        new_key = (enclosing_cls.ident.name, curr_method.f_ident.name)
        # iii) the associated value is a tuple of the current
        #     method's params in order, 
        new_val = []
        if (curr_method.m_formals is not None):
            for f in curr_method.m_formals:
                new_val += [f.type]
        #     then it's return type
        new_val += [curr_method.m_type]
        # iv) Then add the assoc k-v pair to rtn iff the key not in rtn already
        #if (new_key not in r):
        r[new_key] = new_val
        return
    def iterate_ancestors(ct: dict[str, CLClass], 
                          ancestors: deque[CLClass], 
                          r: dict[tuple[str, str], list[CLTypeIdent]],
                          enclosing_cls: CLClass):
        curr_anc = ancestors.popleft()
        # a) Get current ancestor's methods
        anc_methods = get_class_methods(curr_anc)
            
        # b) Loop through the curr_anc's methods
        while (len(anc_methods) != 0):
            iterate_methods(curr_anc, anc_methods, r, enclosing_cls)
    def iterate_class_table(ct: dict[str, CLClass], v_class: CLClass):
        # 1) Get current class ancestors
        ancestors = get_ancestors(ct, v_class)
        ancestors.append(v_class)
        # 2) Loop through all ancestors starting from Object
        while (len(ancestors) != 0):
            iterate_ancestors(ct, ancestors, rtn, v_class)

    for v_class in ct.values():
        iterate_class_table(ct, v_class)
    
    return rtn

def get_class_methods(c: CLClass) -> deque[CLFeature]:
    """Given a `CLClass` object, return a deque of the class's methods not including ancestors

    :param c: class to get method definitions of
    :type c: CLClass
    :return: a deque of class methods
    :rtype: deque of CLFeature
    """
    rtn = deque()

    for f in c.features:
        if (f.f_type != 'method'):
            continue
        rtn.append(f)
    return rtn

def get_class_methods_a(ct: dict[str, CLClass], c: CLClass) -> deque[CLFeature]:
    """Given a CLClass object, return a deque of the class's methods 
    including ancestors

    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str, CLClass]
    :param c: the specific COOL class from a given ast to get the methods of
    :type c: CLClass
    :return: a deque of all the found methods
    :rtype: deque of CLFeature
    """
    rtn = deque()

    c_a = get_ancestors(ct, c)
    while (len(c_a) != 0):
        rtn += get_class_methods(c_a.popleft())
    
    rtn += get_class_methods(c)

    return rtn

def get_obj_env_dict(ct: dict[str, CLClass]) -> dict[tuple[str, str], CLTypeIdent]:
    """Produce a dictionary that maps class name and variable name to 
    it's declared type

    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str,CLClass]
    :return: a dictionary that maps `class name` x `variable name` (as a tuple) to a CLTypeIdent
    :rtype: dict of (str, str): CLTypeIdent
    """
    rtn: dict[tuple[str,str], CLTypeIdent] = dict()
    # iterate through every class in class table
    for c in ct.values():
        # For each class, get all the declared attributes up to Object
        curr_attrs = get_class_attr_a(ct, c)
        a_names = [a.f_ident.name for a in curr_attrs]
        if ('self' in a_names):
            self_idx = a_names.index('self')
            print(f'ERROR: {curr_attrs[self_idx].f_ident.line}: Type-Check: self is used as name of attribute')
            sys.exit()
            return
        # For each class, keep track of all declared attributes; 
        # Print an error if there is a re-define
        decl_ident: set[str] = set()
        while (curr_attrs):
            # For the current class, add to its obj env attributes from ancestors first
            curr_var = curr_attrs.popleft()
            # Re-define is found if the current attribute name is already in `decl_ident`
            if (curr_var.f_ident.name in decl_ident):
                print(f'ERROR: {curr_var.f_ident.line}: Type-Check: attribute {curr_var.f_ident.name} redefined')
                sys.exit()
                return
            decl_ident.add(curr_var.f_ident.name)
            # Make the new k-v pair then add it to the return dict
            new_key = (c.ident.name, curr_var.f_ident.name)
            new_val = curr_var.att_type
            rtn[new_key] = new_val
    return rtn
        
def get_class_attr(c: CLClass) -> deque[CLFeature]:
    """Given a CLClass object, return a deque of the class's attributes not including ancestors

    :param c: class to find all declared attributes of
    :type c: CLClass
    :return: a deque of all found attributes
    :rtype: deque of CLFeature
    """
    rtn = deque()

    for f in c.features:
        if (f.f_type == 'method'):
            continue
        rtn.append(f)
    return rtn

def get_class_attr_a(ct: dict[str, CLClass], c: CLClass) -> deque[CLFeature]:
    """Given a CLClass object, return a deque of the class's attributes including ancestors

    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str,CLClass]
    :param c: class to find all declared attributes of
    :type c: CLClass
    :return: a deque of all found attributes
    :rtype: deque of CLFeature
    """
    rtn = deque()

    c_a = get_ancestors(ct, c)
    while (len(c_a) != 0):
        rtn += get_class_attr(c_a.popleft())
    
    rtn += get_class_attr(c)

    return rtn

def conforms(ct: dict[str, CLClass], enclosing_cls: CLClass, c1: CLTypeIdent, c2: CLTypeIdent) -> bool:
    """Check c1 <= c2
    
    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str,CLClass]
    :param enclosing_cls: Used to "dereference" SELF_TYPE or self identifier
    :type enclosing_cls: CLClass
    :param c1: COOL type of interest
    :type c1: CLTypeIdent
    :param c1: COOL type to check conformance against
    :type c1: CLTypeIdent
    :return: true if c1 <= c2; false if not
    :rtype: bool
    """
    if ((c1.name == 'Object' and c2.name != 'Object') or    # Object only conforms to object
        ((c1.name != c2.name) and c2.name in ('String', 'Bool', 'Int'))):            # Nothing conforms to String, Int, or Bool because no class can inherit from them
        return False                                        # UNLESS c1 is also the same

    if ((c2.name == 'Object') or
        (c1.name == c2.name)):
        return True
    
    if (c1.name == 'SELF_TYPE'):
        c1_a = get_ancestors(ct, ct[c1.self_type_resolve])
        c1_a.append(ct[c1.self_type_resolve])
    else:
        c1_a = get_ancestors(ct, ct[c1.name])
        c1_a.append(ct[c1.name])

    c2_is_ST = False
    if (c2.name == 'SELF_TYPE'):
        c2_is_ST = True

    while (c1_a):
        curr_cls = c1_a.pop()
        if (((not c2_is_ST) and (curr_cls.ident.name == c2.name)) or
            ((c2_is_ST) and (curr_cls.ident.name == c2.self_type_resolve))):
            return True
    return False

def get_direct_ancestor(ct: dict[str, CLClass], c: CLClass) -> CLClass | None:
    """Given a class table and CLClass object, 
    return the direct ancestor of the class.
    if a class has no declared ancestors, it implicitly inherits from Object

    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str,CLClass]
    :param c: class to find immediate ancestor of
    :type c: CLClass
    :return: the instance of the class that c is a child of
    :rtype: CLClass | None
    """
    if (c.ident.name == 'Object'):
        return None
    else:
        try:
            if (c.superclass is not None):
                return ct[c.superclass.name]
            else:
                return CLOBJECTINSTANCE
        except:
            print(f'ERROR: {c.superclass.line}: Type-Check: class {c.ident.name} inherits from unknown class {c.superclass.name}')
            sys.exit()
            return

def get_ancestors(ct: dict[str, CLClass], c: CLClass) -> deque[CLClass]:
    """Given a class table and CLClass object reference,
    return a deque of the class's ancestor classes until Object. 
    The deque contains deep copies (i.e. allocated on heap probably)

    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str,CLClass]
    :param c: class to find all ancestors of, up to object
    :type c: CLClass
    :return: the deque of instances of classes that c is a child of
    :rtype: deque of CLClass
    """
    rtn: deque[CLClass] = deque()
    visited: set[str] = set()
    curr = copy.deepcopy(c)
    if (c.ident.name == 'Object'):
        return rtn
    # If no declared inheritance, a class only inherits from object by def
    if (not c.inherits):
        rtn.appendleft(CLOBJECTINSTANCE)
        return rtn
    #while curr.ident.name != 'Object':
    # Loop while current class does have a declared inheritance
    while (curr.inherits):
        if (curr.ident.name in visited):
            # Cycle
            print('ERROR: 0: Type-Check: inheritance cycle')
            sys.exit()
            return None
        # Create a copy of the curr class's ancestor
        curr_anc: CLClass = copy.deepcopy(get_direct_ancestor(ct, curr))
        # Push at front of rtn deque the ancestor of the current class 
        rtn.appendleft(curr_anc)
        visited.add(curr.ident.name)
        curr = ct[curr.superclass.name]
    if ('Object' not in {c.ident.name for c in rtn}):
        rtn.appendleft(CLOBJECTINSTANCE)
    return(rtn)

def gen_class_map(ct: dict[str, CLClass], c: CLClass) -> (list[tuple[str, str, CLConstant | CLExpr]]|list):
    """Produce a class map. `See CRM page here for spec <https://weimer.github.io/csci2320/crm/Class%20definitions.html>`_
    
    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str,CLClass]
    :param c: class to find all declared attributes of, up to object
    :type c: CLClass
    :return: a list of tuples: (attribute name X attribute type X initial value)
    :rtype: list (tuple(str, str, CLConstant | CLExpr))
    """
    # tuple(str: f_ident, str: att_type, CLConstant|CLExpr)
    rtn: list[tuple[str,str,CLConstant|CLExpr]]
    rtn = []
    c_attrs = get_class_attr_a(ct, c)
    while (c_attrs):
        curr_attr = c_attrs.popleft()
        match curr_attr.f_type:
            case 'attribute_no_init':
                match curr_attr.att_type.name:
                    case 'Int':
                        rtn.append((curr_attr.f_ident.name,
                                    curr_attr.att_type.name,
                                    CLConstant(curr_attr.att_type, 0)))
                    case 'String':
                        rtn.append((curr_attr.f_ident.name,
                                    curr_attr.att_type.name,
                                    CLConstant(curr_attr.att_type, '')))
                    case 'Bool':
                        rtn.append((curr_attr.f_ident.name,
                                    curr_attr.att_type.name,
                                    CLConstant(curr_attr.att_type, 'false')))
                    case _:
                        rtn.append((curr_attr.f_ident.name,
                                    curr_attr.att_type.name,
                                    CLConstant(curr_attr.att_type, 'void')))
            case 'attribute_init':
                rtn.append((curr_attr.f_ident.name, 
                            curr_attr.att_type.name,
                            copy.deepcopy(curr_attr.att_init)))
            case _:
                print('unknown error')
                sys.exit()
                return None
    return rtn

def gen_class_map_a(ct: dict[str, CLClass]) -> list[tuple[str, list[tuple[str, str, CLConstant|CLExpr]]]]:
    """Wrapper for `gen_class_map`. `See CRM page here for spec <https://weimer.github.io/csci2320/crm/Class%20definitions.html>`_.
    produces a list of tuples - (str X `gen_class_map`)
    
    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str,CLClass]
    :return: a list of tuples: (class name X list of tuples: (attribute name X attribute type X initial value))
    :rtype: list(tuple(str, list(tuple(str, str, CLConstant | CLExpr)))
    """
    rtn = []
    for cls in ct:
        rtn.append((cls, gen_class_map(ct, ct[cls])))
    return rtn


def gen_implementation_map(ct: dict[str, CLClass]) -> list[tuple[str,list[tuple[CLFeature, CLClass]]]]:
    """Produce an implementation map. `See CRM page here for spec <https://weimer.github.io/csci2320/crm/Class%20definitions.html>`_

    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str,CLClass]
    :return: a list where each item is a tuple that corresponds to a class in the ast + the basic COOL classes, paired with a list of all methods (declared, inherited and overridden)
    :rtype: list(tuple(str, list(tuple(CLFeature, CLClass)))
    """
    def alpha_cmp_CLFeature(f: CLFeature):
        return f.f_ident.name
    #[(Class.str,[(Method, Class)])]
    # ts crazy i know
    rtn: list[tuple[str,list[tuple[CLFeature,CLClass]]]] = []
    # For each class in the class symbol table,
    for k_cls, v_cls in ct.items():
        # get the path of classes to object
        path_to_obj: deque[CLClass] = get_ancestors(ct, v_cls)
        path_to_obj.append(copy.deepcopy(v_cls))
        c_methods: list[tuple[CLFeature, CLClass]] = []
        for c in path_to_obj:
            # Starting from Object, get the list of methods for each class 
            methods: list[CLFeature] = list(get_class_methods(c))
            # and sort them by method name iff internal methods
            if (c.ident.name in {'Object', 'IO', 'String'}):
                methods = sorted(methods, key=alpha_cmp_CLFeature)
            for m in methods: 
                nm_names = [c_mthd[0].f_ident.name for c_mthd in c_methods]
                if (m.f_ident.name in set(nm_names)):
                    override_idx = list(nm_names).index(m.f_ident.name)
                    if (m.f_ident.name in {'abort', 'copy', 'type_name', 
                                           'in_int', 'in_string', 'out_int', 'out_string'}):
                        # If m already exists in nm_names, and an internal method,
                        # replace the entry
                        c_methods[override_idx] = (copy.deepcopy(m), copy.deepcopy(c))
                    else:
                        # If m already exists in nm_names, and not an internal method,
                        # remove it from c_methods and add to end
                        c_methods.remove(c_methods[override_idx])
                        c_methods.append((copy.deepcopy(m), copy.deepcopy(c)))
                else:
                    c_methods.append((copy.deepcopy(m), copy.deepcopy(c)))
        rtn += [(k_cls, c_methods)]
    return rtn

def gen_parent_map(ct: dict[str, CLClass]) -> list[tuple[str,str]]:
    """Produce a parent map; the parent-child inheritance relations of a given COOL program

    :param ct: dict with references to all COOL classes in the AST
    :type ct: dict[str,CLClass]
    :return: a list of (child X parent) pairs
    :rtype: list(tuple(str, str))
    """
    rtn = []
    for cls in ct:
        if (cls == 'Object'):
            continue        
        if (not ct[cls].inherits):
            rtn += [(cls, 'Object')]
        else:
            rtn += [(cls, ct[cls].superclass.name)]
    return rtn