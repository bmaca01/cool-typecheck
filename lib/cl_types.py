from __future__ import annotations

##  Identifier classes
#   Every Identifier type has a line number (str) and name (str)
class CLClassIdent:
    """
    Attributes:
        line (str): line number where cool class appears
        name (str): name of cool class
    """
    line = ''
    name = ''

    def __init__(self, l: str, n: str):
        self.line = l
        self.name = n

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class CLSelfIdent:
    """
    Attributes:
        line (str): line number where `self` appears
        name (str): `self`
    """
    line = ''
    name = ''

    def __init__(self, l: str, n: str):
        self.line = l
        self.name = n
    
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class CLTypeIdent:
    """
    Attributes:
        line (str): line number where cool TYPE appears
        name (str): name of cool TYPE
        self_type_resolve (str): type of SELF_TYPE (?); empty if name != 'SELF_TYPE'
    """
    line = ''
    name = ''
    self_type_resolve: str=''      # trying hot fix shit i hate self_type

    def __init__(self, l: str, n: str):
        self.line = l
        self.name = n
    
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class CLVarIdent:
    """
    Attributes:
        line (str): line number where variable appears
        name (str): name of variable
    """
    line = ''
    name = ''

    def __init__(self, l: str, n: str):
        self.line = l
        self.name = n
    
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class CLMethodIdent:
    """
    Attributes:
        line (str): line number where method appears
        name (str): name of method
    """
    line = ''
    name = ''

    def __init__(self, l: str, n: str):
        self.line = l
        self.name = n
    
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class CLConstant:
    """
    Attributes:
        type (CLTypeIdent): Bool | Int | String | SELF_TYPE
        value (str | int): any cool constant as a string


    note: accd to CRM - "The special value void is a member of all types" -> implies void `can` be a constant ..?.. and the type of void is SELF_TYPE..? 
    """
    type = None
    value = None

    def __init__(self, t: CLTypeIdent, v: (str | int)):
        self.type = t
        self.value = v
    
    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

class CLFormal:
    """
    Attributes:
        name (CLVarIdent): name of declared param
        type (CLTypeIdent): type of declared param
    """
    name = None
    type = None

    def __init__(self, n: CLVarIdent, t: CLTypeIdent):
        self.name = n
        self.type = t
    
    def __str__(self):
        return self.name.__str__()
    
    def __repr__(self):
        return self.name.__str__()

