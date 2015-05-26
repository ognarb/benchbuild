#!/usr/bin/evn python
# encoding: utf-8

from pprof.project import ProjectFactory, log_with, log
from pprof.settings import config
from group import PprofGroup

from os import path
from plumbum import FG, local
from plumbum.cmd import cp, echo, chmod, find


class Povray(PprofGroup):

    """ povray benchmark """

    class Factory:

        def create(self, exp):
            return Povray(exp, "povray", "multimedia")
    ProjectFactory.addFactory("Povray", Factory())

    src_uri = "https://github.com/POV-Ray/povray"
    src_dir = "povray.git"

    def download(self):
        from pprof.utils.downloader import Git
        with local.cwd(self.builddir):
            Git(self.src_uri, self.src_dir)

    def configure(self):
        povray_dir = path.join(self.builddir, self.src_dir)
        with local.cwd(path.join(povray_dir, "unix")):
            from plumbum.cmd import sh
            sh("prebuild.sh")

        with local.cwd(povray_dir):
            from pprof.utils.compiler import clang, clang_cxx
            configure = local["./configure"]
            with local.env(COMPILED_BY="PPROF <no@mail.nono>",
                           CC=clang(),
                           CFLAGS=" ".join(self.cflags),
                           CXX=clang_cxx(),
                           CXXFLAGS=" ".join(self.cflags),
                           LDFLAGS=" ".join(self.ldflags)):
                configure()

    def build(self):
        from plumbum.cmd import make, ln, mv, rm
        povray_dir = path.join(self.builddir, self.src_dir)
        povray_binary = path.join(povray_dir, "unix", self.name)

        with local.cwd(povray_dir):
            rm("-f", povray_binary)
            make & FG
            #make["clean", "all"] & FG
        mv(path.join(povray_dir, "unix", self.name), self.bin_f)
        self.run_f = self.bin_f

    def prepare(self):
        super(Povray, self).prepare()
        cp["-ar", path.join(self.testdir, "cfg"), self.builddir] & FG
        cp["-ar", path.join(self.testdir, "etc"), self.builddir] & FG
        cp["-ar", path.join(self.testdir, "scenes"), self.builddir] & FG
        cp["-ar", path.join(self.testdir, "share"), self.builddir] & FG
        cp["-ar", path.join(self.testdir, "test"), self.builddir] & FG

    def run_tests(self, experiment):
        from plumbum.cmd import mkdir, chmod
        exp = experiment(self.run_f)

        povray_dir = path.join(self.builddir, self.src_dir)
        povray_binary = path.join(povray_dir, "unix", self.name)
        tmpdir = path.join(self.builddir, "tmp")
        povini = path.join(
            self.builddir, "cfg", ".povray", "3.6", "povray.ini")
        scene_dir = path.join(self.builddir, "share", "povray-3.6", "scenes")
        mkdir(tmpdir, retcode=None)

        with open(povray_binary, 'w') as povray:
            povray.write("#!/bin/sh\n")
            povray.write(str(exp) + " \"$@\"")
        chmod("+x", povray_binary)

        render = local[path.join(povray_dir, "scripts",
                                 "render_scene.sh")]
        pov_files = find(scene_dir, "-name", "*.pov").splitlines()
        for pov_f in pov_files:
            from plumbum.cmd import head, grep, sed
            with local.env(POVRAY=povray_binary, INSTALL_DIR=self.builddir,
                           OUTPUT_DIR=tmpdir, POVINI=povini):
                options = ((((head["-n", "50", "\"" + pov_f + "\""] |
                              grep["-E", "'^//[ ]+[-+]{1}[^ -]'"]) |
                             head["-n", "1"]) |
                            sed["s?^//[ ]*??"]) & FG)
                povray = local[povray_binary]
                povray("+L" + scene_dir, "+L" + tmpdir, "-i" + pov_f,
                       "-o" + tmpdir, options, "-p", retcode=None)