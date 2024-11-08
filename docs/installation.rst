Installation Instructions
=========================

To ensure CycloPhaser and its dependencies are installed in an isolated environment, we recommend using either a Conda or virtual environment. Follow the steps below to set up a compatible environment and install CycloPhaser.

Setting Up a Conda Environment
------------------------------

1. **Create a new Conda environment** (recommended Python version is 3.10 or later):
   
   .. code-block:: bash

      conda create -n cyclophaser_env python=3.10

2. **Activate the Conda environment**:

   .. code-block:: bash

      conda activate cyclophaser_env

3. **Install dependencies from the requirements file**:

   Make sure you’re in the directory containing the requirements file. Then, run:

   .. code-block:: bash

      pip install -r requirements.txt

4. **Install CycloPhaser**:

   After installing dependencies, install CycloPhaser using pip:

   .. code-block:: bash

      pip install cyclophaser

Setting Up a Virtual Environment
--------------------------------

If you prefer not to use Conda, you can set up a virtual environment with `venv` (available in Python standard library).

1. **Create a virtual environment**:

   .. code-block:: bash

      python3 -m venv cyclophaser_env

2. **Activate the virtual environment**:

   - On Windows:

     .. code-block:: bash

        cyclophaser_env\Scripts\activate

   - On macOS and Linux:

     .. code-block:: bash

        source cyclophaser_env/bin/activate

3. **Install dependencies from the requirements file**:

   .. code-block:: bash

      pip install -r requirements.txt

4. **Install CycloPhaser**:

   .. code-block:: bash

      pip install cyclophaser


Notes
-----

- **Compatibility**: CycloPhaser requires Python 3.10 or later.
- **Using `mamba`**: If you prefer `mamba` over `conda` for faster environment management, replace `conda` with `mamba` in the commands above.

With these instructions, you can set up an isolated environment for CycloPhaser, ensuring compatibility and avoiding conflicts with other packages.
