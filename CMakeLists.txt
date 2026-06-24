cmake_minimum_required(VERSION 3.10.0)
set(PROJECT_NAME game)
project(${PROJECT_NAME})

option(BUILD_DYNAMIC_LIB "Build Dynamic library" ON)
option(BUILD_EXAMPLES "Build Examples" ON)
option(BUILD_D3D11 "Build D3D11 library" ON)
option(BUILD_D3D12 "Build D3D12 library" ON)
option(BUILD_VULKAN "Build Vulkan library" ON)
option(BUILD_RAYTRACING "Build With RayTracing library" ON)
option(BUILD_HLSLC "Build HLSL Compiler" ON)

set(TIGFX_PUBLISH_DIR ${PROJECT_SOURCE_DIR}/publish)
set(SOURCE_DIR ${PROJECT_SOURCE_DIR}/source)
set(BUILD_OUTPUT_DIR ${PROJECT_SOURCE_DIR}/build)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

file(MAKE_DIRECTORY ${TIGFX_PUBLISH_DIR})
file(MAKE_DIRECTORY ${SOURCE_DIR})
file(MAKE_DIRECTORY ${BUILD_OUTPUT_DIR})
file(MAKE_DIRECTORY ${PROJECT_SOURCE_DIR}/3rd)

if(CMAKE_BUILD_TYPE)
set(BUILD_CONFIGURATION ${CMAKE_BUILD_TYPE})
elseif(CMAKE_CONFIGURATION_TYPES)
set(BUILD_CONFIGURATION ${CMAKE_CONFIGURATION_TYPES})
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
message("Windows")
set(IsWindows true)
set(IsLinux false)
set(IsUnix false)
elseif(CMAKE_SYSTEM_NAME MATCHES "Linux")
message("Linux")
set(IsWindows false)
set(IsLinux true)
set(IsUnix false)
else()
message("Unsupported Platform")
set(IsWindows false)
set(IsLinux false)
set(IsUnix false)
endif()

set(ARCH_SUFFIX .x64)
if(BUILD_CONFIGURATION MATCHES "Debug")
    add_definitions(
        -DDEBUG=1 )
    set(CONFIG_SUFFIX .d)
elseif(BUILD_CONFIGURATION MATCHES "Release")
    add_definitions(
        -DRELEASE=1)
    set(CONFIG_SUFFIX )
endif()

if(BUILD_RAYTRACING)
    add_definitions(
        -DTI_GFX_ENABLE_RAYTRACING=1
    )
endif()

#add_compile_options(-fsanitize=address)
if(${BUILD_DYNAMIC_LIB} MATCHES "ON")
set(BUILD_DYNAMIC_MACRO -DTI_GFX_USE_DYNAMIC_API=1 -DTI_GFX_BUILD_DYNAMIC_API=1)
endif()

if(IsWindows)
    add_definitions(
        -DPLT_PLATFORM_WINDOWS=1
        -D_CRT_SECURE_NO_WARNINGS
        -D_CRT_NONSTDC_NO_WARNINGS
        -DNOMINMAX=1
        ${BUILD_DYNAMIC_MACRO}
    )
    add_compile_options(/wd4819)
    set(EXECUTABLE_SUFFIX ".exe")
    set(STATIC_SUFFIX ".lib")
    set(DYNAMIC_SUFFIX ".dll")
    #add_compile_options(/ignore:4099)
else(IsLinux)
    add_definitions(
        -DPLT_PLATFORM_LINUX=1
        -DNOMINMAX=1
        ${BUILD_DYNAMIC_MACRO}
    )
    set(EXECUTABLE_SUFFIX "")
    set(STATIC_SUFFIX ".lib")
    set(DYNAMIC_SUFFIX ".a")
endif()

set(STATIC_PUBLISH_SUFFIX ${ARCH_SUFFIX}${CONFIG_SUFFIX}${STATIC_SUFFIX})
set(DYNAMIC_PUBLISH_SUFFIX ${ARCH_SUFFIX}${CONFIG_SUFFIX}${DYNAMIC_SUFFIX})

