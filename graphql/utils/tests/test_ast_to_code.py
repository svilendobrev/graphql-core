from graphql import Source, parse
from graphql.language import ast
from graphql.language.parser import Loc
from graphql.utils.ast_to_code import ast_to_code

from ...language.tests import fixtures
from ...utils.undefined import UndefinedDefaultValue


def test_ast_to_code_using_kitchen_sink():
    doc = parse(fixtures.KITCHEN_SINK)
    code_ast = ast_to_code(doc)
    source = Source(fixtures.KITCHEN_SINK)
    loc = lambda start, end: Loc(start, end, source)

    locals_ = {
        'ast': ast,
        'loc': loc,
        'UndefinedDefaultValue': UndefinedDefaultValue,
    }
    parsed_code_ast = eval(code_ast, {}, locals_)
    assert doc == parsed_code_ast
