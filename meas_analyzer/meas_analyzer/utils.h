#ifndef __UTILS_H_
#define __UTILS_H_

#include <cstdint>
#include <typeinfo>

#define __STRINGIFY__(v) #v
#define STRINGIFY(v) __STRINGIFY__(v)

#define __CONCAT__(x, y) x##y
#define CONCAT(x, y) __CONCAT__(x, y)
#define __CONCAT__3(x, y, z) x##y##z
#define CONCAT3(x, y, z) __CONCAT__3(x, y, z)

#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)

// TODO: something with flatten
// TODO: something with pure
#ifdef __clang__

#define INLINE_WRAPPER inline __attribute__((always_inline, artificial))
#define RARE_FUNC __attribute__((minsize, cold))
#define FREQUENT_FUNC __attribute__((hot))

#elif __GNUC__

#define INLINE_WRAPPER inline __attribute__((always_inline, artificial))
#define RARE_FUNC __attribute__((optimize("-Os"), cold))
#define FREQUENT_FUNC __attribute__((optimize("-Ofast"), hot))

#else

#define INLINE_WRAPPER inline __attribute__((always_inline, artificial))
#define RARE_FUNC __attribute__((optimize("-Os"), minsize, cold))
#define FREQUENT_FUNC __attribute__((optimize("-Ofast"), hot))

#endif

typedef uint8_t byte;

template <class T1, class T2> constexpr auto same_type() {
  return typeid(T1).hash_code() == typeid(T2).hash_code();
}

/**********  LOGGING  ************/
#include <ctime>
#include <errno.h>
#include <iomanip>
#include <iostream>
#include <sys/time.h>
#include <type_traits>

enum class LogLevel {
  NOTSET = 0,
  DEBUG = 1,
  INFO = 2,
  WARNING = 3,
  WARN = WARNING,
  ERROR = 4,
  CRITICAL = 5,
  FATAL = CRITICAL,
};

#define BASH_ESC_CHAR "\x1b"
#define BASH_SET_COLOR(a, b) BASH_ESC_CHAR "[" #a ";" #b "m"
#define BASH_CLEAR_COLOR BASH_ESC_CHAR "[0m"

RARE_FUNC
auto log_level_to_colored_name(LogLevel l) {
  switch (l) {
  case LogLevel::NOTSET:
    return "?";
  case LogLevel::DEBUG:
    return BASH_SET_COLOR(1, 90) "dbg" BASH_CLEAR_COLOR;
  case LogLevel::INFO:
    return BASH_SET_COLOR(1, 34) "info" BASH_CLEAR_COLOR;
  case LogLevel::WARNING:
    return BASH_SET_COLOR(1, 93) "warn" BASH_CLEAR_COLOR;
  case LogLevel::ERROR:
    return BASH_SET_COLOR(1, 31) "err" BASH_CLEAR_COLOR;
  case LogLevel::CRITICAL:
    return BASH_SET_COLOR(1, 91) "critical" BASH_CLEAR_COLOR;
  default:
    return "";
  }
}

class NopStream {
public:
  template <class T> inline auto &operator<<(T v) const { return *this; }
};
const auto NOP_STREAM = NopStream();

template <bool visible>
RARE_FUNC auto &start_log_line_stream(LogLevel level,
                                      const char *channel_name) {
  if constexpr (visible) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm *lt = localtime(&tv.tv_sec);
    char tm_s[24];
    strftime(tm_s, sizeof(tm_s), "%F %X", lt);
    return std::cerr << tm_s << "." << std::setfill('0') << std::setw(3)
                     << tv.tv_usec / 1000 << " "
                     << log_level_to_colored_name(level) << " " << channel_name
                     << ":: ";
  } else {
    return NOP_STREAM;
  }
}

#ifndef LOG_LEVEL
#define LOG_LEVEL DEBUG
#endif /* LOG_LEVEL */

#define DBG_ENDL "\n"
#define DBG_STREAM(channel) std::cerr << #channel << " :: "

#define LOG_ENDL "\n"
#define LOG(level, channel)                                                    \
  start_log_line_stream<LogLevel::level >= LogLevel::LOG_LEVEL &&              \
                        LogLevel::level >= CHANNEL_LOG_LEVEL_##channel>(       \
      LogLevel::level, #channel)

