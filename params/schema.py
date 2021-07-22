from typing import Any, List
import graphene
import json
from graphql.error import GraphQLError

from . import (
    BoolParameter, NumberParameter, Parameter, PercentageParameter, StringParameter,
    ValidationError
)
from nodes.scenario import ScenarioExport
from paths.graphql_helpers import GQLInfo


class ResolveDefaultValueMixin:
    @staticmethod
    def resolve_default_value(root: Parameter, info: GQLInfo) -> Any:
        context = info.context.instance.context
        scenario = context.get_default_scenario()
        return root.get_scenario_setting(scenario)


class ParameterInterface(graphene.Interface):
    id = graphene.ID()  # global id
    label = graphene.String()
    description = graphene.String()
    node_relative_id = graphene.ID()  # can be null if node is null
    node = graphene.Field('nodes.schema.NodeType')  # can be null for global parameters
    is_customized = graphene.Boolean()
    is_customizable = graphene.Boolean()

    # TODO: Use the proper field names instead of defining this alias?
    def resolve_id(root, info):
        return root.global_id

    # TODO: Use the proper field names instead of defining this alias?
    def resolve_node_relative_id(root, info):
        return root.local_id

    @classmethod
    def resolve_type(cls, parameter, info):
        type_map = {
            BoolParameter: BoolParameterType,
            NumberParameter: NumberParameterType,
            StringParameter: StringParameterType,
            PercentageParameter: NumberParameterType,
        }
        # Try to find the parameter type by going through the superclasses
        # of the parameter instance.
        for param_type in type(parameter).mro():
            if param_type in type_map:
                return type_map[param_type]
        raise Exception(f"{parameter} has invalid type")


class BoolParameterType(ResolveDefaultValueMixin, graphene.ObjectType):
    class Meta:
        interfaces = (ParameterInterface,)

    value = graphene.Boolean()
    default_value = graphene.Boolean()


class NumberParameterType(ResolveDefaultValueMixin, graphene.ObjectType):
    class Meta:
        interfaces = (ParameterInterface,)

    value = graphene.Float()
    default_value = graphene.Float()
    min_value = graphene.Float()
    max_value = graphene.Float()
    step = graphene.Float()
    unit = graphene.Field('paths.schema.UnitType')


class StringParameterType(ResolveDefaultValueMixin, graphene.ObjectType):
    class Meta:
        interfaces = (ParameterInterface,)

    value = graphene.String()
    default_value = graphene.String()


class ScenarioExportType(graphene.ObjectType):
    data = graphene.String()
    filename = graphene.String()

    @staticmethod
    def resolve_data(root: ScenarioExport, info: GQLInfo):
        return root.to_json()

    @staticmethod
    def resolve_filename(root: ScenarioExport, info: GQLInfo):
        return root.json_filename


class SetParameterMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        number_value = graphene.Float()
        bool_value = graphene.Boolean()
        string_value = graphene.String()

    ok = graphene.Boolean()
    parameter = graphene.Field(ParameterInterface)

    def mutate(root, info: GQLInfo, id, number_value=None, bool_value=None, string_value=None):
        context = info.context.instance.context
        try:
            param = context.get_parameter(id)
        except KeyError:
            raise GraphQLError("Parameter %s does not exist", [info])

        if not param.is_customizable:
            raise GraphQLError("Parameter %s is not customizable", [info])

        parameter_values = {
            (NumberParameter, PercentageParameter): (number_value, 'numberValue'),
            BoolParameter: (bool_value, 'boolValue'),
            StringParameter: (string_value, 'stringValue'),
        }
        param_type = type(param)
        for klasses, (value, attr_name) in parameter_values.items():
            if isinstance(klasses, tuple):
                if param_type in klasses:
                    break
            elif param_type == klasses:
                break
        else:
            raise Exception("Attempting to mutate an unsupported parameter class: %s" % type(param))

        if value is None:
            raise GraphQLError("You must specify '%s' for '%s'" % (attr_name, param.id))

        del parameter_values[klasses]
        for v, _ in parameter_values.values():
            if v is not None:
                raise GraphQLError("Only one type of value allowed", [info])

        try:
            value = param.clean(value)
        except ValidationError as e:
            raise GraphQLError(str(e), [info])

        session = info.context.session
        session_settings = session.setdefault('settings', {})
        session_settings[id] = value

        context.activate_scenario(context.custom_scenario, session)
        session['active_scenario'] = context.custom_scenario.id
        # Explicitly mark session as modified because we might only have modified `session['settings']`, not `session`
        session.modified = True

        return SetParameterMutation(ok=True, parameter=param)


class ResetParameterMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    ok = graphene.Boolean()

    def mutate(root, info: GQLInfo, id=None):
        context = info.context.instance.context
        session = info.context.session
        if id is None:
            # Reset all parameters to defaults
            session.pop('params', None)
        else:
            params = session.get('params', {})
            params.pop(id, None)

        params = session.get('params', {})
        if not params:
            session['active_scenario'] = context.get_default_scenario().id

        info.context.session.modified = True
        return ResetParameterMutation(ok=True)


class ActivateScenarioMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    active_scenario = graphene.Field('nodes.schema.ScenarioType')

    def mutate(root, info: GQLInfo, id):
        context = info.context.instance.context
        session = info.context.session
        scenario = context.scenarios.get(id)
        if scenario is None:
            raise GraphQLError("Scenario '%s' not found" % id, [info])

        session['active_scenario'] = scenario.id
        context.activate_scenario(scenario, session)

        return dict(ok=True, active_scenario=scenario)


class ImportScenarioMutation(graphene.Mutation):
    class Arguments:
        data = graphene.String(required=True)

    ok = graphene.Boolean()
    scenario = graphene.Field('nodes.schema.ScenarioType')

    def mutate(root, info: GQLInfo, data):
        context = info.context.instance.context
        session = info.context.session
        session['imported_scenario'] = json.loads(data)
        session.modified = True
        return dict(ok=True, scenario=context.imported_scenario)


class Mutations(graphene.ObjectType):
    set_parameter = SetParameterMutation.Field()
    reset_parameter = ResetParameterMutation.Field()
    activate_scenario = ActivateScenarioMutation.Field()
    import_scenario = ImportScenarioMutation.Field()


class Query(graphene.ObjectType):
    parameters = graphene.List(ParameterInterface)
    parameter = graphene.Field(ParameterInterface, id=graphene.ID(required=True))
    scenario_export = graphene.Field(
        ScenarioExportType,
        id=graphene.ID(required=True),
        name=graphene.String(required=True)
    )

    def resolve_parameters(root, info: GQLInfo):
        instance = info.context.instance
        return instance.context.parameters.values()

    def resolve_parameter(root, info: GQLInfo, id):
        instance = info.context.instance
        try:
            return instance.context.get_parameter(id)
        except KeyError:
            raise GraphQLError(f"Parameter {id} does not exist")

    def resolve_scenario_export(root, info: GQLInfo, id, name):
        context = info.context.instance.context
        session = info.context.session
        try:
            return context.export_scenario(id, name, session)
        except KeyError:
            raise GraphQLError(f"Scenario {id} does not exist")


types = [
    BoolParameterType,
    NumberParameterType,
    StringParameterType,
]
