from meas_analyzer.meas_extractor import SeriesFile

from meas_analyzer.file_descr import ValueSeriesDescr


def read_data_series(
        meas_file: SeriesFile, series_descr: ValueSeriesDescr,
        start_frame: int, frame_count: int
):
    if series_descr.format == 'H':
        return meas_file.fetch_data_u16(
            start_frame, frame_count, series_descr.offset, series_descr.count, series_descr.scale
        )
    elif series_descr.format == 'I':
        return meas_file.fetch_data_u32(
            start_frame, frame_count, series_descr.offset, series_descr.count, series_descr.scale
        )
    else:
        raise ValueError(f'Unsupported format {series_descr.format}')