class CLFeature:
    """
    Attributes:
        f_type (str): 'attribute_no_init' | 'attribute_init' | 'method'
        f_ident (CLVarIdent | CLMethodIdent): feature identifier, either a variable name or method name
        att_type (CLTypeIdent | None): CLTypeIdent iff f_type == 'attribute_no_init' | 'attribute_init'; declared type of variable name
        att_init (CLExpr | None): CLExpr iff f_type == 'attribute_init'; expr to evaluate and bind to variable
        m_type (CLTypeIdent | None): CLTypeIdent iff f_type == 'method'; declared return type of method
        m_formals (list[CLFormal]): method params
        m_body (CLExpr | None): CLExpr iff f_type == 'method'; expr to evaluate on method dispatch
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    f_type: str = None
    f_ident: (CLVarIdent|CLMethodIdent) = None
    att_type: (CLTypeIdent|None) = None
    att_init: (CLExpr|None) = None
    m_type: (CLTypeIdent|None) = None
    m_formals: list[CLFormal] = []
    m_body: (CLExpr|None) = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, 
                 f: str, 
                 n: (CLVarIdent | CLMethodIdent), 
                 t: CLTypeIdent, 
                 fls: list[CLFormal] | list = [], 
                 init: CLExpr | None = None, 
                 body: CLExpr | None = None):
        self.f_type = f
        self.f_ident = n
        match f:
            case 'attribute_no_init':
                self.att_type = t
            case 'attribute_init':
                self.att_type = t
                self.att_init = init
            case 'method':
                self.m_type = t
                self.m_formals = fls
                self.m_body = body

    def __str__(self):
        return f'{self.f_type},{self.f_ident.__str__()}'

    def __repr__(self):
        rtn = f'{self.f_type}, {self.f_ident.__str__()}, '
        match self.f_type:
            case 'attribute_no_init' | 'attribute_init':
                rtn += self.att_type.__str__()
            case 'method':
                rtn += self.m_type.__str__()
        return rtn

class CLClass:
    """
    Attributes:
        ident (CLClassIdent): name of cool class
        inherits (bool): False iff ident is 'Object'
        superclass (CLClassIdent | None): None iff ident is 'Object'; else some cool class if inherits is True
        features (list[CLFeature]): list of cool class features
    """
    ident: CLClassIdent = None
    inherits: bool = False
    superclass: CLClassIdent = None
    features: list[CLFeature] = []

    def __init__(self, 
                 id: CLClassIdent, 
                 features: list[CLFeature], 
                 inh: bool|bool=False, 
                 super: CLClassIdent|None=None):
        self.ident = id
        self.inherits = inh
        self.superclass = super
        self.features = features

    def __str__(self):
        return self.ident.__str__()

    def __repr__(self):
        return self.ident.__str__()

## A COOL program (ie AST) is just a list of classes
class CLAST:
    """
    Attributes:
        classes (list[CLClass]): list of declared classes in cool program
    """
    classes: list[CLClass] = []

    def __init__(self, l: list[CLClass]):
        self.classes = l

    def __str__(self):
        return f'{list(map(lambda a : f"{a.__str__()},", self.classes))}'

    def __repr__(self):
        return f'{list(map(lambda a : f"{a.__str__()},", self.classes))}'

class CLExpr:
    """Expr node of AST
    
    Attributes:
        line_num (str)  : line number where expr appears in prog
        type (str)      : "type" of expression. Possible values: [assign | dynamic_dispatch | static_dispatch | self_dispatch | if | while | block | new | isvoid | plus | minus | times | divide | lt | le | eq | not | negate | integer | string | identifier | true | false | let | case] 
        body (CLAssign | CLDynDispatch | CLStaticDispatch | CLSelfDispatch | CLIf | CLWhile | CLBlock | CLNew | CLIsvoid | CLPlus | CLMinus | CLTimes | CLDivide | CLLT | CLLE | CLEQ | CLNOT | CLNegate | CLConstant | CLSelfIdent | CLVarIdent | CLLet | CLCase): node pointer to expr body
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    line_num = ''
    type = ''
    body: (CLAssign | CLDynDispatch | CLStaticDispatch | CLSelfDispatch | CLIf | CLWhile | CLBlock | CLNew | CLIsvoid | CLPlus | CLMinus | CLTimes | CLDivide | CLLT | CLLE | CLEQ | CLNOT | CLNegate | CLConstant | CLSelfIdent | CLVarIdent | CLLet | CLCase | None)
    body = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: str, t: str, term: CLAssign | CLDynDispatch | CLStaticDispatch | CLSelfDispatch | CLIf | CLWhile | CLBlock | CLNew | CLIsvoid | CLPlus | CLMinus | CLTimes | CLDivide | CLLT | CLLE | CLEQ | CLNOT | CLNegate | CLConstant | CLSelfIdent | CLVarIdent | CLLet | CLCase):
        self.line_num = l
        self.type = t
        self.body = term
    
    def __str__(self):
        return f'expr,{self.type},{self.body.__str__()}'
    
    def __repr__(self):
        return f'expr,{self.type},{self.body.__str__()}'

class CLAssign:
    """
    Attributes:
        var (CLVarIdent)    : node pointing to variable being assigned to
        rhs (CLExpr)        : node pointing to expr to assign variable to
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    var = None
    rhs = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, v: CLVarIdent, r: CLExpr):
        self.var = v
        self.rhs = r
    
    def __str__(self):
        return f'{self.var.__str__()},<-,{self.rhs.__str__()}'
    
    def __repr__(self):
        return f'{self.var.__str__()},<-,{self.rhs.__str__()}'


class CLDynDispatch:
    """
    Attributes:
        caller (CLExpr): pointer to CLExpr object that evaluates to a cool object
        method_name (CLMethodIdent): name of method being dispatched on cool object
        args (list[CLExpr]): list of CLExpr objects that evalute to method arguments
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    caller = None
    method_name = None
    args = []
    s_type: (CLTypeIdent|None) = None

    def __init__(self, c: CLExpr, n: CLMethodIdent, a: list[CLExpr]):
        self.caller = c
        self.method_name = n
        self.args = a
    
    def __str__(self):
        return f'{self.caller.__str__()},.,{self.method_name.__str__()},{list(map(lambda a: f"{a.__str__()},", self.args))}'
    
    def __repr__(self):
        return f'{self.caller.__str__()},.,{self.method_name.__str__()},{list(map(lambda a: f"{a.__str__()},", self.args))}'

