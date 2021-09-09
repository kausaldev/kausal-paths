import pandas as pd
from nodes.context import Context
from . import ActionNode as BaseActionNode
from nodes.constants import FORECAST_COLUMN, VALUE_COLUMN
from params import StringParameter
from common.i18n import TranslatedString


class ActionNode(BaseActionNode):
    unit = 'kt'
    quantity = 'emissions'
    input_datasets = ['kpr/indicator_results']

    allowed_parameters = [
        StringParameter(
            local_id='panorama_id',
            label=TranslatedString(en="Node ID in Panorama"),
            is_customizable=False
        ),
    ]

    def compute_effect(self, context: Context) -> pd.DataFrame:
        df = self.get_input_dataset(context)
        sec_id = self.get_parameter_value('panorama_id')
        print(sec_id)
        df = df.set_index(['NyckelID', 'År']).loc[sec_id]
        val = df['Panorama potential (kton utsläppsminskning)']
        df = pd.DataFrame(val.values, index=val.index.astype(int), columns=[VALUE_COLUMN])
        df[VALUE_COLUMN] = -df[VALUE_COLUMN]
        df[FORECAST_COLUMN] = True
        df.loc[df.index < 2020, VALUE_COLUMN] = 0
        return df
