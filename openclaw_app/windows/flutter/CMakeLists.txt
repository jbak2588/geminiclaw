# This file controls Flutter-level build steps. It should not be edited.
cmake_minimum_required(VERSION 3.14)

set(EPHEMERAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/ephemeral")

# Configuration provided via flutter tool.
include(${EPHEMERAL_DIR}/generated_config.cmake)

# TODO: Move the rest of this into files in ephemeral. See
# https://github.com/flutter/flutter/issues/57146.
set(WRAPPER_ROOT "${EPHEMERAL_DIR}/cpp_client_wrapper")
set(FLUTTER_WRAPPER_ARTIFACT_DIR
  "${FLUTTER_ROOT}/bin/cache/artifacts/engine/windows-x64/cpp_client_wrapper")

# Set fallback configurations for older versions of the flutter tool.
if (NOT DEFINED FLUTTER_TARGET_PLATFORM)
  set(FLUTTER_TARGET_PLATFORM "windows-x64")
endif()

# === Flutter Library ===
set(FLUTTER_LIBRARY "${EPHEMERAL_DIR}/flutter_windows.dll")

# Published to parent scope for install step.
set(FLUTTER_LIBRARY ${FLUTTER_LIBRARY} PARENT_SCOPE)
set(FLUTTER_ICU_DATA_FILE "${EPHEMERAL_DIR}/icudtl.dat" PARENT_SCOPE)
set(PROJECT_BUILD_DIR "${PROJECT_DIR}/build/" PARENT_SCOPE)
set(AOT_LIBRARY "${PROJECT_DIR}/build/windows/app.so" PARENT_SCOPE)

list(APPEND FLUTTER_LIBRARY_HEADERS
  "flutter_export.h"
  "flutter_windows.h"
  "flutter_messenger.h"
  "flutter_plugin_registrar.h"
  "flutter_texture_registrar.h"
)
list(TRANSFORM FLUTTER_LIBRARY_HEADERS PREPEND "${EPHEMERAL_DIR}/")
add_library(flutter INTERFACE)
target_include_directories(flutter INTERFACE
  "${EPHEMERAL_DIR}"
)
target_link_libraries(flutter INTERFACE "${FLUTTER_LIBRARY}.lib")
add_dependencies(flutter flutter_assemble)

# === Wrapper ===
list(APPEND CPP_WRAPPER_SOURCES_CORE
  "core_implementations.cc"
  "standard_codec.cc"
)
list(TRANSFORM CPP_WRAPPER_SOURCES_CORE PREPEND "${WRAPPER_ROOT}/")
list(APPEND CPP_WRAPPER_SOURCES_PLUGIN
  "plugin_registrar.cc"
)
list(TRANSFORM CPP_WRAPPER_SOURCES_PLUGIN PREPEND "${WRAPPER_ROOT}/")
list(APPEND CPP_WRAPPER_SOURCES_APP
  "flutter_engine.cc"
  "flutter_view_controller.cc"
)
list(TRANSFORM CPP_WRAPPER_SOURCES_APP PREPEND "${WRAPPER_ROOT}/")

# Wrapper sources needed for a plugin.
add_library(flutter_wrapper_plugin STATIC
  ${CPP_WRAPPER_SOURCES_CORE}
  ${CPP_WRAPPER_SOURCES_PLUGIN}
)
apply_standard_settings(flutter_wrapper_plugin)
target_compile_options(flutter_wrapper_plugin PRIVATE /FS)
set_target_properties(flutter_wrapper_plugin PROPERTIES
  POSITION_INDEPENDENT_CODE ON)
set_target_properties(flutter_wrapper_plugin PROPERTIES
  CXX_VISIBILITY_PRESET hidden)
target_link_libraries(flutter_wrapper_plugin PUBLIC flutter)
target_include_directories(flutter_wrapper_plugin PUBLIC
  "${WRAPPER_ROOT}/include"
)
add_dependencies(flutter_wrapper_plugin flutter_wrapper_sync)

# Wrapper sources needed for the runner.
add_library(flutter_wrapper_app STATIC
  ${CPP_WRAPPER_SOURCES_CORE}
  ${CPP_WRAPPER_SOURCES_APP}
)
apply_standard_settings(flutter_wrapper_app)
target_compile_options(flutter_wrapper_app PRIVATE /FS)
target_link_libraries(flutter_wrapper_app PUBLIC flutter)
target_include_directories(flutter_wrapper_app PUBLIC
  "${WRAPPER_ROOT}/include"
)
add_dependencies(flutter_wrapper_app flutter_wrapper_sync)

# === Flutter tool backend ===
# _phony_ is a non-existent file to force this command to run every time,
# since currently there's no way to get a full input/output list from the
# flutter tool.
set(PHONY_OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/_phony_")
set_source_files_properties("${PHONY_OUTPUT}" PROPERTIES SYMBOLIC TRUE)
add_custom_command(
  OUTPUT ${FLUTTER_LIBRARY} ${FLUTTER_LIBRARY_HEADERS}
    ${CPP_WRAPPER_SOURCES_CORE} ${CPP_WRAPPER_SOURCES_PLUGIN}
    ${CPP_WRAPPER_SOURCES_APP}
    ${PHONY_OUTPUT}
  COMMAND ${CMAKE_COMMAND} -E env
    ${FLUTTER_TOOL_ENVIRONMENT}
    "${FLUTTER_ROOT}/packages/flutter_tools/bin/tool_backend.bat"
      ${FLUTTER_TARGET_PLATFORM} $<CONFIG>
  VERBATIM
)
add_custom_target(flutter_assemble DEPENDS
  "${FLUTTER_LIBRARY}"
  ${FLUTTER_LIBRARY_HEADERS}
  ${CPP_WRAPPER_SOURCES_CORE}
  ${CPP_WRAPPER_SOURCES_PLUGIN}
  ${CPP_WRAPPER_SOURCES_APP}
)

# Some local replacement states leave the wrapper headers in place but drop the
# generated .cc sources. Re-sync the full wrapper bundle from the installed
# Flutter SDK after flutter_assemble so `flutter run` and desktop tests can
# compile consistently against the expected ephemeral paths.
add_custom_target(flutter_wrapper_sync
  COMMAND ${CMAKE_COMMAND} -E make_directory "${WRAPPER_ROOT}"
  COMMAND ${CMAKE_COMMAND} -E copy_directory
    "${FLUTTER_WRAPPER_ARTIFACT_DIR}"
    "${WRAPPER_ROOT}"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${FLUTTER_ROOT}/bin/cache/artifacts/engine/windows-x64/flutter_export.h"
    "${EPHEMERAL_DIR}/flutter_export.h"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${FLUTTER_ROOT}/bin/cache/artifacts/engine/windows-x64/flutter_windows.h"
    "${EPHEMERAL_DIR}/flutter_windows.h"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${FLUTTER_ROOT}/bin/cache/artifacts/engine/windows-x64/flutter_messenger.h"
    "${EPHEMERAL_DIR}/flutter_messenger.h"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${FLUTTER_ROOT}/bin/cache/artifacts/engine/windows-x64/flutter_plugin_registrar.h"
    "${EPHEMERAL_DIR}/flutter_plugin_registrar.h"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${FLUTTER_ROOT}/bin/cache/artifacts/engine/windows-x64/flutter_texture_registrar.h"
    "${EPHEMERAL_DIR}/flutter_texture_registrar.h"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${FLUTTER_ROOT}/bin/cache/artifacts/engine/windows-x64/flutter_windows.dll"
    "${EPHEMERAL_DIR}/flutter_windows.dll"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${FLUTTER_ROOT}/bin/cache/artifacts/engine/windows-x64/flutter_windows.dll.lib"
    "${EPHEMERAL_DIR}/flutter_windows.dll.lib"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${FLUTTER_ROOT}/bin/cache/artifacts/engine/windows-x64/icudtl.dat"
    "${EPHEMERAL_DIR}/icudtl.dat"
  VERBATIM
)
add_dependencies(flutter_wrapper_sync flutter_assemble)
