#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # TODO : Check at some time if the bug in dal_select2 has been fixed, and if so, remove this function here
    def work_around_dal_select2_bug():
        """
        Due to a bug in dal_select2, this workaround function here goes into the offending file and replaces the
        relevant code segment with a work-around segment.

        This function ensures that this replacement is done each time django is run and also modifies only the file
        which is loaded via the respective library within the virtual environment of the current python interpreter.
        """

        import dal_select2

        file_to_fix = dal_select2.__file__.replace("/__init__.py", "/static/autocomplete_light/select2.js")
        min_file_to_fix = dal_select2.__file__.replace("/__init__.py", "/static/autocomplete_light/select2.min.js") 
        
        try:
            with open(file_to_fix, "r") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):

                if \
                        line == "                processResults: function (data, page) {\n" and \
                        lines[i+1] == "                    if ($element.attr('data-tags')) {\n" and \
                        lines[i+2] == "                        $.each(data.results, function (index, value) {\n" and \
                        lines[i+3] == "                            value.id = value.text;\n":

                    lines[i+3] = "                            value.id = value.id;\n"

            with open(file_to_fix, "w") as f:
                f.write("".join(lines))

        except FileNotFoundError:
            raise Exception(
                "Could not find select2.js file to inject bug workaround into.\n" +
                "Maybe the dal_select library has changed and this workaround is not necessary anymore?"
            )
        
        try:
            with open(min_file_to_fix, "r") as f:
                f_out = f.read().replace("e.id=e.text", "e.id=e.id")
            with open(min_file_to_fix, "w") as f:
                f.write(f_out)
        except FileNotFoundError:
            raise Exception(
                "Could not find select2.min.js file to inject bug workaround into.\n" +
                "Maybe the dal_select library has changed and this workaround is not necessary anymore?"
            )
    work_around_dal_select2_bug()
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
