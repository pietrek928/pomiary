from datetime import datetime
from sys import argv

from matplotlib import pyplot as plt
from meas_analyzer.meas_extractor import SeriesFile, SMRFile
from numpy import sqrt, datetime64, cos, pi

from meas_analyzer.file_descr import cfg_3p_nocurrent
from meas_analyzer.meas_file import read_data_series

smr_file = SMRFile('panele-reg/RG000013/RG000013.SMR')
start_time = datetime.strptime(smr_file.start_time, '%Y-%m-%d %H:%M:%S.%f')
# print(datetime.strptime(smr_file.end_time, '%Y-%m-%d %H:%M:%S.%f'))

meas_file = SeriesFile(argv[1])

# print(tuple(map(float, read_data_series(meas_file, cfg_3p_nocurrent.UL12, 0, 100000000)[:100, :])))

l12_test = read_data_series(meas_file, cfg_3p_nocurrent.UL12, 0, 100)[:, 0]
l23_test = read_data_series(meas_file, cfg_3p_nocurrent.UL23, 0, 100)[:, 0]
l_test = sqrt(l12_test * l12_test + l23_test * l23_test - l12_test * l23_test * 2 * cos(pi * 2 / 3)) / sqrt(3)
print(tuple(map(float, l_test)))

# tm_series = read_data_series(meas_file, cfg_3p_nocurrent.time, 0, 100000000)
# tm_series = (tm_series[:, 0] - tm_series[0, 0]).astype('timedelta64[ms]') + datetime64(start_time)
#
# ul12_series = read_data_series(meas_file, cfg_3p_nocurrent.UL12_h, 0, 100000000)[:, 0]
# ul23_series = read_data_series(meas_file, cfg_3p_nocurrent.UL23_h, 0, 100000000)[:, 0]
# ul31_series = read_data_series(meas_file, cfg_3p_nocurrent.UL31_h, 0, 100000000)[:, 0]
#
# fig, (ax_l12, ax_l23, ax_l31) = plt.subplots(3, sharex='all', sharey='all', gridspec_kw={'hspace': 0})
# fig.suptitle('Phase voltage graph')
# ax_l12.plot(tm_series, ul12_series, color='brown', linewidth=.5)
# ax_l23.plot(tm_series, ul23_series, color='black', linewidth=.5)
# ax_l31.plot(tm_series, ul31_series, color='gray', linewidth=.5)
#
# plt.show()
