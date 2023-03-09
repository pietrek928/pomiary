#ifndef __SMR_FILE_H_
#define __SMR_FILE_H_

#include <string>

#include "meas_file.h"

class SMRFile : public MeasFile {
public:
  using MeasFile::MeasFile;

  std::string get_start_time() {
    ensure_size(25);
    return std::string(((char *)get_data()) + 2, 23);
  }

  std::string get_end_time() {
    ensure_size(48);
    return std::string(((char *)get_data()) + 25, 23);
  }
};

#endif /* __SMR_FILE_H_ */
