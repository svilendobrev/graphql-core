from pytest import raises

from graphql.error import GraphQLSyntaxError
from graphql.language import ast
from graphql.language.location import SourceLocation
from graphql.language.parser import Loc, parse
from graphql.language.source import Source

from .fixtures import KITCHEN_SINK


def test_repr_loc():
    # type: () -> None
    loc = Loc(start=10, end=25, source="foo")
    assert repr(loc) == "<Loc start=10 end=25 source=foo>"


def test_empty_parse():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        parse("")
    assert (
        u"Syntax Error GraphQL (1:1) Unexpected EOF\n" u"\n"
    ) == excinfo.value.message


def test_parse_provides_useful_errors():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        parse("""{""")
    assert (
        u"Syntax Error GraphQL (1:2) Expected Name, found EOF\n"
        u"\n"
        u"1: {\n"
        u"    ^\n"
        u""
    ) == excinfo.value.message

    assert excinfo.value.positions == [1]
    assert excinfo.value.locations == [SourceLocation(line=1, column=2)]

    with raises(GraphQLSyntaxError) as excinfo:
        parse(
            """{ ...MissingOn }
fragment MissingOn Type
"""
        )
    assert 'Syntax Error GraphQL (2:20) Expected "on", found Name "Type"' in str(
        excinfo.value
    )

    with raises(GraphQLSyntaxError) as excinfo:
        parse("{ field: {} }")
    assert "Syntax Error GraphQL (1:10) Expected Name, found {" in str(excinfo.value)

    with raises(GraphQLSyntaxError) as excinfo:
        parse("notanoperation Foo { field }")
    assert 'Syntax Error GraphQL (1:1) Unexpected Name "notanoperation"' in str(
        excinfo.value
    )

    with raises(GraphQLSyntaxError) as excinfo:
        parse("...")
    assert "Syntax Error GraphQL (1:1) Unexpected ..." in str(excinfo.value)


def test_parse_provides_useful_error_when_using_source():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        parse(Source("query", "MyQuery.graphql"))
    assert "Syntax Error MyQuery.graphql (1:6) Expected {, found EOF" in str(
        excinfo.value
    )


def test_parses_variable_inline_values():
    # type: () -> None
    parse("{ field(complex: { a: { b: [ $var ] } }) }")


def test_parses_constant_default_values():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        parse("query Foo($x: Complex = { a: { b: [ $var ] } }) { field }")
    assert "Syntax Error GraphQL (1:37) Unexpected $" in str(excinfo.value)


def test_does_not_accept_fragments_named_on():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        parse("fragment on on on { on }")

    assert 'Syntax Error GraphQL (1:10) Unexpected Name "on"' in excinfo.value.message


def test_does_not_accept_fragments_spread_of_on():
    # type: () -> None
    with raises(GraphQLSyntaxError) as excinfo:
        parse("{ ...on }")

    assert "Syntax Error GraphQL (1:9) Expected Name, found }" in excinfo.value.message


def test_allows_null_value():
    parse('{ fieldWithNullableStringInput(input: null) }')


def test_parses_null_value_to_null():
    result = parse('{ fieldWithObjectInput(input: {a: null, b: null, c: "C", d: null}) }')
    values = result.definitions[0].selection_set.selections[0].arguments[0].value.fields
    expected = (
        (u'a', ast.NullValue()),
        (u'b', ast.NullValue()),
        (u'c', ast.StringValue(value=u'C')),
        (u'd', ast.NullValue()),
    )
    for name_value, actual in zip(expected, values):
        assert name_value == (actual.name.value, actual.value)


