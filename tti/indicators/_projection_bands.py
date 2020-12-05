"""
Trading-Technical-Indicators (tti) python library

File name: _projection_bands.py
    Implements the Projection Bands technical indicator.
"""

import pandas as pd
import numpy as np

from ._technical_indicator import TechnicalIndicator
from ..utils.constants import TRADE_SIGNALS
from ..utils.exceptions import NotEnoughInputData, WrongTypeForInputParameter,\
    WrongValueForInputParameter, NotConverged


class ProjectionBands(TechnicalIndicator):
    """
    Projection Bands Technical Indicator class implementation.

    Args:
        input_data (pandas.DataFrame): The input data. Required input columns
            are ``high``, ``low``, ``close``. The index is of type
            ``pandas.DatetimeIndex``.

        period (int, default=14): The past periods to be used for the
            calculation of the indicator.

        fill_missing_values (bool, default=True): If set to True, missing
            values in the input data are being filled.

    Attributes:
        _input_data (pandas.DataFrame): The ``input_data`` after preprocessing.

        _ti_data (pandas.DataFrame): The calculated indicator. Index is of type
            ``pandas.DatetimeIndex``. It contains two columns, the
            ``upper_band``, ``lower_band``.

        _properties (dict): Indicator properties.

        _calling_instance (str): The name of the class.

    Raises:
        WrongTypeForInputParameter: Input argument has wrong type.
        WrongValueForInputParameter: Unsupported value for input argument.
        NotEnoughInputData: Not enough data for calculating the indicator.
        TypeError: Type error occurred when validating the ``input_data``.
        ValueError: Value error occurred when validating the ``input_data``.
    """
    def __init__(self, input_data, period=14, fill_missing_values=True):

        # Validate and store if needed, the input parameters
        if isinstance(period, int):
            if period > 0:
                self._period = period
            else:
                raise WrongValueForInputParameter(
                    period, 'period', '>0')
        else:
            raise WrongTypeForInputParameter(
                type(period), 'period', 'int')

        # Control is passing to the parent class
        super().__init__(calling_instance=self.__class__.__name__,
                         input_data=input_data,
                         fill_missing_values=fill_missing_values)

    def _calculateTi(self):
        """
        Calculates the technical indicator for the given input data. The input
        data are taken from an attribute of the parent class.

        Returns:
            pandas.DataFrame: The calculated indicator. Index is of type
            ``pandas.DatetimeIndex``. It contains two columns, the
            ``upper_band``, ``lower_band``.

        Raises:
            NotEnoughInputData: Not enough data for calculating the indicator.
        """

        # Not enough data for the requested period
        if len(self._input_data.index) < self._period:
            raise NotEnoughInputData('Projection Bands', self._period,
                                     len(self._input_data.index))

        pbs = pd.DataFrame(index=self._input_data.index,
                           columns=['upper_band', 'lower_band'],
                           data=None, dtype='float64')

        # Calculate n-periods slope of high values
        try:
            high_slope = self._input_data['high'].rolling(
                window=self._period, min_periods=self._period, center=False,
                win_type=None, on=None, axis=0, closed=None).apply(
                lambda x: np.polyfit(list(range(self._period)), x.values, 1)[0]
            )

        except np.linalg.LinAlgError:
            raise NotConverged(input_arguments='(period = ' + str(self._period)
                + ')', input_data_length=len(self._input_data.index))

        # Calculate n-periods slope of high values
        try:
            low_slope = self._input_data['low'].rolling(
                window=self._period, min_periods=self._period, center=False,
                win_type=None, on=None, axis=0, closed=None).apply(
                lambda x: np.polyfit(list(range(self._period)), x.values, 1)[0]
            )

        except np.linalg.LinAlgError:
            raise NotConverged(input_arguments='(period = ' + str(self._period)
                + ')', input_data_length=len(self._input_data.index))

        # Calculate the projection bands
        for i in range(self._period - 1, len(self._input_data.index)):

            pbs['upper_band'].iat[i] = max(
                [self._input_data['high'].iat[i]] + [
                    (j * high_slope.iat[i]) + self._input_data['high'].iat[
                        i - j] for j in range(1, self._period)])

            pbs['lower_band'].iat[i] = min(
                [self._input_data['low'].iat[i]] + [
                    (j * low_slope.iat[i]) + self._input_data['low'].iat[
                        i - j] for j in range(1, self._period)])

        return pbs.round(4)

    def getTiSignal(self):
        """
        Calculates and returns the trading signal for the calculated technical
        indicator.

        Returns:
            {('hold', 0), ('buy', -1), ('sell', 1)}: The calculated trading
            signal.
        """

        # Not enough data for calculating trading signal
        if len(self._ti_data.index) < 1:
            return TRADE_SIGNALS['hold']

        # Price goes close to the upper band, closer than 15% of the bands
        # distance
        if (self._ti_data['upper_band'].iat[-1] -
                self._input_data['close'].iat[-1] < 0.15 * (
                        self._ti_data['upper_band'].iat[-1] -
                        self._ti_data['lower_band'].iat[-1])):

            return TRADE_SIGNALS['sell']

        # Price goes close to the lower band, closer than 15% of the bands
        # distance
        if (self._input_data['close'].iat[-1] -
                self._ti_data['lower_band'].iat[-1] < 0.15 * (
                        self._ti_data['upper_band'].iat[-1] -
                        self._ti_data['lower_band'].iat[-1])):

            return TRADE_SIGNALS['buy']

        return TRADE_SIGNALS['hold']