#define DBG(channel) LOG(DEBUG, channel)
#define INFO(channel) LOG(INFO, channel)
#define WARN(channel) LOG(WARNING, channel)
#define ERR(channel) LOG(ERROR, channel)
#define CRIT(channel) LOG(CRITICAL, channel)

/**********  ASSERT  ***********/
#include <string.h>
#include <string>

namespace std {
string to_string(const char *s) { // !!!!!!!!!!!! cc
  return s;
}
string to_string(const std::string &s) { // !!!!!!!!!!!! cc
  return s;
}
} // namespace std
template <const char *sep> RARE_FUNC std::string __dbg_args_to_string__() {
  return "";
}
template <const char *sep, class Tfirst, class... Targs>
RARE_FUNC std::string __dbg_args_to_string__(Tfirst &first_arg,
                                             Targs &...args) {
  return std::to_string(first_arg) + sep + __dbg_args_to_string__<sep>(args...);
}
const char __colon_sep__[] = ":";
const char __space_sep__[] = " ";

#define THROW(exc_cls, ...)                                                    \
  {                                                                            \
    auto line_num = __LINE__;                                                  \
    auto loc_str = __dbg_args_to_string__<__colon_sep__>(                      \
        __FILE__, __FUNCTION__, line_num);                                     \
    auto args_str = __dbg_args_to_string__<__space_sep__>(__VA_ARGS__);        \
    throw exc_cls(__dbg_args_to_string__<__space_sep__>(loc_str, args_str));   \
  }
#define ASSERT(cond, ...)                                                      \
  {                                                                            \
    if (unlikely(!(cond))) {                                                   \
      auto line_num = __LINE__;                                                \
      auto loc_str = __dbg_args_to_string__<__colon_sep__>(                    \
          __FILE__, __FUNCTION__, line_num);                                   \
      auto args_str = __dbg_args_to_string__<__space_sep__>(__VA_ARGS__);      \
      throw std::runtime_error(__dbg_args_to_string__<__space_sep__>(          \
          loc_str, "Assert", "`" #cond "`", "failed:", args_str));             \
    }                                                                          \
  }
#define ASSERT_SYS_BOOL(cond, ...)                                             \
  {                                                                            \
    bool err_cond = (cond);                                                    \
    if (unlikely(!(err_cond))) {                                               \
      auto line_num = __LINE__;                                                \
      auto loc_str = __dbg_args_to_string__<__colon_sep__>(                    \
          __FILE__, __FUNCTION__, line_num);                                   \
      auto args_str = __dbg_args_to_string__<__space_sep__>(__VA_ARGS__);      \
      std::string errno_str = strerror(errno);                                 \
      throw std::runtime_error(__dbg_args_to_string__<__space_sep__>(          \
          loc_str, "Assert", "`" #cond "`", "failed(", errno_str,              \
          "):", args_str));                                                    \
    }                                                                          \
  }
#define ASSERT_SYS(cond, ...) ASSERT_SYS_BOOL((cond) != -1, __VA_ARGS__)
#define ASSERT_EXC(cond, exc, ...)                                             \
  {                                                                            \
    if (unlikely(!(cond))) {                                                   \
      throw exc(__dbg_args_to_string__<__space_sep__>(__VA_ARGS__));           \
    }                                                                          \
  }
#define ASSERT_EXC_VOID(cond, exc)                                             \
  {                                                                            \
    if (unlikely(!(cond))) {                                                   \
      throw exc();                                                             \
    }                                                                          \
  }

#ifdef DEBUG
#define ASSERT_DBG(...) ASSERT(__VA_ARGS__)
#else /* DEBUG */
#define ASSERT_DBG(...)                                                        \
  {}
#endif /* DEBUG */

/****************** PYTHON UTILS ************************/
#if defined USE_PYTHON || defined PYTHON_DWA2002810_HPP
#undef USE_PYTHON
#define USE_PYTHON

#include <boost/python.hpp>

class ReleaseGIL {
  PyThreadState *save_state;

public:
  inline ReleaseGIL() { save_state = PyEval_SaveThread(); }

  inline ~ReleaseGIL() { PyEval_RestoreThread(save_state); }
};

#define NOGIL_SCOPE ReleaseGIL unlockGIL;

#else /* defined USE_PYTHON || defined PYTHON_DWA2002810_HPP */

#define NOGIL_SCOPE

#endif /* defined USE_PYTHON || defined PYTHON_DWA2002810_HPP */

#endif /* __UTILS_H_ */