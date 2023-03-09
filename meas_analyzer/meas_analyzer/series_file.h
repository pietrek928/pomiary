#ifndef __SERIES_FILE_H_
#define __SERIES_FILE_H_

#include <cstddef>
#include <cstdint>
#include <stdexcept>

#include <boost/python/numpy.hpp>

#include "meas_file.h"

namespace p = boost::python;
namespace np = boost::python::numpy;

class SeriesFile: public MeasFile {
  struct start_hdr {
    uint16_t flags;
    uint16_t frame_len;
  };

public:
  using MeasFile::MeasFile;

  std::size_t get_frame_size() {
    ensure_size(sizeof(start_hdr));
    return ((struct start_hdr *)get_data())->frame_len;
  }

  std::size_t get_frame_count() {
    auto frame_size = get_frame_size();
    ASSERT_DBG((size % frame_size) > 0, "File size undividable by frame size",
               size, frame_size);
    return get_size() / frame_size;
  }

  template <class Tread, class Tout>
  auto fetch_data(std::size_t start_frame, std::size_t frame_count,
                  std::size_t off_start, int items_count, Tout scale) {
    auto file_frame_count = get_frame_count();
    auto end_frame = start_frame + frame_count;
    if (end_frame > file_frame_count) {
      end_frame = file_frame_count;
      frame_count = end_frame - start_frame;
    }

    auto frame_size = get_frame_size();
    if (off_start + sizeof(Tread) * items_count > frame_size) {
      items_count = (frame_size - off_start) / sizeof(Tread);
      if (items_count < 0) {
        items_count = 0;
      }
    }

    auto shape = p::make_tuple(frame_count, items_count);
    auto dtype = np::dtype::get_builtin<Tout>();
    auto out_buffer = np::zeros(shape, dtype);

    if (!items_count || !frame_count) {
      return out_buffer;
    }

    auto out = (Tout *)out_buffer.get_data();

    auto cur_pos =
        ((uint8_t *)get_data()) + start_frame * frame_size + off_start;
    auto end_pos = cur_pos + (frame_count * frame_size);

    do {
      auto read_pos = (Tread *)cur_pos;
      for (int i = 0; i < items_count; i++) {
        *(out++) = scale * read_pos[i];
      }
      cur_pos += frame_size;
    } while (cur_pos < end_pos);

    return out_buffer;
  }
};

#endif /* __SERIES_FILE_H_ */
