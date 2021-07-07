import json
import pytest
from graphene_django.utils.testing import graphql_query

from nodes.tests.factories import (
    ActionNodeFactory,  ContextFactory, CustomScenarioFactory, InstanceFactory, ScenarioFactory
)
from params.tests.factories import BoolParameterFactory


@pytest.fixture
def context():
    return ContextFactory()


@pytest.fixture
def action_node(context):
    node = ActionNodeFactory()
    context.add_node(node)
    return node


@pytest.fixture(autouse=True)  # autouse=True since InstanceMiddleware requires a default scenario
def default_scenario(context, action_node):
    scenario = ScenarioFactory(id='default', default=True, all_actions_enabled=True, nodes=[action_node])
    context.add_scenario(scenario)
    return scenario


@pytest.fixture
def custom_scenario(context, action_node, default_scenario):
    custom_scenario = CustomScenarioFactory(
        id='custom',
        name='Custom',
        base_scenario=default_scenario,
        nodes=[action_node],
    )
    context.set_custom_scenario(custom_scenario)
    return custom_scenario


@pytest.fixture(autouse=True)
def instance(context):
    from pages import global_instance
    global_instance.instance = InstanceFactory(context=context)
    return global_instance.instance


@pytest.fixture
def graphql_client_query(client):
    def func(*args, **kwargs):
        return graphql_query(*args, **kwargs, client=client, graphql_url='/v1/graphql/')
    return func


@pytest.fixture
def graphql_client_query_data(graphql_client_query):
    """Make a GraphQL request, make sure the `error` field is not present and return the `data` field."""
    def func(*args, **kwargs):
        response = graphql_client_query(*args, **kwargs)
        content = json.loads(response.content)
        assert 'errors' not in content
        return content['data']
    return func