class CLStaticDispatch:
    """
    Attributes:
        caller (CLExpr): pointer to CLExpr object that evaluates to a cool object
        type (CLTypeIdent): name of class to dispatch method_name from
        method_name (CLMethodIdent): name of method being dispatched on cool object
        args (list[CLExpr]): list of CLExpr objects that evalute to method arguments
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    caller = None
    type = None
    method_name = None
    args = []
    s_type: (CLTypeIdent|None) = None

    def __init__(self, c: CLExpr, t: CLTypeIdent, n: CLMethodIdent, a: list[CLExpr]):
        self.caller = c
        self.type = t
        self.method_name = n
        self.args = a

    def __str__(self):
        return f'{self.caller.__str__()},@,{self.type.__str__()},.,{self.method_name.__str__()},(,{list(map(lambda a: f"{a.__str__()},", self.args))})'

    def __repr__(self):
        return f'{self.caller.__str__()},@,{self.type.__str__()},.,{self.method_name.__str__()},(,{list(map(lambda a: f"{a.__str__()},", self.args))})'

class CLSelfDispatch:
    """
    Attributes:
        method_name (CLMethodIdent): name of method being dispatched on self (ie enclosing class)
        args (list[CLExpr]): list of CLExpr objects that evalute to method arguments
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    method_name = None
    args = []
    s_type: (CLTypeIdent|None) = None

    def __init__(self, n: CLMethodIdent, a: list[CLExpr]):
        self.method_name = n
        self.args = a

    def __str__(self):
        return f'{self.method_name.__str__()},(,{list(map(lambda a : f"{a.__str__()},", self.args))})'

    def __repr__(self):
        return f'{self.method_name.__str__()},(,{list(map(lambda a : f"{a.__str__()},", self.args))})'

class CLIf:
    """
    Attributes:
        pred (CLExpr): CLExpr object that evaluates to some bool to check
        true_case (CLExpr): CLExpr object to evaluate if pred is true
        false_case (CLExpr): CLExpr object to evaluate if pred is false
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    pred = None
    true_case = None
    false_case = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, p: CLExpr, t: CLExpr, f: CLExpr):
        self.pred = p
        self.true_case = t
        self.false_case = f
    
    def __str__(self):
        return f'if,{self.pred.__str__()},then,{self.true_case.__str__()},else,{self.false_case.__str__()}'
    
    def __repr__(self):
        return f'if,{self.pred.__str__()},then,{self.true_case.__str__()},else,{self.false_case.__str__()}'

class CLWhile:
    """
    Attributes:
        pred (CLExpr): CLExpr object that evaluates to some bool to check
        body (CLExpr): CLExpr object to evaluate if pred is true
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    pred = None
    body = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, p: CLExpr, b: CLExpr):
        self.pred = p
        self.body = b

    def __str__(self):
        return f'while,{self.pred.__str__()},loop,{self.body.__str__()},pool'

    def __repr__(self):
        return f'while,{self.pred.__str__()},loop,{self.body.__str__()},pool'

class CLBlock:
    """
    Attributes:
        expr_list (list[CLExpr]): CLExpr objects to evaluate in block
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    expr_list = []
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: list[CLExpr]):
        self.expr_list = l
    
    def __str__(self):
        return f' {{ {list(map(lambda a : f"{a.__str__()},", self.expr_list))} }} '
    
    def __repr__(self):
        return f' {{ {list(map(lambda a : f"{a.__str__()},", self.expr_list))} }} '

class CLNew:
    """
    Attributes:
        type_id (CLTypeIdent): type to instantiate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    type_id = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, t: CLTypeIdent):
        self.type_id = t

    def __str__(self):
        return f'new,{self.type_id.__str__()}'

    def __repr__(self):
        return f'new,{self.type_id.__str__()}'

