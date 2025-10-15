# COOL Type Checker

A semantic analyzer and type checker for the **COOL (Classroom Object-Oriented Language)** programming language. This tool validates COOL programs by checking type conformance, inheritance constraints, method signatures, and expression types according to the COOL language specification.

## Table of Contents

- [Overview](#overview)
- [The COOL Language](#the-cool-language)
- [How the Type Checker Works](#how-the-type-checker-works)
- [Installation & Requirements](#installation--requirements)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Type Checking Rules](#type-checking-rules)
- [Examples](#examples)
- [Testing](#testing)

## Overview

This type checker is part of a COOL compiler toolchain. It reads serialized Abstract Syntax Trees (ASTs), performs comprehensive semantic analysis, and outputs type-annotated ASTs along with class/method/parent mapping information.

**Pipeline:**
```
COOL Source (.cl) → Parser → AST (.cl-ast) → Type Checker → Annotated AST (.cl-type)
```

## The COOL Language

COOL (Classroom Object-Oriented Language) is a small, statically-typed object-oriented language designed for teaching compiler construction. It features:

### Key Features

- **Object-Oriented**: Classes, inheritance, method dispatch
- **Static Typing**: All types checked at compile time
- **Built-in Types**: `Object`, `IO`, `Int`, `String`, `Bool`
- **Special Type**: `SELF_TYPE` for type-safe method chaining
- **Expression-based**: Everything is an expression with a type
- **Automatic Memory Management**: No manual memory management

### Basic Syntax

```cool
(* Hello World in COOL *)
class Main inherits IO {
    main() : Object {
        out_string("Hello, World!\n")
    };
};
```

### Language Constructs

**Class Definitions:**
```cool
class ClassName inherits ParentClass {
    (* Attributes *)
    x : Int <- 42;              -- Initialized attribute
    y : String;                  -- Uninitialized attribute

    (* Methods *)
    foo(param : Int) : Int {
        param + x
    };
};
```

**Expressions:**
- **Arithmetic**: `+`, `-`, `*`, `/`
- **Comparison**: `<`, `<=`, `=`
- **Boolean**: `not`, `isvoid`
- **Control Flow**: `if ... then ... else ... fi`, `while ... loop ... pool`
- **Let Bindings**: `let x : Int <- 5 in x + 1`
- **Case Expressions**: `case expr of x : Type => ... esac`
- **Object Creation**: `new ClassName`
- **Method Dispatch**: `obj.method(args)`, `obj@Type.method(args)`
- **Assignment**: `x <- value`

**Built-in Classes:**

- **Object**: Root of the type hierarchy
  - `abort()`: Aborts program execution
  - `type_name()`: Returns class name as String
  - `copy()`: Returns shallow copy

- **IO**: Input/output operations
  - `out_string(s : String)`: Output string
  - `out_int(i : Int)`: Output integer
  - `in_string()`: Read string
  - `in_int()`: Read integer

- **String**: String operations
  - `length()`: Returns string length
  - `concat(s : String)`: Concatenates strings
  - `substr(i : Int, l : Int)`: Returns substring

- **Int**, **Bool**: Primitive types with no additional methods

### SELF_TYPE Semantics

`SELF_TYPE` is a special type that refers to the class of the current object. It enables type-safe method chaining:

```cool
class Animal {
    copy() : SELF_TYPE { self };
};

class Dog inherits Animal { };

class Main {
    main() : Object {
        let d : Dog <- new Dog in
        let d2 : Dog <- d.copy() in  (* copy() returns Dog, not Animal *)
        d2
    };
};
```

### Program Requirements

Every COOL program must have:
1. A `Main` class
2. A `main()` method in the `Main` class with no parameters
3. No inheritance from `Int`, `String`, or `Bool`
4. No class named `SELF_TYPE`

## How the Type Checker Works

The type checker follows a multi-phase architecture:

### Phase 1: Parsing (parser.py)
- Reads serialized AST format from `.cl-ast` files
- Constructs Python object hierarchy representing the program structure
- Detects duplicate class and method names

### Phase 2: Symbol Table Construction (util.py)
- **Class Table**: Maps class names to class definitions (includes built-in classes)
- **Object Environment**: Maps `(class, variable)` pairs to types (for attributes)
- **Method Environment**: Maps `(class, method)` pairs to signatures (parameter types + return type)

Validates:
- No attribute redefinition in inheritance chain
- Method overrides have identical signatures (parameters and return type)
- No use of `self` as attribute name

### Phase 3: Type Checking (type_checking_rules.py)
Validates for each class:
- **Inheritance Rules**: No cycles, no inheriting from Int/String/Bool
- **Attribute Initializers**: Initializer type conforms to declared type
- **Method Bodies**: Body type conforms to declared return type
- **Expressions**: All expressions satisfy COOL type rules

Type checking uses **environment passing**: each expression is checked in the context of its enclosing class and current variable bindings.

### Phase 4: Output Generation
Produces `.cl-type` file containing:
1. **Class Map**: Attribute initialization info for each class
2. **Implementation Map**: Method dispatch tables (which class defines each method)
3. **Parent Map**: Inheritance relationships
4. **Annotated AST**: Original AST with static type annotations on every expression

## Installation & Requirements

**Prerequisites:**
- Python 3.7+
- COOL parser tool (`./cool`) for generating AST files

**No external dependencies** - uses only Python standard library:
- `sys`, `copy`, `collections.deque`, `contextlib`

## Usage

### Basic Usage

1. **Generate AST from COOL source:**
```bash
./cool --parse --out output input.cl
# Produces: output.cl-ast
```

2. **Run type checker:**
```bash
./main.py output.cl-ast
# Produces: output.cl-type
```

### Example Workflow

```bash
# Type check a COOL program
./cool --parse --out hello tests/hello.cl
./main.py hello.cl-ast

# Output file hello.cl-type contains:
# - Type annotations
# - Class/method/parent maps
```

### Error Handling

The type checker performs **fail-fast** error handling:
- Prints error message with line number
- Exits immediately on first error
- No error recovery or multiple error reporting

Common errors:
- Type mismatch (e.g., assigning String to Int)
- Unknown identifier or method
- Inheritance violations
- Method override signature mismatch
- Invalid use of `self` or `SELF_TYPE`

## Project Structure

```
.
├── main.py                      # Entry point
├── lib/
│   ├── __init__.py             # Module exports
│   ├── cl_types.py             # COOL type definitions (classes, expressions, etc.)
│   ├── parser.py               # AST deserialization
│   ├── util.py                 # Symbol tables, type operations (join, conforms)
│   └── type_checking_rules.py  # Semantic analysis and type checking
├── tests/                       # Test COOL programs
│   ├── *.cl                    # COOL source files
│   ├── good/                   # Expected type-checked output
│   └── bad/                    # Programs with type errors
├── check_tests.sh              # Run all tests
└── README.md
```

### Module Descriptions

**cl_types.py** - Defines data structures for COOL language constructs:
- Class, method, attribute definitions
- 25+ expression types (dispatch, if, let, case, arithmetic, etc.)
- Built-in class generators (`mkCLObject()`, `mkCLIO()`, etc.)

**parser.py** - State machine parser for serialized AST format:
- Converts line-based AST representation to Python objects
- Handles classes, features, formals, expressions recursively

**util.py** - Type system utilities:
- `init_class_table()`: Builds class symbol table with built-ins
- `get_obj_env_dict()`: Creates variable → type mapping
- `get_method_env_dict()`: Creates method → signature mapping
- `conforms(c1, c2)`: Checks subtype relation (c1 ≤ c2)
- `join(t1, t2)`: Computes least upper bound of two types
- `get_ancestors(c)`: Returns inheritance chain

**type_checking_rules.py** - Semantic validation:
- `type_check()`: Main entry point, validates entire program
- `tc_class()`: Type checks all features in a class
- `tc_method()`: Validates method signature and body
- `tc_expr()`: Dispatches to specific expression type checkers
- Output functions: `print_class_map()`, `print_implementation_map()`, etc.

## Type Checking Rules

### Type Conformance

Type `C` conforms to type `D` (written `C ≤ D`) if:
- `C` = `D`, or
- `C` inherits from `D` (directly or transitively)

Special cases:
- Everything conforms to `Object`
- `Int`, `String`, `Bool` only conform to themselves and `Object` (cannot be inherited)
- `SELF_TYPE` in class `C` conforms to `C`

### Expression Type Rules (Selected)

| Expression | Type Rule |
|------------|-----------|
| `e1 + e2` | `e1 : Int` and `e2 : Int`, result is `Int` |
| `e1 < e2` | `e1 : Int` and `e2 : Int`, result is `Bool` |
| `e1 = e2` | If `e1` or `e2` is `Int`/`String`/`Bool`, types must match exactly. Result is `Bool` |
| `if e1 then e2 else e3` | `e1 : Bool`, result is `join(type(e2), type(e3))` |
| `while e1 loop e2` | `e1 : Bool`, `e2` any type, result is `Object` |
| `new T` | Result is type `T` (or `SELF_TYPE` if `T` is `SELF_TYPE`) |
| `isvoid e` | `e` any type, result is `Bool` |
| `e.method(args)` | `e : T`, method exists in `T`, args conform to parameters, result is return type (with `SELF_TYPE` resolution) |
| `let x : T <- e1 in e2` | `e1 : S` where `S ≤ T`, check `e2` with `x : T` in scope |
| `case e of x1:T1 => e1; ... xn:Tn => en esac` | All branch types must be distinct, result is `join(type(e1), ..., type(en))` |

### Method Override Rules

When class `C` inherits from `P` and overrides method `m`:
- Number of parameters must match exactly
- Each parameter type must match exactly (no contravariance)
- Return type must match exactly (no covariance)

This is **stricter** than many OO languages (like Java/C++).

### Attribute Inheritance

- Cannot redefine inherited attributes
- Attributes initialized in inheritance order (ancestors first)
- Initializer expression evaluated at object creation time

## Examples

### Example 1: Basic Class with Inheritance

**Input: simple.cl**
```cool
class Silly {
    copy() : SELF_TYPE { self };
};

class Sally inherits Silly { };

class Main {
    x : Sally <- (new Sally).copy();
    main() : Sally { x };
};
```

The type checker validates:
- `Sally` inherits from `Silly`, which is valid
- `copy()` returns `SELF_TYPE`, which resolves to `Sally` when called on `Sally` instance
- `x` is correctly initialized with type `Sally`
- `main()` returns `x` which has type `Sally`, matching the signature

### Example 2: Method Dispatch and IO

**Input: hello.cl**
```cool
class Printer inherits IO {
    x : String;

    init(s : String) : SELF_TYPE {
        {
            x <- s;
            self;
        }
    };

    print() : Object {
        out_string(x)
    };
};

class Main inherits IO {
    main() : Object {
        (new Printer).init("Hello").print()
    };
};
```

The type checker validates:
- `Printer` inherits from `IO` (built-in class)
- `init()` correctly returns `SELF_TYPE` for method chaining
- `out_string()` method exists in `IO` and accepts `String`
- Method chain `(new Printer).init("Hello").print()` type checks correctly

### Example 3: Type Error

**Input: bad.cl**
```cool
class Main {
    x : Int <- "hello";  (* ERROR: String does not conform to Int *)
    main() : Object { x };
};
```

The type checker will report:
```
ERROR: 2: Type-Check: attribute initializer type String does not conform to declared type Int
```

## Testing

### Run All Tests

```bash
# Run all good tests and compare with expected output
./check_tests.sh

# Run tests that should produce errors
./check_bad.sh
```

### Test Structure

- **tests/*.cl**: COOL source files
- **tests/good/*.cl-type**: Expected type checker output for valid programs
- **tests/bad/**: Programs with intentional type errors

### Adding New Tests

1. Create `tests/yourtest.cl`
2. Generate AST: `./cool --parse --out yourtest tests/yourtest.cl`
3. Run type checker: `./main.py yourtest.cl-ast`
4. For valid programs, save expected output: `cp yourtest.cl-type tests/good/yourtest.cl-type`

## Implementation Notes

### Design Decisions

1. **Fail-fast error handling**: Type checker exits on first error rather than collecting multiple errors
2. **AST mutation**: Type checking annotates AST nodes in-place with `s_type` field
3. **Environment passing**: Object and method environments passed explicitly through call chain (no global state)
4. **SELF_TYPE resolution**: Resolved contextually during type checking, not during parsing

### Performance Considerations

- Symbol tables built once before type checking
- Ancestor chains computed on-demand (could be cached for large inheritance hierarchies)
- Deep copying used extensively to avoid aliasing bugs (acceptable for compiler use case)

### Limitations

- No type inference (all types must be explicitly declared)
- No error recovery (stops at first error)
- No support for generics or parametric polymorphism
- Integer and string literals have no overflow/length checking

## References

- [COOL Reference Manual](https://kelloggm.github.io/martinjkellogg.com/teaching/cs485-sp25/crm/onepage/crm-onepage.html)
- Type Checking Theory: Pierce, Benjamin C. "Types and Programming Languages"

## License

Educational project - see course materials for usage guidelines.
