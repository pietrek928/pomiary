#ifndef __MEAS_FILE_H_
#define __MEAS_FILE_H_

#include <cstddef>
#include <cstdint>
#include <stdexcept>

#include <fcntl.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>

#include "utils.h"

class MeasFile {
  int fd = -1;
  std::size_t size = 0;
  void *addr = NULL;

  static constexpr int block_size = 4096;

public:
  MeasFile() {}

  MeasFile(const std::string &fname) {
    try {
      fd = open(fname.c_str(), O_RDONLY, 0666);
      ASSERT_SYS(fd, "open failed:", fname);
      size = read_size();
      addr = mmap64(NULL, size, PROT_READ, MAP_SHARED, fd, 0);
      ASSERT_SYS_BOOL(addr != MAP_FAILED, "mmap of", size, "bytes failed");
    } catch (...) {
      clear();
      throw;
    }
  }

  ~MeasFile() { clear(); }

  auto &operator=(MeasFile &&m) {
    std::swap(fd, m.fd);
    std::swap(size, m.size);
    std::swap(addr, m.addr);

    m.clear();
    return *this;
  }

  inline auto get_data() const { return addr; }

  auto get_size() const { return size; }

  std::size_t read_size() {
    auto current_size = lseek(fd, 0L, SEEK_END);
    ASSERT_SYS(current_size, "lseek failed")
    ASSERT_SYS(lseek(fd, 0L, SEEK_SET), "lseek failed")
    return current_size;
  }

  void ensure_size(std::size_t min_size) {
    ASSERT(size >= min_size, "File size must be larger than", min_size);
  }

  void clear() {
    if (size && addr) {
      munmap(addr, size);
      size = 0;
      addr = NULL;
    }
    if (fd != -1) {
      close(fd);
      fd = -1;
    }
  }
};

#endif /* __MEAS_FILE_H_ */
