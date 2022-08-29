# normalization-lib
supports normalization calculations

# Installation
To install this package using python package manager PIP, use the below command:

"pip install git+https://github.com/DWPSoftwares/normalization-lib.git"

This will always install the latest and updated version of the package.

# Library name
normalization-lib

# Client's Requirements.txt 
In client's requirements.txt file it would be required to add the line as below. No need to mention the version number, PIP will always pick the latest version number
git+https://github.com/DWPSoftwares/normalization-lib.git

# Update Package
To update package from github, please keep in mind to upddate the version number in setup.py file.
At present any developer who is pushing a new commit to main branch should update the version number 

# Versioning


# Version Nomenclature.
Major Feature added: Minor Changes or Refactor: Minor Bug fixes 

# Force update 
Use the below command to update package:
pip install --upgrade --force-reinstall git+https://github.com/DWPSoftwares/normalization-lib.git@main

Note: The above command will uninstall this package and all the other dependencies and then reinstall them.
This operation is CPU intensive and will increase in installation time as further dependencies and code is added to 
this package.

# PIP Version
Installing this package will require pip version >=22.1.2. Please use command :"python -m pip install --upgrade pip" to upgrade the pip version in your virtual environment.

# Usage
