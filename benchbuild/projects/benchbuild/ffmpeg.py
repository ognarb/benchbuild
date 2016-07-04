from benchbuild.project import wrap
from benchbuild.projects.benchbuild.group import BenchBuildGroup
from benchbuild.utils.compiler import lt_clang
from benchbuild.utils.run import run
from benchbuild.utils.downloader import Wget, Rsync
from plumbum import local
from benchbuild.utils.cmd import make, tar


class LibAV(BenchBuildGroup):
    """ LibAV benchmark """
    NAME = 'ffmpeg'
    DOMAIN = 'multimedia'

    src_dir = "ffmpeg-2.6.3"
    src_file = src_dir + ".tar.bz2"
    src_uri = "http://ffmpeg.org/releases/" + src_file
    fate_dir = "fate-samples"
    fate_uri = "rsync://fate-suite.libav.org/fate-suite/"

    def run_tests(self, experiment):
        wrap(self.name, experiment)
        run(make["V=1", "-i", "fate"])

    def download(self):
        Wget(self.src_uri, self.src_file)
        tar('xfj', self.src_file)
        with local.cwd(self.src_dir):
            Rsync(self.fate_uri, self.fate_dir)

    def configure(self):
        clang = lt_clang(self.cflags, self.ldflags, self.compiler_extension)
        with local.cwd(self.src_dir):
            configure = local["./configure"]
            run(configure["--disable-shared", "--cc=" + str(
                clang), "--extra-ldflags=" + " ".join(self.ldflags),
                          "--samples=" + self.fate_dir])

    def build(self):
        with local.cwd(self.src_dir):
            run(make["clean", "all"])
