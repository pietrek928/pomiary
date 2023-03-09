from typing import Optional

from pydantic.main import BaseModel


class ValueSeriesDescr(BaseModel):
    offset: int
    format: str = 'H'
    count: int = 1
    scale: float = 1.


class PQAFieldConfig(BaseModel):
    frame_size: int
    time: Optional[ValueSeriesDescr] = None
    f_L12: Optional[ValueSeriesDescr] = None
    UL12: Optional[ValueSeriesDescr] = None
    UL23: Optional[ValueSeriesDescr] = None
    UL31: Optional[ValueSeriesDescr] = None
    UL12_h: Optional[ValueSeriesDescr] = None
    UL23_h: Optional[ValueSeriesDescr] = None
    UL31_h: Optional[ValueSeriesDescr] = None


TIME_SCALE = .1  # to miliseconds
U_SCALE = 0.01195
# U_SCALE = 1.

cfg_3p_nocurrent = PQAFieldConfig(
    frame_size=287,
    time=ValueSeriesDescr(
        offset=15, format='I', count=2, scale=TIME_SCALE
    ), UL12=ValueSeriesDescr(
        offset=23, scale=U_SCALE
    ), UL23=ValueSeriesDescr(
        offset=25, scale=U_SCALE
    ), UL31=ValueSeriesDescr(
        offset=27, scale=U_SCALE
    ), f_L12=ValueSeriesDescr(
        offset=29, scale=.01
    ), UL12_h=ValueSeriesDescr(
        offset=31, count=40, scale=U_SCALE
    ), UL23_h=ValueSeriesDescr(
        offset=111, count=40, scale=U_SCALE
    ), UL31_h=ValueSeriesDescr(
        offset=191, count=40, scale=U_SCALE
    )
)