class CLIsvoid:
    """
    Attributes:
        expr (CLExpr): CLExpr object to evaluate and check if value is void
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    expr = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, e: CLExpr):
        self.expr = e

    def __str__(self):
        return f'isvoid,{self.expr.__str__()}'

    def __repr__(self):
        return f'isvoid,{self.expr.__str__()}'

class CLPlus:
    """
    Attributes:
        lhs (CLExpr): CLExpr object to evaluate
        rhs (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    lhs = None
    rhs = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: CLExpr, r: CLExpr):
        self.lhs = l
        self.rhs = r

    def __str__(self):
        return f'{self.lhs.__str__()},+,{self.rhs.__str__()}'

    def __repr__(self):
        return f'{self.lhs.__str__()},+,{self.rhs.__str__()}'

class CLMinus:
    """
    Attributes:
        lhs (CLExpr): CLExpr object to evaluate
        rhs (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    lhs = None
    rhs = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: CLExpr, r: CLExpr):
        self.lhs = l
        self.rhs = r

    def __str__(self):
        return f'{self.lhs.__str__()},-,{self.rhs.__str__()}'

    def __repr__(self):
        return f'{self.lhs.__str__()},-,{self.rhs.__str__()}'

class CLTimes:
    """
    Attributes:
        lhs (CLExpr): CLExpr object to evaluate
        rhs (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    lhs = None
    rhs = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: CLExpr, r: CLExpr):
        self.lhs = l
        self.rhs = r

    def __str__(self):
        return f'{self.lhs.__str__()},*,{self.rhs.__str__()}'

    def __repr__(self):
        return f'{self.lhs.__str__()},*,{self.rhs.__str__()}'
        
class CLDivide:
    """
    Attributes:
        lhs (CLExpr): CLExpr object to evaluate
        rhs (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    lhs = None
    rhs = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: CLExpr, r: CLExpr):
        self.lhs = l
        self.rhs = r

    def __str__(self):
        return f'{self.lhs.__str__()},/,{self.rhs.__str__()}'

    def __repr__(self):
        return f'{self.lhs.__str__()},/,{self.rhs.__str__()}'
        
class CLLT:
    """
    Attributes:
        lhs (CLExpr): CLExpr object to evaluate
        rhs (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    lhs = None
    rhs = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: CLExpr, r: CLExpr):
        self.lhs = l
        self.rhs = r

    def __str__(self):
        return f'{self.lhs.__str__()},<,{self.rhs.__str__()}'

    def __repr__(self):
        return f'{self.lhs.__str__()},<,{self.rhs.__str__()}'
        
class CLLE:
    """
    Attributes:
        lhs (CLExpr): CLExpr object to evaluate
        rhs (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    lhs = None
    rhs = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: CLExpr, r: CLExpr):
        self.lhs = l
        self.rhs = r

    def __str__(self):
        return f'{self.lhs.__str__()},<=,{self.rhs.__str__()}'

    def __repr__(self):
        return f'{self.lhs.__str__()},<=,{self.rhs.__str__()}'
        
class CLEQ:
    """
    Attributes:
        lhs (CLExpr): CLExpr object to evaluate
        rhs (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    lhs = None
    rhs = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: CLExpr, r: CLExpr):
        self.lhs = l
        self.rhs = r

    def __str__(self):
        return f'{self.lhs.__str__()},=,{self.rhs.__str__()}'

    def __repr__(self):
        return f'{self.lhs.__str__()},=,{self.rhs.__str__()}'
        
class CLNOT:
    """
    Attributes:
        expr (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    expr = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, e: CLExpr):
        self.expr = e

    def __str__(self):
        return f'not,{self.expr.__str__()}'

    def __repr__(self):
        return f'not,{self.expr.__str__()}'
        
class CLNegate:
    """
    Attributes:
        expr (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    expr = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, e: CLExpr):
        self.expr = e

    def __str__(self):
        return f'~,{self.expr.__str__()}'

    def __repr__(self):
        return f'~,{self.expr.__str__()}'

class CLLetBindingElem:
    """
    Attributes:
        bind_type (str): 'let_binding_no_init' | 'let_binding_init'
        v_name (CLVarIdent): CLVarIdent object representing the introduced variable binding
        v_type (CLTypeIdent): CLTypeIdent object representing the declared type of the varible
        v_init (None | CLExpr): CLExpr object to evaluate iff bind_type == 'let_binding_init'
    """
    bind_type = ''
    v_name = None
    v_type = None
    v_init = None

    def __init__(self, b: str, vn: CLVarIdent, vt: CLTypeIdent, vi: CLExpr | None=None):
        self.bind_type = b
        self.v_name = vn
        self.v_type = vt
        self.v_init = vi
    
    def __str__(self):
        return f'{self.bind_type},{self.v_name},{self.v_type}'
    
    def __repr__(self):
        return f'{self.bind_type},{self.v_name},{self.v_type}'

