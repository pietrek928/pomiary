#include <boost/core/noncopyable.hpp>
#include <boost/python.hpp>
#include <cstddef>

#include "series_file.h"
#include "smr_file.h"

using namespace boost::python;

BOOST_PYTHON_MODULE(meas_extractor) {
  Py_Initialize();
  np::initialize();

  class_<SeriesFile, boost::noncopyable>("SeriesFile", init<const std::string &>())
      .add_property("frame_size", &SeriesFile::get_frame_size)
      .add_property("frame_count", &SeriesFile::get_frame_count)
      .def("fetch_data_u16", &SeriesFile::fetch_data<uint16_t, float>)
      .def("fetch_data_u32", &SeriesFile::fetch_data<uint32_t, double>)
      .def("clear", &SeriesFile::clear);

  class_<SMRFile, boost::noncopyable>("SMRFile", init<const std::string &>())
      .add_property("start_time", &SMRFile::get_start_time)
      .add_property("end_time", &SMRFile::get_end_time);
}
