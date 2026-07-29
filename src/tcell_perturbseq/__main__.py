"""Allow ``python -m tcell_perturbseq`` to invoke the public CLI."""

from tcell_perturbseq.cli import main

raise SystemExit(main())
