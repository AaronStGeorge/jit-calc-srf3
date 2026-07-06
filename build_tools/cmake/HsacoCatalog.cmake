# Embedded HSACO catalog build helpers.
#
#   add_hsaco_kernel(<source>)      compile a .hip/.asm/etc kernel source to .hsaco
#                                   (via hsaco.py) and register it in the catalog.
#   build_hsaco_catalog(<out.cpp>)  emit the generated catalog .cpp embedding every
#                                   registered kernel (via embed_catalog.py).

# This module lives in build_tools/cmake/; the hsaco.py / embed_catalog.py scripts
# it drives live one level up in build_tools/.
get_filename_component(HSACO_BUILD_TOOLS_DIR "${CMAKE_CURRENT_LIST_DIR}" DIRECTORY)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

function(add_hsaco_kernel source)
    get_filename_component(source_abs "${source}" ABSOLUTE)
    get_filename_component(name "${source}" NAME)
    string(REGEX REPLACE "\\.(hip\\.cpp|hip|cpp|cc|asm|s)$" "" name "${name}")

    set(hsaco "${CMAKE_CURRENT_BINARY_DIR}/hsaco_files/${name}.hsaco")
    get_filename_component(hsaco_dir "${hsaco}" DIRECTORY)
    add_custom_command(
        OUTPUT "${hsaco}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${hsaco_dir}"
        COMMAND "${Python3_EXECUTABLE}" "${HSACO_BUILD_TOOLS_DIR}/hsaco.py"
                "${source_abs}" -o "${hsaco}"
        DEPENDS "${source_abs}" "${HSACO_BUILD_TOOLS_DIR}/hsaco.py"
        VERBATIM
    )

    set_property(GLOBAL APPEND PROPERTY HSACO_CATALOG_PAIRS "${name}=${hsaco}")
    set_property(GLOBAL APPEND PROPERTY HSACO_CATALOG_DEPS "${hsaco}")
endfunction()

function(build_hsaco_catalog output)
    get_property(pairs GLOBAL PROPERTY HSACO_CATALOG_PAIRS)
    get_property(deps GLOBAL PROPERTY HSACO_CATALOG_DEPS)
    get_filename_component(output_dir "${output}" DIRECTORY)
    add_custom_command(
        OUTPUT "${output}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${output_dir}"
        COMMAND "${Python3_EXECUTABLE}" "${HSACO_BUILD_TOOLS_DIR}/embed_catalog.py"
                -o "${output}" ${pairs}
        DEPENDS "${HSACO_BUILD_TOOLS_DIR}/embed_catalog.py" ${deps}
        VERBATIM
    )
endfunction()
