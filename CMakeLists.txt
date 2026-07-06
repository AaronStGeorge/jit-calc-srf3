cmake_minimum_required(VERSION 3.20)

# CXX compiler capable of compiling to HSACO
set(CMAKE_CXX_COMPILER amdclang++)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

project(jit-calc-srf3 CXX)

find_package(hip REQUIRED)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

include(build_tools/cmake/HsacoCatalog.cmake)

add_hsaco_kernel(kernels/vector_add.hip.cpp)

set(catalog_cpp "${CMAKE_CURRENT_BINARY_DIR}/generated/catalog.cpp")
build_hsaco_catalog("${catalog_cpp}")

add_executable(jit-calc-srf3 main.cpp "${catalog_cpp}")
target_include_directories(jit-calc-srf3 PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(jit-calc-srf3 PRIVATE hip::host)