set(CMAKE_STATIC_LIBRARY_SUFFIX ${STATIC_PUBLISH_SUFFIX})
set(CMAKE_SHARED_LIBRARY_SUFFIX ${DYNAMIC_PUBLISH_SUFFIX})
set(CMAKE_IMPORT_LIBRARY_SUFFIX ${STATIC_PUBLISH_SUFFIX})

add_custom_target(Build_3rd
    COMMAND echo --Build tinyGFX
    COMMAND ${CMAKE_COMMAND} --build ${PROJECT_SOURCE_DIR}/3rd/tinyGFX/build --config $<CONFIG>
    COMMAND echo --Build mimalloc
    COMMAND ${CMAKE_COMMAND} --build ${PROJECT_SOURCE_DIR}/3rd/mimalloc/build --config $<CONFIG>
    COMMAND echo --Build recastnavigation
    COMMAND ${CMAKE_COMMAND} --build ${PROJECT_SOURCE_DIR}/3rd/recastnavigation/build --config $<CONFIG>
)

set(THIRD_PARTY_DIR ${PROJECT_SOURCE_DIR}/3rd)
set(GAME_SOURCE_DIR ${PROJECT_SOURCE_DIR}/source)
file(GLOB_RECURSE GAME_SOURCE_SRC ${GAME_SOURCE_DIR}/*.cpp)

file(GLOB_RECURSE UI_SRC
${THIRD_PARTY_DIR}/nuklear/src/*.c
)
file(GLOB_RECURSE CJSON_SRC
${THIRD_PARTY_DIR}/cJSON/cJSON.c
)
file(GLOB_RECURSE LUA_SRC ${THIRD_PARTY_DIR}/lua/lua-5.5.0/src/*.c)
list(FILTER LUA_SRC EXCLUDE REGEX "lua\.c$")
list(FILTER LUA_SRC EXCLUDE REGEX "luac\.c$")

add_executable(${PROJECT_NAME} 
    ${GAME_SOURCE_SRC} 
    ${CJSON_SRC} 
    ${LUA_SRC}
    ${UI_SRC})

target_include_directories(
    ${PROJECT_NAME}
    PRIVATE
    ${GAME_SOURCE_DIR}/
)
target_compile_definitions(
    ${PROJECT_NAME}
    PRIVATE
    #Nuklear
    -DNK_INCLUDE_VERTEX_BUFFER_OUTPUT=1
    -DNK_UINT_DRAW_INDEX=1
    -DNK_INCLUDE_DEFAULT_ALLOCATOR=1
    -DNK_INCLUDE_FONT_BAKING=1
    -DNK_INCLUDE_DEFAULT_FONT=1
    #stbi
    -DTINYGLTF_NO_STB_IMAGE_WRITE=1
)
target_link_directories(
    ${PROJECT_NAME}
    PRIVATE
    ${THIRD_PARTY_DIR}/tinyGFX/publish
    ${THIRD_PARTY_DIR}/mimalloc/build/${BUILD_CONFIGURATION}
    ${THIRD_PARTY_DIR}/recastnavigation/build/Recast/${BUILD_CONFIGURATION}
    ${THIRD_PARTY_DIR}/recastnavigation/build/Detour/${BUILD_CONFIGURATION}
)

target_link_libraries(
    ${PROJECT_NAME}
    PRIVATE
    tinyGFX.hlslc.x64.d
    mimalloc-static
    Recast-d
    Detour-d
    shlwapi.lib
)

add_custom_command(
    TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy "$<TARGET_FILE:game>" ${TIGFX_PUBLISH_DIR}/${PROJECT_NAME}${EXECUTABLE_SUFFIX}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${THIRD_PARTY_DIR}/tinyGFX/publish ${TIGFX_PUBLISH_DIR}/
)