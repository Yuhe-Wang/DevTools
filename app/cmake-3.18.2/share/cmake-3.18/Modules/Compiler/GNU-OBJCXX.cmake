include(Compiler/GNU)
__compiler_gnu(OBJCXX)

if(NOT CMAKE_OBJCXX_COMPILER_VERSION VERSION_LESS 4.2)
  set(CMAKE_OBJCXX_COMPILE_OPTIONS_VISIBILITY_INLINES_HIDDEN "-fvisibility-inlines-hidden")
endif()

if(NOT CMAKE_OBJCXX_LINK_FLAGS)
  set(CMAKE_OBCXX_LINK_FLAGS "-lstdc++")
endif()
