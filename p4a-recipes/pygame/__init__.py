from os.path import join
from pythonforandroid.recipe import CompiledComponentsPythonRecipe


class Pygame2Recipe(CompiledComponentsPythonRecipe):
    """
    Custom local recipe for Pygame 2.1.3 compatible with Python 3.11 and NDK r25b Clang
    """
    version = '2.1.3'
    url = 'https://github.com/pygame/pygame/releases/download/{version}/pygame-{version}.tar.gz'

    site_packages_name = 'pygame'
    name = 'pygame'

    depends = ['sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'setuptools', 'jpeg', 'png']
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with self.ctx.cd(self.get_build_dir(arch.arch)):
            with open('Setup.Android.SDL2', 'w') as setup_file:
                setup_file.write("""#--StartConfig
SDL = -I{sdl_includes} -L{sdl_libs} -lSDL2
FONT = -lSDL2_ttf
IMAGE = -lSDL2_image
MIXER = -lSDL2_mixer
PNG = -lpng16
JPEG = -ljpeg
FREETYPE = -lfreetype
#--EndConfig
_sdl2.sdl2 src_c/_sdl2/sdl2.c $(SDL) $(DEBUG)
_sdl2.audio src_c/_sdl2/audio.c $(SDL) $(DEBUG)
_sdl2.video src_c/_sdl2/video.c $(SDL) $(DEBUG)
_sdl2.mixer src_c/_sdl2/mixer.c $(SDL) $(MIXER) $(DEBUG)
_sdl2.controller src_c/_sdl2/controller.c $(SDL) $(DEBUG)
_sdl2.touch src_c/_sdl2/touch.c $(SDL) $(DEBUG)
imageext src_c/imageext.c $(SDL) $(IMAGE) $(PNG) $(JPEG) $(DEBUG)
font src_c/font.c $(SDL) $(FONT) $(DEBUG)
mixer src_c/mixer.c $(SDL) $(MIXER) $(DEBUG)
mixer_music src_c/music.c $(SDL) $(MIXER) $(DEBUG)
scrap src_c/scrap.c $(SDL) $(DEBUG)
surface src_c/surface.c src_c/alphablit.c src_c/surface_fill.c $(SDL) $(DEBUG)
key src_c/key.c $(SDL) $(DEBUG)
mouse src_c/mouse.c $(SDL) $(DEBUG)
event src_c/event.c $(SDL) $(DEBUG)
joystick src_c/joystick.c $(SDL) $(DEBUG)
time src_c/time.c $(SDL) $(DEBUG)
mask src_c/mask.c src_c/bitmask.c $(SDL) $(DEBUG)
pixelarray src_c/pixelarray.c $(SDL) $(DEBUG)
transform src_c/transform.c src_c/rotozoom.c src_c/scale2x.c src_c/scale_mmx.c $(SDL) $(DEBUG)
gfxdraw src_c/gfxdraw.c src_c/SDL_gfx/SDL_gfxPrimitives.c $(SDL) $(DEBUG)
draw src_c/draw.c $(SDL) $(DEBUG)
display src_c/display.c $(SDL) $(DEBUG)
rect src_c/rect.c $(SDL) $(DEBUG)
constants src_c/constants.c $(SDL) $(DEBUG)
base src_c/base.c $(SDL) $(DEBUG)
color src_c/color.c $(SDL) $(DEBUG)
surflock src_c/surflock.c $(SDL) $(DEBUG)
rwobject src_c/rwobject.c $(SDL) $(DEBUG)
pixelcopy src_c/pixelcopy.c $(SDL) $(DEBUG)
newbuffer src_c/newbuffer.c $(SDL) $(DEBUG)
bufferproxy src_c/bufferproxy.c $(SDL) $(DEBUG)
math src_c/math.c $(SDL) $(DEBUG)
image src_c/image.c $(SDL) $(DEBUG)
""".format(
                    sdl_includes=" -I".join([
                        join(self.ctx.bootstrap.build_dir, 'jni', 'SDL', 'include'),
                        join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_mixer'),
                        join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_mixer', 'include'),
                        join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_image'),
                        join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_ttf'),
                        join(self.get_recipe('png', self.ctx).get_build_dir(arch.arch)),
                        join(self.get_recipe('jpeg', self.ctx).get_build_dir(arch.arch)),
                    ]),
                    sdl_libs=" -L".join([
                        join(self.ctx.bootstrap.build_dir, "libs", str(arch)),
                        join(self.get_recipe('png', self.ctx).get_build_dir(arch.arch), '.libs'),
                        join(self.get_recipe('jpeg', self.ctx).get_build_dir(arch.arch)),
                    ]),
                ))

            # استبدال Setup الافتراضي بملف إعداد أندرويد
            with open('Setup.Android.SDL2', 'r') as src, open('Setup', 'w') as dst:
                dst.write(src.read())

            # تعطيل فحص setup.py لملف Setup
            with open('setup.py', 'r') as f:
                setup_py = f.read()
            setup_py = setup_py.replace(
                "if not os.path.isfile('Setup'):",
                "if False:"
            )
            with open('setup.py', 'w') as f:
                f.write(setup_py)

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['USE_SDL'] = '2'
        env['PYGAME_EXTRA_BASE'] = join(self.ctx.bootstrap.build_dir, 'libs', str(arch))

        # إضافة مسار Include/cpython لحل مشكلة longintrepr.h في Python 3.11 + رايات Clang
        py_inc_cpython = join(self.ctx.get_python_install_dir(arch.arch), 'include', 'python3.11', 'cpython')
        host_py_inc_cpython = join(self.get_recipe('hostpython3', self.ctx).get_build_dir(arch.arch), 'Include', 'cpython')
        target_py_inc_cpython = join(self.get_recipe('python3', self.ctx).get_build_dir(arch.arch), 'Include', 'cpython')

        extra_flags = (
            f" -I{py_inc_cpython} -I{host_py_inc_cpython} -I{target_py_inc_cpython}"
            " -Wno-error=incompatible-function-pointer-types"
            " -Wno-error=implicit-function-declaration"
            " -Wno-error=int-conversion"
            " -Wno-incompatible-pointer-types"
        )
        env['CFLAGS'] = env.get('CFLAGS', '') + extra_flags
        env['CPPFLAGS'] = env.get('CPPFLAGS', '') + extra_flags
        env['LDFLAGS'] = env.get('LDFLAGS', '') + f" -L{env['PYGAME_EXTRA_BASE']}"
        return env


recipe = Pygame2Recipe()