class CLLet:
    """
    Attributes:
        bind_list (list[CLLetBindingElem]): list of let bindings
        let_body (CLExpr): CLExpr object to evaluate
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    bind_list: list[CLLetBindingElem]
    bind_list = []
    let_body = None
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: list[CLLetBindingElem], b: CLExpr):
        self.bind_list = l
        self.let_body = b
    
    def __str__(self):
        return f'{list(map(lambda a : f"{a.__str__()},"))},{self.body.__str__}'
    
    def __repr__(self):
        return f'{list(map(lambda a : f"{a.__str__()},"))},{self.body.__str__}'

class CLCaseElem:
    """
    Attributes:
        ident (CLVarIdent): declared case variable to bind
        type (CLTypeIdent): type of declared case variable
        body (CLExpr): CLExpr object to evaluate and resulting value of whole case expr
    """
    ident = None
    type = None
    body = None

    def __init__(self, i: CLVarIdent, t: CLTypeIdent, b: CLExpr):
        self.ident = i
        self.type = t
        self.body = b

    def __str__(self):
        return f'{self.ident.__str__()},{self.type.__str__()},{self.body.__str__()}'

    def __repr__(self):
        return f'{self.ident.__str__()},{self.type.__str__()},{self.body.__str__()}'

class CLCase:
    """
    Attributes:
        line_num (str): line number of case expr
        c_expr (CLExpr): CLExpr object to evalute and check the dynamic type of
        c_list (list[CLCaseElem]): case elements to check c_expr against, choosing the least type
        s_type (CLTypeIdent): static type evaluated at type-check
    """
    line_num = ''
    c_expr = None
    c_list: list[CLCaseElem] = []
    s_type: (CLTypeIdent|None) = None

    def __init__(self, l: str, e: CLExpr, ls: list[CLCaseElem]):
        self.line_num = l
        self.c_expr = e
        self.c_list = ls

    def __str__(self):
        return f'{self.c_expr.__str__()},{list(map(lambda a : f"{a.__str__()},"))}'

    def __repr__(self):
        return f'{self.c_expr.__str__()},{list(map(lambda a : f"{a.__str__()},"))}'

def mkCLObject() -> CLClass:
    """return a CLClass obj representing COOL's Object class 

    Object is the root of all types
    """
    CLObjectFtList = []
    m_abort = CLExpr('0', 'internal', CLConstant(CLTypeIdent('0','Object'), 'Object.abort'))
    m_abort_rtn_t = CLTypeIdent('0', 'Object')
    m_abort.s_type = m_abort_rtn_t

    m_type_name = CLExpr('0', 'internal', CLConstant(CLTypeIdent('0','String'), 'Object.type_name'))
    m_type_name_rtn_t = CLTypeIdent('0', 'String')
    m_type_name.s_type = m_type_name_rtn_t

    m_copy = CLExpr('0', 'internal', CLConstant(CLTypeIdent('0','SELF_TYPE'), 'Object.copy'))
    m_copy_rtn_t = CLTypeIdent('0', 'SELF_TYPE')
    m_copy.s_type = m_copy_rtn_t

    CLObjectFtList.append(CLFeature('method', 
                               CLMethodIdent('0', 'abort'), 
                               m_abort_rtn_t,
                               [], None,
                               m_abort)
    )
    
    CLObjectFtList.append(CLFeature('method',
                               CLMethodIdent('0', 'type_name'),
                               m_type_name_rtn_t,
                               [], None,
                               m_type_name)
    )

    CLObjectFtList.append(CLFeature('method',
                               CLMethodIdent('0', 'copy'),
                               m_copy_rtn_t,
                               [], None,
                               m_copy)
    )

    return(CLClass(CLClassIdent('0', 'Object'), CLObjectFtList))

def mkCLIO() -> CLClass:
    """return a CLClass obj representing COOL's IO class """
    m_out_string_rtn_t = CLTypeIdent('0', 'SELF_TYPE')
    m_out_string = CLExpr('0', 'internal', CLConstant(m_out_string_rtn_t, 'IO.out_string'))
    m_out_string.s_type = m_out_string_rtn_t

    m_out_int_rtn_t = CLTypeIdent('0', 'SELF_TYPE')
    m_out_int = CLExpr('0', 'internal', CLConstant(m_out_int_rtn_t, 'IO.out_int'))
    m_out_int.s_type = m_out_int_rtn_t

    m_in_string_rtn_t = CLTypeIdent('0', 'String')
    m_in_string = CLExpr('0', 'internal', CLConstant(m_in_string_rtn_t, 'IO.in_string'))
    m_in_string.s_type = m_in_string_rtn_t

    m_in_int_rtn_t = CLTypeIdent('0', 'Int') 
    m_in_int = CLExpr('0', 'internal', CLConstant(m_in_int_rtn_t, 'IO.in_int'))
    m_in_int.s_type = m_in_int_rtn_t
    CLIOFtList = []

    CLIOFtList.append(CLFeature('method',
                               CLMethodIdent('0', 'out_string'),
                               m_out_string_rtn_t,
                               [CLFormal(CLVarIdent('0', 'x'), 
                                         CLTypeIdent('0', 'String'))],
                                None,
                                m_out_string)
    )

    CLIOFtList.append(CLFeature('method',
                               CLMethodIdent('0', 'out_int'),
                               m_out_int_rtn_t,
                               [CLFormal(CLVarIdent('0', 'x'), 
                                         CLTypeIdent('0', 'Int'))],
                                None,
                                m_out_int)
    )

    CLIOFtList.append(CLFeature('method', 
                               CLMethodIdent('0', 'in_string'), 
                               m_in_string_rtn_t,
                               [], None,
                               m_in_string)
    )

    CLIOFtList.append(CLFeature('method', 
                               CLMethodIdent('0', 'in_int'), 
                               m_in_int_rtn_t,
                               [], None,
                               m_in_int)
    )

    return(CLClass(CLClassIdent('0', 'IO'), CLIOFtList, True, mkCLObject().ident))

