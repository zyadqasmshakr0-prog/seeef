import os
from os.path import join
from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.util import current_directory


class Pygame2Recipe(CompiledComponentsPythonRecipe):
    version = '2.1.3'
    url = 'https://github.com/pygame/pygame/releases/download/{version}/pygame-{version}.tar.gz'

    site_packages_name = 'pygame'
    name = 'pygame'

    depends = ['sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'setuptools', 'jpeg', 'png']
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        with current_directory(build_dir):
            # 1. إعداد ملف Setup الخاص بـ Pygame للأندرويد (كما في الوصفة الرسمية تماماً)
            with open(join("buildconfig", "Setup.Android.SDL2.in"), "r") as setup_template:
                setup_file_content = setup_template.read()

            env = self.get_recipe_env(arch)
            android_sdl = env['ANDROID_SDL']
            android_mixer = env['ANDROID_MIXER']
            android_font = env['ANDROID_FONT']
            android_image = env['ANDROID_IMAGE']

            with open("Setup", "w") as setup_file:
                setup_file.write(
                    setup_file_content.format(
                        sdl_includes= (
                            " -I" + android_sdl +
                            " -I" + join(android_mixer) +
                            " -I" + join(android_mixer, "include") +
                            " -I" + android_font +
                            " -I" + android_image +
                            " -I" + env['PNG_INCLUDES'] +
                            " -I" + env['JPEG_INCLUDES']
                        ),
                        sdl_libs=(
                            " -L" + env['PYGAME_EXTRA_BASE'] +
                            " -L" + env['PNG_LIBS'] +
                            " -L" + env['JPEG_LIBS']
                        )
                    )
                )

            # 2. إصلاح مشكلة longintrepr.h في Python 3.11 داخل كود Pygame المصدري مباشرة قبل التجميع
            for root_dir, _, files in os.walk(build_dir):
                for fname in files:
                    if fname.endswith((".c", ".h", ".pyx", ".pxd")):
                        fpath = join(root_dir, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            if "longintrepr.h" in content and "cpython/longintrepr.h" not in content:
                                content = content.replace('#include "longintrepr.h"', '#include "cpython/longintrepr.h"')
                                content = content.replace('#include <longintrepr.h>', '#include <cpython/longintrepr.h>')
                                with open(fpath, "w", encoding="utf-8") as f:
                                    f.write(content)
                        except Exception:
                            pass

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['USE_SDL'] = '2'
        env["PYGAME_EXTRA_BASE"] = join(self.ctx.bootstrap.build_dir, "libs", str(arch))
        env["ANDROID_SDL"] = join(self.ctx.bootstrap.build_dir, "jni", "SDL", "include")
        env["ANDROID_MIXER"] = join(self.ctx.bootstrap.build_dir, "jni", "SDL2_mixer")
        env["ANDROID_FONT"] = join(self.ctx.bootstrap.build_dir, "jni", "SDL2_ttf")
        env["ANDROID_IMAGE"] = join(self.ctx.bootstrap.build_dir, "jni", "SDL2_image")

        png = self.get_recipe('png', self.ctx)
        png_lib_dir = join(png.get_build_dir(arch.arch), '.libs')
        png_inc_dir = png.get_build_dir(arch)
        env['PNG_LIBS'] = png_lib_dir
        env['PNG_INCLUDES'] = png_inc_dir

        jpeg = self.get_recipe('jpeg', self.ctx)
        jpeg_inc_dir = jpeg_lib_dir = jpeg.get_build_dir(arch.arch)
        env['JPEG_LIBS'] = jpeg_lib_dir
        env['JPEG_INCLUDES'] = jpeg_inc_dir

        # تمرير مسارات cpython ورايات Clang حصرياً أثناء بناء Pygame لمنع فشل المترجم
        py_inc_cpython = join(self.ctx.get_python_install_dir(arch.arch), "include", "python3.11", "cpython")
        host_py_inc_cpython = join(self.get_recipe("hostpython3", self.ctx).get_build_dir(arch.arch), "Include", "cpython")
        target_py_inc_cpython = join(self.get_recipe("python3", self.ctx).get_build_dir(arch.arch), "Include", "cpython")

        extra_cflags = (
            f" -I{py_inc_cpython} -I{host_py_inc_cpython} -I{target_py_inc_cpython}"
            " -Wno-error=incompatible-function-pointer-types"
            " -Wno-error=implicit-function-declaration"
            " -Wno-error=int-conversion"
            " -Wno-incompatible-pointer-types"
        )
        env['CFLAGS'] = env.get('CFLAGS', '') + extra_cflags
        env['CPPFLAGS'] = env.get('CPPFLAGS', '') + extra_cflags
        return env


recipe = Pygame2Recipe()