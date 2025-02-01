# Additional clean files
cmake_minimum_required(VERSION 3.16)

if("${CONFIG}" STREQUAL "" OR "${CONFIG}" STREQUAL "Debug")
  file(REMOVE_RECURSE
  "CMakeFiles\\planewar_autogen.dir\\AutogenUsed.txt"
  "CMakeFiles\\planewar_autogen.dir\\ParseCache.txt"
  "planewar_autogen"
  )
endif()