def mkCLString() -> CLClass:
    """return a CLClass obj representing COOL's String class """
    m_length_rtn_t = CLTypeIdent('0', 'Int')
    m_concat_rtn_t = CLTypeIdent('0', 'String')
    m_substr_rtn_t = CLTypeIdent('0', 'String')
    m_length = CLExpr('0', 'internal', CLConstant(m_length_rtn_t, 'String.length'))
    m_concat = CLExpr('0', 'internal', CLConstant(m_concat_rtn_t, 'String.concat'))
    m_substr = CLExpr('0', 'internal', CLConstant(m_substr_rtn_t, 'String.substr'))
    m_length.s_type = m_length_rtn_t
    m_concat.s_type = m_concat_rtn_t
    m_substr.s_type = m_substr_rtn_t
    CLStringFtList = []
    CLStringFtList.append(CLFeature('method', 
                               CLMethodIdent('0', 'length'), 
                               m_length_rtn_t,
                               [], None,
                               m_length)
    )
    
    CLStringFtList.append(CLFeature('method',
                               CLMethodIdent('0', 'concat'),
                               m_concat_rtn_t,
                               [CLFormal(CLVarIdent('0', 's'), 
                                         CLTypeIdent('0', 'String'))],
                                None,
                                m_concat)
    )

    CLStringFtList.append(CLFeature('method',
                               CLMethodIdent('0', 'substr'),
                               m_substr_rtn_t,
                               [CLFormal(CLVarIdent('0', 'i'), 
                                         CLTypeIdent('0', 'Int')),
                                CLFormal(CLVarIdent('0', 'l'), 
                                         CLTypeIdent('0', 'Int'))],
                                None,
                                m_substr)
    )

    return(CLClass(CLClassIdent('0', 'String'), CLStringFtList, True, mkCLObject().ident))

def mkCLInt() -> CLClass:
    """return a CLClass obj representing COOL's Int class """
    return(CLClass(CLClassIdent('0', 'Int'), [], True, mkCLObject().ident))

def mkCLBool() -> CLClass:
    """return a CLClass obj representing COOL's Bool class """
    return(CLClass(CLClassIdent('0', 'Bool'), [], True, mkCLObject().ident))

CLOBJECTINSTANCE = mkCLObject()
CLSTRINGINSTANCE = mkCLString()
CLIOINSTANCE = mkCLIO()
CLINTINSTANCE = mkCLInt()
CLBOOLINSTANCE = mkCLBool()
