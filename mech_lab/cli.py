import sys
import warnings
from blkbx_lab.cli import main as blkbx_main

def main():
    warnings.warn(
        "The 'mechlab' CLI is deprecated and will be removed in a future release. "
        "Please use 'blkbx-lab' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    sys.exit(blkbx_main())

if __name__ == "__main__":
    main()