def test_parses_null_value_in_list():
    result = parse('{ fieldWithObjectInput(input: {b: ["A", null, "C"], c: "C"}) }')
    assert result == ast.Document(
        definitions=[
            ast.OperationDefinition(
                operation='query', name=None, variable_definitions=None, directives=[],
                selection_set=ast.SelectionSet(
                    selections=[
                        ast.Field(
                            alias=None,
                            name=ast.Name(value=u'fieldWithObjectInput'),
                            directives=[],
                            selection_set=None,
                            arguments=[
                                ast.Argument(
                                    name=ast.Name(value=u'input'),
                                    value=ast.ObjectValue(
                                        fields=[
                                            ast.ObjectField(
                                                name=ast.Name(value=u'b'),
                                                value=ast.ListValue(
                                                    values=[
                                                        ast.StringValue(value=u'A'),
                                                        ast.NullValue(),
                                                        ast.StringValue(value=u'C'),
                                                    ],
                                                ),
                                            ),
                                            ast.ObjectField(
                                                name=ast.Name(value=u'c'),
                                                value=ast.StringValue(value=u'C'),
                                            ),
                                        ]
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )


def test_null_as_name():
    result = parse('{ thingy(null: "stringcheese") }')
    assert result.definitions[0].selection_set.selections[0].name.value == 'thingy'
    assert result.definitions[0].selection_set.selections[0].arguments[0].name.value == 'null'


def test_parses_multi_byte_characters():
    # type: () -> None
    result = parse(
        u"""
        # This comment has a \u0A0A multi-byte character.
        { field(arg: "Has a \u0A0A multi-byte character.") }
    """,
        no_location=True,
        no_source=True,
    )
    assert result == ast.Document(
        definitions=[
            ast.OperationDefinition(
                operation="query",
                name=None,
                variable_definitions=None,
                directives=[],
                selection_set=ast.SelectionSet(
                    selections=[
                        ast.Field(
                            alias=None,
                            name=ast.Name(value=u"field"),
                            arguments=[
                                ast.Argument(
                                    name=ast.Name(value=u"arg"),
                                    value=ast.StringValue(
                                        value=u"Has a \u0a0a multi-byte character."
                                    ),
                                )
                            ],
                            directives=[],
                            selection_set=None,
                        )
                    ]
                ),
            )
        ]
    )


def tesst_allows_non_keywords_anywhere_a_name_is_allowed():
    non_keywords = [
        "on",
        "fragment",
        "query",
        "mutation",
        "subscription",
        "true",
        "false",
        "null",
    ]

    query_template = """
    query {keyword} {
        ... {fragment_name}
        ... on {keyword} { field }
    }
    fragment {fragment_name} on Type {
        {keyword}({keyword}: ${keyword}) @{keyword}({keyword}: {keyword})
    }
    """

    for keyword in non_keywords:
        fragment_name = keyword
        if keyword == "on":
            fragment_name = "a"

        parse(query_template.format(fragment_name=fragment_name, keyword=keyword))


def test_parses_kitchen_sink():
    # type: () -> None
    parse(KITCHEN_SINK)


def test_parses_anonymous_mutation_operations():
    # type: () -> None
    parse(
        """
        mutation {
            mutationField
        }
    """
    )


def test_parses_anonymous_subscription_operations():
    # type: () -> None
    parse(
        """
        subscription {
            mutationField
        }
    """
    )


def test_parses_named_mutation_operations():
    # type: () -> None
    parse(
        """
        mutation Foo {
            mutationField
        }
    """
    )


def test_parses_named_subscription_operations():
    # type: () -> None
    parse(
        """
        subscription Foo {
            subscriptionField
        }
    """
    )


def test_parse_creates_ast():
    # type: () -> None
    source = Source(
        """{
  node(id: 4) {
    id,
    name
  }
}
"""
    )
    result = parse(source)

    assert result == ast.Document(
        loc=Loc(start=0, end=41, source=source),
        definitions=[
            ast.OperationDefinition(
                loc=Loc(start=0, end=40, source=source),
                operation="query",
                name=None,
                variable_definitions=None,
                directives=[],
                selection_set=ast.SelectionSet(
                    loc=Loc(start=0, end=40, source=source),
                    selections=[
                        ast.Field(
                            loc=Loc(start=4, end=38, source=source),
                            alias=None,
                            name=ast.Name(
                                loc=Loc(start=4, end=8, source=source), value="node"
                            ),
                            arguments=[
                                ast.Argument(
                                    name=ast.Name(
                                        loc=Loc(start=9, end=11, source=source),
                                        value="id",
                                    ),
                                    value=ast.IntValue(
                                        loc=Loc(start=13, end=14, source=source),
                                        value="4",
                                    ),
                                    loc=Loc(start=9, end=14, source=source),
                                )
                            ],
                            directives=[],
                            selection_set=ast.SelectionSet(
                                loc=Loc(start=16, end=38, source=source),
                                selections=[
                                    ast.Field(
                                        loc=Loc(start=22, end=24, source=source),
                                        alias=None,
                                        name=ast.Name(
                                            loc=Loc(start=22, end=24, source=source),
                                            value="id",
                                        ),
                                        arguments=[],
                                        directives=[],
                                        selection_set=None,
                                    ),
                                    ast.Field(
                                        loc=Loc(start=30, end=34, source=source),
                                        alias=None,
                                        name=ast.Name(
                                            loc=Loc(start=30, end=34, source=source),
                                            value="name",
                                        ),
                                        arguments=[],
                                        directives=[],
                                        selection_set=None,
                                    ),
                                ],
                            ),
                        )
                    ],
                ),
            )
        ],
    )
