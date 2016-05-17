"""
benchbuild subcommand to generate a configuration file.

This generates a default config file for benchbuild. You can edit this
file yourself and provide it to benchbuild befor running its subcommands.

You can still override the options using environment variables or command
line flags.
"""
from plumbum import cli
from benchbuild.utils.user_interface import query_yes_no
import os.path


class BenchBuildGenConfig(cli.Application):
    """ Generate a default configuration that can be edited in a text editor. """

    _outpath = "./.benchbuild_config.py"

    @cli.switch(
        ["-o"],
        str,
        help="Where to write the default config file? File type is *.py")
    def set_output(self, dirname):
        """
        Set the output path for the default config.

        Args:
            dirname (str): Output path to write the config to.
        """
        self._outpath = dirname

    def main(self):
        from benchbuild import settings

        self._outpath = os.path.abspath(self._outpath)

        if os.path.exists(self._outpath):
            if not query_yes_no(
                    "File " + self._outpath + " exists already. Overwrite?",
                    "no"):
                exit(1)

        with open(self._outpath, "w") as outfile:
            outfile.write("config = {}\n\n\n")

            for setting in settings.config_metadata:
                outfile.write("## " + setting["name"] + "\n")
                #outfile.write("# " + setting.desc)
                outfile.write("# Default value: " + repr(setting["default"]) +
                              "\n")
                outfile.write("#CFG[" + repr(setting["name"]) + "] = \n")
                outfile.write("\n\n")

        print(("Configuration file has been written to " + self._outpath))
