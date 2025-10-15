#!/usr/bin/python3
import sys
from contextlib import redirect_stdout

import lib

def main():
    # Get all lines from the file
    # TODO probably need to verify the arg & filename etc. :(
    lines = [ l.strip() for l in tuple(open(sys.argv[1], 'r')) ]

    # Initialize a parser object and give it the lines from the file
    p = lib.COOLParser(lines)
    p.reset_parser()

    ast = lib.read_prog(p)
    class_symbol_table = lib.init_class_table(ast)
    obj_env = lib.get_obj_env_dict(class_symbol_table)
    met_env = lib.get_method_env_dict(class_symbol_table)
    # This should annotate ast_ext nodes' s_type field with the static types calculated
    lib.type_check(class_symbol_table, met_env, obj_env)

    with open(sys.argv[1].split('.')[0] + '.cl-type', 'w') as out_file:
        with redirect_stdout(out_file):
            lib.print_class_map(class_symbol_table)
            lib.print_implementation_map(class_symbol_table)
            lib.print_parent_map(class_symbol_table)
            lib.print_annot_ast(ast)
    return

if __name__ == '__main__':
    main()