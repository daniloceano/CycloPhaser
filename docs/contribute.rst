Contributing
============

Contributions are welcome: bug reports, fixes, new features and improvements
to this documentation.

* **Issues.** Report a problem or propose an idea on the
  `issue tracker <https://github.com/daniloceano/CycloPhaser/issues>`_.
* **Pull requests.** Fork the repository, create a branch from ``develop``, and
  open the pull request **against the** ``develop`` **branch**.

Before opening a pull request:

1. Run the tests (see :doc:`testing`) and add tests for what you change.
2. Describe the change under ``[Unreleased]`` in ``CHANGELOG.md``.
3. If the change affects what a user sees, update this documentation.

.. code-block:: bash

   git clone https://github.com/<your-username>/CycloPhaser.git
   cd CycloPhaser
   git checkout develop
   git checkout -b my-change
   # ... edit, test ...
   git push origin my-change
